"""
Provider Factory for Google Cloud Services Integration
"""
import logging
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add workers directory to Python path for imports
current_dir = Path(__file__).parent
workers_dir = current_dir.parent.parent / "workers"
if str(workers_dir) not in sys.path:
    sys.path.insert(0, str(workers_dir))

from app.core.config import settings

logger = logging.getLogger(__name__)

class ProviderFactory:
    """Factory for creating provider instances based on configuration"""
    
    @staticmethod
    def get_ocr_provider():
        """Get OCR provider based on OCR_PROVIDER setting"""
        provider = settings.OCR_PROVIDER.lower()
        
        if provider == "google":
            try:
                from workers.ocr_google import GoogleDocumentAIWorker
                return GoogleDocumentAIWorker(
                    project_id=settings.GCP_PROJECT_ID,
                    location=settings.GCP_LOCATION,
                    processor_id=settings.GCP_DOC_AI_PROCESSOR_ID
                )
            except ImportError as e:
                logger.error(f"Failed to import Google OCR provider: {e}")
                return ProviderFactory._get_fallback_ocr()
        elif provider == "vision":
            try:
                from workers.ocr_vision import VisionOCRWorker
                return VisionOCRWorker()
            except ImportError as e:
                logger.error(f"Failed to import Vision OCR provider: {e}")
                return ProviderFactory._get_fallback_ocr()
        elif provider == "enhanced_vision":
            try:
                from workers.ocr_vision_enhanced import EnhancedVisionOCRWorker
                return EnhancedVisionOCRWorker()
            except ImportError as e:
                logger.error(f"Failed to import Enhanced Vision OCR provider: {e}")
                return ProviderFactory._get_fallback_ocr()
        elif provider == "paddle":
            # Use existing PaddleOCR implementation
            return ProviderFactory._get_paddle_provider()
        else:
            logger.warning(f"Unknown OCR provider: {provider}, using fallback")
            return ProviderFactory._get_fallback_ocr()
    
    @staticmethod
    def get_llm_provider():
        """Get LLM provider based on LLM_PROVIDER setting"""
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "gemini":
            try:
                from workers.llm_gemini import GeminiLLMWorker
                return GeminiLLMWorker(
                    project_id=settings.GCP_PROJECT_ID,
                    location=settings.GEMINI_LOCATION,
                    model=settings.GEMINI_MODEL
                )
            except ImportError as e:
                logger.error(f"Failed to import Gemini LLM provider: {e}")
                return ProviderFactory._get_fallback_llm()
        elif provider == "openai":
            # Use existing OpenAI implementation
            return ProviderFactory._get_openai_provider()
        elif provider == "openrouter":
            try:
                from workers.llm_openrouter import OpenRouterLLMWorker
                return OpenRouterLLMWorker(
                    api_key=settings.OPENROUTER_API_KEY,
                    model=settings.OPENROUTER_MODEL,
                    base_url=settings.OPENROUTER_BASE_URL
                )
            except ImportError as e:
                logger.error(f"Failed to import OpenRouter LLM provider: {e}")
                return ProviderFactory._get_fallback_llm()
        elif provider == "anthropic":
            # Use existing Anthropic implementation
            return ProviderFactory._get_anthropic_provider()
        elif provider == "ollama":
            # Use existing Ollama implementation
            return ProviderFactory._get_ollama_provider()
        else:
            logger.warning(f"Unknown LLM provider: {provider}, using fallback")
            return ProviderFactory._get_fallback_llm()
    
    @staticmethod
    def get_tts_provider():
        """Get TTS provider based on TTS_PROVIDER setting"""
        provider = settings.TTS_PROVIDER.lower()
        
        if provider == "google":
            try:
                from workers.tts_google import GoogleTTSWorker
                return GoogleTTSWorker(
                    voice=settings.GOOGLE_TTS_VOICE,
                    speaking_rate=settings.GOOGLE_TTS_SPEAKING_RATE,
                    pitch=settings.GOOGLE_TTS_PITCH
                )
            except ImportError as e:
                logger.error(f"Failed to import Google TTS provider: {e}")
                return ProviderFactory._get_fallback_tts()
        elif provider == "azure":
            # Use existing Azure TTS implementation
            return ProviderFactory._get_azure_tts_provider()
        elif provider == "mock":
            # Use mock TTS implementation
            return ProviderFactory._get_mock_tts_provider()
        else:
            logger.warning(f"Unknown TTS provider: {provider}, using fallback")
            return ProviderFactory._get_fallback_tts()
    
    @staticmethod
    def get_image_recognition_provider():
        """Get image recognition provider (fallback only)."""
        return ProviderFactory._get_fallback_image_recognition()
    
    @staticmethod
    def get_storage_provider():
        """Get storage provider based on STORAGE setting"""
        provider = settings.STORAGE.lower()
        
        if provider == "gcs":
            try:
                from app.storage_gcs import GoogleCloudStorageProvider
                return GoogleCloudStorageProvider(
                    bucket_name=settings.GCS_BUCKET,
                    base_url=settings.GCS_BASE_URL
                )
            except ImportError as e:
                logger.error(f"Failed to import Google Cloud Storage provider: {e}")
                return ProviderFactory._get_fallback_storage()
        elif provider == "minio":
            # Use existing MinIO/S3 implementation
            return ProviderFactory._get_minio_provider()
        else:
            logger.warning(f"Unknown storage provider: {provider}, using fallback")
            return ProviderFactory._get_fallback_storage()
    
    # Fallback implementations
    @staticmethod
    def _get_fallback_ocr():
        """Fallback OCR provider"""
        class FallbackOCR:
            def extract_elements_from_pages(self, png_paths, **kwargs):
                # Return placeholder elements
                results = []
                for png_path in png_paths:
                    from PIL import Image
                    with Image.open(png_path) as img:
                        orig_width, orig_height = img.size
                    results.append([{
                        "id": "slide_area",
                        "type": "placeholder",
                        "text": "Slide content area",
                        "bbox": [0, 0, orig_width, orig_height],
                        "confidence": 1.0,
                        "source": "fallback"
                    }])
                return results
        return FallbackOCR()
    
    @staticmethod
    def _get_fallback_llm():
        """Fallback LLM provider"""
        class FallbackLLM:
            def plan_slide_with_gemini(self, elements, **kwargs):
                # Return mock notes
                notes = []
                headings = [e for e in elements if e.get('type') == 'heading']
                if headings:
                    notes.append({
                        "text": f"Let's discuss {headings[0]['text']}",
                        "targetId": headings[0]['id']
                    })
                else:
                    notes.append({
                        "text": "This slide contains important information",
                        "targetId": elements[0]['id'] if elements else "slide_area"
                    })
                return notes
        return FallbackLLM()
    
    @staticmethod
    def _get_fallback_tts():
        """Fallback TTS provider"""
        class FallbackTTS:
            def synthesize_slide_text_google(self, texts, **kwargs):
                import uuid
                import wave
                import struct
                import io
                
                # Generate mock audio
                duration = max(1.0, sum(len(text) for text in texts) * 0.1)
                sample_rate = 22050
                samples = int(duration * sample_rate)
                audio_data = struct.pack(f'{samples}h', *[0] * samples)
                
                wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
                    b'RIFF', 36 + len(audio_data), b'WAVE', b'fmt ',
                    16, 1, 1, sample_rate, sample_rate * 2, 2, 16, b'data', len(audio_data)
                )
                
                audio_path = f"/tmp/mock_{uuid.uuid4().hex[:8]}.wav"
                Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(audio_path, 'wb') as f:
                    f.write(wav_header + audio_data)
                
                tts_words = {
                    "audio": audio_path,
                    "sentences": [{"text": text, "t0": 0.0, "t1": duration} for text in texts],
                    "words": []
                }
                
                return audio_path, tts_words
        return FallbackTTS()
    
    @staticmethod
    def _get_fallback_image_recognition():
        """Fallback image recognition provider"""
        class FallbackImageRecognition:
            def analyze_slide_images(self, png_path, slide_number):
                # Return empty list for fallback
                return []
        return FallbackImageRecognition()
    
    @staticmethod
    def _get_fallback_storage():
        """Fallback storage provider"""
        class FallbackStorage:
            def upload_file(self, local_path, remote_key):
                return f"/assets/fallback/{remote_key}"
            
            def upload_bytes(self, data, remote_key, content_type=None):
                return f"/assets/fallback/{remote_key}"
        return FallbackStorage()
    
    # Legacy provider implementations
    @staticmethod
    def _get_easyocr_provider():
        """Get EasyOCR provider with real OCR functionality"""
        class EasyOCRProvider:
            def __init__(self):
                try:
                    import easyocr
                    import cv2
                    self.easyocr_reader = easyocr.Reader(['en', 'ru'])
                    self.cv2 = cv2
                    self.use_real_ocr = True
                    logger.info("EasyOCR provider initialized successfully")
                except ImportError as e:
                    logger.error(f"Failed to import EasyOCR: {e}")
                    self.use_real_ocr = False
            
            def extract_elements_from_pages(self, png_paths, **kwargs):
                """Extract real text from slide images using EasyOCR"""
                if not self.use_real_ocr:
                    return ProviderFactory._get_fallback_ocr().extract_elements_from_pages(png_paths)
                
                results = []
                for png_path in png_paths:
                    try:
                        # Load image
                        image = self.cv2.imread(png_path)
                        if image is None:
                            logger.warning(f"Could not load image: {png_path}")
                            continue
                        
                        image_rgb = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2RGB)
                        
                        # Run OCR
                        ocr_results = self.easyocr_reader.readtext(image_rgb)
                        
                        # Convert to elements format
                        elements = []
                        for i, (bbox, text, confidence) in enumerate(ocr_results):
                            if confidence > 0.5:  # Filter low confidence results
                                # Convert bbox to [x, y, width, height] format
                                x_coords = [point[0] for point in bbox]
                                y_coords = [point[1] for point in bbox]
                                x_min, x_max = min(x_coords), max(x_coords)
                                y_min, y_max = min(y_coords), max(y_coords)
                                
                                element = {
                                    "id": f"element_{i}",
                                    "type": "paragraph",
                                    "text": text.strip(),
                                    "bbox": [int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min)],
                                    "confidence": confidence
                                }
                                elements.append(element)
                        
                        logger.info(f"EasyOCR extracted {len(elements)} elements from {png_path}")
                        results.append(elements)
                        
                    except Exception as e:
                        logger.error(f"Error processing {png_path} with EasyOCR: {e}")
                        # Fallback to empty elements
                        results.append([])
                
                return results
        
        return EasyOCRProvider()
    
    @staticmethod
    def _get_paddle_provider():
        """Get PaddleOCR provider (placeholder)"""
        # This would integrate with existing PaddleOCR implementation
        return ProviderFactory._get_fallback_ocr()
    
    @staticmethod
    def _get_openai_provider():
        """Get OpenAI provider (placeholder)"""
        # This would integrate with existing OpenAI implementation
        return ProviderFactory._get_fallback_llm()
    
    @staticmethod
    def _get_anthropic_provider():
        """Get Anthropic provider (placeholder)"""
        # This would integrate with existing Anthropic implementation
        return ProviderFactory._get_fallback_llm()
    
    @staticmethod
    def _get_ollama_provider():
        """Get Ollama provider (placeholder)"""
        # This would integrate with existing Ollama implementation
        return ProviderFactory._get_fallback_llm()
    
    @staticmethod
    def _get_azure_tts_provider():
        """Get Azure TTS provider (placeholder)"""
        # This would integrate with existing Azure TTS implementation
        return ProviderFactory._get_fallback_tts()
    
    @staticmethod
    def _get_mock_tts_provider():
        """Get mock TTS provider"""
        return ProviderFactory._get_fallback_tts()
    
    @staticmethod
    def _get_minio_provider():
        """Get MinIO provider (placeholder)"""
        # This would integrate with existing MinIO/S3 implementation
        return ProviderFactory._get_fallback_storage()

