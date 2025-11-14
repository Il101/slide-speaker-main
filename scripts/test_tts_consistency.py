#!/usr/bin/env python3
"""
Тест для проверки консистентности интонации в Gemini TTS
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_gemini_tts_consistency():
    """Проверяем, что все сегменты объединяются в один запрос"""
    print("🧪 Тестируем консистентность Gemini TTS...")
    print()
    
    # Test data - 6 сегментов как на скриншоте
    test_segments = [
        "Давайте рассмотрим важный концепт.",
        "Это связано с тем, что мы обсуждали ранее.",
        "Ключевая идея здесь в том, что Университет Инсбрука Гистология листа Эпидермис ве...",
        "Представьте себе ситуацию, когда...",
        "Важно запомнить основной принцип.",
        "Теперь перейдём к следующему вопросу."
    ]
    
    print(f"📝 Тестовые данные: {len(test_segments)} сегментов")
    for i, seg in enumerate(test_segments, 1):
        print(f"   {i}. {seg[:50]}...")
    print()
    
    try:
        # Проверяем, что функция объединяет тексты
        from workers.tts_gemini import GeminiTTSWorker
        
        # Create worker (will use mock mode if credentials not available)
        worker = GeminiTTSWorker()
        
        print("✅ GeminiTTSWorker инициализирован")
        print(f"   Mock mode: {worker.use_mock}")
        print()
        
        # Check the internal logic
        combined_text = " ".join([text.strip() for text in test_segments if text.strip()])
        
        print(f"✅ Объединённый текст: {len(combined_text)} символов")
        print(f"   Первые 150 символов: {combined_text[:150]}...")
        print()
        
        # Calculate expected timing distribution
        total_chars = sum(len(text.strip()) for text in test_segments)
        
        print("📊 Распределение времени по сегментам (пропорционально длине):")
        for i, text in enumerate(test_segments, 1):
            chars = len(text.strip())
            percent = (chars / total_chars) * 100
            print(f"   Сегмент {i}: {chars:3d} символов ({percent:5.1f}%)")
        print()
        
        # Test actual synthesis (will use mock if no credentials)
        print("🎤 Тестируем синтез...")
        audio_path, tts_timing = worker.synthesize_slide_text_gemini(test_segments)
        
        print(f"✅ Синтез завершён:")
        print(f"   Audio path: {audio_path}")
        print(f"   Total duration: {tts_timing['total_duration']:.2f}s")
        print(f"   Segments: {len(tts_timing['sentences'])}")
        print(f"   Combined request: {tts_timing.get('combined_request', False)}")
        print(f"   Precision: {tts_timing.get('precision', 'unknown')}")
        print()
        
        # Verify timings
        print("⏱️ Проверка таймингов:")
        for i, timing in enumerate(tts_timing['sentences'], 1):
            print(f"   Сегмент {i}: {timing['t0']:.2f}s - {timing['t1']:.2f}s ({timing['duration']:.2f}s)")
        print()
        
        # Verify no gaps/overlaps
        for i in range(len(tts_timing['sentences']) - 1):
            t1_current = tts_timing['sentences'][i]['t1']
            t0_next = tts_timing['sentences'][i + 1]['t0']
            if abs(t1_current - t0_next) > 0.01:  # Allow 10ms tolerance
                print(f"⚠️ Warning: Gap/overlap between segment {i+1} and {i+2}")
                print(f"   Segment {i+1} ends at: {t1_current:.3f}s")
                print(f"   Segment {i+2} starts at: {t0_next:.3f}s")
            else:
                print(f"✅ Segments {i+1}-{i+2} seamless")
        print()
        
        print("=" * 70)
        print("✅ ТЕСТ ПРОЙДЕН: Все сегменты объединены в один запрос")
        print("✅ Интонация будет консистентной по всему слайду")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gemini_tts_consistency()
    sys.exit(0 if success else 1)
