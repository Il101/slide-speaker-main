# 📊 Зачем нужны TTS Timings (t0, t1)?

## 🎯 Основная цель

TTS timings (t0 и t1 для каждого сегмента) используются для **синхронизации визуальных эффектов с аудио**. Это как подписи к фильму, но для интерактивных элементов.

```
Аудио:    [Речь говорящего в течение 20 секунд...]
Тайминги: {t0: 0.3, t1: 2.5} → выделить "Epidermis"
          {t0: 2.7, t1: 5.1} → выделить "Mesophyll"
          {t0: 5.3, t1: 7.8} → выделить "Palisadenmesophyll"
Видео:    0s: выделяем первый элемент
          2.7s: меняем выделение на второй
          5.3s: меняем выделение на третий
```

---

## 🎬 Как работает синхронизация

### Процесс:

```python
1. TTS генерирует аудио + timings:
   {
       "sentences": [
           {"text": "Epidermis ist die äußerste Schicht", "t0": 0.3, "t1": 2.5},
           {"text": "Mesophyll bildet das Grundgewebe", "t0": 2.7, "t1": 5.1}
       ]
   }

2. Visual Effects Engine использует timings:
   - Парсит text из sentences
   - Ищет соответствующие элементы на слайде
   - Создаёт "cues" (команды анимации)
   
3. Manifest содержит synchronized cues:
   {
       "cues": [
           {"t0": 0.3, "t1": 2.5, "action": "highlight", "bbox": [100, 150, 200, 50]},
           {"t0": 2.7, "t1": 5.1, "action": "highlight", "bbox": [300, 200, 150, 40]}
       ]
   }

4. Frontend Player воспроизводит:
   - Играет аудио
   - Отслеживает currentTime
   - Применяет эффекты когда t0 <= currentTime <= t1
```

---

## 📊 Где используются timings

### 1. **Visual Effects Engine** (`visual_effects_engine.py`)
```python
def generate_cues_from_semantic_map(
    self,
    tts_words: Dict[str, Any],  # ← Timings отсюда!
    talk_track: List[Dict],
    elements: List[Dict]
):
    # Для каждого элемента находим когда он упоминается
    for sentence in tts_words['sentences']:
        t0, t1 = sentence['t0'], sentence['t1']  # ← ИСПОЛЬЗУЮТСЯ ЗДЕСЬ
        
        # Ищем совпадающий элемент
        for elem in elements:
            if elem['text'] in sentence['text']:
                # Создаём cue с временем из timings
                cues.append({
                    "t0": t0,
                    "t1": t1,
                    "action": "highlight",
                    "bbox": elem['bbox']
                })
```

### 2. **Bullet Point Sync Service** (`bullet_point_sync.py`)
```python
def _generate_cues_from_timings(self, word_timings: List[Dict]):
    # Находит когда упоминается каждый пункт
    for timing in word_timings:
        t0 = timing['t0']  # ← КОГДА НАЧИНАЕТ ГОВОРИТЬ
        t1 = timing['t1']  # ← КОГДА ЗАКАНЧИВАЕТ ГОВОРИТЬ
        
        # Создаёт cue с этими временами
        cue = {
            't0': t0,
            't1': t1,
            'action': 'highlight'
        }
```

### 3. **Timeline Aligner** (`align.py`)
```python
class TimelineAligner:
    def _generate_synchronized_cues(
        self, 
        sentences: List[SentenceTiming]  # ← Из TTS timings!
    ):
        for sentence in sentences:
            t0, t1 = sentence.t0, sentence.t1  # ← ИСПОЛЬЗУЮТСЯ ЗДЕСЬ
            
            cue = TimingCue(
                t0=t0,  # ← Когда начать выделение
                t1=t1,  # ← Когда закончить выделение
                action='highlight'
            )
```

### 4. **Frontend Player** (`useAudioSync.ts`)
```typescript
const syncLoop = () => {
    const currentTime = audioRef.current.currentTime;
    
    // Проверяем все cues
    for (const cue of slide.cues) {
        // ← t0 и t1 используются ДЛЯ ПРОВЕРКИ!
        if (currentTime >= cue.t0 && currentTime <= cue.t1) {
            // Применяем эффект (highlight, underline и т.д.)
            applyEffect(cue);
        } else {
            removeEffect(cue);
        }
    }
};
```

---

## 📈 Пример: Полный цикл

