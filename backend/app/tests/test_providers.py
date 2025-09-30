"""
Test suite for Slide Speaker backend
"""
import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestProviderFactory:
    """Test provider factory functionality"""
    
    def test_ocr_provider_factory(self):
        """Test OCR provider factory"""
        from app.services.provider_factory import ProviderFactory
        
        # Test with mock provider
        os.environ["OCR_PROVIDER"] = "mock"
        provider = ProviderFactory.get_ocr_provider()
        assert provider is not None
        
        # Test fallback
        os.environ["OCR_PROVIDER"] = "invalid"
        provider = ProviderFactory.get_ocr_provider()
        assert provider is not None
    
    def test_llm_provider_factory(self):
        """Test LLM provider factory"""
        from app.services.provider_factory import ProviderFactory
        
        # Test with mock provider
        os.environ["LLM_PROVIDER"] = "mock"
        provider = ProviderFactory.get_llm_provider()
        assert provider is not None
        
        # Test fallback
        os.environ["LLM_PROVIDER"] = "invalid"
        provider = ProviderFactory.get_llm_provider()
        assert provider is not None
    
    def test_tts_provider_factory(self):
        """Test TTS provider factory"""
        from app.services.provider_factory import ProviderFactory
        
        # Test with mock provider
        os.environ["TTS_PROVIDER"] = "mock"
        provider = ProviderFactory.get_tts_provider()
        assert provider is not None
        
        # Test fallback
        os.environ["TTS_PROVIDER"] = "invalid"
        provider = ProviderFactory.get_tts_provider()
        assert provider is not None
    
    def test_storage_provider_factory(self):
        """Test Storage provider factory"""
        from app.services.provider_factory import ProviderFactory
        
        # Test with mock provider
        os.environ["STORAGE"] = "mock"
        provider = ProviderFactory.get_storage_provider()
        assert provider is not None
        
        # Test fallback
        os.environ["STORAGE"] = "invalid"
        provider = ProviderFactory.get_storage_provider()
        assert provider is not None

class TestGoogleCloudIntegration:
    """Test Google Cloud integration"""
    
    def test_google_cloud_imports(self):
        """Test that Google Cloud modules can be imported"""
        try:
            import google.cloud.documentai
            import google.cloud.aiplatform
            import google.cloud.texttospeech
            import google.cloud.storage
            assert True
        except ImportError:
            pytest.skip("Google Cloud modules not available")
    
    def test_mock_ocr_extraction(self):
        """Test mock OCR extraction"""
        from app.services.provider_factory import extract_elements_from_pages
        
        # Create a temporary PNG file
        try:
            from PIL import Image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img = Image.new('RGB', (100, 100), color='white')
                img.save(tmp.name)
                
                try:
                    elements = extract_elements_from_pages([tmp.name])
                    assert len(elements) > 0
                    assert len(elements[0]) > 0
                finally:
                    os.unlink(tmp.name)
        except ImportError:
            # If PIL is not available, skip this test
            pytest.skip("PIL not available")
    
    def test_mock_llm_planning(self):
        """Test mock LLM planning"""
        from app.services.provider_factory import plan_slide_with_gemini
        
        test_elements = [
            {
                "id": "elem_1",
                "type": "heading",
                "text": "Test Heading",
                "bbox": [100, 50, 600, 80],
                "confidence": 0.95
            }
        ]
        
        notes = plan_slide_with_gemini(test_elements)
        assert len(notes) > 0
        assert "text" in notes[0]
    
    def test_mock_tts_synthesis(self):
        """Test mock TTS synthesis"""
        from app.services.provider_factory import synthesize_slide_text_google
        
        test_texts = ["This is a test sentence."]
        audio_path, tts_words = synthesize_slide_text_google(test_texts)
        
        assert isinstance(audio_path, str)
        assert len(audio_path) > 0
        assert "sentences" in tts_words
        assert len(tts_words["sentences"]) > 0
    
    def test_mock_storage_upload(self):
        """Test mock storage upload"""
        from app.services.provider_factory import upload_file_to_storage
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("test content")
            tmp.flush()
            
            try:
                url = upload_file_to_storage(tmp.name, "test/test_file.txt")
                assert isinstance(url, str)
                assert len(url) > 0
            finally:
                os.unlink(tmp.name)

class TestConfiguration:
    """Test configuration management"""
    
    def test_settings_import(self):
        """Test that settings can be imported"""
        from app.core.config import settings
        assert settings is not None
        assert hasattr(settings, 'OCR_PROVIDER')
        assert hasattr(settings, 'LLM_PROVIDER')
        assert hasattr(settings, 'TTS_PROVIDER')
        assert hasattr(settings, 'STORAGE')
    
    def test_environment_variables(self):
        """Test environment variable handling"""
        from app.core.config import settings
        
        # Test default values
        assert settings.OCR_PROVIDER is not None
        assert settings.LLM_PROVIDER is not None
        assert settings.TTS_PROVIDER is not None
        assert settings.STORAGE is not None

if __name__ == "__main__":
    pytest.main([__file__])