#!/usr/bin/env python3
"""
Тестовый скрипт для проверки TTS генерации
"""
import os
import sys
import json
import logging
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv("backend/.env")

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tts_generation():
    """Тестируем генерацию TTS"""
    
    # Тестовый текст для генерации аудио
    test_text = "Привет! Это тестовый текст для проверки генерации аудио. Машинное обучение - это увлекательная область искусственного интеллекта, которая позволяет компьютерам обучаться на данных без явного программирования."
    
    logger.info("🧪 Тестируем TTS генерацию...")
    logger.info(f"📝 Тестовый текст: {test_text[:50]}...")
    
    try:
        # Импортируем функцию TTS
        from backend.services.provider_factory import synthesize_slide_text_google
        
        logger.info("✅ Импорт synthesize_slide_text_google успешен")
        
        # Генерируем аудио
        logger.info("🔄 Генерируем аудио...")
        audio_path, tts_words = synthesize_slide_text_google([test_text])
        
        logger.info(f"✅ Аудио сгенерировано: {audio_path}")
        logger.info(f"📊 TTS words: {len(tts_words.get('sentences', []))} предложений")
        
        # Проверяем, что файл существует
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            logger.info(f"📁 Размер файла: {file_size} байт")
            
            # Проверяем длительность
            import wave
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / float(sample_rate)
                logger.info(f"⏱️ Длительность: {duration:.2f} секунд")
                
                if duration > 10:
                    logger.info("✅ TTS работает корректно - длинное аудио!")
                    return True
                else:
                    logger.warning("⚠️ Аудио слишком короткое - возможно проблема с TTS")
                    return False
        else:
            logger.error("❌ Аудио файл не создан")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании TTS: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_google_tts_connection():
    """Тестируем подключение к Google TTS"""
    
    logger.info("🧪 Тестируем подключение к Google TTS...")
    
    try:
        from google.cloud import texttospeech
        
        # Проверяем переменные окружения
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS не найден")
            return False
            
        if not os.path.exists(credentials_path):
            logger.error(f"❌ Файл credentials не найден: {credentials_path}")
            return False
            
        logger.info("✅ Файл credentials найден")
        
        # Инициализируем клиент
        client = texttospeech.TextToSpeechClient()
        
        # Тестовый запрос
        synthesis_input = texttospeech.SynthesisInput(text="Тест")
        voice = texttospeech.VoiceSelectionParams(
            language_code="ru-RU",
            name="ru-RU-Wavenet-B"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )
        
        logger.info("🔄 Отправляем тестовый запрос к Google TTS...")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        if response.audio_content:
            logger.info(f"✅ Google TTS работает! Размер ответа: {len(response.audio_content)} байт")
            return True
        else:
            logger.error("❌ Google TTS не вернул аудио")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Google TTS: {e}")
        return False

def test_upload_and_process():
    """Тестируем загрузку и обработку презентации"""
    
    logger.info("🧪 Тестируем загрузку презентации...")
    
    try:
        import requests
        
        # Проверяем, что сервер запущен
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code != 200:
                logger.error("❌ Сервер не отвечает")
                return False
        except:
            logger.error("❌ Не удается подключиться к серверу")
            return False
            
        logger.info("✅ Сервер запущен")
        
        # Ищем тестовую презентацию
        test_files = [
            "Kurs_10.pdf",
            "Kurs_10_short.pdf", 
            "test.pdf",
            "test.pptx"
        ]
        
        test_file = None
        for filename in test_files:
            if os.path.exists(filename):
                test_file = filename
                break
                
        if not test_file:
            logger.error("❌ Тестовая презентация не найдена")
            return False
            
        logger.info(f"📄 Найдена тестовая презентация: {test_file}")
        
        # Загружаем файл
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'application/pdf')}
            response = requests.post("http://localhost:8001/upload", files=files, timeout=60)
            
        if response.status_code == 200:
            result = response.json()
            lesson_id = result.get('lesson_id')
            logger.info(f"✅ Презентация загружена: {lesson_id}")
            
            # Ждем обработки
            import time
            max_wait = 120
            wait_time = 0
            
            while wait_time < max_wait:
                time.sleep(5)
                wait_time += 5
                
                status_response = requests.get(f"http://localhost:8001/lessons/{lesson_id}/status")
                if status_response.status_code == 200:
                    status = status_response.json()
                    logger.info(f"📊 Статус: {status.get('status')}, Прогресс: {status.get('progress', 0)}%")
                    
                    if status.get('status') == 'completed':
                        logger.info("✅ Обработка завершена")
                        break
                    elif status.get('status') == 'failed':
                        logger.error(f"❌ Обработка не удалась: {status.get('error')}")
                        return False
                        
            if wait_time >= max_wait:
                logger.error("❌ Таймаут обработки")
                return False
                
            # Проверяем результат
            manifest_response = requests.get(f"http://localhost:8001/lessons/{lesson_id}/manifest")
            if manifest_response.status_code == 200:
                manifest = manifest_response.json()
                slides = manifest.get('slides', [])
                
                logger.info(f"📊 Обработано слайдов: {len(slides)}")
                
                for i, slide in enumerate(slides):
                    duration = slide.get('duration', 0)
                    lecture_text = slide.get('lecture_text', '')
                    logger.info(f"  Слайд {i+1}: {duration:.1f}с, текст: {lecture_text[:50]}...")
                    
                    if duration > 10:
                        logger.info(f"✅ Слайд {i+1} имеет длинное аудио!")
                        
                return True
            else:
                logger.error("❌ Ошибка получения манифеста")
                return False
                
        else:
            logger.error(f"❌ Ошибка загрузки: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании загрузки: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Запускаем тесты TTS генерации...")
    
    # Тест 1: Подключение к Google TTS
    google_tts_ok = test_google_tts_connection()
    
    # Тест 2: Генерация TTS
    tts_generation_ok = test_tts_generation()
    
    # Тест 3: Загрузка и обработка презентации
    upload_ok = test_upload_and_process()
    
    # Итоговый результат
    logger.info("\n" + "="*50)
    logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    logger.info(f"🔗 Google TTS подключение: {'✅ OK' if google_tts_ok else '❌ FAIL'}")
    logger.info(f"🎤 TTS генерация: {'✅ OK' if tts_generation_ok else '❌ FAIL'}")
    logger.info(f"📤 Загрузка презентации: {'✅ OK' if upload_ok else '❌ FAIL'}")
    
    if all([google_tts_ok, tts_generation_ok, upload_ok]):
        logger.info("🎉 Все тесты прошли успешно!")
    else:
        logger.warning("⚠️ Некоторые тесты не прошли. Проверьте настройки.")




