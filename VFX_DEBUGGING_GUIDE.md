# 🔧 Visual Effects Debugging Guide

**Дата:** 2 ноября 2025  
**Цель:** Найти и исправить проблему с отображением визуальных эффектов

---

## 🐛 Проблема

Визуальные эффекты не видны в плеере, несмотря на то что:
- ✅ Backend генерирует manifest корректно
- ✅ Manifest V2 включён в данные слайда
- ✅ Frontend компонент существует и интегрирован

---

## 🔍 Шаги отладки

### 1. Проверка данных от backend

```bash
# Проверить что manifest есть в данных
docker exec slide-speaker-main-backend-1 cat /app/.data/<lesson-id>/manifest.json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
slide = data['slides'][0]
vfx = slide.get('visual_effects_manifest')
print('Has VFX:', vfx is not None)
if vfx:
    print('Version:', vfx['version'])
    print('Effects:', len(vfx['effects']))
"
```

**Ожидаемый результат:**
```
Has VFX: True
Version: 2.0
Effects: 3
```

---

### 2. Проверка в Browser DevTools

#### Открыть плеер:
```
http://localhost:3000/player/<lesson-id>
```

#### В Console (F12) проверить логи:

**SlideViewer логи:**
```javascript
[SlideViewer] Current slide: {
  slideId: 1,
  hasVisualEffects: true,  // ✅ Должно быть true
  vfxType: "object",       // ✅ Должно быть object
  vfxKeys: ["version", "id", "timeline", "effects", "quality"]
}

[SlideViewer] 🎨 VFX Details: {
  version: "2.0",
  effects: 3,
  timeline_events: 8,
  quality: { score: 94 }
}
```

**VisualEffectsEngine логи:**
```javascript
[VisualEffectsEngine] Component render: {
  hasManifest: true,           // ✅ Должно быть true
  manifestType: "object",
  manifestPreview: {
    version: "2.0",
    effectsCount: 3,
    timelineEventsCount: 8
  },
  hasAudio: true,
  debug: true
}

[VisualEffectsEngine] ✅ Valid manifest, initializing timeline...
[VisualEffectsEngine] Renderer initialized: canvas2d
[VisualEffectsEngine] AudioSyncedTimeline initialized
```

**Если видите ошибки:**
```javascript
❌ [VisualEffectsEngine] NO MANIFEST - skipping timeline init
❌ [VisualEffectsEngine] INVALID MANIFEST STRUCTURE
```

---

### 3. Проверка Canvas Element

В DevTools Elements tab найти:
```html
<canvas 
  style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1000;"
  width="1280" 
  height="720"
></canvas>
```

**Проверить:**
- [ ] Canvas существует в DOM
- [ ] Canvas имеет размеры > 0
- [ ] Canvas имеет `z-index: 1000` (выше слайда)
- [ ] Canvas НЕ имеет `display: none`

**Debug команды в Console:**
```javascript
// Найти canvas
const canvas = document.querySelector('canvas');
console.log('Canvas:', canvas);
console.log('Width:', canvas.width, 'Height:', canvas.height);
console.log('Style:', canvas.style.cssText);
console.log('Computed:', window.getComputedStyle(canvas).cssText);

// Проверить z-index стека
const vfxContainer = canvas.parentElement;
console.log('VFX Container z-index:', window.getComputedStyle(vfxContainer).zIndex);
```

---

### 4. Ручной тест рендеринга

В Console выполнить:
```javascript
// Получить canvas
const canvas = document.querySelector('canvas');
const ctx = canvas.getContext('2d');

// Нарисовать тестовый прямоугольник
ctx.fillStyle = 'rgba(255, 0, 0, 0.5)'; // Красный полупрозрачный
ctx.fillRect(100, 100, 200, 200);

console.log('🔥 Test rectangle drawn at 100,100,200x200');
```

**Если прямоугольник НЕ виден:**
- ❌ Canvas не рендерится вообще
- ❌ Canvas закрыт другим элементом
- ❌ Canvas имеет неправильные размеры

**Если прямоугольник ВИДЕН:**
- ✅ Canvas работает!
- ❌ Проблема в логике рендеринга эффектов

---

### 5. Проверка Timeline Events

```javascript
// В момент когда должен быть эффект (например t=1.0s)
// Проверить что events срабатывают

// Логи должны быть:
[VisualEffectsEngine] ✅ Adding effect to renderer: effect_xxx spotlight
[Canvas2DRenderer] addEffect: effect_xxx (spotlight)
[Canvas2DRenderer] render: 1 active effects
```

**Если логов нет:**
- ❌ Timeline не инициализирован
- ❌ Audio sync не работает
- ❌ Events не привязаны к callbacks

---

### 6. Тестовая страница

Открыть специальную тестовую страницу:
```
http://localhost:3000/vfx-test
```

Эта страница:
- ✅ Использует hardcoded manifest
- ✅ Показывает debug информацию
- ✅ Позволяет управлять timeline вручную
- ✅ Изолирована от остального кода

