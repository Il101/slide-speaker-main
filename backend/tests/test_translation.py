"""
Tests for Language Detection and Translation Services
"""
import pytest
import os
from app.services.language_detector import LanguageDetector
from app.services.translation_service import TranslationService


@pytest.fixture
def language_detector():
    """Create language detector instance"""
    return LanguageDetector()


@pytest.fixture
def translation_service():
    """Create translation service instance"""
    return TranslationService()


class TestLanguageDetection:
    """Test language detection functionality"""
    
    def test_detect_german_slide(self, language_detector):
        """Test detection of German language"""
        elements = [
            {"text": "Aufbau und Architektur der Pflanzen"},
            {"text": "Funktionen der Wurzel"}
        ]
        
        lang = language_detector.detect_slide_language(elements)
        assert lang == 'de'
    
    def test_detect_russian_slide(self, language_detector):
        """Test detection of Russian language"""
        elements = [
            {"text": "Строение и архитектура растений"},
            {"text": "Функции корня"}
        ]
        
        lang = language_detector.detect_slide_language(elements)
        assert lang == 'ru'
    
    def test_detect_english_slide(self, language_detector):
        """Test detection of English language"""
        elements = [
            {"text": "Plant Structure and Architecture"},
            {"text": "Functions of the Root"}
        ]
        
        lang = language_detector.detect_slide_language(elements)
        assert lang == 'en'
    
    def test_detect_presentation_language(self, language_detector):
        """Test detection of entire presentation language"""
        slides = [
            {"elements": [{"text": "Aufbau der Pflanzen"}]},
            {"elements": [{"text": "Funktionen der Wurzel"}]},
            {"elements": [{"text": "Photosynthese"}]}
        ]
        
        lang = language_detector.detect_presentation_language(slides)
        assert lang == 'de'
    
    def test_empty_elements_default_to_english(self, language_detector):
        """Test that empty elements default to English"""
        elements = []
        
        lang = language_detector.detect_slide_language(elements)
        assert lang == 'en'
    
    def test_short_text_defaults_to_english(self, language_detector):
        """Test that too short text defaults to English"""
        elements = [{"text": "Hi"}]
        
        lang = language_detector.detect_slide_language(elements)
        assert lang == 'en'
    
    def test_get_language_name(self, language_detector):
        """Test language name retrieval"""
        assert language_detector.get_language_name('de') == 'Deutsch'
        assert language_detector.get_language_name('ru') == 'Русский'
        assert language_detector.get_language_name('en') == 'English'
        assert language_detector.get_language_name('unknown') == 'unknown'


