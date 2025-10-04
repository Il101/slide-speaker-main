#!/usr/bin/env python3
"""
Скрипт для проверки доступных регионов и процессоров Google Cloud
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def check_regions_and_processors():
    """Проверить доступные регионы и процессоры"""
    
    project_id = os.getenv("GCP_PROJECT_ID")
    processor_id = os.getenv("GCP_DOC_AI_PROCESSOR_ID")
    
    print(f"🔍 Проверка регионов и процессоров для проекта: {project_id}")
    print(f"📋 Processor ID: {processor_id}")
    print("=" * 60)
    
    # Проверяем разные регионы для Document AI
    regions_to_check = ["us", "us-central1", "europe-west1", "europe-west4", "asia-southeast1"]
    
    print("\n🌍 Проверка регионов Document AI:")
    
    try:
        from google.cloud import documentai
        
        for region in regions_to_check:
            try:
                processor_name = f"projects/{project_id}/locations/{region}/processors/{processor_id}"
                print(f"  Проверяю регион: {region}")
                
                # Создаем клиент для этого региона
                client = documentai.DocumentProcessorServiceClient()
                
                # Пытаемся получить информацию о процессоре
                try:
                    processor = client.get_processor(name=processor_name)
                    print(f"  ✅ Процессор найден в регионе: {region}")
                    print(f"     Название: {processor.display_name}")
                    print(f"     Тип: {processor.type_}")
                    print(f"     Статус: {processor.state.name}")
                    return region
                except Exception as e:
                    if "not found" in str(e).lower():
                        print(f"  ❌ Процессор не найден в регионе: {region}")
                    else:
                        print(f"  ⚠️  Ошибка в регионе {region}: {e}")
                        
            except Exception as e:
                print(f"  ❌ Ошибка подключения к региону {region}: {e}")
                
    except ImportError:
        print("❌ Google Cloud Document AI не установлен")
        return None
    
    print("\n🤖 Проверка регионов Gemini:")
    
    try:
        from google.cloud import aiplatform
        
        for region in regions_to_check:
            try:
                print(f"  Проверяю регион: {region}")
                
                # Инициализируем Vertex AI для этого региона
                aiplatform.init(project=project_id, location=region)
                
                # Пытаемся получить список моделей
                from vertexai.generative_models import GenerativeModel
                
                try:
                    model = GenerativeModel("gemini-1.5-flash")
                    print(f"  ✅ Gemini доступен в регионе: {region}")
                    return region
                except Exception as e:
                    if "not found" in str(e).lower():
                        print(f"  ❌ Gemini не найден в регионе: {region}")
                    else:
                        print(f"  ⚠️  Ошибка в регионе {region}: {e}")
                        
            except Exception as e:
                print(f"  ❌ Ошибка подключения к региону {region}: {e}")
                
    except ImportError:
        print("❌ Google Cloud AI Platform не установлен")
        return None
    
    print("\n📝 Рекомендации:")
    print("1. Проверьте в Google Cloud Console, в каком регионе создан Document AI Processor")
    print("2. Убедитесь, что Vertex AI включен в нужном регионе")
    print("3. Используйте тот же регион для всех сервисов")
    
    return None

if __name__ == "__main__":
    check_regions_and_processors()
