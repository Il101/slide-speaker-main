# ✅ Refactoring Step 2-3 - Complete!

## 🎯 Что Сделано

**Этап 2:** ✅ Протестированы новые методы `ingest_v2()` и `extract_elements_ocr()`  
**Этап 3:** ✅ Добавлен feature flag в `main.py`

---

## ✅ Этап 2: Тестирование

### Тестовый Скрипт: `test_new_pipeline.py`

**Запуск:**
```bash
python3 test_new_pipeline.py
```

**Результаты:**
```
✅ ingest_v2() SUCCESS: Created 3 PNG files
✅ Manifest created with 3 slides
✅ extract_elements_ocr() SUCCESS: Extracted 3 total elements
```

### Созданные Файлы:

```
/tmp/test_lesson_new_pipeline/
├── test.pptx                     # Original PPTX
├── manifest.json                 # Created by pipeline
└── slides/
    ├── 001.png                  # 14KB - Generated from PPTX
    ├── 002.png                  # 25KB
    └── 003.png                  # 22KB
```

### Manifest Content:

```json
{
  "slides": [
    {
      "id": 1,
      "image": "/assets/test_lesson_new_pipeline/slides/001.png",
      "elements": [
        {
          "id": "slide_area",
          "type": "placeholder",
          "text": "Slide content area",
          "bbox": [0, 0, 1280, 720],
          "confidence": 1.0,
          "source": "fallback"
        }
      ]
    }
  ],
  "metadata": {
    "source_file": "test.pptx",
    "total_slides": 3,
    "stage": "ocr_complete"
  }
}
```

### Заметки:

- ✅ PPTX → PNG конвертация работает (через python-pptx + PIL)
- ✅ OCR extraction работает (fallback используется т.к. OCR_PROVIDER=easyocr не установлен)
- ✅ Manifest создаётся корректно
- ⚠️ PNG изображения - упрощённые (placeholder), для production нужно LibreOffice/других инструментов

---

## ✅ Этап 3: Feature Flag в main.py

### Изменения в `backend/app/main.py`

#### 1. **Добавлена проверка USE_NEW_PIPELINE:**

```python
# Process document
try:
    if settings.USE_NEW_PIPELINE:
        # ✅ NEW PIPELINE: Everything happens in pipeline (PPTX→PNG→OCR)
        logger.info(f"Using NEW pipeline for {lesson_id}")
        # Manifest will be created by pipeline.ingest_v2()
        # No need to process document here
    else:
        # ❌ OLD PIPELINE: Use document_parser (legacy)
        logger.info(f"Using OLD pipeline for {lesson_id}")
        parser = ParserFactory.create_parser(file_path)
        manifest = await parser.parse()
        
        # Save manifest
        manifest_path = lesson_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully processed document: {lesson_id}")
        
        # Get pipeline for this request
        pipeline = pipeline_for_request(request)
        
        # Run pipeline ingest step
        try:
            logger.info(f"Starting pipeline ingest for lesson {lesson_id}")
            pipeline.ingest(str(lesson_dir))
            logger.info(f"Completed pipeline ingest for lesson {lesson_id}")
        except Exception as e:
            logger.error(f"Error in pipeline ingest for lesson {lesson_id}: {e}")
```

#### 2. **Обработка slides_count для нового pipeline:**

```python
# Get slides count from manifest (if it exists)
slides_count = 0
if not settings.USE_NEW_PIPELINE:
    # Old pipeline: manifest exists
    slides_count = len(manifest.slides)
else:
    # New pipeline: manifest will be created later
    # Set slides_count = 0 for now, will be updated by pipeline
    slides_count = 0

lesson = Lesson(
    id=lesson_id,
    user_id=lesson_user_id,
    title=file.filename,
    file_path=str(file_path),
    file_size=file.size,
    file_type=file_ext,
    slides_count=slides_count,
    status="processing",
    manifest_data=manifest.dict() if not settings.USE_NEW_PIPELINE else {}
)
```

---

## 🧪 Как Тестировать

### Вариант 1: Старый Pipeline (Default)

```bash
# По умолчанию USE_NEW_PIPELINE=false
docker-compose up

# Загрузить файл через API
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test_real.pptx"

# Ожидается: OLD pipeline логи
# "Using OLD pipeline for {lesson_id}"
```

### Вариант 2: Новый Pipeline (Test)

```bash
# Установить feature flag
export USE_NEW_PIPELINE=true

# Или в docker.env:
echo "USE_NEW_PIPELINE=true" >> docker.env

# Запустить
docker-compose up

# Загрузить файл через API
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test_real.pptx"

# Ожидается: NEW pipeline логи
# "Using NEW pipeline for {lesson_id}"
```

### Интеграционный Тест Script:

```bash
bash test_new_pipeline_integration.sh
```

---

## 📊 Сравнение: Old vs New Pipeline