class TestTranslationService:
    """Test translation service functionality"""
    
    def test_is_translation_needed_different_languages(self, translation_service):
        """Test that translation is needed for different languages"""
        # Skip if translation service is not available
        if not translation_service.translation_enabled:
            pytest.skip("Translation service not available (credentials not set)")
        
        # Different languages - translation needed
        assert translation_service.is_translation_needed('de', 'ru') == True
        assert translation_service.is_translation_needed('en', 'de') == True
    
    def test_is_translation_needed_same_language(self, translation_service):
        """Test that translation is not needed for same language"""
        # Skip if translation service is not available
        if not translation_service.translation_enabled:
            pytest.skip("Translation service not available (credentials not set)")
        
        # Same languages - translation not needed
        assert translation_service.is_translation_needed('ru', 'ru') == False
        assert translation_service.is_translation_needed('en', 'en') == False
    
    def test_normalize_language_code(self, translation_service):
        """Test language code normalization"""
        assert translation_service._normalize_language_code('de-DE') == 'de'
        assert translation_service._normalize_language_code('en-US') == 'en'
        assert translation_service._normalize_language_code('de') == 'de'
        assert translation_service._normalize_language_code('') == 'en'
        assert translation_service._normalize_language_code(None) == 'en'
    
    def test_translate_elements_same_language(self, translation_service):
        """Test that elements are not translated when languages match"""
        elements = [
            {"text": "Test text"},
            {"text": "Another test"}
        ]
        
        result = translation_service.translate_elements(elements, 'en', 'en')
        
        # Elements should have translation fields
        assert result[0]['text_original'] == "Test text"
        assert result[0]['text_translated'] == "Test text"
        assert result[0]['language_original'] == 'en'
        assert result[0]['language_target'] == 'en'
    
    @pytest.mark.skipif(
        not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
        reason="Google credentials not available"
    )
    def test_translate_elements_different_languages(self, translation_service):
        """Test actual translation between different languages"""
        # Skip if translation service is not available
        if not translation_service.translation_enabled:
            pytest.skip("Translation service not available")
        
        elements = [
            {"text": "Aufbau der Pflanzen"}
        ]
        
        result = translation_service.translate_elements(elements, 'de', 'ru')
        
        # Check that translation was applied
        assert result[0]['text_original'] == "Aufbau der Pflanzen"
        assert result[0]['language_original'] == 'de'
        assert result[0]['language_target'] == 'ru'
        # Translation should be different from original (in Russian)
        assert result[0]['text_translated'] != "Aufbau der Pflanzen"
        assert len(result[0]['text_translated']) > 0
    
    @pytest.mark.skipif(
        not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
        reason="Google credentials not available"
    )
    def test_translate_text(self, translation_service):
        """Test single text translation"""
        # Skip if translation service is not available
        if not translation_service.translation_enabled:
            pytest.skip("Translation service not available")
        
        text = "Aufbau der Pflanzen"
        result = translation_service.translate_text(text, 'de', 'ru')
        
        # Check that translation happened
        assert result != text
        assert len(result) > 0
    
    def test_translate_elements_empty_list(self, translation_service):
        """Test translation of empty elements list"""
        elements = []
        
        result = translation_service.translate_elements(elements, 'de', 'ru')
        
        assert result == []
    
    def test_translate_elements_with_empty_text(self, translation_service):
        """Test translation of elements with empty text"""
        elements = [
            {"text": ""},
            {"text": "Valid text"}
        ]
        
        result = translation_service.translate_elements(elements, 'en', 'en')
        
        # First element should have empty translations
        assert result[0]['text_original'] == ""
        assert result[0]['text_translated'] == ""
        
        # Second element should be processed
        assert result[1]['text_original'] == "Valid text"
        assert result[1]['text_translated'] == "Valid text"


class TestIntegration:
    """Integration tests for language detection + translation"""
    
    def test_workflow_german_to_russian(self, language_detector, translation_service):
        """Test complete workflow: detect German, translate to Russian"""
        # Step 1: Detect language
        slides = [
            {"elements": [
                {"text": "Aufbau und Architektur der Pflanzen"},
                {"text": "Funktionen der Wurzel"}
            ]}
        ]
        
        detected_lang = language_detector.detect_presentation_language(slides)
        assert detected_lang == 'de'
        
        # Step 2: Check if translation is needed
        target_lang = 'ru'
        needs_translation = translation_service.is_translation_needed(detected_lang, target_lang)
        
        # Step 3: Apply translation if needed
        if needs_translation and translation_service.translation_enabled:
            elements = slides[0]['elements']
            translated = translation_service.translate_elements(elements, detected_lang, target_lang)
            
            # Verify translation fields exist
            for elem in translated:
                assert 'text_original' in elem
                assert 'text_translated' in elem
                assert 'language_original' in elem
                assert 'language_target' in elem
                assert elem['language_original'] == 'de'
                assert elem['language_target'] == 'ru'
        else:
            # If translation not available, ensure fallback behavior
            elements = slides[0]['elements']
            for elem in elements:
                if 'text_original' not in elem:
                    elem['text_original'] = elem.get('text', '')
                    elem['text_translated'] = elem.get('text', '')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
