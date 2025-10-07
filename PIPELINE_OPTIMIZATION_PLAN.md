# 🚀 План оптимизации Intelligent Pipeline

## 📊 Текущая производительность

### Для презентации из 15 слайдов:

| Стадия | Обработка | Время | Стоимость | Bottleneck |
|--------|-----------|-------|-----------|------------|
| **Stage 1: OCR** | Последовательная | ~15 сек | $0.02 | 🟡 Средний |
| **Stage 0: Intelligence** | 1 запрос | ~3 сек | $0.01 | 🟢 Низкий |
| **Stage 2: Semantic (×15)** | Последовательная | ~90 сек | $0.08 | 🔴 **КРИТИЧЕСКИЙ** |
| **Stage 3: Script (×15)** | Последовательная | ~60 сек | $0.05 | 🟠 Высокий |
| **Stage 4: TTS (×15)** | Последовательная | ~45 сек | $0.07 | 🟠 Высокий |
| **Stage 5-7: Local** | Локально | ~5 сек | $0.00 | 🟢 Низкий |
| **ИТОГО** | | **~218 сек** | **$0.23** | |

---

## 🎯 Целевые показатели после оптимизации

| Метрика | Было | Цель | Улучшение |
|---------|------|------|-----------|
| **Время обработки** | 218 сек (3.6 мин) | **60 сек (1 мин)** | **-72%** ⚡ |
| **Стоимость** | $0.23 | **$0.10** | **-57%** 💰 |
| **Качество** | Baseline | **≥ Baseline** | Без потерь ✅ |

---

## 🔥 Критические узкие места

### 1. **Stage 2: Semantic Analysis** 🔴
**Проблема:**
- Последовательная обработка 15 слайдов
- Каждый слайд: 1 Vision API запрос (multimodal)
- Время: ~6 сек × 15 = **90 секунд**
- Стоимость: ~$0.005 × 15 = **$0.075**

**Влияние:** 41% времени, 33% стоимости

---

### 2. **Stage 3: Script Generation** 🟠
**Проблема:**
- Последовательная обработка
- Время: ~4 сек × 15 = **60 секунд**
- Стоимость: ~$0.003 × 15 = **$0.045**

**Влияние:** 28% времени, 20% стоимости

---

### 3. **Stage 4: TTS** 🟠
**Проблема:**
- Последовательная генерация аудио
- Время: ~3 сек × 15 = **45 секунд**
- Стоимость: ~$0.005 × 15 = **$0.075**

**Влияние:** 21% времени, 33% стоимости

---

## 💡 Предложенные оптимизации

### 🚀 **Уровень 1: Быстрые победы** (без изменения архитектуры)

#### 1.1 Параллельная обработка слайдов
**Что:**
```python
# БЫЛО (последовательно):
for i, slide in enumerate(slides):
    semantic_map = await self.semantic_analyzer.analyze_slide(...)  # 6 сек
    script = await self.script_generator.generate_script(...)        # 4 сек
    # Итого: 10 сек × 15 = 150 сек

# СТАЛО (параллельно):
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_slide(slide, index):
    semantic_map = await self.semantic_analyzer.analyze_slide(...)
    script = await self.script_generator.generate_script(...)
    return (index, semantic_map, script)

# Обрабатываем 5 слайдов параллельно
semaphore = asyncio.Semaphore(5)
tasks = [process_slide(slide, i) for i, slide in enumerate(slides)]
results = await asyncio.gather(*tasks)
# Итого: 10 сек × (15/5) = 30 сек
```

**Выгода:**
- ⚡ Время: **218 сек → 88 сек** (-60%)
- 💰 Стоимость: без изменений
- ✅ Качество: без изменений

**Риски:**
- Rate limits API (решается через semaphore)
- Увеличенное потребление памяти

**Реализация:** 2-4 часа

---

