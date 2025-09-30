#!/usr/bin/env python3
"""
Поиск существующего Document AI Processor
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def find_existing_processor():
    """Поиск существующего Document AI Processor"""
    
    print("🔍 Поиск существующего Document AI Processor")
    print("=" * 50)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    location = "us"
    
    print(f"📋 Проект: {project_id}")
    print(f"📋 Регион: {location}")
    
    try:
        from google.cloud import documentai
        
        client = documentai.DocumentProcessorServiceClient()
        
        parent = f"projects/{project_id}/locations/{location}"
        
        print(f"📝 Ищу процессоры в регионе: {location}")
        
        processors = client.list_processors(parent=parent)
        processor_list = list(processors)
        
        print(f"📊 Найдено процессоров: {len(processor_list)}")
        
        for processor in processor_list:
            processor_id = processor.name.split("/")[-1]
            print(f"\n✅ Processor найден:")
            print(f"   ID: {processor_id}")
            print(f"   Название: {processor.display_name}")
            print(f"   Тип: {processor.type_}")
            print(f"   Статус: {processor.state.name}")
            print(f"   Полное имя: {processor.name}")
            
            # Обновляем конфигурацию
            config_file = "backend_env_final.env"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                # Заменяем Processor ID и регион
                import re
                new_content = re.sub(
                    r'GCP_DOC_AI_PROCESSOR_ID=.*',
                    f'GCP_DOC_AI_PROCESSOR_ID={processor_id}',
                    content
                )
                new_content = re.sub(
                    r'GCP_LOCATION=.*',
                    f'GCP_LOCATION={location}',
                    new_content
                )
                
                with open(config_file, 'w') as f:
                    f.write(new_content)
                
                print(f"✅ Конфигурация обновлена:")
                print(f"   GCP_DOC_AI_PROCESSOR_ID={processor_id}")
                print(f"   GCP_LOCATION={location}")
            
            return processor_id
        
        print(f"❌ Процессоры не найдены")
        return None
        
    except ImportError:
        print("❌ Google Cloud Document AI не установлен")
        return None
    except Exception as e:
        print(f"❌ Ошибка поиска процессоров: {e}")
        return None

if __name__ == "__main__":
    processor_id = find_existing_processor()
    
    if processor_id:
        print(f"\n🎉 Найден Processor: {processor_id}")
        print(f"📝 Теперь можно протестировать Document AI")
    else:
        print(f"\n❌ Процессоры не найдены")
        print(f"📝 Создайте Processor в Google Cloud Console")
