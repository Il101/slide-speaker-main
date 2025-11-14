#!/usr/bin/env python3
"""
Test script for Silero TTS integration
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from workers.tts_silero import SileroTTSWorker

def test_silero_tts():
    """Test Silero TTS worker"""
    print("=" * 60)
    print("Testing Silero TTS Integration")
    print("=" * 60)
    
    # Test Russian voice
    print("\n1. Testing Russian TTS (aidar)...")
    worker_ru = SileroTTSWorker(language="ru", speaker="aidar")
    
    test_texts_ru = [
        "Привет, мир!",
        "Это тест Silero TTS.",
        "Локальный синтез речи работает отлично."
    ]
    
    try:
        audio_path, timings = worker_ru.synthesize_slide_text_google(test_texts_ru)
        print(f"✅ Generated Russian audio: {audio_path}")
        print(f"   Sentences: {len(timings['sentences'])}")
        for i, sent in enumerate(timings['sentences'], 1):
            print(f"   {i}. [{sent['t0']:.2f}s - {sent['t1']:.2f}s] {sent['text']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test English voice
    print("\n2. Testing English TTS (en_0)...")
    worker_en = SileroTTSWorker(language="en", speaker="en_0")
    
    test_texts_en = [
        "Hello, world!",
        "This is a Silero TTS test.",
        "Local speech synthesis works great."
    ]
    
    try:
        audio_path, timings = worker_en.synthesize_slide_text_google(test_texts_en)
        print(f"✅ Generated English audio: {audio_path}")
        print(f"   Sentences: {len(timings['sentences'])}")
        for i, sent in enumerate(timings['sentences'], 1):
            print(f"   {i}. [{sent['t0']:.2f}s - {sent['t1']:.2f}s] {sent['text']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test different speakers
    print("\n3. Testing different Russian speakers...")
    speakers = ['aidar', 'baya', 'kseniya', 'eugene']
    test_text = ["Тестируем разные голоса Silero TTS."]
    
    for speaker in speakers:
        try:
            worker = SileroTTSWorker(language="ru", speaker=speaker)
            audio_path, _ = worker.synthesize_slide_text_google(test_text)
            print(f"✅ Speaker '{speaker}': {audio_path}")
        except Exception as e:
            print(f"❌ Speaker '{speaker}' error: {e}")
    
    print("\n" + "=" * 60)
    print("Silero TTS Test Complete!")
    print("=" * 60)
    print("\nTo use Silero TTS in production, set in .env:")
    print("  TTS_PROVIDER=silero")
    print("  SILERO_TTS_LANGUAGE=ru")
    print("  SILERO_TTS_SPEAKER=aidar")
    print("  SILERO_TTS_SAMPLE_RATE=48000")
    print("\nAdvantages:")
    print("  ✅ Completely free")
    print("  ✅ Works offline")
    print("  ✅ No API keys required")
    print("  ✅ Fast generation")
    print("  ✅ Multiple languages and voices")

if __name__ == "__main__":
    test_silero_tts()
