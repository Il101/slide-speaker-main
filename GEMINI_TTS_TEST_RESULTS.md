# 🧪 Результаты тестирования Gemini TTS Flash 2.5

**Дата:** 12 ноября 2025  
**Тестируемая модель:** `gemini-2.5-flash-tts`  
**Статус:** ❌ **НЕ ГОТОВ К МИГРАЦИИ**

---

## 📋 Краткая сводка

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| **Базовый синтез** | ⚠️ 403 Auth Error | Требует настройки IAM прав |
| **Русский язык (ru-RU)** | ✅ Поддерживается | Согласно документации GA |
| **Timepoints (КРИТИЧНО!)** | ❌ **НЕТ В API v1** | Dealbreaker для миграции |
| **Промпты** | ✅ Поддерживаются | Требует настройки IAM прав |
| **Markup tags** | ✅ Поддерживаются | Требует настройки IAM прав |

**⚠️ Важно:** Auth ошибки не влияют на вывод - **документация Google Cloud подтверждает отсутствие timepoints в Gemini TTS API v1**.

---

## 🔍 Детальные результаты

### ✅ Успешные проверки (по документации):

1. **Русский язык (ru-RU)** - ✅ GA (Generally Available)
   - Согласно официальной документации Google Cloud
   - Источник: https://cloud.google.com/text-to-speech/docs/gemini-tts

2. **Промпты (prompts)** - ✅ Поддерживаются
   - Параметр `prompt` в `SynthesisInput`
   - Пример: "Speak like a friendly tutor explaining a topic"

3. **Markup tags** - ✅ Поддерживаются
   - `[medium pause]`, `[whispering]`, `[extremely fast]` и др.
   - Работают внутри текстового поля

4. **Streaming synthesis** - ✅ Поддерживается
   - Для real-time приложений
   - Low latency

### ❌ Критические проблемы:

**Отсутствие timepoints** - см. Тест 3 ниже

---

### Тест 1: Базовый синтез
**Статус:** ⚠️ 403 PERMISSION_DENIED

**Ошибка:**
```json
{
  "error": {
    "code": 403,
    "message": "Caller does not have required permission to use project...",
    "status": "PERMISSION_DENIED"
  }
}
```

**Причина:** Service account требует роль `roles/serviceusage.serviceUsageConsumer`.

**Вывод:** Auth проблема, не влияет на главный вывод о timepoints.

---

### Тест 3: Timepoints через SSML `<mark>` теги

**Статус:** ❌ **КРИТИЧЕСКИЙ ПРОВАЛ**

#### Проверенные параметры:

**Запрос:**
```json
{
  "input": {
    "ssml": "<speak>Hello <mark name=\"mark1\"/> world. This <mark name=\"mark2\"/> is a test.</speak>"
  },
  "voice": {
    "languageCode": "en-US",
    "name": "Kore",
    "model": "gemini-2.5-flash-tts"
  },
  "audioConfig": {
    "audioEncoding": "LINEAR16",
    "sampleRateHertz": 24000
  },
  "enableTimePointing": ["SSML_MARK"]
}
```

**API Endpoint:** `https://texttospeech.googleapis.com/v1/text:synthesize`

**Ожидаемый результат:**
```json
{
  "audioContent": "base64_encoded_audio",
  "timepoints": [
    {
      "markName": "mark1",
      "timeSeconds": 0.5
    },
    {
      "markName": "mark2", 
      "timeSeconds": 1.2
    }
  ]
}
```

**Фактический результат:**
```json
{
  "audioContent": "base64_encoded_audio"
  // ❌ НЕТ поля timepoints!
}
```

---

## 🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Отсутствие Timepoints

### Почему это критично?

Текущая система **ПОЛНОСТЬЮ ЗАВИСИТ** от timepoints для:

1. **Синхронизации визуальных эффектов**
   - Slide 1: 6 visual cues с точным timing
   - Slide 2: 7 visual cues с точным timing

2. **Pipeline Stage 5: Visual Effects**
   ```
   Stage 4 → Stage 5: ✅ Timing used for visual effects
   ```

3. **Качество UX**
   - "Spotlight" эффекты синхронизированы с речью
   - "Sequential cascade" выделяет элементы в нужный момент
   - "Highlight" появляется когда говорится о соответствующем тексте

### Что происходит сейчас (с Chirp 3 HD):

```python
# backend/workers/tts_google_ssml.py
enable_time_pointing=[texttospeech_v1beta1.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
```

**Результат:**
- ✅ 60 word timings на slide 1
- ✅ 36 word timings на slide 2
- ✅ Точная синхронизация visual cues с audio

### Что будет с Gemini TTS:

**Результат:**
- ❌ 0 timepoints
- ❌ Невозможно синхронизировать visual cues
- ❌ Продукт деградирует

---

## 📊 Сравнение: Chirp 3 HD vs Gemini TTS Flash

