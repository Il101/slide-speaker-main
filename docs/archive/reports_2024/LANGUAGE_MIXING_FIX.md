# Исправление смешения языков в TTS

## Проблема

LLM генерировал текст со смешением языков, например:
```
"На слайде представлено название курса – «Aufbau und Architektur der Pflanzen», 
что в переводе означает «Строение и архитектура растений»"
```

Это создавало проблемы для TTS, которая не может корректно озвучить текст с иностранными словами.

## Корневая причина

Хотя в пайплайне есть **Translation Service** (этап 2.5), который переводит элементы:
- `text_original` - оригинальный текст (немецкий, английский)
- `text_translated` - переведённый текст (русский)

**Проблема**: В нескольких местах код использовал просто `text` вместо `text_translated`, 
поэтому LLM получал оригинальный текст и пытался его объяснить.

## Решение

### 1. Архитектура пайплайна

```
extract() → Translation Service → plan() → LLM генерация
                ↓
         text_translated
                ↓
         LLM видит ТОЛЬКО переведённый текст
```

### 2. Исправленные файлы

#### `adaptive_prompt_builder.py` (строка 365)
```python
# БЫЛО:
text = elements_by_id[elem_id].get('text', '').strip()

# СТАЛО:
elem = elements_by_id[elem_id]
text = (elem.get('text_translated') or elem.get('text', '')).strip()
```

#### `smart_script_generator.py`
- Усилены инструкции против смешения языков в system prompt
- Добавлены яркие примеры ПРАВИЛЬНОГО и НЕПРАВИЛЬНОГО подхода
- Добавлена секция "🔥 КРИТИЧЕСКИЕ ПРИМЕРЫ ДЛЯ TTS"

```python
🚨 АБСОЛЮТНО ЗАПРЕЩЕНО СМЕШИВАТЬ ЯЗЫКИ:
   ❌ НИКОГДА не используй конструкции типа "X, что в переводе означает Y"
   ✅ Текст в "Text on slide" уже переведён - используй его напрямую
```

#### `intelligent_optimized.py` (строка 637)
```python
# БЫЛО:
texts = [e.get('text', '')[:50] for e in elements[:3]]

# СТАЛО:
texts = [(e.get('text_translated') or e.get('text', ''))[:50] for e in elements[:3]]
```

#### `visual_effects_engine.py` (строки 441, 1601)
```python
# БЫЛО:
elem_text = elem.get('text', '').strip()

# СТАЛО:
elem_text = (elem.get('text_translated') or elem.get('text', '')).strip()
```

#### `semantic_analyzer.py` (строка 372)
```python
# БЫЛО:
text = el.get('text', '')[:100]

# СТАЛО:
text = (el.get('text_translated') or el.get('text', ''))[:100]
```

#### `presentation_intelligence.py` (строка 96)
```python
# БЫЛО:
if element.get('text'):
    texts.append(element['text'][:100])

# СТАЛО:
text = element.get('text_translated') or element.get('text')
if text:
    texts.append(text[:100])
```

#### `semantic_analyzer.py` (строка 75-86) - КРИТИЧНОЕ ИЗМЕНЕНИЕ
```python
# БЫЛО:
system_prompt = "You are an expert at analyzing presentation slides..."

# СТАЛО:
source_lang = ocr_elements[0].get('language_original', 'unknown')
target_lang = ocr_elements[0].get('language_target', 'ru')

system_prompt = f"""...
IMPORTANT - LANGUAGE HANDLING:
- The slide IMAGE contains text in {source_lang}
- The OCR data below is TRANSLATED to {target_lang}
- Use the TRANSLATED text ({target_lang}) for all your analysis
- The image is provided for VISUAL context only
- DO NOT extract text from the image - use translated OCR data
"""
```

**Почему это важно**: SemanticAnalyzer передаёт в Gemini Vision API:
1. Изображение слайда (с оригинальным текстом)
2. OCR данные (с переведённым текстом)

Без явных инструкций Gemini могла путаться между двумя языками.

## Результат

Теперь LLM генерирует **ТОЛЬКО** чистый русский текст:

✅ **ДО**: "На слайде представлено название курса – «Aufbau und Architektur der Pflanzen», что в переводе означает «Строение и архитектура растений»"

✅ **ПОСЛЕ**: "На слайде название курса: Строение и архитектура растений"

## Как это работает

1. **Этап extract()**: Translation Service переводит все элементы
   - Сохраняет `text_original` и `text_translated`
   - Сохраняет `language_original` и `language_target`
   
2. **Этап plan()**: Все компоненты используют `text_translated`:
   - AdaptivePromptBuilder → передаёт переведённый текст в промпт
   - SmartScriptGenerator → получает только переведённый текст
   - SemanticAnalyzer → анализирует переведённый текст
   - VisualEffectsEngine → ищет элементы по переведённому тексту

3. **Особенность SemanticAnalyzer** (Gemini Vision):
   - Получает **ИЗОБРАЖЕНИЕ** слайда (с оригинальным текстом)
   - Получает **OCR данные** (с переведённым текстом)
   - В system prompt явно указано:
     ```
     - The slide IMAGE contains text in {source_lang}
     - The OCR data is TRANSLATED to {target_lang}
     - Use TRANSLATED text for all analysis
     - Image is for VISUAL context only (layout, diagrams)
     ```

4. **LLM генерация**: LLM видит только переведённый текст, не знает об оригинале

5. **TTS**: Получает чистый русский текст без иностранных слов

## Тестирование

После этих изменений попробуйте загрузить немецкую/английскую презентацию:
- TTS должен говорить **только** на русском
- Никаких конструкций "что в переводе означает"
- Никаких иностранных слов в речи
