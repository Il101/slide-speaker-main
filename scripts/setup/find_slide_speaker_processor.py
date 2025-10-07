#!/usr/bin/env python3
"""
Поиск Processor slideSpeaker в европейском регионе
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def find_slide_speaker_processor():
    """Поиск Processor slideSpeaker в европейском регионе"""
    
    print("🔍 Поиск Processor slideSpeaker в европейском регионе")
    print("=" * 60)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    
    print(f"📋 Проект: {project_id}")
    
    try:
        from google.cloud import documentai
        
        client = documentai.DocumentProcessorServiceClient()
        
        # Проверяем европейский регион "eu"
        location = "eu"
        parent = f"projects/{project_id}/locations/{location}"
        
        print(f"📝 Ищу процессоры в регионе: {location}")
        
        try:
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
                
                # Если это slideSpeaker, обновляем конфигурацию
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
            
            print(f"❌ Processor slideSpeaker не найден в регионе {location}")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка подключения к региону {location}: {e}")
            return None
        
    except ImportError:
        print("❌ Google Cloud Document AI не установлен")
        return None
    except Exception as e:
        print(f"❌ Ошибка поиска процессоров: {e}")
        return None

if __name__ == "__main__":
    processor_id = find_slide_speaker_processor()
    
    if processor_id:
        print(f"\n🎉 Найден Processor slideSpeaker: {processor_id}")
        print(f"📝 Теперь можно протестировать Document AI в европейском регионе")
    else:
        print(f"\n❌ Processor slideSpeaker не найден")
        print(f"📝 Проверьте правильность названия в Google Cloud Console")
