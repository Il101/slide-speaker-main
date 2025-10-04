#!/usr/bin/env python3
"""
Тест разных голосов Google TTS
"""
import os
import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from workers.tts_google import GoogleTTSWorker

async def test_different_voices():
    """Тестирует разные голоса Google TTS"""
    
    print("🎵 Тестирование разных голосов Google TTS")
    print("=" * 60)
    
    # Разные голоса для тестирования
    voices_to_test = [
        {"voice": "ru-RU-Wavenet-A", "description": "Женский WaveNet A"},
        {"voice": "ru-RU-Wavenet-B", "description": "Мужской WaveNet B (текущий)"},
        {"voice": "ru-RU-Wavenet-C", "description": "Женский WaveNet C"},
        {"voice": "ru-RU-Wavenet-D", "description": "Мужской WaveNet D"},
        {"voice": "ru-RU-Standard-A", "description": "Женский Standard A"},
        {"voice": "ru-RU-Standard-B", "description": "Мужской Standard B"},
    ]
    
    test_text = "Привет! Это тест разных голосов Google TTS. Мы проверяем качество и естественность произношения русского языка."
    
    print(f"📝 Тестовый текст: {test_text}")
    print()
    
    for i, voice_info in enumerate(voices_to_test, 1):
        print(f"🎤 Тест {i}: {voice_info['description']}")
        print(f"   Голос: {voice_info['voice']}")
        
        try:
            # Создаем worker с голосом
            worker = GoogleTTSWorker(
                voice=voice_info['voice'],
                speaking_rate=1.0,  # Нормальная скорость
                pitch=0.0           # Нейтральный тон
            )
            
            # Генерируем аудио
            audio_data = await worker.synthesize_speech(test_text)
            
            # Сохраняем файл
            filename = f"voice_comparison_{i:02d}_{voice_info['voice'].replace('-', '_')}.wav"
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
    for file in sorted(Path('.').glob('voice_comparison_*.wav')):
        size_kb = file.stat().st_size / 1024
        print(f"  - {file.name} ({size_kb:.1f} KB)")
    
    print("\n💡 Рекомендации:")
    print("1. Прослушайте все файлы и сравните качество")
    print("2. WaveNet голоса обычно звучат более естественно")
    print("3. Standard голоса быстрее, но менее качественные")
    print("4. Выберите голос, который лучше всего подходит для вашего контента")

if __name__ == "__main__":
    asyncio.run(test_different_voices())
