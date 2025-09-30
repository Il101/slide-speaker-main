"""
Демонстрация новой логики генерации лекций с анти-чтением

Этот файл показывает, как работает новая система:
1. Извлечение концептов вместо полного текста
2. Анти-чтение с проверкой перекрытия
3. Структурированный talk_track
4. Visual cues для подсветки
5. Генерация плана лекции для связности
"""

import asyncio
import json
from pathlib import Path

# Импорт новых модулей
from backend.app.services.sprint2.concept_extractor import (
    extract_slide_concepts, 
    check_anti_reading,
    SlideConcepts
)
from backend.app.services.sprint2.ai_generator import AIGenerator

async def demo_new_lecture_logic():
    """Демонстрация новой логики генерации лекций"""
    
    print("🎯 Демонстрация новой логики генерации лекций")
    print("=" * 50)
    
    # 1. Пример извлечения концептов
    print("\n1. Извлечение концептов из слайда:")
    print("-" * 30)
    
    # Моковые элементы слайда
    mock_elements = [
        {
            "id": "title",
            "type": "text",
            "text": "Histologie des Blattes",
            "bbox": [100, 100, 800, 100],
            "confidence": 0.95
        },
        {
            "id": "bullet1",
            "type": "text", 
            "text": "Épiderme - couche protectrice externe",
            "bbox": [150, 250, 600, 50],
            "confidence": 0.9
        },
        {
            "id": "bullet2",
            "type": "text",
            "text": "Mésophylle - tissu photosynthétique",
            "bbox": [150, 320, 600, 50],
            "confidence": 0.9
        },
        {
            "id": "bullet3",
            "type": "text",
            "text": "Stomates - régulation gazeuse",
            "bbox": [150, 390, 600, 50],
            "confidence": 0.9
        }
    ]
    
    # Извлекаем концепты
    concepts = extract_slide_concepts(mock_elements)
    
    print(f"📝 Заголовок: {concepts.title}")
    print(f"🎯 Ключевые тезисы: {len(concepts.key_theses)}")
    for i, thesis in enumerate(concepts.key_theses, 1):
        print(f"   {i}. {thesis}")
    print(f"🔬 Термины для определения: {concepts.terms_to_define}")
    
    # 2. Проверка анти-чтения
    print("\n2. Проверка анти-чтения:")
    print("-" * 30)
    
    # Пример текста слайда
    slide_text = "Histologie des Blattes. Épiderme - couche protectrice externe. Mésophylle - tissu photosynthétique. Stomates - régulation gazeuse."
    
    # Пример сгенерированного текста (читает слайд)
    reading_text = "Histologie des Blattes. Épiderme - couche protectrice externe. Mésophylle - tissu photosynthétique. Stomates - régulation gazeuse."
    
    # Пример объясняющего текста
    explaining_text = "У листа две основные ткани: верхняя защитная плёнка и слой клеток, где идёт фотосинтез. На схеме справа — столбчатые клетки ловят свет, губчатые — пропускают газ. Запомните: устьица снизу — так растение экономит воду."
    
    should_regenerate_reading, overlap_reading = check_anti_reading(reading_text, slide_text)
    should_regenerate_explaining, overlap_explaining = check_anti_reading(explaining_text, slide_text)
    
    print(f"📖 Текст чтения слайда:")
    print(f"   Перекрытие: {overlap_reading:.3f} (порог: 0.35)")
    print(f"   Нужна регенерация: {'ДА' if should_regenerate_reading else 'НЕТ'}")
    
    print(f"💡 Объясняющий текст:")
    print(f"   Перекрытие: {overlap_explaining:.3f} (порог: 0.35)")
    print(f"   Нужна регенерация: {'ДА' if should_regenerate_explaining else 'НЕТ'}")
    
    # 3. Структурированный talk_track
    print("\n3. Структурированный talk_track:")
    print("-" * 30)
    
    talk_track_example = [
        {"kind": "hook", "text": "У листа две основные ткани: верхняя защитная плёнка и слой клеток, где идёт фотосинтез."},
        {"kind": "core", "text": "На схеме справа — столбчатые клетки ловят свет, губчатые — пропускают газ."},
        {"kind": "example", "text": "Представьте лист как многоэтажный дом: крыша защищает от дождя, а внутри идёт работа."},
        {"kind": "contrast", "text": "Не путайте с корнем — там нет фотосинтеза."},
        {"kind": "takeaway", "text": "Запомните: устьица снизу — так растение экономит воду."},
        {"kind": "question", "text": "Вопрос: почему у пустынных видов устьица открываются ночью?"}
    ]
    
    for segment in talk_track_example:
        print(f"🎭 {segment['kind'].upper()}: {segment['text']}")
    
    # 4. Visual cues
    print("\n4. Visual cues для подсветки:")
    print("-" * 30)
    
    visual_cues_example = [
        {"at": "hook", "targetId": "title"},
        {"at": "core", "targetId": "bullet1"},
        {"at": "example", "targetId": "bullet2"},
        {"at": "contrast", "targetId": "bullet3"},
        {"at": "takeaway", "targetId": "title"}
    ]
    
    for cue in visual_cues_example:
        print(f"🎯 {cue['at']} → подсветка элемента {cue['targetId']}")
    
    # 5. План лекции
    print("\n5. План лекции для связности:")
    print("-" * 30)
    
    lecture_outline_example = {
        "outline": [
            {"idx": 1, "goal": "Ввести понятие гистологии растений"},
            {"idx": 2, "goal": "Объяснить структуру листа"},
            {"idx": 3, "goal": "Показать функции каждой ткани"},
            {"idx": 4, "goal": "Связать с экологией растений"}
        ],
        "narrative_rules": [
            "keep throughline структуры и функций",
            "avoid duplication между слайдами",
            "focus on практическое понимание"
        ]
    }
    
    print("📋 Цели слайдов:")
    for goal in lecture_outline_example["outline"]:
        print(f"   {goal['idx']}. {goal['goal']}")
    
    print("\n📏 Правила повествования:")
    for rule in lecture_outline_example["narrative_rules"]:
        print(f"   • {rule}")
    
    # 6. Пример использования AI Generator
    print("\n6. Использование AI Generator:")
    print("-" * 30)
    
    ai_generator = AIGenerator()
    
    # Генерируем план лекции
    slide_concepts_list = [concepts]
    outline = await ai_generator.generate_lecture_outline("Гистология растений", slide_concepts_list)
    
    print(f"✅ Сгенерирован план лекции с {len(outline['outline'])} целями")
    
    # Генерируем speaker notes
    speaker_notes_result = await ai_generator.generate_speaker_notes(
        slide_content=mock_elements,
        course_title="Ботаника",
        lecture_title="Гистология растений",
        slide_index=0,
        total_slides=4,
        prev_summary="Предыдущий слайд показал общую структуру растения",
        audience_level="undergrad",
        style_preset="explanatory"
    )
    
    print(f"✅ Сгенерированы speaker notes с {len(speaker_notes_result['talk_track'])} сегментами")
    print(f"🎯 Visual cues: {len(speaker_notes_result['visual_cues'])}")
    print(f"📚 Термины для определения: {len(speaker_notes_result['terms_to_define'])}")
    
    print("\n🎉 Демонстрация завершена!")
    print("=" * 50)
    
    return {
        "concepts": concepts,
        "talk_track": talk_track_example,
        "visual_cues": visual_cues_example,
        "lecture_outline": lecture_outline_example,
        "speaker_notes_result": speaker_notes_result
    }

if __name__ == "__main__":
    # Запуск демонстрации
    result = asyncio.run(demo_new_lecture_logic())
    
    # Сохранение результатов в файл
    output_file = Path("demo_new_lecture_logic.json")
    with open(output_file, "w", encoding="utf-8") as f:
        # Конвертируем SlideConcepts в dict для JSON
        result["concepts"] = {
            "title": result["concepts"].title,
            "key_theses": result["concepts"].key_theses,
            "visual_insight": result["concepts"].visual_insight,
            "terms_to_define": result["concepts"].terms_to_define
        }
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Результаты сохранены в {output_file}")