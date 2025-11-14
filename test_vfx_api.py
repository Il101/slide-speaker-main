#!/usr/bin/env python3
"""
Тест для проверки API endpoint /lessons/{id}/manifest
Проверяет наличие visual_effects_manifest в ответе
"""

import requests
import json
import sys

LESSON_ID = "db0ecfc2-1d92-4132-97b5-c22d9c6ebdef"
API_URL = f"http://localhost:8000/lessons/{LESSON_ID}/manifest"

print(f"🔍 Тестирование API endpoint: {API_URL}\n")

# Попытка 1: Без авторизации
print("1️⃣ Попытка без авторизации...")
response = requests.get(API_URL)
print(f"   Status: {response.status_code}")
if response.status_code == 401:
    print("   ❌ Требуется авторизация (ожидаемо)")
elif response.status_code == 200:
    data = response.json()
    if 'slides' in data and len(data['slides']) > 0:
        first_slide = data['slides'][0]
        has_vfx = 'visual_effects_manifest' in first_slide
        print(f"   ✅ Манифест получен")
        print(f"   Visual Effects: {'✅ Есть' if has_vfx else '❌ Нет'}")
        if has_vfx:
            vfx = first_slide['visual_effects_manifest']
            if vfx:
                print(f"   Эффектов: {len(vfx.get('effects', []))}")
                print(f"   Version: {vfx.get('version', 'N/A')}")
            else:
                print(f"   ⚠️ visual_effects_manifest = null")
else:
    print(f"   ❌ Ошибка: {response.text[:200]}")

print("\n" + "="*60)
print("\n💡 ДИАГНОСТИКА:")

# Проверка в базе данных
print("\n2️⃣ Проверка в базе данных...")
import subprocess

result = subprocess.run([
    "docker-compose", "exec", "-T", "postgres", 
    "psql", "-U", "postgres", "-d", "slide_speaker", "-t", "-c",
    f"SELECT jsonb_pretty(manifest_data::jsonb -> 'slides' -> 0 -> 'visual_effects_manifest') FROM lessons WHERE id = '{LESSON_ID}';"
], capture_output=True, text=True, cwd="/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main")

if result.returncode == 0:
    output = result.stdout.strip()
    if output and output != 'null' and len(output) > 10:
        print("   ✅ В БД есть visual_effects_manifest")
        # Парсим JSON
        try:
            vfx_data = json.loads(output)
            print(f"   ID: {vfx_data.get('id', 'N/A')}")
            print(f"   Version: {vfx_data.get('version', 'N/A')}")
            print(f"   Эффектов: {len(vfx_data.get('effects', []))}")
            print(f"   Timeline events: {len(vfx_data.get('timeline', {}).get('events', []))}")
        except:
            print(f"   Размер данных: {len(output)} символов")
    else:
        print("   ❌ В БД НЕТ visual_effects_manifest")
else:
    print(f"   ❌ Ошибка проверки БД: {result.stderr}")

print("\n" + "="*60)
print("\n🎯 ВЫВОД:")
print("Если в БД есть данные, но API не возвращает - проверьте:")
print("1. Backend перезапущен после изменений?")
print("2. Авторизован ли пользователь в браузере?")
print("3. Правильный ли lesson_id используется?")
print("\n📋 Для проверки в браузере откройте DevTools (F12) -> Console")
print("   и посмотрите логи от [SlideViewer] и [VisualEffectsEngine]")