# Integration functions for the main pipeline
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception))
)
def extract_elements_from_pages(png_paths: List[str], **kwargs) -> List[List[Dict]]:
    """Extract elements from pages using configured OCR provider"""
    provider = ProviderFactory.get_ocr_provider()
    return provider.extract_elements_from_pages(png_paths, **kwargs)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception))
)
def plan_slide_with_gemini(elements: List[Dict], **kwargs) -> List[Dict]:
    """Plan slide using configured LLM provider"""
    provider = ProviderFactory.get_llm_provider()
    return provider.plan_slide_with_gemini(elements, **kwargs)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception))
)
def synthesize_slide_text_google(texts: List[str], **kwargs) -> Tuple[str, Dict]:
    """Synthesize text using configured TTS provider"""
    provider = ProviderFactory.get_tts_provider()
    return provider.synthesize_slide_text_google(texts, **kwargs)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception))
)
def generate_lecture_text_with_ssml(elements: List[Dict], **kwargs) -> str:
    """Generate lecture text with SSML markup using configured LLM provider"""
    from workers.llm_openrouter_ssml import OpenRouterLLMWorkerSSML
    worker = OpenRouterLLMWorkerSSML()
    return worker.generate_lecture_text_with_ssml(elements, **kwargs)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception))
)
def synthesize_slide_text_google_ssml(ssml_texts: List[str], **kwargs) -> Tuple[str, Dict]:
    """Synthesize SSML text using configured TTS provider"""
    from workers.tts_google_ssml import GoogleTTSWorkerSSML
    worker = GoogleTTSWorkerSSML()
    return worker.synthesize_slide_text_google_ssml(ssml_texts, **kwargs)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception))
)
def analyze_slide_images(png_path: str, slide_number: int) -> List[Dict]:
    """Analyze images on slide using hybrid image recognition"""
    provider = ProviderFactory.get_image_recognition_provider()
    return provider.analyze_slide_images(png_path, slide_number)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception))
)
def upload_file_to_storage(local_path: str, remote_key: str) -> str:
    """Upload file using configured storage provider"""
    provider = ProviderFactory.get_storage_provider()
    return provider.upload_file(local_path, remote_key)