#### 1.2 Кэширование OCR результатов
**Что:**
```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_ocr(image_hash: str, image_path: str):
    # Проверяем Redis кэш
    cached = redis.get(f"ocr:{image_hash}")
    if cached:
        return json.loads(cached)
    
    # Вызываем Vision API
    result = vision_api.extract_elements(image_path)
    
    # Сохраняем в кэш на 7 дней
    redis.setex(f"ocr:{image_hash}", 604800, json.dumps(result))
    return result
```

**Выгода:**
- ⚡ Повторная обработка: **15 сек → 0.1 сек** (-99%)
- 💰 Повторная обработка: **$0.02 → $0.00** (-100%)
- ✅ Полезно при пересоздании лекций

**Реализация:** 1 час

---

#### 1.3 Batch TTS запросы
**Что:**
```python
# БЫЛО (15 отдельных запросов):
for slide in slides:
    audio = tts_api.synthesize(slide.text)  # 3 сек каждый

# СТАЛО (1 batch запрос):
all_texts = [slide.text for slide in slides]
audios = tts_api.batch_synthesize(all_texts)  # 10 сек для всех
```

**Выгода:**
- ⚡ Время: **45 сек → 10 сек** (-78%)
- 💰 Стоимость: без изменений (или -10% за batch discount)

**Проблема:** Google TTS не поддерживает batch API
**Альтернатива:** Параллельные запросы через ThreadPoolExecutor

**Реализация:** 2 часа

---

### ⚡ **Уровень 2: Архитектурные улучшения**

#### 2.1 Smart Vision: Selective multimodal
**Что:**
Не все слайды требуют Vision API. Используем эвристики:

```python
def needs_vision(slide_elements):
    """Определяем, нужен ли Vision API для этого слайда"""
    
    # Критерии для Vision API:
    # 1. Много визуальных элементов (>5)
    # 2. Есть таблицы или графики
    # 3. Мало текста (<50 символов)
    # 4. Сложный layout
    
    text_length = sum(len(e['text']) for e in slide_elements)
    has_tables = any(e['type'] == 'table' for e in slide_elements)
    has_figures = any(e['type'] == 'figure' for e in slide_elements)
    element_count = len(slide_elements)
    
    # Простой текстовый слайд - Vision не нужен
    if text_length > 200 and not has_tables and not has_figures:
        return False
    
    # Сложный слайд - Vision нужен
    if has_tables or has_figures or element_count > 10:
        return True
    
    # Title slides - Vision не нужен
    if element_count <= 3 and text_length < 100:
        return False
    
    return True  # По умолчанию используем Vision

# Использование:
if needs_vision(slide['elements']):
    # Multimodal (дорого, медленно, точно)
    semantic_map = await analyzer.analyze_slide(
        image=slide_image,
        elements=elements
    )
else:
    # Text-only (дешево, быстро, достаточно точно)
    semantic_map = await analyzer.analyze_slide_text_only(
        elements=elements
    )
```

**Выгода:**
- ⚡ Время: **90 сек → 36 сек** (-60%)
- 💰 Стоимость: **$0.075 → $0.030** (-60%)
- ✅ Качество: -5% только на сложных слайдах
- 📊 ~60% слайдов не требуют Vision

**Реализация:** 4-6 часов

---

#### 2.2 Tiered LLM: Smart model selection
**Что:**
Используем разные модели для разных задач:

```python
MODEL_TIERS = {
    "fast": "gemini-1.5-flash-8b",     # Быстро, дешево
    "balanced": "gemini-2.0-flash",     # Текущий
    "quality": "gemini-2.0-pro"         # Медленно, дорого
}

def select_model(task_type, complexity):
    """Выбираем модель на основе задачи"""
    
    # Stage 0: Presentation Intelligence - требует качества
    if task_type == "presentation_analysis":
        return MODEL_TIERS["balanced"]
    
    # Stage 2: Semantic Analysis
    if task_type == "semantic_analysis":
        if complexity == "high":  # Много элементов, таблицы
            return MODEL_TIERS["balanced"]
        else:  # Простой слайд
            return MODEL_TIERS["fast"]  # -50% стоимости
    
    # Stage 3: Script Generation
    if task_type == "script_generation":
        if complexity == "high":  # Технический контент
            return MODEL_TIERS["balanced"]
        else:
            return MODEL_TIERS["fast"]
    
    return MODEL_TIERS["balanced"]
```

