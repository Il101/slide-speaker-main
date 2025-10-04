#!/usr/bin/env python3
"""
Simple Google Cloud Integration Test
"""
import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_google_cloud_integration():
    """Test Google Cloud services integration"""
    print("🚀 Testing Google Cloud Integration")
    print("=" * 50)
    
    # Test 1: Import Google Cloud modules
    try:
        import google.cloud.documentai
        import google.cloud.aiplatform
        import google.cloud.texttospeech
        import google.cloud.storage
        print("✅ Google Cloud modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Google Cloud modules: {e}")
        return False
    
    # Test 2: Test OCR provider factory
    try:
        # Set environment variables for testing
        os.environ["OCR_PROVIDER"] = "google"
        os.environ["LLM_PROVIDER"] = "gemini"
        os.environ["TTS_PROVIDER"] = "google"
        os.environ["STORAGE"] = "gcs"
        
        from app.services.provider_factory import ProviderFactory
        ocr_provider = ProviderFactory.get_ocr_provider()
        print("✅ OCR provider factory works")
    except Exception as e:
        print(f"❌ OCR provider factory failed: {e}")
        return False
    
    # Test 3: Test LLM provider factory
    try:
        llm_provider = ProviderFactory.get_llm_provider()
        print("✅ LLM provider factory works")
    except Exception as e:
        print(f"❌ LLM provider factory failed: {e}")
        return False
    
    # Test 4: Test TTS provider factory
    try:
        tts_provider = ProviderFactory.get_tts_provider()
        print("✅ TTS provider factory works")
    except Exception as e:
        print(f"❌ TTS provider factory failed: {e}")
        return False
    
    # Test 5: Test Storage provider factory
    try:
        storage_provider = ProviderFactory.get_storage_provider()
        print("✅ Storage provider factory works")
    except Exception as e:
        print(f"❌ Storage provider factory failed: {e}")
        return False
    
    # Test 6: Test mock OCR functionality
    try:
        from app.services.provider_factory import extract_elements_from_pages
        # Create a simple test image
        from PIL import Image
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img = Image.new('RGB', (800, 600), color='white')
            img.save(tmp.name)
            
            # Test OCR extraction
            elements = extract_elements_from_pages([tmp.name])
            print(f"✅ OCR extraction works: {len(elements)} slides, {len(elements[0])} elements")
            
            # Cleanup
            os.unlink(tmp.name)
    except Exception as e:
        print(f"❌ OCR extraction failed: {e}")
        return False
    
    # Test 7: Test mock LLM functionality
    try:
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
        print(f"✅ LLM planning works: {len(notes)} notes generated")
    except Exception as e:
        print(f"❌ LLM planning failed: {e}")
        return False
    
    # Test 8: Test mock TTS functionality
    try:
        from app.services.provider_factory import synthesize_slide_text_google
        
        test_texts = ["This is a test sentence for TTS."]
        audio_path, tts_words = synthesize_slide_text_google(test_texts)
        print(f"✅ TTS synthesis works: {audio_path}")
        print(f"   Sentences: {len(tts_words['sentences'])}")
    except Exception as e:
        print(f"❌ TTS synthesis failed: {e}")
        return False
    
    # Test 9: Test mock Storage functionality
    try:
        from app.services.provider_factory import upload_file_to_storage
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("Test content")
            tmp.flush()
            
            url = upload_file_to_storage(tmp.name, "test/test_file.txt")
            print(f"✅ Storage upload works: {url}")
            
            # Cleanup
            os.unlink(tmp.name)
    except Exception as e:
        print(f"❌ Storage upload failed: {e}")
        return False
    
    print("\n🎉 All Google Cloud integration tests passed!")
    return True

if __name__ == "__main__":
    success = test_google_cloud_integration()
    sys.exit(0 if success else 1)