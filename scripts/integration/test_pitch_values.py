#!/usr/bin/env python3
"""
Тест разных значений pitch для Google TTS
"""
import os
import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from workers.tts_google import GoogleTTSWorker

async def test_pitch_values():
    """Тестирует разные значения pitch"""
    
    print("🎵 Тестирование разных значений PITCH для Google TTS")
    print("=" * 60)
    
    # Разные значения pitch для тестирования
    pitch_values = [
        {"pitch": -2.0, "description": "Очень низкий тон"},
        {"pitch": -1.0, "description": "Низкий тон"},
        {"pitch": -0.5, "description": "Слегка низкий тон"},
        {"pitch": 0.0, "description": "Нейтральный тон (текущий)"},
        {"pitch": 0.5, "description": "Слегка высокий тон"},
        {"pitch": 1.0, "description": "Высокий тон"},
        {"pitch": 2.0, "description": "Очень высокий тон"},
    ]
    
    test_text = "Привет! Это тест разных значений pitch. Мы проверяем, как высота тона влияет на качество и естественность голоса."
    
    print(f"📝 Тестовый текст: {test_text}")
    print(f"🎤 Голос: ru-RU-Chirp3-HD-Charon")
    print()
    
    for i, pitch_info in enumerate(pitch_values, 1):
        try:
            print(f"🎵 Тест {i}: {pitch_info['description']}")
            print(f"   Pitch: {pitch_info['pitch']}")
            
            # Создаем TTS worker с текущими настройками
            tts_worker = GoogleTTSWorker()
            
            # Генерируем аудио с текущим pitch
            audio_data = await tts_worker.synthesize_text(
                text=test_text,
                voice_name="ru-RU-Chirp3-HD-Charon",
                speaking_rate=1.0,
                pitch=pitch_info['pitch']
            )
            
            # Сохраняем файл
            filename = f"pitch_test_{i:02d}_pitch_{pitch_info['pitch']:+.1f}.wav"
            with open(filename, 'wb') as f:
                f.write(audio_data)
            
            file_size = os.path.getsize(filename) / 1024
            print(f"   ✅ Сохранено: {filename} ({file_size:.1f} KB)")
            print()
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            print()
    
    print("🎉 Тестирование pitch завершено!")
    print()
    print("📁 Созданные файлы:")
    for pitch_info in pitch_values:
        filename = f"pitch_test_{pitch_values.index(pitch_info)+1:02d}_pitch_{pitch_info['pitch']:+.1f}.wav"
        if os.path.exists(filename):
            file_size = os.path.getsize(filename) / 1024
            print(f"  - {filename} ({file_size:.1f} KB)")
    
    print()
    print("💡 Рекомендации:")
    print("1. Прослушайте все файлы и сравните качество")
    print("2. Обратите внимание на естественность звучания")
    print("3. Выберите значение pitch, которое звучит наиболее профессионально")
    print("4. Обычно значения от -1.0 до +1.0 дают лучшие результаты")

if __name__ == "__main__":
    asyncio.run(test_pitch_values())
