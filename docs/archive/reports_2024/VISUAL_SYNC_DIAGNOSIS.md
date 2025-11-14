# Диагностика проблемы синхронизации визуальных эффектов

**Дата:** 2025-01-07  
**Статус:** 🔴 КРИТИЧЕСКАЯ ПРОБЛЕМА ОБНАРУЖЕНА

---

## 📋 Краткое описание проблемы

Визуальные эффекты (highlights, spotlights) не синхронизированы с голосом, потому что:
1. ❌ Двойной префикс "group_" создает некорректные SSML марки
2. ❌ Group markers могут отсутствовать в talk_track (зависит от LLM)
3. ❌ Fallback на text-based matching не работает в SSML режиме
4. ❌ Visual effects не получают реальные TTS timings для синхронизации

---

## 🔍 Анализ потока данных

### Этап 1: Semantic Analysis (SemanticAnalyzer)

**Создает semantic groups:**
```python
# Mock режим:
{"id": "group_0", "type": "title", ...}
{"id": "group_1", "type": "content", ...}

# LLM режим (из few-shot examples):
{"id": "group_title", "type": "title", ...}
{"id": "group_heading", "type": "heading", ...}
```

**Проблема:** Непостоянный формат ID:
- Mock: `group_0`, `group_1` (числовой)
- LLM: `group_title`, `group_heading` (семантический)

---

### Этап 2: Script Generation (SmartScriptGenerator)

**Генерирует talk_track:**
```json
{
  "talk_track": [
    {"segment": "hook", "text": "...", "group_id": "group_title"},
    {"segment": "explanation", "text": "...", "group_id": "group_0"}
  ]
}
```

**Проблема:** LLM может НЕ ВЕРНУТЬ `group_id` в response!
- Зависит от temperature и prompt
- В mock режиме group_id есть, но может быть null
- Если group_id отсутствует → SSML markers не создаются → нет синхронизации

---

### Этап 3: SSML Generation (SSMLGenerator)

**Код:**
```python
def generate_ssml_from_talk_track(talk_track):
    for segment in talk_track:
        group_id = segment.get('group_id')  # Может быть None!
        
        if group_id:
            all_parts.append(f'<mark name="group_{group_id}"/>')
            #                                ^^^^^^^^^^^^^^^^
            #                                ДВОЙНОЙ ПРЕФИКС!
```

**Проблема 1: Двойной префикс "group_"**

Если `group_id = "group_title"`, то:
```xml
<mark name="group_group_title"/>  <!-- ❌ Неправильно! -->
```

Правильно было бы:
```xml
<mark name="group_title"/>  <!-- ✅ -->
```

**Проблема 2: Марки не создаются**

Если `group_id` отсутствует в talk_track:
```python
if group_id:  # False!
    # Марка НЕ создается
```

Результат:
```xml
<speak>
  <prosody rate="medium" pitch="+2st">
    <mark name="w0"/>Давайте <mark name="w1"/>рассмотрим...
  </prosody>
</speak>
```

Только word marks (`w0`, `w1`), БЕЗ group marks!

---

### Этап 4: TTS Synthesis (GoogleTTSWorkerSSML)

**Генерирует audio + word_timings:**
```python
word_timings = [
    {'mark_name': 'group_group_title', 'time_seconds': 0.3},  # Если марка была
    {'mark_name': 'w0', 'time_seconds': 0.35},
    {'mark_name': 'w1', 'time_seconds': 0.58},
    ...
]
```

**Проблема:** Если group markers не были созданы в SSML:
```python
word_timings = [
    {'mark_name': 'w0', 'time_seconds': 0.35},  # Только word marks!
    {'mark_name': 'w1', 'time_seconds': 0.58},
    # ❌ НЕТ group_group_title!
]
```

---

### Этап 5: Visual Effects (VisualEffectsEngine)

**Пытается найти timing для группы:**

