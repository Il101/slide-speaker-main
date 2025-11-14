# ✅ Визуальные эффекты исправлены

## Проблема

Визуальные эффекты (highlight, underline и др.) не работали из-за нескольких критичных ошибок в pipeline:

### Найденные проблемы:

1. **`duration = None` блокировал генерацию cues**
   - Проверка `if duration == 0` не срабатывала когда `duration = None`
   - Аудио файлы существовали, но duration не был рассчитан

2. **`semantic_map` отсутствовал** 
   - Старые уроки были обработаны без semantic_map
   - build_manifest не мог работать без semantic_map

3. **Неправильный путь к аудио**
   - В manifest было два поля: `audio` (.mp3) и `audio_path` (.wav)
   - Код использовал неправильное поле

4. **Несоответствие полей в fallback_sync**
   - `_fallback_sync` искал `group.get('group_id')` вместо `group.get('id')`
   - Искал `group.get('elements')` вместо `group.get('element_ids')`

5. **Еще одна проверка duration**
   - В timeline generation: `if duration > 0` падала с TypeError при `None`

---

## Решение

### 1. Автоматический расчет duration из аудио файла

**Файл:** `backend/app/pipeline/intelligent_optimized.py`

```python
# ✅ FIX: Calculate duration from audio file if missing
if (not duration or duration == 0) and audio_path:
    audio_filename = Path(audio_path).name
    audio_full_path = lesson_path / "audio" / audio_filename
    
    if audio_full_path.exists():
        try:
            import wave
            with wave.open(str(audio_full_path), 'rb') as audio_file:
                frames = audio_file.getnframes()
                rate = audio_file.getframerate()
                duration = frames / float(rate)
                slide['duration'] = duration
                self.logger.info(f"✅ Calculated duration from audio file: {duration:.2f}s")
        except Exception as e:
            # Fallback to pydub if wave fails
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_full_path))
            duration = len(audio) / 1000.0
            slide['duration'] = duration
```

### 2. Создание простой semantic_map для старых уроков

**Файл:** `backend/app/pipeline/intelligent_optimized.py`

```python
# ✅ FIX: Create simple semantic_map if missing (for old lessons)
if not semantic_map or not semantic_map.get('groups'):
    self.logger.warning(f"⚠️ No semantic_map for slide {slide_id}, creating simple one")
    # Create simple groups from elements (one element = one group)
    simple_groups = []
    for i, elem in enumerate(elements):
        elem_type = elem.get('type', 'text')
        # Skip tiny elements (bullets, dots)
        bbox = elem.get('bbox', [0, 0, 0, 0])
        if len(bbox) >= 4 and (bbox[2] < 20 or bbox[3] < 10):
            continue
        
        group = {
            'id': f'simple_group_{i}',
            'type': 'bullet_list' if elem_type == 'list_item' else elem_type,
            'element_ids': [elem.get('id')],
            'priority': 'normal',
            'highlight_strategy': {
                'when': 'during_explanation',
                'effect_type': 'highlight',
                'duration': 2.0,
                'intensity': 'normal'
            }
        }
        simple_groups.append(group)
    
    semantic_map = {'groups': simple_groups, 'fallback': True}
    slide['semantic_map'] = semantic_map
```

### 3. Правильный путь к аудио

```python
# ✅ FIX: Try audio_path first, then audio (different naming in old vs new pipeline)
audio_path = slide.get('audio_path') or slide.get('audio')
```

### 4. Исправление _fallback_sync

**Файл:** `backend/app/services/bullet_point_sync.py`

```python
# ✅ FIX: If no talk_track segments, create simple sequential cues
if not talk_track_raw or not any(seg.get('group_id') for seg in talk_track_raw):
    logger.warning("No talk_track with group_id, creating simple time-based cues")
    elements_by_id = {elem.get('id'): elem for elem in (elements or [])}
    
    # Distribute groups evenly across time
    total_duration = max((seg.get('end', 0) for seg in talk_track_raw), default=10.0)
    time_per_group = total_duration / max(len(groups), 1)
    current_time = 0.0
    
    for group in groups:
        group_id = group.get('id')  # ✅ Use 'id' not 'group_id'
        element_ids = group.get('element_ids', [])  # ✅ Use 'element_ids'
        
        for elem_id in element_ids:
            elem = elements_by_id.get(elem_id)
            if not elem:
                continue
            
            bbox = elem.get('bbox')
            if not bbox:
                continue
            
            cue = {
                'action': 'highlight',
                'bbox': bbox,
                't0': round(current_time, 2),
                't1': round(min(current_time + 2.0, total_duration), 2),
                'group_id': group_id,
                'element_id': elem_id,
                'timing_source': 'simple_fallback'
            }
            cues.append(cue)
        
        current_time += time_per_group
```

