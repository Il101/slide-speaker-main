# 🎨 Решения для визуальных эффектов с Gemini TTS

**Проблема:** Gemini TTS не предоставляет timepoints (word-level timestamps), необходимые для точной синхронизации визуальных эффектов.

**Цель:** Сохранить качественный голос Gemini TTS + синхронные визуальные эффекты.

---

## 🎯 Анализ текущей системы

### Что требуется для VFX:
```typescript
interface Effect {
  effect_id: string;
  type: 'spotlight' | 'highlight' | 'fade_in' | ...;
  t0: number;        // Start time (секунды) ⚠️ НУЖНО!
  t1: number;        // End time (секунды) ⚠️ НУЖНО!
  duration: number;  // Duration (секунды)
  target: {
    element_id?: string;
    bbox?: [x, y, w, h];
  };
}
```

**Ключевое:** Нужны `t0` и `t1` для каждого эффекта.

---

## 💡 Решение 1: Speech Recognition (STT) для обратной синхронизации

### Идея:
После генерации аудио с Gemini TTS, прогнать его через Google Speech-to-Text с `enable_word_time_offsets=True` для получения timepoints.

### Workflow:
```
1. Gemini TTS → audio.mp3 (отличный голос)
2. audio.mp3 → Google STT → word_timestamps
3. Мэппинг: script_words → word_timestamps → effects[].t0/t1
4. Render VFX синхронно
```

### Преимущества:
✅ Используем качественный голос Gemini TTS  
✅ Получаем точные timepoints из STT  
✅ Минимальные изменения в коде (Stage 5 остается как есть)  
✅ Google STT очень точный для русского языка  

### Недостатки:
⚠️ Дополнительный API call (STT после TTS)  
⚠️ Небольшая задержка (+1-2 сек на STT)  
⚠️ Дополнительные расходы (~$0.024 за минуту для STT)  

### Код:
```python
from google.cloud import speech_v1 as speech

def get_timepoints_from_audio(audio_content: bytes, language_code: str = "ru-RU"):
    """Получить word-level timepoints из аудио через STT"""
    client = speech.SpeechClient()
    
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=24000,
        language_code=language_code,
        enable_word_time_offsets=True,  # ⭐ Ключевое!
        model="latest_long"
    )
    
    response = client.recognize(config=config, audio=audio)
    
    word_timings = []
    for result in response.results:
        for word_info in result.alternatives[0].words:
            word_timings.append({
                'word': word_info.word,
                'start_time': word_info.start_time.total_seconds(),
                'end_time': word_info.end_time.total_seconds()
            })
    
    return word_timings
```

### Интеграция в pipeline:
```python
# Stage 4: TTS с Gemini
audio_content = gemini_tts_synthesize(text, prompt)

# Stage 4.5: STT для timepoints (НОВОЕ!)
word_timings = get_timepoints_from_audio(audio_content)

# Stage 5: Visual Effects (без изменений!)
effects = generate_effects_from_timings(word_timings, script)
```

---

## 💡 Решение 2: Forced Alignment с Gentle/Aeneas

### Идея:
Использовать forced alignment алгоритмы для синхронизации текста и аудио.

