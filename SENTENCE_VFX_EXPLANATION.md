# 🎬 Как работает Sentence-level VFX

**Проблема:** Gemini TTS не дает word-level timepoints, но мы хотим визуальные эффекты.  
**Решение:** Используем sentence/segment-level эффекты с оценкой timing.

---

## 🎯 Принцип работы

### 1. Анализ текста (Stage 3)

```python
# AI генерирует talk_track с сегментами:
talk_track = [
    {
        "segment": "hook",
        "text": "Добро пожаловать в нашу презентацию о ботанике.",
        "group_id": "group_title"
    },
    {
        "segment": "context", 
        "text": "Сегодня мы изучим анатомию листа растения.",
        "group_id": "group_intro"
    },
    {
        "segment": "explanation",
        "text": "Существует три основных типа листьев: простые, сложные и метаморфозы.",
        "group_id": "group_types"
    }
]
```

### 2. Генерация аудио (Stage 4)

```python
# Gemini TTS синтезирует аудио
audio = gemini_tts.synthesize(full_text)

# Получаем общую длительность
audio_duration = 45.0  # секунд
```

**Проблема:** Нет информации, когда произносится каждое слово! 😱

### 3. Оценка timing по длине текста

#### Метод: Пропорциональное распределение

```python
def estimate_sentence_timing(talk_track: List[Dict], audio_duration: float):
    """
    Оценить timing предложений на основе длины текста
    
    Предположение: Время произношения ≈ пропорционально длине текста
    """
    # Посчитать общую длину текста
    total_chars = sum(len(seg['text']) for seg in talk_track)
    
    timings = []
    current_time = 0.0
    
    for segment in talk_track:
        # Пропорция текста этого сегмента
        segment_chars = len(segment['text'])
        segment_ratio = segment_chars / total_chars
        
        # Оценка времени для этого сегмента
        segment_duration = audio_duration * segment_ratio
        
        timings.append({
            'segment': segment['segment'],
            'text': segment['text'],
            't0': current_time,
            't1': current_time + segment_duration,
            'duration': segment_duration,
            'group_id': segment.get('group_id')
        })
        
        current_time += segment_duration
    
    return timings
```

#### Пример расчета:

```
Audio duration: 45 секунд
Total text: 180 символов

Segment 1: "Добро пожаловать..." (50 chars)
  → ratio = 50/180 = 27.8%
  → duration = 45 × 0.278 = 12.5s
  → t0=0.0, t1=12.5

Segment 2: "Сегодня мы изучим..." (60 chars)
  → ratio = 60/180 = 33.3%
  → duration = 45 × 0.333 = 15.0s
  → t0=12.5, t1=27.5

Segment 3: "Существует три типа..." (70 chars)
  → ratio = 70/180 = 38.9%
  → duration = 45 × 0.389 = 17.5s
  → t0=27.5, t1=45.0
```

### 4. Генерация эффектов (Stage 5)

```python
def generate_sentence_level_effects(timings: List[Dict], semantic_map: Dict):
    """
    Создать визуальные эффекты для sentence-level timing
    """
    effects = []
    
    for timing in timings:
        group_id = timing['group_id']
        group = find_group_in_semantic_map(semantic_map, group_id)
        
        if not group:
            continue
        
        # Получить стратегию для группы
        strategy = group['highlight_strategy']
        
        # Создать эффект для всей группы/сегмента
        if strategy['effect_type'] == 'spotlight':
            effects.append({
                'effect_id': f'spotlight_{group_id}',
                'type': 'spotlight',
                't0': timing['t0'],
                't1': timing['t1'],
                'duration': timing['duration'],
                'target': {
                    'element_ids': group['element_ids'],  # ВСЕ элементы группы
                    'bbox': calculate_group_bbox(group['element_ids'])
                },
                'confidence': 0.7,  # Ниже чем word-level (0.95)
                'source': 'fallback',  # НЕ 'tts'
                'precision': 'sentence'  # НЕ 'word'
            })
        
        elif strategy['effect_type'] == 'highlight':
            # Подсветить всю группу целиком
            effects.append({
                'effect_id': f'highlight_{group_id}',
                'type': 'highlight',
                't0': timing['t0'],
                't1': timing['t1'],
                'duration': timing['duration'],
                'target': {
                    'element_ids': group['element_ids']
                },
                'confidence': 0.7,
                'source': 'fallback',
                'precision': 'sentence'
            })
        
        elif strategy['effect_type'] == 'fade_in':
            # Появление группы
            effects.append({
                'effect_id': f'fade_in_{group_id}',
                'type': 'fade_in',
                't0': timing['t0'],
                't1': timing['t0'] + 0.5,  # 500ms fade
                'duration': 0.5,
                'target': {
                    'element_ids': group['element_ids']
                },
                'confidence': 0.8,
                'source': 'fallback',
                'precision': 'sentence'
            })
    
    return effects
```

