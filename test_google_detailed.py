#!/usr/bin/env python3
"""
Детальная проверка работы с Google Cloud
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def test_google_cloud_detailed():
    """Детальная проверка работы с Google Cloud"""
    
    print("🔍 Детальная проверка работы с Google Cloud")
    print("=" * 60)
    
    # Проверяем переменные окружения
    print("📋 Проверка переменных окружения:")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("GCP_PROJECT_ID")
    processor_id = os.getenv("GCP_DOC_AI_PROCESSOR_ID")
    
    print(f"  GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")
    print(f"  GCP_PROJECT_ID: {project_id}")
    print(f"  GCP_DOC_AI_PROCESSOR_ID: {processor_id}")
    
    if not credentials_path or not os.path.exists(credentials_path):
        print("❌ Файл ключей не найден!")
        return False
    
    if not project_id:
        print("❌ GCP_PROJECT_ID не установлен!")
        return False
    
    # Проверяем содержимое ключа
    print(f"\n🔑 Проверка Service Account ключа:")
    try:
        import json
        with open(credentials_path, 'r') as f:
            key_data = json.load(f)
        
        print(f"  Тип: {key_data.get('type')}")
        print(f"  Project ID: {key_data.get('project_id')}")
        print(f"  Client Email: {key_data.get('client_email')}")
        print(f"  Private Key ID: {key_data.get('private_key_id', 'N/A')[:20]}...")
        
        if key_data.get('project_id') != project_id:
            print(f"⚠️  Project ID в ключе ({key_data.get('project_id')}) не совпадает с GCP_PROJECT_ID ({project_id})")
        
    except Exception as e:
        print(f"❌ Ошибка чтения ключа: {e}")
        return False
    
    # Проверяем аутентификацию
    print(f"\n🔐 Проверка аутентификации:")
    try:
        from google.auth import default
        credentials, project = default()
        print(f"  ✅ Аутентификация успешна")
        print(f"  Проект: {project}")
        print(f"  Email: {credentials.service_account_email if hasattr(credentials, 'service_account_email') else 'N/A'}")
    except Exception as e:
        print(f"  ❌ Ошибка аутентификации: {e}")
        return False
    
    # Проверяем Document AI
    print(f"\n📄 Проверка Document AI:")
    try:
        from google.cloud import documentai
        
        client = documentai.DocumentProcessorServiceClient()
        print(f"  ✅ Document AI клиент создан")
        
        # Проверяем доступность API
        try:
            # Пробуем получить список процессоров в разных регионах
            regions_to_check = ["us", "us-central1", "europe-west1"]
            
            for region in regions_to_check:
                try:
                    parent = f"projects/{project_id}/locations/{region}"
                    processors = client.list_processors(parent=parent)
                    processor_list = list(processors)
                    print(f"  Регион {region}: {len(processor_list)} процессоров")
                    
                    # Проверяем конкретный процессор
                    if processor_id:
                        processor_name = f"{parent}/processors/{processor_id}"
                        try:
                            processor = client.get_processor(name=processor_name)
                            print(f"  ✅ Processor {processor_id} найден в регионе {region}")
                            print(f"     Название: {processor.display_name}")
                            print(f"     Тип: {processor.type_}")
                            print(f"     Статус: {processor.state.name}")
                            return True
                        except Exception as e:
                            if "not found" in str(e).lower():
                                print(f"  ❌ Processor {processor_id} не найден в регионе {region}")
                            else:
                                print(f"  ⚠️  Ошибка в регионе {region}: {e}")
                                
                except Exception as e:
                    print(f"  ❌ Ошибка подключения к региону {region}: {e}")
                    
        except Exception as e:
            print(f"  ❌ Ошибка проверки API: {e}")
            
    except ImportError:
        print(f"  ❌ Google Cloud Document AI не установлен")
    except Exception as e:
        print(f"  ❌ Ошибка Document AI: {e}")
    
    # Проверяем Gemini
    print(f"\n🤖 Проверка Gemini:")
    try:
        from google.cloud import aiplatform
        from vertexai.generative_models import GenerativeModel
        
        # Проверяем разные регионы
        regions_to_check = ["us-central1", "europe-west1", "europe-west4"]
        
        for region in regions_to_check:
            try:
                print(f"  Проверяю регион: {region}")
                aiplatform.init(project=project_id, location=region)
                
                model = GenerativeModel("gemini-1.5-flash")
                print(f"  ✅ Gemini доступен в регионе: {region}")
                
                # Пробуем простой запрос
                try:
                    response = model.generate_content("Hello")
                    print(f"  ✅ Gemini отвечает в регионе: {region}")
                    return True
                except Exception as e:
                    print(f"  ⚠️  Gemini не отвечает в регионе {region}: {e}")
                    
            except Exception as e:
                print(f"  ❌ Ошибка в регионе {region}: {e}")
                
    except ImportError:
        print(f"  ❌ Google Cloud AI Platform не установлен")
    except Exception as e:
        print(f"  ❌ Ошибка Gemini: {e}")
    
    # Проверяем TTS
    print(f"\n🎤 Проверка Text-to-Speech:")
    try:
        from google.cloud import texttospeech
        
        client = texttospeech.TextToSpeechClient()
        print(f"  ✅ TTS клиент создан")
        
        # Пробуем получить список голосов
        try:
            voices = client.list_voices()
            voice_list = list(voices.voices)
            print(f"  ✅ TTS API доступен: {len(voice_list)} голосов")
            
            # Пробуем синтез
            synthesis_input = texttospeech.SynthesisInput(text="Test")
            voice = texttospeech.VoiceSelectionParams(
                language_code="ru-RU",
                name="ru-RU-Wavenet-A"
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            print(f"  ✅ TTS синтез работает: {len(response.audio_content)} байт")
            return True
            
        except Exception as e:
            print(f"  ❌ Ошибка TTS API: {e}")
            
    except ImportError:
        print(f"  ❌ Google Cloud Text-to-Speech не установлен")
    except Exception as e:
        print(f"  ❌ Ошибка TTS: {e}")
    
    return False

if __name__ == "__main__":
    success = test_google_cloud_detailed()
    
    if success:
        print(f"\n🎉 Google Cloud работает правильно!")
    else:
        print(f"\n⚠️  Есть проблемы с Google Cloud")
        print(f"📝 Рекомендации:")
        print(f"1. Проверьте права доступа Service Account")
        print(f"2. Убедитесь, что API включены в проекте")
        print(f"3. Проверьте правильность Processor ID")
