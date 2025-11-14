# 💰 Анализ стоимости Pipeline

**Дата:** 12 ноября 2025  
**Презентация:** Типичная (15 слайдов, 10 минут аудио)

---

## 🎯 Текущая архитектура пайплайна

### Stage 0: Presentation Context Analysis
**Сервис:** Google Gemini 1.5 Flash  
**Задача:** Анализ темы, уровня, стиля всей презентации  
**Вход:** Все слайды (15 PNG изображений)  
**Выход:** JSON с метаданными  

**API:** Google Cloud Vertex AI - Gemini API  
**Pricing:** https://cloud.google.com/vertex-ai/generative-ai/pricing

| Модель | Input | Output | Характеристики |
|--------|-------|--------|----------------|
| Gemini 1.5 Flash | $0.075 / 1M tokens | $0.30 / 1M tokens | Быстрая, multimodal |
| Gemini 1.5 Pro | $1.25 / 1M tokens | $5.00 / 1M tokens | Точная, мощная |

**Расчет для Stage 0 (Gemini 1.5 Flash):**
- Вход: 15 images (~125 tokens/image) + system prompt (~500 tokens) = **2,375 tokens**
- Выход: JSON (~200 tokens) = **200 tokens**
- **Стоимость:** $0.075/1M × 2,375 + $0.30/1M × 200 = **$0.000238**

---

### Stage 1: Ingest (PDF/PPTX → PNG)
**Сервис:** Локальный (pdf2image/python-pptx)  
**Задача:** Конвертация в PNG  
**Стоимость:** **$0** (локальная обработка)

---

### Stage 2: OCR (Google Cloud Document AI)
**Сервис:** Google Cloud Document AI  
**Задача:** Извлечение текста, bbox координат, структуры  
**Вход:** 15 PNG слайдов  
**Выход:** JSON с элементами (heading, paragraph, table)  

**API:** Document AI OCR  
**Pricing:** https://cloud.google.com/document-ai/pricing

| Тип | Цена за страницу | Характеристики |
|-----|-----------------|----------------|
| Document OCR | $1.50 / 1000 pages | Базовый OCR |
| Form Parser | $10.00 / 1000 pages | Структурированные формы |
| Custom Extractor | $75.00 / 1000 pages | Custom trained |

**Расчет для Stage 2 (Document OCR):**
- Страниц: 15
- **Стоимость:** $1.50/1000 × 15 = **$0.0225**

**Примечание:** В реальном проекте используется кэширование OCR → повторная обработка = $0

---

### Stage 3: PLAN - AI Intelligence

#### Stage 3.1: Semantic Analysis (per slide)
**Сервис:** Google Gemini 1.5 Flash (Vision)  
**Задача:** Анализ слайда → semantic_map (groups, priorities, strategies)  
**Вход:** 1 PNG image + OCR elements + context  
**Выход:** JSON semantic_map  

**Обработка:** Параллельно до 5 слайдов  

**Расчет для 1 слайда (Gemini 1.5 Flash Vision):**
- Вход: 1 image (~125 tokens) + OCR text (~300 tokens) + context (~500 tokens) = **925 tokens**
- Выход: JSON semantic_map (~400 tokens) = **400 tokens**
- **Стоимость на 1 слайд:** $0.075/1M × 925 + $0.30/1M × 400 = **$0.000189**

**Стоимость для 15 слайдов:** $0.000189 × 15 = **$0.002835**

#### Stage 3.2: Script Generation (per slide)
**Сервис:** Google Gemini 1.5 Flash (Text)  
**Задача:** Генерация talk_track из semantic_map  
**Вход:** semantic_map + elements + context  
**Выход:** talk_track (6-10 segments), speaker_notes  

**Расчет для 1 слайда (Gemini 1.5 Flash Text):**
- Вход: semantic_map (~400 tokens) + elements (~300 tokens) + context (~500 tokens) = **1,200 tokens**
- Выход: talk_track (~800 tokens) = **800 tokens**
- **Стоимость на 1 слайд:** $0.075/1M × 1,200 + $0.30/1M × 800 = **$0.000330**

**Стоимость для 15 слайдов:** $0.000330 × 15 = **$0.00495**

**Итого Stage 3:** $0.002835 + $0.00495 = **$0.007785**

---

### Stage 4: TTS (Google Cloud Text-to-Speech)

#### Текущая система: Chirp 3 HD + Timepoints

