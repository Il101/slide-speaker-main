# 🔄 Pipeline Refactoring - Progress Summary

## 🎯 Цель Рефакторинга

**Перенести ВСЮ логику обработки в pipeline** - от PPTX до готового видео.

Упростить архитектуру:
- ❌ Убрать дублирование между main.py и pipeline
- ✅ Сделать pipeline полностью самодостаточным
- ✅ Упростить main.py до 30 строк (только upload + celery task)

---

## 📊 Текущий Прогресс

### ✅ Этап 1: Добавить новые методы (ГОТОВО)

**Файлы изменены:**
- `backend/app/pipeline/intelligent_optimized.py` (+177 строк)
- `backend/app/core/config.py` (+4 строки)
- `test_new_pipeline.py` (новый файл)

**Что добавлено:**

1. **Helper методы:**
   - `_find_pptx_file()` - находит PPTX в директории
   - `_convert_pptx_to_png()` - PyMuPDF конвертация

2. **Stage 1 (NEW):**
   - `ingest_v2()` - PPTX → PNG конвертация + создание manifest

3. **Stage 2 (NEW):**
   - `extract_elements_ocr()` - OCR извлечение через Vision API

4. **Feature flag:**
   - `USE_NEW_PIPELINE` - переключение между старым/новым путём

**Статус:** ✅ **Код готов, ждёт тестирования**

---

### ⏳ Этап 2: Протестировать новые методы (СЕЙЧАС)

**Как тестировать:**

```bash
# Быстрый тест
python test_new_pipeline.py

# Или вручную
python -c "
from backend.app.pipeline.intelligent_optimized import OptimizedIntelligentPipeline
from pathlib import Path
import shutil

test_dir = Path('/tmp/test_lesson')
test_dir.mkdir(exist_ok=True)
shutil.copy('test_presentation.pptx', test_dir / 'test.pptx')

pipeline = OptimizedIntelligentPipeline()
pipeline.ingest_v2(str(test_dir))
pipeline.extract_elements_ocr(str(test_dir))

print('✅ Test passed!')
"
```

**Критерии успеха:**
- ✅ PNG файлы созданы
- ✅ manifest.json содержит слайды и elements
- ✅ Нет ошибок

**Статус:** 🔄 **Ждёт выполнения**

---

### 📋 Этапы 3-8 (Планируется)

| Этап | Задача | Приоритет | Статус |
|------|--------|-----------|--------|
| 3 | Добавить feature flag в main.py | Medium | ⏸️ Pending |
| 4 | Протестировать на реальной презентации | Medium | ⏸️ Pending |
| 5 | Переименовать методы (ingest_v2 → ingest) | Low | ⏸️ Pending |
| 6 | Упростить main.py (убрать document_parser) | Low | ⏸️ Pending |
| 7 | Удалить document_parser.py | Low | ⏸️ Pending |
| 8 | VideoBuilder service (опционально) | Low | ⏸️ Pending |

---

## 📁 Структура Изменений

### Текущая Архитектура (До Рефакторинга)

```
main.py (150 строк):
├─ Upload file
├─ PPTX → PNG (ParserFactory)         ← ДУБЛИРОВАНИЕ
├─ OCR extraction (ParserFactory)      ← ДУБЛИРОВАНИЕ
├─ Create manifest                     ← ДУБЛИРОВАНИЕ
├─ Pipeline.ingest() (только валидация!) ← БЕСПОЛЕЗНО
└─ Start Celery task

Pipeline:
├─ Stage 1: Ingest (только валидация)
├─ Stage 2-3: Plan
├─ Stage 4: TTS
└─ Stage 5-8: Build Manifest
```

### Новая Архитектура (После Рефакторинга)

```
main.py (30 строк):
├─ Upload file
├─ Save to disk
└─ Start Celery task → Pipeline делает ВСЁ!

Pipeline:
├─ Stage 1: PPTX → PNG (ingest_v2)           ✅ НОВОЕ
├─ Stage 2: OCR (extract_elements_ocr)       ✅ НОВОЕ
├─ Stage 3: Presentation Context
├─ Stage 4-5: Semantic + Script
├─ Stage 6: TTS
├─ Stage 7-8: Visual Effects + Timeline
└─ Stage 9: Build Video (опционально)        🔮 БУДУЩЕЕ
```

---

## 🔧 Технические Детали

### PPTX → PNG Конвертация

```python
import fitz  # PyMuPDF

doc = fitz.open("presentation.pptx")
for page_num in range(len(doc)):
    page = doc[page_num]
    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    
    with open(f"{page_num+1:03d}.png", "wb") as f:
        f.write(img_data)
```

