# 🌍 Translation Flow для Visual Effects

## Проблема которую решает переводчик

**Ситуация:**
- Презентация на **немецком** языке: `"Epidermis der Blattoberseite"`
- TTS озвучка на **русском**: `"эпидермис верхней стороны листа"`
- Визуальные эффекты должны **подсветить немецкий текст** В МОМЕНТ произношения русского перевода

**Без переводчика:** Visual effects не могут сопоставить "эпидермис" (в аудио) с "Epidermis" (на слайде)

## ✅ Решение: Translation Service + Dual Text Storage

### Stage 2.5: Language Detection & Translation

```python
# 1. Определяем язык презентации
presentation_lang = language_detector.detect_presentation_language(slides)
# → "de" (немецкий)

# 2. Целевой язык TTS
target_tts_lang = os.getenv('SILERO_TTS_LANGUAGE', 'ru')
# → "ru" (русский)

# 3. Переводим ВСЕ элементы
translated_elements = translation_service.translate_elements(
    elements,
    source_lang='de',
    target_lang='ru'
)
```

### Результат - Dual Text Storage:

Каждый элемент получает **оба варианта текста:**

```json
{
  "id": "slide_1_block_2",
  "type": "paragraph",
  "bbox": [72, 346, 515, 42],
  
  "text": "Epidermis der Blattoberseite",
  "text_original": "Epidermis der Blattoberseite",
  "text_translated": "Эпидермис верхней стороны листа",
  
  "language_original": "de",
  "language_target": "ru"
}
```

## 🎯 Как используется в Pipeline

### Stage 3: Script Generation (LLM)

**Использует `text_translated` для генерации скрипта:**

```python
# semantic_analyzer.py
text = elem.get('text_translated') or elem.get('text', '')

# smart_script_generator.py
text = elem.get('text_translated') or elem.get('text')
```

**Результат:** TTS произносит на русском языке

```json
{
  "talk_track": [
    {
      "text": "Эпидермис верхней стороны листа с кутикулой",
      "group_id": "group_epidermis"
    }
  ]
}
```

### Stage 4: TTS Generation

**TTS получает русский текст:**
```
"Эпидермис верхней стороны листа" → TTS → audio + word_timings
```

**Word timings содержат русские слова:**
```json
[
  {"word": "эпидермис", "start": 2.5, "end": 3.2},
  {"word": "верхней", "start": 3.2, "end": 3.6},
  {"word": "стороны", "start": 3.6, "end": 4.0},
  {"word": "листа", "start": 4.0, "end": 4.3}
]
```

### Stage 5: Visual Effects (КЛЮЧЕВОЙ ЭТАП)

**bullet_point_sync.py использует `text_translated` для matching:**

```python
# 1. Matching с Whisper использует ПЕРЕВЕДЕННЫЙ текст
text = match['text_translated'].strip()  # "Эпидермис верхней стороны листа"
first_time = self._find_first_mention_time(text, group_words)
# → Находит timing 2.5s (когда произносится "эпидермис")

# 2. Но в cue сохраняется ОРИГИНАЛЬНЫЙ текст и bbox
cue = {
    'action': 'highlight',
    'bbox': elem.get('bbox'),  # Координаты немецкого текста на слайде!
    't0': 2.5,  # Когда произносится "эпидермис"
    't1': 4.3,  # Когда заканчивается "листа"
    
    'text': match['text_original'].strip(),  # "Epidermis der Blattoberseite"
    'text_original': "Epidermis der Blattoberseite",
    'text_translated': "Эпидермис верхней стороны листа"
}
```

## 🎬 Результат

**Что видит пользователь:**

```
t=2.5s: 🎤 "Эпидермис..." (аудио на русском)
        ✨ Подсвечивается "Epidermis der Blattoberseite" (текст на слайде на немецком)
        ✅ СИНХРОНИЗАЦИЯ РАБОТАЕТ!
```

## 📊 Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: OCR                                                 │
│ ┌───────────────────┐                                        │
│ │ "Epidermis der    │                                        │
│ │ Blattoberseite"   │ ← Немецкий текст с слайда              │
│ └───────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2.5: Translation                                       │
│ ┌───────────────────┐        ┌───────────────────┐          │
│ │ text_original:    │        │ text_translated:  │          │
│ │ "Epidermis..."    │ ----→  │ "Эпидермис..."    │          │
│ │ (DE)              │        │ (RU)              │          │
│ └───────────────────┘        └───────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                        ↓                    ↓
                        │                    │
         ┌──────────────┘                    └──────────────┐
         │ (для отображения)                  (для LLM/TTS) │
         ↓                                                   ↓