```python
def _find_group_timing(self, group_id: str, word_timings: List[Dict], ...) -> Optional[Dict]:
    marker_name = f"group_{group_id}"  # "group_" + "group_title" = "group_group_title"
    
    for timing in word_timings:
        mark_name = timing.get('mark_name', timing.get('word', ''))
        
        if mark_name == marker_name:  # Сравнение "group_group_title" == ?
            # ✅ Нашли!
            return {'start': timing['time_seconds'], ...}
    
    # ❌ Не нашли!
    return None
```

**Сценарий 1: Двойной префикс работает (случайно)**
- SSML создал: `group_group_title`
- TTS вернул: `mark_name: "group_group_title"`
- VisualEffects ищет: `"group_group_title"`
- **Результат:** ✅ Работает, но семантически неправильно

**Сценарий 2: Group marker отсутствует**
- SSML НЕ создал group marker (group_id был null)
- TTS вернул только word marks: `w0`, `w1`, ...
- VisualEffects ищет: `"group_group_title"`
- **Результат:** ❌ НЕ НАЙДЕНО → fallback

**Fallback: _find_text_timing()**

```python
def _find_text_timing(self, text: str, word_timings: List[Dict], ...) -> Optional[Dict]:
    for timing in word_timings:
        word = timing.get('word', timing.get('mark_name', '')).lower().strip()
        # ❌ ПРОБЛЕМА: 'word' содержит mark name ("w0", "group_group_title")
        #    а НЕ реальный текст!
        
        if self._normalize_word(word) == self._normalize_word(search_words[0]):
            # Никогда не найдет, потому что сравнивает "w0" с "давайте"
            return {'start': ...}
    
    return None  # ❌ НЕ НАЙДЕНО
```

**Проблема fallback:**
- В SSML режиме `word_timings` содержит только mark names
- `timing.get('word')` возвращает `"w0"`, `"w1"`, а не реальные слова
- Text matching не работает!

---

## 🎯 Корневые причины

### 1. ❌ Двойной префикс "group_"

**Где:** `backend/app/services/ssml_generator.py:60`

```python
if group_id:
    all_parts.append(f'<mark name="group_{group_id}"/>')
    #                                ^^^^^^ Добавляет "group_" к уже существующему "group_title"
```

**Решение:**
```python
if group_id:
    # Не добавляем префикс, если он уже есть
    marker_name = group_id if group_id.startswith('group_') else f'group_{group_id}'
    all_parts.append(f'<mark name="{marker_name}"/>')
```

---

### 2. ❌ Group_id может отсутствовать в talk_track

**Где:** `backend/app/services/smart_script_generator.py`

SmartScriptGenerator полагается на LLM для возврата `group_id`:

```python
# LLM prompt просит:
"group_id": "group_id_from_semantic_map_or_null"

# Но LLM может вернуть:
{"segment": "hook", "text": "...", "group_id": null}  # ❌
# или вообще пропустить поле:
{"segment": "hook", "text": "..."}  # ❌
```

**Решение:**
1. Улучшить prompt - требовать обязательное заполнение group_id
2. Post-processing: если group_id отсутствует, попытаться сопоставить текст с groups
3. Fallback: использовать sentence timings для синхронизации

---

### 3. ❌ Text-based fallback сломан

**Где:** `backend/app/services/visual_effects_engine.py:370`

```python
def _find_text_timing(...):
    for timing in word_timings:
        word = timing.get('word', timing.get('mark_name', ''))
        # В SSML режиме 'word' = mark name ("w0", "group_group_title")
        # НЕ реальное слово!
```

**Решение:**
Использовать `sentences` из `tts_words` для text matching:

```python
def _find_text_timing(self, text: str, tts_words: Dict, ...) -> Optional[Dict]:
    # Use sentences instead of word_timings
    sentences = tts_words.get('sentences', [])
    
    for sentence in sentences:
        sentence_text = sentence.get('text', '').lower()
        
        if text.lower()[:30] in sentence_text:  # Match first 30 chars
            return {
                'start': sentence['t0'],
                'duration': sentence['t1'] - sentence['t0'],
                'end': sentence['t1']
            }
    
    return None
```

---

### 4. ❌ VisualEffectsEngine также добавляет "group_"