**Сервис:** Google Cloud TTS v1beta1  
**Модель:** ru-RU-Wavenet-D (Chirp 3 HD)  
**Особенности:** 
- ✅ SSML support
- ✅ **enable_time_pointing** (word-level timestamps)
- ✅ Высокое качество 24kHz
- ⚠️ НЕ поддерживает speaking_rate, pitch (ограничение Chirp 3)

**API:** Cloud Text-to-Speech v1beta1  
**Pricing:** https://cloud.google.com/text-to-speech/pricing

| Технология | Цена за 1M символов | Качество | Timepoints |
|-----------|-------------------|----------|------------|
| Standard | $4.00 | 16kHz | ❌ |
| WaveNet | $16.00 | 24kHz | ✅ |
| Neural2 | $16.00 | 24kHz | ✅ |
| Studio | $160.00 | 24kHz high-fidelity | ✅ |
| **Chirp 3 HD** | **$16.00** | 24kHz | **✅** |
| Chirp 3 Lite | $2.00 | 16kHz | ❌ |

**Расчет для Stage 4 (Chirp 3 HD):**
- Длительность: 10 минут
- Слов: ~1,200 слов (русский язык, средняя скорость 120 слов/мин)
- Символов: ~7,200 символов (6 символов на слово в среднем)
- **Стоимость:** $16.00/1M × 7,200 = **$0.1152**

**Дополнительно:** Timepoints включены в цену ✅

---

### Stage 5: Visual Effects
**Сервис:** Локальный (VisualEffectsEngineV2)  
**Задача:** Генерация visual cues из semantic_map + word timings  
**Стоимость:** **$0** (локальная обработка, использует timepoints из Stage 4)

---

### Stage 6: Validation & Timeline
**Сервис:** Локальный (ValidationEngine)  
**Задача:** Multi-layer validation (temporal, visual, semantic, cognitive, technical)  
**Стоимость:** **$0** (локальная обработка)

---

## �� Итого: Текущая стоимость пайплайна

| Stage | Сервис | Стоимость |
|-------|--------|-----------|
| 0. Context Analysis | Gemini 1.5 Flash | $0.000238 |
| 1. Ingest | Локально | $0 |
| 2. OCR | Document AI | $0.0225 |
| 3.1. Semantic Analysis | Gemini 1.5 Flash Vision | $0.002835 |
| 3.2. Script Generation | Gemini 1.5 Flash Text | $0.00495 |
| 4. TTS | **Chirp 3 HD** | **$0.1152** |
| 5. Visual Effects | Локально | $0 |
| 6. Validation | Локально | $0 |
| **ИТОГО** | | **$0.145223** |

**Стоимость 1 презентации (15 слайдов, 10 мин):** ~**$0.145** ≈ **14.5¢**

---

## 💡 Предложенная система: Gemini TTS + STT

### Stage 4 (NEW): TTS - Gemini Flash 2.5

**Сервис:** Google Cloud TTS v1  
**Модель:** gemini-2.5-flash-tts  
**Особенности:**
- ✅ Отличное качество голоса
- ✅ Natural Language Prompts
- ✅ 15+ Markup Tags
- ✅ Multi-speaker support
- ✅ Streaming
- ❌ **НЕТ timepoints**

**Pricing:** https://cloud.google.com/text-to-speech/pricing

| Модель | Цена за 1M символов | Качество | Timepoints |
|--------|-------------------|----------|------------|
| **Gemini 2.5 Flash TTS** | **$3.50** | 24kHz отличный | **❌** |
| Gemini 2.5 Pro TTS | $10.50 | 24kHz превосходный | ❌ |
| Gemini 2.5 Flash Lite | $0.00 (preview) | 24kHz | ❌ |

**Расчет для Stage 4 (Gemini Flash 2.5 TTS):**
- Символов: 7,200
- **Стоимость:** $3.50/1M × 7,200 = **$0.0252**

**💰 Экономия TTS:** $0.1152 - $0.0252 = **$0.09** (78% дешевле!)

---

### Stage 4.5 (NEW): STT для получения timepoints

**Сервис:** Google Cloud Speech-to-Text  
**Модель:** latest_long  
**Задача:** Получить word-level timepoints из аудио  
**Вход:** 10 минут аудио (MP3, 24kHz)  
**Выход:** word_timings [{word, start_time, end_time}, ...]  

**API:** Cloud Speech-to-Text v1  
**Pricing:** https://cloud.google.com/speech-to-text/pricing

| Модель | Цена за минуту | Характеристики |
|--------|---------------|----------------|
| Chirp 2 (Standard) | $0.016 / min | Базовая точность |
| Chirp 2 (Enhanced) | $0.024 / min | Высокая точность, русский ✅ |
| Chirp (Preview) | FREE | Новая версия |

