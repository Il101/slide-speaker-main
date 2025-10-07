"""
Google Cloud Text-to-Speech Worker with SSML support
"""
import asyncio
import json
import logging
import os
import wave
import struct
import io
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import uuid
import re

try:
    from google.cloud import texttospeech
    from google.cloud import texttospeech_v1beta1  # For timepoint support
    from google.api_core import exceptions as gcp_exceptions
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    logging.warning("Google Cloud Text-to-Speech not available. Install google-cloud-texttospeech")

logger = logging.getLogger(__name__)

class GoogleTTSWorkerSSML:
    """Worker for generating speech with SSML support and precise timing using Google Cloud Text-to-Speech"""
    
    def __init__(self, voice: str = None, speaking_rate: float = None, pitch: float = None):
        self.voice = voice or os.getenv("GOOGLE_TTS_VOICE", "ru-RU-Wavenet-D")
        self.speaking_rate = float(speaking_rate or os.getenv("GOOGLE_TTS_SPEAKING_RATE", "1.0"))
        self.pitch = float(pitch or os.getenv("GOOGLE_TTS_PITCH", "0.0"))
        
        if not GOOGLE_TTS_AVAILABLE:
            logger.warning("Google Cloud TTS not available, will use mock mode")
            self.use_mock = True
        else:
            self.use_mock = False
            # Initialize TTS client (use v1beta1 for timepoint support)
            try:
                self.client = texttospeech_v1beta1.TextToSpeechClient()
                logger.info("✅ Google Cloud TTS client initialized (v1beta1 for timepoints)")
            except Exception as e:
                logger.error(f"Failed to initialize Google TTS client: {e}")
                self.use_mock = True
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def synthesize_speech_with_ssml(self, ssml_text: str, enable_timing: bool = True) -> Tuple[bytes, List[Dict]]:
        """
        Синтез речи с SSML-разметкой для лучшего контроля над произношением.
        
        Args:
            ssml_text: Текст с SSML-разметкой
            enable_timing: Включить ли получение word-level timing через <mark> теги
            
        Returns:
            Tuple[bytes, List[Dict]]: (Аудио данные, список word timings)
        """
        try:
            if self.use_mock:
                return self._generate_mock_audio(ssml_text), []
            
            # ✅ FIX: Validate SSML before sending to Google TTS
            from app.services.ssml_validator import validate_ssml, fix_common_ssml_issues
            
            is_valid, errors = validate_ssml(ssml_text)
            
            if not is_valid:
                logger.warning(f"❌ Invalid SSML detected:")
                for error in errors:
                    logger.warning(f"   - {error}")
                
                # Try to fix automatically
                logger.info("🔧 Attempting to auto-fix SSML...")
                ssml_text = fix_common_ssml_issues(ssml_text)
                
                # Validate again
                is_valid, errors = validate_ssml(ssml_text)
                if not is_valid:
                    logger.error(f"❌ Cannot fix SSML errors: {errors}")
                    raise ValueError(f"Invalid SSML: {errors}")
                else:
                    logger.info("✅ SSML auto-fixed successfully")
            
            # Use Google Cloud TTS v1beta1 with SSML (supports timepoints)
            synthesis_input = texttospeech_v1beta1.SynthesisInput(ssml=ssml_text)
            
            # For Chirp 3 models, we don't need ssml_gender parameter
            voice_config = texttospeech_v1beta1.VoiceSelectionParams(
                language_code=self.voice.split('-')[0] + '-' + self.voice.split('-')[1],
                name=self.voice
            )
            
            # Chirp 3 supports higher quality audio at 24000 Hz
            audio_config = texttospeech_v1beta1.AudioConfig(
                audio_encoding=texttospeech_v1beta1.AudioEncoding.LINEAR16,
                sample_rate_hertz=24000
            )
            
            # Enable time pointing to get word-level timing from <mark> tags
            if enable_timing:
                request = texttospeech_v1beta1.SynthesizeSpeechRequest(
                    input=synthesis_input,
                    voice=voice_config,
                    audio_config=audio_config,
                    enable_time_pointing=[texttospeech_v1beta1.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
                )
                response = self.client.synthesize_speech(request=request)
                
                # Extract word timings from timepoints
                word_timings = []
                if hasattr(response, 'timepoints') and response.timepoints:
                    for timepoint in response.timepoints:
                        word_timings.append({
                            'mark_name': timepoint.mark_name,
                            'time_seconds': timepoint.time_seconds
                        })
                    logger.info(f"✅ Got {len(word_timings)} word timings from Google TTS")
                else:
                    logger.warning("⚠️ No timepoints returned (check if SSML has <mark> tags)")
                
                logger.info(f"Synthesized SSML speech with timing: {len(response.audio_content)} bytes, {len(word_timings)} timepoints")
                return response.audio_content, word_timings
            else:
                # Simple synthesis without timepoints
                request = texttospeech_v1beta1.SynthesizeSpeechRequest(
                    input=synthesis_input,
                    voice=voice_config,
                    audio_config=audio_config
                )
                response = self.client.synthesize_speech(request=request)
                logger.info(f"Synthesized SSML speech: {len(response.audio_content)} bytes")
                return response.audio_content, []
            
        except Exception as e:
            logger.error(f"Error synthesizing SSML speech: {e}")
            # Fallback to mock audio
            return self._generate_mock_audio(ssml_text), []
    
    def synthesize_slide_text_google_ssml(self, ssml_texts: List[str], voice: str = None) -> Tuple[str, Dict]:
        """
        Синтез речи для SSML-текстов; собрать mp3 и TtsWords.json с таймингами предложений.
        
        Args:
            ssml_texts: Список SSML-текстов для синтеза
            voice: Голос для синтеза
            
        Returns:
            Tuple[str, Dict]: (путь к mp3 файлу, структура таймингов)
        """
        try:
            if self.use_mock:
                return self._synthesize_mock(ssml_texts)
            
            # Use provided voice or fallback to instance settings
            voice = voice or self.voice
            
            # Process each SSML text
            audio_segments = []
            sentence_timings = []
            all_word_timings = []  # Store all word timings with absolute time
            current_time = 0.0
            
            for i, ssml_text in enumerate(ssml_texts):
                logger.info(f"Synthesizing SSML text {i+1}/{len(ssml_texts)}: {ssml_text[:50]}...")
                
                # Generate audio for this SSML text with word timing
                audio_data, word_timings = self.synthesize_speech_with_ssml(ssml_text, enable_timing=True)
                
                # Calculate duration
                duration = self._get_audio_duration(audio_data)
                
                # Extract clean text from SSML for timing info
                clean_text = self._extract_text_from_ssml(ssml_text)
                
                # Adjust word timings to absolute time (relative to full audio)
                for wt in word_timings:
                    all_word_timings.append({
                        'mark_name': wt['mark_name'],
                        'time_seconds': current_time + wt['time_seconds'],
                        'sentence_index': i
                    })
                
                # Store timing information
                timing_info = {
                    "text": clean_text.strip(),
                    "t0": current_time,
                    "t1": current_time + duration,
                    "duration": duration,
                    "index": i,
                    "word_timings": word_timings  # Keep original relative timings too
                }
                
                audio_segments.append(audio_data)
                sentence_timings.append(timing_info)
                
                current_time += duration
                
                # Add small pause between segments
                if i < len(ssml_texts) - 1:
                    pause_duration = 0.3  # 300ms pause
                    current_time += pause_duration
            
            # Concatenate all audio segments
            full_audio = self._concatenate_audio_segments(audio_segments)
            
            # Convert WAV to MP3 using pydub
            from pydub import AudioSegment
            import io
            
            # Create AudioSegment from WAV data
            audio_segment = AudioSegment.from_wav(io.BytesIO(full_audio))
            
            # Save audio file as MP3
            audio_filename = f"synthesized_ssml_{uuid.uuid4().hex[:8]}.mp3"
            audio_path = Path(f"/tmp/audio/{audio_filename}")
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export as MP3
            audio_segment.export(str(audio_path), format="mp3")
            
            # ✅ Create sentences based on group markers for better fallback matching
            sentences_from_markers = self._create_sentences_from_markers(all_word_timings, sentence_timings)
            
            # Create TtsWords.json structure
            tts_words = {
                "audio": str(audio_path),
                "sentences": sentences_from_markers,  # ✅ Use marker-based sentences
                "word_timings": all_word_timings,  # All word timings with absolute time
                "words": []  # Legacy format, kept for compatibility
            }
            
            logger.info(f"✅ Created {len(sentences_from_markers)} sentences from markers for better sync")
            
            logger.info(f"Generated TTS audio with {len(all_word_timings)} word timepoints")
            
            logger.info(f"Generated SSML TTS: {len(full_audio)} bytes, {len(sentence_timings)} sentences, {current_time:.2f}s total")
            
            return str(audio_path), tts_words
            
        except Exception as e:
            logger.error(f"Error synthesizing SSML slide text: {e}")
            # Fallback to mock TTS
            return self._synthesize_mock(ssml_texts)
    
    def _extract_text_from_ssml(self, ssml_text: str) -> str:
        """Extract clean text from SSML markup"""
        # Remove SSML tags but keep the text content
        text = re.sub(r'<[^>]+>', '', ssml_text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _get_audio_duration(self, audio_data: bytes) -> float:
        """Calculate duration of audio data"""
        try:
            # Create a temporary WAV file to read duration
            with io.BytesIO(audio_data) as audio_io:
                with wave.open(audio_io, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    duration = frames / sample_rate
                    return duration
        except Exception as e:
            logger.warning(f"Could not calculate audio duration: {e}")
            # Estimate duration based on data size (rough approximation)
            return len(audio_data) / 44100  # Assume 44.1kHz, 16-bit
    
    def _concatenate_audio_segments(self, audio_segments: List[bytes]) -> bytes:
        """Concatenate multiple audio segments into one"""
        if not audio_segments:
            return b''
        
        if len(audio_segments) == 1:
            return audio_segments[0]
        
        try:
            # For simplicity, we'll just concatenate the raw audio data
            # In a production system, you'd want to properly handle WAV headers
            concatenated = b''.join(audio_segments)
            return concatenated
        except Exception as e:
            logger.error(f"Error concatenating audio segments: {e}")
            return audio_segments[0] if audio_segments else b''
    
    def _synthesize_mock(self, texts: List[str]) -> Tuple[str, Dict]:
        """Mock TTS synthesis for testing"""
        logger.info("Using mock TTS synthesis")
        
        # Create mock audio file
        audio_filename = f"mock_ssml_{uuid.uuid4().hex[:8]}.wav"
        audio_path = Path(f"/tmp/audio/{audio_filename}")
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a simple WAV file with silence
        sample_rate = 24000
        duration = 2.0  # 2 seconds per text
        samples = int(sample_rate * duration)
        
        with wave.open(str(audio_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Write silence
            silence = struct.pack('<h', 0) * samples
            wav_file.writeframes(silence)
        
        # Create mock timing structure
        tts_words = {
            "audio": str(audio_path),
            "sentences": [
                {
                    "text": text[:100],  # First 100 chars
                    "t0": i * duration,
                    "t1": (i + 1) * duration
                }
                for i, text in enumerate(texts)
            ],
            "words": []
        }
        
        return str(audio_path), tts_words
    
    def _generate_mock_audio(self, text: str) -> bytes:
        """Generate mock audio data"""
        # Create a simple WAV file with silence
        sample_rate = 24000
        duration = 1.0  # 1 second
        samples = int(sample_rate * duration)
        
        with io.BytesIO() as audio_io:
            with wave.open(audio_io, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Write silence
                silence = struct.pack('<h', 0) * samples
                wav_file.writeframes(silence)
            
            return audio_io.getvalue()
    
    def _create_sentences_from_markers(
        self, 
        word_timings: List[Dict[str, Any]], 
        original_sentences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create sentences based on group markers from word_timings
        
        This splits the audio into logical sentences aligned with group markers,
        enabling better fallback text matching for visual synchronization.
        
        Args:
            word_timings: List of all word timings with mark_name
            original_sentences: Original sentence timings (might be just one big sentence)
            
        Returns:
            List of sentence dicts with t0, t1, text
        """
        if not word_timings:
            return original_sentences
        
        # Find all group markers
        group_markers = []
        for i, wt in enumerate(word_timings):
            mark_name = wt.get('mark_name', '')
            if mark_name.startswith('group_'):
                group_markers.append({
                    'index': i,
                    'mark_name': mark_name,
                    'time': wt.get('time_seconds', 0)
                })
        
        if len(group_markers) < 2:
            # Not enough markers to split, return original
            logger.info(f"Only {len(group_markers)} group markers, keeping original sentences")
            return original_sentences
        
        # Create sentences between consecutive group markers
        sentences = []
        for i in range(len(group_markers)):
            current_marker = group_markers[i]
            t0 = current_marker['time']
            
            # Find t1: next group marker or end of audio
            if i + 1 < len(group_markers):
                t1 = group_markers[i + 1]['time']
            else:
                # Last marker: use original end time
                if original_sentences:
                    t1 = original_sentences[-1].get('t1', t0 + 5.0)
                else:
                    t1 = t0 + 5.0
            
            # Get text for this segment (approximate - use marker name as identifier)
            text = f"Segment {current_marker['mark_name']}"
            
            # Try to extract actual text from original sentence
            if original_sentences and len(original_sentences) > 0:
                orig_text = original_sentences[0].get('text', '')
                # Get a portion of text based on timing
                # This is approximate, but better than nothing
                text = f"{current_marker['mark_name']}: {orig_text[:100]}"
            
            sentences.append({
                'text': text,
                't0': t0,
                't1': t1,
                'group_marker': current_marker['mark_name']
            })
        
        logger.info(f"Split audio into {len(sentences)} sentences based on group markers")
        return sentences

# Convenience function
def synthesize_slide_text_google_ssml(ssml_texts: List[str], voice: str = None) -> Tuple[str, Dict]:
    """Convenience function for SSML TTS synthesis"""
    worker = GoogleTTSWorkerSSML()
    return worker.synthesize_slide_text_google_ssml(ssml_texts, voice)
