"""
Base Provider Interfaces - абстракции для AI сервисов
✅ FIX: Легко переключаться между провайдерами (Google, Azure, AWS, etc.)
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Voice:
    """Конфигурация голоса для TTS"""
    id: str
    name: str
    language: str
    gender: str  # "male", "female", "neutral"
    provider: str
    sample_rate: int = 24000
    quality: str = "high"  # "low", "medium", "high", "premium"


@dataclass
class TTSResult:
    """Результат синтеза речи"""
    audio_bytes: bytes
    duration_seconds: float
    word_timings: List[Dict[str, Any]]  # [{"word": "hello", "start": 0.0, "end": 0.5}, ...]
    format: str = "wav"  # "wav", "mp3", "ogg"
    sample_rate: int = 24000


class TTSProvider(ABC):
    """
    Абстрактный интерфейс для Text-to-Speech провайдеров
    
    ✅ FIX: Унифицированный интерфейс для Google TTS, Azure TTS, ElevenLabs, AWS Polly, etc.
    Позволяет переключаться между провайдерами через env переменную.
    """
    
    @abstractmethod
    async def synthesize_ssml(
        self,
        ssml_text: str,
        voice_config: Voice,
        enable_word_timing: bool = True
    ) -> TTSResult:
        """
        Синтезировать речь из SSML
        
        Args:
            ssml_text: SSML разметка
            voice_config: Конфигурация голоса
            enable_word_timing: Получать ли word-level timing
            
        Returns:
            TTSResult с аудио и таймингами
        """
        pass
    
    @abstractmethod
    async def synthesize_text(
        self,
        text: str,
        voice_config: Voice
    ) -> TTSResult:
        """
        Синтезировать речь из обычного текста
        
        Args:
            text: Обычный текст
            voice_config: Конфигурация голоса
            
        Returns:
            TTSResult с аудио
        """
        pass
    
    @abstractmethod
    def get_supported_voices(self, language: Optional[str] = None) -> List[Voice]:
        """
        Получить список поддерживаемых голосов
        
        Args:
            language: Фильтр по языку (опционально)
            
        Returns:
            Список доступных голосов
        """
        pass
    
    @abstractmethod
    def validate_ssml(self, ssml: str) -> Tuple[bool, List[str]]:
        """
        Валидировать SSML для данного провайдера
        
        Args:
            ssml: SSML текст
            
        Returns:
            (is_valid, list_of_errors)
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Получить имя провайдера"""
        pass
    
    @abstractmethod
    def get_pricing_info(self) -> Dict[str, Any]:
        """
        Получить информацию о ценах
        
        Returns:
            {"per_1m_chars": float, "currency": str, ...}
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, text_length: int) -> float:
        """
        Оценить стоимость синтеза
        
        Args:
            text_length: Длина текста в символах
            
        Returns:
            Стоимость в USD
        """
        pass


class OCRProvider(ABC):
    """
    Абстрактный интерфейс для OCR провайдеров
    
    ✅ FIX: Унифицированный интерфейс для Google Document AI, Azure OCR, AWS Textract, etc.
    """
    
    @abstractmethod
    async def extract_text(
        self,
        image_path: str,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Извлечь текст из изображения
        
        Args:
            image_path: Путь к изображению
            language: Язык для OCR (опционально)
            
        Returns:
            List of elements: [{"id": str, "text": str, "bbox": [x, y, w, h], "confidence": float}, ...]
        """
        pass
    
    @abstractmethod
    async def extract_batch(
        self,
        image_paths: List[str],
        language: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Извлечь текст из нескольких изображений (batch)
        
        Args:
            image_paths: Список путей к изображениям
            language: Язык для OCR
            
        Returns:
            List of results for each image
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Получить имя провайдера"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Получить список поддерживаемых языков"""
        pass


class LLMProvider(ABC):
    """
    Абстрактный интерфейс для LLM провайдеров
    
    ✅ FIX: Унифицированный интерфейс для Gemini, OpenRouter, OpenAI, Anthropic, etc.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        image_base64: Optional[str] = None
    ) -> str:
        """
        Генерировать текст
        
        Args:
            prompt: Промпт пользователя
            system_prompt: Системный промпт
            temperature: Температура (0.0-1.0)
            max_tokens: Максимум токенов
            image_base64: Base64 изображения для vision моделей
            
        Returns:
            Сгенерированный текст
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Получить имя провайдера"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Получить имя модели"""
        pass
    
    @abstractmethod
    def supports_vision(self) -> bool:
        """Поддерживает ли провайдер vision (изображения)"""
        pass
    
    @abstractmethod
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Оценить стоимость запроса
        
        Args:
            prompt_tokens: Количество токенов в промпте
            completion_tokens: Количество токенов в ответе
            
        Returns:
            Стоимость в USD
        """
        pass


# Пример использования:
"""
# В коде pipeline:
from app.services.providers.registry import ProviderRegistry

# Получить TTS провайдер (автоматически из env: TTS_PROVIDER=google/azure/elevenlabs)
tts_provider = ProviderRegistry.get_tts_provider()

# Использовать унифицированный интерфейс
result = await tts_provider.synthesize_ssml(
    ssml_text="<speak>Hello world</speak>",
    voice_config=Voice(
        id="ru-RU-Wavenet-D",
        name="Russian Female",
        language="ru-RU",
        gender="female",
        provider="google"
    )
)

# Легко переключиться на другой провайдер:
# 1. Установить TTS_PROVIDER=azure в .env
# 2. Код остаётся тот же!

# A/B тестирование:
google_result = await ProviderRegistry.get_tts_provider("google").synthesize_ssml(...)
azure_result = await ProviderRegistry.get_tts_provider("azure").synthesize_ssml(...)
# Сравнить качество/стоимость
"""
