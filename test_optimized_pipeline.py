#!/usr/bin/env python3
"""
Тестирование оптимизированного пайплайна
Загружает презентацию и отслеживает обработку
"""
import requests
import time
import json
import sys

API_URL = "http://localhost:8000"
PRESENTATION_FILE = "test_real.pptx"

def test_upload():
    """Загружает презентацию через API"""
    
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ ОПТИМИЗИРОВАННОГО ПАЙПЛАЙНА")
    print("=" * 60)
    
    # Проверяем, что API доступен
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"✅ API доступен: {response.status_code}")
    except Exception as e:
        print(f"❌ API недоступен: {e}")
        return None
    
    # Загружаем презентацию
    print(f"\n📤 Загружаем: {PRESENTATION_FILE}")
    
    try:
        with open(PRESENTATION_FILE, 'rb') as f:
            files = {'file': (PRESENTATION_FILE, f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
            
            response = requests.post(
                f"{API_URL}/upload",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            lesson_uuid = data.get('lesson_id') or data.get('uuid') or data.get('lesson_uuid') or data.get('id')
            print(f"✅ Презентация загружена!")
            print(f"   UUID: {lesson_uuid}")
            print(f"   Slides: {data.get('slide_count', 'N/A')}")
            return lesson_uuid
        else:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


def monitor_processing(lesson_uuid):
    """Мониторит обработку презентации"""
    
    print(f"\n⏳ Мониторинг обработки...")
    print(f"   UUID: {lesson_uuid}")
    print(f"\n{'='*60}")
    
    start_time = time.time()
    max_wait = 300  # 5 минут максимум
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > max_wait:
            print(f"\n⏱️ Превышено время ожидания ({max_wait}s)")
            break
        
        try:
            # Проверяем статус
            response = requests.get(f"{API_URL}/lessons/{lesson_uuid}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                
                print(f"\r⏳ [{elapsed:.1f}s] Статус: {status}...", end='', flush=True)
                
                if status == 'completed':
                    print(f"\n\n✅ Обработка завершена за {elapsed:.1f}s!")
                    return data
                elif status == 'failed':
                    print(f"\n\n❌ Обработка завершилась с ошибкой")
                    return data
            
        except Exception as e:
            print(f"\n⚠️ Ошибка проверки статуса: {e}")
        
        time.sleep(2)
    
    return None


def analyze_results(data):
    """Анализирует результаты обработки"""
    
    print(f"\n{'='*60}")
    print("📊 АНАЛИЗ РЕЗУЛЬТАТОВ")
    print(f"{'='*60}")
    
    if not data:
        print("❌ Нет данных для анализа")
        return
    
    # Основная информация
    print(f"\n📋 Основная информация:")
    print(f"   UUID: {data.get('uuid', 'N/A')}")
    print(f"   Статус: {data.get('status', 'N/A')}")
    print(f"   Filename: {data.get('filename', 'N/A')}")
    
    # Слайды
    slides = data.get('slides', [])
    print(f"\n📄 Слайды: {len(slides)} шт.")
    
    if slides:
        for i, slide in enumerate(slides[:3], 1):  # Первые 3 слайда
            print(f"\n   Слайд {i}:")
            print(f"      ID: {slide.get('id', 'N/A')}")
            print(f"      Duration: {slide.get('duration', 0):.1f}s")
            
            # Semantic map
            semantic_map = slide.get('semantic_map', {})
            groups = semantic_map.get('groups', [])
            print(f"      Semantic groups: {len(groups)}")
            
            # Talk track
            talk_track = slide.get('talk_track', [])
            print(f"      Talk track segments: {len(talk_track)}")
            
            if talk_track:
                total_text = " ".join([seg.get('text', '') for seg in talk_track])
                print(f"      Script length: {len(total_text)} chars")
                print(f"      Preview: {total_text[:100]}...")
            
            # Audio
            audio = slide.get('audio')
            if audio:
                print(f"      Audio: ✅ {audio}")
            else:
                print(f"      Audio: ❌ not generated")
        
        if len(slides) > 3:
            print(f"\n   ... и ещё {len(slides) - 3} слайдов")
    
    # Presentation context
    context = data.get('presentation_context', {})
    if context:
        print(f"\n🧠 Presentation Context:")
        print(f"   Theme: {context.get('theme', 'N/A')}")
        print(f"   Level: {context.get('level', 'N/A')}")
        print(f"   Style: {context.get('presentation_style', 'N/A')}")
    
    # Проверка качества
    print(f"\n✅ Проверка качества:")
    
    issues = []
    for i, slide in enumerate(slides, 1):
        # Проверяем semantic map
        if not slide.get('semantic_map', {}).get('groups'):
            issues.append(f"Слайд {i}: отсутствует semantic map")
        
        # Проверяем talk track
        if not slide.get('talk_track'):
            issues.append(f"Слайд {i}: отсутствует talk track")
        
        # Проверяем аудио
        if not slide.get('audio'):
            issues.append(f"Слайд {i}: отсутствует аудио")
        
        # Проверяем длительность
        if slide.get('duration', 0) < 5:
            issues.append(f"Слайд {i}: слишком короткая озвучка ({slide.get('duration', 0):.1f}s)")
    
    if issues:
        print(f"   ⚠️ Найдено {len(issues)} проблем:")
        for issue in issues[:5]:
            print(f"      - {issue}")
        if len(issues) > 5:
            print(f"      ... и ещё {len(issues) - 5} проблем")
    else:
        print(f"   ✅ Проблем не найдено!")
    
    return len(issues) == 0


if __name__ == "__main__":
    print("\n")
    
    # Загружаем презентацию
    lesson_uuid = test_upload()
    
    if not lesson_uuid:
        print("\n❌ Не удалось загрузить презентацию")
        sys.exit(1)
    
    # Мониторим обработку
    result = monitor_processing(lesson_uuid)
    
    # Анализируем результаты
    success = analyze_results(result)
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
    else:
        print("⚠️ ТЕСТ ЗАВЕРШЁН С ПРЕДУПРЕЖДЕНИЯМИ")
    print(f"{'='*60}\n")
    
    sys.exit(0 if success else 1)
