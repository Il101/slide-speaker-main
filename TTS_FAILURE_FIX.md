# ✅ TTS Failure Fix - Partial Audio Generation

## Проблема
При обработке презентации некоторые слайды получают аудио, а другие остаются без аудио. Pipeline не показывал детальную информацию о причинах и не пытался исправить ситуацию.

## Коренные причины

### 1. Отсутствие скрипта
**Симптом:** Слайд не получил `talk_track_raw` или `speaker_notes` на этапе plan
**Причины:**
- LLM не сгенерировал текст (ошибка или timeout)
- Semantic analysis вернул пустую структуру
- Script generator пропустил слайд из-за исключения

### 2. TTS Timeout
**Симптом:** Google TTS не ответил в течение 60 секунд
**Причины:**
- Слишком длинный SSML (>5000 символов)
- Сетевые проблемы
- API rate limiting

### 3. TTS Errors
**Симптом:** Исключение при вызове Google TTS API
**Причины:**
- Невалидный SSML
- API credentials проблемы
- Quota exceeded

## Применённые исправления

### 1. OCR Fallback для отсутствующих скриптов
```python
if not talk_track_raw:
    speaker_notes = slide.get("speaker_notes", "")
    if not speaker_notes:
        # ✅ NEW: Generate from OCR elements
        elements = slide.get("elements", [])
        ocr_text = " ".join([e.get('text', '')[:100] for e in elements if e.get('text')])
        
        if not ocr_text:
            logger.error(f"❌ Slide {slide_id}: no script AND no OCR text")
            return (index, None, {}, 0.0, None)
        
        logger.warning(f"⚠️ Slide {slide_id}: using OCR fallback")
        speaker_notes = f"Слайд {slide_id}. {ocr_text[:200]}"
```

**Эффект:** Теперь даже если LLM не сгенерировал скрипт, мы используем текст со слайда для базового TTS.

### 2. Retry механизм для Timeout
```python
except asyncio.TimeoutError:
    logger.error(f"⏱️ Slide {slide_id}: timeout - will retry once")
    # ✅ NEW: Retry once with longer timeout
    try:
        logger.info(f"🔄 Retrying TTS for slide {slide_id}...")
        audio_path, tts_words = await asyncio.wait_for(
            loop.run_in_executor(
                self.executor,
                lambda: GoogleTTSWorkerSSML().synthesize_slide_text_google_ssml(ssml_texts)
            ),
            timeout=90.0  # Longer timeout for retry
        )
    except Exception as retry_error:
        logger.error(f"❌ Retry failed: {retry_error}")
        return (index, None, {}, 0.0, None)
```

**Эффект:** Временные сетевые проблемы или загрузка API не приводят к полному отказу.

### 3. Детальное логирование причин
```python
if not audio_path or not Path(audio_path).exists():
    # ✅ NEW: Log detailed failure info
    slide_id = slides[index]["id"]
    logger.error(f"❌ Slide {slide_id}: TTS failed - no audio file")
    logger.error(f"   - audio_path: {audio_path}")
    logger.error(f"   - talk_track_raw length: {len(slides[index].get('talk_track_raw', []))}")
    logger.error(f"   - speaker_notes length: {len(slides[index].get('speaker_notes', ''))}")
    
    slides[index]["audio"] = None
    slides[index]["duration"] = 0.0
    slides[index]["tts_error"] = "Audio generation failed"
    continue
```

**Эффект:** Теперь в логах видно точную причину отсутствия аудио для каждого слайда.

### 4. Финальный отчёт по ошибкам
```python
# ✅ NEW: Report all failures at the end
failed_slides = [s for s in slides if s.get("audio") is None]
if failed_slides:
    logger.error(f"⚠️ TTS FAILURES: {len(failed_slides)} slides without audio:")
    for slide in failed_slides:
        slide_id = slide.get("id")
        error = slide.get("tts_error", "Unknown error")
        logger.error(f"   - Slide {slide_id}: {error}")

logger.info(f"⚡ TTS completed ({success_count}/{len(slides)} slides)")

if success_count < len(slides):
    logger.warning(f"⚠️ Only {success_count}/{len(slides)} slides have audio")
```

**Эффект:** Один концентрированный отчёт в конце обработки вместо разрозненных ошибок.

## Дополнительные улучшения

### Рекомендация 1: Проверка quota перед обработкой
```python
# TODO: Add quota check before starting TTS batch
def check_google_tts_quota():
    """Check if we have enough TTS quota for all slides"""
    # Get current quota usage
    # Estimate required quota
    # Return True if enough, False otherwise
    pass
```

### Рекомендация 2: Progressive retry с backoff
```python
# TODO: Implement exponential backoff for retries
max_retries = 3
for attempt in range(max_retries):
    try:
        result = await generate_tts()
        break
    except Exception as e:
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            await asyncio.sleep(wait_time)
        else:
            raise
```

### Рекомендация 3: Alternative TTS provider fallback
```python
# TODO: Fallback to Edge TTS if Google TTS fails
try:
    audio = await google_tts.synthesize(text)
except Exception:
    logger.warning("Google TTS failed, trying Edge TTS")
    audio = await edge_tts.synthesize(text)
```

## Тестирование

### Сценарий 1: Пустой скрипт
```bash
# Create test slide with no script but OCR text
# Expected: Uses OCR fallback, generates audio
```

### Сценарий 2: TTS Timeout
```bash
# Simulate timeout (disconnect network briefly)
# Expected: Retries once, potentially succeeds
```

### Сценарий 3: Quota exceeded
```bash
# Process many presentations to exhaust quota
# Expected: Detailed error message, partial results saved
```

## Мониторинг

### Ключевые метрики
- **TTS Success Rate:** `success_count / total_slides`
- **Fallback Usage:** Count of OCR fallback uses
- **Retry Success Rate:** Retries that succeeded / total retries

### Алерты
- ✅ Alert если success rate < 80%
- ✅ Alert если >5 fallbacks за один запуск
- ✅ Alert если >3 timeouts подряд

### Логи для мониторинга
```
grep "TTS FAILURES" celery.log
grep "using OCR fallback" celery.log
grep "Retrying TTS" celery.log
```

## Результаты

### До исправления
- ❌ Слайды без аудио просто пропускались
- ❌ Непонятно почему нет аудио
- ❌ Нет попыток исправить ситуацию
- ❌ Нет финального отчёта

### После исправления
- ✅ OCR fallback для пустых скриптов
- ✅ Retry для временных сбоев
- ✅ Детальное логирование причин
- ✅ Концентрированный отчёт в конце
- ✅ Маркировка failed slides в manifest

---

**Статус:** ✅ Исправления применены и готовы к тестированию
**Дата:** 2025-01-16
**Версия:** 1.1.0