### Инструменты:
- **Gentle** (https://github.com/lowerquality/gentle) - Python, использует Kaldi
- **Aeneas** (https://github.com/readbeyond/aeneas) - Python, fast
- **Montreal Forced Aligner** - более точный, но сложнее

### Workflow:
```
1. Gemini TTS → audio.mp3
2. Forced Aligner(audio.mp3, script.txt) → word_timestamps
3. Effects mapping → VFX rendering
```

### Преимущества:
✅ Локальное решение (no API calls)  
✅ Бесплатно  
✅ Высокая точность для известного текста  
✅ Оффлайн работа  

### Недостатки:
⚠️ Требует установки дополнительных зависимостей  
⚠️ Нужна поддержка русского языка (не все поддерживают)  
⚠️ Медленнее чем STT API  

### Код (Aeneas):
```python
from aeneas.executetask import ExecuteTask
from aeneas.task import Task

def align_audio_text(audio_path: str, text: str):
    """Forced alignment через Aeneas"""
    config_string = "task_language=rus|is_text_type=plain|os_task_file_format=json"
    
    task = Task(config_string=config_string)
    task.audio_file_path_absolute = audio_path
    task.text_file_path_absolute = "text.txt"  # Сохранить text
    
    ExecuteTask(task).execute()
    
    # Получить JSON с timepoints
    return task.sync_map_leaves()
```

---

## 💡 Решение 3: ML-модель для предсказания timing

### Идея:
Обучить ML-модель предсказывать timepoints на основе:
- Длины слов
- Фонетики
- Длительности аудио
- Исторических данных

### Workflow:
```
1. Сбор данных: {text, audio, real_timepoints} из Chirp 3 HD
2. Обучение модели: predict(text, audio_duration) → timepoints
3. Inference: Gemini TTS audio → predicted_timepoints → VFX
```

### Преимущества:
✅ Быстрое inference  
✅ No API calls после обучения  
✅ Можно fine-tune под специфику контента  

### Недостатки:
⚠️ Требует обучающих данных  
⚠️ Сложность разработки  
⚠️ Точность может быть ниже STT  

---

## 💡 Решение 4: Hybrid - Sentence-level VFX

### Идея:
Если word-level timing недоступен, переключиться на sentence-level или segment-level эффекты.

### Подход:
```typescript
// Вместо word-level spotlight:
effects = [
  { type: 'highlight', target: word1, t0: 0.5, t1: 0.8 },  // ❌ Нет данных
  { type: 'highlight', target: word2, t0: 0.8, t1: 1.2 },  // ❌ Нет данных
]

// Используем sentence-level:
effects = [
  { type: 'fade_in', target: sentence1, t0: 0.0, t1: 0.5 },   // ✅ Можно вычислить
  { type: 'highlight', target: sentence1, t0: 0.5, t1: 3.5 }, // ✅ Segment timing
  { type: 'fade_out', target: sentence1, t0: 3.5, t1: 4.0 },  // ✅ Transition
]
```

### Timing estimation:
```python
def estimate_sentence_timing(text: str, audio_duration: float):
    """Оценить timing предложений на основе длины текста и аудио"""
    sentences = split_into_sentences(text)
    total_chars = len(text)
    
    timings = []
    current_time = 0.0
    
    for sentence in sentences:
        sentence_ratio = len(sentence) / total_chars
        sentence_duration = audio_duration * sentence_ratio
        
        timings.append({
            'sentence': sentence,
            't0': current_time,
            't1': current_time + sentence_duration,
            'duration': sentence_duration
        })
        
        current_time += sentence_duration
    
    return timings
```

### Преимущества:
✅ Простая реализация  
✅ No external dependencies  
✅ Работает сразу  

### Недостатки:
⚠️ Менее точная синхронизация  
⚠️ Не все эффекты возможны (spotlight требует word-level)  

---

## 💡 Решение 5: Markup Tags + Timing Estimation

### Идея:
Использовать Gemini TTS markup tags `[pause]` как timing markers.

### Подход:
```python
# Вставить паузы в текст как markers:
text_with_markers = """
Добро пожаловать [short pause] в нашу презентацию.
[medium pause]
Сегодня мы расскажем [short pause] о трёх ключевых моментах.
"""

# После TTS:
# 1. Detect pauses в audio (silence detection)
# 2. Map паузы → markers → segments
# 3. Segment-level VFX

audio = gemini_tts(text_with_markers)
pause_times = detect_silences(audio)  # [1.5s, 3.2s, 5.1s]
segments = map_pauses_to_segments(text_with_markers, pause_times)
effects = generate_segment_effects(segments)
```

### Преимущества:
✅ Используем native Gemini TTS features  
✅ Точные boundaries между сегментами  
✅ Креативный контроль над pacing  

### Недостатки:
⚠️ Требует изменения исходного текста  
⚠️ Только segment-level, не word-level  

---

## 📊 Сравнительная таблица решений

| Решение | Точность | Сложность | Стоимость | Скорость | Рекомендация |
|---------|----------|-----------|-----------|----------|--------------|
| **1. STT обратная синхр.** | ⭐⭐⭐⭐⭐ | ⭐⭐ | $ | ⭐⭐⭐⭐ | **🏆 ЛУЧШИЙ** |
| **2. Forced Alignment** | ⭐⭐⭐⭐ | ⭐⭐⭐ | FREE | ⭐⭐⭐ | Хороший |
| **3. ML предсказание** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | FREE* | ⭐⭐⭐⭐⭐ | Долгосрочно |
| **4. Sentence-level VFX** | ⭐⭐ | ⭐ | FREE | ⭐⭐⭐⭐⭐ | Временное |
| **5. Markup Tags** | ⭐⭐⭐ | ⭐⭐ | FREE | ⭐⭐⭐⭐ | Креативное |

---

## 🎯 Рекомендуемая стратегия

### Фаза 1: Quick Win (немедленно)
```python
# Используем Sentence-level VFX как fallback
if tts_provider == "gemini":
    word_timings = estimate_sentence_timing(text, audio_duration)
    vfx_mode = "segment"  # Вместо "word"
else:  # chirp3
    word_timings = get_chirp3_timepoints(text)
    vfx_mode = "word"
```

### Фаза 2: Production Solution (1-2 недели)
```python
# Интегрировать STT для точных timepoints
def generate_with_vfx(text: str, use_gemini: bool = False):
    if use_gemini:
        # Gemini TTS + STT alignment
        audio = gemini_tts.synthesize(text, prompt="...")
        word_timings = stt_client.get_word_timings(audio)
    else:
        # Chirp 3 HD native timepoints
        audio, word_timings = chirp3_tts.synthesize(text)
    
    effects = vfx_generator.create_effects(word_timings, script)
    return audio, effects
```

### Фаза 3: Optimization (долгосрочно)
- ML модель для предсказания timing
- Кэширование STT результатов
- Hybrid подход (разные VFX для разных режимов)

---

## 💰 Cost Analysis

### Текущая система (Chirp 3 HD):
- TTS: $16 per 1M characters
- Timepoints: included ✅

### Gemini TTS + STT:
- TTS: $3.50 per 1M characters (дешевле!)
- STT: $0.024 per minute ($1.44 per hour)

**Пример (10-минутная презентация):**
- Chirp 3 HD: ~5000 chars × $16/1M = $0.08
- Gemini TTS: ~5000 chars × $3.50/1M = $0.0175
- STT: 10 min × $0.024 = $0.24
- **Итого:** $0.2575 vs $0.08 = **+221% дороже**

**Вывод:** Gemini TTS + STT дороже, но даёт лучшее качество голоса.

---

## 🚀 Proof of Concept код

```python
# poc_gemini_with_stt_vfx.py

from google.cloud import texttospeech, speech_v1 as speech

def generate_with_gemini_and_vfx(text: str, language: str = "ru-RU"):
    """
    POC: Gemini TTS + STT для VFX
    """
    # 1. Generate audio with Gemini TTS
    tts_client = texttospeech.TextToSpeechClient()
    
    synthesis_input = texttospeech.SynthesisInput(
        text=text,
        prompt="Speak naturally and clearly"
    )
    
    voice = texttospeech.VoiceSelectionParams(
        language_code=language,
        name="Charon",
        model_name="gemini-2.5-flash-tts"
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    tts_response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    audio_content = tts_response.audio_content
    
    # 2. Get word timings via STT
    stt_client = speech.SpeechClient()
    
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=24000,
        language_code=language,
        enable_word_time_offsets=True,
        model="latest_long"
    )
    
    stt_response = stt_client.recognize(config=config, audio=audio)
    
    word_timings = []
    for result in stt_response.results:
        for word_info in result.alternatives[0].words:
            word_timings.append({
                'word': word_info.word,
                't0': word_info.start_time.total_seconds(),
                't1': word_info.end_time.total_seconds(),
                'duration': (word_info.end_time - word_info.start_time).total_seconds()
            })
    
    # 3. Generate VFX from word timings
    effects = []
    for i, timing in enumerate(word_timings):
        effects.append({
            'effect_id': f'highlight_{i}',
            'type': 'highlight',
            't0': timing['t0'],
            't1': timing['t1'],
            'duration': timing['duration'],
            'target': {'element_id': f'word_{i}'},
            'confidence': 0.95,
            'source': 'stt',
            'precision': 'word'
        })
    
    return {
        'audio': audio_content,
        'word_timings': word_timings,
        'effects': effects
    }

# Usage:
result = generate_with_gemini_and_vfx("Добро пожаловать в нашу презентацию")
print(f"Generated {len(result['effects'])} effects")
```

---

## ✅ Рекомендации

### Для production:
1. **Используйте Решение 1 (STT)** - наилучший баланс качества/сложности
2. Добавьте **кэширование** STT результатов (для повторных генераций)
3. Реализуйте **fallback** на sentence-level VFX (если STT fails)
4. **Мониторинг** расходов на STT

### Для development/testing:
1. Начните с **Решения 4** (sentence-level) как quick win
2. Соберите метрики качества VFX
3. A/B тест: Chirp 3 HD vs Gemini+STT

### Для будущего:
1. Исследуйте **Forced Alignment** (бесплатная альтернатива)
2. Соберите dataset для **ML модели** (долгосрочно)
3. Hybrid approach: **Gemini для демо, Chirp 3 для production**

---

**Вывод:** Gemini TTS + STT = ✅ Feasible! Отличный голос + синхронные VFX возможны.