**Расчет для Stage 4.5 (Chirp 2 Enhanced):**
- Минут: 10
- **Стоимость:** $0.024 × 10 = **$0.24**

**Примечание:** 
- Можно использовать Chirp 2 Standard ($0.016/min) → $0.16 для 10 минут
- Можно кэшировать результаты → повторная обработка = $0

---

## 📊 Сравнение: Текущая vs Предложенная система

### Вариант A: Chirp 3 HD (текущая система)

| Stage | Сервис | Стоимость |
|-------|--------|-----------|
| 0-3 | AI Intelligence | $0.030023 |
| 4. TTS | **Chirp 3 HD (с timepoints)** | **$0.1152** |
| 5-6 | Local Processing | $0 |
| **ИТОГО** | | **$0.145223** |

### Вариант B: Gemini TTS + STT Enhanced

| Stage | Сервис | Стоимость |
|-------|--------|-----------|
| 0-3 | AI Intelligence | $0.030023 |
| 4. TTS | **Gemini Flash 2.5 TTS** | **$0.0252** |
| 4.5. STT | **Chirp 2 Enhanced STT** | **$0.24** |
| 5-6 | Local Processing | $0 |
| **ИТОГО** | | **$0.295223** |

**Разница:** $0.295223 - $0.145223 = **+$0.15** (+103% дороже)

### Вариант C: Gemini TTS + STT Standard

| Stage | Сервис | Стоимость |
|-------|--------|-----------|
| 0-3 | AI Intelligence | $0.030023 |
| 4. TTS | **Gemini Flash 2.5 TTS** | **$0.0252** |
| 4.5. STT | **Chirp 2 Standard STT** | **$0.16** |
| 5-6 | Local Processing | $0 |
| **ИТОГО** | | **$0.215223** |

**Разница:** $0.215223 - $0.145223 = **+$0.07** (+48% дороже)

### Вариант D: Gemini TTS + Sentence-level VFX (no STT)

| Stage | Сервис | Стоимость |
|-------|--------|-----------|
| 0-3 | AI Intelligence | $0.030023 |
| 4. TTS | **Gemini Flash 2.5 TTS** | **$0.0252** |
| 5. VFX | Sentence-level (no word timings) | $0 |
| 6. Validation | Local | $0 |
| **ИТОГО** | | **$0.055223** |

**Разница:** $0.055223 - $0.145223 = **-$0.09** (-62% дешевле! ⚡)

---

## 🎯 Оптимизации стоимости

### 1. Кэширование (УЖЕ реализовано)

#### OCR Cache
- **Экономия:** $0.0225 при повторной обработке
- **Реализация:** `backend/app/services/ocr_cache.py`
- **Эффект:** При редактировании презентации OCR не пересчитывается

#### STT Cache (предлагается)
- **Экономия:** $0.24 при повторной генерации с тем же текстом
- **Реализация:** Hash(text) → word_timings
- **Эффект:** При редактировании других слайдов STT не пересчитывается

### 2. Hybrid подход

#### Chirp 3 HD для production, Gemini TTS для preview
```python
if mode == "production":
    # Chirp 3 HD: native timepoints, проверенное качество
    audio, word_timings = chirp3_tts.synthesize(text)
    cost = $0.145
elif mode == "preview" or demo:
    # Gemini TTS: лучший голос, sentence-level VFX
    audio = gemini_tts.synthesize(text)
    word_timings = estimate_sentence_timing(text, audio_duration)
    cost = $0.055  # 62% дешевле!
```

### 3. Fallback STT только когда нужен word-level precision

```python
if vfx_mode == "spotlight":
    # Spotlight требует word-level timing
    word_timings = stt_client.get_word_timings(audio)
    cost += $0.24
elif vfx_mode == "highlight":
    # Highlight работает с sentence-level
    word_timings = estimate_sentence_timing(text, duration)
    cost += $0  # бесплатно!
```

**Экономия:** $0.24 для презентаций без spotlight эффектов

---

## 📈 Масштабирование стоимости

### Сценарий: 1000 презентаций/месяц

| Вариант | Стоимость 1 | Стоимость 1000 | Экономия/месс |
|---------|------------|----------------|--------------|
| **A. Chirp 3 HD** | $0.145 | **$145** | baseline |
| **B. Gemini + STT Enhanced** | $0.295 | **$295** | -$150 |
| **C. Gemini + STT Standard** | $0.215 | **$215** | -$70 |
| **D. Gemini + Sentence VFX** | $0.055 | **$55** | **+$90** ✅ |

