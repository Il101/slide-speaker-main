# 🔍 Диагностика: Отсутствие визуальных эффектов

**Дата:** 2 ноября 2025  
**Проблема:** Визуальные эффекты не отображаются при воспроизведении презентации

---

## ✅ Что работает

### 1. Backend генерация эффектов ✅
Проверено в базе данных:
```sql
SELECT jsonb_pretty((manifest_data::jsonb -> 'slides' -> 0 -> 'visual_effects_manifest')::jsonb) 
FROM lessons WHERE id = 'db0ecfc2-1d92-4132-97b5-c22d9c6ebdef';
```

**Результат:** Эффекты генерируются корректно:
- ✅ `visual_effects_manifest` присутствует
- ✅ Содержит эффекты типа `spotlight`, `highlight`
- ✅ Timing настроен правильно (t0, t1, duration)
- ✅ Target bbox указаны

**Пример эффекта:**
```json
{
  "id": "effect_eeab61ab",
  "type": "spotlight",
  "params": {
    "color": "#3b82f6",
    "intensity": "normal",
    "beam_width": 1.2
  },
  "target": {
    "bbox": [588, 97, 265, 47],
    "element_id": "slide_1_block_1"
  },
  "timing": {
    "t0": 0.0,
    "t1": 5.0,
    "duration": 5.0,
    "confidence": 0.95
  }
}
```

### 2. Frontend компоненты ✅
- ✅ `VisualEffectsEngine.tsx` импортируется в `SlideViewer.tsx`
- ✅ Компонент рендерится (есть debug логи)
- ✅ Canvas2DRenderer инициализируется

---

## ❌ Проблемы

### Проблема 1: Manifest не передается правильно

**Проверка в SlideViewer.tsx (строки 27-50):**
```tsx
console.log('[SlideViewer] Current slide:', {
  slideIndex: playerState.currentSlide,
  slideId: currentSlide.id,
  hasVisualEffects: !!currentSlide.visual_effects_manifest,
  vfxManifest: currentSlide.visual_effects_manifest
});
```

**Ожидаемое поведение:**
- `hasVisualEffects` должен быть `true`
- `vfxManifest` должен содержать объект с полями: `id`, `effects`, `timeline`, `quality`, `version`

**Возможная проблема:**
- Manifest не загружается с backend
- Поле имеет другое имя в API response

### Проблема 2: Timeline не запускается

**В VisualEffectsEngine.tsx (строки 225-260):**
```tsx
useEffect(() => {
  if (!manifest || !isReady) {
    console.warn('[VisualEffectsEngine] ⚠️ NO MANIFEST - skipping timeline init');
    return;
  }
  
  // Создаём timeline
  // ...
}, [manifest, isReady]);
```

**Проверки:**
1. Проверить в Console: появляется ли `"⚠️ NO MANIFEST"`?
2. Если да → manifest не передается
3. Если нет, но эффектов нет → проблема в timeline

### Проблема 3: Audio element не передается

**В SlideViewer.tsx (строка 117):**
```tsx
<VisualEffectsEngine
  manifest={currentSlide.visual_effects_manifest}
  audioElement={audioRef.current}  // ← Может быть null!
  preferredRenderer="auto"
  debug={import.meta.env.DEV}
/>
```

**Возможная проблема:**
- `audioRef.current` равен `null` при первом рендере
- Timeline не может синхронизироваться с audio

---

## 🔧 План диагностики

### Шаг 1: Проверить Console в браузере

Открыть DevTools (F12) и посмотреть логи:

1. **Ожидаемые логи (если всё работает):**
   ```
   [SlideViewer] Current slide: { hasVisualEffects: true, ... }
   [SlideViewer] 🎨 VFX Details: { version: "2.0", effects: 2, ... }
   [VisualEffectsEngine] Component render: { hasManifest: true, ... }
   [VisualEffectsEngine] ✅ Valid manifest, initializing timeline...
   [VisualEffectsEngine] ✅ Adding effect to renderer: effect_xxx spotlight
   ```

2. **Логи при проблеме с manifest:**
   ```
   [SlideViewer] ⚠️ NO VISUAL EFFECTS MANIFEST!
   [VisualEffectsEngine] ⚠️ NO MANIFEST - skipping timeline init
   ```

3. **Логи при проблеме с audio:**
   ```
   [VisualEffectsEngine] ⚠️ Audio element is null
   ```

