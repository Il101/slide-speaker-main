# 🐛 Проблемы с визуальными эффектами

## Обнаружено 2 критичные проблемы:

---

## ❌ Проблема 1: TTS word timings НЕ используются

### Что не так:

**В manifest.json:**
```json
{
  "tts_words": false  ← НЕТ временных меток от TTS!
}
```

**В коде:**
```python
# visual_effects_engine.py line 83
def generate_cues_from_semantic_map(
    semantic_map,
    elements,
    audio_duration,
    tts_words: Optional[Dict[str, Any]] = None  ← Параметр есть, но НЕ используется!
):
    # ...
    current_time = 0.5  # Start with 0.5s delay ← HARDCODED!
    
    for group in groups:
        # ...
        current_time += duration + self.min_gap_between_effects
        # ← Просто равномерно распределяем по времени!
```

### Проблема:

Visual cues **НЕ синхронизированы** с реальной озвучкой!

**Что должно быть:**
- TTS возвращает: `word_timings = [{mark_name: "машинное", time_seconds: 2.5}, ...]`
- Cue появляется ровно когда слово произносится: `t0 = 2.5`

**Что есть сейчас:**
- TTS timing игнорируется
- Cues распределяются равномерно: 0.5s, 3s, 6s, ...
- НЕ совпадает с реальной озвучкой!

---

## ❌ Проблема 2: Координаты (bbox) используются, но есть проблемы

### Что не так:

**1. Координаты от Vision API используются:**
```python
# Из manifest.json - элементы с bbox от Vision API ✅
{
  "id": "slide_1_block_2",
  "bbox": [72, 346, 515, 42],  ← От Vision API
  "text": "Anatomische Blatt - Typen :"
}

# В cues - bbox копируется ✅
{
  "bbox": [72, 346, 515, 42],
  "element_id": "slide_1_block_2"
}
```

**НО есть проблемы:**

#### 2.1. Несуществующие element_id

```json
{
  "cue_id": "cue_6f511b15",
  "bbox": [578, 87, 285, 67],
  "element_id": "group_title",  ← Такого ID нет в elements!
  "invalid_element": true  ← Флаг ошибки
}
```

**Причина:**
```python
# visual_effects_engine.py
cues.append({
    "element_id": group.get('id'),  ← ID группы, а не элемента!
    # Должно быть: elem.get('id') для каждого элемента
})
```

#### 2.2. Bbox для группы вычисляется неправильно

```python
def _calculate_group_bbox(self, elements: List[Dict[str, Any]]) -> List[float]:
    """Calculate bounding box for group of elements"""
    bboxes = [elem.get('bbox', [0, 0, 0, 0]) for elem in elements]
    
    # Extract min/max
    min_x = min(bbox[0] for bbox in bboxes)
    min_y = min(bbox[1] for bbox in bboxes)
    max_x = max(bbox[0] + bbox[2] for bbox in bboxes)  ← Правильно
    max_y = max(bbox[1] + bbox[3] for bbox in bboxes)  ← Правильно
    
    return [min_x, min_y, max_x - min_x, max_y - min_y]
```

**Это правильно!** Но проблема в том, что группы не всегда корректны.

#### 2.3. Масштабирование НЕ проверяется

```python
# Нет проверки размера слайда!
# Vision API возвращает координаты для оригинального размера
# А слайд может быть масштабирован!

# Должна быть нормализация:
bbox_normalized = [
    bbox[0] / original_width,   # x в процентах
    bbox[1] / original_height,  # y в процентах
    bbox[2] / original_width,   # width в процентах
    bbox[3] / original_height   # height в процентах
]
```

---

## 📊 Примеры проблем из реального manifest

### Проблема А: Неверный element_id

```json
{
  "cue_id": "cue_6f511b15",
  "t0": 0.3,
  "t1": 2.3,
  "element_id": "group_title",  ← НЕ существует!
  "invalid_element": true
}
```

**Элементы в slide:**
```json
["slide_1_block_0", "slide_1_block_1", ...]  ← "group_title" нет!
```

### Проблема Б: Выделение буллита вместо текста

```json
{
  "cue_id": "cue_7db67092",
  "bbox": [75, 440, 13, 11],  ← Размер 13x11 px!
  "element_id": "slide_1_block_3",
  "text": "•"  ← Выделяется только буллит!
}
```

**Должно выделяться:**
```json
{
  "bbox": [129, 429, 712, 121],  ← Весь текст
  "text": "Monokotyle Pflanzen : parallelnervig..."
}
```

**Причина:** Semantic analyzer не объединяет буллит с текстом в одну группу.

---

## 🔧 Решение проблем

### Решение 1: Использовать TTS word timings

**Изменить:** `visual_effects_engine.py`