┌─────────────────────┐                    ┌─────────────────────┐
│ Stage 5:            │                    │ Stage 3+4:          │
│ Visual Effects      │                    │ Script + TTS        │
│                     │                    │                     │
│ bbox ← text_original│                    │ LLM ← text_translated│
│ timing ← matching   │ ← word_timings ← │ TTS ← русский текст  │
│   по text_translated│                    │                     │
└─────────────────────┘                    └─────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Результат: Highlight "Epidermis..." в момент "Эпидермис..." │
└─────────────────────────────────────────────────────────────┘
```

## ✅ Проверка работы Translation

### В Docker:

```bash
docker exec slide-speaker-main-backend-1 python3 -c "
from app.services.translation_service import TranslationService
ts = TranslationService()
print(f'Available: {ts.available}')
print(f'Enabled: {ts.translation_enabled}')
print(f'de→ru needed: {ts.is_translation_needed(\"de\", \"ru\")}')
"
```

**Ожидаемый output:**
```
Available: True ✅
Enabled: True ✅
de→ru needed: True ✅
```

### В manifest.json:

```bash
# Проверить что элементы имеют оба поля
cat manifest.json | jq '.slides[0].elements[0] | {
  text_original, 
  text_translated, 
  language_original, 
  language_target
}'
```

**Ожидаемый output:**
```json
{
  "text_original": "Epidermis der Blattoberseite",
  "text_translated": "Эпидермис верхней стороны листа",
  "language_original": "de",
  "language_target": "ru"
}
```

### В cues:

```bash
# Проверить что cues содержат оба текста
cat manifest.json | jq '.slides[0].cues[0] | {
  text_original,
  text_translated,
  t0,
  t1
}'
```

**Ожидаемый output:**
```json
{
  "text_original": "Epidermis der Blattoberseite",
  "text_translated": "Эпидермис верхней стороны листа",
  "t0": 2.5,
  "t1": 4.3
}
```

## 🐛 Проблемы и решения

### Проблема 1: "Старые уроки без translation"

**Симптом:**
```json
{
  "text": "Epidermis...",
  "text_original": null,  ❌
  "text_translated": null  ❌
}
```

**Причина:** Урок обработан до добавления Translation Service

**Решение:**
```bash
# Очистить кэш и перезапустить обработку
docker exec slide-speaker-main-redis-1 redis-cli FLUSHDB
# Загрузить урок заново
```

### Проблема 2: "Translation disabled"

**Симптом:**
```
Translation enabled: False
```

**Причина:** Отсутствует `GOOGLE_APPLICATION_CREDENTIALS`

**Решение:**
```bash
# В docker.env или docker-compose.yml
GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-sa.json

# Убедиться что файл существует
docker exec slide-speaker-main-backend-1 ls -la /app/keys/gcp-sa.json
```

### Проблема 3: "Visual effects не синхронизированы"

**Симптом:** Подсветка появляется не вовремя

**Причина:** Возможно:
1. Не работает Whisper word-level timing
2. text_translated не используется для matching
3. Кэш содержит старые результаты

**Решение:**
```bash
# 1. Очистить slide dedup cache
docker exec slide-speaker-main-redis-1 sh -c "redis-cli KEYS 'slide_processed:*' | xargs redis-cli DEL"

# 2. Проверить что bullet_point_sync использует text_translated
grep "text_translated" backend/app/services/bullet_point_sync.py

# 3. Перезапустить обработку
```

## 🎓 Важные детали реализации

### 1. Fallback в visual_effects_engine.py

Есть **статический словарь** немецких терминов:

```python
self.term_translations = {
    'epidermis': ['эпидермис', 'эпидерма'],
    'hypodermis': ['гиподермис', 'гиподерма'],
    'mesophyll': ['мезофилл'],
    # ... еще ~30 терминов
}
```

**Зачем?** Fallback если Google Translate API недоступен

### 2. Двойной matching в bullet_point_sync

```python
# Сначала пробуем найти по text_translated
text = elem.get('text_translated') or elem.get('text', '')
first_time = self._find_first_mention_time(text, whisper_words)

# Если не нашли - fallback на text (для старых уроков)
```

### 3. Frontend показывает оригинальный текст

```typescript
// Player.tsx НЕ переключает текст
// Слайд всегда показывает оригинальный текст (немецкий)
// Только highlight bbox основан на timing русской озвучки
```

## 📈 Преимущества подхода

✅ **Универсальность**: Работает для любой языковой пары  
✅ **Точность**: Word-level timing через Whisper  
✅ **Прозрачность**: Оригинальный текст остается на слайде  
✅ **Fallback**: Static dictionary + Google Translate  
✅ **Кэширование**: Переводы кэшируются (экономия API calls)

## 🚀 Итог

**Translation Service - ключевой компонент** для визуальных эффектов на мультиязычных презентациях.

Без него невозможно синхронизировать:
- Немецкий текст на слайдах
- С русской озвучкой
- В реальном времени

**Статус:** ✅ Реализовано и работает в Docker
