#!/usr/bin/env python3
"""
Тест OpenRouter интеграции
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend_env_openrouter.env")

def test_openrouter_integration():
    """Тест OpenRouter интеграции"""
    
    print("🤖 Тест OpenRouter интеграции")
    print("=" * 50)
    
    # Проверяем переменные окружения
    print("📋 Проверка переменных окружения:")
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    print(f"  OPENROUTER_API_KEY: {'✅ Установлен' if api_key and api_key != 'your-openrouter-api-key-here' else '❌ Не установлен'}")
    print(f"  OPENROUTER_MODEL: {model}")
    print(f"  OPENROUTER_BASE_URL: {base_url}")
    
    if not api_key or api_key == 'your-openrouter-api-key-here':
        print("\n❌ OpenRouter API ключ не установлен!")
        print("📝 Инструкции по получению ключа:")
        print("1. Перейдите на https://openrouter.ai/")
        print("2. Зарегистрируйтесь или войдите в аккаунт")
        print("3. Перейдите в раздел 'Keys'")
        print("4. Создайте новый API ключ")
        print("5. Скопируйте ключ и установите в OPENROUTER_API_KEY")
        return False
    
    try:
        from backend.workers.llm_openrouter import OpenRouterLLMWorker
        
        worker = OpenRouterLLMWorker()
        
        print(f"\n📋 Настройки OpenRouter:")
        print(f"  Модель: {worker.model}")
        print(f"  Base URL: {worker.base_url}")
        print(f"  Temperature: {worker.temperature}")
        print(f"  Mock режим: {worker.use_mock}")
        
        if worker.use_mock:
            print("\n⚠️  OpenRouter работает в MOCK режиме")
            print("   Это означает, что:")
            print("   - API ключ недействителен")
            print("   - Или есть проблемы с подключением")
        else:
            print("\n✅ OpenRouter настроен для работы с реальным API")
        
        # Тестовые элементы слайда
        test_elements = [
            {
                "id": "elem_1",
                "type": "heading",
                "text": "Machine Learning Fundamentals",
                "bbox": [100, 50, 600, 80],
                "confidence": 0.95
            },
            {
                "id": "elem_2", 
                "type": "paragraph",
                "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
                "bbox": [100, 150, 600, 100],
                "confidence": 0.90
            },
            {
                "id": "elem_3",
                "type": "table",
                "text": "ML Types Comparison",
                "bbox": [100, 300, 600, 200],
                "table_id": "table_1",
                "rows": 3,
                "cols": 2
            },
            {
                "id": "elem_4",
                "type": "table_cell",
                "text": "Supervised Learning",
                "bbox": [100, 300, 300, 50],
                "table_id": "table_1",
                "row": 0,
                "col": 0
            },
            {
                "id": "elem_5",
                "type": "table_cell", 
                "text": "Uses labeled data",
                "bbox": [400, 300, 300, 50],
                "table_id": "table_1",
                "row": 0,
                "col": 1
            }
        ]
        
        print(f"\n🔊 Тестовый генерация заметок:")
        print(f"  Элементов: {len(test_elements)}")
        
        notes = worker.plan_slide_with_gemini(test_elements)
        
        print(f"  ✅ Сгенерировано заметок: {len(notes)}")
        
        for i, note in enumerate(notes):
            print(f"    {i+1}. {note['text']}")
            if 'targetId' in note:
                print(f"       Target: {note['targetId']}")
            elif 'target' in note:
                print(f"       Target: {note['target']}")
        
        return not worker.use_mock
        
    except Exception as e:
        print(f"❌ Ошибка тестирования OpenRouter: {e}")
        return False

if __name__ == "__main__":
    success = test_openrouter_integration()
    
    if success:
        print(f"\n🎉 OpenRouter работает с реальным API!")
    else:
        print(f"\n⚠️  OpenRouter работает в fallback режиме")
        print(f"📝 Для включения реального API:")
        print(f"1. Убедитесь, что API ключ правильный")
        print(f"2. Проверьте подключение к интернету")
        print(f"3. Убедитесь, что модель доступна")
