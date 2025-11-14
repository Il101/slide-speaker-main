#!/usr/bin/env python3
"""
Прямая проверка манифеста - БЕЗ авторизации
Читает данные напрямую из базы данных
"""

import subprocess
import json
import sys

def run_db_query(query):
    """Выполнить SQL запрос в PostgreSQL"""
    result = subprocess.run([
        "docker-compose", "exec", "-T", "postgres", 
        "psql", "-U", "postgres", "-d", "slide_speaker", "-t", "-c", query
    ], capture_output=True, text=True, cwd="/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main")
    
    if result.returncode != 0:
        print(f"❌ Ошибка SQL: {result.stderr}")
        return None
    
    return result.stdout.strip()

print("🔍 Проверка Visual Effects в базе данных\n")
print("="*60)

# Получаем список уроков
print("\n1️⃣ Список доступных уроков:")
query = """
    SELECT 
        id, 
        title, 
        status,
        created_at::date as created,
        (manifest_data::jsonb -> 'slides' -> 0 -> 'visual_effects_manifest' ->> 'version') as vfx_version
    FROM lessons 
    ORDER BY created_at DESC 
    LIMIT 10;
"""
result = run_db_query(query)
if result:
    print(result)
else:
    print("❌ Не удалось получить список уроков")
    sys.exit(1)

print("\n" + "="*60)

# Получаем ID последнего урока
query = "SELECT id FROM lessons ORDER BY created_at DESC LIMIT 1;"
lesson_id = run_db_query(query)

if not lesson_id:
    print("❌ Нет уроков в базе данных")
    sys.exit(1)

lesson_id = lesson_id.strip()
print(f"\n2️⃣ Проверяем последний урок: {lesson_id}")

# Проверяем наличие VFX
query = f"""
    SELECT 
        (manifest_data::jsonb -> 'slides' -> 0 -> 'visual_effects_manifest') IS NOT NULL as has_vfx,
        jsonb_array_length((manifest_data::jsonb -> 'slides' -> 0 -> 'visual_effects_manifest' -> 'effects')::jsonb) as effects_count,
        (manifest_data::jsonb -> 'slides' -> 0 -> 'visual_effects_manifest' ->> 'version') as version
    FROM lessons 
    WHERE id = '{lesson_id}';
"""
result = run_db_query(query)
print(f"\nСтатус VFX:")
print(result)

# Проверяем все слайды
query = f"""
    SELECT 
        jsonb_array_length(manifest_data::jsonb -> 'slides') as total_slides
    FROM lessons 
    WHERE id = '{lesson_id}';
"""
total_slides = run_db_query(query)
print(f"\nВсего слайдов: {total_slides}")

# Подсчитываем эффекты по всем слайдам
print(f"\n3️⃣ Подсчёт эффектов по всем слайдам:")
query = f"""
    WITH slide_effects AS (
        SELECT 
            idx,
            (slide->>'id') as slide_id,
            jsonb_array_length((slide->'visual_effects_manifest'->'effects')::jsonb) as effect_count
        FROM lessons,
             jsonb_array_elements(manifest_data::jsonb->'slides') WITH ORDINALITY AS t(slide, idx)
        WHERE lessons.id = '{lesson_id}'
    )
    SELECT 
        idx as "№",
        slide_id as "Slide ID",
        COALESCE(effect_count, 0) as "Эффектов"
    FROM slide_effects
    ORDER BY idx;
"""
result = run_db_query(query)
print(result)

# Итоговая статистика
query = f"""
    WITH all_effects AS (
        SELECT 
            effect->>'type' as effect_type
        FROM lessons,
             jsonb_array_elements(manifest_data::jsonb->'slides') as slide,
             jsonb_array_elements(slide->'visual_effects_manifest'->'effects') as effect
        WHERE lessons.id = '{lesson_id}'
    )
    SELECT 
        effect_type as "Тип эффекта",
        COUNT(*) as "Количество"
    FROM all_effects
    GROUP BY effect_type
    ORDER BY COUNT(*) DESC;
"""
print(f"\n4️⃣ Типы эффектов:")
result = run_db_query(query)
if result:
    print(result)
else:
    print("⚠️ Нет эффектов или ошибка запроса")

print("\n" + "="*60)
print("\n🎯 ВЫВОД:")

# Финальная проверка
query = f"""
    SELECT 
        COUNT(*) FILTER (WHERE (slide->'visual_effects_manifest'->'effects') IS NOT NULL) as slides_with_vfx,
        SUM(jsonb_array_length((slide->'visual_effects_manifest'->'effects')::jsonb)) as total_effects
    FROM lessons,
         jsonb_array_elements(manifest_data::jsonb->'slides') as slide
    WHERE lessons.id = '{lesson_id}';
"""
result = run_db_query(query)

if result:
    parts = result.strip().split('|')
    if len(parts) >= 2:
        slides_with_vfx = parts[0].strip()
        total_effects = parts[1].strip()
        
        print(f"✅ Слайдов с VFX: {slides_with_vfx}")
        print(f"✅ Всего эффектов: {total_effects}")
        
        if int(total_effects or 0) > 0:
            print("\n✅✅✅ ВИЗУАЛЬНЫЕ ЭФФЕКТЫ ЕСТЬ В БАЗЕ ДАННЫХ!")
            print("\nЕсли их не видно в браузере:")
            print("1. Убедитесь, что вы авторизованы")
            print("2. Обновите страницу (Ctrl+R)")
            print("3. Проверьте Console в DevTools (F12)")
            print("4. Убедитесь, что открываете этот урок:")
            print(f"   http://localhost:3000/player/{lesson_id}")
        else:
            print("\n❌ ЭФФЕКТЫ НЕ НАЙДЕНЫ!")
            print("Презентация обработана старой версией pipeline.")
            print("Решение: Загрузите презентацию заново!")

print("\n" + "="*60)