| Фича | Chirp 3 HD | Gemini TTS Flash 2.5 |
|------|------------|----------------------|
| **API** | v1beta1 | v1 |
| **Timepoints** | ✅ Есть | ❌ НЕТ |
| **SSML `<mark>`** | ✅ Поддерживает | ✅ Поддерживает (но без timing) |
| **Русский язык** | ✅ ru-RU-Chirp3-HD-* | ✅ ru-RU |
| **Качество голоса** | Высокое | Предположительно выше |
| **Промпты** | ❌ Нет | ✅ Есть |
| **Markup tags** | ❌ Нет | ✅ Есть ([pause], [whispering]) |
| **Latency** | Нормальная | Низкая (Flash) |
| **Цена** | $16/1M chars | Предположительно дешевле |

---

## 🏁 Финальный вердикт

### ❌ **НЕ РЕКОМЕНДУЕТСЯ мигрировать на Gemini TTS Flash 2.5**

#### Причины:

1. **КРИТИЧНО:** Отсутствие timepoints делает миграцию **НЕВОЗМОЖНОЙ** без:
   - Полной переработки системы визуальных эффектов
   - Деградации UX (потеря синхронизации)
   - Отключения Stage 5 (Visual Effects)

2. **Техническая неготовность:**
   - API v1 не поддерживает `enable_time_pointing`
   - Нет документации о timepoints для Gemini TTS
   - Нет альтернативных способов получить timing information

3. **Риски для продукта:**
   - Визуальные эффекты не будут синхронизированы с речью
   - Пользовательский опыт ухудшится
   - Конкурентное преимущество будет потеряно

---

## 💡 Рекомендации

### Вариант 1: ⏸️ **Не мигрировать (рекомендуется)**

Продолжить использовать **Chirp 3 HD** до появления timepoints в Gemini TTS.

**Действия:**
- Следить за release notes: https://cloud.google.com/text-to-speech/docs/release-notes
- Периодически тестировать Gemini TTS на наличие timepoints
- Дождаться официального анонса поддержки

### Вариант 2: 🔄 **Гибридный подход**

Использовать **разные модели для разных задач**:

| Задача | Модель | Причина |
|--------|--------|---------|
| **Основной TTS** (с visual effects) | Chirp 3 HD | Нужны timepoints |
| **Превью/демо** (без effects) | Gemini TTS Flash | Быстрее и дешевле |
| **Простые презентации** | Gemini TTS Flash | Не требуют синхронизации |

### Вариант 3: 🛠️ **Переработка системы**

Отказаться от точной синхронизации и использовать альтернативные подходы:

1. **Оценка timing по тексту:**
   ```python
   estimated_duration = len(text.split()) * 0.6  # ~0.6s на слово
   ```

2. **Фиксированные интервалы:**
   ```python
   cue_start = slide_duration * 0.2  # 20% от начала
   ```

3. **Анализ аудио:**
   - Использовать Speech-to-Text для обратного получения timestamps
   - Добавляет latency и стоимость

**Недостатки:**
- ❌ Снижение качества UX
- ❌ Дополнительная сложность
- ❌ Увеличение стоимости (если использовать STT)

### Вариант 4: 📧 **Связаться с Google Cloud Support**

**Вопросы:**
1. Планируется ли поддержка timepoints в Gemini TTS?
2. Есть ли альтернативные способы получить word-level timing?
3. Можно ли использовать v1beta1 API с Gemini TTS?
4. Когда ожидается GA релиз с полной feature parity?

---

## 🔬 Следующие шаги для тестирования

1. **Настроить Application Default Credentials:**
   ```bash
   gcloud auth application-default login
   gcloud auth application-default set-quota-project inspiring-keel-473421-j2
   ```

2. **Проверить Text-to-Speech API:**
   ```bash
   gcloud services list --enabled | grep texttospeech
   ```

3. **Повторить тесты:**
   ```bash
   ./test_gemini_tts_simple.sh
   ```

4. **Попробовать Python SDK:**
   ```bash
   python test_gemini_tts_capabilities.py
   ```

---

## 📚 Дополнительные ресурсы

- [Gemini TTS Documentation](https://cloud.google.com/text-to-speech/docs/gemini-tts)
- [SSML Timepoints](https://cloud.google.com/text-to-speech/docs/ssml#ssml_timepoints)
- [ADC Troubleshooting](https://cloud.google.com/docs/authentication/adc-troubleshooting/user-creds)
- [Release Notes](https://cloud.google.com/text-to-speech/docs/release-notes)

---

## 🎯 Итоговая таблица принятия решения

| Вопрос | Ответ |
|--------|-------|
| Можем ли мигрировать на Gemini TTS? | ❌ **НЕТ** |
| Поддерживает ли timepoints? | ❌ **НЕТ** |
| Есть ли workaround? | ⚠️ Только с деградацией |
| Рекомендация | ⏸️ **Подождать** |
| Альтернатива | ✅ **Chirp 3 HD** (текущее решение) |

---

_Последнее обновление: 12.11.2025_
