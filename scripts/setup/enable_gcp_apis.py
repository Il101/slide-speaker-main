#!/usr/bin/env python3
"""
Скрипт для включения Google Cloud Text-to-Speech API
"""
import subprocess
import sys
import os

def enable_tts_api():
    """Включить Text-to-Speech API через gcloud CLI"""
    
    # Получаем project_id из переменных окружения
    project_id = os.getenv("GCP_PROJECT_ID", "inspiring-keel-473421-j2")
    
    print(f"🔧 Включение Text-to-Speech API для проекта: {project_id}")
    
    try:
        # Включаем Text-to-Speech API
        result = subprocess.run([
            "gcloud", "services", "enable", "texttospeech.googleapis.com",
            "--project", project_id
        ], capture_output=True, text=True, check=True)
        
        print("✅ Text-to-Speech API успешно включен!")
        print(result.stdout)
        
        # Также включаем другие необходимые API
        apis_to_enable = [
            "documentai.googleapis.com",
            "aiplatform.googleapis.com"
        ]
        
        for api in apis_to_enable:
            try:
                subprocess.run([
                    "gcloud", "services", "enable", api,
                    "--project", project_id
                ], capture_output=True, text=True, check=True)
                print(f"✅ {api} включен")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  {api}: {e.stderr}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при включении API: {e.stderr}")
        print("\n📝 Ручная инструкция:")
        print("1. Перейдите в Google Cloud Console")
        print("2. Выберите ваш проект")
        print("3. Перейдите в 'APIs & Services' → 'Library'")
        print("4. Найдите 'Cloud Text-to-Speech API' и нажмите 'Enable'")
        return False
    except FileNotFoundError:
        print("❌ gcloud CLI не найден")
        print("📝 Установите Google Cloud CLI: https://cloud.google.com/sdk/docs/install")
        return False

if __name__ == "__main__":
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    
    success = enable_tts_api()
    
    if success:
        print("\n🎉 Все API включены! Теперь можно тестировать TTS.")
    else:
        print("\n⚠️  Включите API вручную через Google Cloud Console")
