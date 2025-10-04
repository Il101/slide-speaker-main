#!/usr/bin/env python3
"""
Проверка доступности Gemini в европейских регионах
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def check_gemini_european_regions():
    """Проверка доступности Gemini в европейских регионах"""
    
    print("🌍 Проверка доступности Gemini в европейских регионах")
    print("=" * 60)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    
    print(f"📋 Проект: {project_id}")
    
    try:
        from google.cloud import aiplatform
        
        # Европейские регионы для проверки
        european_regions = [
            "europe-west1", "europe-west2", "europe-west3", "europe-west4", 
            "europe-west6", "europe-west8", "europe-west9", "europe-west10",
            "europe-north1", "europe-central2", "europe-southwest1"
        ]
        
        available_regions = []
        
        for region in european_regions:
            try:
                print(f"  Проверяю регион: {region}")
                
                aiplatform.init(project=project_id, location=region)
                
                from vertexai.generative_models import GenerativeModel
                
                try:
                    model = GenerativeModel("gemini-1.5-flash")
                    print(f"  ✅ Gemini доступен в регионе: {region}")
                    available_regions.append(region)
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if "not found" in error_msg:
                        print(f"  ❌ Gemini не найден в регионе: {region}")
                    elif "permission" in error_msg:
                        print(f"  ⚠️  Нет прав доступа в регионе: {region}")
                    else:
                        print(f"  ⚠️  Ошибка в регионе {region}: {e}")
                        
            except Exception as e:
                print(f"  ❌ Ошибка подключения к региону {region}: {e}")
        
        if available_regions:
            print(f"\n🎉 Gemini доступен в европейских регионах: {', '.join(available_regions)}")
            print(f"📝 Рекомендуемый регион: {available_regions[0]}")
            
            # Обновляем конфигурацию
            config_file = "backend_env_final.env"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                # Заменяем GEMINI_LOCATION
                import re
                new_content = re.sub(
                    r'GEMINI_LOCATION=.*',
                    f'GEMINI_LOCATION={available_regions[0]}',
                    content
                )
                
                with open(config_file, 'w') as f:
                    f.write(new_content)
                
                print(f"✅ Конфигурация обновлена: GEMINI_LOCATION={available_regions[0]}")
        else:
            print(f"\n❌ Gemini не доступен ни в одном европейском регионе!")
            print(f"📝 Возможные причины:")
            print(f"   1. Vertex AI не включен в европейских регионах")
            print(f"   2. Gemini не поддерживается в Европе")
            print(f"   3. Нужно использовать регион us-central1")
            
            # Предлагаем использовать us-central1 как fallback
            print(f"\n💡 Рекомендация: Использовать us-central1 для Gemini")
            
            config_file = "backend_env_final.env"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                import re
                new_content = re.sub(
                    r'GEMINI_LOCATION=.*',
                    f'GEMINI_LOCATION=us-central1',
                    content
                )
                
                with open(config_file, 'w') as f:
                    f.write(new_content)
                
                print(f"✅ Конфигурация обновлена: GEMINI_LOCATION=us-central1")
                
    except ImportError:
        print("❌ Google Cloud AI Platform не установлен")

if __name__ == "__main__":
    check_gemini_european_regions()
