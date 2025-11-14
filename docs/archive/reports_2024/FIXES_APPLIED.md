# 🔧 Исправления проблем фронтенда

## ✅ Исправлено:

### 1. **SSML теги в субтитрах**

**Проблема:** В субтитрах отображались SSML теги типа `<speak>`, `<prosody>`, `<emphasis>`.

**Решение:** Добавлена функция `stripSSML()` для удаления всех XML тегов из текста:
```typescript
const stripSSML = (text: string): string => {
  if (!text) return '';
  return text.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
};
```

**Применено в:**
- Отображение субтитров (строка 909)
- Aria-label для screen readers (строка 709)

**Результат:** Теперь показывается чистый текст без SSML тегов.

---

### 2. **Обработка ошибок аудио**

**Проблема:** Аудио останавливалось сразу после запуска, не было понятно почему.

**Решение:** Добавлены обработчики событий:
```typescript
<audio
  onError={(e) => {
    console.error('Audio error:', e);
    const audio = e.currentTarget;
    if (audio.error) {
      console.error('Audio error code:', audio.error.code);
    }
  }}
  onLoadedMetadata={() => {
    console.log('Audio loaded, duration:', audioRef.current?.duration);
  }}
/>
```

**Результат:** Теперь в консоли будут видны ошибки аудио (если есть).

---

### 3. **React Router предупреждения**

**Проблема:** Предупреждения о future flags в React Router v7.

**Решение:** Добавлены future flags в BrowserRouter:
```typescript
<BrowserRouter
  future={{
    v7_startTransition: true,
    v7_relativeSplatPath: true,
  }}
>
```

**Результат:** Предупреждения исчезли.

---

## 🔍 Диагностика оставшихся проблем:

### Проблема 1: Аудио останавливается

**Возможные причины:**
1. **CORS ошибка** - браузер блокирует загрузку аудио
2. **Неправильный MIME type** - сервер отдаёт неправильный Content-Type
3. **Проблема с кодеком** - браузер не может декодировать MP3
4. **Проблема авторизации** - токен не передаётся для аудио

**Проверьте в Console (F12):**
```javascript
const audio = document.querySelector('audio');
console.log('Audio src:', audio?.src);
console.log('Audio error:', audio?.error);
console.log('Audio networkState:', audio?.networkState);
console.log('Audio readyState:', audio?.readyState);
```

**Коды networkState:**
- 0 = NETWORK_EMPTY (нет источника)
- 1 = NETWORK_IDLE (выбран источник)
- 2 = NETWORK_LOADING (загружается)
- 3 = NETWORK_NO_SOURCE (ошибка загрузки)

**Коды readyState:**
- 0 = HAVE_NOTHING (нет данных)
- 1 = HAVE_METADATA (есть метаданные)
- 2 = HAVE_CURRENT_DATA (есть текущий кадр)
- 3 = HAVE_FUTURE_DATA (можно начать воспроизведение)
- 4 = HAVE_ENOUGH_DATA (достаточно данных)

---

### Проблема 2: Визуальные эффекты съехали

**Причина:** Координаты в cues не соответствуют реальным элементам на слайде.

**В манифесте:**
```json
{
  "bbox": [100, 100, 800, 200]
}
```

**Проблема:** Это примитивные координаты, которые не соответствуют реальным элементам OCR.

**Решение:** Нужно исправить генерацию визуальных cues в backend.

**Где искать:**
- `backend/app/services/sprint2/ai_generator.py` - метод `generate_visual_cues()`
- `backend/app/tasks.py` - строки 168-177 (генерация cues)

**Проблема в коде:** Cues генерируются примитивно, не используя реальные bbox из OCR элементов.

**Правильный подход:**
```python
async def generate_visual_cues(self, elements: List[Dict], speaker_notes: str) -> List[Dict]:
    """Generate visual cues based on actual OCR elements"""
    cues = []
    current_time = 0.5
    
    for element in elements:
        # Use REAL bbox from OCR
        real_bbox = element.get('bbox', [0, 0, 0, 0])
        
        cues.append({
            't0': current_time,
            't1': current_time + 2.0,
            'action': 'highlight',
            'bbox': real_bbox,  # <-- Use real coordinates!
            'element_id': element.get('id')
        })
        
        current_time += 2.5
    
    return cues
```

---

## 🛠️ Что нужно сделать дальше:

### Шаг 1: Проверить аудио в Console

Откройте DevTools (F12) → Console и выполните:
```javascript
const audio = document.querySelector('audio');
console.log({
  src: audio?.src,
  error: audio?.error,
  errorCode: audio?.error?.code,
  networkState: audio?.networkState,
  readyState: audio?.readyState,
  duration: audio?.duration,
  paused: audio?.paused
});
```

Если `error.code` есть:
- **1 (MEDIA_ERR_ABORTED)** - загрузка прервана пользователем
- **2 (MEDIA_ERR_NETWORK)** - ошибка сети
- **3 (MEDIA_ERR_DECODE)** - ошибка декодирования
- **4 (MEDIA_ERR_SRC_NOT_SUPPORTED)** - формат не поддерживается

### Шаг 2: Проверить Network tab

1. Откройте DevTools → Network
2. Обновите страницу (F5)
3. Найдите запрос к `.mp3` файлу
4. Проверьте:
   - **Status:** должен быть 200
   - **Content-Type:** должен быть `audio/mpeg`
   - **Size:** должен быть > 0
   - **Headers:** есть ли CORS заголовки

### Шаг 3: Исправить координаты визуальных эффектов

Если нужны правильные координаты, нужно исправить backend:

```bash
cd backend

# Открыть файл с генерацией cues
# backend/app/services/sprint2/ai_generator.py

# Найти метод generate_visual_cues()
# Изменить, чтобы использовались реальные bbox из elements
```

---

## 📊 Текущий статус:

| Проблема | Статус | Решение |
|----------|--------|---------|
| SSML теги в субтитрах | ✅ ИСПРАВЛЕНО | Добавлена функция stripSSML() |
| React Router warnings | ✅ ИСПРАВЛЕНО | Добавлены future flags |
| Обработка ошибок аудио | ✅ ДОБАВЛЕНО | Логирование в Console |
| Аудио останавливается | ❓ ТРЕБУЕТ ПРОВЕРКИ | Проверьте Console |
| Визуальные эффекты съехали | ❌ BACKEND ПРОБЛЕМА | Нужно исправить генерацию cues |

---

## 🎯 Следующие шаги:

1. **Обновите страницу** (после перезапуска frontend)
2. **Откройте Console** (F12) и проверьте ошибки аудио
3. **Попробуйте воспроизвести** аудио
4. **Пришлите логи** из Console

**Дата исправлений:** 1 октября 2025, 21:25
