# 📊 Intelligent Pipeline - Детальная Документация

## 🎯 Обзор

**Intelligent Pipeline** - это AI-driven система для автоматического преобразования презентаций (PPTX/PDF) в интерактивные видео-лекции с голосовым сопровождением и визуальными эффектами.

---

## 🏗️ Архитектура: 8 стадий обработки

```
📤 Загрузка файла (PPTX/PDF)
    ↓
[Pre-Stage] PDF → PNG конвертация
    ↓
[Stage 1] INGEST - OCR распознавание текста
    ↓
[Stage 0] PRESENTATION INTELLIGENCE - Глобальный анализ
    ↓
[Stage 2] SEMANTIC ANALYSIS - Группировка элементов (LLM + Vision)
    ↓
[Stage 3] SCRIPT GENERATION - Генерация сценария лекции (LLM)
    ↓
[Stage 4] TTS - Синтез речи
    ↓
[Stage 5] VISUAL EFFECTS - Генерация эффектов
    ↓
[Stage 6] VALIDATION - Проверка и исправление
    ↓
[Stage 7] BUILD MANIFEST - Финальная сборка
    ↓
🎬 Готовая видео-лекция
```

---

## 📤 Pre-Stage: Загрузка и конвертация

### Что происходит:
1. Пользователь загружает файл через frontend (http://localhost:3000)
2. Backend получает файл через FastAPI endpoint `/upload`
3. Создаётся уникальная папка для лекции: `.data/{uuid}/`
4. PDF/PPTX конвертируется в PNG изображения

### API используется:
- **PyMuPDF (fitz)** - для PDF → PNG
- **python-pptx** или **libreoffice** - для PPTX → PDF → PNG

### Код:
```python
# backend/app/services/sprint1/document_parser.py
def extract_slides_from_pdf(pdf_path: Path, output_dir: Path) -> List[Path]:
    doc = fitz.open(pdf_path)
    slide_paths = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution
        img_path = output_dir / f"{page_num + 1:03d}.png"
        pix.save(img_path)
        slide_paths.append(img_path)
    
    return slide_paths
```

### Результат:
```
.data/{uuid}/
├── slides/
│   ├── 001.png  # Слайд 1 (1440x1080)
│   ├── 002.png  # Слайд 2
│   └── ...
└── original_file.pdf
```

---

## 🔍 Stage 1: INGEST - OCR распознавание

### Что происходит:
Извлечение текста и координат всех элементов с каждого слайда

### API используется:
**Текущая конфигурация: `OCR_PROVIDER=vision`**

#### Option 1: Google Vision API ✅ (активна)
```python
from google.cloud import vision

client = vision.ImageAnnotatorClient()

# Отправка изображения в Vision API
with open(slide_path, 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)
response = client.document_text_detection(image=image)

# Извлечение текста с координатами
for page in response.full_text_annotation.pages:
    for block in page.blocks:
        for paragraph in block.paragraphs:
            vertices = paragraph.bounding_box.vertices
            text = ''.join([symbol.text for word in paragraph.words for symbol in word.symbols])
```

#### Option 2: Google Document AI (альтернатива)
```python
from google.cloud import documentai_v1 as documentai

client = documentai.DocumentProcessorServiceClient()
processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"

# Обработка документа
request = documentai.ProcessRequest(
    name=processor_name,
    raw_document=documentai.RawDocument(content=image_content, mime_type="image/png")
)
result = client.process_document(request=request)
```

#### Option 3: EasyOCR (локальный OCR)
```python
import easyocr
reader = easyocr.Reader(['en', 'ru', 'de'])
results = reader.readtext(slide_path)
```

### Процесс:
```python
# backend/app/services/provider_factory.py
def extract_elements_from_pages(png_paths: List[str]) -> List[List[Dict]]:
    provider = ProviderFactory.get_ocr_provider()  # Google Vision
    return provider.extract_elements_from_pages(png_paths)
```

### Пример результата OCR:
```json
{
  "id": "slide_1_block_0",
  "type": "heading",
  "text": "Physik für Studierende der Biologie",
  "bbox": [452, 276, 546, 245],  // [x, y, width, height]
  "confidence": 0.95
}
```

### Типы элементов:
- `heading` - заголовки
- `paragraph` - текстовые блоки
- `list_item` - элементы списка
- `table` - таблицы
- `table_cell` - ячейки таблиц
- `figure` - графики/изображения

### Результат Stage 1:
Базовый `manifest.json`:
```json
{
  "slides": [
    {
      "id": 1,
      "image": "/assets/{uuid}/slides/001.png",
      "elements": [
        {"id": "slide_1_block_0", "type": "heading", "text": "...", "bbox": [...]},
        {"id": "slide_1_block_1", "type": "paragraph", "text": "...", "bbox": [...]}
      ]
    }
  ]
}
```

---

## 🧠 Stage 0: PRESENTATION INTELLIGENCE

### Что происходит:
LLM анализирует **всю презентацию целиком** для понимания глобального контекста

### API используется:
**`LLM_PROVIDER=gemini` → Vertex AI Gemini**

```python
# backend/workers/llm_gemini.py
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel

aiplatform.init(project=project_id, location="europe-west1")
model = GenerativeModel("gemini-2.0-flash")

response = model.generate_content(
    prompt,
    generation_config={
        "temperature": 0.2,
        "max_output_tokens": 2000
    }
)
```

### Входные данные:
```python
# backend/app/services/presentation_intelligence.py
slides_summary = []
for slide in slides:
    # Первые 5 элементов каждого слайда
    texts = [elem['text'][:100] for elem in slide['elements'][:5]]
    slides_summary.append(f"Slide {i}: {' | '.join(texts)}")
```

### Промпт для LLM:
```
Analyze this presentation and provide structured context.

Presentation: lecture_physics.pdf

Slides summary:
Slide 1: Physik für Studierende | Christian Roos | Institut
Slide 2: Thermodynamik | Entropie | Zweiter Hauptsatz
Slide 3: ...

Provide analysis in JSON:
{
  "theme": "Main theme",
  "subject_area": "Physics/Biology/etc",
  "level": "undergraduate/graduate/high_school",
  "language": "ru/en/de",
  "structure": ["intro", "main_content", "summary"],
  "key_concepts": ["concept1", "concept2"],
  "presentation_style": "academic/corporate/casual"
}
```

### Результат Stage 0:
```json
{
  "presentation_context": {
    "theme": "Physik für Studierende der Biologie",
    "subject_area": "Physics",
    "level": "undergraduate",
    "language": "ru",  // из LLM_LANGUAGE
    "structure": ["intro", "thermodynamics", "entropy", "examples"],
    "key_concepts": ["Thermodynamik", "Entropie", "Energieumwandlung"],
    "presentation_style": "academic",
    "total_slides": 15
  }
}
```

### API Cost:
- **Gemini 2.0 Flash**: ~$0.0001875 / 1K input chars
- Примерная стоимость для 15 слайдов: **~$0.01**

---

## 🔍 Stage 2: SEMANTIC ANALYSIS

### Что происходит:
LLM анализирует **каждый слайд** и создаёт semantic map - карту смысловых групп

### API используется:
**Vertex AI Gemini + Vision (Multimodal)**

```python
# backend/app/services/semantic_analyzer.py
from vertexai.generative_models import GenerativeModel, Part
import base64

# Encode image
with open(slide_image_path, 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')
image_bytes = base64.b64decode(image_base64)
image_part = Part.from_data(data=image_bytes, mime_type="image/png")

# Generate with text + image
response = model.generate_content(
    [prompt, image_part],
    generation_config={
        "temperature": 0.2,
        "max_output_tokens": 3000
    }
)
```

### Входные данные для LLM:
1. **📷 Изображение слайда** (PNG, 1440x1080)
2. **📝 OCR элементы** с координатами
3. **🎯 Presentation context** из Stage 0
4. **📚 Previous slides summary** (2-3 предыдущих слайда)

### Промпт:
```
Analyze this slide and create a semantic map.

You have access to:
1. The slide IMAGE (see attached image)
2. OCR-extracted text with coordinates (below)

Use BOTH visual layout AND OCR data.

PRESENTATION CONTEXT:
- Theme: Physik für Studierende der Biologie
- Level: undergraduate
- Style: academic
- Language: ru
- Slide 3 of 15

OCR ELEMENTS:
- slide_3_block_0: 'Thermodynamik' | type:heading | bbox:[100, 50, 800, 100]
- slide_3_block_1: 'Erster Hauptsatz' | type:paragraph | bbox:[100, 200, 600, 80]
- slide_3_block_2: 'ΔU = Q - W' | type:formula | bbox:[400, 350, 200, 60]

TASK: Group related elements and define highlight strategies.

RETURN JSON:
{
  "slide_type": "content_slide",
  "groups": [
    {
      "id": "group_title",
      "name": "Main Title",
      "type": "title",
      "priority": "high",
      "element_ids": ["slide_3_block_0"],
      "reading_order": [1],
      "educational_intent": "Introduce thermodynamics concept",
      "highlight_strategy": {
        "when": "start",
        "effect_type": "spotlight",
        "duration": 2.5,
        "intensity": "dramatic"
      }
    },
    {
      "id": "group_formula",
      "type": "key_point",
      "priority": "high",
      "element_ids": ["slide_3_block_2"],
      "educational_intent": "Show first law formula",
      "highlight_strategy": {
        "when": "during_explanation",
        "effect_type": "zoom_subtle",
        "duration": 3.0
      }
    }
  ]
}
```

### Результат Stage 2:
```json
{
  "semantic_map": {
    "slide_type": "content_slide",
    "groups": [
      {
        "id": "group_0",
        "name": "Title",
        "type": "title",
        "priority": "high",
        "element_ids": ["slide_3_block_0"],
        "reading_order": [1],
        "educational_intent": "Introduce thermodynamics",
        "highlight_strategy": {
          "when": "start",
          "effect_type": "spotlight",
          "duration": 2.5,
          "intensity": "dramatic"
        }
      },
      {
        "id": "group_1",
        "type": "key_point",
        "priority": "high",
        "element_ids": ["slide_3_block_1", "slide_3_block_2"],
        "educational_intent": "Explain first law",
        "highlight_strategy": {
          "when": "during_explanation",
          "effect_type": "sequential_cascade",
          "duration": 4.0
        }
      }
    ],
    "visual_density": "medium",
    "cognitive_load": "medium"
  }
}
```

### API Cost:
- **Gemini 2.0 Flash с Vision**: ~$0.0001875 / 1K input chars + $0.00075 / 1K output chars
- Примерная стоимость для 1 слайда: **~$0.005**
- Для 15 слайдов: **~$0.075**

---

## 📝 Stage 3: SCRIPT GENERATION

### Что происходит:
LLM генерирует подробный сценарий лекции для каждого слайда

### API используется:
**Vertex AI Gemini (text-only)**

```python
# backend/app/services/smart_script_generator.py
result_text = self.llm_worker.generate(
    prompt=prompt,
    system_prompt=system_prompt,
    temperature=0.3,
    max_tokens=2000
)
```

### Входные данные:
1. **🗺️ Semantic Map** из Stage 2
2. **🎯 Presentation Context** из Stage 0
3. **📚 Previous Slides Summary** - краткое содержание предыдущих слайдов
4. **🔢 Slide Index** - номер текущего слайда

### Промпт:
```
Generate an engaging lecture script for this slide.

PRESENTATION CONTEXT:
- Theme: Physik für Studierende der Biologie
- Level: undergraduate
- Language: ru
- Style: academic
- Slide 3 of 15

PREVIOUS SLIDES SUMMARY:
Slide 2: Мы обсудили основные концепты термодинамики...

CURRENT SLIDE SEMANTIC GROUPS:
- title: Introduce thermodynamics
- key_point: Explain first law
- formula: Show mathematical relationship

CRITICAL RULES:
1. DO NOT read the slide text directly
2. EXPLAIN concepts with your own words
3. Add examples and analogies
4. Use conversational tone
5. Reference previous slides
6. Keep it 30-60 seconds (130-160 words/min)
7. Generate ALL text in "ru" language

RETURN JSON:
{
  "talk_track": [
    {"segment": "hook", "text": "Engaging opening in ru"},
    {"segment": "context", "text": "Link to previous slide"},
    {"segment": "explanation", "text": "Main explanation"},
    {"segment": "example", "text": "Real-world example"},
    {"segment": "emphasis", "text": "Key takeaway"},
    {"segment": "transition", "text": "Transition to next"}
  ],
  "speaker_notes": "Brief summary for speaker",
  "estimated_duration": 45
}
```

### Результат Stage 3:
```json
{
  "talk_track": [
    {
      "segment": "hook",
      "text": "Willkommen zum ersten Teil unserer Reise in die Welt der Physik!"
    },
    {
      "segment": "context",
      "text": "Wir haben gerade über Energie gesprochen. Jetzt schauen wir uns an, wie Energie umgewandelt wird."
    },
    {
      "segment": "explanation",
      "text": "Der erste Hauptsatz der Thermodynamik besagt, dass Energie weder erzeugt noch vernichtet werden kann, sondern nur umgewandelt. Die Formel ΔU = Q - W bedeutet: Die Änderung der inneren Energie eines Systems entspricht der zugeführten Wärme minus der geleisteten Arbeit."
    },
    {
      "segment": "example",
      "text": "Stellt euch vor, ihr erhitzt Wasser in einem Topf. Die Wärme (Q) geht ins Wasser, erhöht seine innere Energie, und wenn es kocht, leistet der Dampf Arbeit (W) gegen den Deckel."
    },
    {
      "segment": "emphasis",
      "text": "Merkt euch: Energie ist unvergänglich - sie ändert nur ihre Form!"
    },
    {
      "segment": "transition",
      "text": "Im nächsten Schritt schauen wir uns an, warum manche Prozesse spontan ablaufen und andere nicht."
    }
  ],
  "speaker_notes": "Erklärung des ersten Hauptsatzes mit Beispiel Wasserkochen",
  "estimated_duration": 45,
  "overlap_score": 0.25  // < 0.35 = passed anti-reading check
}
```

### Anti-Reading Check:
```python
# Проверка, что LLM не просто читает слайд
generated_words = set(talk_track_text.split())
slide_words = set(slide_ocr_text.split())
overlap = len(generated_words ∩ slide_words) / len(generated_words ∪ slide_words)

if overlap > 0.35:
    # Regenerate with stronger instructions
    prompt += "\n\nIMPORTANT: You are READING the slide. EXPLAIN in your own words!"
```

### API Cost:
- ~$0.0001875 / 1K input + $0.00075 / 1K output
- Примерная стоимость для 1 слайда: **~$0.003**
- Для 15 слайдов: **~$0.045**

---

## 🎙️ Stage 4: TTS (Text-to-Speech)

### Что происходит:
Синтез речи из полного сценария `talk_track`

### API используется:
**Google Cloud Text-to-Speech API**

```python
# backend/workers/tts_google.py
from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

# Настройка голоса
voice = texttospeech.VoiceSelectionParams(
    language_code="ru-RU",
    name="ru-RU-Wavenet-D",  # Высококачественный Neural2/Wavenet голос
    ssml_gender=texttospeech.SsmlVoiceGender.MALE
)

# Настройки аудио
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    sample_rate_hertz=22050,
    speaking_rate=1.0,  # Скорость речи
    pitch=0.0           # Высота тона
)

# Синтез
input_text = texttospeech.SynthesisInput(text=full_script)
response = client.synthesize_speech(
    input=input_text,
    voice=voice,
    audio_config=audio_config,
    enable_time_pointing=[texttospeech.SynthesisInput.TimepointType.SSML_MARK]
)

# Сохранение WAV
with open("audio.wav", "wb") as out:
    out.write(response.audio_content)
```

### Входные данные:
```python
# backend/app/pipeline/intelligent.py (Stage 4)
talk_track = slide.get("talk_track", [])
full_script = " ".join([segment.get("text", "") for segment in talk_track])

# Пример full_script:
# "Willkommen zum ersten Teil unserer Reise... Wir haben gerade über Energie..."
# (весь текст из 6 сегментов, ~200-300 слов)
```

### Процесс:
```python
# backend/app/services/provider_factory.py
def synthesize_slide_text_google(texts: List[str]) -> Tuple[str, Dict]:
    provider = ProviderFactory.get_tts_provider()  # Google TTS
    return provider.synthesize_slide_text_google(texts)
```

### Результат Stage 4:
```json
{
  "audio": "/assets/{uuid}/audio/003.wav",
  "duration": 45.3,  // секунды
  "tts_words": {
    "sentences": [
      {"text": "Willkommen zum ersten Teil...", "t0": 0.0, "t1": 3.2},
      {"text": "Wir haben gerade über Energie...", "t0": 3.2, "t1": 6.8},
      ...
    ],
    "words": [
      {"word": "Willkommen", "t0": 0.0, "t1": 0.5},
      {"word": "zum", "t0": 0.5, "t1": 0.7},
      ...
    ]
  }
}
```

### Доступные голоса:
```python
# Русский
"ru-RU-Wavenet-A" (женский)
"ru-RU-Wavenet-B" (мужской)
"ru-RU-Wavenet-C" (женский)
"ru-RU-Wavenet-D" (мужской) ✅ текущий
"ru-RU-Wavenet-E" (женский)

# Немецкий
"de-DE-Neural2-A" (женский)
"de-DE-Neural2-B" (мужской)
"de-DE-Wavenet-A" (женский)

# Английский
"en-US-Neural2-A" (мужской)
"en-US-Neural2-C" (женский)
"en-US-Wavenet-D" (мужской)
```

### API Cost:
- **Wavenet голоса**: $16 / 1M символов
- **Neural2 голоса**: $16 / 1M символов
- **Standard голоса**: $4 / 1M символов
- Примерная стоимость для 1 слайда (300 символов): **~$0.005**
- Для 15 слайдов (4500 символов): **~$0.07**

---

## ✨ Stage 5: VISUAL EFFECTS

### Что происходит:
Генерация временных меток для визуальных эффектов (подсветка элементов)

### Используемая логика:
**Rule-based engine на основе Semantic Map**

```python
# backend/app/services/visual_effects_engine.py
def generate_cues_from_semantic_map(
    semantic_map: Dict,
    elements: List[Dict],
    duration: float,
    tts_words: Dict
) -> List[Dict]:
    
    cues = []
    current_time = 0.0
    
    for group in semantic_map.get('groups', []):
        strategy = group.get('highlight_strategy', {})
        effect_type = strategy.get('effect_type', 'highlight')
        when = strategy.get('when', 'during_explanation')
        duration_sec = strategy.get('duration', 2.0)
        
        # Определяем время на основе 'when'
        if when == 'start':
            t0 = 0.3
        elif when == 'during_explanation':
            t0 = current_time + 0.5
        elif when == 'during_detail':
            t0 = duration * 0.4
        elif when == 'end':
            t0 = duration - duration_sec - 0.5
        else:
            t0 = current_time
        
        t1 = t0 + duration_sec
        
        # Получаем bbox элементов группы
        element_ids = group.get('element_ids', [])
        bbox = get_group_bbox(element_ids, elements)
        
        cue = {
            "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
            "t0": t0,
            "t1": t1,
            "action": effect_type,  # spotlight, highlight, zoom, etc
            "bbox": bbox,
            "element_id": group.get('id'),
            "effect_type": effect_type,
            "intensity": strategy.get('intensity', 'normal')
        }
        cues.append(cue)
        
        current_time = t1
    
    return cues
```

### Типы эффектов:
```python
EFFECT_TYPES = {
    "spotlight":            # Драматическая подсветка (для заголовков)
    "highlight":            # Мягкая подсветка (для текста)
    "zoom_subtle":          # Лёгкое приближение (для формул)
    "sequential_cascade":   # Последовательная подсветка (для списков)
    "group_bracket":        # Скобка для группы элементов
    "blur_others":          # Размытие остальных элементов
    "pointer":              # Указатель (для таблиц/графиков)
    "dimmed_spotlight":     # Приглушённая подсветка
}
```

### Результат Stage 5:
```json
{
  "cues": [
    {
      "cue_id": "cue_99c0abf6",
      "t0": 0.3,
      "t1": 2.8,
      "action": "spotlight",
      "bbox": [100, 50, 800, 100],
      "element_id": "group_title",
      "effect_type": "spotlight",
      "intensity": "dramatic"
    },
    {
      "cue_id": "cue_9dcc97d9",
      "t0": 3.0,
      "t1": 7.0,
      "action": "sequential_cascade",
      "bbox": [100, 200, 600, 300],
      "element_id": "group_list",
      "effect_type": "sequential_cascade",
      "intensity": "normal"
    },
    {
      "cue_id": "cue_be8ca7f8",
      "t0": 8.0,
      "t1": 12.0,
      "action": "zoom_subtle",
      "bbox": [400, 350, 200, 60],
      "element_id": "group_formula",
      "effect_type": "zoom_subtle",
      "intensity": "normal"
    }
  ]
}
```

### Синхронизация с речью:
```python
# Опционально: синхронизация с конкретными словами из TTS
def sync_with_speech(cues, tts_words):
    for cue in cues:
        # Найти ближайшее предложение
        for sentence in tts_words['sentences']:
            if sentence['t0'] <= cue['t0'] <= sentence['t1']:
                cue['synced_text'] = sentence['text']
                break
```

---

## ✅ Stage 6: VALIDATION

### Что происходит:
Проверка и автоматическое исправление ошибок

### Проверки:
```python
# backend/app/services/validation_engine.py

# 1. Semantic Map Validation
def validate_semantic_map(semantic_map, elements, slide_size):
    errors = []
    
    for group in semantic_map['groups']:
        # Проверка: element_ids существуют
        for elem_id in group['element_ids']:
            if elem_id not in [e['id'] for e in elements]:
                errors.append(f"Invalid element_id: {elem_id}")
                group['element_ids'].remove(elem_id)
        
        # Проверка: bbox в пределах слайда
        bbox = get_group_bbox(group['element_ids'], elements)
        if bbox[0] < 0 or bbox[1] < 0:
            errors.append(f"Negative bbox coordinates")
            bbox = [max(0, bbox[0]), max(0, bbox[1]), bbox[2], bbox[3]]
        
        if bbox[0] + bbox[2] > slide_size[0]:
            errors.append(f"Bbox exceeds slide width")
            bbox[2] = slide_size[0] - bbox[0]
    
    return semantic_map, errors

# 2. Cues Validation
def validate_cues(cues, duration, elements):
    errors = []
    
    for cue in cues:
        # Проверка: t0 < t1
        if cue['t0'] >= cue['t1']:
            errors.append(f"Invalid time range: {cue['cue_id']}")
            cue['t1'] = cue['t0'] + 2.0
        
        # Проверка: не выходят за duration
        if cue['t1'] > duration:
            errors.append(f"Cue exceeds duration: {cue['cue_id']}")
            cue['t1'] = duration - 0.1
            cue['t0'] = min(cue['t0'], cue['t1'] - 0.5)
        
        # Проверка: bbox валиден
        bbox = cue.get('bbox', [0, 0, 100, 100])
        if len(bbox) != 4:
            errors.append(f"Invalid bbox format")
            cue['bbox'] = [0, 0, 100, 100]
        
        # Проверка: element_id существует
        elem_id = cue.get('element_id')
        if elem_id and elem_id not in [e['id'] for e in elements]:
            errors.append(f"Invalid element_id in cue")
            cue['invalid_element'] = True
    
    return cues, errors
```

### Автоматические исправления:
- Отрицательные координаты → 0
- Время за пределами duration → обрезка
- Несуществующие element_ids → удаление
- Перекрывающиеся cues → корректировка времени
- Пустые groups → удаление

---

## 📦 Stage 7: BUILD MANIFEST

### Что происходит:
Финальная сборка manifest.json со всеми данными

### Процесс:
```python
# backend/app/pipeline/intelligent.py
def build_manifest(lesson_dir):
    manifest_data = load_manifest(lesson_dir)
    
    # Построение timeline
    timeline = []
    current_time = 0.0
    
    for slide in manifest_data['slides']:
        duration = slide.get('duration', 0.0)
        
        if duration > 0:
            timeline.append({
                "t0": current_time,
                "t1": current_time + duration,
                "action": "slide_change",
                "slide_id": slide['id']
            })
            current_time += duration
    
    manifest_data['timeline'] = timeline
    
    # Очистка временных данных
    for slide in manifest_data['slides']:
        if 'tts_words' in slide:
            del slide['tts_words']
    
    save_manifest(lesson_dir, manifest_data)
```

### Финальный manifest.json:
```json
{
  "presentation_context": {
    "theme": "Physik für Studierende der Biologie",
    "level": "undergraduate",
    "language": "ru",
    "total_slides": 15
  },
  "slides": [
    {
      "id": 1,
      "image": "/assets/{uuid}/slides/001.png",
      "audio": "/assets/{uuid}/audio/001.wav",
      "duration": 29.4,
      "elements": [...],
      "semantic_map": {...},
      "talk_track": [
        {"segment": "hook", "text": "..."},
        {"segment": "context", "text": "..."},
        ...
      ],
      "speaker_notes": "...",
      "cues": [...]
    },
    ...
  ],
  "timeline": [
    {"t0": 0.0, "t1": 29.4, "action": "slide_change", "slide_id": 1},
    {"t0": 29.4, "t1": 58.7, "action": "slide_change", "slide_id": 2},
    ...
  ]
}
```

---

## 💰 Итоговая стоимость обработки

### Для презентации из 15 слайдов:

| Стадия | API | Стоимость |
|--------|-----|-----------|
| Stage 0: Presentation Intelligence | Vertex AI Gemini | $0.01 |
| Stage 1: OCR | Google Vision API | $1.50 / 1000 images → $0.02 |
| Stage 2: Semantic Analysis (×15) | Vertex AI Gemini + Vision | $0.08 |
| Stage 3: Script Generation (×15) | Vertex AI Gemini | $0.05 |
| Stage 4: TTS (×15) | Google TTS Wavenet | $0.07 |
| Stage 5-7: Local processing | - | $0.00 |
| **ИТОГО** | | **~$0.23** |

### Сравнение с OpenRouter:
- **Gemma-3-12b:free**: $0.00 (но медленнее, есть rate limits)
- **GPT-4o-mini**: ~$0.50-1.00 (дороже, но лучше качество)

---

## ⚙️ Конфигурация

### Текущие настройки (docker.env):
```env
# Pipeline
PIPELINE=intelligent

# OCR
OCR_PROVIDER=vision
GCP_PROJECT_ID=inspiring-keel-473421-j2
GCP_LOCATION=us

# LLM
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash
GEMINI_LOCATION=europe-west1
LLM_TEMPERATURE=0.2
LLM_LANGUAGE=ru

# TTS
TTS_PROVIDER=google
GOOGLE_TTS_VOICE=ru-RU-Wavenet-D
GOOGLE_TTS_SPEAKING_RATE=1.0
GOOGLE_TTS_PITCH=0.0

# Auth
GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-sa.json
```

---

## 🔄 Полный flow с временными метками

### Пример для презентации из 3 слайдов:

```
00:00:00 - Пользователь загружает presentation.pdf
00:00:01 - Backend создаёт .data/{uuid}/
00:00:02 - PDF → PNG конвертация (3 слайда)
00:00:05 - Stage 1: OCR всех слайдов через Vision API
00:00:12 - Stage 0: Presentation Intelligence (1 LLM вызов)
00:00:15 - Stage 2: Semantic Analysis слайда 1 (LLM + Vision)
00:00:20 - Stage 3: Script Generation слайда 1 (LLM)
00:00:22 - Stage 4: TTS слайда 1 (Google TTS)
00:00:25 - Stage 5: Visual Effects слайда 1 (local)
00:00:26 - Stage 6: Validation слайда 1 (local)
00:00:27 - [повтор для слайдов 2-3]
00:00:45 - Stage 7: Build final manifest
00:00:46 - Frontend получает готовый manifest.json
00:00:46 - Пользователь видит интерактивную лекцию
```

---

## 🎬 Результат: Интерактивная видео-лекция

### Frontend Player:
```typescript
// src/components/Player.tsx
const Player = () => {
  const [currentSlide, setCurrentSlide] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)
  const audioRef = useRef<HTMLAudioElement>(null)
  
  // Воспроизведение аудио
  useEffect(() => {
    const audio = audioRef.current
    audio.src = slides[currentSlide].audio
    audio.play()
  }, [currentSlide])
  
  // Синхронизация визуальных эффектов
  useEffect(() => {
    const cues = slides[currentSlide].cues
    const activeCues = cues.filter(cue => 
      cue.t0 <= currentTime && currentTime <= cue.t1
    )
    
    // Применяем эффекты
    activeCues.forEach(cue => {
      applyEffect(cue.effect_type, cue.bbox, cue.intensity)
    })
  }, [currentTime])
  
  return (
    <div>
      <img src={slides[currentSlide].image} />
      {/* Визуальные эффекты */}
      <audio ref={audioRef} onTimeUpdate={...} />
    </div>
  )
}
```

### Возможности:
- ▶️ Автоматическое воспроизведение лекции
- ⏸️ Пауза/перемотка
- 📝 Отображение субтитров (из talk_track)
- ✨ Синхронизированные визуальные эффекты
- 🎨 Подсветка важных элементов
- 📊 Прогресс бар с временной шкалой

---

## 🔧 Debugging и мониторинг

### Логи:
```bash
# Backend логи
docker logs slide-speaker-main-backend-1 -f

# Celery worker логи
docker logs slide-speaker-main-celery-1 -f

# Поиск ошибок
docker logs slide-speaker-main-backend-1 2>&1 | grep -i "error\|failed"

# Проверка стадий
docker logs slide-speaker-main-backend-1 2>&1 | grep "Stage"
```

### Примеры логов:
```
✅ Stage 0: Presentation context: Physik für Studierende
🔍 Stage 2: Semantic analysis for slide 1...
✅ Semantic map: 3 groups
📝 Stage 3: Generating script for slide 1...
✅ Script generated (overlap: 0.247)
🎙️ Stage 4: Generating audio for slide 1...
📝 Script length: 287 chars
✅ Audio generated: 29.4s
✨ Stage 5: Generating visual effects for slide 1...
✅ Generated 3 visual cues
```

---

## 📚 Документация API провайдеров

### Google Cloud APIs:
- **Vision API**: https://cloud.google.com/vision/docs
- **Document AI**: https://cloud.google.com/document-ai/docs
- **Vertex AI**: https://cloud.google.com/vertex-ai/docs
- **Text-to-Speech**: https://cloud.google.com/text-to-speech/docs

### Vertex AI Gemini:
- **Models**: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/overview
- **Pricing**: https://cloud.google.com/vertex-ai/generative-ai/pricing

### OpenRouter (альтернатива):
- **API**: https://openrouter.ai/docs
- **Models**: https://openrouter.ai/models

---

## 🚀 Оптимизация производительности

### Параллельная обработка:
```python
# Можно обрабатывать несколько слайдов параллельно
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = []
    for slide in slides:
        future = executor.submit(process_slide, slide)
        futures.append(future)
```

### Кэширование:
- OCR результаты кэшируются по хэшу изображения
- LLM промпты можно кэшировать для похожих слайдов

### Batch обработка:
- OCR может обрабатывать несколько слайдов за один API запрос
- TTS может генерировать аудио для нескольких текстов сразу

---

Это полная документация Intelligent Pipeline! Есть вопросы по конкретной стадии?
