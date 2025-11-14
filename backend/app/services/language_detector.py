"""
Language Detection Service
Определяет язык текста на слайдах для условного перевода
"""

import logging
from typing import List, Dict, Any, Optional
import re

try:
    from langdetect import detect, detect_langs, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logging.warning("langdetect not available. Install: pip install langdetect")

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Определение языка презентации"""
    
    # Mapping ISO 639-1 codes to language names
    LANGUAGE_NAMES = {
        'en': 'English',
        'ru': 'Русский', 
        'de': 'Deutsch',
        'es': 'Español',
        'fr': 'Français',
        'it': 'Italiano',
        'pt': 'Português',
        'zh-cn': '中文',
        'ja': '日本語',
        'ko': '한국어',
        'ar': 'العربية'
    }
    
    def __init__(self):
        self.available = LANGDETECT_AVAILABLE
    
    def detect_slide_language(
        self, 
        elements: List[Dict[str, Any]], 
        min_text_length: int = 20
    ) -> str:
        """
        Определяет язык слайда по тексту элементов
        
        Args:
            elements: Список элементов слайда с полем 'text'
            min_text_length: Минимальная длина текста для определения
            
        Returns:
            ISO 639-1 код языка (например: 'en', 'ru', 'de')
        """
        if not self.available:
            logger.warning("langdetect not available, defaulting to 'en'")
            return 'en'
        
        # Собираем весь текст со слайда
        texts = []
        for elem in elements:
            text = elem.get('text', '').strip()
            # Фильтруем короткие тексты и числа
            if len(text) >= 3 and not self._is_only_numbers(text):
                texts.append(text)
        
        if not texts:
            logger.warning("No text found on slide, defaulting to 'en'")
            return 'en'
        
        combined_text = ' '.join(texts)
        
        # Нужно хотя бы min_text_length символов для надёжного определения
        if len(combined_text) < min_text_length:
            logger.warning(f"Text too short ({len(combined_text)} chars), defaulting to 'en'")
            return 'en'
        
        try:
            # Основное определение
            detected_lang = detect(combined_text)
            
            # Дополнительная проверка с вероятностями
            lang_probs = detect_langs(combined_text)
            
            # Логируем топ-3 языка
            top_langs = sorted(lang_probs, key=lambda x: x.prob, reverse=True)[:3]
            logger.info(f"Detected languages: {[(l.lang, f'{l.prob:.2f}') for l in top_langs]}")
            
            # Если уверенность низкая, предупреждаем
            if top_langs[0].prob < 0.7:
                logger.warning(f"Low confidence in language detection: {top_langs[0].prob:.2f}")
            
            return detected_lang
            
        except LangDetectException as e:
            logger.error(f"Language detection failed: {e}")
            return 'en'
    
    def detect_presentation_language(
        self, 
        slides: List[Dict[str, Any]]
    ) -> str:
        """
        Определяет язык всей презентации (по нескольким слайдам)
        
        Args:
            slides: Список слайдов с полем 'elements'
            
        Returns:
            Наиболее вероятный язык презентации
        """
        if not self.available:
            return 'en'
        
        # Собираем языки со всех слайдов
        slide_languages = []
        
        for slide in slides[:5]:  # Проверяем первые 5 слайдов
            elements = slide.get('elements', [])
            if elements:
                lang = self.detect_slide_language(elements)
                slide_languages.append(lang)
        
        if not slide_languages:
            return 'en'
        
        # Возвращаем наиболее частый язык
        from collections import Counter
        lang_counter = Counter(slide_languages)
        most_common_lang = lang_counter.most_common(1)[0][0]
        
        logger.info(f"Presentation language detected: {most_common_lang} ({self.LANGUAGE_NAMES.get(most_common_lang, most_common_lang)})")
        
        return most_common_lang
    
    def _is_only_numbers(self, text: str) -> bool:
        """Проверяет, состоит ли текст только из чисел и знаков"""
        return bool(re.match(r'^[\d\s\.\,\-\+\%\$\€\£]+$', text))
    
    def get_language_name(self, lang_code: str) -> str:
        """Возвращает название языка по коду"""
        return self.LANGUAGE_NAMES.get(lang_code, lang_code)
