#!/usr/bin/env python3
"""
Тестовый скрипт для проверки LLM генерации
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

def test_llm_generation():
    """Тестируем генерацию LLM для слайдов"""
    
    # Тестовые элементы слайда
    test_elements = [
        {
            "id": "heading_1",
            "type": "heading",
            "text": "Введение в машинное обучение",
            "bbox": [100, 100, 800, 150],
            "confidence": 0.95
        },
        {
            "id": "paragraph_1", 
            "type": "paragraph",
            "text": "Машинное обучение - это раздел искусственного интеллекта, который позволяет компьютерам обучаться без явного программирования.",
            "bbox": [100, 200, 800, 300],
            "confidence": 0.92
        },
        {
            "id": "list_1",
            "type": "list",
            "text": "Основные типы машинного обучения:\n• Обучение с учителем\n• Обучение без учителя\n• Обучение с подкреплением",
            "bbox": [100, 350, 800, 500],
            "confidence": 0.88
        }
    ]
    
    logger.info("🧪 Тестируем LLM генерацию...")
    logger.info(f"📊 Тестовые элементы: {len(test_elements)}")
    
    try:
        # Импортируем функцию генерации
        from backend.services.provider_factory import plan_slide_with_gemini
        
        logger.info("✅ Импорт plan_slide_with_gemini успешен")
        
        # Генерируем speaker notes
        logger.info("🔄 Генерируем speaker notes...")
        speaker_notes = plan_slide_with_gemini(test_elements)
        
        logger.info(f"✅ Сгенерировано {len(speaker_notes)} speaker notes:")
        for i, note in enumerate(speaker_notes):
            logger.info(f"  {i+1}. {note.get('text', '')}")
        
        # Проверяем, что это не mock данные
        if len(speaker_notes) > 0 and "This slide contains important information" in speaker_notes[0].get('text', ''):
            logger.warning("⚠️ Обнаружены mock данные! LLM не работает правильно.")
            return False
        
        logger.info("✅ LLM генерация работает корректно!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании LLM: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_lecture_text_generation():
    """Тестируем генерацию lecture text"""
    
    test_elements = [
        {
            "id": "heading_1",
            "type": "heading", 
            "text": "Алгоритмы классификации",
            "bbox": [100, 100, 800, 150],
            "confidence": 0.95
        },
        {
            "id": "paragraph_1",
            "type": "paragraph",
            "text": "Классификация - это задача машинного обучения, где мы предсказываем категорию или класс для новых данных на основе обучающих примеров.",
            "bbox": [100, 200, 800, 300], 
            "confidence": 0.92
        }
    ]
    
    logger.info("🧪 Тестируем генерацию lecture text...")
    
    try:
        # Импортируем функцию генерации lecture text
        from backend.services.provider_factory import generate_lecture_text_with_ssml
        
        logger.info("✅ Импорт generate_lecture_text_with_ssml успешен")
        
        # Генерируем lecture text
        logger.info("🔄 Генерируем lecture text...")
        lecture_text = generate_lecture_text_with_ssml(test_elements)
        
        logger.info(f"✅ Сгенерирован lecture text ({len(lecture_text)} символов):")
        logger.info(f"📝 {lecture_text[:200]}...")
        
        # Проверяем, что это не mock данные
        if "Let's discuss the content of this slide together" in lecture_text:
            logger.warning("⚠️ Обнаружены mock данные! LLM не работает правильно.")
            return False
            
        logger.info("✅ Генерация lecture text работает корректно!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании lecture text: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_openrouter_connection():
    """Тестируем подключение к OpenRouter"""
    
    logger.info("🧪 Тестируем подключение к OpenRouter...")
    
    try:
        import requests
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.error("❌ OPENROUTER_API_KEY не найден в переменных окружения")
            return False
            
        logger.info("✅ API ключ найден")
        
        # Тестовый запрос к OpenRouter
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "x-ai/grok-4-fast:free",
            "messages": [
                {"role": "user", "content": "Привет! Ответь коротко: работает ли API?"}
            ],
            "max_tokens": 50
        }
        
        logger.info("🔄 Отправляем тестовый запрос к OpenRouter...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info(f"✅ OpenRouter API работает! Ответ: {content}")
            return True
        else:
            logger.error(f"❌ Ошибка OpenRouter API: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к OpenRouter: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Запускаем тесты LLM генерации...")
    
    # Тест 1: Подключение к OpenRouter
    openrouter_ok = test_openrouter_connection()
    
    # Тест 2: Генерация speaker notes
    speaker_notes_ok = test_llm_generation()
    
    # Тест 3: Генерация lecture text
    lecture_text_ok = test_lecture_text_generation()
    
    # Итоговый результат
    logger.info("\n" + "="*50)
    logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    logger.info(f"🔗 OpenRouter подключение: {'✅ OK' if openrouter_ok else '❌ FAIL'}")
    logger.info(f"📝 Speaker notes генерация: {'✅ OK' if speaker_notes_ok else '❌ FAIL'}")
    logger.info(f"🎤 Lecture text генерация: {'✅ OK' if lecture_text_ok else '❌ FAIL'}")
    
    if all([openrouter_ok, speaker_notes_ok, lecture_text_ok]):
        logger.info("🎉 Все тесты прошли успешно!")
    else:
        logger.warning("⚠️ Некоторые тесты не прошли. Проверьте настройки.")




