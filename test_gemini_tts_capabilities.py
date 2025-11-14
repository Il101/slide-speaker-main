#!/usr/bin/env python3
"""
Тест возможностей Gemini TTS Flash 2.5
Проверяем:
1. Базовый синтез
2. Поддержку русского языка
3. Наличие timepoints (критично!)
4. Промпты для стилистики
5. Markup tags ([sigh], [pause], etc)
6. Сравнение с текущим Chirp 3
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

try:
    from google.cloud import texttospeech
    from google.cloud import texttospeech_v1beta1  # Для сравнения с текущей версией
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    print("❌ Google Cloud TTS не установлен!")
    print("   Установите: pip install google-cloud-texttospeech")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создать директорию для результатов
OUTPUT_DIR = Path(".test_results/gemini_tts_test")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_1_basic_synthesis():
    """Тест 1: Базовый синтез с Gemini TTS Flash"""
    print("\n" + "="*70)
    print("🧪 ТЕСТ 1: Базовый синтез с Gemini TTS Flash 2.5")
    print("="*70)
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Простой текст
        text = "Hello world! This is a test of Gemini TTS Flash."
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="Kore",  # Женский голос Gemini
            model_name="gemini-2.5-flash-tts"
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Сохранить аудио
        output_file = OUTPUT_DIR / "test1_basic_en.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        print(f"✅ Базовый синтез работает")
        print(f"   Файл: {output_file}")
        print(f"   Размер: {len(response.audio_content)} bytes")
        
        # Проверить наличие timepoints
        if hasattr(response, 'timepoints'):
            print(f"   ⚠️  Timepoints в response: {response.timepoints}")
        else:
            print(f"   ❌ Timepoints НЕТ в response (v1 API)")
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False


def test_2_russian_language():
    """Тест 2: Поддержка русского языка"""
    print("\n" + "="*70)
    print("🧪 ТЕСТ 2: Поддержка русского языка (ru-RU)")
    print("="*70)
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Русский текст
        text = "Привет мир! Это тест голосовой модели Gemini TTS Flash."
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Попробовать русский голос
        voice = texttospeech.VoiceSelectionParams(
            language_code="ru-RU",
            name="Kore",  # Gemini голоса не привязаны к локали
            model_name="gemini-2.5-flash-tts"
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        output_file = OUTPUT_DIR / "test2_russian.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        print(f"✅ Русский язык поддерживается")
        print(f"   Файл: {output_file}")
        print(f"   Размер: {len(response.audio_content)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False


def test_3_timepoints_with_marks():
    """Тест 3: КРИТИЧЕСКИЙ - Поддержка timepoints через <mark> теги"""
    print("\n" + "="*70)
    print("🧪 ТЕСТ 3: ⚠️  КРИТИЧЕСКИЙ - Timepoints через SSML <mark>")
    print("="*70)
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        # SSML с mark тегами
        ssml = """
        <speak>
            Hello <mark name="mark1"/> world.
            This <mark name="mark2"/> is <mark name="mark3"/> a test.
        </speak>
        """
        
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="Kore",
            model_name="gemini-2.5-flash-tts"
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=24000
        )
        
        # Попытка 1: v1 API (без enable_time_pointing)
        print("\n📍 Попытка 1: v1 API (стандартный)")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        output_file = OUTPUT_DIR / "test3_marks_v1.wav"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        print(f"   Аудио создано: {output_file}")
        
        # Проверить response на наличие timepoints
        has_timepoints = False
        if hasattr(response, 'timepoints'):
            if response.timepoints:
                print(f"   ✅ ЕСТЬ timepoints: {len(response.timepoints)}")
                for tp in response.timepoints:
                    print(f"      - {tp.mark_name}: {tp.time_seconds:.3f}s")
                has_timepoints = True
            else:
                print(f"   ⚠️  Атрибут timepoints есть, но пустой")
        else:
            print(f"   ❌ НЕТ атрибута timepoints в response")
        
        # Попытка 2: v1beta1 API (с enable_time_pointing)
        print("\n📍 Попытка 2: v1beta1 API (с enable_time_pointing)")
        try:
            client_beta = texttospeech_v1beta1.TextToSpeechClient()
            
            synthesis_input_beta = texttospeech_v1beta1.SynthesisInput(ssml=ssml)
            
            voice_beta = texttospeech_v1beta1.VoiceSelectionParams(
                language_code="en-US",
                name="Kore",
                model_name="gemini-2.5-flash-tts"
            )
            
            audio_config_beta = texttospeech_v1beta1.AudioConfig(
                audio_encoding=texttospeech_v1beta1.AudioEncoding.LINEAR16,
                sample_rate_hertz=24000
            )
            
            request = texttospeech_v1beta1.SynthesizeSpeechRequest(
                input=synthesis_input_beta,
                voice=voice_beta,
                audio_config=audio_config_beta,
                enable_time_pointing=[texttospeech_v1beta1.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
            )
            
            response_beta = client_beta.synthesize_speech(request=request)
            
            output_file_beta = OUTPUT_DIR / "test3_marks_v1beta1.wav"
            with open(output_file_beta, "wb") as out:
                out.write(response_beta.audio_content)
            
            print(f"   Аудио создано: {output_file_beta}")
            
            if hasattr(response_beta, 'timepoints') and response_beta.timepoints:
                print(f"   ✅ ЕСТЬ timepoints (v1beta1): {len(response_beta.timepoints)}")
                for tp in response_beta.timepoints:
                    print(f"      - {tp.mark_name}: {tp.time_seconds:.3f}s")
                has_timepoints = True
            else:
                print(f"   ❌ НЕТ timepoints даже с enable_time_pointing")
                
        except Exception as e:
            print(f"   ⚠️  v1beta1 не работает с Gemini: {e}")
        
        if not has_timepoints:
            print("\n" + "!"*70)
            print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Gemini TTS НЕ возвращает timepoints!")
            print("   Это делает миграцию НЕВОЗМОЖНОЙ без деградации продукта")
            print("!"*70)
        
        return has_timepoints
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_prompts_and_styling():
    """Тест 4: Промпты для контроля стиля"""
    print("\n" + "="*70)
    print("🧪 ТЕСТ 4: Промпты для контроля стиля")
    print("="*70)
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        text = "This is a test of emotional expression in speech synthesis."
        
        prompts = [
            ("neutral", "Say this in a neutral, professional tone"),
            ("friendly", "Speak like a friendly tutor explaining a topic to a student"),
            ("excited", "Speak with excitement and enthusiasm"),
        ]
        
        for name, prompt in prompts:
            print(f"\n📝 Тест промпта: {name}")
            
            synthesis_input = texttospeech.SynthesisInput(
                text=text,
                prompt=prompt
            )
            
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="Kore",
                model_name="gemini-2.5-flash-tts"
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            output_file = OUTPUT_DIR / f"test4_prompt_{name}.mp3"
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
            
            print(f"   ✅ Создано: {output_file}")
            print(f"   Размер: {len(response.audio_content)} bytes")
        
        print(f"\n✅ Промпты работают")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False


def test_5_markup_tags():
    """Тест 5: Markup tags ([pause], [whispering], etc)"""
    print("\n" + "="*70)
    print("🧪 ТЕСТ 5: Markup tags для пауз и эффектов")
    print("="*70)
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Текст с markup tags
        text = "Hello. [medium pause] This is a test. [whispering] Can you hear this whisper? [extremely fast] This part should be very fast."
        
        synthesis_input = texttospeech.SynthesisInput(
            text=text,
            prompt="Read this text naturally with the markup instructions"
        )
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="Kore",
            model_name="gemini-2.5-flash-tts"
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioConfig.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        output_file = OUTPUT_DIR / "test5_markup.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        print(f"✅ Markup tags работают")
        print(f"   Файл: {output_file}")
        print(f"   Размер: {len(response.audio_content)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False


def test_6_compare_with_chirp3():
    """Тест 6: Сравнение с текущим Chirp 3 HD (baseline)"""
    print("\n" + "="*70)
    print("🧪 ТЕСТ 6: Сравнение с Chirp 3 HD (текущая система)")
    print("="*70)
    
    try:
        client_beta = texttospeech_v1beta1.TextToSpeechClient()
        
        # Русский текст с mark тегами
        ssml = """
        <speak>
            Привет <mark name="m1"/> мир.
            Это <mark name="m2"/> тест <mark name="m3"/> системы.
        </speak>
        """
        
        synthesis_input = texttospeech_v1beta1.SynthesisInput(ssml=ssml)
        
        # Chirp 3 HD (текущая система)
        voice = texttospeech_v1beta1.VoiceSelectionParams(
            language_code="ru-RU",
            name="ru-RU-Chirp3-HD-Charon"  # Текущий голос
        )
        
        audio_config = texttospeech_v1beta1.AudioConfig(
            audio_encoding=texttospeech_v1beta1.AudioEncoding.LINEAR16,
            sample_rate_hertz=24000
        )
        
        request = texttospeech_v1beta1.SynthesizeSpeechRequest(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
            enable_time_pointing=[texttospeech_v1beta1.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
        )
        
        response = client_beta.synthesize_speech(request=request)
        
        output_file = OUTPUT_DIR / "test6_chirp3_baseline.wav"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        print(f"✅ Chirp 3 HD (baseline)")
        print(f"   Файл: {output_file}")
        print(f"   Размер: {len(response.audio_content)} bytes")
        
        # Проверить timepoints
        if hasattr(response, 'timepoints') and response.timepoints:
            print(f"   ✅ Timepoints: {len(response.timepoints)}")
            for tp in response.timepoints:
                print(f"      - {tp.mark_name}: {tp.time_seconds:.3f}s")
        else:
            print(f"   ❌ НЕТ timepoints (странно для Chirp 3!)")
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_summary(results):
    """Сохранить сводку результатов"""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "tests": results,
        "conclusion": {
            "can_migrate": results.get("test_3_timepoints", False),
            "reasons": []
        }
    }
    
    if not results.get("test_3_timepoints", False):
        summary["conclusion"]["reasons"].append(
            "❌ КРИТИЧНО: Gemini TTS не возвращает timepoints для синхронизации визуальных эффектов"
        )
    
    if results.get("test_1_basic", False):
        summary["conclusion"]["reasons"].append("✅ Базовый синтез работает")
    
    if results.get("test_2_russian", False):
        summary["conclusion"]["reasons"].append("✅ Русский язык поддерживается")
    
    if results.get("test_4_prompts", False):
        summary["conclusion"]["reasons"].append("✅ Промпты для стилистики работают")
    
    summary_file = OUTPUT_DIR / "test_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Сводка сохранена: {summary_file}")
    
    return summary


def main():
    """Запустить все тесты"""
    print("\n" + "="*70)
    print("🚀 ТЕСТИРОВАНИЕ GEMINI TTS FLASH 2.5")
    print("="*70)
    print(f"📁 Результаты сохраняются в: {OUTPUT_DIR}")
    
    # Проверить credentials
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("\n⚠️  ВНИМАНИЕ: GOOGLE_APPLICATION_CREDENTIALS не установлен")
        print("   Убедитесь, что credentials настроены правильно")
    
    results = {}
    
    # Запустить тесты
    results["test_1_basic"] = test_1_basic_synthesis()
    results["test_2_russian"] = test_2_russian_language()
    results["test_3_timepoints"] = test_3_timepoints_with_marks()  # КРИТИЧЕСКИЙ
    results["test_4_prompts"] = test_4_prompts_and_styling()
    results["test_5_markup"] = test_5_markup_tags()
    results["test_6_baseline"] = test_6_compare_with_chirp3()
    
    # Сводка
    print("\n" + "="*70)
    print("📊 ИТОГОВАЯ СВОДКА")
    print("="*70)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    summary = save_summary(results)
    
    # Вердикт
    print("\n" + "="*70)
    print("🏁 ФИНАЛЬНЫЙ ВЕРДИКТ")
    print("="*70)
    
    if summary["conclusion"]["can_migrate"]:
        print("✅ МОЖНО мигрировать на Gemini TTS Flash 2.5")
    else:
        print("❌ НЕ РЕКОМЕНДУЕТСЯ мигрировать на Gemini TTS Flash 2.5")
    
    print("\nПричины:")
    for reason in summary["conclusion"]["reasons"]:
        print(f"  {reason}")
    
    print("\n" + "="*70)
    
    return 0 if summary["conclusion"]["can_migrate"] else 1


if __name__ == "__main__":
    sys.exit(main())
