# �� Gemini TTS: Полный обзор возможностей

**Дата анализа:** 12 ноября 2025  
**Источники:** Официальная документация Google Cloud + Эмпирическое тестирование

---

## 📊 Краткая таблица сравнения

| Возможность | Chirp 3 HD | Gemini TTS Flash 2.5 | Статус |
|-------------|------------|---------------------|--------|
| **Базовый синтез** | ✅ | ✅ | OK |
| **Русский язык** | ✅ | ✅ (GA) | OK |
| **SSML поддержка** | ✅ Полная | ❌ Нет | ДЕГРАДАЦИЯ |
| **Timepoints** | ✅ enable_time_pointing | ❌ Не поддерживается | **КРИТИЧНО!** |
| **Natural Language Prompts** | ❌ Нет | ✅ Да | НОВАЯ ВОЗМОЖНОСТЬ |
| **Markup Tags** | ❌ Нет | ✅ 15+ тегов | НОВАЯ ВОЗМОЖНОСТЬ |
| **Streaming** | ✅ Есть | ✅ Есть | OK |
| **Multi-speaker** | ✅ Studio voices | ✅ Multi-speaker config | OK |
| **Low latency** | ✅ | ✅ | OK |
| **Кол-во голосов (русский)** | 30 | 30 | OK |

---

## 🎤 Доступные модели

### 1. Gemini 2.5 Flash TTS
- **Model ID:** `gemini-2.5-flash-tts`
- **Описание:** Low latency, controllable, single- and multi-speaker TTS
- **Формат вывода:** 
  - Unary: LINEAR16 (default), ALAW, MULAW, MP3, OGG_OPUS, PCM
  - Streaming: PCM (default), ALAW, MULAW, OGG_OPUS
- **Endpoint:** global
- **Цена:** Cost-efficient

### 2. Gemini 2.5 Flash Lite TTS (Preview)
- **Model ID:** `gemini-2.5-flash-lite-preview-tts`
- **Описание:** Ultra-low latency для real-time приложений
- **Статус:** Preview

### 3. Gemini 2.5 Pro TTS
- **Model ID:** `gemini-2.5-pro-tts`
- **Описание:** Highest quality, expressive multi-speaker synthesis
- **Формат вывода:** LINEAR16, MP3, WAV

---

## ✨ Новые возможности (недоступные в Chirp 3 HD)

### 1. 🎭 Natural Language Prompts

Возможность управлять стилем синтеза через естественный язык:

```python
synthesis_input = texttospeech.SynthesisInput(
    text="Your text here",
    prompt="Speak like a friendly tutor explaining a complex topic to a curious student"
)
```

**Примеры промптов:**
- "Narrate in a calm, professional tone for a documentary"
- "Say this in a robotic way"
- "Speak with enthusiasm and excitement"
- "Adopt a whisper for dramatic effect"
- "React with an amused laugh"
- "Speak like a 1940s radio news announcer"

**Применение:** Контроль тона, эмоций, акцента без изменения кода

---

### 2. 🏷️ Markup Tags (15+ тегов)

Inline-контроль внутри текста без SSML:

#### Mode 1: Non-speech sounds (звуки)
- `[sigh]` - вздох
- `[laughing]` - смех
- `[uhm]` - запинка (hesitation)

**Пример:**
```python
text = "I can't believe this happened [sigh] again."
```

#### Mode 2: Style modifiers (модификаторы стиля)
- `[sarcasm]` - саркастический тон
- `[robotic]` - роботизированный голос
- `[shouting]` - повышение громкости
- `[whispering]` - шёпот
- `[extremely fast]` - очень быстрая речь

**Пример:**
```python
text = "[whispering] Don't tell anyone about this."
text = "[extremely fast] Terms and conditions apply. See website for details."
```

#### Mode 3: Pacing and pauses (паузы)
- `[short pause]` - короткая пауза (~250ms)
- `[medium pause]` - средняя пауза (~500ms)
- `[long pause]` - длинная пауза (~1000ms+)

**Пример:**
```python
text = "The answer is... [long pause] ...no."
```

