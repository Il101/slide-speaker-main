#!/usr/bin/env python3
"""
Проверка доступных моделей OpenRouter
"""
import os
import sys
from pathlib import Path
import httpx
import json

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend_env_openrouter.env")

def check_openrouter_models():
    """Проверка доступных моделей OpenRouter"""
    
    print("🤖 Проверка доступных моделей OpenRouter")
    print("=" * 50)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    if not api_key:
        print("❌ OpenRouter API ключ не установлен!")
        return False
    
    print(f"📋 Base URL: {base_url}")
    print(f"📋 API Key: {api_key[:20]}...")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Получаем список моделей
        print(f"\n📝 Получаю список моделей...")
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{base_url}/models",
                headers=headers
            )
            
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get("data", [])
                
                print(f"✅ Найдено моделей: {len(models)}")
                
                # Показываем первые 10 моделей
                print(f"\n📋 Доступные модели:")
                for i, model in enumerate(models[:10]):
                    model_id = model.get("id", "unknown")
                    model_name = model.get("name", "Unknown")
                    pricing = model.get("pricing", {})
                    prompt_price = pricing.get("prompt", "N/A")
                    completion_price = pricing.get("completion", "N/A")
                    
                    print(f"  {i+1}. {model_id}")
                    print(f"     Название: {model_name}")
                    print(f"     Цена: {prompt_price} / {completion_price}")
                    print()
                
                # Ищем бесплатные модели
                free_models = [m for m in models if m.get("pricing", {}).get("prompt") == "0"]
                
                if free_models:
                    print(f"🆓 Бесплатные модели:")
                    for model in free_models[:5]:
                        print(f"  - {model.get('id', 'unknown')}")
                
                return True
                
            else:
                print(f"❌ Ошибка получения моделей: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_openrouter_api():
    """Тест OpenRouter API с простым запросом"""
    
    print(f"\n🧪 Тест OpenRouter API")
    print("=" * 30)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Попробуем разные модели
    models_to_test = [
        "meta-llama/llama-3.1-8b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "google/gemini-flash-1.5:free",
        "openai/gpt-3.5-turbo"
    ]
    
    for model in models_to_test:
        try:
            print(f"  Тестирую модель: {model}")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://slide-speaker.app",
                "X-Title": "Slide Speaker"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello! Please respond with 'Test successful'."
                    }
                ],
                "max_tokens": 50,
                "temperature": 0.1
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    print(f"  ✅ {model} работает!")
                    print(f"     Ответ: {content}")
                    return model
                else:
                    print(f"  ❌ {model} ошибка: {response.status_code}")
                    print(f"     Ответ: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"  ❌ {model} ошибка: {e}")
    
    return None

if __name__ == "__main__":
    # Сначала проверим доступные модели
    if check_openrouter_models():
        # Затем протестируем API
        working_model = test_openrouter_api()
        
        if working_model:
            print(f"\n🎉 Найдена рабочая модель: {working_model}")
            print(f"📝 Обновите OPENROUTER_MODEL в конфигурации")
        else:
            print(f"\n❌ Не найдено рабочих моделей")
            print(f"📝 Проверьте API ключ и баланс аккаунта")