```python
def generate_cues_from_semantic_map(
    self,
    semantic_map,
    elements,
    audio_duration,
    tts_words: Optional[Dict[str, Any]] = None
):
    # ...
    
    # ✅ ДОБАВИТЬ: Извлечь word timings
    word_timings = []
    if tts_words and 'sentences' in tts_words:
        for sentence in tts_words['sentences']:
            if 'words' in sentence:
                word_timings.extend(sentence['words'])
    
    # ✅ ИСПОЛЬЗОВАТЬ: Найти время произношения текста группы
    for group in groups:
        group_text = self._get_group_text(group, elements_by_id)
        
        # Найти когда произносится этот текст
        timing = self._find_text_timing(group_text, word_timings)
        
        if timing:
            current_time = timing['start']  ← Реальное время!
            duration = timing['end'] - timing['start']
        else:
            # Fallback: равномерное распределение
            current_time = ...
```

### Решение 2: Исправить element_id для групп

```python
def _generate_group_cues(...):
    # БЫЛО:
    cues.append({
        "element_id": group.get('id'),  ← Неверно!
    })
    
    # СТАЛО:
    # Для spotlight на группу
    if effect_type == "spotlight":
        group_bbox = self._calculate_group_bbox(elements)
        
        cues.append({
            "element_id": f"group_{group.get('id')}",  ← Явно указываем что это группа
            "bbox": group_bbox,
            "group_elements": [e.get('id') for e in elements]  ← Список элементов
        })
    
    # Для sequential - создаём cue для каждого элемента
    elif effect_type == "sequential_cascade":
        for elem in elements:
            cues.append({
                "element_id": elem.get('id'),  ← Правильный ID элемента
                "bbox": elem.get('bbox')  ← Правильный bbox
            })
```

### Решение 3: Нормализовать координаты

```python
def _normalize_bbox(self, bbox: List[float], slide_width: int = 1440, slide_height: int = 1080):
    """Normalize bbox to percentage values"""
    return {
        "x": bbox[0] / slide_width,
        "y": bbox[1] / slide_height,
        "width": bbox[2] / slide_width,
        "height": bbox[3] / slide_height,
        "absolute": bbox  # Сохраняем оригинальные для debugging
    }
```

### Решение 4: Улучшить semantic grouping

**Проблема:** Буллит и текст в разных группах

**Решение:** В `semantic_analyzer.py`:

```python
def _should_merge_elements(elem1, elem2):
    """Check if elements should be in same group"""
    
    # Если elem1 - буллит, а elem2 - текст рядом
    if elem1['text'] in ['•', '-', '*'] and elem1['type'] == 'list_item':
        # Проверяем близость
        bbox1 = elem1['bbox']
        bbox2 = elem2['bbox']
        
        # Буллит и текст на одной высоте и близко по горизонтали
        vertical_overlap = abs(bbox1[1] - bbox2[1]) < 20
        horizontal_gap = abs(bbox1[0] + bbox1[2] - bbox2[0]) < 100
        
        if vertical_overlap and horizontal_gap:
            return True  # Объединить!
    
    return False
```

---

## 🧪 Проверка текущего состояния

### Что работает ✅:

1. ✅ **Bbox от Vision API используется** - координаты извлекаются
2. ✅ **Group bbox вычисляется правильно** - min/max алгоритм корректен
3. ✅ **Validation engine проверяет bbox** - есть проверки формата

### Что НЕ работает ❌:

1. ❌ **TTS timing НЕ используется** - cues не синхронизированы с озвучкой
2. ❌ **element_id для групп неверный** - указывается group_id вместо element_id
3. ❌ **Буллиты не объединяются с текстом** - выделяется только "•"
4. ❌ **Нормализация bbox отсутствует** - могут быть проблемы при масштабировании

---

## 📈 Влияние на UX

### Текущая ситуация:

```
Лектор говорит: "Анатомические типы листа..."  (t=2.5s)
Visual cue:      Выделяет буллит "•"         (t=4.2s)  ← НЕ синхронизировано!
                 Размер: 13x11 px             ← Слишком маленький!
```

### После исправления:

```
Лектор говорит: "Анатомические типы листа..."  (t=2.5s)
Visual cue:      Выделяет весь текст          (t=2.5s)  ← Синхронизировано! ✅
                 Размер: 712x121 px            ← Весь текст! ✅
```

---

## 🎯 План исправления

### Priority 1: TTS Timing (КРИТИЧНО)

**Файлы:**
- `backend/app/services/visual_effects_engine.py`
- `backend/app/pipeline/intelligent.py` (передать tts_words)

**Время:** 2-3 часа

### Priority 2: Element ID Fix (ВЫСОКИЙ)

**Файлы:**
- `backend/app/services/visual_effects_engine.py` (исправить _generate_group_cues)

**Время:** 1 час

### Priority 3: Semantic Grouping (СРЕДНИЙ)

**Файлы:**
- `backend/app/services/semantic_analyzer.py` (улучшить группировку)

**Время:** 3-4 часа

### Priority 4: Bbox Normalization (НИЗКИЙ)

**Файлы:**
- `backend/app/services/visual_effects_engine.py`

**Время:** 1-2 часа

---

## 💡 Рекомендация

**Начать с Priority 1 (TTS Timing)** - это самая критичная проблема, влияющая на восприятие лекции.

Без синхронизации с озвучкой визуальные эффекты выглядят случайными и отвлекают, а не помогают.

---

**Автор:** Droid AI Assistant  
**Дата:** 2025-01-06 23:55
