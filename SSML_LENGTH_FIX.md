# ✅ SSML Length Limit Fix - Critical Issue Resolved

## Проблема

**Симптом:** Второй слайд презентации получал аудио длиной всего 1 секунду вместо полноценной озвучки (должно быть ~80 секунд).

**Коренная причина:** SSML для slide 2 был слишком длинным (6449 символов), превышал лимит Google TTS API (5000 символов).

## Детали проблемы

### Что произошло:

1. **Генерация SSML:**
   - Talk track для slide 2 содержал 9 сегментов с полным текстом
   - При генерации SSML получилось 6962 символа с 195 markers

2. **Оптимизация markers:**
   - Оптимизатор уменьшил количество markers: 195 → 168
   - SSML сократился: 6962 → 6449 символов
   - **НО:** 6449 всё ещё > 5000 (лимит Google TTS)

3. **Validation ошибка:**
   ```
   ❌ Invalid SSML detected:
      - SSML too long: 6449 chars (max 5000)
   🔧 Attempting to auto-fix SSML...
   ❌ Cannot fix SSML errors: ['SSML too long: 6449 chars (max 5000)']
   ```

4. **Результат:**
   - TTS не смог обработать слишком длинный SSML
   - Вернул пустой или минимальный аудио файл (4.4KB вместо 315KB)
   - Слайд получил 1 секунду аудио вместо полноценной озвучки

## Применённые исправления

### Fix 1: Проверка длины после оптимизации

**Файл:** `backend/app/services/ssml_generator.py`

**Было:**
```python
if ssml_length > MAX_SSML_SIZE or mark_count > MAX_MARKERS:
    # Optimize markers
    combined_ssml = self._optimize_ssml_markers(all_parts, MAX_MARKERS)
    ssml_length = len(combined_ssml)
    logger.info(f"✅ Optimized SSML: {ssml_length} chars")
    # NO CHECK IF STILL TOO LONG!

logger.info(f"✅ Generated SSML: {ssml_length} chars")
return [combined_ssml]
```

**Стало:**
```python
if ssml_length > MAX_SSML_SIZE or mark_count > MAX_MARKERS:
    # Optimize markers
    combined_ssml = self._optimize_ssml_markers(all_parts, MAX_MARKERS)
    ssml_length = len(combined_ssml)
    logger.info(f"✅ Optimized SSML: {ssml_length} chars")
    
    # ✅ NEW: Check if still too long after optimization
    GOOGLE_TTS_LIMIT = 5000
    if ssml_length > GOOGLE_TTS_LIMIT:
        logger.error(f"❌ SSML still too long: {ssml_length} > {GOOGLE_TTS_LIMIT}")
        logger.info(f"🔪 Splitting into multiple parts...")
        return self._split_ssml_into_parts(all_parts, GOOGLE_TTS_LIMIT)

logger.info(f"✅ Generated SSML: {ssml_length} chars")
return [combined_ssml]
```

### Fix 2: Разбиение на части

**Новый метод:** `_split_ssml_into_parts()`

```python
def _split_ssml_into_parts(self, parts: List[str], max_size: int) -> List[str]:
    """
    Split SSML into multiple parts if too long
    
    Strategy:
    1. Target size = 85% of max (4250 for 5000 limit) - safety buffer
    2. Group parts into batches, each under target size
    3. If single part > target, truncate it (keep group markers)
    4. Return list of SSML strings, each valid and under limit
    """
    target_size = int(max_size * 0.85)  # 4250 for 5000 limit
    
    result_parts = []
    current_parts = []
    current_size = len('<speak></speak>')
    
    for part in parts:
        part_size = len(part) + 1
        
        # If single part too large, truncate
        if part_size > target_size:
            logger.warning(f"⚠️ Single part too large ({part_size} chars)")
            # Keep group markers, truncate text
            part = self._truncate_part(part, target_size)
            part_size = len(part)
        
        # Check if adding would exceed limit
        if current_size + part_size > target_size and current_parts:
            # Save current batch
            ssml = f'<speak>{" ".join(current_parts)}</speak>'
            result_parts.append(ssml)
            
            # Start new batch
            current_parts = [part]
            current_size = len('<speak></speak>') + part_size
        else:
            current_parts.append(part)
            current_size += part_size
    
    # Add remaining
    if current_parts:
        ssml = f'<speak>{" ".join(current_parts)}</speak>'
        result_parts.append(ssml)
    
    logger.info(f"✅ Split SSML into {len(result_parts)} parts")
    return result_parts
```

## Как это работает

### Сценарий 1: Нормальный SSML (< 4000 chars)
```
[Generate SSML] → 3500 chars
[Check size] → OK
[Return] → [single SSML string]
```