### Сценарий: 10,000 презентаций/месяц

| Вариант | Стоимость 10K | Экономия/месс |
|---------|--------------|---------------|
| **A. Chirp 3 HD** | **$1,450** | baseline |
| **B. Gemini + STT Enhanced** | **$2,950** | -$1,500 |
| **C. Gemini + STT Standard** | **$2,150** | -$700 |
| **D. Gemini + Sentence VFX** | **$550** | **+$900** ✅ |

**Вывод:** Вариант D (Gemini TTS + Sentence-level VFX) = **62% экономия** при масштабе!

---

## 🎭 Качественная оценка

### Voice Quality (субъективно)

| Система | Естественность | Интонация | Эмоциональность | Рейтинг |
|---------|---------------|-----------|-----------------|---------|
| Chirp 3 HD | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 8/10 |
| **Gemini Flash 2.5 TTS** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **10/10** |

### VFX Precision (измеримо)

| Система | Timing точность | Word-level | Sentence-level | Рейтинг |
|---------|----------------|------------|----------------|---------|
| Chirp 3 HD + native timepoints | ±50ms | ✅ | ✅ | 10/10 |
| Gemini + STT Enhanced | ±100ms | ✅ | ✅ | 9/10 |
| Gemini + STT Standard | ±200ms | ✅ | ✅ | 7/10 |
| **Gemini + Sentence-level** | **±500ms** | **❌** | **✅** | **6/10** |

**Trade-off:** Качество голоса ⬆️ 25%, Точность VFX ⬇️ 40%, Стоимость ⬇️ 62%

---

## ✅ Рекомендации

### Для текущего production:
1. **Оставить Chirp 3 HD** - надежно, проверено, включает timepoints
2. **Реализовать OCR cache** - уже есть ✅
3. **Стоимость:** $0.145/презентация

### Для новых проектов (premium):
1. **Gemini TTS + STT Standard** - лучший голос + word-level VFX
2. **Реализовать STT cache** - экономия на повторах
3. **Стоимость:** $0.215/презентация (+48%)
4. **Выгода:** Значительно лучшее качество голоса

### Для масштабирования (cost-optimized):
1. **Gemini TTS + Sentence-level VFX** - отличный голос + приемлемые VFX
2. **Без STT** - экономия $0.24 на каждой презентации
3. **Стоимость:** $0.055/презентация (-62%)
4. **Выгода:** При 10K презентаций = **+$900/месяц экономии**

### Hybrid Strategy (рекомендуется):
```python
# Пользователь выбирает режим:
if user.premium_mode:
    # Gemini TTS + STT → лучшее качество
    cost = $0.215
elif user.needs_word_level_vfx:
    # Chirp 3 HD → native timepoints
    cost = $0.145
else:
    # Gemini TTS + sentence-level → экономия
    cost = $0.055
```

---

## 💡 Долгосрочная стратегия

### Фаза 1: MVP (сейчас)
- ✅ Chirp 3 HD работает
- ✅ OCR cache реализован
- **Стоимость:** $0.145/презентация

### Фаза 2: Optimization (3 месяца)
- 🔄 Интегрировать Gemini TTS + STT Standard
- 🔄 STT cache
- 🔄 A/B тестирование качества голоса
- **Стоимость:** $0.215/презентация (premium tier)

### Фаза 3: Scale (6 месяцев)
- 🔄 Sentence-level VFX как default
- 🔄 Word-level VFX как premium feature
- 🔄 ML модель для предсказания timing (free)
- **Стоимость:** $0.055/презентация (base tier)

### Фаза 4: Advanced (12 месяцев)
- 🔄 Forced Alignment (Gentle/Aeneas) вместо STT
- 🔄 On-device timing generation
- 🔄 Zero STT cost
- **Стоимость:** $0.055/презентация (все тиры)

---

**Итоговый вердикт:**

| Метрика | Chirp 3 HD | Gemini + STT | Gemini + Sentence |
|---------|-----------|-------------|------------------|
| Стоимость | $0.145 | $0.215 (+48%) | $0.055 (-62%) |
| Качество голоса | 8/10 | **10/10** | **10/10** |
| VFX точность | 10/10 | 7-9/10 | 6/10 |
| **Рекомендация** | Production | Premium | Scale |

**Лучший выбор:** Hybrid strategy с тремя тирами (base/standard/premium) для разных use cases.
