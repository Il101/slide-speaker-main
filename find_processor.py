#!/usr/bin/env python3
"""
Поиск Document AI Processor в разных регионах
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def find_document_ai_processor():
    """Поиск Document AI Processor в разных регионах"""
    
    print("🔍 Поиск Document AI Processor")
    print("=" * 50)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    processor_id = os.getenv("GCP_DOC_AI_PROCESSOR_ID")
    
    print(f"📋 Проект: {project_id}")
    print(f"📋 Processor ID: {processor_id}")
    
    try:
        from google.cloud import documentai
        
        # Расширенный список регионов для проверки
        regions_to_check = [
            "us", "us-central1", "us-east1", "us-west1", "us-west2", "us-west3", "us-west4",
            "europe-west1", "europe-west2", "europe-west3", "europe-west4", "europe-west6", "europe-west8", "europe-west9",
            "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2", "asia-northeast3",
            "asia-south1", "asia-southeast1", "asia-southeast2"
        ]
        
        found_regions = []
        
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
                    found_regions.append(region)
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if "not found" in error_msg:
                        print(f"  ❌ Processor не найден в регионе: {region}")
                    elif "permission" in error_msg:
                        print(f"  ⚠️  Нет прав доступа в регионе: {region}")
                    else:
                        print(f"  ⚠️  Ошибка в регионе {region}: {e}")
                        
            except Exception as e:
                print(f"  ❌ Ошибка подключения к региону {region}: {e}")
        
        if found_regions:
            print(f"\n🎉 Processor найден в регионах: {', '.join(found_regions)}")
            print(f"📝 Рекомендуемый регион: {found_regions[0]}")
            
            # Обновляем конфигурацию
            config_file = "backend_env_final.env"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                # Заменяем GCP_LOCATION
                import re
                new_content = re.sub(
                    r'GCP_LOCATION=.*',
                    f'GCP_LOCATION={found_regions[0]}',
                    content
                )
                
                with open(config_file, 'w') as f:
                    f.write(new_content)
                
                print(f"✅ Конфигурация обновлена: GCP_LOCATION={found_regions[0]}")
        else:
            print(f"\n❌ Processor не найден ни в одном регионе!")
            print(f"📝 Возможные причины:")
            print(f"   1. Processor ID неправильный: {processor_id}")
            print(f"   2. Processor был удален")
            print(f"   3. Недостаточно прав доступа")
            print(f"   4. Нужно создать новый Processor")
                
    except ImportError:
        print("❌ Google Cloud Document AI не установлен")

if __name__ == "__main__":
    find_document_ai_processor()
