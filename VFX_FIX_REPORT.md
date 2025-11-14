# 🎨 Visual Effects Debugging Guide - Исправление проблемы

## 🔍 Проблема
Визуальные эффекты не отображаются во фронтенде плеера.

## ✅ Найденная причина
В базе данных эффекты хранятся с **вложенным объектом `timing`**, но фронтенд (VisualEffectsEngine) ожидает **плоские поля** `t0`, `t1`, `duration`.

### Структура в БД (неправильная для фронтенда):
```json
{
  "id": "effect_e42a3d10",
  "type": "spotlight",
  "timing": {
    "t0": 10.5,
    "t1": 15.5,
    "duration": 5.0,
    "confidence": 0.95,
    "source": "talk_track",
    "precision": "segment"
  }
}
```

### Структура для фронтенда (правильная):
```json
{
  "id": "effect_e42a3d10",
  "effect_id": "effect_e42a3d10",
  "type": "spotlight",
  "t0": 10.5,
  "t1": 15.5,
  "duration": 5.0,
  "confidence": 0.95,
  "source": "talk_track",
  "precision": "segment",
  "timing": { ... }  // сохраняется для обратной совместимости
}
```

## 🔧 Исправление
Добавлена трансформация данных в **backend/app/main.py** в функции `get_manifest()`.

### Что делает трансформация:
1. **Добавляет `effect_id`**: создаёт алиас для поля `id`
2. **Расплющивает `timing`**: копирует поля из `timing` на верхний уровень объекта effect
3. **Добавляет алиасы для timeline events**: `t` ↔ `time`, `type` ↔ `event_type`

### Код трансформации:
```python
# backend/app/main.py, строки ~732-780
# 🔥 Transform visual_effects_manifest for frontend compatibility
if "slides" in manifest:
    for slide in manifest["slides"]:
        if "visual_effects_manifest" in slide and slide["visual_effects_manifest"]:
            vfx = slide["visual_effects_manifest"]
            
            # Transform effects: flatten timing object
            if "effects" in vfx and vfx["effects"]:
                for effect in vfx["effects"]:
                    # Add effect_id alias if missing
                    if "id" in effect and "effect_id" not in effect:
                        effect["effect_id"] = effect["id"]
                    
                    # Flatten timing fields if they're nested
                    if "timing" in effect and effect["timing"]:
                        timing = effect["timing"]
                        if "t0" not in effect:
                            effect["t0"] = timing.get("t0", 0)
                        if "t1" not in effect:
                            effect["t1"] = timing.get("t1", 0)
                        # ... и т.д.
```

## 🧪 Тестирование

### 1. Проверка трансформации (CLI)
```bash
python3 test_vfx_transformation.py
```

Ожидаемый результат:
```
✅ Transformation successful!
   Frontend will now receive all required fields
```

### 2. Проверка в браузере

#### Шаг 1: Запустить приложение
```bash
docker-compose up -d
```

#### Шаг 2: Открыть браузер
1. Перейти на http://localhost:5173
2. Войти в систему (если требуется)
3. Открыть урок с ID: `c3bf4454-5711-4020-a767-6e4e6da29ca1`

#### Шаг 3: Открыть DevTools Console
Нажать `F12` или `Cmd+Option+I` (Mac)

#### Шаг 4: Проверить логи

**Должны появиться следующие логи:**

```javascript
// 1. SlideViewer получил данные
[SlideViewer] Current slide: {
  slideIndex: 0,
  slideId: 1,
  hasVisualEffects: true,
  vfxManifest: { version: "2.0", effects: [...], timeline: {...} }
}

[SlideViewer] 🎨 VFX Details: {
  version: "2.0",
  effects: 12,
  timeline_events: 26,
  quality: { ... }
}

// 2. VisualEffectsEngine инициализировался
[VisualEffectsEngine] Component render: {
  hasManifest: true,
  manifestType: "object",
  manifestPreview: {
    version: "2.0",
    id: "slide_1",
    effectsCount: 12,
    timelineEventsCount: 26
  }
}

[VisualEffectsEngine] ✅ Valid manifest, initializing timeline...
[VisualEffectsEngine] 🔧 Transformed effects: {
  original: 12,
  transformed: 12,
  sample: { id: "effect_...", effect_id: "effect_...", t0: 10.5, ... }
}

// 3. Canvas2DRenderer работает
[Canvas2DRenderer] Started
[Canvas2DRenderer] Added effect: effect_e42a3d10 spotlight
```

