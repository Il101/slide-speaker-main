"""
Silero Text-to-Speech Worker - Local and Free TTS
"""
import asyncio
import logging
import os
import wave
import struct
import io
import threading
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import uuid
import re
import tempfile
import numpy as np

try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available. Install torch and torchaudio for Silero TTS")

logger = logging.getLogger(__name__)

class SileroTTSWorker:
    """Worker for generating speech using Silero TTS (local, free, fast)"""
    
    # ✅ CRITICAL FIX: Cache loaded models to prevent memory exhaustion
    # Loading model for every slide causes OOM and SIGKILL
    _model_cache = {}  # {(language, model_id): model}
    _cache_lock = threading.Lock()  # Thread-safe access to cache
    
    # Supported languages and model IDs
    SUPPORTED_LANGUAGES = {
        'ru': 'v4_ru',      # v4 - latest Russian model
        'en': 'v3_en',
        'de': 'v3_de',
        'es': 'v3_es',
        'fr': 'v3_fr',
        'ua': 'v3_ua',
        'uz': 'v3_uz',
        'xal': 'v3_xal',
        'indic': 'v3_indic',
        'ba': 'v3_ba',
        'kk': 'v3_kk',
        'tt': 'v3_tt',
    }
    
    # Speakers for Russian language
    RU_SPEAKERS = ['aidar', 'baya', 'kseniya', 'xenia', 'eugene', 'random']
    EN_SPEAKERS = ['en_0', 'en_1', 'en_2', 'en_3', 'random']
    
    def __init__(self, language: str = None, speaker: str = None, sample_rate: int = None):
        self.language = language or os.getenv("SILERO_TTS_LANGUAGE", "ru")
        self.speaker = speaker or os.getenv("SILERO_TTS_SPEAKER", "aidar")
        self.sample_rate = int(sample_rate or os.getenv("SILERO_TTS_SAMPLE_RATE", "48000"))
        
        # Validate language
        if self.language not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language '{self.language}', falling back to 'ru'")
            self.language = "ru"
        
        # Check environment to prevent mock mode in production
        environment = os.getenv("ENVIRONMENT", "development")
        
        if not TORCH_AVAILABLE:
            if environment == "production":
                raise RuntimeError("PyTorch not available in production! Install torch and torchaudio")
            logger.warning("PyTorch not available, will use mock mode (development only)")
            self.use_mock = True
            self.model = None
            self.device = None
        else:
            self.use_mock = False
            self.device = torch.device('cpu')  # Use CPU for inference
            self.model = None  # Lazy loading
            logger.info(f"✅ Silero TTS initialized: language={self.language}, speaker={self.speaker}")
    
    def _load_model(self):
        """Lazy load Silero model with caching to prevent OOM"""
        if self.model is not None:
            return
        
        if self.use_mock:
            return
        
        try:
            model_id = self.SUPPORTED_LANGUAGES[self.language]
            cache_key = (self.language, model_id)
            
            # ✅ CRITICAL FIX: Thread-safe model loading with lock to prevent race condition
            with SileroTTSWorker._cache_lock:
                # Double-check cache inside lock (another thread might have loaded it)
                if cache_key in SileroTTSWorker._model_cache:
                    self.model = SileroTTSWorker._model_cache[cache_key]
                    logger.info(f"✅ Reusing cached Silero model: {model_id} (speaker: {self.speaker})")
                    return
                
                logger.info(f"Loading Silero TTS model for language '{self.language}' (first time, with lock)...")
                
                # ✅ FIX: Load model correctly according to Silero docs
                # The 'speaker' parameter in torch.hub.load should be MODEL_ID
                # The actual speaker name is used later in model.apply_tts()
                model, example_text = torch.hub.load(
                    repo_or_dir='snakers4/silero-models',
                    model='silero_tts',
                    language=self.language,
                    speaker=model_id,
                    verbose=False,
                    trust_repo=True  # ✅ Add trust_repo to avoid security warnings
                )
                
                model.to(self.device)
                
                # Store in cache for reuse
                SileroTTSWorker._model_cache[cache_key] = model
                self.model = model
                
                logger.info(f"✅ Silero TTS model loaded and cached: {model_id}, speaker: {self.speaker}, example: {example_text[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to load Silero model: {e}")
            logger.warning("Falling back to mock mode")
            self.use_mock = True
            self.model = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        if self.model is not None:
            del self.model
            if TORCH_AVAILABLE:
                torch.cuda.empty_cache()
    
    def _generate_mock_audio(self, text: str) -> bytes:
        """Generate silent audio for mock mode"""
        # Estimate duration based on text length (rough approximation)
        duration = max(1.0, len(text) * 0.1)  # ~0.1 second per character
        sample_rate = self.sample_rate
        samples = int(duration * sample_rate)
        
        # Generate silence
        audio_data = struct.pack(f'{samples}h', *[0] * samples)
        
        # Create WAV header
        wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + len(audio_data), b'WAVE', b'fmt ',
            16, 1, 1, sample_rate, sample_rate * 2, 2, 16, b'data', len(audio_data)
        )
        
        return wav_header + audio_data
    
    def _split_long_text(self, text: str, max_length: int = 800) -> list:
        """Split long text into chunks for Silero (max ~1000 chars)"""
        # ✅ CRITICAL FIX: Check if text is SSML first
        is_ssml = '<speak>' in text or '<prosody>' in text
        
        # Remove SSML tags for length calculation
        plain_text = re.sub(r'<[^>]+>', '', text)
        
        if len(plain_text) <= max_length:
            return [text]
        
        # ✅ CRITICAL: For SSML, strip tags before splitting to avoid invalid XML
        if is_ssml:
            # Remove all SSML tags, split plain text, then return as plain chunks
            # Silero can't handle partial SSML anyway
            plain_text = re.sub(r'<[^>]+>', ' ', text)
            plain_text = re.sub(r'\s+', ' ', plain_text).strip()
            
            # Split plain text by sentences
            sentences = re.split(r'([.!?]+\s+)', plain_text)
            chunks = []
            current_chunk = ""
            
            for i in range(0, len(sentences), 2):
                sentence = sentences[i]
                if i + 1 < len(sentences):
                    sentence += sentences[i + 1]  # Add punctuation
                
                # Check if adding sentence exceeds limit
                test_chunk = current_chunk + sentence
                
                if len(test_chunk) > max_length and current_chunk:
                    # Save current chunk and start new one
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += sentence
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            return chunks if chunks else [plain_text]
        
        # For plain text, split normally
        sentences = re.split(r'([.!?]+\s+)', text)
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]  # Add punctuation
            
            # Check if adding sentence exceeds limit
            test_chunk = current_chunk + sentence
            
            if len(test_chunk) > max_length and current_chunk:
                # Save current chunk and start new one
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]
    
    def _synthesize_text(self, text: str) -> bytes:
        """Synthesize single text to audio using Silero TTS"""
        if self.use_mock:
            return self._generate_mock_audio(text)
        
        try:
            # Lazy load model
            self._load_model()
            
            if self.model is None:
                return self._generate_mock_audio(text)
            
            # ✅ CRITICAL FIX: Split long text to prevent "text too long" error
            text_chunks = self._split_long_text(text, max_length=800)
            
            if len(text_chunks) > 1:
                logger.info(f"Splitting long text into {len(text_chunks)} chunks for Silero")
                # Synthesize each chunk and combine
                audio_segments = []
                for chunk in text_chunks:
                    audio_bytes = self._synthesize_single_chunk(chunk)
                    audio_segments.append(audio_bytes)
                return self._combine_audio_segments(audio_segments)
            
            # Single chunk - process normally
            return self._synthesize_single_chunk(text)
            
        except Exception as e:
            logger.error(f"Error synthesizing text with Silero: {e}")
            return self._generate_mock_audio(text)
    
    def _synthesize_single_chunk(self, text: str) -> bytes:
        """Synthesize a single chunk of text (internal method)"""
        try:
            # ✅ Check if text contains SSML and use appropriate method
            is_ssml = '<speak>' in text or '<prosody>' in text or '<break' in text

            if is_ssml:
                # ✅ Clean SSML for Silero compatibility
                # Silero supports: <speak>, <prosody rate/pitch>, <break>, <p>, <s>
                # Remove unsupported tags: <mark>, <emphasis>, <lang>, <phoneme>

                ssml_text = text

                # Remove unsupported tags but keep their content
                ssml_text = re.sub(r'<mark[^>]*/?>', '', ssml_text)  # Remove marks
                ssml_text = re.sub(r'<emphasis[^>]*>|</emphasis>', '', ssml_text)  # Remove emphasis
                ssml_text = re.sub(r'<lang[^>]*>(.*?)</lang>', r'\1', ssml_text)  # Keep content, remove lang
                ssml_text = re.sub(r'<phoneme[^>]*>(.*?)</phoneme>', r'\1', ssml_text)  # Keep content
                ssml_text = re.sub(r'xml:lang="[^"]*"', '', ssml_text)  # Remove xml:lang

                # Clean up spacing
                ssml_text = re.sub(r'\s+', ' ', ssml_text).strip()

                if not ssml_text or ssml_text == '<speak></speak>':
                    return self._generate_mock_audio(".")

                # ✅ Use Silero SSML mode
                audio = self.model.apply_tts(
                    ssml_text=ssml_text,
                    speaker=self.speaker,
                    sample_rate=self.sample_rate
                )
            else:
                # Plain text mode
                plain_text = text.strip()
                if not plain_text:
                    return self._generate_mock_audio(".")

                # ✅ Use plain text mode with proper Russian handling
                audio = self.model.apply_tts(
                    text=plain_text,
                    speaker=self.speaker,
                    sample_rate=self.sample_rate,
                    put_accent=True,  # Automatically place stress marks (Russian)
                    put_yo=True       # Properly handle 'ё' letter (Russian)
                )
            
            # Convert tensor to bytes
            audio_numpy = audio.cpu().numpy()

            # ✅ IMPROVED: Very gentle normalization to prevent metallic sound
            # Use even lower peak (0.75) for warmer, less synthetic sound
            max_val = np.abs(audio_numpy).max()
            if max_val > 0:
                # Gentle normalization with significant headroom
                audio_numpy = audio_numpy * (0.75 / max_val)

            # Optional: Apply very light low-pass filter to reduce high-frequency artifacts
            # This helps eliminate metallic "ringing" sound
            # Simple moving average for smoothing
            if len(audio_numpy) > 3:
                kernel_size = 3
                kernel = np.ones(kernel_size) / kernel_size
                audio_numpy = np.convolve(audio_numpy, kernel, mode='same')

            # Convert to int16 with very soft scaling
            audio_int16 = (audio_numpy * 32767).astype('int16')
            
            # Create WAV
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            return wav_io.getvalue()
            
        except Exception as e:
            logger.error(f"Error synthesizing chunk with Silero: {e}")
            return self._generate_mock_audio(text)
    
    def _split_into_sentences(self, texts: List[str]) -> List[str]:
        """Split texts into sentences"""
        sentences = []
        for text in texts:
            # Split by sentence-ending punctuation
            parts = re.split(r'([.!?]+)', text)
            
            current_sentence = ""
            for i, part in enumerate(parts):
                if part.strip():
                    current_sentence += part
                    # If it's punctuation and not the last element
                    if re.match(r'[.!?]+', part) and current_sentence.strip():
                        sentences.append(current_sentence.strip())
                        current_sentence = ""
            
            # Add remaining text as sentence
            if current_sentence.strip():
                sentences.append(current_sentence.strip())
        
        return sentences if sentences else [" ".join(texts)]
    
    def _estimate_duration(self, text: str, audio_bytes: bytes) -> float:
        """Estimate audio duration from WAV bytes"""
        try:
            with io.BytesIO(audio_bytes) as wav_io:
                with wave.open(wav_io, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    duration = frames / float(rate)
                    return duration
        except Exception as e:
            logger.warning(f"Could not estimate duration: {e}")
            # Fallback estimation
            return max(1.0, len(text) * 0.1)
    
    def _combine_audio_segments(self, audio_segments: List[bytes]) -> bytes:
        """Combine multiple WAV audio segments into one"""
        if not audio_segments:
            return self._generate_mock_audio("")
        
        if len(audio_segments) == 1:
            return audio_segments[0]
        
        try:
            all_frames = []
            params = None
            
            for audio_bytes in audio_segments:
                with io.BytesIO(audio_bytes) as wav_io:
                    with wave.open(wav_io, 'rb') as wav_file:
                        if params is None:
                            params = wav_file.getparams()
                        all_frames.append(wav_file.readframes(wav_file.getnframes()))
            
            # Combine all frames
            combined_io = io.BytesIO()
            with wave.open(combined_io, 'wb') as wav_out:
                wav_out.setparams(params)
                for frames in all_frames:
                    wav_out.writeframes(frames)
            
            return combined_io.getvalue()
            
        except Exception as e:
            logger.error(f"Error combining audio segments: {e}")
            return audio_segments[0] if audio_segments else self._generate_mock_audio("")
    
    def synthesize_slide_text_google(self, texts: List[str], **kwargs) -> Tuple[str, Dict]:
        """
        Synthesize speech for slide texts (compatible with Google TTS interface)
        
        Args:
            texts: List of texts to synthesize
            **kwargs: Additional parameters (ignored for Silero)
            
        Returns:
            Tuple[str, Dict]: (path to audio file, timing structure)
            {
              "audio": "/path/to/audio.wav",
              "sentences": [
                {"text": "sentence 1", "t0": 0.00, "t1": 1.25},
                {"text": "sentence 2", "t0": 1.30, "t1": 3.10}
              ],
              "words": []
            }
        """
        try:
            if not texts:
                raise ValueError("No texts provided for synthesis")
            
            # ✅ SIMPLIFIED: Remove <mark> tags, keep SSML structure
            # If text has SSML tags (<speak>, <prosody>, <break>) - keep them for quality!
            # Only remove <mark> tags that break sentence splitting
            
            segments_to_synthesize = []
            plain_for_timing = []
            
            for text in texts:
                # Remove only <mark> tags
                cleaned = re.sub(r'<mark[^>]*/?>', '', text)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                
                # Check if this is SSML or plain text
                has_ssml = '<speak>' in cleaned or '<prosody>' in cleaned or '<break' in cleaned
                
                if has_ssml:
                    # Keep SSML as-is for quality (Silero will handle it)
                    segments_to_synthesize.append(cleaned)
                    # Extract plain text for duration calculation AND timing display
                    plain = re.sub(r'<[^>]+>', '', cleaned).strip()
                    if plain:  # Only add if there's actual text content
                        plain_for_timing.append(plain)
                    else:
                        # If empty after removing tags, skip this segment
                        segments_to_synthesize.pop()
                else:
                    # Plain text - use as-is (don't split for now to preserve SSML benefits)
                    plain = cleaned.strip()
                    if plain:
                        segments_to_synthesize.append(plain)
                        plain_for_timing.append(plain)
            
            logger.info(f"Synthesizing {len(segments_to_synthesize)} segments with Silero TTS (from {len(texts)} inputs)")
            
            # Generate audio for each segment
            audio_segments = []
            sentence_timings = []
            current_time = 0.0
            
            for i, (segment, plain_text) in enumerate(zip(segments_to_synthesize, plain_for_timing)):
                # Synthesize segment (with SSML if present)
                audio_bytes = self._synthesize_text(segment)
                audio_segments.append(audio_bytes)
                
                # Estimate duration
                duration = self._estimate_duration(plain_text, audio_bytes)
                
                # Store timing (use plain text for display)
                sentence_timings.append({
                    "text": plain_text,
                    "t0": current_time,
                    "t1": current_time + duration
                })
                
                current_time += duration
                
                # Add small pause between segments (200ms)
                if i < len(segments_to_synthesize) - 1:
                    pause_duration = 0.2
                    silence = self._generate_mock_audio(".")  # Short silence
                    audio_segments.append(silence[:int(self.sample_rate * pause_duration * 2)])
                    current_time += pause_duration
            
            # Combine all audio segments
            combined_audio = self._combine_audio_segments(audio_segments)
            
            # Save to temporary file
            audio_path = Path(tempfile.gettempdir()) / f"silero_tts_{uuid.uuid4().hex[:8]}.wav"
            with open(audio_path, 'wb') as f:
                f.write(combined_audio)
            
            # Create timing structure
            tts_words = {
                "audio": str(audio_path),
                "sentences": sentence_timings,
                "words": []  # Silero doesn't provide word-level timing
            }
            
            logger.info(f"✅ Generated Silero TTS: {audio_path}, {len(sentence_timings)} sentences, {current_time:.2f}s")
            
            # ✅ CRITICAL: Force memory cleanup after TTS to prevent accumulation
            import gc
            del audio_segments
            del combined_audio
            gc.collect()
            if TORCH_AVAILABLE:
                torch.cuda.empty_cache()
            
            return str(audio_path), tts_words
            
        except Exception as e:
            logger.error(f"Error synthesizing slide text with Silero: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback to mock
            return self._synthesize_mock(texts)
    
    def _synthesize_mock(self, texts: List[str]) -> Tuple[str, Dict]:
        """Generate mock audio and timings for fallback"""
        combined_text = " ".join(texts)
        mock_audio = self._generate_mock_audio(combined_text)
        
        # Save to file
        audio_path = Path(tempfile.gettempdir()) / f"mock_silero_{uuid.uuid4().hex[:8]}.wav"
        with open(audio_path, 'wb') as f:
            f.write(mock_audio)
        
        # Estimate total duration
        duration = max(1.0, len(combined_text) * 0.1)
        
        # Create mock timings
        sentences = self._split_into_sentences(texts)
        sentence_timings = []
        time_per_sentence = duration / len(sentences) if sentences else duration
        
        for i, sentence in enumerate(sentences):
            sentence_timings.append({
                "text": sentence,
                "t0": i * time_per_sentence,
                "t1": (i + 1) * time_per_sentence
            })
        
        tts_words = {
            "audio": str(audio_path),
            "sentences": sentence_timings,
            "words": []
        }
        
        return str(audio_path), tts_words


# Example usage
if __name__ == "__main__":
    # Test Silero TTS
    worker = SileroTTSWorker(language="ru", speaker="aidar")
    
    test_texts = [
        "Привет, мир!",
        "Это тест Silero TTS.",
        "Локальный синтез речи работает отлично."
    ]
    
    audio_path, timings = worker.synthesize_slide_text_google(test_texts)
    print(f"Generated audio: {audio_path}")
    print(f"Timings: {timings}")
