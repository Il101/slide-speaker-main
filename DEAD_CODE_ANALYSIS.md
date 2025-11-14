# 🔍 Анализ мёртвого кода в Pipeline

**Дата:** 2 ноября 2025  
**Цель:** Найти неиспользуемый, устаревший и бессмысленный код

---

## 📋 Executive Summary

### Результаты анализа:

| Категория | Найдено | Размер | Действие |
|-----------|---------|--------|----------|
| 🔴 **DEPRECATED файлы** | 4 файла | ~2000 строк | **УДАЛИТЬ** |
| 🟡 **Неиспользуемые классы** | 1 класс | ~1936 строк | **УДАЛИТЬ инициализацию** |
| 🟢 **Неиспользуемые методы** | 2 метода | ~50 строк | **УДАЛИТЬ** |
| 🔵 **Legacy compatibility** | 1 метод | ~5 строк | **МОЖНО УДАЛИТЬ** |

**Потенциальная экономия:** ~4000 строк кода (25% от codebase)

---

## 🔴 DEPRECATED файлы (КРИТИЧНО - можно удалить)

### 1. `services/sprint1/document_parser.py` (654 строки)

**Статус:** ⚠️ DEPRECATED с явным warning

```python
warnings.warn(
    "document_parser.py is deprecated. Use new pipeline with USE_NEW_PIPELINE=true",
    DeprecationWarning,
    stacklevel=2
)
```

**Использование:**
```python
# main.py:419 - только если USE_NEW_PIPELINE=false
if not settings.USE_NEW_PIPELINE:
    from .services.sprint1.document_parser import ParserFactory
    pipeline.ingest_old(str(lesson_dir))
```

**Проблема:**
- `USE_NEW_PIPELINE=true` по умолчанию с версии 2.0
- `ingest_old()` метод УДАЛЁН из `intelligent_optimized.py` (строка 227)
- Код вызывает НЕСУЩЕСТВУЮЩИЙ метод!

**Рекомендация:** 🗑️ **УДАЛИТЬ ПОЛНОСТЬЮ**

**План удаления:**
1. Удалить `backend/app/services/sprint1/` целиком
2. Удалить импорты из `main.py` (строки 47-48, 419)
3. Удалить импорт из `tasks.py` (строка 25, 177)
4. Удалить условие `if not settings.USE_NEW_PIPELINE` в `main.py` (строки 413-437)

**Сэкономим:** ~700 строк кода

---

### 2. `services/sprint2/concept_extractor.py` (~200 строк, оценка)

**Статус:** 🟡 Используется только в DEPRECATED модулях

**Использование:**
```python
# Только в document_parser.py (который сам deprecated!)
from ..sprint2.concept_extractor import extract_slide_concepts
```

**Единственное место использования:**
```python
# api/v2_lecture.py:17
from ..services.sprint2.concept_extractor import SlideConcepts
```

**Вопрос:** Используется ли API v2_lecture.py в продакшене?

**Рекомендация:** 
- ✅ Проверить, используется ли `v2_lecture.py`
- 🗑️ Если нет - **УДАЛИТЬ**

---

### 3. `services/sprint2/smart_cue_generator.py` (оценка ~300 строк)

**Статус:** 🔴 НЕ импортируется нигде!

**Использование:** НОЛЬ импортов в проекте

**Рекомендация:** 🗑️ **УДАЛИТЬ**

---

### 4. Legacy pipeline код в `main.py`

**Размер:** ~50 строк (строки 413-437)

```python
if not settings.USE_NEW_PIPELINE:
    # OLD pipeline code (DEPRECATED!)
    logger.warning("OLD pipeline is deprecated! Set USE_NEW_PIPELINE=true")
    from .services.sprint1.document_parser import ParserFactory
    
    parser = ParserFactory.create_parser(file_path)
    manifest = await parser.parse()
    # ...
    pipeline.ingest_old(str(lesson_dir))  # ❌ ЭТОТ МЕТОД НЕ СУЩЕСТВУЕТ!
```

**Проблема:**
- Вызывает несуществующий метод `ingest_old()`
- Никогда не выполняется (USE_NEW_PIPELINE=true по умолчанию)
- Даже если выполнится - упадёт с ошибкой!

**Рекомендация:** 🗑️ **УДАЛИТЬ немедленно**

