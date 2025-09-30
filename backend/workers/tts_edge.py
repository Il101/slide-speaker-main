"""
TTS Edge Worker for generating speech with precise timing information
"""
import asyncio
import aiohttp
import json
import logging
import wave
import struct
import io
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import uuid
import re
import azure.cognitiveservices.speech as speechsdk

logger = logging.getLogger(__name__)

class TTSEdgeWorker:
    """Worker for generating TTS with sentence-level timing using Azure Speech Services"""
    
    def __init__(self, azure_key: str = None, azure_region: str = None, voice: str = "ru-RU-SvetlanaNeural"):
        self.azure_key = azure_key or os.getenv("AZURE_TTS_KEY")
        self.azure_region = azure_region or os.getenv("AZURE_TTS_REGION")
        self.voice = voice or os.getenv("TTS_VOICE", "ru-RU-SvetlanaNeural")
        self.speed = float(os.getenv("TTS_SPEED", "1.0"))
        
        if not self.azure_key or not self.azure_region:
            logger.warning("Azure TTS credentials not provided, will use mock TTS")
            self.use_mock = True
        else:
            self.use_mock = False
            # Initialize Azure Speech SDK
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.azure_key,
                region=self.azure_region
            )
            self.speech_config.speech_synthesis_voice_name = self.voice
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_audio_with_timing(self, text: str, voice: str = "alloy", speed: float = 1.0) -> Tuple[bytes, List[Dict[str, Any]]]:
        """
        Generate audio with sentence-level timing information
        
        Args:
            text: Text to convert to speech
            voice: Voice to use for synthesis
            speed: Speech speed multiplier
            
        Returns:
            Tuple of (audio_data, sentence_timings)
        """
        try:
            # Split text into sentences for timing analysis
            sentences = self._split_into_sentences(text)
            
            if not sentences:
                raise ValueError("No sentences found in text")
            
            # Generate audio for each sentence
            audio_segments = []
            sentence_timings = []
            current_time = 0.0
            
            for i, sentence in enumerate(sentences):
                logger.info(f"Generating audio for sentence {i+1}/{len(sentences)}: {sentence[:50]}...")
                
                # Generate audio for this sentence
                audio_data = await self._generate_sentence_audio(sentence, voice, speed)
                
                # Analyze audio duration
                duration = self._get_audio_duration(audio_data)
                
                # Store timing information
                timing_info = {
                    "sentence": sentence.strip(),
                    "t0": current_time,
                    "t1": current_time + duration,
                    "duration": duration,
                    "index": i
                }
                
                audio_segments.append(audio_data)
                sentence_timings.append(timing_info)
                
                current_time += duration
                
                # Add small pause between sentences
                if i < len(sentences) - 1:
                    pause_duration = 0.3  # 300ms pause
                    current_time += pause_duration
            
            # Concatenate all audio segments
            full_audio = self._concatenate_audio_segments(audio_segments)
            
            logger.info(f"Generated audio: {len(full_audio)} bytes, {len(sentence_timings)} sentences, {current_time:.2f}s total")
            
            return full_audio, sentence_timings
            
        except Exception as e:
            logger.error(f"Error generating audio with timing: {e}")
            raise
    
    async def generate_audio_for_slide(self, speaker_notes: str, slide_elements: List[Dict[str, Any]], voice: str = "alloy", speed: float = 1.0) -> Tuple[bytes, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate audio for a slide with element-level timing synchronization
        
        Args:
            speaker_notes: Speaker notes text
            slide_elements: List of slide elements with IDs
            voice: Voice to use
            speed: Speech speed
            
        Returns:
            Tuple of (audio_data, sentence_timings, element_mapping)
        """
        try:
            # Generate audio with sentence timing
            audio_data, sentence_timings = await self.generate_audio_with_timing(speaker_notes, voice, speed)
            
            # Map sentences to slide elements
            element_mapping = self._map_sentences_to_elements(sentence_timings, slide_elements)
            
            # Create enhanced timing with element references
            enhanced_timings = []
            for timing in sentence_timings:
                enhanced_timing = timing.copy()
                
                # Find associated elements
                associated_elements = element_mapping.get(timing['index'], [])
                enhanced_timing['elements'] = associated_elements
                
                # Add visual cue suggestions
                enhanced_timing['suggested_cues'] = self._suggest_visual_cues(timing, associated_elements)
                
                enhanced_timings.append(enhanced_timing)
            
            logger.info(f"Generated slide audio: {len(audio_data)} bytes, {len(enhanced_timings)} timed segments")
            
            return audio_data, enhanced_timings, element_mapping
            
        except Exception as e:
            logger.error(f"Error generating slide audio: {e}")
            raise
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for timing analysis"""
        # Enhanced sentence splitting that handles various formats
        sentences = []
        
        # Split by common sentence endings
        parts = re.split(r'[.!?]+', text)
        
        for part in parts:
            part = part.strip()
            if part and len(part) > 10:  # Filter out very short fragments
                sentences.append(part)
        
        # If no sentences found, split by paragraphs
        if not sentences:
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                para = para.strip()
                if para:
                    sentences.append(para)
        
        # If still no sentences, use the whole text
        if not sentences:
            sentences = [text]
        
        return sentences
    
    async def _generate_sentence_audio(self, sentence: str, voice: str = None, speed: float = None) -> bytes:
        """Generate audio for a single sentence using Azure TTS"""
        if self.use_mock:
            return self._generate_mock_audio(sentence)
        
        try:
            # Use Azure Speech SDK for real TTS
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Prepare SSML for better control
            ssml_text = self._create_ssml(sentence, voice or self.voice, speed or self.speed)
            
            # Synthesize speech
            result = synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                raise Exception(f"TTS synthesis canceled: {cancellation_details.reason}")
            else:
                raise Exception(f"TTS synthesis failed: {result.reason}")
                
        except Exception as e:
            logger.error(f"Azure TTS failed: {e}")
            # Fallback to mock TTS
            logger.info("Falling back to mock TTS")
            return self._generate_mock_audio(sentence)
    
    def _create_ssml(self, text: str, voice: str, speed: float) -> str:
        """Create SSML markup for Azure TTS"""
        # Escape XML special characters
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ru-RU">
            <voice name="{voice}">
                <prosody rate="{speed}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        return ssml.strip()
    
    def _generate_mock_audio(self, text: str) -> bytes:
        """Generate mock audio data for testing"""
        # Create a simple WAV file with silence
        duration = max(1.0, len(text) * 0.1)  # Rough estimate: 0.1s per character
        sample_rate = 22050
        samples = int(duration * sample_rate)
        
        # Generate silence (zeros)
        audio_data = struct.pack(f'{samples}h', *[0] * samples)
        
        # Create WAV header
        wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + len(audio_data),
            b'WAVE',
            b'fmt ',
            16,  # fmt chunk size
            1,   # audio format (PCM)
            1,   # number of channels
            sample_rate,
            sample_rate * 2,  # byte rate
            2,   # block align
            16,  # bits per sample
            b'data',
            len(audio_data)
        )
        
        return wav_header + audio_data
    
    def _get_audio_duration(self, audio_data: bytes) -> float:
        """Calculate duration of audio data"""
        try:
            # Try to read as WAV file
            with io.BytesIO(audio_data) as audio_io:
                with wave.open(audio_io, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    duration = frames / sample_rate
                    return duration
        except Exception:
            # Fallback: estimate duration based on text length
            # Rough estimate: 150 words per minute = 2.5 words per second
            text_length = len(audio_data)  # This is a rough proxy
            estimated_duration = text_length / 1000  # Very rough estimate
            return max(0.5, estimated_duration)  # Minimum 0.5 seconds
    
    def _concatenate_audio_segments(self, audio_segments: List[bytes]) -> bytes:
        """Concatenate multiple audio segments into one"""
        if not audio_segments:
            return b''
        
        if len(audio_segments) == 1:
            return audio_segments[0]
        
        try:
            # For WAV files, we can concatenate properly
            concatenated = io.BytesIO()
            
            with wave.open(concatenated, 'wb') as output_wav:
                # Set up output format based on first segment
                with io.BytesIO(audio_segments[0]) as first_io:
                    with wave.open(first_io, 'rb') as first_wav:
                        output_wav.setparams(first_wav.getparams())
                        output_wav.writeframes(first_wav.readframes(first_wav.getnframes()))
                
                # Append remaining segments
                for segment in audio_segments[1:]:
                    with io.BytesIO(segment) as segment_io:
                        with wave.open(segment_io, 'rb') as segment_wav:
                            output_wav.writeframes(segment_wav.readframes(segment_wav.getnframes()))
            
            return concatenated.getvalue()
            
        except Exception as e:
            logger.warning(f"Failed to concatenate audio segments properly: {e}")
            # Fallback: simple concatenation
            return b''.join(audio_segments)
    
    def _map_sentences_to_elements(self, sentence_timings: List[Dict[str, Any]], slide_elements: List[Dict[str, Any]]) -> Dict[int, List[str]]:
        """Map sentences to slide elements based on content similarity"""
        mapping = {}
        
        for i, timing in enumerate(sentence_timings):
            sentence_text = timing['sentence'].lower()
            associated_elements = []
            
            for element in slide_elements:
                if element.get('type') == 'text' and element.get('text'):
                    element_text = element['text'].lower()
                    
                    # Simple keyword matching
                    if self._text_similarity(sentence_text, element_text) > 0.3:
                        associated_elements.append(element['id'])
            
            mapping[i] = associated_elements
        
        return mapping
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity score"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _suggest_visual_cues(self, timing: Dict[str, Any], elements: List[str]) -> List[Dict[str, Any]]:
        """Suggest visual cues based on timing and elements"""
        cues = []
        
        if elements:
            # Suggest highlight for main elements
            for element_id in elements:
                cue = {
                    "t0": timing['t0'],
                    "t1": timing['t1'],
                    "action": "highlight",
                    "element_id": element_id
                }
                cues.append(cue)
        else:
            # Suggest laser movement for general content
            cue = {
                "t0": timing['t0'],
                "t1": timing['t1'],
                "action": "laser_move",
                "to": [400, 300]  # Center position
            }
            cues.append(cue)
        
        return cues
    
    def save_audio_with_metadata(self, audio_data: bytes, sentence_timings: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
        """Save audio file with timing metadata"""
        try:
            # Save audio file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            # Save metadata
            metadata_path = output_path.with_suffix('.json')
            metadata = {
                "audio_file": str(output_path),
                "total_duration": sentence_timings[-1]['t1'] if sentence_timings else 0.0,
                "sentence_count": len(sentence_timings),
                "sentences": sentence_timings,
                "generated_at": str(uuid.uuid4())
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved audio and metadata: {output_path}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error saving audio with metadata: {e}")
            raise

# Main function for slide text synthesis
async def synthesize_slide_text(slide_notes: List[str], voice: str = "ru-RU-SvetlanaNeural", speed: float = 1.0) -> Dict[str, Any]:
    """
    Synthesize slide text to audio with timing information
    
    Args:
        slide_notes: List of text notes for the slide
        voice: Voice to use for synthesis
        speed: Speech speed multiplier
        
    Returns:
        Dictionary with audio file path and timing information
    """
    try:
        # Combine all notes into single text
        full_text = " ".join(slide_notes)
        
        # Initialize TTS worker
        worker = TTSEdgeWorker(voice=voice)
        
        # Generate audio with timing
        audio_data, sentence_timings = await worker.generate_audio_with_timing(full_text, voice, speed)
        
        # Create output filename
        audio_filename = "001.mp3"  # For now, use single audio file per slide
        output_path = Path(f"/tmp/audio/{audio_filename}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert WAV to MP3 (simplified - in real implementation use ffmpeg)
        # For now, save as WAV
        wav_path = output_path.with_suffix('.wav')
        with open(wav_path, 'wb') as f:
            f.write(audio_data)
        
        # Create TtsWords.json structure
        tts_words = {
            "audio": str(wav_path),
            "sentences": [
                {
                    "text": timing["sentence"],
                    "t0": timing["t0"],
                    "t1": timing["t1"]
                }
                for timing in sentence_timings
            ],
            "words": []  # Word-level timing would require more complex analysis
        }
        
        # Save TtsWords.json
        tts_words_path = wav_path.with_suffix('.json')
        with open(tts_words_path, 'w', encoding='utf-8') as f:
            json.dump(tts_words, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Generated TTS for slide: {len(audio_data)} bytes, {len(sentence_timings)} sentences")
        
        return {
            "audio_file": str(wav_path),
            "tts_words_file": str(tts_words_path),
            "sentences": sentence_timings,
            "total_duration": sentence_timings[-1]["t1"] if sentence_timings else 0.0
        }
        
    except Exception as e:
        logger.error(f"Error synthesizing slide text: {e}")
        raise

# Utility functions for integration
async def generate_slide_audio(lesson_id: str, slide_id: int, speaker_notes: str, slide_elements: List[Dict[str, Any]], voice: str = "alloy", speed: float = 1.0) -> Dict[str, Any]:
    """
    Generate audio for a slide with complete timing information
    
    Args:
        lesson_id: Lesson identifier
        slide_id: Slide number
        speaker_notes: Speaker notes text
        slide_elements: List of slide elements
        voice: Voice to use
        speed: Speech speed
        
    Returns:
        Dictionary containing audio_path, metadata, and timing information
    """
    async with TTSEdgeWorker() as worker:
        try:
            # Generate audio with timing
            audio_data, sentence_timings, element_mapping = await worker.generate_audio_for_slide(
                speaker_notes, slide_elements, voice, speed
            )
            
            # Create output paths
            audio_filename = f"{slide_id:03d}.mp3"
            audio_path = Path(f"/tmp/lessons/{lesson_id}/audio/{audio_filename}")
            
            # Save audio and metadata
            metadata = worker.save_audio_with_metadata(audio_data, sentence_timings, audio_path)
            
            return {
                "lesson_id": lesson_id,
                "slide_id": slide_id,
                "audio_path": str(audio_path),
                "audio_url": f"/assets/{lesson_id}/audio/{audio_filename}",
                "metadata": metadata,
                "sentence_timings": sentence_timings,
                "element_mapping": element_mapping,
                "total_duration": metadata["total_duration"]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate slide audio: {e}")
            raise

if __name__ == "__main__":
    # Test the worker
    async def test_worker():
        test_notes = """
        Welcome to our presentation about artificial intelligence. 
        Today we will explore the fundamentals of machine learning. 
        We'll discuss supervised learning, unsupervised learning, and reinforcement learning.
        """
        
        test_elements = [
            {"id": "elem_1", "type": "text", "text": "Artificial Intelligence", "bbox": [100, 100, 400, 50]},
            {"id": "elem_2", "type": "text", "text": "Machine Learning", "bbox": [100, 200, 400, 50]},
            {"id": "elem_3", "type": "text", "text": "Supervised Learning", "bbox": [100, 300, 400, 50]}
        ]
        
        async with TTSEdgeWorker() as worker:
            audio_data, timings, mapping = await worker.generate_audio_for_slide(
                test_notes, test_elements
            )
            
            print(f"Generated audio: {len(audio_data)} bytes")
            print(f"Sentences: {len(timings)}")
            print(f"Element mapping: {mapping}")
            
            for timing in timings:
                print(f"  {timing['t0']:.2f}s - {timing['t1']:.2f}s: {timing['sentence'][:50]}...")
    
    asyncio.run(test_worker())