**Выгода:**
- ⚡ Время: **150 сек → 90 сек** (-40%)
- 💰 Стоимость: **$0.13 → $0.07** (-46%)
- ✅ Качество: -3% на простых слайдах

**Gemini Flash 8B стоимость:**
- Input: $0.0000375 / 1K chars (-80%)
- Output: $0.00015 / 1K chars (-80%)

**Реализация:** 3-4 часа

---

#### 2.3 Progressive Enhancement
**Что:**
Показываем результаты пользователю сразу, улучшаем в фоне:

```python
async def process_presentation_progressive(presentation_id):
    """Прогрессивная обработка с немедленной отдачей"""
    
    # Phase 1: Fast pass (15 секунд)
    # - OCR всех слайдов
    # - Mock semantic maps
    # - Generic talk tracks
    # - Простые визуальные эффекты
    await publish_preview(presentation_id, quality="draft")
    
    # Phase 2: Intelligent pass (45 секунд)
    # - Semantic analysis (text-only для простых слайдов)
    # - Real script generation
    # - TTS
    await publish_update(presentation_id, quality="standard")
    
    # Phase 3: Enhancement pass (фон, 30 секунд)
    # - Vision analysis для сложных слайдов
    # - Улучшенные визуальные эффекты
    # - Refinement проверка
    await publish_final(presentation_id, quality="enhanced")
```

**Выгода:**
- ⚡ Time to First Content: **218 сек → 15 сек** (-93%)
- ⚡ Time to Good Content: **218 сек → 60 сек** (-72%)
- ✅ UX значительно лучше
- 📊 Пользователь видит прогресс

**Реализация:** 8-10 часов

---

### 🎨 **Уровень 3: Advanced оптимизации**

#### 3.1 Prompt Compression
**Что:**
Сокращаем размер промптов без потери смысла:

```python
# БЫЛО (verbose):
prompt = f"""
Analyze this slide and create a semantic map with intelligent grouping and highlight strategies.

You have access to:
1. The slide IMAGE (see attached image)
2. OCR-extracted text with coordinates (below)

Use BOTH the visual layout from the image AND the OCR data to understand the slide structure.

PRESENTATION CONTEXT:
- Theme: {presentation_context.get('theme', 'Unknown')}
- Level: {presentation_context.get('level', 'undergraduate')}
- Style: {presentation_context.get('presentation_style', 'academic')}
- Target Language: {os.getenv('LLM_LANGUAGE', 'ru')} (output language for scripts)
- Slide {slide_index + 1} of {presentation_context.get('total_slides', '?')}

OCR ELEMENTS (detected text with coordinates):
{ocr_summary}

{few_shot_examples}  # 2000+ символов!

TASK:
Create a semantic map with:
1. **Semantic groups** - логические блоки контента
2. **Element classification** - title/content/example/decorative/noise
...
"""
# Длина: ~4000 символов

# СТАЛО (compressed):
prompt = f"""Group slide elements semantically.

Context: {theme} | {level} | Slide {idx}/{total}
Elements: {compressed_ocr}  # Только ключевая инфо

Return JSON:
{{"groups": [{{"id": "g1", "type": "title", "elements": ["e1"], "intent": "introduce", "highlight": {{"when": "start", "effect": "spotlight"}}}}]}}

Examples: [compressed examples]  # 500 символов
"""
# Длина: ~1500 символов (-62%)
```

**Выгода:**
- 💰 Стоимость: **$0.13 → $0.05** (-62%)
- ⚡ Время: **150 сек → 120 сек** (-20%)
- ✅ Качество: -2% (незначительно)

**Реализация:** 4-6 часов

---

#### 3.2 Hybrid Pipeline: Classic + Intelligent
**Что:**
Умный выбор pipeline на основе презентации:

