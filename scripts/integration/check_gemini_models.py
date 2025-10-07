#!/usr/bin/env python3
"""
Проверка доступных моделей Gemini в проекте
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def check_gemini_models():
    """Проверка доступных моделей Gemini"""
    
    print("🤖 Проверка доступных моделей Gemini")
    print("=" * 50)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    current_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    current_location = os.getenv("GEMINI_LOCATION", "europe-west1")
    
    print(f"📋 Проект: {project_id}")
    print(f"📋 Текущая модель: {current_model}")
    print(f"📋 Текущий регион: {current_location}")
    
    try:
        from google.cloud import aiplatform
        from vertexai.generative_models import GenerativeModel
        
        # Проверяем разные модели в разных регионах
        models_to_test = [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-1.0-pro",
            "gemini-1.5-flash-001",
            "gemini-1.5-pro-001",
            "gemini-1.0-pro-001"
        ]
        
        regions_to_test = ["us-central1", "europe-west1", "europe-west4"]
        
        working_combinations = []
        
        for region in regions_to_test:
            print(f"\n🌍 Регион: {region}")
            
            try:
                aiplatform.init(project=project_id, location=region)
                
                for model_name in models_to_test:
                    try:
                        print(f"  Тестирую модель: {model_name}")
                        
                        model = GenerativeModel(model_name)
                        
                        # Пробуем простой запрос
                        response = model.generate_content("Hello, how are you?")
                        
                        print(f"  ✅ {model_name} работает в {region}")
                        print(f"     Ответ: {response.text[:50]}...")
                        
                        working_combinations.append({
                            "model": model_name,
                            "region": region,
                            "response": response.text[:100]
                        })
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "not found" in error_msg:
                            print(f"  ❌ {model_name} не найден в {region}")
                        elif "permission" in error_msg:
                            print(f"  ⚠️  Нет прав доступа для {model_name} в {region}")
                        else:
                            print(f"  ⚠️  {model_name} ошибка в {region}: {e}")
                            
            except Exception as e:
                print(f"  ❌ Ошибка подключения к региону {region}: {e}")
        
        if working_combinations:
            print(f"\n🎉 Найдены рабочие комбинации:")
            for combo in working_combinations:
                print(f"  ✅ {combo['model']} в {combo['region']}")
                print(f"     Ответ: {combo['response']}...")
            
            # Обновляем конфигурацию с первой рабочей комбинацией
            best_combo = working_combinations[0]
            config_file = 'backend/.env'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                import re
                new_content = re.sub(
                    r'GEMINI_MODEL=.*',
                    f'GEMINI_MODEL={best_combo["model"]}',
                    content
                )
                new_content = re.sub(
                    r'GEMINI_LOCATION=.*',
                    f'GEMINI_LOCATION={best_combo["region"]}',
                    new_content
                )
                
                with open(config_file, 'w') as f:
                    f.write(new_content)
                
                print(f"\n✅ Конфигурация обновлена:")
                print(f"   GEMINI_MODEL={best_combo['model']}")
                print(f"   GEMINI_LOCATION={best_combo['region']}")
            
            return True
        else:
            print(f"\n❌ Не найдено рабочих комбинаций моделей")
            print(f"📝 Возможные причины:")
            print(f"1. Проект не имеет доступа к Gemini")
            print(f"2. Vertex AI не включен в нужных регионах")
            print(f"3. Недостаточно прав доступа")
            print(f"4. Проект находится в ограниченном регионе")
            
            return False
                
    except ImportError:
        print("❌ Google Cloud AI Platform не установлен")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = check_gemini_models()
    
    if success:
        print(f"\n🎉 Найдена рабочая модель Gemini!")
        print(f"📝 Теперь можно протестировать LLM")
    else:
        print(f"\n❌ Не найдена рабочая модель Gemini")
        print(f"📝 Рекомендации:")
        print(f"1. Проверьте права доступа Service Account")
        print(f"2. Убедитесь, что Vertex AI включен")
        print(f"3. Попробуйте другой проект")