#### Шаг 5: Проверить визуально
1. Запустить воспроизведение (нажать Play)
2. Должны появиться визуальные эффекты:
   - **Spotlight**: затемнение с "световым лучом" на элементе
   - **Highlight**: подсветка элемента
   - **Pulse**: пульсация
   - **Particles**: частицы

### 3. Проверка API напрямую

**С аутентификацией через cookies:**
```bash
# В браузере после входа откройте DevTools -> Network
# Найдите запрос к /lessons/{id}/manifest
# Скопируйте Cookie header и используйте:

curl -H "Cookie: session=..." \
  http://localhost:8000/lessons/c3bf4454-5711-4020-a767-6e4e6da29ca1/manifest \
  | jq '.slides[0].visual_effects_manifest.effects[0]'
```

Должны увидеть:
```json
{
  "id": "effect_e42a3d10",
  "effect_id": "effect_e42a3d10",  // ← Добавлено трансформацией
  "type": "spotlight",
  "t0": 10.5,                       // ← Расплющено из timing
  "t1": 15.5,                       // ← Расплющено из timing
  "duration": 5.0,                  // ← Расплющено из timing
  "timing": {                       // ← Оригинальный объект сохранён
    "t0": 10.5,
    "t1": 15.5,
    "duration": 5.0,
    "confidence": 0.95,
    "source": "talk_track",
    "precision": "segment"
  }
}
```

## 🐛 Если эффекты всё ещё не работают

### Чеклист проблем:

1. **Backend не перезапущен:**
   ```bash
   docker-compose restart backend
   ```

2. **Браузер кэширует старый manifest:**
   - Hard refresh: `Cmd+Shift+R` (Mac) или `Ctrl+Shift+R` (Windows)
   - Очистить кэш в DevTools -> Network -> Disable cache

3. **Canvas не рисует:**
   - Проверить что canvas element существует в DOM
   - Проверить размеры canvas (не должны быть 0x0)
   - Проверить z-index (должен быть выше изображения)

4. **Timeline не запускается:**
   - Проверить что audioElement передан в VisualEffectsEngine
   - Проверить что audio играет (не в pause)

5. **Effects не добавляются в renderer:**
   - Проверить логи `[Canvas2DRenderer] Added effect`
   - Если нет - проблема в timeline callbacks

## 📝 Debug режим

В `SlideViewer.tsx` уже включен debug overlay (в development):

```tsx
{import.meta.env.DEV && (
  <div className="absolute top-2 left-2 bg-black/80 text-white p-2 text-xs rounded z-50 font-mono">
    <div>VFX: {vfxManifest ? '✅ OK' : '❌ NO MANIFEST'}</div>
    {vfxManifest && (
      <>
        <div>Effects: {vfxManifest.effects?.length || 0}</div>
        <div>Events: {vfxManifest.timeline?.events?.length || 0}</div>
        <div>Version: {vfxManifest.version || 'N/A'}</div>
      </>
    )}
  </div>
)}
```

Если видите:
- `VFX: ✅ OK` - manifest загружен
- `VFX: ❌ NO MANIFEST` - проблема с API или данными

## 🎯 Итоги

✅ **Исправлено:**
- Добавлена трансформация данных в backend API
- Effects теперь имеют плоские поля `t0`, `t1`, `duration`
- Effects имеют `effect_id` для совместимости
- Timeline events имеют алиасы полей

✅ **Тестировано:**
- Трансформация работает корректно
- Структура данных соответствует ожиданиям фронтенда

⏭️ **Следующий шаг:**
- Протестировать в браузере с реальным плеером
- Убедиться что визуальные эффекты отображаются

## 📚 Связанные файлы
- `backend/app/main.py` - трансформация API
- `src/components/Player/SlideViewer.tsx` - рендеринг плеера
- `src/components/VisualEffects/VisualEffectsEngine.tsx` - движок эффектов
- `src/components/VisualEffects/renderers/Canvas2DRenderer.ts` - рендерер
- `test_vfx_transformation.py` - тестовый скрипт