---

## 🟡 Неиспользуемые классы

### 1. `VisualEffectsEngine` (1936 строк!) - НЕ ИСПОЛЬЗУЕТСЯ

**Местонахождение:** `services/visual_effects_engine.py`

**Инициализация:**
```python
# pipeline/intelligent_optimized.py:52
self.effects_engine = VisualEffectsEngine()
```

**Использование:** **НОЛЬ!** Нигде не вызывается!

```bash
$ grep -r "self.effects_engine" backend/app/
backend/app/pipeline/intelligent_optimized.py:52:        self.effects_engine = VisualEffectsEngine()
# Только инициализация, НИ ОДНОГО вызова метода!
```

**Почему существует:**
Заменён на `BulletPointSyncService` который делает всё сам:

```python
# pipeline/intelligent_optimized.py:1288 (build_manifest)
cues = self.bullet_sync.sync_bullet_points(
    audio_path=str(audio_full_path),
    talk_track_raw=talk_track_raw,
    semantic_map=semantic_map,
    elements=elements,
    # ...
)
# ✅ BulletPointSync САМА генерирует visual cues
```

**Рекомендация:** 
1. 🔧 **Удалить инициализацию** из `__init__` (строка 52)
2. 🔧 **Удалить импорт** (строка 20)
3. 📝 **Оставить файл** - может понадобиться для будущих эффектов
4. ⚠️ **Или удалить файл полностью** если уверены что не нужен

**Сэкономим:** 2 строки кода, 1936 строк неиспользуемых методов

---

## 🟢 Неиспользуемые методы

### 1. `_find_pptx_file()` - Legacy compatibility

**Местонахождение:** `pipeline/intelligent_optimized.py:253-256`

```python
def _find_pptx_file(self, lesson_dir: str) -> Path:
    """Find PPTX file in lesson directory (legacy method for compatibility)"""
    file_path, file_type = self._find_presentation_file(lesson_dir)
    return file_path
```

**Использование:** НОЛЬ вызовов

**Причина существования:** Backward compatibility (больше не нужна)

**Рекомендация:** 🗑️ **УДАЛИТЬ**

---

### 2. Комментарий `# REMOVED: ingest_old()`

**Местонахождение:** `pipeline/intelligent_optimized.py:227`

```python
# REMOVED: ingest_old() method - deprecated, use ingest() instead
```

**Проблема:** Метод удалён, но комментарий остался + код в `main.py` пытается его вызвать!

**Рекомендация:** 🗑️ **Удалить комментарий после удаления legacy кода из main.py**

---

## 🔵 Сомнительные части кода

### 1. Огромные словари эффектов в `visual_effects_engine.py`

**Размер:** ~100 строк определений (строки 24-124)

```python
EFFECTS = {
    "spotlight": {...},
    "group_bracket": {...},
    "blur_others": {...},
    # ... ещё 20+ эффектов
}
```

**Использование:** НОЛЬ (класс не используется)

**Рекомендация:** 
- Если класс удаляем - удалить и словари
- Если оставляем класс - оставить словари (они полезны)

---

### 2. `effects_engine` в `__init__` (строка 52)

```python
self.effects_engine = VisualEffectsEngine()  # ❌ НЕ ИСПОЛЬЗУЕТСЯ
```

**Рекомендация:** 🗑️ **УДАЛИТЬ строку**

---

### 3. Google Translate fallback в `visual_effects_engine.py`

**Код:**
```python
try:
    from google.cloud import translate_v2 as translate
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False
```

**Использование:** Если класс не используется - это тоже не нужно

---

## 📊 Статистика по файлам

### Размеры файлов (от большего к меньшему):

