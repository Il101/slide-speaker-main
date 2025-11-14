# Adaptive Prompt System - Умная адаптивная генерация текста презентации

## Описание

Новая система адаптивной генерации промптов для LLM, которая автоматически подстраивает детализацию и инструкции под характеристики каждого слайда.

## Проблемы, которые решает

### Было (старая система):
❌ Универсальный промпт для всех слайдов  
❌ Включение до 8 групп без фильтрации  
❌ Игнорирование метрик плотности и сложности  
❌ Фиксированная длительность 30-60 секунд  
❌ Неуместные объяснения (слишком подробные или краткие)

### Стало (новая система):
✅ Адаптивные инструкции для каждого типа слайда  
✅ Интеллектуальная фильтрация и ранжирование групп  
✅ Учёт visual_density и cognitive_load  
✅ Динамическая длительность (20-70 секунд)  
✅ Контекстно-зависимые объяснения

## Архитектура

### 1. AdaptivePromptBuilder (`backend/app/services/adaptive_prompt_builder.py`)

Новый класс для построения адаптивных промптов.

**Основные методы:**

- `build_adaptive_groups_section()` - фильтрует и форматирует группы
- `generate_adaptive_instructions()` - создаёт контекстные инструкции
- `_calculate_group_importance()` - ранжирует группы по важности
- `_assign_explanation_depth()` - определяет уровень детализации
- `_calculate_optimal_duration()` - рассчитывает оптимальную длительность

### 2. Интеграция в SmartScriptGenerator

Обновлённый `_create_script_generation_prompt()` использует AdaptivePromptBuilder:

```python
# Умная фильтрация групп
groups_text, filtered_groups, optimal_duration = self.prompt_builder.build_adaptive_groups_section(
    semantic_map, ocr_elements, max_groups=None
)

# Адаптивные инструкции
adaptive_instructions = self.prompt_builder.generate_adaptive_instructions(
    semantic_map, content_strategy, len(filtered_groups)
)

# Подсказка по длительности
duration_hint = self.prompt_builder.build_duration_hint(optimal_duration, visual_density)
```

## Как работает адаптация

### 1. Фильтрация групп по плотности

```python
visual_density = "high"  # Плотный слайд
max_groups = 4  # Только топ-4 группы

visual_density = "low"   # Простой слайд
max_groups = 10  # Можно больше деталей
```

### 2. Ранжирование по важности

Факторы важности группы:
- **Priority** (high/medium/low/none) → вес 10.0 / 5.0 / 2.0 / 0.0
- **Type** (title/heading/key_point) → вес 3.0 / 2.5 / 2.0
- **Educational intent** → бонус +2.0
- **Размер** (количество элементов) → до +2.0
- **Позиция** (reading_order) → до +2.0

### 3. Уровни детализации

Для каждой группы назначается depth:

- **DETAILED** - подробное объяснение с примерами
- **BRIEF** - краткое объяснение + 1 пример
- **MENTION** - только упомянуть ключевой момент
- **SKIP** - пропустить

Зависит от:
- Visual density (high → меньше DETAILED)
- Cognitive load (complex → больше DETAILED)
- Priority группы
- Позиция в списке

### 4. Адаптивные инструкции

#### High Density:
```
⚡ CRITICAL STRATEGY - HIGH DENSITY SLIDE:
This slide is PACKED with information - you MUST be CONCISE!
- Focus ONLY on the TOP priority groups marked above
- Aim for 20-30 seconds total (NO MORE!)
- Mention key terms but DON'T elaborate on everything
- Skip examples and analogies - get to the point
```

#### Low Density:
```
📖 STRATEGY - LOW DENSITY SLIDE:
This slide has limited information - you can ELABORATE more:
- Take 40-60 seconds
- Add examples and real-world analogies
- Explain WHY concepts matter
- Provide context and connections
```

#### Complex Cognitive Load:
```
🧠 COMPLEXITY HANDLING:
This content is COMPLEX - help students understand:
- Break down concepts step-by-step
- Use simpler language and analogies
- Explain the "why" before the "what"
- Slow down speaking rate [rate:90%] for key definitions
```

### 5. Динамическая длительность

