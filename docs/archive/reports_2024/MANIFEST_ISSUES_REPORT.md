# 🔍 Отчет об ошибках в manifest.json

**Дата:** 2025-01-XX  
**Файл:** `.data/2370ee5a-b9e5-4af1-8374-f087096f7151/manifest.json`  
**Презентация:** `Kurs_10 (verschoben).pdf`  
**Слайдов:** 2

---

## ❌ КРИТИЧЕСКИЕ ОШИБКИ (3)

### 1. ❌ **Неправильные ID элементов на слайде 2**

**Серьёзность:** 🔴 КРИТИЧЕСКАЯ

**Проблема:**
Все 22 элемента на слайде 2 имеют ID с префиксом `slide_1_` вместо `slide_2_`

```json
// Слайд 2, элемент 1:
{
  "id": "slide_1_block_0",  // ❌ Должно быть slide_2_block_0
  "text": "...",
  ...
}
```

**Последствия:**
- Конфликт ID между слайдами
- Невозможность правильно идентифицировать элементы
- Потенциальные ошибки при обработке

**Причина:**
Ошибка в OCR провайдере или парсере - ID генерируются некорректно для слайдов после первого.

**Как исправить:**
Проверить код в `backend/app/services/provider_factory.py` или OCR worker - возможно счётчик слайдов не инкрементируется.

---

### 2. ⚠️ **Отсутствуют group_id во всех cues**

**Серьёзность:** 🟡 СРЕДНЯЯ

**Проблема:**
Ни один cue не содержит поле `group_id`

```json
// Текущая структура:
{
  "cue_id": "cue_6c3e3935",
  "element_id": "slide_1_block_1",  // ✅ Есть
  "group_id": null,                  // ❌ Отсутствует!
  ...
}
```

**Последствия:**
- Невозможно напрямую связать cue с semantic группой
- Усложняется отладка визуальных эффектов
- Нужно искать через element_id → group.element_ids

**Причина:**
Манифест создан **СТАРОЙ** версией кода (до наших исправлений в `visual_effects_engine.py`)

**Как исправить:**
Перезапустить обработку презентации с новым кодом. Наши исправления добавляют `group_id` автоматически.

---

### 3. ⚠️ **Перекрытия временных меток на слайде 2**

**Серьёзность:** 🟡 СРЕДНЯЯ

**Проблема:**
6 пар cues перекрываются по времени

```
Cue 13: t0=10.0s, t1=10.5s
Cue 14: t0=10.0s, t1=10.5s  // ❌ Перекрытие 0.5s!
```

**Последствия:**
- Несколько визуальных эффектов одновременно
- Может запутать пользователя
- Перегрузка экрана

**Причина:**
Validation engine не исправил все перекрытия или они допустимы для sequential_cascade эффектов.

**Как исправить:**
Улучшить логику в `validation_engine.py` для устранения перекрытий.

---

## ⚠️ НЕКРИТИЧЕСКИЕ ПРОБЛЕМЫ (2)

### 4. ⚠️ **Отсутствует total_slides в presentation_context**

**Проблема:**
```json
{
  "presentation_context": {
    "theme": "...",
    "total_slides": null  // ❌ Должно быть 2
  }
}
```

**Как исправить:**
В `presentation_intelligence.py` убедиться что поле `total_slides` заполняется.

---

### 5. ⚠️ **Дополнительное поле metadata**

**Проблема:**
```json
{
  "slides": [...],
  "metadata": {...},  // ⚠️ Не в спецификации
  "presentation_context": {...},
  "timeline": [...]
}
```

**Примечание:**
Не критично, но может быть лишним. Проверить нужен ли этот ключ.

---

## ✅ ЧТО РАБОТАЕТ ПРАВИЛЬНО (9)

### Структура данных:
1. ✅ Все обязательные поля присутствуют (id, image, elements, audio, duration, cues)
2. ✅ BBox координаты валидны (нет отрицательных значений, корректные размеры)
3. ✅ Временные метки на слайде 1 без перекрытий
4. ✅ Временные метки не выходят за duration аудио
5. ✅ Все ссылки cues → elements валидны

### Semantic анализ:
6. ✅ Semantic map создан (5 групп на слайде 1, 4 на слайде 2)
7. ✅ Highlight strategies определены для всех групп
8. ✅ Talk track создан (6 сегментов на каждый слайд)

### Audio:
9. ✅ Аудио файлы существуют и имеют правильную длительность

---

