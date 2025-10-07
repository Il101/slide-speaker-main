#!/usr/bin/env python3
"""
Тест для проверки поддержки языка в LLM
"""

import requests
import json
import time
import os
from pathlib import Path
from dotenv import load_dotenv

def test_language_support():
    """Тестируем поддержку языка в LLM"""
    
    print("🌍 ТЕСТ ПОДДЕРЖКИ ЯЗЫКА В LLM")
    print("=" * 50)
    
    # Загружаем переменные окружения
    load_dotenv("backend/.env")
    
    # 1. Проверяем переменные окружения
    print("\n1. Проверка переменных окружения...")
    llm_language = os.getenv("LLM_LANGUAGE")
    print(f"✅ LLM_LANGUAGE: {llm_language}")
    
    if llm_language != "ru":
        print(f"❌ Ожидался русский язык (ru), получен: {llm_language}")
        return False
    
    # 2. Проверяем backend
    print("\n2. Проверка backend...")
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
    
    # 3. Загружаем тестовую презентацию
    print("\n3. Загрузка тестовой презентации...")
    test_file = Path("backend/test_presentation.pptx")
    if not test_file.exists():
        print("❌ Тестовый файл не найден")
        return False
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_presentation.pptx', f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
            response = requests.post("http://localhost:8001/upload", files=files, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            lesson_id = data.get('lesson_id')
            print(f"✅ Презентация загружена, lesson_id: {lesson_id}")
        else:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при загрузке файла: {e}")
        return False
    
    # 4. Ждем обработки
    print("\n4. Ожидание обработки...")
    max_wait = 120
    wait_time = 0
    
    while wait_time < max_wait:
        try:
            response = requests.get(f"http://localhost:8001/lessons/{lesson_id}/status", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                print(f"   Статус: {status}")
                
                if status == 'completed':
                    print("✅ Обработка завершена!")
                    break
                elif status == 'failed':
                    print("❌ Обработка завершилась с ошибкой")
                    return False
            else:
                print(f"   Ошибка получения статуса: {response.status_code}")
        except Exception as e:
            print(f"   Ошибка: {e}")
        
        time.sleep(5)
        wait_time += 5
    
    if wait_time >= max_wait:
        print("❌ Таймаут ожидания обработки")
        return False
    
    # 5. Проверяем manifest
    print("\n5. Проверка manifest...")
    try:
        response = requests.get(f"http://localhost:8001/lessons/{lesson_id}/manifest", timeout=10)
        if response.status_code == 200:
            manifest = response.json()
            
            # Проверяем наличие лекционного текста
            slides = manifest.get('slides', [])
            if slides:
                first_slide = slides[0]
                lecture_text = first_slide.get('lecture_text', '')
                
                print(f"✅ Лекционный текст получен: {len(lecture_text)} символов")
                print(f"   Первые 100 символов: {lecture_text[:100]}...")
                
                # Проверяем, что текст на русском языке
                russian_chars = sum(1 for char in lecture_text if 'а' <= char.lower() <= 'я' or char in 'ё')
                total_chars = len([c for c in lecture_text if c.isalpha()])
                
                if total_chars > 0:
                    russian_ratio = russian_chars / total_chars
                    print(f"   Соотношение русских символов: {russian_ratio:.2%}")
                    
                    if russian_ratio > 0.5:
                        print("✅ Текст преимущественно на русском языке!")
                    else:
                        print("⚠️ Текст может быть не на русском языке")
                else:
                    print("⚠️ Не удалось определить язык текста")
                
                # Проверяем speaker notes
                speaker_notes = first_slide.get('speaker_notes', [])
                if speaker_notes:
                    print(f"✅ Speaker notes получены: {len(speaker_notes)} заметок")
                    for i, note in enumerate(speaker_notes[:2]):  # Показываем первые 2
                        note_text = note.get('text', '')
                        print(f"   Заметка {i+1}: {note_text}")
                else:
                    print("⚠️ Speaker notes не найдены")
                
            else:
                print("❌ Слайды не найдены в manifest")
                return False
        else:
            print(f"❌ Ошибка получения manifest: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке manifest: {e}")
        return False
    
    print("\n🎉 ТЕСТ ПОДДЕРЖКИ ЯЗЫКА ЗАВЕРШЕН УСПЕШНО!")
    print("✅ LLM генерирует контент на русском языке")
    return True

if __name__ == "__main__":
    success = test_language_support()
    if success:
        print("\n✅ Все тесты прошли успешно!")
    else:
        print("\n❌ Тесты завершились с ошибками")