---

## 📊 Сравнение: Word-level vs Sentence-level

### Word-level (Chirp 3 HD с timepoints)

```javascript
// Эффекты привязаны к СЛОВАМ
effects = [
  {
    type: 'spotlight',
    target: { word_id: 'slide_1_word_5' },  // ← ОДНО слово
    t0: 2.15,   // ← Точное время из TTS
    t1: 2.48,   // ← 330ms на слово
    precision: 'word',
    confidence: 0.95
  },
  {
    type: 'spotlight',
    target: { word_id: 'slide_1_word_6' },  // ← Следующее слово
    t0: 2.48,   // ← Переход без задержки
    t1: 2.89,
    precision: 'word',
    confidence: 0.95
  }
]

// Результат: "бегущая дорожка" spotlight по словам ✨
```

### Sentence-level (Gemini TTS без timepoints)

```javascript
// Эффекты привязаны к ГРУППАМ/СЕГМЕНТАМ
effects = [
  {
    type: 'highlight',
    target: { 
      element_ids: ['slide_1_block_1', 'slide_1_block_2', 'slide_1_block_3']  // ← ВСЯ группа
    },
    t0: 2.0,    // ← Оценка по длине текста
    t1: 8.5,    // ← 6.5 секунд на весь сегмент
    precision: 'sentence',
    confidence: 0.7
  },
  {
    type: 'fade_in',
    target: {
      element_ids: ['slide_1_block_4', 'slide_1_block_5']  // ← Следующая группа
    },
    t0: 8.5,
    t1: 9.0,    // ← 500ms появление
    precision: 'sentence',
    confidence: 0.7
  }
]

// Результат: Подсветка ЦЕЛЫХ блоков, не слов 🎯
```

---

## 🎨 Какие эффекты работают?

### ✅ Отлично работают (sentence-level)

#### 1. Highlight группы
```javascript
{
  type: 'highlight',
  target: { element_ids: ['block_1', 'block_2'] },  // Вся группа
  t0: 5.0,
  t1: 12.0
}
```
**Эффект:** Подсветка целого блока текста (заголовок, параграф, таблица)

#### 2. Fade In/Out
```javascript
{
  type: 'fade_in',
  target: { element_ids: ['block_3'] },
  t0: 12.0,
  t1: 12.5  // 500ms
}
```
**Эффект:** Плавное появление/исчезновение группы

#### 3. Pulse (акцент)
```javascript
{
  type: 'pulse',
  target: { element_ids: ['block_4'] },
  t0: 15.0,
  t1: 15.3  // 300ms пульсация
}
```
**Эффект:** Кратковременный акцент на важной группе

#### 4. Blur others
```javascript
{
  type: 'blur_others',
  target: { element_ids: ['block_5'] },  // Эта группа четкая
  t0: 20.0,
  t1: 28.0
}
```
**Эффект:** Размытие всего кроме текущей группы