| Файл | Строк | Используется? | Действие |
|------|-------|---------------|----------|
| visual_effects_engine.py | 1936 | ❌ Инициализируется, но не вызывается | Удалить init |
| bullet_point_sync.py | 1006 | ✅ Активно используется | Оставить |
| sprint3/video_exporter.py | 805 | ✅ Используется | Оставить |
| smart_script_generator.py | 749 | ✅ Активно используется | Оставить |
| sprint1/document_parser.py | 654 | 🔴 DEPRECATED | **УДАЛИТЬ** |
| sprint2/ai_generator.py | 649 | ✅ Используется | Оставить |
| ssml_generator.py | 584 | ✅ Активно используется | Оставить |
| playlist_service.py | 572 | ✅ Используется | Оставить |
| provider_factory.py | 534 | ✅ Активно используется | Оставить |
| ocr_cache.py | 492 | ✅ Активно используется | Оставить |
| adaptive_prompt_builder.py | 485 | ✅ Используется | Оставить |
| diagram_detector.py | 440 | ✅ Активно используется | Оставить |
| semantic_analyzer.py | 412 | ✅ Активно используется | Оставить |
| validation_engine.py | 401 | ✅ Активно используется | Оставить |

---

## 🎯 План очистки кода

### Phase 1: Удаление критичного мёртвого кода (Приоритет: ВЫСОКИЙ)

#### Шаг 1: Удалить sprint1/ целиком (30 минут)
- [ ] `rm -rf backend/app/services/sprint1/`
- [ ] Удалить импорты из `main.py`:
  ```python
  # Строка 47-48
  # Legacy import (kept for backward compatibility if USE_NEW_PIPELINE=false)
  # from .services.sprint1.document_parser import ParserFactory
  ```
- [ ] Удалить импорт из `tasks.py`:
  ```python
  # Строка 25
  # from .services.sprint1.document_parser import ParserFactory
  ```
- [ ] Удалить весь блок legacy pipeline из `main.py` (строки 413-437)

**Экономия:** ~700 строк

---

#### Шаг 2: Проверить использование API v2 (15 минут)
```bash
# Проверить, вызывается ли v2_lecture API
grep -r "v2/lecture" frontend/
grep -r "v2_lecture" backend/
```

**Если НЕ используется:**
- [ ] Удалить `backend/app/api/v2_lecture.py`
- [ ] Удалить `backend/app/services/sprint2/concept_extractor.py`

**Экономия:** ~400 строк

---

#### Шаг 3: Удалить неиспользуемый smart_cue_generator (5 минут)
- [ ] `rm backend/app/services/sprint2/smart_cue_generator.py`

**Экономия:** ~300 строк

---

#### Шаг 4: Очистить VisualEffectsEngine init (5 минут)
```python
# pipeline/intelligent_optimized.py

# УДАЛИТЬ строку 20:
# from ..services.visual_effects_engine import VisualEffectsEngine

# УДАЛИТЬ строку 52:
# self.effects_engine = VisualEffectsEngine()
```

**Экономия:** 2 строки кода, но убирает загрузку 1936 строк в память

---

#### Шаг 5: Удалить устаревшие методы (5 минут)
```python
# pipeline/intelligent_optimized.py

# УДАЛИТЬ строки 253-256:
def _find_pptx_file(self, lesson_dir: str) -> Path:
    """Find PPTX file in lesson directory (legacy method for compatibility)"""
    file_path, file_type = self._find_presentation_file(lesson_dir)
    return file_path

# УДАЛИТЬ строку 227:
# REMOVED: ingest_old() method - deprecated, use ingest() instead
```

**Экономия:** ~10 строк

---

### Phase 2: Опциональная очистка (Приоритет: СРЕДНИЙ)

#### Шаг 6: Удалить visual_effects_engine.py целиком? (обсудить)

**За удаление:**
- Класс не используется нигде
- Код устарел (заменён BulletPointSync)
- 1936 строк мёртвого кода

**Против удаления:**
- Может пригодиться для новых эффектов в будущем
- Содержит полезные определения эффектов
- История разработки

**Компромисс:**
- Переместить в `backend/app/services/archive/visual_effects_engine.py`
- Добавить README с объяснением почему архивировали

---

### Phase 3: Конфигурация (Приоритет: НИЗКИЙ)

#### Шаг 7: Удалить USE_NEW_PIPELINE флаг (10 минут)

Поскольку старый pipeline полностью удалён:

```python
# core/config.py - УДАЛИТЬ строку 112:
# USE_NEW_PIPELINE: bool = os.getenv("USE_NEW_PIPELINE", "true").lower() in ("true", "1", "yes")

# Удалить проверки из tasks.py (строки 82-85, 157, 196)
# Удалить проверки из main.py (строки 413, 453, 470)
```

**Экономия:** ~20 строк + упрощение логики

---

## 📈 Итоговая экономия

