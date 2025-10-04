#!/usr/bin/env python3
"""
Перегенерация аудио для второго слайда урока
"""
import os
import sys
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

# Добавляем путь к backend
sys.path.append('backend')

# Загружаем environment переменные
load_dotenv('backend_env_enhanced_hybrid.env')

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def regenerate_slide2_audio():
    """Перегенерация аудио для второго слайда"""
    
    lesson_id = "4a786fb1-9fad-401b-b61a-af9a2c375804"
    slide_id = 2
    
    try:
        # Переходим в директорию backend
        os.chdir('backend')
        
        # Добавляем текущую директорию в путь
        sys.path.insert(0, '.')
        
        # Импортируем необходимые модули
        from app.services.provider_factory import synthesize_slide_text_google
        from app.core.config import settings
        
        logger.info(f"🔄 Перегенерация аудио для урока {lesson_id}, слайд {slide_id}")
        
        # Читаем манифест чтобы получить lecture_text
        manifest_path = Path(f".data/{lesson_id}/manifest.json")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Находим второй слайд
        slide2 = None
        for slide in manifest['slides']:
            if slide['id'] == slide_id:
                slide2 = slide
                break
        
        if not slide2:
            logger.error(f"❌ Слайд {slide_id} не найден в манифесте")
            return
        
        # Получаем lecture_text
        lecture_text = slide2.get('lecture_text', '')
        if not lecture_text:
            logger.error(f"❌ Нет lecture_text для слайда {slide_id}")
            return
        
        logger.info(f"📝 Текст для генерации: {lecture_text[:100]}...")
        
        # Генерируем аудио
        logger.info("🎵 Генерируем аудио...")
        audio_path, tts_words = synthesize_slide_text_google([lecture_text], voice="ru-RU-Wavenet-B", rate=1.0)
        
        logger.info(f"✅ Аудио сгенерировано: {audio_path}")
        logger.info(f"📊 Длительность: {tts_words['sentences'][-1]['t1']:.2f}s")
        
        # Копируем файл в папку урока
        audio_dest = Path(f".data/{lesson_id}/audio/002.wav")
        audio_dest.parent.mkdir(exist_ok=True)
        
        import shutil
        shutil.copy2(audio_path, audio_dest)
        
        # Сохраняем timing информацию
        tts_words_path = Path(f".data/{lesson_id}/audio/002_words.json")
        with open(tts_words_path, 'w', encoding='utf-8') as f:
            json.dump(tts_words, f, ensure_ascii=False, indent=2)
        
        # Обновляем манифест с новой длительностью
        slide2['duration'] = tts_words['sentences'][-1]['t1']
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        logger.info(f"🎉 Аудио успешно перегенерировано!")
        logger.info(f"📁 Файл: {audio_dest}")
        logger.info(f"⏱️ Длительность: {slide2['duration']:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    regenerate_slide2_audio()




