#!/usr/bin/env python3
"""
Проверка доступности Document AI в европейских регионах
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def check_document_ai_european_regions():
    """Проверка доступности Document AI в европейских регионах"""
    
    print("🌍 Проверка доступности Document AI в европейских регионах")
    print("=" * 60)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    processor_id = os.getenv("GCP_DOC_AI_PROCESSOR_ID")
    
    print(f"📋 Проект: {project_id}")
    print(f"📋 Processor ID: {processor_id}")
    
    try:
        from google.cloud import documentai
        
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
                
                processor_name = f"projects/{project_id}/locations/{region}/processors/{processor_id}"
                
                client = documentai.DocumentProcessorServiceClient()
                
                try:
                    processor = client.get_processor(name=processor_name)
                    print(f"  ✅ Processor найден в регионе: {region}")
                    print(f"     Название: {processor.display_name}")
                    print(f"     Тип: {processor.type_}")
                    print(f"     Статус: {processor.state.name}")
                    available_regions.append(region)
                    
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
        
        if available_regions:
            print(f"\n🎉 Processor найден в европейских регионах: {', '.join(available_regions)}")
            print(f"📝 Рекомендуемый регион: {available_regions[0]}")
            
            # Обновляем конфигурацию
            config_file = 'backend/.env'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                # Заменяем GCP_LOCATION
                import re
                new_content = re.sub(
                    r'GCP_LOCATION=.*',
                    f'GCP_LOCATION={available_regions[0]}',
                    content
                )
                
                with open(config_file, 'w') as f:
                    f.write(new_content)
                
                print(f"✅ Конфигурация обновлена: GCP_LOCATION={available_regions[0]}")
        else:
            print(f"\n❌ Processor не найден ни в одном европейском регионе!")
            print(f"📝 Возможные причины:")
            print(f"   1. Processor ID неправильный: {processor_id}")
            print(f"   2. Processor был удален")
            print(f"   3. Нужно создать новый Processor в европейском регионе")
            
            # Предлагаем создать новый Processor
            print(f"\n💡 Рекомендация: Создать новый Processor в europe-west1")
            
            config_file = 'backend/.env'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                import re
                new_content = re.sub(
                    r'GCP_LOCATION=.*',
                    f'GCP_LOCATION=europe-west1',
                    content
                )
                
                with open(config_file, 'w') as f:
                    f.write(new_content)
                
                print(f"✅ Конфигурация обновлена: GCP_LOCATION=europe-west1")
                print(f"📝 Теперь нужно создать новый Processor в Google Cloud Console")
                
    except ImportError:
        print("❌ Google Cloud Document AI не установлен")

if __name__ == "__main__":
    check_document_ai_european_regions()