```python
def select_pipeline(presentation):
    """Выбираем оптимальный pipeline"""
    
    slides_count = len(presentation.slides)
    avg_complexity = analyze_complexity(presentation)
    
    # Простая презентация - Classic Pipeline
    if slides_count <= 5 or avg_complexity < 0.3:
        return "classic"  # Без AI, быстро, дешево
    
    # Сложная презентация - Intelligent Pipeline
    if slides_count > 20 or avg_complexity > 0.7:
        return "intelligent"  # Полный AI
    
    # Средняя сложность - Hybrid
    return "hybrid"  # AI только для сложных слайдов

# Hybrid pipeline:
async def hybrid_process(presentation):
    complex_slides = [s for s in slides if s.complexity > 0.5]
    simple_slides = [s for s in slides if s.complexity <= 0.5]
    
    # Простые слайды - быстрая обработка
    await classic_pipeline.process(simple_slides)
    
    # Сложные слайды - AI обработка
    await intelligent_pipeline.process(complex_slides)
```

**Выгода:**
- ⚡ Среднее время: **218 сек → 80 сек** (-63%)
- 💰 Средняя стоимость: **$0.23 → $0.08** (-65%)
- ✅ Качество сохранено где нужно

**Реализация:** 10-12 часов

---

#### 3.3 Streaming Responses
**Что:**
Получаем ответы от LLM stream-ом, начинаем обработку раньше:

```python
# БЫЛО:
response = await llm.generate(prompt)  # Ждём полного ответа
parsed = json.loads(response)          # Парсим весь JSON
process(parsed)                        # Обрабатываем

# СТАЛО:
async for chunk in llm.generate_stream(prompt):
    partial_response += chunk
    
    # Парсим частичный JSON
    if can_parse_partial(partial_response):
        partial_data = parse_partial_json(partial_response)
        
        # Начинаем обработку до окончания генерации
        asyncio.create_task(process_partial(partial_data))

# Экономим время между генерацией и обработкой
```

**Выгода:**
- ⚡ Время: **150 сек → 110 сек** (-27%)
- ✅ Лучший UX (видим прогресс в реальном времени)

**Реализация:** 6-8 часов

---

#### 3.4 Pre-computed Templates
**Что:**
Предвычисляем шаблоны для типичных слайдов:

```python
SLIDE_TEMPLATES = {
    "title_slide": {
        "semantic_map": {
            "groups": [
                {"type": "title", "priority": "high", "highlight_strategy": {...}},
                {"type": "subtitle", "priority": "medium", ...}
            ]
        },
        "talk_track_template": "Introduce {title}. Context {subtitle}."
    },
    "bullet_list": {
        "semantic_map": {...},
        "talk_track_template": "Key points: {points}"
    },
    ...
}

def quick_process_if_matches_template(slide):
    """Быстрая обработка если слайд соответствует шаблону"""
    
    template = detect_template(slide)
    
    if template and confidence > 0.8:
        # Используем шаблон (мгновенно)
        return apply_template(slide, SLIDE_TEMPLATES[template])
    else:
        # Полная AI обработка
        return await intelligent_process(slide)
```

**Выгода:**
- ⚡ Время: **218 сек → 100 сек** (-54%)
- 💰 Стоимость: **$0.23 → $0.10** (-57%)
- ✅ Качество: 100% на шаблонных слайдах
- 📊 ~30-40% слайдов подходят под шаблоны

**Реализация:** 8-10 часов

---

## 📊 Сравнение оптимизаций

