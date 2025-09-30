#!/usr/bin/env python3
"""
Финальный тест системы Slide Speaker
Проверяет все основные функции: upload, manifest, демо режим
"""

import requests
import json
import time

def test_system():
    base_url = "http://localhost:8001"
    
    print("🚀 Тестирование системы Slide Speaker")
    print("=" * 50)
    
    # 1. Проверка health endpoint
    print("\n1. Проверка health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data['message']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # 2. Проверка демо режима
    print("\n2. Проверка демо режима...")
    try:
        response = requests.get(f"{base_url}/lessons/demo-lesson/manifest", timeout=5)
        if response.status_code == 200:
            data = response.json()
            slides_count = len(data['slides'])
            print(f"✅ Демо режим: {slides_count} слайдов")
            
            # Проверяем структуру первого слайда
            first_slide = data['slides'][0]
            required_fields = ['id', 'image', 'audio', 'cues']
            if all(field in first_slide for field in required_fields):
                print(f"✅ Структура слайда корректна")
                print(f"   - ID: {first_slide['id']}")
                print(f"   - Изображение: {first_slide['image']}")
                print(f"   - Аудио: {first_slide['audio']}")
                print(f"   - Эффектов: {len(first_slide['cues'])}")
            else:
                print(f"❌ Неверная структура слайда")
                return False
        else:
            print(f"❌ Демо режим failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Демо режим failed: {e}")
        return False
    
    # 3. Тест upload
    print("\n3. Тест загрузки файла...")
    try:
        # Создаем тестовый файл
        test_content = b"Test PPTX content for upload"
        files = {
            'file': ('test.pptx', test_content, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
        }
        
        response = requests.post(f"{base_url}/upload", files=files, timeout=10)
        if response.status_code == 200:
            data = response.json()
            lesson_id = data['lesson_id']
            print(f"✅ Upload успешен: lesson_id = {lesson_id}")
            
            # Проверяем созданный manifest
            manifest_response = requests.get(f"{base_url}/lessons/{lesson_id}/manifest", timeout=5)
            if manifest_response.status_code == 200:
                manifest_data = manifest_response.json()
                slides_count = len(manifest_data['slides'])
                print(f"✅ Manifest создан: {slides_count} слайдов")
                
                # Проверяем доступность статических файлов
                first_slide = manifest_data['slides'][0]
                image_url = f"{base_url}{first_slide['image']}"
                image_response = requests.head(image_url, timeout=5)
                if image_response.status_code == 200:
                    print(f"✅ Статические файлы доступны")
                else:
                    print(f"⚠️  Статические файлы недоступны: {image_response.status_code}")
            else:
                print(f"❌ Manifest не создан: {manifest_response.status_code}")
                return False
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False
    
    # 4. Тест export endpoint
    print("\n4. Тест export endpoint...")
    try:
        response = requests.post(f"{base_url}/lessons/demo-lesson/export", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Export endpoint работает")
            print(f"   - Статус: {data['status']}")
            print(f"   - URL: {data['download_url']}")
            print(f"   - Время: {data['estimated_time']}")
        else:
            print(f"❌ Export failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Export test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Все тесты пройдены успешно!")
    print("✅ Backend готов к работе")
    print("✅ API endpoints функционируют")
    print("✅ Mock-данные создаются корректно")
    print("✅ Демо режим работает")
    print("\n📝 Следующие шаги:")
    print("1. Запустите фронтенд: npm run dev")
    print("2. Откройте http://localhost:5173")
    print("3. Попробуйте загрузить файл или запустить демо")
    
    return True

if __name__ == "__main__":
    success = test_system()
    exit(0 if success else 1)