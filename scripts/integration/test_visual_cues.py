#!/usr/bin/env python3
"""
Тест для проверки генерации визуальных эффектов
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.workers.visual_cues_generator import generate_visual_cues_for_slide

def test_visual_cues_generation():
    """Тестирует генерацию визуальных cues"""
    print("🧪 Тестируем генерацию визуальных cues...")
    
    # Тестовые элементы
    test_elements = [
        {
            "id": "element_1",
            "type": "text",
            "text": "Заголовок слайда",
            "bbox": [100, 50, 800, 100],
            "confidence": 0.9
        },
        {
            "id": "element_2", 
            "type": "text",
            "text": "Основной текст слайда с важной информацией",
            "bbox": [100, 200, 600, 150],
            "confidence": 0.8
        },
        {
            "id": "element_3",
            "type": "text", 
            "text": "Дополнительная информация",
            "bbox": [100, 400, 500, 100],
            "confidence": 0.7
        }
    ]
    
    # Тестовые данные аудио
    test_audio_duration = 10.0
    
    test_tts_words = {
        "sentences": [
            {"t0": 0.0, "t1": 3.0, "text": "Заголовок слайда"},
            {"t0": 3.5, "t1": 7.0, "text": "Основной текст слайда с важной информацией"},
            {"t0": 7.5, "t1": 10.0, "text": "Дополнительная информация"}
        ]
    }
    
    # Генерируем cues
    cues = generate_visual_cues_for_slide(test_elements, test_audio_duration, test_tts_words)
    
    print(f"✅ Сгенерировано {len(cues)} визуальных cues:")
    
    for i, cue in enumerate(cues):
        print(f"  Cue {i+1}:")
        print(f"    ID: {cue.cue_id}")
        print(f"    Время: {cue.t0:.1f}s - {cue.t1:.1f}s")
        print(f"    Действие: {cue.action}")
        print(f"    Координаты: {cue.bbox}")
        print(f"    Элемент: {cue.element_id}")
        if cue.to:
            print(f"    Лазерная указка: {cue.to}")
        print()
    
    # Проверяем, что cues созданы правильно
    assert len(cues) > 0, "Должны быть созданы cues"
    
    # Проверяем типы действий
    actions = [cue.action for cue in cues]
    assert "highlight" in actions, "Должны быть highlight cues"
    assert "underline" in actions, "Должны быть underline cues"
    
    print("🎉 Тест генерации визуальных cues прошел успешно!")
    return True

if __name__ == "__main__":
    try:
        test_visual_cues_generation()
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