```python
base = количество_групп * 10  # 10 секунд на группу

# Корректировки:
if visual_density == "high":
    duration *= 0.7  # -30% для плотных слайдов
elif visual_density == "low":
    duration *= 1.3  # +30% для простых слайдов

if cognitive_load == "complex":
    duration *= 1.3  # +30% для сложного контента

# Минимумы:
min_duration = {
    "high": 20,
    "medium": 25,
    "low": 30
}
```

## Примеры работы

### Пример 1: Плотный слайд с формулами

**Вход:**
- visual_density: "high"
- cognitive_load: "medium"
- 5 групп (title, 2 formulas, 2 examples)

**Результат:**
- Отфильтровано: 4 группы (убран footer)
- Depth: [DETAILED, BRIEF, MENTION, MENTION]
- Duration: 28 секунд
- Инструкция: "CONCISE! 20-30 seconds MAX"

### Пример 2: Простой title slide

**Вход:**
- visual_density: "low"
- cognitive_load: "easy"
- 2 группы (title, subtitle)

**Результат:**
- Отфильтровано: 2 группы
- Depth: [DETAILED, DETAILED]
- Duration: 30 секунд
- Инструкция: "ELABORATE - take 40-60 seconds"

### Пример 3: Сложная диаграмма

**Вход:**
- visual_density: "medium"
- cognitive_load: "complex"
- content_type: "diagram"

**Результат:**
- Duration: 25+ секунд
- Инструкции: 
  - "Break down step-by-step"
  - "Start with big picture"
  - "Explain relationships"

## Тестирование

Запуск тестов:

```bash
# Unit тесты
python3 test_adaptive_prompt.py

# Интеграционные тесты
python3 test_integration_adaptive.py
```

**Покрытие тестов:**
- ✅ Фильтрация групп по плотности
- ✅ Ранжирование по важности
- ✅ Назначение уровней детализации
- ✅ Расчёт длительности
- ✅ Генерация адаптивных инструкций
- ✅ Интеграция со SmartScriptGenerator

## Влияние на качество

### Ожидаемые улучшения:

1. **Для плотных слайдов:**
   - Более лаконичные объяснения
   - Фокус на ключевых концептах
   - Меньше "воды"

2. **Для простых слайдов:**
   - Более подробные объяснения
   - Больше примеров и контекста
   - Увлекательная подача

3. **Для сложного контента:**
   - Пошаговые объяснения
   - Простой язык
   - Больше времени на понимание

4. **Для диаграмм:**
   - Структурированное описание
   - Пространственная навигация
   - Объяснение связей

## Конфигурация

Параметры можно настроить в `AdaptivePromptBuilder.__init__()`:

```python
# Веса приоритетов
PRIORITY_WEIGHTS = {
    'high': 10.0,
    'medium': 5.0,
    'low': 2.0,
    'none': 0.0
}

# Веса типов групп
TYPE_WEIGHTS = {
    'title': 3.0,
    'heading': 2.5,
    'key_point': 2.0,
    'example': 1.5,
    ...
}
```

## Обратная совместимость

✅ Старый код продолжит работать  
✅ Новая система автоматически активируется  
✅ Mock mode работает как раньше  
✅ Все существующие тесты проходят

## Файлы изменений

### Новые файлы:
- `backend/app/services/adaptive_prompt_builder.py` (520 строк)
- `test_adaptive_prompt.py` (260 строк)
- `test_integration_adaptive.py` (235 строк)
- `ADAPTIVE_PROMPT_SYSTEM.md` (эта документация)

### Изменённые файлы:
- `backend/app/services/smart_script_generator.py`
  - Добавлен импорт AdaptivePromptBuilder
  - Обновлён метод `_create_script_generation_prompt`
  - Добавлена гибридная оценка длительности

## Следующие шаги

1. ✅ Реализация базовой системы
2. ✅ Unit и интеграционные тесты
3. 📝 Тестирование с реальным LLM
4. 📊 Сбор метрик качества
5. 🔧 Тонкая настройка весов и параметров
6. 📈 A/B тестирование со старой системой

## Авторы

Разработано для улучшения качества генерации текста презентаций в Slide Speaker.

Дата: 2024
