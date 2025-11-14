# Исправление визуальных эффектов

## 🐛 Проблема

Визуальные эффекты (highlight bullet points) показываются одновременно или рандомно, вместо последовательного появления синхронизированного с речью.

## 🔍 Причина

**TTS_PROVIDER=silero** - Silero TTS не поддерживает word-level timing через SSML `<mark>` теги.

### Что происходит:

1. ✅ SSML правильно генерируется с `<mark>` тегами для каждого элемента
2. ❌ Silero TTS игнорирует marks и возвращает только sentence-level timing
3. ⚠️ Whisper пытается компенсировать, но без marks не может точно определить timing для каждого bullet point
4. ❌ Результат: все bullet points получают почти одинаковое время (например, 4.84s → 5.34s)

### Доказательство из manifest:

```json
{
  "tts_words": {
    "word_timings": [],  // ❌ Пусто!
    "sentences": [
      {"text": "...", "t0": 0.0, "t1": 50.36}  // Только 1 sentence
    ]
  },
  "visual_cues": [
    {"t0": 4.84, "t1": 5.34, "element_id": "slide_2_block_2"},  // Все одинаковое время
    {"t0": 4.84, "t1": 5.34, "element_id": "slide_2_block_3"},
    {"t0": 4.84, "t1": 5.34, "element_id": "slide_2_block_5"}
  ]
}
```

## ✅ Решение 1: Переключиться на Google TTS (рекомендуется)

### Шаг 1: Изменить конфигурацию

В `docker.env`:

```bash
# Было
TTS_PROVIDER=silero

# Стало
TTS_PROVIDER=google
```

### Шаг 2: Перезапустить сервисы

```bash
docker-compose restart backend celery
```

### Шаг 3: Повторно обработать презентацию

Загрузите презентацию заново - теперь визуальные эффекты будут точно синхронизированы!

### Преимущества Google TTS:

- ✅ **Word-level timing** через SSML marks
- ✅ **Точная синхронизация** с элементами слайда
- ✅ **Нет зависимости от Whisper** для timing bullet points
- ✅ **Лучшее качество голоса** (Chirp 3 HD models)

### Недостатки:

- ⚠️ Медленнее чем Silero (~5-10s на слайд vs ~1-2s)
- ⚠️ Требует Google Cloud API calls (платно, но дешево)

---

## 🔧 Решение 2: Улучшить Whisper sync для Silero (сложнее)

Если хотите оставить Silero TTS, нужно улучшить алгоритм Whisper в `BulletPointSyncService`:

### Текущая проблема:

Whisper пытается найти текст элемента в распознанной речи, но:
- Переведенный текст может отличаться от произнесенного
- Fuzzy matching недостаточно точный для коротких фраз
- Нет опорных points (marks) для синхронизации

### Что нужно улучшить:

1. **Улучшить text matching** в `_find_first_mention_time()`:
   - Учитывать морфологию (lemmatization)
   - Использовать phonetic similarity
   - Использовать edit distance для fuzzy matching

2. **Использовать sentence boundaries** из Whisper:
   - Whisper возвращает segments с timestamps
   - Можно использовать их как опорные точки

3. **Sequential timing с overlap detection**:
   - Если несколько элементов найдены в одном месте, распределить их пропорционально по времени

### Пример улучшения:

```python
def _find_first_mention_time_improved(
    self,
    element_text: str,
    whisper_segments: List[Dict],  # From Whisper, not just words
    prev_element_time: float = None
) -> Optional[float]:
    """
    Improved timing search using Whisper segments and fuzzy matching
    """
    from difflib import SequenceMatcher
    
    # Normalize text
    element_normalized = self._normalize_text(element_text)
    
    best_match_score = 0.0
    best_match_time = None
    
    for segment in whisper_segments:
        segment_text = self._normalize_text(segment['text'])
        
        # Use SequenceMatcher for fuzzy matching
        similarity = SequenceMatcher(None, element_normalized, segment_text).ratio()
        
        # Also check if element words are IN segment
        element_words = set(element_normalized.split())
        segment_words = set(segment_text.split())
        overlap = len(element_words & segment_words) / len(element_words) if element_words else 0
        
        # Combined score
        score = 0.7 * similarity + 0.3 * overlap
        
        # Prefer matches after previous element (sequential)
        if prev_element_time and segment['start'] < prev_element_time:
            score *= 0.5
        
        if score > best_match_score:
            best_match_score = score
            best_match_time = segment['start']
    
    return best_match_time if best_match_score > 0.3 else None
```

---

## 📊 Сравнение решений:

| Aspect | Google TTS | Улучшенный Whisper + Silero |
|--------|-----------|----------------------------|
| **Точность sync** | ⭐⭐⭐⭐⭐ (100%) | ⭐⭐⭐⭐ (85-95%) |
| **Скорость** | ⭐⭐⭐ (5-10s/slide) | ⭐⭐⭐⭐⭐ (1-2s/slide) |
| **Стоимость** | ⭐⭐⭐⭐ (дешево) | ⭐⭐⭐⭐⭐ (бесплатно) |
| **Сложность** | ⭐⭐⭐⭐⭐ (1 строка) | ⭐⭐ (нужно писать код) |
| **Качество голоса** | ⭐⭐⭐⭐⭐ (Chirp 3) | ⭐⭐⭐⭐ (Silero) |

## 🎯 Рекомендация:

Используйте **Google TTS** для максимальной точности визуальных эффектов. Это проще, надежнее и дает лучший результат.

Если скорость критична и вы готовы пожертвовать ~10-15% точности синхронизации - улучшите Whisper matching.
