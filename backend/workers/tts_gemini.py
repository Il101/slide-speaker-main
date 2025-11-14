"""
Google Cloud Gemini TTS Flash 2.5 Worker

✅ Features:
- Gemini 2.5 Flash TTS model (superior voice quality)
- Natural Language Prompts for style control
- Markup Tags for inline effects
- Multi-speaker synthesis
- Streaming support
- 78% cheaper than Chirp 3 HD ($3.50 vs $16.00 per 1M chars)

❌ Limitations:
- No SSML support
- No timepoints (word-level timing)
- Text limit: 4000 bytes per request
- Prompt limit: 4000 bytes

Note: For visual effects, use sentence-level timing estimation instead of word-level.
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

class GeminiTTSWorker:
    """Worker for generating speech using Gemini TTS Flash 2.5"""
    
    def __init__(self, voice: str = None, model: str = None, prompt: str = None):
        """
        Initialize Gemini TTS Worker
        
        Args:
            voice: Voice name (default: Charon, language-independent)
            model: Model name (default: gemini-2.5-flash-tts)
            prompt: Natural language style prompt (optional)
        """
        self.voice = voice or os.getenv("GEMINI_TTS_VOICE", "Charon")
        self.model = model or os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-tts")
        self.prompt = prompt or os.getenv("GEMINI_TTS_PROMPT", "Speak naturally and clearly, with good pacing and intonation.")
        
        # Language from voice or environment
        self.language_code = os.getenv("GEMINI_TTS_LANGUAGE", "ru-RU")
        
        # Check environment
        environment = os.getenv("ENVIRONMENT", "development")
        
        if not GOOGLE_TTS_AVAILABLE:
            if environment == "production":
                raise RuntimeError("Google Cloud TTS library not available in production! Install google-cloud-texttospeech")
            logger.warning("Google Cloud TTS not available, will use mock mode (development only)")
            self.use_mock = True
        else:
            self.use_mock = False
            # Initialize TTS client (use v1 for Gemini TTS)
            try:
                self.client = texttospeech.TextToSpeechClient()
                logger.info(f"✅ Gemini TTS client initialized: model={self.model}, voice={self.voice}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini TTS client: {e}")
                self.use_mock = True
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def synthesize_speech(self, text: str, prompt: str = None) -> bytes:
        """
        Synthesize speech using Gemini 2.5 Flash TTS
        
        Args:
            text: Plain text to synthesize (NO SSML - not supported by Gemini TTS)
            prompt: Optional natural language style prompt for expressiveness
            
        Returns:
            Audio data as bytes (LINEAR16, 24kHz)
        """
        try:
            if self.use_mock:
                return self._generate_mock_audio(text)
            
            # Use provided prompt or fallback to instance settings
            style_prompt = prompt or self.prompt
            
            # ⚠️ Validate text length (Gemini TTS limit: 4000 bytes)
            text_bytes = text.encode('utf-8')
            if len(text_bytes) > 4000:
                logger.warning(f"⚠️ Text too long ({len(text_bytes)} bytes), truncating to 4000 bytes")
                # Truncate by bytes, not characters
                text = text_bytes[:3900].decode('utf-8', errors='ignore')
            
            # ✅ NEW API: SynthesisInput now supports prompt parameter (requires google-cloud-texttospeech>=2.29.0)
            synthesis_input = texttospeech.SynthesisInput(
                text=text,
                prompt=style_prompt  # Natural language style control
            )
            
            # Voice configuration for Gemini TTS
            # Gemini voices work with language_code parameter to determine pronunciation
            voice_config = texttospeech.VoiceSelectionParams(
                language_code=self.language_code,  # e.g., "ru-RU"
                name=self.voice,  # e.g., "Charon", "Kore", "Fenrir", "Aoede", etc.
                model_name=self.model  # "gemini-2.5-flash-tts"
            )
            
            # Audio config: LINEAR16 at 24kHz (high quality)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=24000
            )
            
            # Synthesize speech
            logger.info(f"🎤 Synthesizing with Gemini TTS: {len(text)} chars, model={self.model}, voice={self.voice}, lang={self.language_code}")
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_config,
                audio_config=audio_config
            )
            
            logger.info(f"✅ Gemini TTS synthesis complete: {len(response.audio_content)} bytes")
            return response.audio_content
            
        except Exception as e:
            logger.error(f"❌ Error synthesizing speech with Gemini TTS: {e}")
            # Fallback to mock audio
            return self._generate_mock_audio(text)
    
    def synthesize_slide_text_gemini(self, texts: List[str], voice: str = None, 
                                     prompt: str = None) -> Tuple[str, Dict]:
        """
        Synthesize multiple text segments using Gemini TTS
        
        Args:
            texts: List of plain text segments to synthesize
            voice: Optional voice override
            prompt: Optional style prompt override
            
        Returns:
            Tuple[str, Dict]: (path to audio file, timing structure)
            
        Note: Returns sentence-level timing (NO word-level - not supported by Gemini TTS)
        """
        try:
            if self.use_mock:
                return self._synthesize_mock(texts)
            
            # Use provided voice/prompt or fallback to instance settings
            voice = voice or self.voice
            style_prompt = prompt or self.prompt
            
            # ✅ FIX: Объединяем все сегменты в один текст для единого запроса
            # Это гарантирует консистентную интонацию по всему слайду
            combined_text = " ".join([text.strip() for text in texts if text.strip()])
            
            logger.info(f"🎤 Synthesizing combined text: {len(combined_text)} chars from {len(texts)} segments")
            logger.info(f"   First 100 chars: {combined_text[:100]}...")
            
            # ✅ ОДИН запрос для всего слайда
            audio_data = self.synthesize_speech(combined_text, prompt=style_prompt)
            
            # Calculate total duration
            total_duration = self._get_audio_duration(audio_data)
            
            # ⚠️ FALLBACK TIMING: Gemini TTS doesn't provide real timing data
            # Primary timing source is now talk_track (calculated in pipeline before TTS)
            # This timing is kept as fallback for backward compatibility
            sentence_timings = []
            current_time = 0.0
            total_chars = sum(len(text.strip()) for text in texts if text.strip())
            
            for i, text in enumerate(texts):
                if not text.strip():
                    continue
                    
                # Proportional time distribution based on text length
                text_chars = len(text.strip())
                segment_duration = (text_chars / total_chars) * total_duration if total_chars > 0 else 0
                
                timing_info = {
                    "text": text.strip(),
                    "t0": current_time,
                    "t1": current_time + segment_duration,
                    "duration": segment_duration,
                    "sentence_index": i,
                    "source": "gemini_tts",
                    "precision": "estimated"  # ← Estimated (not accurate)
                }
                
                sentence_timings.append(timing_info)
                current_time += segment_duration
            
            # No need to combine - we already have one audio file
            combined_audio = audio_data
            
            # Save to file
            output_path = Path(f"/tmp/gemini_tts_{uuid.uuid4().hex[:8]}.wav")
            self._save_audio_to_file(combined_audio, output_path)
            
            # Build timing structure (compatible with pipeline)
            tts_timing = {
                "sentences": sentence_timings,
                "total_duration": total_duration,
                "model": self.model,
                "voice": voice,
                "prompt": style_prompt,
                "word_timings": [],  # ❌ Empty - not supported by Gemini TTS
                "precision": "estimated",  # ← Estimated (fallback only)
                "combined_request": True  # ✅ Flag indicating single API call for consistency
            }
            
            logger.info(f"✅ Gemini TTS synthesis complete: {len(texts)} segments combined, {total_duration:.2f}s total")
            logger.info(f"   ✅ Single API call ensures consistent voice/intonation")
            logger.info(f"   ℹ️  TTS timing is fallback only - primary timing from talk_track (calculated in pipeline)")

            
            return str(output_path), tts_timing
            
        except Exception as e:
            logger.error(f"❌ Error in synthesize_slide_text_gemini: {e}")
            return self._synthesize_mock(texts)
    
    def _get_audio_duration(self, audio_data: bytes) -> float:
        """Calculate audio duration from LINEAR16 audio data"""
        try:
            # LINEAR16: 2 bytes per sample, 24000 Hz sample rate
            sample_rate = 24000
            bytes_per_sample = 2
            num_samples = len(audio_data) / bytes_per_sample
            duration = num_samples / sample_rate
            return duration
        except Exception as e:
            logger.error(f"Error calculating audio duration: {e}")
            return 0.0
    
    def _combine_audio_segments(self, segments: List[bytes]) -> bytes:
        """Combine multiple LINEAR16 audio segments"""
        try:
            # Simply concatenate LINEAR16 data
            combined = b''.join(segments)
            return combined
        except Exception as e:
            logger.error(f"Error combining audio segments: {e}")
            return b''
    
    def _save_audio_to_file(self, audio_data: bytes, output_path: Path) -> None:
        """Save LINEAR16 audio data to WAV file"""
        try:
            with wave.open(str(output_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes (16-bit)
                wav_file.setframerate(24000)  # 24kHz
                wav_file.writeframes(audio_data)
            
            logger.debug(f"Audio saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving audio to file: {e}")
            raise
    
    def _generate_mock_audio(self, text: str) -> bytes:
        """Generate mock audio for testing (1 second of silence)"""
        logger.warning("⚠️ Using mock audio (Gemini TTS not available)")
        # 1 second of silence at 24kHz, 16-bit mono
        duration_sec = 1.0
        sample_rate = 24000
        num_samples = int(duration_sec * sample_rate)
        silence = struct.pack('<' + 'h' * num_samples, *([0] * num_samples))
        return silence
    
    def _synthesize_mock(self, texts: List[str]) -> Tuple[str, Dict]:
        """Generate mock synthesis result for testing"""
        logger.warning("⚠️ Using mock synthesis (Gemini TTS not available)")
        
        # ✅ FIX: Mock should also combine texts to simulate real behavior
        combined_text = " ".join([text.strip() for text in texts if text.strip()])
        
        # Generate audio based on combined text length (more realistic)
        # Реалистичная скорость речи: ~13-15 символов в секунду (включая пробелы)
        # Для русского языка: ~12-14 символов в секунду
        estimated_duration = max(1.0, len(combined_text) / 13.0)  # ~13 chars per sec (realistic speech speed)
        
        # Generate appropriate length of silence
        sample_rate = 24000
        num_samples = int(estimated_duration * sample_rate)
        silence = struct.pack('<' + 'h' * num_samples, *([0] * num_samples))
        
        # Save to file
        output_path = Path(f"/tmp/gemini_tts_mock_{uuid.uuid4().hex[:8]}.wav")
        self._save_audio_to_file(silence, output_path)
        
        # Mock timing structure with proportional distribution (like real version)
        sentence_timings = []
        current_time = 0.0
        total_chars = sum(len(text.strip()) for text in texts if text.strip())
        
        for i, text in enumerate(texts):
            if not text.strip():
                continue
            
            # Proportional time distribution
            text_chars = len(text.strip())
            segment_duration = (text_chars / total_chars) * estimated_duration if total_chars > 0 else 0
            
            sentence_timings.append({
                "text": text.strip(),
                "t0": current_time,
                "t1": current_time + segment_duration,
                "duration": segment_duration,
                "sentence_index": i,
                "source": "mock",
                "precision": "estimated"
            })
            current_time += segment_duration
        
        tts_timing = {
            "sentences": sentence_timings,
            "total_duration": estimated_duration,
            "model": "mock",
            "voice": "mock",
            "word_timings": [],
            "precision": "estimated",
            "combined_request": True  # ✅ Mock also simulates combined request
        }
        
        return str(output_path), tts_timing


# =============== Module-level convenience function ===============

def synthesize_slide_text_gemini(texts: List[str], **kwargs) -> Tuple[str, Dict]:
    """
    Module-level function for synthesizing text with Gemini TTS
    
    Args:
        texts: List of text segments to synthesize
        **kwargs: Optional parameters (voice, prompt, model)
        
    Returns:
        Tuple[str, Dict]: (path to audio file, timing structure)
    """
    worker = GeminiTTSWorker(
        voice=kwargs.get('voice'),
        model=kwargs.get('model'),
        prompt=kwargs.get('prompt')
    )
    return worker.synthesize_slide_text_gemini(texts)


# =============== Test function ===============

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test Gemini TTS synthesis
    test_texts = [
        "Добро пожаловать в нашу презентацию о ботанике.",
        "Сегодня мы изучим анатомию листа растения.",
        "Существует три основных типа листьев: простые, сложные и метаморфозы."
    ]
    
    logger.info("=" * 60)
    logger.info("Testing Gemini TTS Flash 2.5")
    logger.info("=" * 60)
    
    worker = GeminiTTSWorker()
    audio_path, tts_timing = worker.synthesize_slide_text_gemini(test_texts)
    
    logger.info(f"✅ Audio saved to: {audio_path}")
    logger.info(f"✅ Total duration: {tts_timing['total_duration']:.2f}s")
    logger.info(f"✅ Sentences: {len(tts_timing['sentences'])}")
    logger.info(f"⚠️ Word timings: {len(tts_timing['word_timings'])} (expected 0 for Gemini TTS)")
    logger.info(f"✅ Precision: {tts_timing['precision']}")
    
    logger.info("\nSentence timings:")
    for sent in tts_timing['sentences']:
        logger.info(f"  [{sent['t0']:.2f}s - {sent['t1']:.2f}s] {sent['text'][:50]}...")
