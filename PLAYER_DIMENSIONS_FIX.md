# Исправление позиционирования элементов в режиме Edit (Player.tsx)

## Дата: 2025-11-02

## Проблема
При нажатии кнопки "Edit Edit" в старом Player.tsx зелёные рамки редактирования (highlight boxes) отображались в неправильных позициях.

## Причина
Компонент `Player.tsx` использовал **фиксированные размеры слайда 1920x1080**:
```typescript
const [slideDimensions] = useState({ width: 1920, height: 1080 });
```

Но реальный слайд имел размер **1191x1684** (портретная ориентация), что приводило к неправильному вычислению масштаба и смещению всех элементов.

## Решение

### 1. Добавлено поле metadata в интерфейс Manifest (`src/lib/api.ts`)
```typescript
export interface Manifest {
  // ... existing fields
  metadata?: {
    slide_width?: number;
    slide_height?: number;
    total_slides?: number;
    source_file?: string;
    source_type?: string;
    stage?: string;
    translation_applied?: boolean;
  };
}
```

### 2. Изменен Player.tsx для использования реальных размеров

**Было:**
```typescript
const [slideDimensions] = useState({ width: 1920, height: 1080 });
```

**Стало:**
```typescript
const [slideDimensions, setSlideDimensions] = useState({ width: 1920, height: 1080 });

// В useEffect при загрузке манифеста:
if (data.metadata?.slide_width && data.metadata?.slide_height) {
  const realDimensions = {
    width: data.metadata.slide_width,
    height: data.metadata.slide_height
  };
  setSlideDimensions(realDimensions);
  console.log('[Player] 📐 Using real slide dimensions from manifest:', realDimensions);
}
```

## Изменённые файлы
1. `src/components/Player.tsx` - использует реальные размеры слайда из манифеста
2. `src/lib/api.ts` - добавлено поле `metadata` в интерфейс `Manifest`

## Как проверить
1. Обновите страницу в браузере (Cmd+R или F5)
2. Нажмите кнопку "Edit Edit"
3. Зелёные рамки должны точно совпадать с элементами на слайде
4. В консоли браузера должно появиться сообщение:
   ```
   [Player] 📐 Using real slide dimensions from manifest: {width: 1191, height: 1684}
   ```

## Техническая информация

### Пример реальных данных из базы
```sql
SELECT metadata FROM lessons WHERE id = '...';
-- Result:
{
  "slide_width": 1191,
  "slide_height": 1684,
  "source_file": "02_Z3_Anatomie+der+Biene (1).pdf",
  "source_type": "pdf",
  "total_slides": 13
}
```

### Вычисление масштаба
```typescript
const scaleX = containerWidth / slideDimensions.width;
const scaleY = containerHeight / slideDimensions.height;
const finalScale = Math.min(scaleX, scaleY);
```

**До исправления** (с фиксированными 1920x1080):
- Масштаб вычислялся неправильно
- Координаты bbox не совпадали с реальными элементами

**После исправления** (с реальными 1191x1684):
- Масштаб вычисляется правильно
- Координаты bbox точно соответствуют элементам

## Связанные исправления
- `VFX_POSITIONING_FIX.md` - исправление позиционирования визуальных эффектов в Canvas2DRenderer
- Это исправление относится к старому компоненту Player.tsx
- Новый PlayerPage.tsx + SlideViewer.tsx уже используют правильные размеры из манифеста
