#!/usr/bin/env python3
"""
Быстрый тест улучшенного голоса Google TTS
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

async def test_improved_voice():
    """Тестирует улучшенный голос с новыми настройками"""
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Тестовый текст из реальной лекции
        test_text = """
        Добрый день, друзья! Сегодня мы говорим о темах нашего практического занятия в Университете Иннсбрука. 
        Давайте посмотрим на этот слайд вместе – здесь перечислены все ключевые пункты, которые мы разберем по порядку.
        """
        
        # Настройки синтеза (улучшенные)
        synthesis_input = texttospeech.SynthesisInput(text=test_text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="ru-RU",
            name="ru-RU-Wavenet-B",  # Мужской WaveNet голос
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.1,  # Немного быстрее
            pitch=2.0,          # Более высокий тон
        )
        
        # Синтез речи
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Сохранение аудио файла
        output_file = "improved_voice_test.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"✅ Улучшенный голос создан: {output_file}")
        logger.info(f"🎵 Голос: ru-RU-Wavenet-B")
        logger.info(f"⚡ Скорость: 1.1x")
        logger.info(f"🎼 Тон: +2.0")
        logger.info(f"📁 Размер файла: {len(response.audio_content)} байт")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_improved_voice())
