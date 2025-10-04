#!/usr/bin/env python3
"""
Скрипт для получения API ключа Gemini
"""
import os
import json
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account

def get_gemini_api_key():
    """Получить API ключ для Gemini через Google Cloud Console"""
    print("🔑 Получение API ключа для Gemini...")
    print("=" * 50)
    
    try:
        # Загружаем service account
        credentials_path = '/app/keys/gcp-sa.json'
        if not os.path.exists(credentials_path):
            print(f"❌ Файл ключа не найден: {credentials_path}")
            return None
        
        with open(credentials_path, 'r') as f:
            sa_info = json.load(f)
        
        project_id = sa_info.get('project_id', 'inspiring-keel-473421-j2')
        print(f"📋 Project ID: {project_id}")
        
        # Инструкции для получения API ключа
        print(f"\n📝 ИНСТРУКЦИИ ПО ПОЛУЧЕНИЮ API КЛЮЧА:")
        print("=" * 50)
        print("1. Откройте Google Cloud Console:")
        print(f"   https://console.cloud.google.com/apis/credentials?project={project_id}")
        print("\n2. Нажмите 'Создать учетные данные' -> 'API ключ'")
        print("\n3. Скопируйте созданный API ключ")
        print("\n4. Добавьте его в docker.env:")
        print("   GEMINI_API_KEY=ваш_api_ключ_здесь")
        print("\n5. Перезапустите контейнеры:")
        print("   docker-compose restart backend")
        
        return None
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    get_gemini_api_key()