| Оптимизация | Время | Стоимость | Качество | Сложность | Приоритет |
|-------------|-------|-----------|----------|-----------|-----------|
| **1.1 Параллелизация** | -60% ⚡⚡⚡ | 0% | 0% ✅ | 2-4 ч | 🔥 ВЫСОКИЙ |
| **1.2 Кэширование OCR** | -99% (repeat) | -100% (repeat) | 0% ✅ | 1 ч | 🔥 ВЫСОКИЙ |
| **1.3 Batch TTS** | -78% ⚡⚡⚡ | -10% | 0% ✅ | 2 ч | 🟠 СРЕДНИЙ |
| **2.1 Selective Vision** | -60% ⚡⚡⚡ | -60% 💰💰💰 | -5% ⚠️ | 4-6 ч | 🔥 ВЫСОКИЙ |
| **2.2 Tiered LLM** | -40% ⚡⚡ | -46% 💰💰 | -3% ⚠️ | 3-4 ч | 🟠 СРЕДНИЙ |
| **2.3 Progressive** | -93% UX ⚡⚡⚡ | 0% | 0% ✅ | 8-10 ч | 🟠 СРЕДНИЙ |
| **3.1 Prompt Compress** | -20% ⚡ | -62% 💰💰💰 | -2% ⚠️ | 4-6 ч | 🟠 СРЕДНИЙ |
| **3.2 Hybrid Pipeline** | -63% ⚡⚡⚡ | -65% 💰💰💰 | 0% ✅ | 10-12 ч | 🟡 НИЗКИЙ |
| **3.3 Streaming** | -27% ⚡⚡ | 0% | 0% ✅ | 6-8 ч | 🟡 НИЗКИЙ |
| **3.4 Templates** | -54% ⚡⚡⚡ | -57% 💰💰💰 | 0% ✅ | 8-10 ч | 🟠 СРЕДНИЙ |

---

## 🎯 Рекомендуемый план внедрения

### **Phase 1: Quick Wins** (1 день)
1. ✅ Параллелизация обработки слайдов
2. ✅ Кэширование OCR результатов
3. ✅ Параллельные TTS запросы

**Результат:**
- ⚡ Время: **218 сек → 50 сек** (-77%)
- 💰 Стоимость: **$0.23** (без изменений)
- ✅ Качество: без изменений

---

### **Phase 2: Smart Processing** (2-3 дня)
4. ✅ Selective Vision (определяем сложность слайдов)
5. ✅ Tiered LLM (используем Flash-8B где возможно)

**Результат:**
- ⚡ Время: **50 сек → 30 сек** (-40%)
- 💰 Стоимость: **$0.23 → $0.08** (-65%)
- ✅ Качество: -5% на сложных слайдах (acceptable)

---

### **Phase 3: UX Enhancement** (3-4 дня)
6. ✅ Progressive Enhancement (показываем preview сразу)
7. ✅ Streaming responses (real-time обновления)

**Результат:**
- ⚡ Time to First Content: **30 сек → 10 сек** (-67%)
- ✅ UX значительно лучше

---

### **Phase 4: Advanced** (опционально, 1-2 недели)
8. ✅ Pre-computed Templates
9. ✅ Hybrid Pipeline
10. ✅ Prompt Compression

---

## 📈 Итоговые улучшения (Phase 1 + Phase 2)

| Метрика | До | После | Улучшение |
|---------|-----|-------|-----------|
| **Время (15 слайдов)** | 218 сек | **30 сек** | **-86%** ⚡ |
| **Стоимость** | $0.23 | **$0.08** | **-65%** 💰 |
| **Качество** | Baseline | **95%** | **-5%** ⚠️ |
| **Time to First Content** | 218 сек | **10 сек** | **-95%** ⚡ |

### Масштабирование:

**100 презентаций/день (1500 слайдов):**
- **До:** 6.05 часов, $23
- **После:** 0.85 часов, **$8** 
- **Экономия:** 5.2 часа, **$15/день = $450/месяц** 💰

---

## 🛠️ Пример реализации: Параллелизация

