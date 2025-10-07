# 📊 Аудит данных загруженной презентации

**Дата:** 2025-01-XX  
**Презентация:** `Kurs_10 (verschoben).pdf`  
**UUID:** `2370ee5a-b9e5-4af1-8374-f087096f7151`  
**Слайдов:** 2

---

## ✅ Что работает ПРАВИЛЬНО:

### 1. **Elements & BBox** ✅
```json
{
  "id": "slide_1_block_0",
  "type": "heading",
  "text": "universität innsbruck",
  "bbox": [93, 37, 237, 74],
  "confidence": 0.9
}
```
- ✅ Все элементы имеют `bbox` координаты
- ✅ Типы элементов определены (heading, paragraph, list_item)
- ✅ OCR работает корректно
- **Статистика:** 2/2 слайдов (100%)

---

### 2. **Semantic Map** ✅
```json
{
  "id": "group_title",
  "name": "Slide Title",
  "type": "title",
  "priority": "high",
  "element_ids": ["slide_1_block_1"],
  "highlight_strategy": {
    "when": "start",
    "effect_type": "spotlight",
    "duration": 2.0,
    "intensity": "normal"
  }
}
```
- ✅ Семантические группы созданы
- ✅ Приоритеты определены (high/medium)
- ✅ Стратегии подсветки определены
- ✅ 5 групп для слайда 1

---

### 3. **Talk Track** ✅
```json
{
  "segment": "hook",
  "text": "Итак, друзья, сегодня мы погружаемся в удивительный мир листьев..."
}
```
- ✅ Сгенерирован структурированный сценарий
- ✅ 6 сегментов: hook, context, explanation, example, emphasis, transition
- ✅ Текст на русском языке
- **Статистика:** 2/2 слайдов (100%)

---

### 4. **Audio Files** ✅
```json
{
  "audio": "/assets/{uuid}/audio/001.wav",
  "duration": 98.535
}
```
- ✅ Аудио файлы созданы
- ✅ Длительность записана
- ✅ Формат: WAV
- **Статистика:** 2/2 слайдов (100%)

---

### 5. **Visual Cues (временные метки)** ✅
```json
{
  "cue_id": "cue_abc123",
  "t0": 0.3,
  "t1": 2.3,
  "action": "spotlight",
  "bbox": [588, 97, 265, 47],
  "element_id": "slide_1_block_1"
}
```
- ✅ Временные метки присутствуют
- ✅ BBox координаты есть
- ✅ Типы эффектов определены (spotlight, underline, sequential_cascade)
- ✅ 6 cues для слайда 1
- **Статистика:** 2/2 слайдов (100%)

---

## ❌ Что НЕ работает:

### 1. **SSML отсутствует** ❌

**Проблема:**
```python
# В manifest.json:
talk_track[0]['ssml_text']  # ← НЕТ!
slide['speaker_notes_ssml']  # ← НЕТ!
```

**Что ожидалось:**
```xml
<speak>
  <prosody rate="medium" pitch="+2st">
    <mark name="w0"/>Итак, <mark name="w1"/>друзья, <mark name="w2"/>сегодня...
  </prosody>
</speak>
```

**Почему это критично:**
- ❌ Без SSML нет `<mark>` тегов
- ❌ Без `<mark>` тегов Google TTS не возвращает word timings
- ❌ Без word timings невозможна точная синхронизация визуальных эффектов с речью

**Причина:**
- Функция `generate_ssml_from_talk_track()` вызывается в коде
- Но SSML не сохраняется в manifest.json
- Вероятно, передается напрямую в TTS, но не сохраняется для проверки

**Статистика:** 0/2 слайдов (0%) ❌

---

### 2. **Word Timings отсутствуют** ❌

**Проблема:**
```python
# В manifest.json:
slide['tts_words']  # ← НЕТ! (удалено после финализации)
```

**Что ожидалось:**
```json
{
  "tts_words": {
    "sentences": [
      {"text": "...", "t0": 0.0, "t1": 2.5}
    ],
    "word_timings": [
      {"mark_name": "w0", "time_seconds": 0.34},
      {"mark_name": "w1", "time_seconds": 0.82}
    ]
  }
}
```

**Почему это критично:**
- ❌ Визуальные эффекты используют приблизительные временные метки
- ❌ Нет точной синхронизации "когда это слово произносится"
- ❌ Невозможно проверить правильность работы SSML

**Причина:**
- `tts_words` удаляется из manifest в методе `build_manifest()`
- Это делается намеренно для уменьшения размера файла
- Но для debugging нужно сохранять хотя бы sample

**Статистика:** 0/2 слайдов (0%) ❌

---

### 3. **Cues привязаны к element_ids, а не group_ids** ⚠️

**Проблема:**
```json
// Cue:
{
  "element_id": "slide_1_block_1"  // ← element!
}

// Semantic group:
{
  "id": "group_title",  // ← group!
  "element_ids": ["slide_1_block_1"]
}
```