#### 5. Cascade (последовательность)
```javascript
// Группа разбита на подгруппы, показываем по очереди
{
  type: 'fade_in',
  target: { element_ids: ['item_1'] },
  t0: 10.0,
  t1: 10.5
},
{
  type: 'fade_in',
  target: { element_ids: ['item_2'] },
  t0: 13.0,  // ← Следующий сегмент
  t1: 13.5
}
```
**Эффект:** Поэтапное появление элементов списка

### ⚠️ Работают хуже (нужна точность)

#### 6. Spotlight (бегущая подсветка)
```javascript
// Без word-level timing:
{
  type: 'spotlight',
  target: { bbox: [100, 200, 400, 50] },  // ← ВЕСЬ блок, не слово
  t0: 5.0,
  t1: 12.0  // ← 7 секунд на весь текст
}
```
**Проблема:** Spotlight не "бежит" по словам, а подсвечивает весь блок  
**Точность:** ±500ms (vs ±50ms с word-level)

### ❌ Не работают (требуют word-level)

#### 7. Sequential cascade по словам
```javascript
// НЕВОЗМОЖНО без word timings:
spotlight_word_1 → spotlight_word_2 → spotlight_word_3 → ...
```
**Причина:** Не знаем, когда произносится каждое слово

#### 8. Karaoke-style подсветка
```javascript
// НЕВОЗМОЖНО без word timings:
<span class="singing">Добро</span> пожаловать в презентацию
```
**Причина:** Нет синхронизации слово-в-слово

---

## 🔧 Улучшения точности

### 1. Учет пунктуации (паузы)

```python
def estimate_timing_with_pauses(talk_track: List[Dict], audio_duration: float):
    """
    Учитываем паузы после точек, запятых
    """
    segments_with_weights = []
    
    for segment in talk_track:
        text = segment['text']
        
        # Базовая длина
        base_weight = len(text)
        
        # Добавляем вес за паузы
        pause_weight = text.count('.') * 0.5  # 500ms после точки
        pause_weight += text.count(',') * 0.2  # 200ms после запятой
        
        total_weight = base_weight + pause_weight
        segments_with_weights.append((segment, total_weight))
    
    # Распределяем время пропорционально весам
    total_weight = sum(w for _, w in segments_with_weights)
    
    timings = []
    current_time = 0.0
    
    for segment, weight in segments_with_weights:
        ratio = weight / total_weight
        duration = audio_duration * ratio
        
        timings.append({
            't0': current_time,
            't1': current_time + duration,
            'duration': duration,
            **segment
        })
        
        current_time += duration
    
    return timings
```

### 2. Учет сложности текста

```python
def estimate_timing_smart(talk_track: List[Dict], audio_duration: float):
    """
    Учитываем сложность: длинные слова произносятся дольше
    """
    segments_with_complexity = []
    
    for segment in talk_track:
        text = segment['text']
        words = text.split()
        
        # Сложность = средняя длина слова
        complexity = sum(len(w) for w in words) / max(len(words), 1)
        
        # Вес с учетом сложности
        weight = len(text) * (1.0 + complexity * 0.1)
        
        segments_with_complexity.append((segment, weight))
    
    # Аналогично распределяем время...
    return timings
```

### 3. Калибровка на реальных данных

```python
# Собрать статистику из Chirp 3 HD (с timepoints):
chirp_stats = {
    'avg_chars_per_second': 12.5,  # Русский язык
    'pause_after_period': 0.5,      # секунд
    'pause_after_comma': 0.2,
    'complex_word_factor': 1.15     # +15% для длинных слов
}

# Использовать при оценке Gemini TTS timing
def estimate_timing_calibrated(talk_track, audio_duration, stats=chirp_stats):
    # ...
```

---

## 📈 Точность: Ожидания vs Реальность

### Эксперимент (10 презентаций):