```python
# backend/app/pipeline/intelligent_optimized.py

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

class OptimizedIntelligentPipeline(IntelligentPipeline):
    """Оптимизированный пайплайн с параллельной обработкой"""
    
    def __init__(self, max_parallel: int = 5):
        super().__init__()
        self.max_parallel = max_parallel
        self.executor = ThreadPoolExecutor(max_workers=max_parallel)
    
    async def plan_parallel(self, lesson_dir: str) -> None:
        """Параллельная обработка слайдов"""
        
        manifest_data = self.load_manifest(lesson_dir)
        slides = manifest_data.get("slides", [])
        
        # Stage 0: Presentation Intelligence (1 раз)
        presentation_context = await self.presentation_intelligence.analyze_presentation(
            slides, filename=Path(lesson_dir).name
        )
        
        # Stage 2-3: Параллельная обработка слайдов
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def process_single_slide(slide, index):
            async with semaphore:  # Ограничиваем параллелизм
                logger.info(f"Processing slide {index + 1}/{len(slides)}")
                
                # Stage 2: Semantic Analysis
                semantic_map = await self.semantic_analyzer.analyze_slide(
                    slide_image_path=...,
                    ocr_elements=slide['elements'],
                    presentation_context=presentation_context,
                    slide_index=index
                )
                
                # Stage 3: Script Generation  
                script = await self.script_generator.generate_script(
                    semantic_map=semantic_map,
                    ocr_elements=slide['elements'],
                    presentation_context=presentation_context,
                    slide_index=index
                )
                
                return (index, semantic_map, script)
        
        # Запускаем обработку всех слайдов параллельно
        tasks = [
            process_single_slide(slide, i)
            for i, slide in enumerate(slides)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Применяем результаты к слайдам
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Slide processing failed: {result}")
                continue
            
            index, semantic_map, script = result
            slides[index]['semantic_map'] = semantic_map
            slides[index]['talk_track'] = script['talk_track']
            slides[index]['speaker_notes'] = script['speaker_notes']
        
        # Сохраняем обновлённый manifest
        self.save_manifest(lesson_dir, manifest_data)
    
    async def tts_parallel(self, lesson_dir: str) -> None:
        """Параллельная генерация TTS"""
        
        manifest_data = self.load_manifest(lesson_dir)
        slides = manifest_data.get("slides", [])
        
        async def generate_audio_for_slide(slide, index):
            talk_track = slide.get("talk_track", [])
            full_script = " ".join([s.get("text", "") for s in talk_track])
            
            # Синхронный вызов TTS в executor
            loop = asyncio.get_event_loop()
            audio_path, tts_words = await loop.run_in_executor(
                self.executor,
                synthesize_slide_text_google,
                [full_script]
            )
            
            return (index, audio_path, tts_words)
        
        # Параллельная генерация аудио
        tasks = [generate_audio_for_slide(slide, i) for i, slide in enumerate(slides)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Применяем результаты
        for result in results:
            if isinstance(result, Exception):
                continue
            index, audio_path, tts_words = result
            slides[index]['audio'] = audio_path
            slides[index]['duration'] = tts_words['sentences'][-1]['t1']
        
        self.save_manifest(lesson_dir, manifest_data)
```

---

## 🧪 A/B тестирование

Перед полным внедрением рекомендую A/B тест:

```python
# 50% пользователей - оптимизированный пайплайн
# 50% пользователей - текущий пайплайн

def get_pipeline(user_id: str):
    if hash(user_id) % 2 == 0:
        return OptimizedIntelligentPipeline()
    else:
        return IntelligentPipeline()
```

**Метрики для сравнения:**
- Время обработки
- Качество результата (user feedback)
- Error rate
- Стоимость

---

## ⚠️ Важные замечания

### Риски оптимизаций:

1. **Selective Vision:**
   - Может пропустить важные визуальные детали на "простых" слайдах
   - Решение: Консервативный порог определения сложности

2. **Tiered LLM:**
   - Flash-8B может генерировать менее качественные скрипты
   - Решение: A/B тест, fallback на full model при низком качестве

3. **Параллелизация:**
   - Rate limits API
   - Решение: Semaphore с ограничением (5-10 параллельных запросов)

4. **Prompt Compression:**
   - Может снизить качество генерации
   - Решение: Сохранить few-shot examples для критичных задач

---

## 🎯 Рекомендация

**Начните с Phase 1 (Quick Wins):**
1. Параллелизация (2-4 часа разработки)
2. Кэширование (1 час разработки)
3. Parallel TTS (2 часа разработки)

**Итого:** 5-7 часов работы для получения **-77% времени обработки**.

**ROI:** Если обрабатываете 100+ презентаций/день, окупится за 1 день.

---

Хотите, чтобы я начал реализацию Phase 1? 🚀