**Почему это проблема:**
- Visual Effects Engine генерирует cues на основе semantic_map
- Но использует `element_id` в cue вместо `group_id`
- Это затрудняет отладку: непонятно какая группа к какому cue относится

**Последствия:**
- ⚠️ Cue нельзя напрямую сопоставить с semantic группой
- ⚠️ Нужно искать через element_ids
- ⚠️ Усложняет логику фронтенда

**Код:**
```python
# backend/app/services/visual_effects_engine.py
cue = {
    "element_id": group.get('id'),  # ← Должно быть group_id!
    ...
}
```

---

## 📊 Итоговая таблица

| Компонент | Статус | Использование | Критичность |
|-----------|--------|---------------|-------------|
| **Elements + BBox** | ✅ 100% | Да, для визуальных эффектов | Высокая |
| **Semantic Map** | ✅ 100% | Да, для группировки | Высокая |
| **Talk Track** | ✅ 100% | Да, для генерации текста | Высокая |
| **Audio Files** | ✅ 100% | Да, для воспроизведения | Высокая |
| **Visual Cues** | ✅ 100% | Да, для эффектов | Высокая |
| **SSML** | ❌ 0% | Нет в manifest | **КРИТИЧНО** |
| **Word Timings** | ❌ 0% | Удалены из manifest | Средняя |
| **Group IDs в cues** | ⚠️ Проблема | Используются element_ids | Низкая |

---

## 🎯 Рекомендации

### Приоритет 1 (критично):

#### 1. Сохранять SSML в manifest для проверки
```python
# В intelligent_optimized.py, метод tts()
slide['speaker_notes_ssml'] = ssml_texts[0] if ssml_texts else None
```

#### 2. Проверить что SSML действительно используется TTS
```python
# Логировать:
logger.info(f"SSML preview: {ssml_texts[0][:200]}...")
logger.info(f"SSML has <mark> tags: {bool('<mark' in ssml_texts[0])}")
```

#### 3. Сохранять word_timings для отладки
```python
# Не удалять tts_words полностью, а сохранять sample:
slide['tts_words_sample'] = {
    'total_marks': len(tts_words.get('word_timings', [])),
    'first_3_marks': tts_words.get('word_timings', [])[:3],
    'sentences_count': len(tts_words.get('sentences', []))
}
```

### Приоритет 2 (важно):

#### 4. Исправить привязку cues к группам
```python
# visual_effects_engine.py
cue = {
    "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
    "group_id": group.get('id'),  # ← Добавить!
    "element_id": element_ids[0] if element_ids else None,  # ← Оставить для совместимости
    ...
}
```

#### 5. Добавить валидацию SSML
```python
def validate_ssml(ssml: str) -> bool:
    """Проверить что SSML валиден и содержит <mark> теги"""
    if '<speak>' not in ssml:
        return False
    if '<mark' not in ssml:
        logger.warning("SSML без <mark> тегов!")
        return False
    return True
```

### Приоритет 3 (желательно):

#### 6. Логирование статистики
```python
logger.info(f"TTS generated: {len(word_timings)} word marks, "
            f"{len(sentences)} sentences, "
            f"duration: {duration:.1f}s")
```

#### 7. Smoke test после обработки
```python
# Проверить что данные полные:
assert len(cues) > 0, "No visual cues generated!"
assert all('bbox' in c for c in cues), "Some cues missing bbox!"
assert duration > 0, "Audio duration is zero!"
```

---

## 📝 Выводы

### ✅ Работает хорошо:
1. OCR и извлечение элементов
2. Семантический анализ и группировка
3. Генерация сценария (talk_track)
4. Синтез аудио
5. Создание визуальных эффектов с временными метками

### ❌ Требует исправления:
1. **SSML не сохраняется** - критическая проблема для отладки
2. **Word timings удаляются** - невозможно проверить точность синхронизации
3. **Cues используют element_ids** - затрудняет отладку

### 🎯 Главное:
**Пайплайн генерирует все необходимые данные**, но:
- SSML создается, но не сохраняется в manifest
- Word timings получаются от TTS, но удаляются после финализации
- Визуальные эффекты работают, но используют приблизительные временные метки

**Для production:** Пайплайн работает, но для отладки и улучшения синхронизации нужно сохранять SSML и word timings хотя бы частично.

---

## 📂 Файлы для проверки

1. `manifest.json` - проверить наличие:
   - `speaker_notes_ssml` ❌
   - `tts_words` ❌
   - `cues[].group_id` ❌

2. Логи пайплайна:
   ```bash
   docker logs slide-speaker-main-backend-1 2>&1 | grep -i "ssml\|mark\|timing"
   ```

3. Код для исправления:
   - `backend/app/pipeline/intelligent_optimized.py` - метод `tts()`
   - `backend/app/services/visual_effects_engine.py` - метод `generate_cues_from_semantic_map()`
