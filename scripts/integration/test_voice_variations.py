#!/usr/bin/env python3
"""
Тест разных настроек голоса WaveNet-B
"""
import os
import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from workers.tts_google import GoogleTTSWorker

async def test_voice_variations():
    """Тестирует разные варианты настроек голоса"""
    
    print("🎵 Тестирование разных настроек голоса WaveNet-B")
    print("=" * 60)
    
    # Разные варианты настроек
    voice_variations = [
        {"rate": 0.9, "pitch": 0.0, "description": "Медленно, нейтральный тон"},
        {"rate": 1.0, "pitch": 0.0, "description": "Нормально, нейтральный тон"},
        {"rate": 1.1, "pitch": 0.0, "description": "Быстро, нейтральный тон"},
        {"rate": 1.0, "pitch": -1.0, "description": "Нормально, низкий тон"},
        {"rate": 1.0, "pitch": 1.0, "description": "Нормально, высокий тон"},
        {"rate": 1.1, "pitch": 2.0, "description": "Текущие настройки (быстро, высокий)"},
        {"rate": 0.95, "pitch": -0.5, "description": "Немного медленно, немного ниже"},
    ]
    
    test_text = "Привет! Это тест мужского голоса WaveNet-B. Проверяем разные настройки скорости и тона для выбора оптимального варианта."
    
    print(f"📝 Тестовый текст: {test_text}")
    print()
    
    for i, settings in enumerate(voice_variations, 1):
        print(f"🎤 Тест {i}: {settings['description']}")
        print(f"   Скорость: {settings['rate']}, Тон: {settings['pitch']}")
        
        try:
            # Создаем worker с настройками
            worker = GoogleTTSWorker(
                voice="ru-RU-Wavenet-B",
                speaking_rate=settings['rate'],
                pitch=settings['pitch']
            )
            
            # Генерируем аудио
            audio_data = await worker.synthesize_speech(test_text)
            
            # Сохраняем файл
            filename = f"voice_test_{i:02d}_rate_{settings['rate']}_pitch_{settings['pitch']}.wav"
            filepath = Path(filename)
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            size_kb = len(audio_data) / 1024
            print(f"   ✅ Сохранено: {filename} ({size_kb:.1f} KB)")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        print()
    
    print("🎉 Тестирование завершено!")
    print("\n📁 Созданные файлы:")
    
    # Показываем созданные файлы
    for file in sorted(Path('.').glob('voice_test_*.wav')):
        size_kb = file.stat().st_size / 1024
        print(f"  - {file.name} ({size_kb:.1f} KB)")
    
    print("\n💡 Рекомендации:")
    print("1. Прослушайте все файлы и выберите наиболее подходящий")
    print("2. Обратите внимание на естественность и понятность речи")
    print("3. Выберите настройки, которые лучше всего подходят для вашего контента")
    print("4. Обновите настройки в backend/.env")

if __name__ == "__main__":
    asyncio.run(test_voice_variations())