#### Mode 4: Vocalized adjectives (эмоции)
- `[scared]` - испуганный тон (слово произносится!)
- `[curious]` - любопытный тон
- `[bored]` - скучающий, монотонный тон

⚠️ **Внимание:** В Mode 4 тег произносится как слово! Лучше использовать prompts.

---

### 3. 🎯 Advanced Controls

**Четыре ключевых возможности:**

1. **Natural conversation** - высококачественные голосовые взаимодействия с низкой задержкой
2. **Style control** - адаптация произношения через natural language prompts
3. **Dynamic performance** - выразительное чтение поэзии, новостей, сторителлинга
4. **Enhanced pace and pronunciation control** - точный контроль скорости и произношения

---

### 4. 🎪 Multi-speaker synthesis

Два режима:

#### A. Freeform text input (свободный текст)
```python
text = "Sam: Hi Bob!\nBob: Hi Sam!"
prompt = "Create a natural conversation between two friends"

multi_speaker_voice_config = MultiSpeakerVoiceConfig(
    speaker_voice_configs=[
        MultispeakerPrebuiltVoice(speaker_alias="Sam", speaker_id="Kore"),
        MultispeakerPrebuiltVoice(speaker_alias="Bob", speaker_id="Charon"),
    ]
)
```

#### B. Structured text input (структурированный)
```python
turns = [
    MultiSpeakerMarkup.Turn(speaker="Sam", text="Hi Bob!"),
    MultiSpeakerMarkup.Turn(speaker="Bob", text="Hi Sam!")
]
```

**Преимущество structured:** Интеллектуальная вокализация (адреса, даты читаются естественно)

---

### 5. 📡 Streaming synthesis

**Возможности:**
- Real-time generation для low-latency приложений
- Async отправка chunks
- Audio возвращается по мере готовности
- Half-Close signal для начала синтеза

**Применение:** Live чат-боты, голосовые ассистенты

---

## 🌍 Поддерживаемые языки

### GA (Generally Available) - 24 языка:
- Русский (ru-RU) ✅
- Английский (en-US, en-IN)
- Французский (fr-FR)
- Немецкий (de-DE)
- Испанский (es-ES)
- Итальянский (it-IT)
- Японский (ja-JP)
- Корейский (ko-KR)
- Арабский (ar-EG)
- Хинди (hi-IN)
- Индонезийский (id-ID)
- Польский (pl-PL)
- Португальский (pt-BR)
- Румынский (ro-RO)
- Тайский (th-TH)
- Турецкий (tr-TR)
- Украинский (uk-UA)
- Вьетнамский (vi-VN)
- И другие

### Preview - 60+ языков дополнительно
Включая китайский, греческий, иврит, и многие другие.

---

## 🎤 Голоса

**30 голосов** (те же имена, что в Chirp 3 HD):

### Female voices (11):
- Achernar, Aoede, Autonoe, Callirrhoe, Despina, Erinome, Gacrux, Kore, Laomedeia, Leda, Pulcherrima, Sulafat, Vindemiatrix, Zephyr

### Male voices (16):
- Achird, Algenib, Algieba, Alnilam, Charon, Enceladus, Fenrir, Iapetus, Orus, Puck, Rasalgethi, Sadachbia, Sadaltager, Schedar, Umbriel, Zubenelgenubi

**Отличие от Chirp 3 HD:** Голоса **язык-независимые** (любой голос может говорить на любом языке)

---

## 🚫 Что ОТСУТСТВУЕТ в Gemini TTS

### 1. ❌ SSML поддержка
- **Нет `<speak>`, `<break>`, `<emphasis>`, `<prosody>`**
- Замена: Markup tags `[pause]`, prompts для эмоций

### 2. ❌ **TIMEPOINTS (КРИТИЧНО!)**
```json
{
  "error": {
    "code": 400,
    "message": "Unknown name \"enableTimePointing\": Cannot find field"
  }
}
```

**Тестировано эмпирически:**
- Параметр `enableTimePointing` отвергается API v1
- Нет альтернативного способа получить word-level timing
- Нет поля `timepoints` в ответе

