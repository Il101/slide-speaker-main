#!/usr/bin/env python3
"""
Тест настроек голоса WaveNet-B
"""
import os
import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from workers.tts_google import GoogleTTSWorker

async def test_current_voice():
    """Тестирует текущие настройки голоса"""
    
    print("🎵 Тестирование текущих настроек голоса")
    print("=" * 50)
    
    # Текущие настройки из .env
    voice = os.getenv("GOOGLE_TTS_VOICE", "ru-RU-Wavenet-B")
    rate = float(os.getenv("GOOGLE_TTS_SPEAKING_RATE", "1.1"))
    pitch = float(os.getenv("GOOGLE_TTS_PITCH", "2.0"))
    
    print(f"🎤 Голос: {voice}")
    print(f"🎤 Скорость: {rate}")
    print(f"🎤 Тон: {pitch}")
    print()
    
    test_text = "Привет! Это тест мужского голоса WaveNet-B. Проверяем настройки скорости и тона."
    
    print(f"📝 Тестовый текст: {test_text}")
    print()
    
    try:
        # Создаем worker с текущими настройками
        worker = GoogleTTSWorker(
            voice=voice,
            speaking_rate=rate,
            pitch=pitch
        )
        
        print("🔄 Генерируем аудио...")
        
        # Генерируем аудио
        audio_data = await worker.synthesize_speech(test_text)
        
        # Сохраняем файл
        filename = f"current_voice_test.wav"
        filepath = Path(filename)
        
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        size_kb = len(audio_data) / 1024
        print(f"✅ Аудио сохранено: {filename} ({size_kb:.1f} KB)")
        
        if worker.use_mock:
            print("⚠️  ВНИМАНИЕ: Используется mock режим (Google TTS недоступен)")
            print("   Проверьте настройки Google Cloud в .env файле")
        else:
            print("✅ Google TTS работает корректно")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("💡 Если голос звучит неправильно:")
    print("1. Проверьте настройки в backend_env_enhanced_hybrid.env")
    print("2. Убедитесь, что Google Cloud TTS настроен правильно")
    print("3. Попробуйте другие настройки скорости и тона")

if __name__ == "__main__":
    asyncio.run(test_current_voice())
