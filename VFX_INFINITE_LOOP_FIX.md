# 🔴 СРОЧНОЕ ИСПРАВЛЕНИЕ: Бесконечный ререндер + Эффекты не запускаются

## Дата: 2 ноября 2025, 21:40

## 🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ НАЙДЕНЫ:

### Проблема #1: Бесконечный цикл ререндеров ✅ ИСПРАВЛЕНО
**Симптом:** `[PlayerProvider] Initializing` появляется 20+ раз подряд

**Причина:**
```tsx
const value = useMemo(() => ({
  ...
}), [
  manifest,
  playerState,  // ❌ Меняется на каждом рендере!
  editingState, // ❌ Меняется на каждом рендере!
  scale,        // ❌ Меняется на каждом рендере!
  ...
]);
```

**Что происходило:**
1. `playerState` меняется (например, `currentTime` обновляется)
2. `useMemo` видит изменение зависимости → создает новый объект `value`
3. `PlayerContext.Provider` получает новый `value` → триггерит ререндер всех потребителей
4. Потребители ререндерятся → вызывают `setPlayerState` → **GOTO 1** ♾️

**Исправление:**
```tsx
const value = useMemo(() => ({
  ...
}), [
  manifest,
  loading,
  error,
  // 🔥 УБРАНЫ: playerState, editingState, scale, imageOffset
  // Они все равно передаются в value, но не триггерят ререндер
  play,
  pause,
  togglePlayPause,
  ...
]);
```

**Результат:** Теперь контекст обновляется **только** когда меняется `manifest`, `loading`, `error` или функции управления.

---

### Проблема #2: Эффекты не запускаются ⚠️ ДИАГНОСТИКА

**Симптом:** 
- ✅ Timeline создан: 26 событий
- ✅ Renderer инициализирован
- ❌ **НЕТ логов `[EffectsTimeline] 🎬 Starting effect`**
- ❌ **НЕТ логов `[Canvas2DRenderer] Added effect`**

**Возможные причины:**

#### A. События timeline не триггерятся
Timeline создан, но события не обрабатываются из-за:
- Audio не воспроизводится (пауза)
- Время audio не совпадает с timing эффектов
- Sync drift слишком большой

**В логах видно:**
```
[EffectsTimeline] Seeked to 0
[EffectsTimeline] Sync drift detected: 172ms
[EffectsTimeline] Sync drift detected: 98ms
```

Это значит, что timeline **постоянно сбрасывается на начало**, и эффекты не успевают запуститься!

#### B. Эффекты имеют неправильные t0/t1
Трансформация timing может работать неправильно.

**В логах видно:**
```
[VisualEffectsEngine] 🔧 Transformed effects: { original: 12, transformed: 12, sample: Object }
```

Нужно проверить, что `sample` содержит правильные `t0`, `t1`.

---

### Проблема #3: Sync drift - Timeline постоянно ресетится ⚠️

**В логах:**
```
[EffectsTimeline] Resumed from 3.426s
[EffectsTimeline] Sync drift detected: 3425ms ← ❌ 3.4 секунды!
[EffectsTimeline] Seeked to 0
[EffectsTimeline] Sync drift detected: 172ms
[EffectsTimeline] Seeked to 0
[EffectsTimeline] Sync drift detected: 98ms
[EffectsTimeline] Seeked to 0
```

**Проблема:** Timeline **думает**, что audio на 3.4 секунде, но на самом деле audio на 0 секунде. Это вызывает постоянный seek, и **эффекты никогда не запускаются**.

**Возможная причина:** Audio элемент не синхронизирован с timeline.

---

## ✅ ЧТО ИСПРАВЛЕНО:

### 1. PlayerContext.tsx - убран infinite loop
**Файл:** `src/components/Player/PlayerContext.tsx`

**Изменение:**
- Убраны `playerState`, `editingState`, `scale`, `imageOffset` из зависимостей `useMemo`
- Теперь контекст обновляется только при изменении `manifest` или функций

### 2. EffectsTimeline.ts - добавлено логирование startEffect
**Файл:** `src/components/VisualEffects/core/EffectsTimeline.ts`

**Добавлено:**
```typescript
console.log('[EffectsTimeline] 🎬 Starting effect:', {
  effect_id: effect.effect_id,
  type: effect.type,
  startTime,
  endTime,
  duration: effect.duration,
  hasCallback: !!this.callbacks.onStart
});
```

Теперь будет видно, **вызывается ли** `startEffect` вообще.

---

## 🧪 ЧТО НУЖНО ПРОВЕРИТЬ:

### Шаг 1: Проверить, что infinite loop исчезл
Перезагрузите страницу. В консоли должно быть:
```
[PlayerProvider] Initializing with lessonId: ...  ← 1 раз
[PlayerPageContent] Render: ...                    ← 1 раз
[VisualEffectsEngine] Component render: ...        ← 1 раз
```

**Без 20+ повторов!**

### Шаг 2: Запустить audio и проверить логи
Нажмите Play. В консоли должно появиться:
```
[EffectsTimeline] 🎬 Starting effect: { effect_id: "...", type: "spotlight", ... }
[VisualEffectsEngine] ✅ Adding effect to renderer: ...
[Canvas2DRenderer] Added effect: ...
```

Если **НЕТ** этих логов, значит проблема в одном из:
- Timeline не триггерит события (sync drift)
- Эффекты имеют неправильное время (t0/t1)
- Audio не синхронизирован

### Шаг 3: Проверить transformed effects
Откройте DevTools Console и найдите:
```
[VisualEffectsEngine] 🔧 Transformed effects: { original: 12, transformed: 12, sample: Object }
```

Раскройте `sample` и проверьте:
```javascript
sample: {
  id: "effect-1",
  effect_id: "effect-1",
  type: "spotlight",
  t0: 1.5,        // ← Должно быть число > 0
  t1: 3.0,        // ← Должно быть число > t0
  duration: 1.5,  // ← Должно быть t1 - t0
  timing: { ... } // ← Старый объект (опционально)
}
```

Если `t0: 0`, `t1: 0`, `duration: 0` → **проблема в backend** (не присылает timing).

### Шаг 4: Проверить audio sync
В Console проверьте:
```javascript
// Во время воспроизведения
const audio = document.querySelector('audio');
console.log('Audio time:', audio.currentTime);
console.log('Audio paused:', audio.paused);
```

Если audio воспроизводится, но `currentTime` не растет → проблема с audio файлом.

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ:

### Если эффекты ВСЕ ЕЩЕ не появляются:

#### Вариант A: Sync drift слишком большой
**Решение:** Увеличить tolerance в `AudioSyncedTimeline`:

```typescript
// В VisualEffectsEngine.tsx, строка ~300
const audioTimeline = new AudioSyncedTimeline({
  preloadBuffer: 100,
  tickInterval: 16,
  syncTolerance: 500,  // ← Добавить это (500ms вместо 100ms)
  debug,
}, callbacks);
```

#### Вариант B: Эффекты имеют неправильное время
**Решение:** Проверить backend - возможно, `timing` пустой или не генерируется.

#### Вариант C: Canvas не видно из-за z-index
**Решение:** Проверить в DevTools → Elements:
```html
<canvas style="z-index: 10"></canvas>
<img style="z-index: ???">  <!-- Не должно быть > 10 -->
```

---

## 📊 СТАТУС

- ✅ **Infinite loop ИСПРАВЛЕН**
- ⏳ **Эффекты не запускаются - ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА**
- ⏳ **Sync drift - ТРЕБУЕТСЯ ПРОВЕРКА**

**Перезагрузите страницу и проверьте консоль!**