**Воздействие:**
- ❌ Невозможно синхронизировать визуальные эффекты
- ❌ Stage 5 (Visual Effects) pipeline сломается
- ❌ Потеря ключевого конкурентного преимущества

---

## 📏 Ограничения

| Параметр | Ограничение |
|----------|-------------|
| Text field | ≤ 4,000 bytes |
| Prompt field | ≤ 4,000 bytes |
| Text + Prompt | ≤ 8,000 bytes |
| Output audio duration | ~655 seconds (truncated if longer) |
| Speaker aliases | Alphanumeric только, no whitespace |
| Multi-speaker dialogue | ≤ 4,000 bytes combined |

---

## 💰 API формат

### REST API (v1):
```bash
POST https://texttospeech.googleapis.com/v1/text:synthesize
```

### Python SDK (minimum v2.29.0):
```python
from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

synthesis_input = texttospeech.SynthesisInput(
    text="Your text",
    prompt="Style instruction"
)

voice = texttospeech.VoiceSelectionParams(
    language_code="ru-RU",
    name="Charon",
    model_name="gemini-2.5-flash-tts"  # НЕ "model", а "modelName"!
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)

response = client.synthesize_speech(
    input=synthesis_input,
    voice=voice,
    audio_config=audio_config
)
```

---

## 🎯 Три столпа контроля (Best Practices)

### 1. Style Prompt
Основной драйвер эмоционального тона и стиля произношения.

**Хорошо:**
```
"You are an AI assistant speaking in a friendly and helpful tone."
"Narrate this in the calm, authoritative tone of a nature documentary narrator."
```

### 2. Text Content
Семантика слов должна быть **эмоционально согласована** с prompt'ом.

**Хорошо:**
- Prompt: "scared tone" + Text: "I think someone is in the house."

**Плохо:**
- Prompt: "scared tone" + Text: "The meeting is at 4 PM." (ambiguous results)

### 3. Markup Tags
Используются для **локальных** модификаций, а не общего тона.

**Правило:** Align all three levers - Style Prompt, Text Content, Markup Tags должны работать к одной цели.

---

## 🏆 Рекомендации по использованию

### ✅ **Gemini TTS идеален для:**
1. **Чат-боты и голосовые ассистенты** - low latency streaming
2. **Контент с эмоциями** - prompts для контроля тона
3. **Multi-speaker диалоги** - подкасты, интервью, дискуссии
4. **Динамический стиль** - когда нужно менять тон на лету
5. **Простые превью** - где timepoints не нужны

### ❌ **Gemini TTS НЕ подходит для:**
1. **Синхронизированные презентации** - нет timepoints
2. **Karaoke/субтитры в реальном времени** - нужны word timings
3. **Визуальные эффекты на timeline** - нужна точная синхронизация
4. **Legacy SSML code** - SSML не поддерживается

---

## 🎬 Итоговый вердикт

### ❌ **Миграция с Chirp 3 HD на Gemini TTS НЕ рекомендуется**

**Причина:** Отсутствие timepoints делает невозможной реализацию Stage 5 (Visual Effects).

### ✅ **Альтернативный план: Гибридный подход**

**Используйте Gemini TTS для:**
- Простых превью без визуальных эффектов
- Демо-режима
- Чат-ботов и голосовых помощников
- Генерации audio без синхронизации

**Продолжайте использовать Chirp 3 HD для:**
- Основной продукт (презентации с визуальными эффектами)
- Все случаи, где нужны timepoints
- Существующий production pipeline

---

## �� Источники

1. **Google Cloud Documentation:**
   - https://cloud.google.com/text-to-speech/docs/gemini-tts
   - https://cloud.google.com/text-to-speech/docs/voices
   - https://cloud.google.com/text-to-speech/docs/reference/rest/v1/text/synthesize

2. **Эмпирическое тестирование:**
   - `.test_results/gemini_final/` - успешные тесты prompts и markup tags
   - API error response - подтверждение отсутствия enableTimePointing

---

**Дата последнего обновления:** 12 ноября 2025  
**Проверено на:** google-cloud-texttospeech v2.29.0+