**Где:** `backend/app/services/visual_effects_engine.py:280`

```python
def _find_group_timing(self, group_id: str, ...):
    marker_name = f"group_{group_id}"  # Если group_id = "group_title"
    #                                  # Получится "group_group_title"
```

Это работает, потому что SSMLGenerator тоже добавляет "group_", но семантически неправильно.

**Решение:**
```python
def _find_group_timing(self, group_id: str, ...):
    # Don't add prefix if already present
    marker_name = group_id if group_id.startswith('group_') else f'group_{group_id}'
```

---

## 🔧 План исправления

### Исправление 1: Убрать двойной префикс

**Файл:** `backend/app/services/ssml_generator.py`

```python
# ДО:
if group_id:
    all_parts.append(f'<mark name="group_{group_id}"/>')

# ПОСЛЕ:
if group_id:
    # Normalize marker name - don't double "group_" prefix
    marker_name = group_id if group_id.startswith('group_') else f'group_{group_id}'
    all_parts.append(f'<mark name="{marker_name}"/>')
    logger.debug(f"Added group marker: {marker_name}")
```

---

### Исправление 2: Нормализация в VisualEffectsEngine

**Файл:** `backend/app/services/visual_effects_engine.py`

```python
# ДО:
def _find_group_timing(self, group_id: str, ...):
    marker_name = f"group_{group_id}"

# ПОСЛЕ:
def _find_group_timing(self, group_id: str, ...):
    # Normalize marker name to match SSML
    marker_name = group_id if group_id.startswith('group_') else f'group_{group_id}'
    logger.debug(f"Looking for group marker: {marker_name}")
```

---

### Исправление 3: Использовать sentences для text fallback

**Файл:** `backend/app/services/visual_effects_engine.py`

```python
def generate_cues_from_semantic_map(
    self,
    semantic_map: Dict[str, Any],
    elements: List[Dict[str, Any]],
    audio_duration: float,
    tts_words: Optional[Dict[str, Any]] = None  # Передаем полный tts_words!
) -> List[Dict[str, Any]]:
    
    # ...
    
    # ✅ Try to find timing from TTS words using group_id
    timing_info = self._find_group_timing(group_id, word_timings, audio_duration)
    
    if not timing_info:
        # ✅ Fallback: use sentence-level matching
        group_text = self._get_group_text(group, elements_by_id)
        timing_info = self._find_text_timing_from_sentences(group_text, tts_words, audio_duration)
```

**Новый метод:**
```python
def _find_text_timing_from_sentences(
    self, 
    text: str, 
    tts_words: Optional[Dict[str, Any]], 
    audio_duration: float
) -> Optional[Dict[str, float]]:
    """
    Find timing by matching text to TTS sentences (fallback)
    """
    if not tts_words or not text:
        return None
    
    sentences = tts_words.get('sentences', [])
    if not sentences:
        return None
    
    # Normalize search text
    search_text = text.lower().strip()[:50]  # First 50 chars
    
    for sentence in sentences:
        sentence_text = sentence.get('text', '').lower().strip()
        
        # Check if search text appears in sentence
        if search_text[:20] in sentence_text:
            duration = sentence['t1'] - sentence['t0']
            return {
                'start': sentence['t0'],
                'duration': min(duration, self.max_highlight_duration),
                'end': sentence['t1']
            }
    
    return None
```

---

### Исправление 4: Улучшить LLM prompt для group_id

**Файл:** `backend/app/services/smart_script_generator.py`

```python
def _create_script_generation_prompt(...):
    # ...
    
    return f"""...

IMPORTANT ABOUT group_id:
- **MANDATORY**: Include "group_id" field for EVERY segment
- When talking about a specific group, use its "id" field exactly as given
- Use null ONLY for general introductions without specific group reference
- Available group IDs: {', '.join([g.get('id') for g in groups])}

Example with group_ids:
{{
  "talk_track": [
    {{"segment": "hook", "text": "...", "group_id": "group_title"}},  ✅ HAS group_id
    {{"segment": "context", "text": "...", "group_id": null}},        ✅ Explicit null
    {{"segment": "explanation", "text": "...", "group_id": "group_0"}} ✅ HAS group_id
  ]
}}

❌ WRONG:
{{"segment": "hook", "text": "..."}}  <!-- Missing group_id field! -->

..."""
```

