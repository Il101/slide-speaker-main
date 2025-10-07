#!/usr/bin/env python3
"""
Тест настроек WaveNet голосов Google TTS
"""
import os
import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from workers.tts_google import GoogleTTSWorker

async def test_wavenet_voices():
    """Тестирует все доступные WaveNet голоса с разными настройками"""
    
    print("🎵 Тестирование настроек WaveNet голосов Google TTS")
    print("=" * 60)
    
    # Доступные WaveNet голоса
    wavenet_voices = [
        "ru-RU-Wavenet-A",  # Женский
        "ru-RU-Wavenet-B",  # Мужской (рекомендуемый)
        "ru-RU-Wavenet-C",  # Женский
        "ru-RU-Wavenet-D",  # Мужской
        "ru-RU-Wavenet-E",  # Женский
    ]
    
    # Разные настройки для тестирования
    voice_settings = [
        {"rate": 0.8, "pitch": -2.0, "description": "Медленно, низкий тон"},
        {"rate": 1.0, "pitch": 0.0, "description": "Нормально, нейтральный тон"},
        {"rate": 1.1, "pitch": 2.0, "description": "Быстро, высокий тон"},
        {"rate": 1.2, "pitch": 4.0, "description": "Очень быстро, очень высокий тон"},
        {"rate": 0.9, "pitch": -1.0, "description": "Немного медленно, немного ниже"},
    ]
    
    test_text = "Привет! Это тест голоса WaveNet. Мы проверяем разные настройки скорости и тона."
    
    print(f"📝 Тестовый текст: {test_text}")
    print()
    
    for voice in wavenet_voices:
        print(f"🎤 Тестируем голос: {voice}")
        print("-" * 40)
        
        for i, settings in enumerate(voice_settings, 1):
            print(f"  {i}. {settings['description']}")
            print(f"     Скорость: {settings['rate']}, Тон: {settings['pitch']}")
            
            try:
                # Создаем worker с настройками
                worker = GoogleTTSWorker(
                    voice=voice,
                    speaking_rate=settings['rate'],
                    pitch=settings['pitch']
                )
                
                # Генерируем аудио
                audio_data = await worker.synthesize_speech(test_text)
                
                # Сохраняем файл
                filename = f"wavenet_test_{voice.replace('-', '_')}_{i}.wav"
                filepath = Path(filename)
                
                with open(filepath, 'wb') as f:
                    f.write(audio_data)
                
                print(f"     ✅ Сохранено: {filename} ({len(audio_data)} байт)")
                
            except Exception as e:
                print(f"     ❌ Ошибка: {e}")
            
            print()
        
        print()
    
    print("🎉 Тестирование завершено!")
    print("\n📁 Созданные файлы:")
    
    # Показываем созданные файлы
    for file in Path('.').glob('wavenet_test_*.wav'):
        size_kb = file.stat().st_size / 1024
        print(f"  - {file.name} ({size_kb:.1f} KB)")
    
    print("\n💡 Рекомендации:")
    print("1. Прослушайте все файлы и выберите наиболее подходящий голос")
    print("2. Обратите внимание на качество произношения и естественность")
    print("3. Выберите настройки скорости и тона, которые лучше всего подходят для вашего контента")
    print("4. Обновите настройки в backend/.env")

if __name__ == "__main__":
    asyncio.run(test_wavenet_voices())
