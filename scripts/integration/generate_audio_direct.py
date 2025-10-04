#!/usr/bin/env python3
"""
Прямая генерация аудио файлов с новыми настройками голоса
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Добавляем путь к backend
sys.path.append('backend')

# Загружаем environment переменные
load_dotenv('backend_env_docker.env')

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_audio_directly():
    """Прямая генерация аудио файлов"""
    
    lesson_id = "f9d8bb26-0a3f-404b-9d19-dc7172cdc9d0"
    
    try:
        # Переходим в директорию backend
        os.chdir('backend')
        
        # Добавляем текущую директорию в путь
        sys.path.insert(0, '.')
        
        # Импортируем необходимые модули
        from app.tasks import process_lesson_full_pipeline
        
        logger.info(f"🔄 Прямая генерация аудио для урока {lesson_id}")
        
        # Запускаем задачу напрямую (не через Celery)
        result = process_lesson_full_pipeline(lesson_id)
        
        logger.info(f"🎉 Генерация завершена: {result}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    generate_audio_directly()
