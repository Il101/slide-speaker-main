#!/usr/bin/env python3
"""
Детальный тест Text-to-Speech API
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def test_tts_detailed():
    """Детальный тест TTS API"""
    
    print("🎤 Детальный тест Google Cloud Text-to-Speech")
    print("=" * 50)
    
    try:
        from backend.workers.tts_google import GoogleTTSWorker
        
        worker = GoogleTTSWorker()
        
        print(f"📋 Настройки TTS:")
        print(f"  Голос: {worker.voice}")
        print(f"  Скорость: {worker.speaking_rate}")
        print(f"  Высота тона: {worker.pitch}")
        print(f"  Mock режим: {worker.use_mock}")
        
        if worker.use_mock:
            print("\n⚠️  TTS работает в MOCK режиме")
            print("   Это означает, что:")
            print("   - API не доступен")
            print("   - Права доступа не настроены")
            print("   - Или API не включен")
        else:
            print("\n✅ TTS работает с реальным Google Cloud API")
        
        # Тестовый синтез
        test_texts = ["Привет! Это тест Google Cloud Text-to-Speech API."]
        
        print(f"\n🔊 Тестовый синтез:")
        print(f"  Текст: {test_texts[0]}")
        
        audio_path, tts_words = worker.synthesize_slide_text_google(test_texts)
        
        print(f"  ✅ Аудио создано: {audio_path}")
        print(f"  📊 Размер файла: {os.path.getsize(audio_path) if os.path.exists(audio_path) else 'N/A'} байт")
        print(f"  📝 Предложений: {len(tts_words['sentences'])}")
        
        # Проверяем содержимое аудио файла
        if os.path.exists(audio_path):
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            print(f"  🔍 Анализ аудио:")
            print(f"    Размер данных: {len(audio_data)} байт")
            
            # Проверяем, это реальное аудио или mock
            if len(audio_data) > 1000 and audio_data[:4] == b'RIFF':
                print(f"    ✅ Это реальный WAV файл")
            elif len(audio_data) < 1000:
                print(f"    ⚠️  Это mock аудио (очень маленький размер)")
            else:
                print(f"    ❓ Неизвестный формат аудио")
        
        # Проверяем доступность API напрямую
        print(f"\n🌐 Проверка API доступности:")
        try:
            from google.cloud import texttospeech
            client = texttospeech.TextToSpeechClient()
            
            # Пробуем получить список голосов
            voices = client.list_voices()
            print(f"  ✅ API доступен")
            print(f"  📊 Доступно голосов: {len(list(voices.voices))}")
            
        except Exception as e:
            print(f"  ❌ API недоступен: {e}")
        
        return not worker.use_mock
        
    except Exception as e:
        print(f"❌ Ошибка тестирования TTS: {e}")
        return False

if __name__ == "__main__":
    success = test_tts_detailed()
    
    if success:
        print("\n🎉 TTS работает с реальным Google Cloud API!")
    else:
        print("\n⚠️  TTS работает в fallback режиме")
        print("📝 Для включения реального API:")
        print("1. Убедитесь, что Cloud Speech Client роль добавлена")
        print("2. Проверьте, что Text-to-Speech API включен в проекте")
        print("3. Подождите несколько минут для распространения прав")
