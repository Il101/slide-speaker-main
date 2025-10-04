#!/usr/bin/env python3
"""
Тестовый скрипт для проверки пайплайна Slide Speaker
"""
import requests
import time
import json
import sys
from pathlib import Path

def test_pipeline():
    """Тестирует весь пайплайн обработки файла"""
    
    # URL API
    base_url = "http://localhost:8001"
    
    # Тестовый файл
    test_file = "test.pdf"  # Используем PDF вместо PPTX
    
    if not Path(test_file).exists():
        print(f"❌ Тестовый файл {test_file} не найден!")
        print("Создайте тестовый файл test.pptx или test.pdf в текущей директории")
        return False
    
    print(f"🚀 Тестируем пайплайн с файлом: {test_file}")
    
    # 1. Загружаем файл
    print("\n📤 Шаг 1: Загрузка файла...")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
            response = requests.post(f"{base_url}/test-upload", files=files)
        
        if response.status_code != 200:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
        
        result = response.json()
        lesson_id = result['lesson_id']
        print(f"✅ Файл загружен успешно!")
        print(f"📋 Lesson ID: {lesson_id}")
        print(f"📊 Статус: {result['status']}")
        
    except Exception as e:
        print(f"❌ Ошибка при загрузке файла: {e}")
        return False
    
    # 2. Ждем обработки и проверяем статус
    print("\n⏳ Шаг 2: Ожидание обработки...")
    max_attempts = 30  # 30 попыток по 10 секунд = 5 минут максимум
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{base_url}/test-lessons/{lesson_id}/status")
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status', 'unknown')
                
                print(f"🔄 Попытка {attempt + 1}/{max_attempts}: Статус = {status}")
                
                if status == 'completed':
                    print("✅ Обработка завершена успешно!")
                    print(f"📊 Количество слайдов: {status_data.get('slides_count', 0)}")
                    
                    # Показываем информацию о манифесте
                    manifest = status_data.get('manifest', {})
                    slides = manifest.get('slides', [])
                    
                    print(f"\n📋 Детали манифеста:")
                    print(f"   - Всего слайдов: {len(slides)}")
                    
                    for i, slide in enumerate(slides[:3]):  # Показываем первые 3 слайда
                        title = slide.get('title', 'Без названия')
                        elements_count = len(slide.get('elements', []))
                        print(f"   - Слайд {i+1}: '{title}' ({elements_count} элементов)")
                    
                    if len(slides) > 3:
                        print(f"   - ... и еще {len(slides) - 3} слайдов")
                    
                    return True
                    
                elif status == 'error':
                    print(f"❌ Ошибка обработки: {status_data.get('error', 'Неизвестная ошибка')}")
                    return False
                    
                elif status == 'not_found':
                    print("⏳ Обработка еще не началась...")
                    
            else:
                print(f"⚠️ Неожиданный статус ответа: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Ошибка при проверке статуса: {e}")
        
        attempt += 1
        if attempt < max_attempts:
            print("⏳ Ждем 10 секунд...")
            time.sleep(10)
    
    print("❌ Таймаут: обработка не завершилась за 5 минут")
    return False

def check_server():
    """Проверяет доступность сервера"""
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Сервер доступен")
            return True
        else:
            print(f"❌ Сервер недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Сервер недоступен: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестирование пайплайна Slide Speaker")
    print("=" * 50)
    
    # Проверяем сервер
    if not check_server():
        print("\n❌ Сервер недоступен!")
        print("Убедитесь, что backend запущен на порту 8001:")
        print("cd backend && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload")
        sys.exit(1)
    
    # Тестируем пайплайн
    success = test_pipeline()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ТЕСТ ПРОЙДЕН! Пайплайн работает корректно!")
    else:
        print("💥 ТЕСТ НЕ ПРОЙДЕН! Есть проблемы в пайплайне.")
        sys.exit(1)
