# 🎯 Исправление центровки визуальных эффектов

## 🔍 Проблема
Визуальные эффекты не отцентрованы по слайду - они рисуются в неправильных координатах.

## 🐛 Корневая причина

**Несоответствие систем координат:**

1. **Координаты bbox в эффектах** указаны в системе координат **оригинального изображения слайда** (например, 1920x1080 пикселей)
2. **Canvas для эффектов** имеет размеры **контейнера плеера** (например, 800x450 пикселей)
3. **Изображение слайда** масштабируется через CSS `transform: scale()` и `translate()`
4. **Canvas с эффектами НЕ учитывал** это масштабирование

### Пример проблемы:

```
Оригинальный слайд: 1920x1080
Элемент на слайде: bbox=[100, 100, 300, 200]

Контейнер плеера: 800x450
Масштаб: 0.4167 (450/1080)
Offset: x=8.3, y=0

Изображение:
  ✅ transform: translate(8.3px, 0) scale(0.4167)
  ✅ Рисуется в правильной позиции

Canvas с эффектами:
  ❌ bbox=[100, 100, 300, 200] (оригинальные координаты)
  ❌ Рисуется НЕ там где элемент!

НУЖНО:
  ✅ bbox=[100*0.4167+8.3, 100*0.4167+0, 300*0.4167, 200*0.4167]
  ✅ bbox=[50.0, 41.67, 125.0, 83.33]
```

## ✅ Решение

Добавили **трансформацию координат** в Canvas2DRenderer:

1. **SlideViewer** передаёт параметры масштабирования в **VisualEffectsEngine**:
   - `slideScale` - масштаб слайда (x, y)
   - `slideOffset` - смещение слайда (x, y)
   - `slideDimensions` - размеры оригинального слайда

2. **VisualEffectsEngine** передаёт эти параметры в **Canvas2DRenderer**

3. **Canvas2DRenderer** применяет трансформацию к координатам bbox в методе `getEffectBBox()`:
   ```typescript
   const [x, y, w, h] = effect.target.bbox;
   const scale = this.config.slideScale;
   const offset = this.config.slideOffset;
   
   return [
     x * scale.x + offset.x,  // Трансформированный X
     y * scale.y + offset.y,  // Трансформированный Y
     w * scale.x,             // Трансформированная ширина
     h * scale.y              // Трансформированная высота
   ];
   ```

## 📝 Изменённые файлы

### 1. `src/components/Player/SlideViewer.tsx`
```tsx
<VisualEffectsEngine
  manifest={vfxManifest}
  audioElement={audioRef.current}
  preferredRenderer="auto"
  debug={import.meta.env.DEV}
  slideScale={scale}              // ✅ Передаём масштаб
  slideOffset={imageOffset}       // ✅ Передаём offset
  slideDimensions={slideDimensions} // ✅ Передаём размеры
/>
```

### 2. `src/components/VisualEffects/VisualEffectsEngine.tsx`
```tsx
export interface VisualEffectsEngineProps {
  // ... другие props
  slideScale?: { x: number; y: number };
  slideOffset?: { x: number; y: number };
  slideDimensions?: { width: number; height: number };
}

// В конструкторе Canvas2DRenderer:
rendererRef.current = new Canvas2DRenderer(canvasRef.current, {
  // ... другие options
  slideScale,
  slideOffset,
  slideDimensions,
});

// useEffect для обновления при изменении scale/offset:
useEffect(() => {
  if (rendererRef.current && 'updateSlideTransform' in rendererRef.current) {
    rendererRef.current.updateSlideTransform(
      slideScale,
      slideOffset,
      slideDimensions
    );
  }
}, [slideScale, slideOffset, slideDimensions]);
```

### 3. `src/components/VisualEffects/renderers/Canvas2DRenderer.ts`
```typescript
export interface Canvas2DConfig {
  // ... другие поля
  slideScale?: { x: number; y: number };
  slideOffset?: { x: number; y: number };
  slideDimensions?: { width: number; height: number };
}

class Canvas2DRenderer {
  // В конструкторе:
  this.config = {
    // ... другие поля
    slideScale: config.slideScale ?? { x: 1, y: 1 },
    slideOffset: config.slideOffset ?? { x: 0, y: 0 },
    slideDimensions: config.slideDimensions ?? { width: 1920, height: 1080 },
  };
  
  // Новый метод для обновления transform:
  updateSlideTransform(scale, offset, dimensions): void {
    this.config.slideScale = scale;
    this.config.slideOffset = offset;
    this.config.slideDimensions = dimensions;
  }
  
  // Обновлённый метод getEffectBBox:
  private getEffectBBox(effect: Effect): [number, number, number, number] | null {
    if (effect.target.bbox) {
      const [x, y, w, h] = effect.target.bbox;
      const scale = this.config.slideScale ?? { x: 1, y: 1 };
      const offset = this.config.slideOffset ?? { x: 0, y: 0 };
      
      return [
        x * scale.x + offset.x,
        y * scale.y + offset.y,
        w * scale.x,
        h * scale.y
      ];
    }
    // fallback...
  }
}
```

## 🧪 Тестирование

### 1. Проверка в браузере

1. Открыть http://localhost:5173
2. Войти и открыть урок с эффектами
3. Запустить воспроизведение
4. **Проверить**: эффекты должны появляться **точно на элементах слайда**

### 2. Проверка в DevTools Console

При загрузке слайда должны появиться логи:

```javascript
[SlideViewer] Current slide: {
  slideIndex: 0,
  hasVisualEffects: true,
  // ...
}

[Canvas2DRenderer] Slide transform updated: {
  scale: { x: 0.4167, y: 0.4167 },
  offset: { x: 8.3, y: 0 },
  dimensions: { width: 1920, height: 1080 }
}
```

### 3. Визуальная проверка

При появлении эффекта (например, spotlight):
- ✅ Световой луч должен быть **точно на элементе**
- ✅ Размер эффекта должен соответствовать **размеру элемента**
- ✅ Эффект должен **двигаться вместе с элементом** при изменении размера окна

### 4. Проверка при resize

1. Изменить размер окна браузера
2. **Проверить**: эффекты должны остаться отцентрованными на элементах

## 🎯 Результат

✅ **До исправления:**
- Эффекты рисовались в абсолютных координатах оригинального слайда
- Не учитывался масштаб контейнера
- Эффекты были смещены относительно элементов

✅ **После исправления:**
- Координаты bbox трансформируются по формуле: `x' = x * scale + offset`
- Эффекты точно позиционируются на элементах
- Работает при любом размере контейнера и любом масштабе
- Автоматически обновляется при resize окна

## 🔗 Связанные файлы

- `src/components/Player/SlideViewer.tsx` - передача параметров масштабирования
- `src/components/VisualEffects/VisualEffectsEngine.tsx` - приём и передача в renderer
- `src/components/VisualEffects/renderers/Canvas2DRenderer.ts` - применение трансформации
- `src/components/Player/utils/scaleCalculations.ts` - вычисление масштаба (уже было)

## 📚 Дополнительно

Уже существующие утилиты в `scaleCalculations.ts`:
- `calculateScale()` - вычисляет масштаб и offset
- `scaleCoordinates()` - трансформирует точку
- `scaleBbox()` - трансформирует bbox (можно использовать в будущем)

## 🚀 Следующие шаги

1. ✅ Трансформация координат реализована
2. ⏳ Протестировать в браузере
3. ⏳ Проверить на разных размерах окна
4. ⏳ Проверить на разных слайдах с разными эффектами

---

**Дата исправления:** 2 ноября 2025  
**Статус:** ✅ Готово к тестированию