### Шаг 2: Проверить API response

Открыть Network tab в DevTools:

1. Найти запрос к `/api/lessons/{id}` или `/api/lessons/{id}/manifest`
2. Посмотреть response body
3. Убедиться, что в `slides[0]` есть поле `visual_effects_manifest`

**Возможная проблема:** API не возвращает `visual_effects_manifest`

### Шаг 3: Проверить Canvas visibility

В Elements tab:

1. Найти `<canvas>` элемент
2. Проверить computed styles:
   - `display` не должен быть `none`
   - `opacity` должен быть `1`
   - `z-index` должен быть больше, чем у слайда
   - `width` и `height` должны быть > 0

**Возможная проблема:** Canvas перекрыт другими элементами

---

## 🚀 Решения

### Решение 1: Убедиться, что API возвращает visual_effects_manifest

**Проверить endpoint:** `backend/app/api/lessons.py`

Найти функцию, которая возвращает lesson manifest:
```python
@router.get("/{lesson_id}/manifest")
async def get_lesson_manifest(...):
    # Должен возвращать slides с visual_effects_manifest
    pass
```

**Исправление (если нужно):**
```python
# Убедиться, что manifest_data сохраняется с visual_effects_manifest
manifest_data = {
    "slides": [
        {
            "id": "slide_1",
            "image": "...",
            "visual_effects_manifest": {...},  # ← Должно быть!
            ...
        }
    ]
}
```

### Решение 2: Добавить fallback для audioRef

**В SlideViewer.tsx:**
```tsx
const audioElement = audioRef.current || undefined;

<VisualEffectsEngine
  manifest={currentSlide.visual_effects_manifest}
  audioElement={audioElement}  // ← Не null, а undefined
  preferredRenderer="auto"
  debug={true}  // ← Всегда показывать debug в dev
/>
```

### Решение 3: Увеличить z-index Canvas

**В VisualEffectsEngine.tsx (строка 413):**
```tsx
<canvas
  ref={canvasRef}
  style={{
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    pointerEvents: 'none',
    zIndex: 9999,  // ← Было 1000, увеличить
  }}
/>
```

### Решение 4: Добавить визуальный тест Canvas

**Временный код в VisualEffectsEngine.tsx для теста:**
```tsx
useEffect(() => {
  if (!canvasRef.current) return;
  
  const ctx = canvasRef.current.getContext('2d');
  if (ctx) {
    // Рисуем красный квадрат для теста
    ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
    ctx.fillRect(100, 100, 200, 200);
    console.log('🔥 [TEST] Canvas should show RED SQUARE at top-left');
  }
}, []);
```

Если красный квадрат видим → Canvas работает, проблема в timeline/эффектах
Если красный квадрат НЕ видим → Canvas перекрыт или не рендерится

---

## 📋 Checklist для пользователя

Выполните эти шаги и сообщите результаты:

- [ ] Открыть презентацию в браузере
- [ ] Открыть DevTools (F12)
- [ ] Перейти на вкладку Console
- [ ] Найти логи от `[SlideViewer]` и `[VisualEffectsEngine]`
- [ ] Проверить: есть ли лог `"⚠️ NO VISUAL EFFECTS MANIFEST!"`?
- [ ] Проверить: есть ли лог `"✅ Valid manifest, initializing timeline..."`?
- [ ] Перейти на вкладку Network
- [ ] Найти запрос к API с манифестом
- [ ] Проверить: содержит ли response поле `visual_effects_manifest`?
- [ ] Перейти на вкладку Elements
- [ ] Найти `<canvas>` элемент
- [ ] Проверить: какие у него размеры (width x height)?
- [ ] Сделать скриншот Console с логами

---

## 🎯 Быстрый тест

Выполните в Console браузера:
```javascript
// Проверить, что canvas существует
document.querySelector('canvas');

// Проверить текущий слайд
const slide = document.querySelector('[aria-label*="Слайд"]');
console.log('Slide element:', slide);

// Проверить manifest в памяти (если доступен)
// (зависит от того, как хранится состояние)
```

---

## 📞 Следующие шаги

1. **Выполнить диагностику** (Checklist выше)
2. **Предоставить логи** из Console
3. **Сообщить результаты** проверок
4. **Применить решения** по порядку

После этого я смогу точно определить проблему и исправить её.
