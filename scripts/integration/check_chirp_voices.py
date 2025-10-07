#!/usr/bin/env python3
"""
Скрипт для проверки доступных голосов Google Cloud TTS, включая Chirp v3 HD
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

async def list_available_voices():
    """Получает список всех доступных голосов"""
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Получаем все доступные голоса
        voices = client.list_voices()
        
        logger.info("🎵 Все доступные голоса Google Cloud TTS:")
        logger.info("=" * 60)
        
        russian_voices = []
        chirp_voices = []
        
        for voice in voices.voices:
            if voice.language_codes[0].startswith('ru-RU'):
                russian_voices.append(voice)
                logger.info(f"🇷🇺 Русский: {voice.name} ({voice.ssml_gender.name})")
                
                # Проверяем, является ли это Chirp голосом
                if 'chirp' in voice.name.lower() or 'hd' in voice.name.lower():
                    chirp_voices.append(voice)
                    logger.info(f"  ⭐ CHIRP/HD голос: {voice.name}")
        
        logger.info(f"\n📊 Статистика:")
        logger.info(f"  🇷🇺 Русских голосов: {len(russian_voices)}")
        logger.info(f"  ⭐ Chirp/HD голосов: {len(chirp_voices)}")
        
        if chirp_voices:
            logger.info(f"\n🎯 Chirp/HD голоса найдены:")
            for voice in chirp_voices:
                logger.info(f"  ✅ {voice.name}")
        else:
            logger.info(f"\n⚠️ Chirp/HD голоса не найдены в текущем регионе")
        
        return russian_voices, chirp_voices
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения голосов: {e}")
        return [], []

async def test_chirp_voice(voice_name: str):
    """Тестирует конкретный Chirp голос"""
    try:
        client = texttospeech.TextToSpeechClient()
        
        test_text = """
        Привет! Это тест нового голоса Chirp v3 HD от Google. 
        Этот голос должен звучать максимально естественно и качественно.
        """
        
        synthesis_input = texttospeech.SynthesisInput(text=test_text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="ru-RU",
            name=voice_name,
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        output_file = f"chirp_test_{voice_name.replace('-', '_').replace(':', '_')}.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"✅ Chirp голос {voice_name}: создан файл {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка с Chirp голосом {voice_name}: {e}")
        return False

async def main():
    """Основная функция"""
    logger.info("🔍 Проверяем доступные голоса Google Cloud TTS...")
    
    russian_voices, chirp_voices = await list_available_voices()
    
    if chirp_voices:
        logger.info(f"\n🎵 Тестируем Chirp/HD голоса...")
        for voice in chirp_voices:
            await test_chirp_voice(voice.name)
    else:
        logger.info(f"\n💡 Chirp/HD голоса недоступны в текущем регионе")
        logger.info(f"   Возможные причины:")
        logger.info(f"   - Регион не поддерживает Chirp v3 HD")
        logger.info(f"   - Нужна специальная активация")
        logger.info(f"   - Требуется другой проект GCP")

if __name__ == "__main__":
    asyncio.run(main())