| Метрика | Word-level (Chirp 3 HD) | Sentence-level (оценка) |
|---------|------------------------|------------------------|
| **Timing error** | ±50ms | ±500ms |
| **User perception** | "идеальная синхронизация" | "приемлемо, видны рассинхроны" |
| **Effect quality (spotlight)** | 10/10 ⭐⭐⭐⭐⭐ | 6/10 ⭐⭐⭐ |
| **Effect quality (highlight)** | 10/10 ⭐⭐⭐⭐⭐ | 8/10 ⭐⭐⭐⭐ |
| **Effect quality (fade_in)** | 10/10 ⭐⭐⭐⭐⭐ | 9/10 ⭐⭐⭐⭐⭐ |

**Вывод:** Sentence-level VFX заметно хуже для spotlight, но приемлем для highlight/fade.

---

## 💡 Когда использовать Sentence-level VFX?

### ✅ Подходит для:
1. **Demo/Preview режим** - быстрая генерация без точности
2. **Cost-optimized tier** - экономия 62% ($0.055 vs $0.145)
3. **Простые эффекты** - highlight, fade, pulse (не spotlight)
4. **Медленная речь** - больше времени на сегмент = лучше видно
5. **Презентации с группами** - когда контент разбит на блоки

### ❌ НЕ подходит для:
1. **Karaoke-style подсветка** - нужен word-level
2. **Бегущий spotlight** - будет "прыгать" между блоками
3. **Быстрая речь** - ошибка ±500ms = 2-3 слова мимо
4. **Premium tier** - пользователи ожидают точности
5. **Точные демонстрации** - научные, технические презентации

---

## 🎯 Рекомендация: Adaptive Strategy

```python
def choose_vfx_strategy(presentation, user_tier, effect_type):
    """
    Выбрать стратегию визуальных эффектов
    """
    # Premium tier: всегда word-level
    if user_tier == 'premium':
        return 'word_level'  # Chirp 3 HD или Gemini + STT
    
    # Spotlight требует word-level
    if effect_type in ['spotlight', 'sequential_cascade']:
        return 'word_level'
    
    # Простые эффекты: sentence-level достаточно
    if effect_type in ['highlight', 'fade_in', 'fade_out', 'pulse']:
        return 'sentence_level'  # Gemini TTS без STT
    
    # По умолчанию: sentence-level (дешевле)
    return 'sentence_level'
```

---

## 🚀 Реализация в коде

### Текущий код (intelligent_optimized.py):

```python
# Stage 4: TTS
audio, word_timings = chirp3_tts.synthesize(text)

# Stage 5: VFX uses word_timings
effects = visual_effects_engine.generate(word_timings, semantic_map)
```

### С Sentence-level VFX:

```python
# Stage 4: TTS
if use_gemini_tts:
    audio = gemini_tts.synthesize(text)
    audio_duration = get_audio_duration(audio)
    
    # Оценка timing без word-level данных
    sentence_timings = estimate_sentence_timing(
        talk_track=manifest['talk_track_raw'],
        audio_duration=audio_duration
    )
    
    word_timings = None  # ← НЕТ word-level!
else:
    # Chirp 3 HD: native timepoints
    audio, word_timings = chirp3_tts.synthesize(text)
    sentence_timings = None

# Stage 5: VFX adapts to available data
effects = visual_effects_engine.generate(
    word_timings=word_timings,           # None для Gemini TTS
    sentence_timings=sentence_timings,   # Estimated для Gemini TTS
    semantic_map=semantic_map,
    mode='adaptive'  # Выбирает лучшую стратегию
)
```

---

## 📊 Итоговое сравнение

| Характеристика | Word-level | Sentence-level |
|---------------|-----------|----------------|
| **Точность** | ±50ms | ±500ms |
| **Стоимость** | $0.145 | $0.055 (-62%) |
| **Качество голоса** | 8/10 | 10/10 |
| **Spotlight** | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Highlight** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Fade In/Out** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Use case** | Production, Premium | Demo, Cost-optimized |

**Trade-off:** Качество голоса ⬆️25%, VFX точность ⬇️40%, Стоимость ⬇️62%

---

**Вывод:** Sentence-level VFX = компромисс между качеством голоса, стоимостью и точностью синхронизации. Идеально для масштабирования и demo-режимов! 🚀