### 5. Исправление проверки duration в timeline

```python
duration = slide.get("duration") or 0.0

if duration and duration > 0:  # ✅ Check for None first
    timeline.append({...})
```

---

## Результаты тестирования

### До исправления:

```
Duration: None
Semantic map groups: 0
Cues: 2 (тестовые хардкод)
Visual cues: 0
```

### После исправления:

```
Duration: 87.22s ✅
Semantic map groups: 5 ✅
Cues: 5 ✅
Visual cues: 5 ✅

First 3 cues:
  1. t0=0.0s, t1=2.0s, action=highlight, bbox=[93, 37]
  2. t0=2.0s, t1=4.0s, action=highlight, bbox=[588, 97]
  3. t0=4.0s, t1=6.0s, action=highlight, bbox=[72, 346]
```

---

## Как работают visual effects сейчас

### Для новых уроков (с полным pipeline):

1. **Semantic Analyzer** создает semantic_map с группами элементов
2. **TTS** генерирует аудио и возвращает word timings
3. **BulletPointSyncService** синхронизирует cues с word timings (Whisper только для Silero TTS)
4. **Visual cues** привязаны к реальному произношению слов

### Для старых уроков (fallback):

1. **build_manifest** автоматически:
   - Рассчитывает duration из audio файла
   - Создает простую semantic_map из элементов
   - Генерирует cues равномерно распределенные по времени

2. **_fallback_sync** создает cues:
   - Каждый элемент = отдельный cue
   - Равномерное распределение по времени
   - Длительность каждого cue: 2 секунды

---

## Frontend интеграция

Player.tsx правильно отображает эффекты:

```typescript
// Рендер cues с правильным масштабированием
const [x, y, width, height] = cue.bbox;
const scaledX = x * scale.x + imageOffset.x;
const scaledY = y * scale.y + imageOffset.y;
const scaledWidth = width * scale.x;
const scaledHeight = height * scale.y;

// Проверка активности с временным допуском
const TIME_TOLERANCE = 0.05; // 50ms
const isActive = playerState.currentTime >= (cue.t0 - TIME_TOLERANCE) && 
                playerState.currentTime <= (cue.t1 + TIME_TOLERANCE);
```

---

## Что нужно для оптимальной работы

### Обязательно:

- ✅ Audio файлы в формате .wav или .mp3
- ✅ Elements с bbox координатами (от OCR)
- ✅ Хотя бы один из: semantic_map ИЛИ talk_track

### Для лучшей синхронизации (опционально):

- 🎯 Google TTS с SSML markers (native word-level timing, no Whisper needed)
- 🎯 Silero TTS + Whisper (fallback for word-level timing)
- 🎯 Full semantic_map с priority и highlight_strategy

---

## Как запустить для существующих уроков

```bash
# Перегенерировать cues для всех уроков
python3 test_visual_effects_fix.py

# Или через API:
# POST /api/lessons/{lesson_id}/rebuild_manifest
```

---

## Измененные файлы

1. `backend/app/pipeline/intelligent_optimized.py` - build_manifest fallbacks
2. `backend/app/services/bullet_point_sync.py` - _fallback_sync fix
3. `test_visual_effects_fix.py` - тестовый скрипт ✨

---

## 📚 Связанная документация

1. **VISUAL_EFFECTS_FIXED.md** (этот файл) - детальное описание исправлений
2. **HTTPX_CONFLICT_SOLUTION.md** - решение конфликта зависимостей
3. **TRANSLATION_VISUAL_EFFECTS_FLOW.md** - архитектура перевода
4. **VISUAL_EFFECTS_COMPLETE_FIX_SUMMARY.md** - полный summary
5. **WHISPER_VS_GOOGLE_TTS_TIMING.md** - когда используется Whisper (уточнение) ✨

---

**Статус:** ✅ ИСПРАВЛЕНО И ПРОТЕСТИРОВАНО

**Дата:** 2025-01-15

**Автор:** Droid AI Assistant
