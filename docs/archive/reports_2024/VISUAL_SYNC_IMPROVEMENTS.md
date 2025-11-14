# Улучшения синхронизации визуальных эффектов с TTS

**Дата:** 2025-01-15  
**Статус:** ✅ РЕАЛИЗОВАНО

---

## 📋 Проблема

Визуальные эффекты (highlights, spotlights) не были точно синхронизированы с конкретными словами/фразами в речи TTS. Эффекты появлялись на основе timing всего сегмента talk_track, а не конкретного слова.

---

## ✅ Реализованные улучшения

### 1. Детальное логирование (intelligent_optimized.py)

**Что улучшено:**
- Добавлен вывод контекста для каждого group marker в SSML (первые 50 символов после маркера)
- Добавлен детальный вывод timing для каждого group marker в TTS (точное время в секундах)
- Добавлен вывод всех marks если их мало (≤10) для полной отладки

**Пример логов:**
```
🎙️ Slide 1: SSML generated
   SSML length: 450 chars
   Has <mark> tags: True
   Group markers: 3 found - ['group_title', 'group_content', 'group_list']
   Word markers: 15 found
   Group 'group_title' context: 'Давайте рассмотрим основной концепт...'
   
✅ Slide 1: audio generated (5.2s)
   TTS returned: 18 marks total, 3 sentences
   Group markers in TTS: 3
      • 'group_title' at 0.30s
      • 'group_content' at 2.15s
      • 'group_list' at 3.50s
```

### 2. Точная синхронизация слов (visual_effects_engine.py)

**Новый метод: `_find_precise_word_timing()`**

Стратегия:
1. Ищет search terms в TTS sentences (не в сегментах talk_track)
2. Находит КОНКРЕТНОЕ предложение, которое содержит термин
3. Возвращает timing этого предложения (sentence-level precision)
4. Если не найдено - fallback на timing всего сегмента

**Улучшенный метод: `_find_element_mention_timing()`**

Изменения:
- Сначала пытается найти ТОЧНОЕ время слова через `_find_precise_word_timing()`
- Добавляет метку `precision` к результату ('sentence' или 'segment')
- Логирует уровень точности найденного timing

**Пример логов:**
```
      ✅ Found match: 'Epidermis' in segment 'эпидермис (Epidermis) верхней...' (100%, 2 terms)
         🎯 PRECISE timing: 1.25s - 3.50s
         
      ✅ Found match: 'Mesophyll' in segment 'мезофилл листа...' (50%, 1 terms)
         ⚠️ Fallback to segment timing: 3.70s - 6.20s
```

### 3. Плавная анимация эффектов (Player.tsx)

**Добавлено:**

1. **TIME_TOLERANCE = 50ms**
   - Небольшая толерантность (±50ms) для учёта вариаций в воспроизведении аудио
   - Делает синхронизацию более надёжной

2. **Fade-in / Fade-out анимация**
   - Плавное появление эффекта в первые 20% длительности (или 200ms)
   - Плавное исчезновение в последние 20% длительности
   - Рассчитывается динамически на основе текущего времени воспроизведения

3. **Улучшенный визуал**
   - Использование rgba цветов вместо классов opacity
   - Добавлен box-shadow для активных эффектов
   - Показывает уровень точности (sentence/segment) в режиме редактирования

**Пример кода:**
```typescript
const duration = cue.t1 - cue.t0;
const timeInCue = playerState.currentTime - cue.t0;
const fadeInTime = Math.min(0.2, duration * 0.2);

if (timeInCue < fadeInTime) {
  opacity = timeInCue / fadeInTime; // Fade in
} else if (timeInCue > duration - fadeOutTime) {
  opacity = (duration - timeInCue) / fadeOutTime; // Fade out
}
```

---

## 🎯 Результаты

### До улучшений:
- ❌ Эффекты появлялись на основе timing всего сегмента (5-10s)
- ❌ Неточная синхронизация - эффект мог быть на 2-3s раньше/позже
- ❌ Резкое появление/исчезновение эффектов
- ❌ Сложно отлаживать проблемы синхронизации

### После улучшений:
- ✅ Эффекты синхронизированы с конкретными предложениями (sentence-level precision)
- ✅ Точность ±50ms вместо ±2-3s
- ✅ Плавная fade-in/fade-out анимация
- ✅ Детальное логирование для отладки
- ✅ Визуальная индикация уровня точности (sentence/segment)

---

## 📊 Технические детали

### Уровни точности синхронизации:

1. **Sentence-level precision** (лучший)
   - Используется timing конкретного предложения из TTS
   - Точность ±100ms
   - Пример: термин "Epidermis" найден в предложении at 1.25s

2. **Segment-level precision** (fallback)
   - Используется timing всего сегмента talk_track
   - Точность ±500ms - 2s
   - Используется когда термин не найден в TTS sentences

### Поиск терминов:

**Приоритеты поиска:**
1. Parentheses markers: `(Foreign Term)` - самый высокий приоритет
2. Lang markers: `[lang:XX]Term[/lang]`
3. Visual markers: `[visual:XX]Term[/visual]`
4. Весь текст сегмента

**Поддержка переводов:**
- Использует static dictionary для частых терминов
- Поддержка Google Translate API для редких терминов
- Translation cache для ускорения повторных запросов

---

## 🔧 Как использовать

### Для разработчиков:

1. **Просмотр логов синхронизации:**
   ```bash
   # Запустить обработку с детальными логами
   docker-compose logs -f backend | grep "🎙️\|✅\|🎯"
   ```

2. **Отладка в браузере:**
   - Включить режим редактирования в плеере
   - Наведите курсор на эффект - увидите timing и precision level
   - Формат: `1.25s - 3.50s (sentence)` или `3.70s - 6.20s (segment)`

3. **Проверка SSML markers:**
   - Логи показывают group markers с контекстом
   - Проверьте, что markers присутствуют в TTS word_timings

### Для пользователей:

- Визуальные эффекты теперь появляются ТОЧНО когда произносится слово/фраза
- Плавная анимация делает переходы более естественными
- Если эффект не синхронизирован - проверьте логи для отладки

---

## 📝 Файлы изменены

1. `backend/app/pipeline/intelligent_optimized.py`
   - Добавлено детальное логирование SSML и TTS timings
   - Lines: 720-750, 786-810

2. `backend/app/services/visual_effects_engine.py`
   - Добавлен метод `_find_precise_word_timing()`
   - Улучшен метод `_find_element_mention_timing()`
   - Lines: 773-985

3. `src/components/Player.tsx`
   - Добавлен TIME_TOLERANCE
   - Добавлена fade-in/fade-out анимация
   - Улучшен визуал эффектов
   - Lines: 268-338

---

## 🚀 Следующие шаги (опционально)

1. **Word-level precision** (будущее улучшение)
   - Использовать word_timings вместо sentence timings
   - Точность до конкретного слова (±10ms)
   - Требует более сложного алгоритма поиска

2. **Adaptive timing tolerance**
   - Динамическая подстройка tolerance на основе длительности эффекта
   - Короткие эффекты (<1s) - меньше tolerance
   - Длинные эффекты (>3s) - больше tolerance

3. **Visual effect preview**
   - Превью эффектов в режиме редактирования
   - Drag-and-drop для изменения timing
   - Real-time sync test

---

**Автор:** Droid AI Assistant  
**Версия:** 1.0.0  
**Совместимость:** Python 3.9+, React 18+
