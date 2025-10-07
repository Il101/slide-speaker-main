#!/usr/bin/env python3
"""
Тест для проверки дублирования голосов в SSML
"""
import os
import logging
from dotenv import load_dotenv
from backend.workers.tts_google_ssml import GoogleTTSWorkerSSML

# Загружаем переменные окружения
load_dotenv("backend/.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_ssml():
    """Тестирует простой SSML без дублирования"""
    logger.info("🎵 Тестируем простой SSML без дублирования...")
    
    # Простой SSML текст без дублирования
    ssml_text = '''<speak>
<prosody rate="0.95" pitch="-1.0">Привет, это тест.</prosody> 
<break time="1s"/>
<emphasis level="strong">Один голос</emphasis> должен звучать.
</speak>'''
    
    try:
        worker = GoogleTTSWorkerSSML()
        audio_path, tts_words = worker.synthesize_slide_text_google_ssml([ssml_text])
        
        logger.info(f"✅ Аудио файл: {audio_path}")
        logger.info(f"✅ Размер: {os.path.getsize(audio_path)} байт")
        logger.info(f"✅ Длительность: {tts_words['sentences'][-1]['t1']:.2f}s")
        
        # Сохраним файл для прослушивания
        test_file = "test_single_voice.wav"
        os.system(f"cp {audio_path} {test_file}")
        logger.info(f"✅ Тестовый файл сохранен: {test_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_ssml()
    if success:
        print("\n🎉 Тест завершен! Проверьте файл test_single_voice.wav")
    else:
        print("\n❌ Тест не удался!")
