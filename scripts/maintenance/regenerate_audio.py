#!/usr/bin/env python3
"""
Скрипт для пересоздания аудио файлов с новыми настройками голоса
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Добавляем путь к backend
sys.path.append('backend')

# Загружаем environment переменные
load_dotenv('backend/.env')

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def regenerate_audio():
    """Пересоздает аудио файлы для презентации с новыми настройками голоса"""
    
    lesson_id = "f9d8bb26-0a3f-404b-9d19-dc7172cdc9d0"
    
    try:
        # Импортируем задачи Celery
        from backend.app.tasks import process_lesson_full_pipeline
        
        logger.info(f"🔄 Запускаем пересоздание аудио для урока {lesson_id}")
        
        # Запускаем задачу генерации аудио
        result = process_lesson_full_pipeline.delay(lesson_id)
        
        logger.info(f"✅ Задача запущена с ID: {result.id}")
        logger.info("⏳ Ожидаем завершения...")
        
        # Ждем результат
        task_result = result.get(timeout=300)  # 5 минут таймаут
        
        logger.info(f"🎉 Задача завершена: {task_result}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    regenerate_audio()