### OCR Extraction

```python
from backend.app.services.provider_factory import extract_elements_from_pages

elements_data = extract_elements_from_pages([
    "/path/to/001.png",
    "/path/to/002.png"
])

# Fallback на placeholder если OCR не сработал
if not elements_data:
    elements_data = [[{
        "id": "slide_area",
        "type": "placeholder",
        "bbox": [0, 0, 1600, 900]
    }]]
```

---

## 🎯 Преимущества Нового Подхода

### Было (До)
- 🔴 Логика размазана между main.py и pipeline
- 🔴 Дублирование кода (PPTX→PNG в двух местах)
- 🔴 Сложно тестировать (нужен full stack)
- 🔴 Нельзя запустить pipeline отдельно
- 🔴 main.py раздут (150 строк логики)

### Стало (После)
- ✅ Вся логика в pipeline (единое место)
- ✅ Нет дублирования (PPTX→PNG только в pipeline)
- ✅ Легко тестировать (изолированные методы)
- ✅ Pipeline самодостаточен (можно запустить отдельно)
- ✅ main.py минимален (30 строк - только upload)

---

## ⚙️ Environment Variables

```bash
# Feature flag (default: false)
USE_NEW_PIPELINE=true          # Использовать новый путь

# Pipeline settings
PIPELINE_MAX_PARALLEL_SLIDES=5
PIPELINE_MAX_PARALLEL_TTS=10

# OCR provider
OCR_PROVIDER=vision            # vision | google | easyocr

# Google credentials
GOOGLE_APPLICATION_CREDENTIALS=/app/keys/credentials.json
```

---

## 📊 Ожидаемые Результаты

### Производительность
- 🚀 PPTX→PNG: ~0.5-1 сек/слайд
- 🚀 OCR: ~0.5 сек/слайд (с кэшем Redis)
- 🚀 Общее Stage 1+2: ~1-2 сек/слайд

### Качество Кода
- 📉 main.py: 150 → 30 строк (80% меньше)
- 📈 Pipeline: самодостаточный (от PPTX до видео)
- 🧪 Тестируемость: +100% (изолированные методы)

### Поддерживаемость
- ✅ Легко дебажить (все этапы видны в логах)
- ✅ Легко расширять (добавить Stage 9 - Video Builder)
- ✅ Легко тестировать (каждый stage отдельно)

---

## 🚀 Следующие Шаги

### Немедленно:
1. ✅ **Запустить тест:** `python test_new_pipeline.py`
2. ✅ **Проверить результаты:** `/tmp/test_lesson_new_pipeline/`
3. ✅ **Убедиться что работает**

### После успешного теста:
4. ⏭️ **Добавить feature flag в main.py** (Этап 3)
5. ⏭️ **Протестировать на production** с `USE_NEW_PIPELINE=true`
6. ⏭️ **Переименовать методы** (ingest_v2 → ingest)
7. ⏭️ **Удалить старый код** (document_parser.py)

---

## 📝 Документация

**Созданные файлы:**
- `PIPELINE_REFACTORING_PLAN.md` - Полный план рефакторинга
- `REFACTORING_STEP1_COMPLETE.md` - Детали Этапа 1
- `QUICK_TEST_GUIDE.md` - Быстрая инструкция по тестированию
- `REFACTORING_SUMMARY.md` - Этот файл (summary)

**Обновлённые файлы:**
- `backend/app/pipeline/intelligent_optimized.py`
- `backend/app/core/config.py`

**Новые файлы:**
- `test_new_pipeline.py` - Тестовый скрипт

---

## ✅ Checklist

### Этап 1 (Готово)
- [x] Создать helper методы
- [x] Добавить ingest_v2()
- [x] Добавить extract_elements_ocr()
- [x] Добавить feature flag
- [x] Создать тестовый скрипт
- [x] Написать документацию

### Этап 2 (Сейчас)
- [ ] Запустить test_new_pipeline.py
- [ ] Проверить PNG создались
- [ ] Проверить manifest.json корректен
- [ ] Убедиться что OCR работает

### Этапы 3-8 (Будущее)
- [ ] Feature flag в main.py
- [ ] Production тест
- [ ] Переименование
- [ ] Cleanup старого кода
- [ ] VideoBuilder (опционально)

---

## 🎉 Итого

**Этап 1 ЗАВЕРШЁН!** ✅

Новые методы добавлены, feature flag настроен, тесты готовы.

**Готов к тестированию!** 🚀

---

**Автор:** Droid AI Assistant  
**Дата:** 2025-01-06 03:30  
**Статус:** ✅ Step 1 Complete - Ready for Testing