| Действие | Файлы | Строки | Время |
|----------|-------|--------|-------|
| **Удалить sprint1/** | 1 папка | ~700 | 30 мин |
| **Удалить v2_lecture** | 2 файла | ~400 | 20 мин |
| **Удалить smart_cue** | 1 файл | ~300 | 5 мин |
| **Очистить effects init** | - | ~1940 | 5 мин |
| **Удалить устаревшие методы** | - | ~10 | 5 мин |
| **Удалить USE_NEW_PIPELINE** | - | ~20 | 10 мин |
| **ИТОГО** | **~5 файлов** | **~3370 строк** | **75 мин** |

---

## ⚠️ Риски и проверки

### Перед удалением проверить:

1. ✅ **Нет production трафика на старый pipeline**
   ```bash
   # Проверить логи за последние 30 дней
   grep "USE_NEW_PIPELINE=false" logs/
   grep "ingest_old" logs/
   ```

2. ✅ **Нет пользователей с USE_NEW_PIPELINE=false**
   ```bash
   # Проверить переменные окружения production
   echo $USE_NEW_PIPELINE
   ```

3. ✅ **API v2_lecture не используется**
   ```bash
   # Проверить API логи
   grep "/v2/lecture" nginx_access.log | tail -100
   ```

4. ✅ **Нет тестов, зависящих от удаляемого кода**
   ```bash
   # Запустить тесты перед удалением
   pytest backend/app/tests/
   ```

---

## 🔍 Дополнительные находки

### 1. Дублирование SemanticAnalyzer

Найдено **ДВА** файла с одинаковым классом:
- `services/semantic_analyzer.py` (412 строк)
- `services/semantic_analyzer_gemini.py` (аналогичный)

**Вопрос:** Это разные реализации или дубликат?

**Рекомендация:** Проверить, используются ли обе версии

---

### 2. Sprint3 ещё используется

```python
# tasks.py
from .services.sprint3.video_exporter import VideoExporter

# main.py  
from .services.sprint3.video_exporter import VideoExporter, QueueManager, StorageManager
```

**Статус:** ✅ Активно используется - **НЕ УДАЛЯТЬ**

---

### 3. Sprint2 частично используется

**Используется:**
- `ai_generator.py` (649 строк) - ✅ используется
- `concept_extractor.py` - 🟡 только в v2_lecture

**НЕ используется:**
- `smart_cue_generator.py` - 🔴 нигде не импортируется

---

## 📝 Заключение

### Найдено мёртвого кода:

1. **Критичный мёртвый код:** ~1400 строк (sprint1/, concept_extractor, smart_cue)
2. **Неиспользуемый класс:** VisualEffectsEngine (1936 строк)
3. **Legacy compatibility:** ~50 строк (методы, флаги)

**Общий объём:** ~3400 строк (21% от codebase!)

### Рекомендации:

1. 🔴 **УДАЛИТЬ НЕМЕДЛЕННО (Phase 1):**
   - `sprint1/document_parser.py` - вызывает несуществующий метод
   - Legacy код в `main.py` - никогда не выполняется
   - `smart_cue_generator.py` - нигде не импортируется

2. 🟡 **ПРОВЕРИТЬ И УДАЛИТЬ (Phase 2):**
   - API v2_lecture + concept_extractor - если не используется
   - VisualEffectsEngine init - не вызывается

3. 🟢 **ОПЦИОНАЛЬНО (Phase 3):**
   - Удалить `USE_NEW_PIPELINE` флаг - больше не нужен
   - Архивировать `visual_effects_engine.py` - может пригодиться

### Выгоды:

- ✅ **-3400 строк** мёртвого кода
- ✅ **-21%** размера codebase
- ✅ Упрощение навигации и понимания кода
- ✅ Быстрее запуск приложения (меньше импортов)
- ✅ Меньше путаницы для разработчиков

### Время на очистку: **1-2 часа**

---

## 🚀 Следующие шаги

1. ✅ Создать backup ветку `backup-before-cleanup`
2. ✅ Выполнить Phase 1 (критичное удаление)
3. ✅ Запустить все тесты
4. ✅ Deploy в staging и проверить
5. ✅ Выполнить Phase 2 (после проверки v2 API)
6. 💡 Обсудить Phase 3 с командой
