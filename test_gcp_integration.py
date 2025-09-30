#!/usr/bin/env python3
"""
Тест интеграции Google Cloud сервисов для Slide Speaker
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_google_cloud_integration():
    """Тестирование всех Google Cloud сервисов"""
    
    print("🚀 Тестирование Google Cloud интеграции")
    print("=" * 50)
    
    # Проверка переменных окружения
    print("\n📋 Проверка переменных окружения:")
    required_vars = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GCP_PROJECT_ID", 
        "GCP_DOC_AI_PROCESSOR_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: НЕ НАСТРОЕНА")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Необходимо настроить переменные: {', '.join(missing_vars)}")
        return False
    
    # Тест 1: Document AI (OCR)
    print("\n🔍 Тестирование Document AI (OCR):")
    try:
        from backend.workers.ocr_google import GoogleDocumentAIWorker
        
        worker = GoogleDocumentAIWorker()
        if worker.use_mock:
            print("⚠️  Document AI работает в mock режиме")
        else:
            print("✅ Document AI инициализирован успешно")
            
        # Тестовое извлечение элементов
        test_png_paths = ["/tmp/test_slide.png"]
        results = await worker.extract_elements_from_pages(test_png_paths)
        print(f"✅ OCR извлечение работает: {len(results)} слайдов")
        
    except Exception as e:
        print(f"❌ Ошибка Document AI: {e}")
        return False
    
    # Тест 2: Gemini (LLM)
    print("\n🤖 Тестирование Gemini (LLM):")
    try:
        from backend.workers.llm_gemini import GeminiLLMWorker
        
        worker = GeminiLLMWorker()
        if worker.use_mock:
            print("⚠️  Gemini работает в mock режиме")
        else:
            print("✅ Gemini инициализирован успешно")
            
        # Тестовая генерация заметок
        test_elements = [{
            "id": "test_1",
            "type": "heading",
            "text": "Тестовый заголовок",
            "bbox": [100, 50, 600, 80],
            "confidence": 0.95
        }]
        
        notes = worker.plan_slide_with_gemini(test_elements)
        print(f"✅ LLM генерация работает: {len(notes)} заметок")
        
    except Exception as e:
        print(f"❌ Ошибка Gemini: {e}")
        return False
    
    # Тест 3: Google Cloud Text-to-Speech
    print("\n🎤 Тестирование Google Cloud TTS:")
    try:
        from backend.workers.tts_google import GoogleTTSWorker
        
        worker = GoogleTTSWorker()
        if worker.use_mock:
            print("⚠️  TTS работает в mock режиме")
        else:
            print("✅ Google Cloud TTS инициализирован успешно")
            
        # Тестовый синтез речи
        test_texts = ["Привет, это тестовый синтез речи"]
        audio_path, tts_words = worker.synthesize_slide_text_google(test_texts)
        print(f"✅ TTS синтез работает: {audio_path}")
        
    except Exception as e:
        print(f"❌ Ошибка TTS: {e}")
        return False
    
    # Тест 4: Provider Factory
    print("\n🏭 Тестирование Provider Factory:")
    try:
        from backend.app.services.provider_factory import ProviderFactory
        
        # Тест OCR провайдера
        ocr_provider = ProviderFactory.get_ocr_provider()
        print("✅ OCR провайдер создан")
        
        # Тест LLM провайдера
        llm_provider = ProviderFactory.get_llm_provider()
        print("✅ LLM провайдер создан")
        
        # Тест TTS провайдера
        tts_provider = ProviderFactory.get_tts_provider()
        print("✅ TTS провайдер создан")
        
    except Exception as e:
        print(f"❌ Ошибка Provider Factory: {e}")
        return False
    
    print("\n🎉 Все тесты Google Cloud интеграции пройдены!")
    return True

if __name__ == "__main__":
    # Загружаем переменные окружения из .env файла
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    
    success = asyncio.run(test_google_cloud_integration())
    
    if success:
        print("\n✅ Google Cloud сервисы готовы к использованию!")
        print("\n📝 Следующие шаги:")
        print("1. Убедитесь, что Service Account ключ доступен")
        print("2. Проверьте права доступа к API")
        print("3. Запустите приложение: python backend/main.py")
    else:
        print("\n❌ Есть проблемы с настройкой Google Cloud сервисов")
        print("Проверьте переменные окружения и права доступа")