---

### Исправление 5: Добавить debug logging

**Файл:** `backend/app/pipeline/intelligent_optimized.py`

```python
# После генерации SSML
if ssml_texts:
    ssml_preview = ssml_texts[0][:500]  # Больше для debug
    has_marks = '<mark' in ssml_texts[0]
    
    # ✅ Подсчитаем group markers
    import re
    group_marks = re.findall(r'<mark name="(group_[^"]+)"', ssml_texts[0])
    
    self.logger.info(f"🎙️ Slide {slide_id}: SSML generated")
    self.logger.info(f"   SSML length: {len(ssml_texts[0])} chars")
    self.logger.info(f"   Has <mark> tags: {has_marks}")
    self.logger.info(f"   Group markers found: {len(group_marks)} - {group_marks[:5]}")
    self.logger.info(f"   SSML preview: {ssml_preview}")
```

**Файл:** `backend/app/services/visual_effects_engine.py`

```python
def _find_group_timing(...):
    marker_name = group_id if group_id.startswith('group_') else f'group_{group_id}'
    
    logger.debug(f"🔍 Looking for group marker: '{marker_name}'")
    logger.debug(f"   Available marks: {[t.get('mark_name', t.get('word', '?')) for t in word_timings[:10]]}")
    
    for i, timing in enumerate(word_timings):
        mark_name = timing.get('mark_name', timing.get('word', ''))
        
        if mark_name == marker_name:
            logger.info(f"✅ Found group marker '{marker_name}' at {timing['time_seconds']:.2f}s")
            # ...
    
    logger.warning(f"⚠️  Group marker '{marker_name}' NOT FOUND in {len(word_timings)} timings")
    return None
```

---

## 📊 Ожидаемый результат после исправлений

### До:
```
🎙️ Slide 1: generating SSML audio (1 segments)
   SSML preview: <speak><mark name="group_group_title"/>...
   Has <mark> tags: True

✅ Slide 1: audio generated (5.2s)
   Word timings: 15 marks, 3 sentences

⚠️  Group marker 'group_group_title' NOT FOUND in 15 timings
WARNING: No TTS word timings available, using time-based distribution
Generated 3 visual cues
```

### После:
```
🎙️ Slide 1: SSML generated
   SSML length: 450 chars
   Has <mark> tags: True
   Group markers found: 3 - ['group_title', 'group_content', 'group_list']
   SSML preview: <speak><mark name="group_title"/>...

✅ Slide 1: audio generated (5.2s)
   Word timings: 15 marks, 3 sentences

🔍 Looking for group marker: 'group_title'
   Available marks: ['group_title', 'w0', 'w1', 'w2', 'w3', ...]
✅ Found group marker 'group_title' at 0.30s

Group 'group_title' synced to TTS: 0.30s - 2.50s
Group 'group_content' synced to TTS: 2.70s - 5.10s
Generated 3 visual cues
```

---

## ✅ Checklist исправлений

- [ ] 1. Убрать двойной префикс "group_" в SSMLGenerator
- [ ] 2. Нормализовать marker_name в VisualEffectsEngine._find_group_timing()
- [ ] 3. Добавить _find_text_timing_from_sentences() для fallback
- [ ] 4. Улучшить LLM prompt в SmartScriptGenerator
- [ ] 5. Добавить debug logging в intelligent_optimized.py
- [ ] 6. Добавить debug logging в visual_effects_engine.py
- [ ] 7. Протестировать на реальной презентации
- [ ] 8. Проверить логи на наличие group markers
- [ ] 9. Проверить синхронизацию визуальных эффектов в плеере

---

**Автор:** Droid AI Assistant  
**Дата:** 2025-01-07  
**Время анализа:** 45 минут
