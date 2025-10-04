#!/usr/bin/env python3
"""
Скрипт для тестирования различных голосов Google Cloud Text-to-Speech
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from google.cloud import texttospeech

# Загружаем переменные окружения
load_dotenv("backend_env_enhanced_hybrid.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Доступные русские голоса Google Cloud TTS
RUSSIAN_VOICES = [
    "ru-RU-Standard-A",      # Женский стандартный
    "ru-RU-Standard-B",      # Мужской стандартный
    "ru-RU-Standard-C",      # Женский стандартный
    "ru-RU-Standard-D",      # Мужской стандартный
    "ru-RU-Standard-E",      # Женский стандартный
    "ru-RU-Wavenet-A",       # Женский WaveNet (старая версия)
    "ru-RU-Wavenet-B",       # Мужской WaveNet (старая версия)
    "ru-RU-Wavenet-C",       # Женский WaveNet (старая версия)
    "ru-RU-Wavenet-D",       # Мужской WaveNet (старая версия)
    "ru-RU-Wavenet-E",       # Женский WaveNet (старая версия)
    "ru-RU-Neural2-A",       # Женский Neural2 (новая версия)
    "ru-RU-Neural2-B",       # Мужской Neural2 (новая версия)
    "ru-RU-Neural2-C",       # Женский Neural2 (новая версия)
    "ru-RU-Neural2-D",       # Мужской Neural2 (новая версия)
]

# Тестовый текст для озвучки
TEST_TEXT = """
Привет! Это тест голоса Google Cloud Text-to-Speech. 
Мы тестируем различные варианты синтеза речи на русском языке.
Этот голос должен звучать естественно и понятно.
"""

async def test_voice(voice_name: str, text: str) -> bool:
    """Тестирует конкретный голос"""
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Настройки синтеза
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="ru-RU",
            name=voice_name,
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.1,
            pitch=2.0,
        )
        
        # Синтез речи
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Сохранение аудио файла
        output_file = f"voice_test_{voice_name.replace('-', '_')}.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"✅ Голос {voice_name}: создан файл {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка с голосом {voice_name}: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    logger.info("🎵 Тестируем голоса Google Cloud Text-to-Speech")
    logger.info(f"📝 Тестовый текст: {TEST_TEXT[:50]}...")
    
    successful_voices = []
    
    for voice in RUSSIAN_VOICES:
        logger.info(f"🔊 Тестируем голос: {voice}")
        success = await test_voice(voice, TEST_TEXT)
        if success:
            successful_voices.append(voice)
    
    logger.info(f"\n🎉 Успешно протестировано {len(successful_voices)} голосов:")
    for voice in successful_voices:
        logger.info(f"  ✅ {voice}")
    
    logger.info(f"\n📁 Аудио файлы сохранены в текущей директории")
    logger.info(f"🎧 Прослушайте файлы и выберите наиболее подходящий голос")
    
    # Рекомендации по выбору голоса
    logger.info(f"\n💡 Рекомендации:")
    logger.info(f"  🥇 Neural2 голоса - самые качественные (ru-RU-Neural2-*)")
    logger.info(f"  🥈 WaveNet голоса - хорошее качество (ru-RU-Wavenet-*)")
    logger.info(f"  🥉 Standard голоса - базовое качество (ru-RU-Standard-*)")
    logger.info(f"  👨 Мужские голоса: *-B, *-D")
    logger.info(f"  👩 Женские голоса: *-A, *-C, *-E")

if __name__ == "__main__":
    asyncio.run(main())
