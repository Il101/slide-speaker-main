#!/usr/bin/env python3
"""
Быстрый тест улучшенного голоса с правильными акцентами
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from google.cloud import texttospeech

# Загружаем переменные окружения
load_dotenv("backend/.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_improved_accent_voice():
    """Тестирует улучшенный голос с правильными акцентами"""
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Тестовый текст с акцентами
        test_text = """
        Добрый день, студенты! Сегодня мы изучаем анатомию растений.
        Обратите внимание на важные детали в таблице.
        Мы рассмотрим строение листьев, стеблей и корней.
        Это очень интересная тема для университета.
        """
        
        synthesis_input = texttospeech.SynthesisInput(text=test_text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="ru-RU",
            name="ru-RU-Wavenet-A",  # Женский WaveNet голос
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.95,  # Немного медленнее для лучших акцентов
            pitch=-1.0,          # Немного ниже для естественности
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        output_file = "improved_accent_voice.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"✅ Улучшенный голос с акцентами создан: {output_file}")
        logger.info(f"🎵 Голос: ru-RU-Wavenet-A (женский)")
        logger.info(f"⚡ Скорость: 0.95x (медленнее для лучших акцентов)")
        logger.info(f"🎼 Тон: -1.0 (ниже для естественности)")
        logger.info(f"📁 Размер файла: {len(response.audio_content)} байт")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_improved_accent_voice())
