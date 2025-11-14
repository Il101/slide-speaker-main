"""
Translation Service with Google Translate API
Переводит элементы слайдов с одного языка на другой
"""

import logging
import os
from typing import List, Dict, Any, Optional
from functools import lru_cache

try:
    from google.cloud import translate_v2 as translate
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False
    logging.warning("Google Translate not available. Install: pip install google-cloud-translate>=3.0")

logger = logging.getLogger(__name__)


class TranslationService:
    """Сервис перевода текста через Google Translate API"""
    
    def __init__(self):
        """
        Инициализация Google Translate клиента
        
        Требует переменную окружения:
        - GOOGLE_APPLICATION_CREDENTIALS: путь к JSON ключу
        """
        self.available = GOOGLE_TRANSLATE_AVAILABLE
        self.client = None
        self.translation_enabled = os.getenv('TRANSLATION_ENABLED', 'true').lower() == 'true'
        
        if not self.available:
            logger.warning("Google Translate library not available")
            return
        
        # Проверяем credentials
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set, translation will be disabled")
            self.translation_enabled = False
            return
        
        try:
            self.client = translate.Client()
            logger.info("✅ Google Translate client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Translate client: {e}")
            self.translation_enabled = False
    
    def is_translation_needed(
        self, 
        source_lang: str, 
        target_lang: str
    ) -> bool:
        """
        Проверяет, нужен ли перевод
        
        Args:
            source_lang: Язык источника
            target_lang: Целевой язык
            
        Returns:
            True если языки разные и перевод включён
        """
        # Если перевод отключен
        if not self.translation_enabled or not self.available or not self.client:
            return False
        
        # Нормализуем языковые коды
        source_normalized = self._normalize_language_code(source_lang)
        target_normalized = self._normalize_language_code(target_lang)
        
        # Если языки совпадают - перевод не нужен
        if source_normalized == target_normalized:
            logger.info(f"Languages match ({source_lang}), skipping translation")
            return False
        
        logger.info(f"Languages differ ({source_lang} → {target_lang}), translation needed")
        return True
    
    def translate_elements(
        self,
        elements: List[Dict[str, Any]],
        source_lang: str,
        target_lang: str,
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Переводит текст всех элементов
        
        Args:
            elements: Список элементов с полем 'text'
            source_lang: Язык источника (например: 'de')
            target_lang: Целевой язык (например: 'ru')
            batch_size: Размер batch для Google API (экономия запросов)
            
        Returns:
            Элементы с добавленными полями:
            - text_original: оригинальный текст
            - text_translated: переведённый текст
            - language_original: язык источника
            - language_target: целевой язык
        """
        if not self.is_translation_needed(source_lang, target_lang):
            # Перевод не нужен - просто копируем text в оба поля
            for elem in elements:
                text = elem.get('text', '')
                elem['text_original'] = text
                elem['text_translated'] = text
                elem['language_original'] = source_lang
                elem['language_target'] = target_lang
            return elements
        
        # Собираем тексты для перевода
        texts_to_translate = []
        indices = []  # Индексы элементов с текстом
        
        for i, elem in enumerate(elements):
            text = elem.get('text', '').strip()
            if text:
                texts_to_translate.append(text)
                indices.append(i)
        
        if not texts_to_translate:
            logger.warning("No text to translate")
            return elements
        
        logger.info(f"Translating {len(texts_to_translate)} texts from {source_lang} to {target_lang}")
        
        # Batch translation для экономии
        translated_texts = []
        
        try:
            for i in range(0, len(texts_to_translate), batch_size):
                batch = texts_to_translate[i:i+batch_size]
                
                # Google Translate API call
                results = self.client.translate(
                    batch,
                    source_language=source_lang,
                    target_language=target_lang,
                    format_='text'
                )
                
                # Extract translated text
                if isinstance(results, list):
                    translated_texts.extend([r['translatedText'] for r in results])
                else:
                    translated_texts.append(results['translatedText'])
            
            # Добавляем переводы к элементам
            for idx, translated_text in zip(indices, translated_texts):
                elem = elements[idx]
                original_text = elem.get('text', '')
                
                elem['text_original'] = original_text
                elem['text_translated'] = translated_text
                elem['language_original'] = source_lang
                elem['language_target'] = target_lang
                
                logger.debug(f"Translated: '{original_text[:30]}' → '{translated_text[:30]}'")
            
            logger.info(f"✅ Successfully translated {len(translated_texts)} texts")
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Fallback: копируем оригинальный текст
            for elem in elements:
                text = elem.get('text', '')
                elem['text_original'] = text
                elem['text_translated'] = text
                elem['language_original'] = source_lang
                elem['language_target'] = target_lang
        
        return elements
    
    def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Переводит отдельный текст
        
        Args:
            text: Текст для перевода
            source_lang: Язык источника
            target_lang: Целевой язык
            
        Returns:
            Переведённый текст или оригинал при ошибке
        """
        if not self.is_translation_needed(source_lang, target_lang):
            return text
        
        try:
            result = self.client.translate(
                text,
                source_language=source_lang,
                target_language=target_lang,
                format_='text'
            )
            return result['translatedText']
        except Exception as e:
            logger.error(f"Failed to translate text: {e}")
            return text
    
    def _normalize_language_code(self, lang: str) -> str:
        """Нормализует языковой код (de-DE → de)"""
        if not lang:
            return 'en'
        return lang.lower().split('-')[0]
    
    @lru_cache(maxsize=1000)
    def _cached_translate(self, text: str, source: str, target: str) -> str:
        """Кэшированный перевод для часто встречающихся фраз"""
        return self.translate_text(text, source, target)
