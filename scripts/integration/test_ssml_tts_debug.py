#!/usr/bin/env python3
"""
Тест SSML TTS Worker для проверки дублирования голосов
"""
import os
import logging
from dotenv import load_dotenv
from backend.workers.tts_google_ssml import GoogleTTSWorkerSSML

# Загружаем переменные окружения
load_dotenv("backend_env_enhanced_hybrid.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ssml_tts():
    """Тестирует SSML TTS на простом тексте"""
    logger.info("🎵 Тестируем SSML TTS Worker...")
    
    # Простой SSML текст
    ssml_text = '''<speak>
<prosody rate="0.95" pitch="-1.0">Привет, это тест SSML.</prosody> 
<break time="0.5s"/>
<emphasis level="strong">Важное слово</emphasis> выделено.
</speak>'''
    
    try:
        worker = GoogleTTSWorkerSSML()
        
        # Тест 1: Простой синтез
        logger.info("🔍 Тест 1: Простой синтез SSML")
        audio_data = worker.synthesize_speech_with_ssml(ssml_text)
        logger.info(f"✅ Синтезировано: {len(audio_data)} байт")
        
        # Тест 2: Полный синтез слайда
        logger.info("🔍 Тест 2: Полный синтез слайда")
        audio_path, tts_words = worker.synthesize_slide_text_google_ssml([ssml_text])
        logger.info(f"✅ Аудио файл: {audio_path}")
        logger.info(f"✅ Тайминги: {len(tts_words['sentences'])} предложений")
        
        # Проверим, что файл создан
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            logger.info(f"✅ Размер файла: {file_size} байт")
        else:
            logger.error(f"❌ Файл не создан: {audio_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в SSML TTS: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_ssml_tts()
    if success:
        print("\n🎉 SSML TTS тест успешен!")
    else:
        print("\n❌ SSML TTS тест не удался!")
