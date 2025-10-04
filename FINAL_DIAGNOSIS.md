# 🔍 Финальная диагностика проблемы

## ✅ ЧТО УЖЕ ПРОВЕРИЛИ И РАБОТАЕТ:

1. ✅ **Backend обработка:** Полностью работает
   - Парсинг: 2 слайда из PDF
   - SSML генерация: есть
   - Аудио TTS: есть (330KB и 456KB)
   - Визуальные cues: есть (по 2 на слайд)
   - Elements OCR: есть (7 и 22 элемента)

2. ✅ **API endpoints:** Работают с авторизацией
   - `/lessons/{id}/manifest` - возвращает полный манифест
   - `/assets/{id}/audio/*.mp3` - аудио доступно

3. ✅ **Авторизация:** Работает
   - Login: admin@example.com / admin123
   - JWT токен в localStorage

4. ✅ **Данные в манифесте:** Все на месте
   ```json
   {
     "slides": [
       {
         "id": 1,
         "audio": "/assets/.../001.mp3",
         "speaker_notes": "текст...",
         "speaker_notes_ssml": "<speak>...</speak>",
         "cues": [...]
       }
     ]
   }
   ```

---

## ❌ ПРОБЛЕМА: Фронтенд не отображает данные

### Возможные причины:

#### 1. **Несоответствие типов TypeScript (ИСПРАВЛЕНО)**
   
**Было:**
```typescript
speaker_notes?: Array<{text: string; ...}>
```

**Стало:**
```typescript
speaker_notes?: string | Array<{text: string; ...}>
speaker_notes_ssml?: string
audio_path?: string
```

#### 2. **Player компонент может не отображать элементы**

Проверьте в `Player.tsx`:
- Строка 699-703: отображение speaker_notes
- Строка 708-721: audio элемент с `src={currentSlide.audio}`
- Строка 889-903: отображение субтитров

#### 3. **Проблема загрузки манифеста (требует проверки)**

В `Player.tsx` строка 226:
```typescript
const data = await apiClient.getManifest(lessonId);
```

Может быть ошибка при загрузке. Проверьте консоль браузера!

---

## 🔧 ЧТО ДЕЛАТЬ:

### Шаг 1: Откройте DevTools (F12) в браузере

1. Перейдите на вкладку **Console**
2. Ищите ошибки (красный текст)
3. Проверьте, есть ли сообщения типа:
   - `Failed to load manifest`
   - `401 Unauthorized`
   - `Network error`

### Шаг 2: Проверьте вкладку **Network**

1. Обновите страницу (F5)
2. Найдите запрос к `/lessons/{id}/manifest`
3. Проверьте:
   - **Status:** должен быть 200 (не 401)
   - **Response:** должен содержать полный manifest с audio, speaker_notes, cues
   - **Headers:** должен быть `Authorization: Bearer ...`

### Шаг 3: Проверьте, что отображается

Откройте React DevTools или просто посмотрите на страницу:
- **Есть ли элемент `<audio>`?** (в HTML)
- **Есть ли текст субтитров?** (speaker_notes)
- **Есть ли слайды?** (изображения)

### Шаг 4: Проверьте localStorage

В Console выполните:
```javascript
// Проверить токен
localStorage.getItem('slide-speaker-auth-token')

// Проверить сохранённое состояние
localStorage.getItem('slide-speaker-app-state')
```

---

## 🐛 Возможные сценарии:

### Сценарий A: "Нет авторизации"
**Симптомы:** 
- В Network вкладке запрос manifest возвращает 401
- В Console ошибка "Not authenticated"

**Решение:**
1. Разлогиньтесь: http://localhost:3000/login
2. Войдите снова: admin@example.com / admin123
3. Проверьте token в localStorage

### Сценарий B: "Манифест не загружается"
**Симптомы:**
- В Console ошибка "Failed to load manifest"
- Spinner крутится бесконечно

**Решение:**
1. Проверьте, что backend работает: `curl http://localhost:8000/health`
2. Проверьте lesson_id: правильный ли ID в URL?
3. Перезапустите frontend: `docker-compose restart frontend`

### Сценарий C: "Данные есть, но не отображаются"
**Симптомы:**
- Манифест загружается (200 OK)
- Нет ошибок в Console
- Но аудио/субтитры не видны

