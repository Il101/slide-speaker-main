# Где генерируется текст talk_track

## 🎯 Ваш вопрос:
> "Сегодня мы начинаем изучение анатомии и гистологии листьев. Тема нашей лекции – Das Blatt, что в переводе с немецкого означает «лист»."

## 📍 Где это генерируется:

### 1. **Файл**: `backend/app/services/smart_script_generator.py`

### 2. **Метод**: `SmartScriptGenerator.generate_script()`

```python
async def generate_script(
    self,
    semantic_map: Dict[str, Any],      # Семантическая карта слайда
    ocr_elements: List[Dict[str, Any]],  # Текст со слайда
    presentation_context: Dict[str, Any],  # Контекст презентации
    ...
) -> Dict[str, Any]:
```

### 3. **Процесс генерации:**

```
Stage 3: Plan (в pipeline)
    ↓
SmartScriptGenerator.generate_script()
    ↓
_create_script_generation_prompt()  ← создаёт промпт для LLM
    ↓
LLM (Gemini) генерирует JSON:
{
  "talk_track": [
    {
      "text": "Сегодня мы начинаем изучение...",
      "group_id": "group_title",
      "segment": "introduction"
    },
    ...
  ]
}
    ↓
Сохраняется в manifest.json → slides[N].talk_track
```

---

## 📝 Что передается в LLM:

### **System Prompt** (строка 176-190):

```python
system_prompt = f"""You are an expert lecturer who creates engaging explanations without simply reading slides.

{lang_instruction}  # "Весь текст должен быть ТОЛЬКО на русском языке!"

🔴 КРИТИЧЕСКИ ВАЖНО - СТРОГО СЛЕДУЙ (БЕЗ ИСКЛЮЧЕНИЙ):
1. Говори ТОЛЬКО о том, что ЕСТЬ на слайде
2. НЕ добавляй дополнительную информацию из твоих знаний
3. НЕ упоминай темы, которых НЕТ на слайде
4. НЕ делай общих утверждений - только конкретика со слайда
5. Если на слайде список - говори про каждый пункт из списка
...
"""
```

### **User Prompt** (строка 409-500):

```python
def _create_script_generation_prompt(...):
    return f"""
PRESENTATION CONTEXT:
- Theme: {theme}
- Level: {level}
- Language: {language}
- Slide {slide_index + 1}/{total_slides}

SLIDE SEMANTIC GROUPS (в порядке важности):
{groups_text}  # Список групп: group_title, group_list_items, etc.

TASK:
Generate a lecture script that:
1. Explains ONLY what is shown on the slide
2. Does NOT add extra information from your knowledge
3. Covers each important group
4. Uses natural speech (not reading verbatim)
5. Wraps foreign terms in [lang:XX] markers

RETURN JSON:
{{
  "talk_track": [
    {{"text": "...", "group_id": "group_title", "segment": "introduction"}},
    ...
  ],
  "speaker_notes": "Brief summary...",
  "estimated_duration": 45
}}
"""
```

---

## ❌ **Проблема в вашем случае:**

**LLM добавляет информацию, которой НЕТ на слайде!**

### На слайде было:
```
Темы стажировки:
1 - микроскоп, растительная клетка
2 - ...
```

### LLM сгенерировал:
```
"Сегодня мы начинаем изучение анатомии и гистологии листьев. 
Тема нашей лекции – Das Blatt..."
```

Слов "анатомия", "гистология", "лекция" **НЕТ** на слайде!

---

## 🔧 **Как это контролировать:**

### Вариант 1: Усилить промпт (уже есть, но LLM игнорирует)

В `_create_script_generation_prompt()` добавить:

```python
⚠️ ABSOLUTE RULE - NO EXCEPTIONS:
- NEVER mention "anatomy", "histology", "lecture" unless they are EXPLICITLY on the slide
- NEVER say "Today we begin..." - just explain what is shown
- Start directly with the slide content: "На слайде показаны темы: ..."
- DO NOT add context, background, or introductions
```

### Вариант 2: Post-processing фильтр (надежнее)

После генерации проверять текст:

```python
# В generate_script(), после получения response от LLM:
forbidden_phrases = [
    "сегодня мы начинаем",
    "тема нашей лекции",
    "давайте рассмотрим",
    "в этой лекции"
]

for segment in script['talk_track']:
    text_lower = segment['text'].lower()
    if any(phrase in text_lower for phrase in forbidden_phrases):
        logger.warning(f"⚠️ LLM added forbidden phrase: {segment['text'][:50]}")
        # Regenerate or skip this segment
```

### Вариант 3: Few-shot examples (лучший результат)

Добавить в промпт примеры правильной генерации:

```python
FEW-SHOT EXAMPLES:

❌ BAD:
Slide: "Topics: 1. Cells 2. DNA 3. Proteins"
Generated: "Today we begin studying biology. The fundamental concepts are..."

✅ GOOD:
Slide: "Topics: 1. Cells 2. DNA 3. Proteins"  
Generated: "На слайде перечислены три темы: клетки, ДНК и белки. Первая тема - клетки..."

---

❌ BAD:
Slide: "Das Blatt - Anatomie"
Generated: "Сегодня мы изучаем анатомию листьев. Лист - важная часть растения..."

✅ GOOD:
Slide: "Das Blatt - Anatomie"
Generated: "На слайде заголовок: [visual:de]Das Blatt[/visual] - Anatomie. Это означает анатомию листа."
```

---

## 🎯 **Где изменить:**

### Файл: `backend/app/services/smart_script_generator.py`

**Строка 176** - `system_prompt` - общие инструкции

**Строка 409** - `_create_script_generation_prompt()` - конкретный промпт для слайда

**Строка 290** - После получения response - добавить валидацию

### Пример изменения:

```python
# В методе generate_script(), после строки 290:
if 'talk_track' in script:
    for segment in script['talk_track']:
        text = segment.get('text', '')
        
        # ✅ Проверяем что LLM не добавил лишнего
        forbidden_starts = [
            'сегодня мы начинаем',
            'тема нашей лекции',
            'в этой лекции',
            'давайте начнем с'
        ]
        
        text_lower = text.lower()
        for forbidden in forbidden_starts:
            if text_lower.startswith(forbidden):
                logger.warning(f"⚠️ LLM added forbidden intro: '{text[:50]}...'")
                # Можно удалить или заменить
                segment['text'] = text.split('. ', 1)[1] if '. ' in text else text
                break
```

---

## 💡 **Рекомендация:**

Самый надежный способ - **Few-shot examples** в промпте. LLM лучше учится на примерах, чем на правилах.

Добавьте в `_create_script_generation_prompt()` после строки 450:

```python
FEW-SHOT EXAMPLES OF CORRECT BEHAVIOR:
{few_shot_examples}
```

Где `few_shot_examples` содержит 3-5 примеров правильной генерации без добавления лишней информации.
