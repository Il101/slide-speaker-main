#!/usr/bin/env python3
"""
Поиск всех процессоров в регионе us
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def find_all_processors():
    """Поиск всех процессоров в регионе us"""
    
    print("🔍 Поиск всех процессоров в регионе us")
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
        
        for i, processor in enumerate(processor_list, 1):
            processor_id = processor.name.split("/")[-1]
            print(f"\n📋 Processor {i}:")
            print(f"   ID: {processor_id}")
            print(f"   Название: {processor.display_name}")
            print(f"   Тип: {processor.type_}")
            print(f"   Статус: {processor.state.name}")
            print(f"   Полное имя: {processor.name}")
            
            # Проверяем, есть ли slideSpeaker
            if "slideSpeaker" in processor.display_name.lower() or "slidespeaker" in processor.display_name.lower():
                print(f"🎯 Найден Processor slideSpeaker!")
                
                # Обновляем конфигурацию
                config_file = 'backend/.env'
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
        
        print(f"\n❌ Processor slideSpeaker не найден в регионе {location}")
        print(f"📝 Доступные процессоры:")
        for i, processor in enumerate(processor_list, 1):
            print(f"   {i}. {processor.display_name} ({processor.name.split('/')[-1]})")
        
        return None
        
    except ImportError:
        print("❌ Google Cloud Document AI не установлен")
        return None
    except Exception as e:
        print(f"❌ Ошибка поиска процессоров: {e}")
        return None

if __name__ == "__main__":
    processor_id = find_all_processors()
    
    if processor_id:
        print(f"\n🎉 Найден Processor slideSpeaker: {processor_id}")
        print(f"📝 Теперь можно протестировать Document AI")
    else:
        print(f"\n❌ Processor slideSpeaker не найден")
        print(f"📝 Используйте один из доступных процессоров")
