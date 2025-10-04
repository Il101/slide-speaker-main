#!/usr/bin/env python3
"""
Диагностика проблем с Google Cloud сервисами
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def diagnose_gcp_issues():
    """Диагностика проблем с Google Cloud сервисами"""
    
    print("🔍 Диагностика проблем с Google Cloud сервисами")
    print("=" * 60)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    processor_id = os.getenv("GCP_DOC_AI_PROCESSOR_ID")
    
    print(f"📋 Проект: {project_id}")
    print(f"📋 Processor ID: {processor_id}")
    
    # 1. Проверка Document AI Processor
    print(f"\n🔍 Проверка Document AI Processor:")
    
    regions_to_check = ["us", "us-central1", "europe-west1", "europe-west4"]
    
    try:
        from google.cloud import documentai
        
        for region in regions_to_check:
            try:
                processor_name = f"projects/{project_id}/locations/{region}/processors/{processor_id}"
                print(f"  Проверяю регион: {region}")
                
                client = documentai.DocumentProcessorServiceClient()
                
                try:
                    processor = client.get_processor(name=processor_name)
                    print(f"  ✅ Processor найден в регионе: {region}")
                    print(f"     Название: {processor.display_name}")
                    print(f"     Тип: {processor.type_}")
                    print(f"     Статус: {processor.state.name}")
                    return region
                except Exception as e:
                    if "not found" in str(e).lower():
                        print(f"  ❌ Processor не найден в регионе: {region}")
                    else:
                        print(f"  ⚠️  Ошибка в регионе {region}: {e}")
                        
            except Exception as e:
                print(f"  ❌ Ошибка подключения к региону {region}: {e}")
                
    except ImportError:
        print("❌ Google Cloud Document AI не установлен")
    
    # 2. Проверка Gemini в разных регионах
    print(f"\n🤖 Проверка Gemini в разных регионах:")
    
    try:
        from google.cloud import aiplatform
        
        for region in ["us-central1", "us-east1", "europe-west1", "europe-west4"]:
            try:
                print(f"  Проверяю регион: {region}")
                
                aiplatform.init(project=project_id, location=region)
                
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
    
    print(f"\n📝 Рекомендации:")
    print(f"1. Проверьте в Google Cloud Console, в каком регионе создан Document AI Processor")
    print(f"2. Убедитесь, что Vertex AI включен в нужном регионе")
    print(f"3. Возможно, нужно создать новый Processor в правильном регионе")
    
    return None

if __name__ == "__main__":
    diagnose_gcp_issues()
