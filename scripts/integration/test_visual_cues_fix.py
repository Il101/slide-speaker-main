#!/usr/bin/env python3
"""
Тестирование генератора визуальных эффектов с реальными данными из manifest
"""
import json
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "app"))

# Now import
from app.models.schemas import Cue, ActionType
from workers.visual_cues_generator import VisualCuesGenerator

def test_visual_cues():
    """Тест генератора визуальных эффектов"""
    
    # Загружаем реальный manifest
    manifest_path = Path(__file__).parent / "backend" / ".data" / "34954f21-3a4d-4a4e-b975-d8f892f8961b" / "manifest.json"
    
    if not manifest_path.exists():
        print(f"❌ Manifest не найден: {manifest_path}")
        return False
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    # Берём первый слайд для теста
    slide = manifest["slides"][0]
    elements = slide["elements"]
    duration = slide.get("duration", 10.0)
    
    print(f"📊 Тестируем слайд {slide['id']}")
    print(f"   Элементов: {len(elements)}")
    print(f"   Длительность: {duration:.2f}s")
    print(f"   Формат первого bbox: {type(elements[0]['bbox'])}, {elements[0]['bbox']}")
    
    # Генерируем визуальные эффекты
    try:
        generator = VisualCuesGenerator()
        cues = generator.generate_cues_for_slide(elements, duration, tts_words=None)
        
        print(f"\n✅ Сгенерировано {len(cues)} визуальных эффектов:")
        for i, cue in enumerate(cues, 1):
            print(f"   {i}. {cue.action} ({cue.t0:.2f}s - {cue.t1:.2f}s)")
            if cue.bbox:
                print(f"      bbox: {cue.bbox}")
            if cue.to:
                print(f"      to: {cue.to}")
        
        # Проверяем формат для JSON
        cues_data = []
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
            cues_data.append(cue_dict)
        
        print(f"\n✅ JSON сериализация успешна")
        print(f"   Первый cue: {json.dumps(cues_data[0], ensure_ascii=False, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка генерации визуальных эффектов: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_visual_cues()
    sys.exit(0 if success else 1)