## 📊 СВОДНАЯ ТАБЛИЦА

| # | Проблема | Серьёзность | Слайды | Исправление |
|---|----------|-------------|--------|-------------|
| 1 | Неправильные element IDs | 🔴 Критическая | 2 | Исправить OCR provider |
| 2 | Нет group_id в cues | 🟡 Средняя | 1, 2 | Перезапустить с новым кодом |
| 3 | Перекрытия временных меток | 🟡 Средняя | 2 | Улучшить validation |
| 4 | Нет total_slides | 🟢 Низкая | - | Заполнить поле |
| 5 | Лишний ключ metadata | 🟢 Низкая | - | Убрать или оставить |

---

## 🔧 ПЛАН ИСПРАВЛЕНИЙ

### Приоритет 1 (критично):

#### 1. Исправить генерацию element IDs для слайдов
```python
# Найти код который генерирует ID
# Убедиться что используется правильный slide_index

# Должно быть:
element_id = f"slide_{slide_index + 1}_block_{block_index}"

# Проверить в:
# - backend/workers/ocr_vision.py
# - backend/workers/ocr_google.py
# - backend/app/services/provider_factory.py
```

#### 2. Перезапустить обработку презентации
```bash
# После исправления кода:
docker-compose restart backend

# Загрузить презентацию заново
# Проверить что element IDs правильные
```

### Приоритет 2 (важно):

#### 3. Проверить group_id добавлен в новых манифестах
```bash
# Загрузить новую презентацию
# Проверить cues:
python3 -c "
import json
with open('.data/{new_uuid}/manifest.json') as f:
    m = json.load(f)
    has_group_id = 'group_id' in m['slides'][0]['cues'][0]
    print(f'Has group_id: {has_group_id}')
"
```

#### 4. Добавить валидацию перекрытий
```python
# В validation_engine.py:

def fix_overlapping_cues(cues):
    sorted_cues = sorted(cues, key=lambda c: c['t0'])
    for i in range(len(sorted_cues) - 1):
        if sorted_cues[i]['t1'] > sorted_cues[i+1]['t0']:
            # Уменьшить t1 первого cue
            sorted_cues[i]['t1'] = sorted_cues[i+1]['t0'] - 0.1
```

### Приоритет 3 (желательно):

#### 5. Заполнить total_slides
```python
# В presentation_intelligence.py:
context['total_slides'] = len(slides)
```

---

## 🧪 КАК ПРОВЕРИТЬ

### Тест 1: Проверка element IDs
```python
import json
with open('.data/{uuid}/manifest.json') as f:
    m = json.load(f)
    for slide in m['slides']:
        slide_id = slide['id']
        for elem in slide['elements']:
            elem_id = elem['id']
            expected_prefix = f'slide_{slide_id}_'
            if not elem_id.startswith(expected_prefix):
                print(f'❌ ОШИБКА: {elem_id} на слайде {slide_id}')
```

### Тест 2: Проверка group_id
```python
import json
with open('.data/{uuid}/manifest.json') as f:
    m = json.load(f)
    for slide in m['slides']:
        cues = slide.get('cues', [])
        has_group_id = any('group_id' in c and c['group_id'] for c in cues)
        print(f'Slide {slide["id"]}: group_id = {has_group_id}')
```

### Тест 3: Проверка перекрытий
```python
import json
with open('.data/{uuid}/manifest.json') as f:
    m = json.load(f)
    for slide in m['slides']:
        cues = sorted(slide.get('cues', []), key=lambda c: c['t0'])
        overlaps = 0
        for i in range(len(cues) - 1):
            if cues[i]['t1'] > cues[i+1]['t0']:
                overlaps += 1
        print(f'Slide {slide["id"]}: {overlaps} перекрытий')
```

---

## 📝 ВЫВОДЫ

### Критический баг:
**Element IDs на слайде 2 имеют неправильный префикс** - это нужно исправить в OCR provider или парсере.

### Проблемы после исправлений:
Наши исправления (`group_id` в cues, SSML сохранение) **не применились** к этому манифесту, потому что он был создан **до** наших изменений.

### Следующие шаги:
1. ✅ Исправить генерацию element IDs
2. ✅ Перезапустить обработку презентации
3. ✅ Проверить что новый манифест не содержит этих ошибок
4. ✅ Убедиться что `group_id`, `speaker_notes_ssml` и `tts_words_sample` присутствуют

---

**Создан:** 2025-01-XX  
**Автор:** Droid AI
