#!/usr/bin/env python3
"""
Создание нового Document AI Processor
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def create_document_ai_processor():
    """Создание нового Document AI Processor"""
    
    print("🔧 Создание нового Document AI Processor")
    print("=" * 50)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    location = "us-central1"  # Используем стандартный регион
    
    print(f"📋 Проект: {project_id}")
    print(f"📋 Регион: {location}")
    
    try:
        from google.cloud import documentai
        
        client = documentai.DocumentProcessorServiceClient()
        
        # Создаем Processor
        processor = documentai.Processor(
            display_name="Slide Speaker OCR Processor",
            type_="OCR_PROCESSOR",
            location=location
        )
        
        parent = f"projects/{project_id}/locations/{location}"
        
        print(f"📝 Создаю Processor в регионе: {location}")
        
        operation = client.create_processor(
            parent=parent,
            processor=processor
        )
        
        print(f"⏳ Processor создается... Это может занять несколько минут")
        
        # Ждем завершения операции
        result = operation.result(timeout=300)  # 5 минут
        
        processor_id = result.name.split("/")[-1]
        
        print(f"✅ Processor создан успешно!")
        print(f"📋 Processor ID: {processor_id}")
        print(f"📋 Полное имя: {result.name}")
        
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
        
    except ImportError:
        print("❌ Google Cloud Document AI не установлен")
        return None
    except Exception as e:
        print(f"❌ Ошибка создания Processor: {e}")
        return None

if __name__ == "__main__":
    processor_id = create_document_ai_processor()
    
    if processor_id:
        print(f"\n🎉 Новый Processor создан: {processor_id}")
        print(f"📝 Теперь можно протестировать Document AI")
    else:
        print(f"\n❌ Не удалось создать Processor")
        print(f"📝 Попробуйте создать Processor вручную в Google Cloud Console")