```
Слайд: "Структура листа"
Элементы: [Epidermis, Mesophyll, Vascular Bundle]
Аудио: ~8 секунд

ШАГ 1: TTS генерирует аудио + timings
├─ "Эпидермис - это верхний слой." → {t0: 0.3, t1: 2.5}
├─ "Мезофилл находится под ним." → {t0: 2.7, t1: 5.1}
└─ "Проводящие пучки в центре." → {t0: 5.3, t1: 7.8}

ШАГ 2: Visual Effects Engine обрабатывает
├─ Парсит "Эпидермис" → находит элемент "Epidermis"
├─ Создаёт cue: {t0: 0.3, t1: 2.5, action: "highlight", bbox: [...]}
└─ Повторяет для остальных

ШАГ 3: Manifest содержит synchronized cues
{
  "cues": [
    {"t0": 0.3, "t1": 2.5, "element_id": "epidermis", "action": "highlight"},
    {"t0": 2.7, "t1": 5.1, "element_id": "mesophyll", "action": "highlight"},
    {"t0": 5.3, "t1": 7.8, "element_id": "vascular", "action": "highlight"}
  ]
}

ШАГ 4: Frontend воспроизводит
├─ 0.3s: начинается аудио "Эпидермис..."
│        одновременно выделяется Epidermis элемент ← СИНХРОНИЗИРОВАНО!
│
├─ 2.5s: Epidermis перестаёт выделяться
├─ 2.7s: начинается "Мезофилл..."
│        одновременно выделяется Mesophyll ← СИНХРОНИЗИРОВАНО!
│
└─ 7.8s: конец речи и выделения
```

---

## ❌ Проблема БЕЗ таймингов

**Если бы мы НЕ использовали timings:**

```
Что происходит:
├─ 0s: показываем все элементы равномерно
├─ 3s: меняем на следующий элемент
├─ 6s: меняем ещё
└─ Результат: РАССИНХРОНИЗИРОВАНО с аудио!

Пользователь слышит "Epidermis" но видит "Vascular Bundle" ❌
```

---

## 📋 Структура TTS timings

```python
tts_words = {
    "audio": "/path/to/audio.mp3",
    
    # ← ЭТА ЧАСТЬ НУЖНА ДЛЯ СИНХРОНИЗАЦИИ:
    "sentences": [
        {
            "text": "Эпидермис является внешним слоем листа",
            "t0": 0.3,      # ← Когда говорящий начинает это предложение
            "t1": 2.5,      # ← Когда заканчивает
            "duration": 2.2  # ← Вычисляется как t1 - t0
        },
        {
            "text": "Мезофилл расположен под эпидермисом",
            "t0": 2.7,      # ← Следующее предложение
            "t1": 5.1,
            "duration": 2.4
        }
    ],
    
    # Опционально (не всегда есть):
    "word_timings": [  # ← Word-level timings для более точной синхронизации
        {"mark_name": "group_epidermis", "time_seconds": 0.3},
        {"mark_name": "w0", "time_seconds": 0.5},
        ...
    ]
}
```

---

## 🎯 Зависимость: Timings → Cues → Effects

```
┌─────────────────────┐
│ TTS Timings         │
│ (t0, t1 для каждой │
│  фразы/слова)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Visual Effects      │
│ Engine парсит текст │
│ и создаёт cues      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Manifest.json       │
│ содержит synchronized │
│ cues с временами     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Frontend Player     │
│ использует t0, t1   │
│ для анимации        │
└─────────────────────┘
```

---

## 🔍 Почему это важно

✅ **Без таймингов:** визуальные эффекты идут "просто так", не совпадая с озвучкой  
✅ **С таймингами:** эффекты **точно** синхронизированы с тем, что говорит диктор  

### Примеры:
- 🎯 Когда диктор говорит "Эпидермис", **ровно в этот момент** выделяется соответствующий элемент
- 🎯 Когда диктор говорит "Мезофилл", выделение **автоматически** переходит на этот элемент
- 🎯 Поэтому выглядит так, как будто диктор **указывает** на элементы!

---

## 📝 Резюме

| Вопрос | Ответ |
|--------|-------|
| **Зачем нужны timings?** | Синхронизация видеоэффектов с аудио |
| **Где используются?** | Visual Effects Engine, Bullet Point Sync, Timeline Aligner |
| **Какой формат?** | `{"text": "...", "t0": 0.3, "t1": 2.5}` |
| **Что произойдёт без них?** | Эффекты будут асинхронные и не совпадут с озвучкой |
| **Точность?** | Sentence-level для Gemini TTS, word-level для Google TTS |
