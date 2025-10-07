#!/usr/bin/env python3
"""
Тест разных моделей Gemini
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def test_gemini_models():
    """Тест разных моделей Gemini"""
    
    print("🤖 Тест разных моделей Gemini")
    print("=" * 50)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    
    print(f"📋 Проект: {project_id}")
    
    try:
        from google.cloud import aiplatform
        from vertexai.generative_models import GenerativeModel
        
        # Разные модели для тестирования
        models_to_test = [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-1.0-pro",
            "gemini-1.5-flash-001",
            "gemini-1.5-pro-001"
        ]
        
        # Регионы для тестирования
        regions_to_test = ["us-central1", "europe-west1", "europe-west4"]
        
        for region in regions_to_test:
            print(f"\n🌍 Регион: {region}")
            
            try:
                aiplatform.init(project=project_id, location=region)
                
                for model_name in models_to_test:
                    try:
                        print(f"  Тестирую модель: {model_name}")
                        
                        model = GenerativeModel(model_name)
                        
                        # Пробуем простой запрос
                        response = model.generate_content("Hello")
                        
                        print(f"  ✅ {model_name} работает в {region}")
                        print(f"     Ответ: {response.text[:50]}...")
                        
                        # Обновляем конфигурацию
                        config_file = 'backend/.env'
                        if os.path.exists(config_file):
                            with open(config_file, 'r') as f:
                                content = f.read()
                            
                            import re
                            new_content = re.sub(
                                r'GEMINI_MODEL=.*',
                                f'GEMINI_MODEL={model_name}',
                                content
                            )
                            new_content = re.sub(
                                r'GEMINI_LOCATION=.*',
                                f'GEMINI_LOCATION={region}',
                                new_content
                            )
                            
                            with open(config_file, 'w') as f:
                                f.write(new_content)
                            
                            print(f"  ✅ Конфигурация обновлена: {model_name} в {region}")
                        
                        return True
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "not found" in error_msg:
                            print(f"  ❌ {model_name} не найден в {region}")
                        else:
                            print(f"  ⚠️  {model_name} ошибка в {region}: {e}")
                            
            except Exception as e:
                print(f"  ❌ Ошибка подключения к региону {region}: {e}")
                
    except ImportError:
        print("❌ Google Cloud AI Platform не установлен")
    except Exception as e:
        print(f"❌ Ошибка Gemini: {e}")
    
    return False

if __name__ == "__main__":
    success = test_gemini_models()
    
    if success:
        print(f"\n🎉 Найдена рабочая модель Gemini!")
    else:
        print(f"\n❌ Не найдена рабочая модель Gemini")
        print(f"📝 Рекомендации:")
        print(f"1. Проверьте, включен ли Vertex AI API")
        print(f"2. Убедитесь, что у Service Account есть права aiplatform.user")
        print(f"3. Попробуйте другой проект или регион")
