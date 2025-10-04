#!/usr/bin/env python3
"""
Тест SSML интеграции в основном пайплайне
"""
import os
import asyncio
import logging
import requests
import time
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv("backend_env_enhanced_hybrid.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ssml_integration():
    """Тестирует SSML интеграцию через API"""
    logger.info("🎵 Тестируем SSML интеграцию в основном пайплайне...")
    
    # URL API
    api_base = "http://127.0.0.1:8001"
    
    try:
        # Шаг 1: Проверяем здоровье API
        logger.info("🔍 Проверяем здоровье API...")
        health_response = requests.get(f"{api_base}/health")
        if health_response.status_code != 200:
            logger.error(f"❌ API не отвечает: {health_response.status_code}")
            return False
        
        logger.info("✅ API работает")
        
        # Шаг 2: Загружаем тестовую презентацию
        logger.info("📤 Загружаем тестовую презентацию...")
        
        # Используем существующую презентацию
        test_file_path = "test_presentation.pptx"
        if not os.path.exists(test_file_path):
            logger.error(f"❌ Тестовый файл не найден: {test_file_path}")
            return False
        
        with open(test_file_path, 'rb') as f:
            files = {'file': (test_file_path, f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
            upload_response = requests.post(f"{api_base}/upload", files=files)
        
        if upload_response.status_code != 200:
            logger.error(f"❌ Ошибка загрузки: {upload_response.status_code}")
            logger.error(f"Response: {upload_response.text}")
            return False
        
        upload_data = upload_response.json()
        lesson_id = upload_data['lesson_id']
        logger.info(f"✅ Презентация загружена, lesson_id: {lesson_id}")
        
        # Шаг 3: Полный пайплайн запускается автоматически при загрузке
        logger.info("🎵 Полный пайплайн с SSML запускается автоматически...")
        
        # Шаг 4: Ждем завершения обработки
        logger.info("⏳ Ждем завершения обработки...")
        max_wait_time = 300  # 5 минут
        wait_interval = 10   # 10 секунд
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            time.sleep(wait_interval)
            elapsed_time += wait_interval
            
            # Проверяем статус
            status_response = requests.get(f"{api_base}/lessons/{lesson_id}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status', 'unknown')
                progress = status_data.get('progress', 0)
                
                logger.info(f"📊 Статус: {status}, Прогресс: {progress}%")
                
                if status == 'completed':
                    logger.info("✅ Обработка завершена!")
                    break
                elif status == 'failed':
                    logger.error(f"❌ Обработка не удалась: {status_data.get('error', 'Unknown error')}")
                    return False
            else:
                logger.warning(f"⚠️ Не удалось получить статус: {status_response.status_code}")
        
        if elapsed_time >= max_wait_time:
            logger.error("❌ Таймаут ожидания обработки")
            return False
        
        # Шаг 5: Получаем манифест и проверяем SSML
        logger.info("📋 Получаем манифест и проверяем SSML...")
        manifest_response = requests.get(f"{api_base}/lessons/{lesson_id}/manifest")
        
        if manifest_response.status_code != 200:
            logger.error(f"❌ Ошибка получения манифеста: {manifest_response.status_code}")
            return False
        
        manifest_data = manifest_response.json()
        slides = manifest_data.get('slides', [])
        
        logger.info(f"📊 Найдено слайдов: {len(slides)}")
        
        # Проверяем SSML в лекционном тексте
        ssml_found = 0
        for i, slide in enumerate(slides):
            lecture_text = slide.get('lecture_text', '')
            if lecture_text.startswith('<speak>'):
                ssml_found += 1
                logger.info(f"✅ Слайд {i+1}: SSML найден ({len(lecture_text)} символов)")
            else:
                logger.warning(f"⚠️ Слайд {i+1}: SSML не найден")
        
        logger.info(f"📊 SSML найден в {ssml_found}/{len(slides)} слайдах")
        
        # Шаг 6: Проверяем аудио файлы
        logger.info("🎵 Проверяем аудио файлы...")
        audio_files_found = 0
        
        # Проверяем директорию audio напрямую
        audio_dir = f"backend/.data/{lesson_id}/audio"
        if os.path.exists(audio_dir):
            audio_files = [f for f in os.listdir(audio_dir) if f.endswith(('.wav', '.mp3'))]
            audio_files_found = len(audio_files)
            logger.info(f"✅ Найдено {audio_files_found} аудио файлов в {audio_dir}")
            for audio_file in audio_files:
                logger.info(f"  📁 {audio_file}")
        else:
            logger.warning(f"⚠️ Директория audio не найдена: {audio_dir}")
        
        # Также проверяем манифест
        for i, slide in enumerate(slides):
            audio_path = slide.get('audio')
            if audio_path:
                logger.info(f"📋 Слайд {i+1}: Аудио путь в манифесте: {audio_path}")
            else:
                logger.warning(f"⚠️ Слайд {i+1}: Аудио путь не указан в манифесте")
        
        logger.info(f"📊 Аудио файлы найдены для {audio_files_found}/{len(slides)} слайдов")
        
        # Результат
        if ssml_found > 0 and audio_files_found > 0:
            logger.info(f"\n🎉 SSML ИНТЕГРАЦИЯ УСПЕШНА!")
            logger.info(f"✅ SSML текст: {ssml_found}/{len(slides)} слайдов")
            logger.info(f"✅ Аудио файлы: {audio_files_found}/{len(slides)} слайдов")
            logger.info(f"🎵 Качество русских акцентов должно быть улучшено!")
            return True
        else:
            logger.error(f"\n❌ SSML ИНТЕГРАЦИЯ НЕ РАБОТАЕТ")
            logger.error(f"❌ SSML текст: {ssml_found}/{len(slides)} слайдов")
            logger.error(f"❌ Аудио файлы: {audio_files_found}/{len(slides)} слайдов")
            return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте SSML интеграции: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ssml_integration())
    if success:
        print("\n🎉 SSML интеграция работает!")
    else:
        print("\n❌ SSML интеграция не работает!")
