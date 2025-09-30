#!/usr/bin/env python3
"""
Тест Gemini через Google AI API
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def test_gemini_google_ai():
    """Тест Gemini через Google AI API"""
    
    print("🤖 Тест Gemini через Google AI API")
    print("=" * 50)
    
    try:
        import google.generativeai as genai
        
        # Получаем API ключ из Service Account
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not credentials_path or not os.path.exists(credentials_path):
            print("❌ Файл ключей не найден!")
            return False
        
        # Читаем ключ
        import json
        with open(credentials_path, 'r') as f:
            key_data = json.load(f)
        
        # Для Google AI API нужен API ключ, а не Service Account
        # Попробуем использовать Service Account для получения токена
        from google.auth import default
        from google.auth.transport.requests import Request
        
        credentials, project = default()
        
        # Получаем токен доступа
        credentials.refresh(Request())
        access_token = credentials.token
        
        print(f"✅ Получен токен доступа")
        print(f"📋 Проект: {project}")
        
        # Настраиваем API
        genai.configure(api_key=access_token)
        
        # Тестируем модель
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        try:
            response = model.generate_content("Hello, how are you?")
            print(f"✅ Gemini работает через Google AI API!")
            print(f"📝 Ответ: {response.text[:100]}...")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка генерации: {e}")
            return False
            
    except ImportError:
        print("❌ Google Generative AI не установлен")
        print("📝 Установите: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_google_ai()
    
    if success:
        print(f"\n🎉 Gemini работает через Google AI API!")
    else:
        print(f"\n❌ Gemini не работает через Google AI API")
        print(f"📝 Рекомендации:")
        print(f"1. Установите google-generativeai: pip install google-generativeai")
        print(f"2. Проверьте права доступа Service Account")
        print(f"3. Попробуйте другой подход")
