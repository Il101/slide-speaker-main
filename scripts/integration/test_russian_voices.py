#!/usr/bin/env python3
"""
Тестирование различных русских голосов для лучшего качества акцентов и интонаций
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

# Тестовый текст с акцентами и интонациями
TEST_TEXT = """
Добрый день! Сегодня мы изучаем анатомию растений.
Это очень интересная тема для студентов университета.
Мы рассмотрим строение листьев, стеблей и корней.
Обратите внимание на важные детали в таблице.
"""

async def test_voice_with_settings(voice_name: str, speaking_rate: float, pitch: float, output_suffix: str = ""):
    """Тестирует голос с различными настройками"""
    try:
        client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=TEST_TEXT)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="ru-RU",
            name=voice_name,
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch,
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        output_file = f"voice_test_{voice_name.replace('-', '_').replace(':', '_')}{output_suffix}.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"✅ {voice_name} (rate={speaking_rate}, pitch={pitch}): {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка с голосом {voice_name}: {e}")
        return False

async def main():
    """Тестируем различные голоса и настройки"""
    logger.info("🎵 Тестируем русские голоса для лучшего качества акцентов...")
    
    # Список голосов для тестирования
    voices_to_test = [
        "ru-RU-Chirp3-HD-Leda",      # Женский Chirp
        "ru-RU-Chirp3-HD-Kore",      # Женский Chirp
        "ru-RU-Chirp3-HD-Aoede",     # Женский Chirp
        "ru-RU-Chirp3-HD-Zephyr",    # Женский Chirp
        "ru-RU-Chirp3-HD-Puck",      # Мужской Chirp
        "ru-RU-Chirp3-HD-Fenrir",    # Мужской Chirp
        "ru-RU-Chirp3-HD-Orus",      # Мужской Chirp
        "ru-RU-Wavenet-A",           # Женский WaveNet
        "ru-RU-Wavenet-B",           # Мужской WaveNet
    ]
    
    # Различные настройки для тестирования
    settings = [
        (1.0, 0.0, "_normal"),      # Нормальные настройки
        (0.9, -2.0, "_slow_low"),   # Медленнее и ниже
        (1.1, 2.0, "_fast_high"),   # Быстрее и выше
        (0.95, -1.0, "_gentle"),     # Мягче
    ]
    
    for voice in voices_to_test:
        logger.info(f"\n🔊 Тестируем голос: {voice}")
        for speaking_rate, pitch, suffix in settings:
            await test_voice_with_settings(voice, speaking_rate, pitch, suffix)
    
    logger.info(f"\n🎧 Прослушайте файлы и выберите лучший голос с правильными акцентами!")
    logger.info(f"💡 Рекомендации:")
    logger.info(f"  - Женские голоса часто лучше справляются с интонациями")
    logger.info(f"  - Более медленная речь (0.9-0.95) может улучшить акценты")
    logger.info(f"  - Немного пониженный тон (-1.0 до -2.0) может звучать естественнее")

if __name__ == "__main__":
    asyncio.run(main())