**Возможные причины:**
1. **CSS скрывает элементы** - проверьте `display: none` в стилях
2. **Условный рендеринг** - Player может не показывать элементы по какому-то условию
3. **Путь к аудио неправильный** - проверьте `src` атрибут audio элемента

**Отладка:**
```javascript
// В Console выполните:
document.querySelector('audio')?.src
// Должно быть: http://localhost:8000/assets/.../001.mp3

document.querySelector('audio')?.error
// Если есть ошибка - покажет код ошибки
```

### Сценарий D: "Неправильный lesson_id"
**Симптомы:**
- Страница показывает старый урок
- Или демо-урок вместо загруженного

**Решение:**
1. Очистите localStorage:
   ```javascript
   localStorage.removeItem('slide-speaker-app-state')
   ```
2. Обновите страницу
3. Загрузите файл заново

---

## 📝 Чеклист отладки:

- [ ] **Console:** Нет красных ошибок
- [ ] **Network:** Запрос `/manifest` возвращает 200 OK
- [ ] **Network:** Response содержит `audio`, `speaker_notes`, `cues`
- [ ] **Headers:** Есть `Authorization: Bearer ...`
- [ ] **localStorage:** Есть токен `slide-speaker-auth-token`
- [ ] **HTML:** Есть элемент `<audio>` с `src`
- [ ] **HTML:** Аудио src правильный (начинается с http://localhost:8000)
- [ ] **Console:** `document.querySelector('audio')?.error` возвращает null

---

## 🔬 Команды для отладки:

### В терминале:

```bash
# Проверить lesson_id последнего урока
docker-compose exec -T backend python -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:postgres@postgres:5432/slide_speaker')
with engine.connect() as conn:
    result = conn.execute(text('SELECT id, title FROM lessons ORDER BY created_at DESC LIMIT 1'))
    for row in result:
        print(f'ID: {row[0]}, Title: {row[1]}')"

# Проверить манифест напрямую
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

LESSON_ID="96860133-af68-4312-a433-7b94aad093bf"

curl -s "http://localhost:8000/lessons/$LESSON_ID/manifest" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -100

# Проверить аудио
curl -I "http://localhost:8000/assets/$LESSON_ID/audio/001.mp3"
```

### В браузере Console:

```javascript
// 1. Проверить состояние приложения
JSON.parse(localStorage.getItem('slide-speaker-app-state'))

// 2. Проверить токен
localStorage.getItem('slide-speaker-auth-token')

// 3. Проверить аудио элемент
const audio = document.querySelector('audio');
console.log('Audio src:', audio?.src);
console.log('Audio error:', audio?.error);
console.log('Audio duration:', audio?.duration);

// 4. Принудительно загрузить манифест
// (откройте React DevTools и найдите Player компонент)
```

---

## 💡 Быстрые решения:

### Решение 1: Полная перезагрузка
```bash
# Очистить кэш браузера
# Ctrl+Shift+Delete -> Clear cache

# Очистить localStorage в Console
localStorage.clear()

# Обновить страницу
# F5
```

### Решение 2: Перезапуск фронтенда
```bash
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main
docker-compose restart frontend
# Подождать 30 секунд
# Обновить страницу
```

### Решение 3: Проверка напрямую через API
```bash
# Получить токен
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'

# Скопировать access_token
# Открыть в браузере:
# http://localhost:8000/docs
# Authorize с этим токеном
# Попробовать GET /lessons/{id}/manifest
```

---

## 📊 Статус исправлений:

| Проблема | Статус | Комментарий |
|----------|--------|-------------|
| Парсинг слайдов | ✅ ИСПРАВЛЕНО | Теперь обрабатываются все слайды |
| Генерация аудио | ✅ РАБОТАЕТ | MP3 файлы созданы |
| Генерация SSML | ✅ РАБОТАЕТ | Speaker notes с SSML |
| Визуальные cues | ✅ РАБОТАЕТ | Cues сгенерированы |
| API авторизация | ✅ РАБОТАЕТ | JWT токены |
| TypeScript типы | ✅ ИСПРАВЛЕНО | speaker_notes может быть string |
| Отображение на фронтенде | ❓ ТРЕБУЕТ ПРОВЕРКИ | Откройте DevTools |

---

**Следующий шаг:** Откройте http://localhost:3000 и проверьте Console (F12) на наличие ошибок!

**Дата диагностики:** 1 октября 2025, 21:18