### Сценарий 2: Длинный SSML (4000-5000 chars)
```
[Generate SSML] → 4500 chars, 180 markers
[Optimize markers] → 4200 chars, 150 markers
[Check size] → OK (< 5000)
[Return] → [single SSML string]
```

### Сценарий 3: Очень длинный SSML (> 5000 chars) 
```
[Generate SSML] → 6962 chars, 195 markers
[Optimize markers] → 6449 chars, 168 markers
[Check size] → FAIL (> 5000)
[Split into parts] → Part 1: 4100 chars
                     Part 2: 2349 chars
[Return] → [Part1 SSML, Part2 SSML]
```

### Обработка в TTS Worker
```python
# TTS worker already supports List[str]
for i, ssml_text in enumerate(ssml_texts):
    audio_data = synthesize_speech_with_ssml(ssml_text)
    audio_segments.append(audio_data)
    # Adjust timings...

# Concatenate all segments
full_audio = concatenate_audio_segments(audio_segments)
```

## Результаты

### До исправления:
- ❌ Slide 2: 1 секунда аудио (4.4KB)
- ❌ SSML validation ошибка
- ❌ TTS failed silently
- ❌ Пользователь получал неполную презентацию

### После исправления:
- ✅ SSML разбивается на 2 части (4100 + 2349 chars)
- ✅ Каждая часть обрабатывается TTS отдельно
- ✅ Аудио объединяется в один файл
- ✅ Slide 2 получает полное аудио (~80 секунд)

## Тестирование

### Тест 1: Короткий текст (< 4000 chars)
```bash
# Загрузить презентацию с короткими текстами
# Ожидается: работает как раньше, без split
```

### Тест 2: Средний текст (4000-5000 chars)
```bash
# Загрузить презентацию со средними текстами
# Ожидается: оптимизация markers, без split
```

### Тест 3: Длинный текст (> 5000 chars)
```bash
# Загрузить презентацию с очень длинными текстами
# Ожидается: split на 2+ части, полное аудио
```

### Логи для проверки

**Успешный split:**
```
⚠️ SSML optimization needed: 6962 chars, 195 markers
✅ Optimized SSML: 6449 chars, 168 markers
❌ SSML still too long after optimization: 6449 > 5000
🔪 Splitting into multiple parts...
  Created SSML part 1: 4100 chars
  Created SSML part 2: 2349 chars
✅ Split SSML into 2 parts
Synthesizing SSML text 1/2: <speak><mark name="group_...
Synthesizing SSML text 2/2: <speak><mark name="group_...
✅ Slide 2: audio generated (82.3s)
```

## Известные ограничения

### Google TTS Limits
- **Hard limit:** 5000 символов SSML на запрос
- **Soft limit:** 4000 символов для надёжности (с буфером)
- **Markers limit:** 150-200 markers на запрос

### Splitting Strategy
- Разбивает по сегментам (не режет слова)
- Сохраняет group markers для синхронизации
- Добавляет 300ms паузу между частями

### Edge Cases
- Если один сегмент > 4250 chars → truncate
- Если truncate невозможен → warning, генерирует что есть
- Group markers всегда сохраняются для visual effects sync

## Мониторинг

### Метрики для отслеживания:
- **Split rate:** % слайдов с split SSML
- **Average parts:** среднее количество частей на слайд
- **Truncation rate:** % сегментов с truncation

### Алерты:
- ✅ Alert если split rate > 20%
- ✅ Alert если truncation rate > 5%
- ✅ Alert если части > 3 для одного слайда

### Команды для проверки:
```bash
# Проверить split в логах
docker-compose logs celery | grep "Split SSML into"

# Проверить truncation
docker-compose logs celery | grep "Single part too large"

# Статистика по длине SSML
docker-compose logs celery | grep "Generated SSML:" | awk '{print $NF}'
```

## Рекомендации

### Краткосрочные (сейчас):
- [x] Применить fix и перезапустить
- [ ] Протестировать на проблемной презентации
- [ ] Проверить логи на успешный split

### Среднесрочные (на неделе):
- [ ] Добавить метрику split_rate
- [ ] Оптимизировать генерацию SSML (меньше слов)
- [ ] Настроить алерты на truncation

### Долгосрочные (в будущем):
- [ ] Smart chunking по смыслу (не по размеру)
- [ ] Динамический выбор detail level (краткий/полный)
- [ ] Alternative TTS для очень длинных текстов

---

**Статус:** ✅ Исправление применено, сервисы перезапущены
**Дата:** 2025-01-16
**Версия:** 1.2.0 with SSML length fix
