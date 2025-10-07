#!/usr/bin/env python3
"""
Проверка доступа к Gemini через Google AI Studio API
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def check_gemini_ai_studio():
    """Проверка доступа к Gemini через Google AI Studio API"""
    
    print("🤖 Проверка доступа к Gemini через Google AI Studio API")
    print("=" * 60)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    
    print(f"📋 Проект: {project_id}")
    
    try:
        import google.generativeai as genai
        
        # Получаем токен доступа из Service Account
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
        
        # Тестируем разные модели
        models_to_test = [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-1.0-pro"
        ]
        
        working_models = []
        
        for model_name in models_to_test:
            try:
                print(f"  Тестирую модель: {model_name}")
                
                model = genai.GenerativeModel(model_name)
                
                # Пробуем простой запрос
                response = model.generate_content("Hello, how are you?")
                
                print(f"  ✅ {model_name} работает!")
                print(f"     Ответ: {response.text[:50]}...")
                
                working_models.append({
                    "model": model_name,
                    "response": response.text[:100]
                })
                
            except Exception as e:
                print(f"  ❌ {model_name} не работает: {e}")
        
        if working_models:
            print(f"\n🎉 Найдены рабочие модели:")
            for model_info in working_models:
                print(f"  ✅ {model_info['model']}")
                print(f"     Ответ: {model_info['response']}...")
            
            # Обновляем конфигурацию
            best_model = working_models[0]["model"]
            config_file = 'backend/.env'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                import re
                new_content = re.sub(
                    r'GEMINI_MODEL=.*',
                    f'GEMINI_MODEL={best_model}',
                    content
                )
                
                with open(config_file, 'w') as f:
                    f.write(new_content)
                
                print(f"\n✅ Конфигурация обновлена:")
                print(f"   GEMINI_MODEL={best_model}")
            
            return True
        else:
            print(f"\n❌ Не найдено рабочих моделей")
            return False
            
    except ImportError:
        print("❌ Google Generative AI не установлен")
        print("📝 Установите: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = check_gemini_ai_studio()
    
    if success:
        print(f"\n🎉 Найдена рабочая модель Gemini!")
        print(f"📝 Теперь можно протестировать LLM")
    else:
        print(f"\n❌ Не найдена рабочая модель Gemini")
        print(f"📝 Рекомендации:")
        print(f"1. Проверьте права доступа Service Account")
        print(f"2. Убедитесь, что Generative Language API включен")
        print(f"3. Попробуйте другой подход")
