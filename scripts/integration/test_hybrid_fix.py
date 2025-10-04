#!/usr/bin/env python3
"""
Тест для проверки работы Hybrid Pipeline после исправления переменных окружения
"""

import requests
import json
import time
import os
from pathlib import Path

def test_hybrid_pipeline():
    """Тестируем Hybrid pipeline с реальными сервисами"""
    
    print("🔧 ТЕСТ HYBRID PIPELINE ПОСЛЕ ИСПРАВЛЕНИЯ")
    print("=" * 50)
    
    # 1. Проверяем backend
    print("\n1. Проверка backend...")
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend работает")
        else:
            print(f"❌ Backend недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к backend: {e}")
        return False
    
    # 2. Проверяем переменные окружения
    print("\n2. Проверка переменных окружения...")
    from dotenv import load_dotenv
    load_dotenv("backend_env_hybrid_default.env")
    
    required_vars = [
        "GCP_PROJECT_ID",
        "OPENROUTER_API_KEY", 
        "OCR_PROVIDER",
        "LLM_PROVIDER",
        "TTS_PROVIDER"
    ]
    
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}..." if len(str(value)) > 20 else f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: НЕ НАСТРОЕН")
            all_ok = False
    
    if not all_ok:
        print("❌ Не все переменные окружения настроены")
        return False
    
    # 3. Проверяем доступность тестового файла
    print("\n3. Проверка тестового файла...")
    test_file = Path("test_presentation.pptx")
    if test_file.exists():
        print(f"✅ Тестовый файл найден: {test_file}")
    else:
        print("❌ Тестовый файл test_presentation.pptx не найден")
        return False
    
    # 4. Загружаем презентацию
    print("\n4. Загрузка презентации...")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test.pptx', f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
            response = requests.post("http://localhost:8001/upload", files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            lesson_id = data.get('lesson_id')
            print(f"✅ Презентация загружена, lesson_id: {lesson_id}")
        else:
            print(f"❌ Ошибка загрузки: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при загрузке: {e}")
        return False
    
    # 5. Ждем обработки и проверяем статус
    print("\n5. Ожидание обработки...")
    max_wait = 60  # максимум 60 секунд
    wait_time = 0
    
    while wait_time < max_wait:
        try:
            response = requests.get(f"http://localhost:8001/lessons/{lesson_id}/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"   Статус: {status.get('status', 'unknown')}")
                
                if status.get('status') == 'completed':
                    print("✅ Обработка завершена")
                    break
                elif status.get('status') == 'failed':
                    print(f"❌ Обработка завершилась с ошибкой: {status.get('error', 'unknown')}")
                    return False
            else:
                print(f"   Ошибка получения статуса: {response.status_code}")
                
        except Exception as e:
            print(f"   Ошибка проверки статуса: {e}")
        
        time.sleep(5)
        wait_time += 5
    
    if wait_time >= max_wait:
        print("❌ Таймаут ожидания обработки")
        return False
    
    # 6. Проверяем manifest
    print("\n6. Проверка manifest.json...")
    try:
        response = requests.get(f"http://localhost:8001/lessons/{lesson_id}/manifest", timeout=10)
        if response.status_code == 200:
            manifest = response.json()
            
            # Проверяем структуру
            slides = manifest.get('slides', [])
            print(f"✅ Manifest получен, слайдов: {len(slides)}")
            
            if slides:
                first_slide = slides[0]
                lecture_text = first_slide.get('lecture_text', '')
                elements = first_slide.get('elements', [])
                cues = first_slide.get('cues', [])
                
                print(f"   - Lecture text: {'✅ Есть' if lecture_text else '❌ Нет'}")
                print(f"   - Elements: {'✅ Есть' if elements else '❌ Нет'} ({len(elements)} элементов)")
                print(f"   - Cues: {'✅ Есть' if cues else '❌ Нет'} ({len(cues)} подсказок)")
                
                # Проверяем, что это не просто OCR
                if lecture_text and len(lecture_text) > 100:
                    print("✅ LLM контент сгенерирован (длинный текст)")
                else:
                    print("❌ LLM контент не сгенерирован (короткий или пустой текст)")
                    
        else:
            print(f"❌ Ошибка получения manifest: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки manifest: {e}")
        return False
    
    # 7. Проверяем аудио
    print("\n7. Проверка аудио...")
    try:
        response = requests.get(f"http://localhost:8001/lessons/{lesson_id}/audio", timeout=10)
        if response.status_code == 200:
            print("✅ Аудио файл доступен")
        else:
            print(f"❌ Аудио файл недоступен: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка проверки аудио: {e}")
    
    print("\n🎉 ТЕСТ ЗАВЕРШЕН!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    test_hybrid_pipeline()
