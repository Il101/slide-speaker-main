# Pipeline Stages - OptimizedIntelligentPipeline

## 📋 Все Stages по порядку

### **Stage 0: Presentation Context Analysis**
**Метод:** `plan()`  
**Время:** ~2-3 сек  
**Что делает:**
- Анализирует ВСЮ презентацию целиком (1 раз)
- Определяет тему, уровень, стиль
- Создаёт контекст для генерации скриптов

**Входные данные:**
- Все слайды презентации
- Filename

**Выходные данные:**
```json
{
  "theme": "Биология растений",
  "level": "undergraduate", 
  "presentation_style": "academic",
  "total_slides": 15
}
```

**Сервис:** `PresentationIntelligence`  
**LLM:** Gemini  

---

### **Stage 1: Ingest (Валидация)**
**Метод:** `ingest()`  
**Время:** ~0.1 сек  
**Что делает:**
- Проверяет существование manifest.json
- Валидирует структуру
- Подсчитывает слайды

**Входные данные:**
- `lesson_dir` path
- `manifest.json` (создан в main.py при загрузке)

**Выходные данные:**
- Validated manifest

---

### **Stage 2: Semantic Analysis** ⚡ (Параллельно)
**Метод:** `plan()` → `process_single_slide()`  
**Время:** ~3-4 сек на слайд, ~12 сек для 15 слайдов (параллельно)  
**Параллелизм:** До 5 слайдов одновременно  

**Что делает:**
- Анализирует изображение слайда
- Группирует логически связанные элементы
- Определяет приоритеты и стратегии выделения

**Входные данные (для каждого слайда):**
- Slide image (PNG)
- OCR elements (text + coordinates)
- Presentation context
- Previous slides (для контекста)

**Выходные данные:**
```json
{
  "slide_type": "content_slide",
  "groups": [
    {
      "id": "group_0",
      "name": "Title",
      "type": "title",
      "priority": "high",
      "element_ids": ["slide_1_block_0"],
      "highlight_strategy": {
        "when": "start",
        "effect_type": "spotlight",
        "duration": 2.5
      }
    }
  ],
  "visual_density": "medium",
  "cognitive_load": "easy"
}
```

**Сервис:** `SemanticAnalyzer`  
**LLM:** Gemini Vision API  

---

### **Stage 3: Script Generation** ⚡ (Параллельно)
**Метод:** `plan()` → `process_single_slide()`  
**Время:** ~2-3 сек на слайд, ~12 сек для 15 слайдов (параллельно)  
**Параллелизм:** До 5 слайдов одновременно (вместе с Stage 2)

**Что делает:**
- Генерирует структурированный talk_track
- Создаёт педагогически правильный скрипт
- 6 сегментов: hook → context → explanation → example → emphasis → transition

**Входные данные:**
- semantic_map (из Stage 2)
- elements
- presentation_context
- previous_slides_summary

**Выходные данные:**
```json
{
  "talk_track": [
    {"segment": "hook", "text": "Willkommen! Heute starten wir..."},
    {"segment": "context", "text": "Stattdessen wollen wir..."},
    {"segment": "explanation", "text": "Heute starten wir mit..."},
    {"segment": "example", "text": "Stell dir vor..."},
    {"segment": "emphasis", "text": "Merkt euch..."},
    {"segment": "transition", "text": "Im nächsten Schritt..."}
  ],
  "speaker_notes": "Full combined text...",
  "estimated_duration": 45
}
```

**Сервис:** `SmartScriptGenerator`  
**LLM:** Gemini Text API  

---

### **Stage 4: TTS Generation** ⚡ (Параллельно)
**Метод:** `tts()`  
**Время:** ~4-6 сек на слайд, ~10 сек для 15 слайдов (параллельно)  
**Параллелизм:** До 10 слайдов одновременно  

**Что делает:**
1. Генерирует SSML из talk_track с `<mark>` тегами
2. Синтезирует речь через Google TTS v1beta1
3. Получает word-level timings

**Входные данные:**
- talk_track segments

**SSML (промежуточный):**
```xml
<speak>
<prosody rate="medium" pitch="+2st">
<mark name="mark_0"/>Willkommen <mark name="mark_1"/>zum <mark name="mark_2"/>ersten
</prosody>
</speak>
```

**Выходные данные:**
```json
{
  "audio": "/tmp/audio/001.wav",
  "sentences": [
    {"text": "Willkommen zum ersten...", "t0": 0.0, "t1": 2.5}
  ],
  "word_timings": [
    {"mark_name": "mark_0", "time_seconds": 0.34},
    {"mark_name": "mark_1", "time_seconds": 0.82},
    {"mark_name": "mark_2", "time_seconds": 1.15}
  ]
}
```

**Сервисы:** 
- `SSMLGenerator` (создание SSML)
- `GoogleTTSWorkerSSML` (синтез речи)

**API:** Google Cloud TTS v1beta1  

---

### **Stage 5: Visual Effects Generation**
**Метод:** `build_manifest()`  
**Время:** ~0.2 сек на слайд, ~3 сек для 15 слайдов  