**Если эффекты работают на /vfx-test но НЕ работают в плеере:**
- Проблема в интеграции с Player component
- Проблема в передаче manifest/audio

**Если эффекты НЕ работают даже на /vfx-test:**
- Проблема в самом VisualEffectsEngine
- Проблема в renderer (Canvas2D/CSS)

---

## 🔧 Возможные проблемы и решения

### Проблема 1: Manifest не передаётся

**Симптомы:**
```javascript
[VisualEffectsEngine] ⚠️ NO MANIFEST - skipping timeline init
```

**Решение:**
```typescript
// В SlideViewer.tsx проверить:
const vfxManifest = currentSlide?.visual_effects_manifest;
console.log('VFX Manifest:', vfxManifest);

// Должно быть object, не null/undefined
```

---

### Проблема 2: Manifest имеет неправильную структуру

**Симптомы:**
```javascript
[VisualEffectsEngine] ❌ INVALID MANIFEST STRUCTURE
```

**Решение:**
```typescript
// Manifest V2 должен иметь:
{
  version: "2.0",
  id: string,
  timeline: {
    events: [...],
    total_duration: number
  },
  effects: [...]
}
```

---

### Проблема 3: Canvas не видим из-за z-index

**Симптомы:**
- Canvas существует, но ничего не видно
- Тестовый прямоугольник не виден

**Решение:**
```css
/* В SlideViewer.tsx убедиться что: */
.vfx-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 10; /* Выше слайда */
}
```

---

### Проблема 4: Audio sync не работает

**Симптомы:**
- Manifest есть, renderer инициализирован
- Но события не срабатывают

**Решение:**
```typescript
// Проверить что audioElement передан:
<VisualEffectsEngine
  manifest={manifest}
  audioElement={audioRef.current}  // ✅ Должен быть HTMLAudioElement
/>

// В Console:
console.log('Audio element:', audioRef.current);
console.log('Current time:', audioRef.current.currentTime);
```

---

### Проблема 5: Renderer не запущен

**Симптомы:**
```javascript
[Canvas2DRenderer] addEffect called but renderer not started
```

**Решение:**
```typescript
// В VisualEffectsEngine.tsx убедиться:
rendererRef.current.start(); // ✅ Вызывается после инициализации
```

---

## 📋 Checklist отладки

### Backend:
- [ ] Manifest генерируется (`docker logs` показывает "✅ VFX manifest generated")
- [ ] Manifest сохранён в файл (проверить через `cat manifest.json`)
- [ ] Manifest имеет правильную структуру V2

### API:
- [ ] API возвращает manifest в response (`/api/lessons/<id>`)
- [ ] Frontend получает manifest (Network tab в DevTools)

### Frontend:
- [ ] SlideViewer логирует "Has VFX: true"
- [ ] VisualEffectsEngine получает manifest
- [ ] VisualEffectsEngine инициализирует renderer
- [ ] VisualEffectsEngine инициализирует timeline
- [ ] Canvas element существует в DOM
- [ ] Canvas имеет размеры > 0
- [ ] Canvas visible (no display:none)
- [ ] Events срабатывают (START/END логи)
- [ ] Renderer.addEffect вызывается
- [ ] Renderer.render рисует на canvas

---

## 🎯 Quick Debug Commands

```javascript
// В Browser Console (F12)

// 1. Проверить manifest
const slides = window.__LESSON_DATA__?.slides || [];
const vfx = slides[0]?.visual_effects_manifest;
console.log('VFX:', vfx);

// 2. Проверить canvas
const canvas = document.querySelector('canvas');
console.log('Canvas:', canvas?.width, 'x', canvas?.height);

// 3. Нарисовать тест
const ctx = canvas?.getContext('2d');
ctx.fillStyle = 'red';
ctx.fillRect(50, 50, 100, 100);

// 4. Проверить audio
const audio = document.querySelector('audio');
console.log('Audio time:', audio?.currentTime);

// 5. Проверить React DevTools
// Найти VisualEffectsEngine component
// Посмотреть props.manifest
```

---

## 💡 Следующие шаги

1. **Запустить пересобранный контейнер:**
   ```bash
   docker-compose up -d
   ```

2. **Открыть тестовую страницу:**
   ```
   http://localhost:3000/vfx-test
   ```
   - Должны увидеть debug панель
   - Нажать Play - эффект должен появиться

3. **Открыть реальный плеер:**
   ```
   http://localhost:3000/player/75dc761d-f4f7-4ecc-8c53-d92a076ffc3c
   ```
   - Открыть DevTools Console
   - Следить за логами
   - Проверить что manifest передаётся

4. **Если не работает - собрать logs:**
   ```bash
   # Browser Console logs
   # Save as vfx-browser-logs.txt
   
   # Backend logs
   docker logs slide-speaker-main-backend-1 2>&1 | grep -i vfx > vfx-backend-logs.txt
   ```

---

**Статус:** 🔄 Контейнеры пересобираются, ждём завершения для тестирования
