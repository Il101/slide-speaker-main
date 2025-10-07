#!/usr/bin/env python3
"""
Скрипт для загрузки презентации через API и получения URL для фронтенда
"""

import requests
import json
import time

def upload_presentation():
    """Загружаем презентацию через API"""
    
    print("📤 Загружаем презентацию через API...")
    
    # Загружаем файл
    with open('test_presentation.pptx', 'rb') as f:
        files = {'file': ('test_presentation.pptx', f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
        response = requests.post("http://localhost:8000/upload", files=files, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        lesson_id = data.get('lesson_id')
        print(f"✅ Презентация загружена, lesson_id: {lesson_id}")
        
        # Ждем обработки
        print("⏳ Ожидаем обработки...")
        max_wait = 120
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
                        return None
                else:
                    print(f"   Ошибка получения статуса: {response.status_code}")
                    
            except Exception as e:
                print(f"   Ошибка проверки статуса: {e}")
            
            time.sleep(5)
            wait_time += 5
        
        if wait_time >= max_wait:
            print("❌ Таймаут ожидания обработки")
            return None
        
        # Проверяем manifest
        print("📋 Проверяем manifest...")
        response = requests.get(f"http://localhost:8001/lessons/{lesson_id}/manifest", timeout=10)
        if response.status_code == 200:
            manifest = response.json()
            slides = manifest.get('slides', [])
            print(f"✅ Manifest получен, слайдов: {len(slides)}")
            
            if slides:
                first_slide = slides[0]
                lecture_text = first_slide.get('lecture_text', '')
                audio = first_slide.get('audio', '')
                
                print(f"   - Lecture text: {'✅ Есть' if lecture_text else '❌ Нет'}")
                print(f"   - Audio: {'✅ Есть' if audio else '❌ Нет'}")
                
                if lecture_text and len(lecture_text) > 100:
                    print("✅ LLM контент сгенерирован")
                else:
                    print("❌ LLM контент не сгенерирован")
        
        print(f"\n🌐 URL для фронтенда: http://localhost:5173/lesson/{lesson_id}")
        return lesson_id
        
    else:
        print(f"❌ Ошибка загрузки: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    lesson_id = upload_presentation()
    if lesson_id:
        print(f"\n🎉 Успешно! Lesson ID: {lesson_id}")
        print(f"🔗 Откройте в браузере: http://localhost:5173/lesson/{lesson_id}")
    else:
        print("\n❌ Не удалось загрузить презентацию")
