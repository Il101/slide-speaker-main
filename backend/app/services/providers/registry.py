"""
Provider Registry - реестр провайдеров для динамического выбора
✅ FIX: Единая точка для получения провайдеров
"""
import os
import logging
from typing import Optional, Dict, Type
from .base import TTSProvider, OCRProvider, LLMProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Реестр провайдеров AI сервисов
    
    ✅ FIX: Централизованное управление провайдерами.
    Позволяет переключаться через env переменные и регистрировать новые провайдеры.
    """
    
    # Зарегистрированные провайдеры
    _tts_providers: Dict[str, Type[TTSProvider]] = {}
    _ocr_providers: Dict[str, Type[OCRProvider]] = {}
    _llm_providers: Dict[str, Type[LLMProvider]] = {}
    
    @classmethod
    def register_tts_provider(cls, name: str, provider_class: Type[TTSProvider]):
        """
        Зарегистрировать TTS провайдер
        
        Args:
            name: Имя провайдера (например, "google", "azure", "elevenlabs")
            provider_class: Класс провайдера
        """
        cls._tts_providers[name] = provider_class
        logger.debug(f"Registered TTS provider: {name}")
    
    @classmethod
    def register_ocr_provider(cls, name: str, provider_class: Type[OCRProvider]):
        """Зарегистрировать OCR провайдер"""
        cls._ocr_providers[name] = provider_class
        logger.debug(f"Registered OCR provider: {name}")
    
    @classmethod
    def register_llm_provider(cls, name: str, provider_class: Type[LLMProvider]):
        """Зарегистрировать LLM провайдер"""
        cls._llm_providers[name] = provider_class
        logger.debug(f"Registered LLM provider: {name}")
    
    @classmethod
    def get_tts_provider(cls, provider_name: Optional[str] = None) -> TTSProvider:
        """
        Получить TTS провайдер
        
        Args:
            provider_name: Имя провайдера (если None, берётся из TTS_PROVIDER env)
            
        Returns:
            Instance of TTSProvider
            
        Raises:
            ValueError: Если провайдер не найден
        """
        provider_name = provider_name or os.getenv('TTS_PROVIDER', 'google')
        
        if provider_name not in cls._tts_providers:
            available = ', '.join(cls._tts_providers.keys())
            raise ValueError(
                f"Unknown TTS provider: {provider_name}. "
                f"Available: {available}"
            )
        
        provider_class = cls._tts_providers[provider_name]
        return provider_class()
    
    @classmethod
    def get_ocr_provider(cls, provider_name: Optional[str] = None) -> OCRProvider:
        """
        Получить OCR провайдер
        
        Args:
            provider_name: Имя провайдера (если None, берётся из OCR_PROVIDER env)
            
        Returns:
            Instance of OCRProvider
        """
        provider_name = provider_name or os.getenv('OCR_PROVIDER', 'google')
        
        if provider_name not in cls._ocr_providers:
            available = ', '.join(cls._ocr_providers.keys())
            raise ValueError(
                f"Unknown OCR provider: {provider_name}. "
                f"Available: {available}"
            )
        
        provider_class = cls._ocr_providers[provider_name]
        return provider_class()
    
    @classmethod
    def get_llm_provider(cls, provider_name: Optional[str] = None) -> LLMProvider:
        """
        Получить LLM провайдер
        
        Args:
            provider_name: Имя провайдера (если None, берётся из LLM_PROVIDER env)
            
        Returns:
            Instance of LLMProvider
        """
        provider_name = provider_name or os.getenv('LLM_PROVIDER', 'openrouter')
        
        if provider_name not in cls._llm_providers:
            available = ', '.join(cls._llm_providers.keys())
            raise ValueError(
                f"Unknown LLM provider: {provider_name}. "
                f"Available: {available}"
            )
        
        provider_class = cls._llm_providers[provider_name]
        return provider_class()
    
    @classmethod
    def list_available_providers(cls) -> Dict[str, list]:
        """
        Получить список всех доступных провайдеров
        
        Returns:
            {"tts": [...], "ocr": [...], "llm": [...]}
        """
        return {
            "tts": list(cls._tts_providers.keys()),
            "ocr": list(cls._ocr_providers.keys()),
            "llm": list(cls._llm_providers.keys())
        }


# Для будущей регистрации провайдеров:
"""
# В backend/app/services/providers/google_tts.py:
from .base import TTSProvider
from .registry import ProviderRegistry

class GoogleTTSProvider(TTSProvider):
    async def synthesize_ssml(self, ssml_text, voice_config, enable_word_timing=True):
        # Существующий код GoogleTTSWorkerSSML
        pass
    
    # ... остальные методы

# Регистрируем при импорте
ProviderRegistry.register_tts_provider("google", GoogleTTSProvider)


# В backend/app/services/providers/azure_tts.py:
class AzureTTSProvider(TTSProvider):
    async def synthesize_ssml(self, ssml_text, voice_config, enable_word_timing=True):
        # Azure TTS implementation
        pass

ProviderRegistry.register_tts_provider("azure", AzureTTSProvider)


# В backend/app/services/providers/elevenlabs_tts.py:
class ElevenLabsTTSProvider(TTSProvider):
    async def synthesize_ssml(self, ssml_text, voice_config, enable_word_timing=True):
        # ElevenLabs API
        pass

ProviderRegistry.register_tts_provider("elevenlabs", ElevenLabsTTSProvider)
"""
