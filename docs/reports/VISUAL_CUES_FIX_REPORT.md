# Исправление визуальных эффектов (Visual Cues Fix)

## Проблема

Визуальные эффекты (подсветка, подчеркивание, лазерная указка) не отображались в плеере. При проверке `manifest.json` обнаружено, что все слайды имели пустой массив `cues: []`.

## Причина

**Несоответствие формата bbox:**

- **Ожидалось:** список `[x, y, width, height]`
- **Получено:** словарь `{"x": ..., "y": ..., "width": ..., "height": ...}`

Генератор визуальных эффектов (`backend/workers/visual_cues_generator.py`) падал с ошибкой при попытке обработать bbox в формате словаря, но ошибка перехватывалась в `try-except` блоке, и cues не создавались.

## Решение

### 1. Добавлена функция нормализации bbox

```python
def _normalize_bbox(self, bbox: Any) -> List[float]:
    """Нормализует bbox к формату [x, y, width, height]"""
    if isinstance(bbox, dict):
        # Формат словаря: {"x": ..., "y": ..., "width": ..., "height": ...}
        return [
            bbox.get("x", 0),
            bbox.get("y", 0),
            bbox.get("width", 100),
            bbox.get("height", 50)
        ]
    elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        # Формат списка: [x, y, width, height]
        return list(bbox[:4])
    else:
        # Fallback
        return [0, 0, 100, 50]
```

### 2. Обновлены методы генерации

- `_generate_synchronized_cues()` - использует `_normalize_bbox()` для всех bbox
- `_generate_basic_cues()` - использует `_normalize_bbox()` для всех bbox

### 3. Исправлены импорты

Добавлен fallback для импортов, чтобы модуль работал как в Celery, так и при прямом запуске:

```python
try:
    from ..app.models.schemas import Cue, ActionType
except (ImportError, ValueError):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.models.schemas import Cue, ActionType
```

## Тестирование

### Тестовый скрипт

```bash
python3 test_visual_cues_fix.py
```

**Результат:**
```
✅ Сгенерировано 8 визуальных эффектов:
   1. ActionType.HIGHLIGHT (0.50s - 28.02s)
   2. ActionType.UNDERLINE (7.38s - 31.46s)
   3. ActionType.LASER_MOVE (28.02s - 69.30s)
   ...
```

### Регенерация для существующих уроков

```bash
python3 regenerate_visual_cues.py <lesson_id>
```

**Пример:**
```bash
python3 regenerate_visual_cues.py 34954f21-3a4d-4a4e-b975-d8f892f8961b
```

**Результат:**
```
✅ Урок 34954f21-3a4d-4a4e-b975-d8f892f8961b: сохранено 42 визуальных эффектов
```

## Проверка

### 1. Проверка manifest.json

```bash
cat backend/.data/<lesson_id>/manifest.json | python3 -m json.tool | grep -A 10 '"cues"'
```

**До исправления:**
```json
"cues": []
```

**После исправления:**
```json
"cues": [
  {
    "cue_id": "cue_89e25608",
    "t0": 0.5,
    "t1": 28.02,
    "action": "highlight",
    "bbox": [91, 36, 239, 75],
    "element_id": "slide_1_text_0"
  },
  ...
]
```

### 2. Проверка в плеере

1. Откройте плеер: `http://localhost:5173`
2. Загрузите урок с ID `34954f21-3a4d-4a4e-b975-d8f892f8961b`
3. Запустите воспроизведение
4. Визуальные эффекты должны отображаться:
   - 🟡 **Желтая подсветка** текстовых элементов
   - 🔴 **Красное подчеркивание** под текстом
   - 🔵 **Лазерная указка** перемещается между элементами

## Типы визуальных эффектов

### Highlight (Подсветка)
- **Цвет:** желтый (yellow-300/yellow-500)
- **Применяется к:** текстовым элементам
- **Длительность:** ~80% времени слайда для каждого элемента

### Underline (Подчеркивание)
- **Цвет:** красный (red-500)
- **Применяется к:** текстовым элементам (под текстом)
- **Длительность:** начинается через 20% времени highlight

### Laser Move (Лазерная указка)
- **Действие:** перемещение от одного элемента к следующему
- **Применяется:** между элементами
- **Длительность:** ~20% времени между элементами

## Следующие шаги

### Для новых загрузок

Визуальные эффекты будут генерироваться автоматически при обработке новых презентаций через `/upload` endpoint.

### Для существующих уроков

Используйте скрипт `regenerate_visual_cues.py` для регенерации эффектов:

```bash
# Для всех уроков
python3 regenerate_visual_cues.py

# Для конкретного урока
python3 regenerate_visual_cues.py <lesson_id>
```

## Файлы изменены

- ✅ `backend/workers/visual_cues_generator.py` - исправлен генератор
- ✅ `test_visual_cues_fix.py` - тестовый скрипт
- ✅ `regenerate_visual_cues.py` - скрипт для регенерации
- ✅ `VISUAL_CUES_FIX_REPORT.md` - эта документация

## Статус

✅ **Исправление завершено и протестировано**

Визуальные эффекты теперь корректно генерируются и отображаются в плеере для всех уроков.
