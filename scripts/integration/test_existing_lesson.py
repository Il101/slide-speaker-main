#!/usr/bin/env python3
"""
Тест генерации cues для существующей лекции
"""
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.workers.visual_cues_generator import generate_visual_cues_for_slide

def test_existing_lesson():
    """Тестирует генерацию cues для существующей лекции"""
    print("🧪 Тестируем генерацию cues для существующей лекции...")
    
    # Загружаем manifest
    manifest_path = "/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/backend/.data/0d2b8717-d67d-4823-a2bf-bad411ef5bda/manifest.json"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    print(f"📄 Загружен manifest с {len(manifest['slides'])} слайдами")
    
    # Тестируем первый слайд
    slide = manifest['slides'][0]
    elements = slide.get('elements', [])
    duration = slide.get('duration', 0)
    
    print(f"📊 Слайд 1:")
    print(f"  - Элементов: {len(elements)}")
    print(f"  - Длительность: {duration:.2f}s")
    print(f"  - Текущие cues: {len(slide.get('cues', []))}")
    
    if elements:
        print(f"  - Первый элемент: {elements[0]['text'][:50]}...")
        print(f"  - Bbox первого элемента: {elements[0]['bbox']}")
    
    # Генерируем cues
    print("\n🎯 Генерируем новые cues...")
    cues = generate_visual_cues_for_slide(elements, duration)
    
    print(f"✅ Сгенерировано {len(cues)} cues:")
    
    for i, cue in enumerate(cues):
        print(f"  Cue {i+1}:")
        print(f"    Время: {cue.t0:.1f}s - {cue.t1:.1f}s")
        print(f"    Действие: {cue.action}")
        print(f"    Координаты: {cue.bbox}")
        print(f"    Элемент: {cue.element_id}")
        print()
    
    # Проверяем, что cues созданы правильно
    if len(cues) > 0:
        print("🎉 Тест прошел успешно! Cues генерируются корректно.")
        
        # Обновляем manifest с новыми cues
        print("\n💾 Обновляем manifest с новыми cues...")
        slide['cues'] = []
        for cue in cues:
            cue_dict = {
                "cue_id": cue.cue_id,
                "t0": cue.t0,
                "t1": cue.t1,
                "action": cue.action.value if hasattr(cue.action, 'value') else str(cue.action),
                "bbox": cue.bbox,
                "element_id": cue.element_id,
                "to": cue.to
            }
            slide['cues'].append(cue_dict)
        
        # Сохраняем обновленный manifest
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Manifest обновлен с {len(slide['cues'])} cues")
        return True
    else:
        print("❌ Тест не прошел: cues не сгенерированы")
        return False

if __name__ == "__main__":
    try:
        success = test_existing_lesson()
        if success:
            print("\n🎉 Все готово! Теперь можно тестировать визуальные эффекты в браузере.")
        else:
            print("\n❌ Есть проблемы с генерацией cues.")
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
