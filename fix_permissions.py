#!/usr/bin/env python3
"""
Скрипт для исправления прав доступа Service Account
"""
import subprocess
import os
import sys

def fix_service_account_permissions():
    """Исправить права доступа для Service Account"""
    
    project_id = os.getenv("GCP_PROJECT_ID", "inspiring-keel-473421-j2")
    service_account_email = "slide-speaker-service@inspiring-keel-473421-j2.iam.gserviceaccount.com"
    
    print(f"🔧 Исправление прав доступа для Service Account: {service_account_email}")
    print(f"📋 Проект: {project_id}")
    print("=" * 60)
    
    # Роли, которые нужно добавить
    roles_to_add = [
        "roles/documentai.apiUser",           # Document AI API User
        "roles/aiplatform.user",             # Vertex AI User  
        "roles/cloudtts.serviceAgent",        # Cloud Text-to-Speech Service Agent
        "roles/storage.objectAdmin"           # Cloud Storage Object Admin
    ]
    
    print("\n📝 Добавление ролей:")
    
    for role in roles_to_add:
        try:
            print(f"  Добавляю роль: {role}")
            
            result = subprocess.run([
                "gcloud", "projects", "add-iam-policy-binding", project_id,
                "--member", f"serviceAccount:{service_account_email}",
                "--role", role
            ], capture_output=True, text=True, check=True)
            
            print(f"  ✅ Роль {role} добавлена успешно")
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Ошибка добавления роли {role}: {e.stderr}")
        except FileNotFoundError:
            print("❌ gcloud CLI не найден")
            print("📝 Установите Google Cloud CLI: https://cloud.google.com/sdk/docs/install")
            return False
    
    print("\n🎉 Права доступа обновлены!")
    print("\n📝 Ручная инструкция (если gcloud CLI недоступен):")
    print("1. Перейдите в Google Cloud Console")
    print("2. Выберите проект → IAM & Admin → IAM")
    print("3. Найдите Service Account: slide-speaker-service@inspiring-keel-473421-j2.iam.gserviceaccount.com")
    print("4. Нажмите 'Edit' (карандаш)")
    print("5. Добавьте роли:")
    for role in roles_to_add:
        print(f"   - {role}")
    print("6. Сохраните изменения")
    
    return True

if __name__ == "__main__":
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    
    fix_service_account_permissions()
