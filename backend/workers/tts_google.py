"""
Google Cloud Text-to-Speech Worker
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
    from google.api_core import exceptions as gcp_exceptions
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    logging.warning("Google Cloud Text-to-Speech not available. Install google-cloud-texttospeech")

logger = logging.getLogger(__name__)

class GoogleTTSWorker:
    """Worker for generating speech with precise timing using Google Cloud Text-to-Speech"""
    
    def __init__(self, voice: str = None, speaking_rate: float = None, pitch: float = None):
        self.voice = voice or os.getenv("GOOGLE_TTS_VOICE", "ru-RU-Neural2-B")
        self.speaking_rate = float(speaking_rate or os.getenv("GOOGLE_TTS_SPEAKING_RATE", "1.0"))
        self.pitch = float(pitch or os.getenv("GOOGLE_TTS_PITCH", "0.0"))
        
        if not GOOGLE_TTS_AVAILABLE:
            logger.warning("Google Cloud TTS not available, will use mock mode")
            self.use_mock = True
        else:
            self.use_mock = False
            # Initialize TTS client
            try:
                self.client = texttospeech.TextToSpeechClient()
            except Exception as e:
                logger.error(f"Failed to initialize Google TTS client: {e}")
                self.use_mock = True
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def synthesize_speech(self, text: str) -> bytes:
        """
        Простой метод синтеза речи для совместимости с тестами.
        
        Args:
            text: Текст для синтеза
            
        Returns:
            bytes: Аудио данные
        """
        try:
            if self.use_mock:
                return self._generate_mock_audio(text)
            
            # Use Google Cloud TTS
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice_config = texttospeech.VoiceSelectionParams(
                language_code=self.voice.split('-')[0] + '-' + self.voice.split('-')[1],
                name=self.voice,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                speaking_rate=self.speaking_rate,
                pitch=self.pitch,
                sample_rate_hertz=22050
            )
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_config,
                audio_config=audio_config
            )
            
            return response.audio_content
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            # Fallback to mock audio
            return self._generate_mock_audio(text)
    
    def synthesize_slide_text_google(self, texts: List[str], voice: str = None, 
                                   rate: float = None, pitch: float = None) -> Tuple[str, Dict]:
        """
        Синтез речи для каждой фразы; собрать mp3 и TtsWords.json (минимум — тайминги предложений).
        
        Args:
            texts: Список текстов для синтеза
            voice: Голос для синтеза
            rate: Скорость речи
            pitch: Высота тона
            
        Returns:
            Tuple[str, Dict]: (путь к mp3 файлу, структура таймингов)
            {
              "sentences": [
                {"text": "фраза 1", "t0": 0.00, "t1": 1.25},
                {"text": "фраза 2", "t0": 1.30, "t1": 3.10}
              ]
            }
        """
        try:
            if self.use_mock:
                return self._synthesize_mock(texts)
            
            # Use provided parameters or fallback to instance settings
            voice = voice or self.voice
            rate = rate or self.speaking_rate
            pitch = pitch or self.pitch
            
            # Split texts into sentences
            sentences = self._split_into_sentences(texts)
            
            if not sentences:
                raise ValueError("No sentences found in texts")
            
            # Generate audio for each sentence
            audio_segments = []
            sentence_timings = []
            current_time = 0.0
            
            for i, sentence in enumerate(sentences):
                logger.info(f"Synthesizing sentence {i+1}/{len(sentences)}: {sentence[:50]}...")
                
                # Generate audio for this sentence
                audio_data = self._synthesize_sentence(sentence, voice, rate, pitch)
                
                # Calculate duration
                duration = self._get_audio_duration(audio_data)
                
                # Store timing information
                timing_info = {
                    "text": sentence.strip(),
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
            
            # Save audio file
            audio_filename = f"synthesized_{uuid.uuid4().hex[:8]}.wav"
            audio_path = Path(f"/tmp/audio/{audio_filename}")
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(audio_path, 'wb') as f:
                f.write(full_audio)
            
            # Create TtsWords.json structure
            tts_words = {
                "audio": str(audio_path),
                "sentences": [
                    {
                        "text": timing["text"],
                        "t0": timing["t0"],
                        "t1": timing["t1"]
                    }
                    for timing in sentence_timings
                ],
                "words": []  # Word-level timing would require SSML with marks
            }
            
            logger.info(f"Generated TTS: {len(full_audio)} bytes, {len(sentence_timings)} sentences, {current_time:.2f}s total")
            
            return str(audio_path), tts_words
            
        except Exception as e:
            logger.error(f"Error synthesizing slide text: {e}")
            # Fallback to mock TTS
            logger.info("Falling back to mock TTS")
            return self._synthesize_mock(texts)
    
    def _synthesize_sentence(self, sentence: str, voice: str, rate: float, pitch: float) -> bytes:
        """Synthesize audio for a single sentence"""
        try:
            # Prepare synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=sentence)
            
            # Configure voice
            voice_config = texttospeech.VoiceSelectionParams(
                language_code=voice.split('-')[0] + '-' + voice.split('-')[1],  # Extract language code
                name=voice,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            
            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                speaking_rate=rate,
                pitch=pitch,
                sample_rate_hertz=22050
            )
            
            # Perform synthesis
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_config,
                audio_config=audio_config
            )
            
            return response.audio_content
            
        except Exception as e:
            logger.error(f"Error synthesizing sentence: {e}")
            # Fallback to mock audio
            return self._generate_mock_audio(sentence)
    
    def _split_into_sentences(self, texts: List[str]) -> List[str]:
        """Split texts into sentences for timing analysis"""
        sentences = []
        
        for text in texts:
            # Split by common sentence endings
            parts = re.split(r'[.!?]+', text)
            
            for part in parts:
                part = part.strip()
                if part and len(part) > 10:  # Filter out very short fragments
                    sentences.append(part)
        
        # If no sentences found, split by paragraphs
        if not sentences:
            for text in texts:
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        sentences.append(para)
        
        # If still no sentences, use the whole text
        if not sentences:
            sentences = [text for text in texts if text.strip()]
        
        return sentences
    
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
    
    def _synthesize_mock(self, texts: List[str]) -> Tuple[str, Dict]:
        """Mock TTS synthesis for testing"""
        try:
            # Combine all texts
            full_text = " ".join(texts)
            
            # Split into sentences
            sentences = self._split_into_sentences(texts)
            
            # Generate mock timings
            sentence_timings = []
            current_time = 0.0
            
            for i, sentence in enumerate(sentences):
                # Estimate duration based on text length
                duration = max(1.0, len(sentence) * 0.1)  # Rough estimate
                
                timing_info = {
                    "text": sentence.strip(),
                    "t0": current_time,
                    "t1": current_time + duration,
                    "duration": duration,
                    "index": i
                }
                
                sentence_timings.append(timing_info)
                current_time += duration + 0.3  # Add pause
            
            # Generate mock audio
            mock_audio = self._generate_mock_audio(full_text)
            
            # Save mock audio file
            audio_filename = f"mock_{uuid.uuid4().hex[:8]}.wav"
            audio_path = Path(f"/tmp/audio/{audio_filename}")
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(audio_path, 'wb') as f:
                f.write(mock_audio)
            
            # Create TtsWords.json structure
            tts_words = {
                "audio": str(audio_path),
                "sentences": [
                    {
                        "text": timing["text"],
                        "t0": timing["t0"],
                        "t1": timing["t1"]
                    }
                    for timing in sentence_timings
                ],
                "words": []
            }
            
            logger.info(f"Mock TTS generated: {len(mock_audio)} bytes, {len(sentence_timings)} sentences, {current_time:.2f}s total")
            
            return str(audio_path), tts_words
            
        except Exception as e:
            logger.error(f"Error in mock TTS: {e}")
            raise

# Utility functions for integration
def synthesize_slide_text_google(texts: List[str], voice: str = None, 
                                 rate: float = None, pitch: float = None) -> Tuple[str, Dict]:
    """
    Синтез речи для каждой фразы; собрать mp3 и TtsWords.json (минимум — тайминги предложений).
    
    Args:
        texts: Список текстов для синтеза
        voice: Голос для синтеза
        rate: Скорость речи
        pitch: Высота тона
        
    Returns:
        Tuple[str, Dict]: (путь к mp3 файлу, структура таймингов)
        {
          "sentences": [
            {"text": "фраза 1", "t0": 0.00, "t1": 1.25},
            {"text": "фраза 2", "t0": 1.30, "t1": 3.10}
          ]
        }
    """
    worker = GoogleTTSWorker(voice, rate, pitch)
    return worker.synthesize_slide_text_google(texts, voice, rate, pitch)

if __name__ == "__main__":
    # Test the worker
    async def test_worker():
        test_texts = [
            "Welcome to our presentation about artificial intelligence.",
            "Today we will explore the fundamentals of machine learning.",
            "We'll discuss supervised learning, unsupervised learning, and reinforcement learning."
        ]
        
        worker = GoogleTTSWorker()
        audio_path, tts_words = worker.synthesize_slide_text_google(test_texts)
        
        print(f"Generated audio: {audio_path}")
        print(f"Sentences: {len(tts_words['sentences'])}")
        
        for sentence in tts_words['sentences']:
            print(f"  {sentence['t0']:.2f}s - {sentence['t1']:.2f}s: {sentence['text'][:50]}...")
    
    asyncio.run(test_worker())