**Что делает:**
- Генерирует visual cues синхронизированные с TTS word timings
- Определяет когда выделять каждый элемент
- Создаёт точные timings для эффектов

**Алгоритм:**
1. Извлекает word_timings из TTS
2. Для каждой группы:
   - Получает текст группы
   - Ищет когда этот текст произносится в word_timings
   - Генерирует cue с точным timing
3. Применяет стратегию из semantic_map (spotlight/highlight/etc)

**Входные данные:**
- semantic_map (groups + strategies)
- elements (OCR data)
- duration (audio length)
- tts_words (с word_timings!)

**Выходные данные:**
```json
[
  {
    "cue_id": "cue_abc123",
    "t0": 0.34,  // ← Синхронизировано с TTS word timing!
    "t1": 1.67,
    "action": "spotlight",
    "element_id": "slide_1_block_0",
    "bbox": [588, 97, 265, 47],
    "effect_type": "spotlight",
    "intensity": "dramatic"
  }
]
```

**Сервис:** `VisualEffectsEngine`  

---

### **Stage 6: Validation**
**Метод:** `build_manifest()`  
**Время:** ~0.1 сек на слайд  

**Что делает:**
- Валидирует visual cues
- Проверяет timing (t1 > t0)
- Проверяет overlaps
- Проверяет element_id existence
- Исправляет ошибки автоматически

**Входные данные:**
- cues (из Stage 5)
- duration
- elements

**Выходные данные:**
- Validated and fixed cues
- List of errors (if any)

**Сервис:** `ValidationEngine`  

---

### **Stage 7: (Нет отдельного stage)**
**Примечание:** Stage 7 пропущен в текущей реализации

---

### **Stage 8: Timeline Building**
**Метод:** `build_manifest()`  
**Время:** ~0.1 сек  

**Что делает:**
- Создаёт общий timeline для всей презентации
- Определяет когда переключать слайды
- Рассчитывает общую длительность

**Входные данные:**
- All slides with durations

**Выходные данные:**
```json
{
  "timeline": [
    {
      "t0": 0.0,
      "t1": 29.376,
      "action": "slide_change",
      "slide_id": 1
    },
    {
      "t0": 29.376,
      "t1": 58.752,
      "action": "slide_change",
      "slide_id": 2
    }
  ]
}
```

---

## 🔄 Полный Flow

```
STAGE 0  → Presentation Context (1x, 2-3s)
   ↓
STAGE 1  → Ingest/Validation (0.1s)
   ↓
STAGE 2  → Semantic Analysis (parallel, 12s for 15 slides)
   ↓
STAGE 3  → Script Generation (parallel with Stage 2)
   ↓
STAGE 4  → TTS with SSML (parallel, 10s for 15 slides)
   ↓
STAGE 5  → Visual Effects (3s)
   ↓
STAGE 6  → Validation (0.3s)
   ↓
STAGE 8  → Timeline (0.1s)
   ↓
OUTPUT   → Final manifest.json
```

---

## ⚡ Параллелизация

| Stages | Parallel | Max Concurrent | Speedup |
|--------|----------|----------------|---------|
| Stage 2+3 | ✅ Yes | 5 slides | **3.75x** |
| Stage 4 | ✅ Yes | 10 slides | **7.5x** |
| Stage 5+6+8 | ❌ No | Sequential | 1x |

---

## 📊 Timing Summary (15 slides)

| Stage | Time | Notes |
|-------|------|-------|
| Stage 0 | 2-3s | Once for entire presentation |
| Stage 1 | 0.1s | Validation only |
| Stage 2+3 | 12s | Parallel processing |
| Stage 4 | 10s | Parallel TTS generation |
| Stage 5 | 3s | Visual effects |
| Stage 6 | 0.3s | Validation |
| Stage 8 | 0.1s | Timeline |
| **TOTAL** | **~25s** | **For 15 slides** |

---

## 🎯 Методы Pipeline

```python
class OptimizedIntelligentPipeline(BasePipeline):
    
    def ingest(lesson_dir):
        # Stage 1
        pass
    
    def plan(lesson_dir):
        # Stage 0, 2, 3
        pass
    
    def tts(lesson_dir):
        # Stage 4
        pass
    
    def build_manifest(lesson_dir):
        # Stage 5, 6, 8
        pass
    
    def process_full_pipeline(lesson_dir):
        # Orchestrator: calls all stages in order
        self.ingest(lesson_dir)
        self.plan(lesson_dir)
        self.tts(lesson_dir)
        self.build_manifest(lesson_dir)
```

---

## 🔧 Используемые Сервисы по Stages

| Stage | Service | LLM/API |
|-------|---------|---------|
| 0 | PresentationIntelligence | Gemini |
| 1 | - | - |
| 2 | SemanticAnalyzer | Gemini Vision |
| 3 | SmartScriptGenerator | Gemini |
| 4 | SSMLGenerator + GoogleTTSWorkerSSML | Google TTS v1beta1 |
| 5 | VisualEffectsEngine | - |
| 6 | ValidationEngine | - |
| 8 | - | - |

---

**Итого: 8 stages** (Stage 0-6, 8)  
**Stage 7 отсутствует** в текущей реализации
