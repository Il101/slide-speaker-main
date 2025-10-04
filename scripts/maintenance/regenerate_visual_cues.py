#!/usr/bin/env python3
"""
Скрипт для регенерации визуальных эффектов в существующих уроках
"""
import json
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "app"))

from app.models.schemas import Cue, ActionType
from workers.visual_cues_generator import VisualCuesGenerator

def regenerate_cues_for_lesson(lesson_id: str):
    """Регенерирует визуальные эффекты для урока"""
    
    # Путь к manifest
    manifest_path = Path(__file__).parent / "backend" / ".data" / lesson_id / "manifest.json"
    
    if not manifest_path.exists():
        print(f"❌ Manifest не найден для урока {lesson_id}")
        return False
    
    print(f"\n🔄 Обработка урока: {lesson_id}")
    
    # Загружаем manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    generator = VisualCuesGenerator()
    total_cues = 0
    
    # Обрабатываем каждый слайд
    for i, slide in enumerate(manifest["slides"], 1):
        elements = slide.get("elements", [])
        duration = slide.get("duration", 10.0)
        
        if not elements:
            print(f"   Слайд {i}: пропущен (нет элементов)")
            continue
        
        try:
            # Генерируем визуальные эффекты
            cues = generator.generate_cues_for_slide(elements, duration, tts_words=None)
            
            # Конвертируем в dict для JSON
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
            
            # Обновляем слайд
            slide["cues"] = cues_data
            total_cues += len(cues)
            
            print(f"   Слайд {i}: ✅ {len(cues)} визуальных эффектов")
            
        except Exception as e:
            print(f"   Слайд {i}: ❌ ошибка - {e}")
            slide["cues"] = []
    
    # Сохраняем обновлённый manifest
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Урок {lesson_id}: сохранено {total_cues} визуальных эффектов")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения manifest для урока {lesson_id}: {e}")
        return False

def main():
    """Главная функция"""
    
    # Получаем список всех уроков
    data_dir = Path(__file__).parent / "backend" / ".data"
    
    if not data_dir.exists():
        print("❌ Директория .data не найдена")
        return 1
    
    lesson_dirs = [d for d in data_dir.iterdir() if d.is_dir() and (d / "manifest.json").exists()]
    
    if not lesson_dirs:
        print("❌ Не найдено уроков с manifest.json")
        return 1
    
    print(f"📚 Найдено {len(lesson_dirs)} уроков")
    
    # Обрабатываем последний урок (или можно обработать все)
    if len(sys.argv) > 1:
        lesson_id = sys.argv[1]
        success = regenerate_cues_for_lesson(lesson_id)
    else:
        # Обрабатываем последний урок
        latest_lesson = max(lesson_dirs, key=lambda d: d.stat().st_mtime)
        success = regenerate_cues_for_lesson(latest_lesson.name)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
