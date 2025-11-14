# 🔍 Пошаговая диагностика: Почему нет визуальных эффектов

## Шаг 1: Откройте презентацию в браузере

1. Перейдите на главную страницу: http://localhost:3000
2. Авторизуйтесь (если ещё не авторизованы)
3. Найдите свою загруженную презентацию в списке
4. **Откройте её в плеере**

## Шаг 2: Откройте DevTools

1. Нажмите **F12** (или **Cmd+Option+I** на Mac)
2. Перейдите на вкладку **Console**
3. Очистите консоль (кнопка 🗑️ или Ctrl+L)

## Шаг 3: Проверьте логи при загрузке страницы

Обновите страницу (**Ctrl+R** или **Cmd+R**) и найдите в Console:

### ✅ Ожидаемые логи (если всё работает):

```
[SlideViewer] Current slide: { 
  slideIndex: 0, 
  slideId: "slide_1", 
  hasVisualEffects: true,    ← ДОЛЖНО быть true!
  vfxManifest: {...}
}

[SlideViewer] 🎨 VFX Details: { 
  version: "2.0", 
  effects: 2,                ← Количество эффектов
  timeline_events: 5,
  quality: {...}
}

[VisualEffectsEngine] Component render: { 
  hasManifest: true,         ← ДОЛЖНО быть true!
  manifestType: "object",
  manifestPreview: {...}
}

[VisualEffectsEngine] ✅ Valid manifest, initializing timeline...
[VisualEffectsEngine] ✅ Adding effect to renderer: effect_xxx spotlight
[VisualEffectsEngine] ✅ Adding effect to renderer: effect_yyy highlight
```

### ❌ Проблемные логи (если что-то не так):

**Вариант 1: Нет манифеста**
```
[SlideViewer] ⚠️ NO VISUAL EFFECTS MANIFEST!
[VisualEffectsEngine] ⚠️ NO MANIFEST - skipping timeline init
```
→ **Проблема:** API не возвращает `visual_effects_manifest`

**Вариант 2: Неверная структура манифеста**
```
[VisualEffectsEngine] ❌ INVALID MANIFEST STRUCTURE: { 
  hasTimeline: false,
  hasEffects: false,
  manifestKeys: [...]
}
```
→ **Проблема:** Манифест есть, но в нём нет `timeline` или `effects`

**Вариант 3: Ошибка авторизации**
- В Network tab (вкладка Network) ищем запрос `/lessons/{id}/manifest`
- Если Status: `401` → Не авторизованы
- Если Status: `403` → Нет доступа к этому уроку
- Если Status: `404` → Урок не найден

## Шаг 4: Проверьте Network запросы

1. Перейдите на вкладку **Network** в DevTools
2. Обновите страницу
3. Найдите запрос к `/lessons/.../manifest`
4. Кликните на него
5. Посмотрите:
   - **Status:** должен быть `200 OK`
   - **Response:** должен содержать JSON с `slides[].visual_effects_manifest`

### Как проверить Response:

1. Откройте запрос `/manifest` в Network tab
2. Перейдите на вкладку **Response** или **Preview**
3. Раскройте `slides[0]`
4. Найдите поле `visual_effects_manifest`
5. Раскройте его и проверьте:
   ```json
   {
     "id": "slide_1",
     "version": "2.0",
     "effects": [       ← Должны быть эффекты!
       {
         "id": "effect_...",
         "type": "spotlight",
         ...
       }
     ],
     "timeline": {      ← Должен быть timeline!
       "events": [...]
     }
   }
   ```

## Шаг 5: Проверьте Canvas элемент

1. Перейдите на вкладку **Elements** в DevTools
2. Найдите `<canvas>` элемент (Ctrl+F → введите "canvas")
3. Проверьте его свойства:
   - `width` и `height` должны быть > 0
   - `style` должен содержать `position: absolute`, `z-index: 1000`
   - Элемент должен быть виден на странице

### Как проверить:

```javascript
// Вставьте в Console:
const canvas = document.querySelector('canvas');
console.log('Canvas:', canvas);
console.log('Canvas size:', canvas?.width, 'x', canvas?.height);
console.log('Canvas style:', canvas?.style.cssText);
console.log('Canvas visible:', canvas?.offsetParent !== null);
```

**Ожидаемый результат:**
```
Canvas: <canvas>
Canvas size: 1280 x 720  (или другие значения > 0)
Canvas style: position: absolute; top: 0px; left: 0px; ...
Canvas visible: true
```

## Шаг 6: Воспроизведите аудио

1. Нажмите **Play** (▶️)
2. Смотрите на слайд
3. Должны появиться визуальные эффекты:
   - **Spotlight** - луч света, выделяющий элемент
   - **Highlight** - яркая подсветка элемента
   - **Particles** - анимированные частицы

### Проверьте логи во время воспроизведения:

```
[VisualEffectsEngine] Start effect: effect_xxx spotlight
[VisualEffectsEngine] ✅ Adding effect to renderer: effect_xxx spotlight
...
[VisualEffectsEngine] End effect: effect_xxx spotlight
[VisualEffectsEngine] ✅ Removing effect from renderer: effect_xxx spotlight
```

## 📋 Что сообщить для диагностики:

После выполнения всех шагов, пожалуйста, сообщите:

1. **Что показано в Console:**
   - Есть ли логи `[SlideViewer]`?
   - Что написано в `hasVisualEffects`? (true/false)
   - Есть ли логи `[VisualEffectsEngine]`?
   - Есть ли ошибки (красные сообщения)?

2. **Network tab:**
   - Какой Status у запроса `/manifest`? (200, 401, 403, 404?)
   - Есть ли в Response поле `visual_effects_manifest`?
   - Если да, сколько в нём `effects`?

3. **Canvas:**
   - Найден ли `<canvas>` элемент?
   - Какие у него размеры (width x height)?
   - Виден ли он на странице?

4. **При воспроизведении:**
   - Появляются ли какие-то визуальные изменения на слайде?
   - Есть ли логи "Start effect" в Console?

## 🚀 Быстрая проверка (одна команда в Console):

Вставьте в Console браузера:

```javascript
// Проверка всех компонентов
const results = {
  canvas: !!document.querySelector('canvas'),
  canvasSize: document.querySelector('canvas') ? 
    `${document.querySelector('canvas').width}x${document.querySelector('canvas').height}` : 'N/A',
  vfxEngine: !!document.querySelector('[data-renderer]'),
  renderer: document.querySelector('[data-renderer]')?.getAttribute('data-renderer'),
  ready: document.querySelector('[data-ready]')?.getAttribute('data-ready'),
};
console.table(results);
console.log('Если canvas=false или canvasSize=0x0 → проблема с рендерингом');
console.log('Если ready=false → VisualEffectsEngine не готов');
```

**Скопируйте результат и отправьте мне!**

---

## 🔧 Быстрые исправления

### Если canvas не найден:
1. Убедитесь, что презентация загружена полностью
2. Обновите страницу (Ctrl+R)

### Если Status 401 (Unauthorized):
1. Авторизуйтесь заново
2. Проверьте, что не истёк срок сессии

### Если hasVisualEffects = false:
1. Презентация обрабатывалась старым pipeline (до обновления)
2. Нужно перезагрузить презентацию заново

### Если hasVisualEffects = true, но эффектов нет:
1. Canvas перекрыт другими элементами (проверьте z-index)
2. Timeline не запустился (проверьте логи)
3. Audio элемент не передан (проверьте логи)

---

**Пожалуйста, выполните эти шаги и сообщите результаты!** 🙏