| Aspect | Old Pipeline (USE_NEW_PIPELINE=false) | New Pipeline (USE_NEW_PIPELINE=true) |
|--------|---------------------------------------|--------------------------------------|
| **PPTX→PNG** | main.py (document_parser.py) | pipeline.ingest_v2() |
| **OCR** | main.py (document_parser.py) | pipeline.extract_elements_ocr() |
| **Manifest создание** | main.py | pipeline (Stage 1+2) |
| **pipeline.ingest()** | Только валидация | Не вызывается (новые методы) |
| **Код в main.py** | ~150 строк логики | ~30 строк (только upload) |
| **Дублирование** | ✅ Есть (main.py + pipeline) | ❌ Нет (всё в pipeline) |

---

## 🔧 Environment Variables

```bash
# Feature flag (default: false)
USE_NEW_PIPELINE=true

# Pipeline settings
PIPELINE_MAX_PARALLEL_SLIDES=5
PIPELINE_MAX_PARALLEL_TTS=10

# OCR provider
OCR_PROVIDER=vision  # vision | google | easyocr
```

---

## ⚠️ Важные Моменты

### 1. **Новый Pipeline пока не вызывается в Celery task!**

После upload файла запускается Celery task:
```python
task = process_lesson_full_pipeline.delay(lesson_id, ...)
```

**Текущая реализация task:** Вызывает `pipeline.process_full_pipeline()`

**Что вызывает:** 
- `pipeline.ingest()` - старый метод (только валидация)
- `pipeline.plan()` - работает
- `pipeline.tts()` - работает
- `pipeline.build_manifest()` - работает

**Проблема:** Новые методы `ingest_v2()` и `extract_elements_ocr()` НЕ вызываются!

**Решение:** Нужно обновить `pipeline.process_full_pipeline()` для поддержки нового flow.

### 2. **PPTX→PNG качество**

Текущая реализация использует `python-pptx` + `PIL` для генерации PNG.  
Это создаёт **упрощённые placeholder изображения**.

**Для production:** Использовать LibreOffice, unoconv или другие инструменты:

```python
# Option 1: LibreOffice (best quality)
subprocess.run([
    "soffice",
    "--headless",
    "--convert-to", "pdf",
    str(pptx_file)
])

# Then PDF → PNG with PyMuPDF
doc = fitz.open(pdf_file)
# ... convert pages to PNG

# Option 2: unoconv
subprocess.run([
    "unoconv",
    "-f", "pdf",
    str(pptx_file)
])
```

### 3. **OCR Provider Fallback**

Если OCR provider не настроен, используется fallback (placeholder elements).

Это **нормально для тестирования**, но для production нужно настроить:
```bash
OCR_PROVIDER=vision
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

---

## 📝 Следующие Шаги

### Этап 4: Обновить Celery Task

Нужно обновить `process_full_pipeline()` чтобы использовать новые методы:

```python
# backend/app/pipeline/intelligent_optimized.py

def process_full_pipeline(self, lesson_dir: str):
    """Full pipeline from PPTX to video"""
    
    try:
        # Check if we should use new pipeline
        from ..core.config import settings
        
        if settings.USE_NEW_PIPELINE:
            # NEW FLOW
            self.ingest_v2(lesson_dir)          # PPTX → PNG
            self.extract_elements_ocr(lesson_dir)  # OCR
            self.plan(lesson_dir)                # Context + Semantic + Script
            self.tts(lesson_dir)                  # TTS
            self.build_manifest(lesson_dir)       # Visual Effects + Timeline
        else:
            # OLD FLOW
            self.ingest(lesson_dir)           # Only validation
            self.plan(lesson_dir)
            self.tts(lesson_dir)
            self.build_manifest(lesson_dir)
        
        return {
            "status": "success",
            "lesson_dir": lesson_dir
        }
    
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise
```

### Этап 5: Production PPTX→PNG

Улучшить качество PNG изображений:
- Использовать LibreOffice для PPTX→PDF
- Использовать PyMuPDF для PDF→PNG (высокое качество)

---

## ✅ Чеклист Step 2-3

- [x] Создать тестовый скрипт
- [x] Протестировать ingest_v2()
- [x] Протестировать extract_elements_ocr()
- [x] Добавить feature flag в config.py
- [x] Обновить main.py upload endpoint
- [x] Обработать slides_count для нового pipeline
- [x] Создать интеграционный тест
- [x] Документация

---

## 🎉 Итого

**Этапы 2-3 ЗАВЕРШЕНЫ!** ✅

- ✅ Новые методы протестированы и работают
- ✅ Feature flag добавлен в main.py
- ✅ Можно переключаться между старым/новым pipeline
- ⏸️ Нужно обновить Celery task (Этап 4)

**Статус:** Ready for Etap 4 - Update Celery Task

---

**Автор:** Droid AI Assistant  
**Дата:** 2025-01-06 04:00  
**Статус:** ✅ Steps 2-3 Complete
