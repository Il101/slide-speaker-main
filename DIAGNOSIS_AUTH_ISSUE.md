# 🔍 Диагностика проблемы: нет аудио, субтитров и визуальных эффектов

## ✅ ЧТО РАБОТАЕТ:

1. ✅ **Backend обработка работает корректно:**
   - Оба слайда распарсились
   - SSML заметки сгенерированы (2026 и 2351 символов)
   - Аудио файлы созданы (287KB и 360KB)
   - Визуальные cues сгенерированы (по 2 на слайд)
   - Elements распознаны (7 и 22 элементов)
   - Манифест сохранён корректно

2. ✅ **API endpoints работают:**
   - `/health` - ОК
   - `/assets/{lesson_id}/audio/*.mp3` - доступны (HTTP 200)
   - `/lessons/{lesson_id}/manifest` - работает **с авторизацией**

3. ✅ **Данные в файловой системе:**
   ```bash
   .data/470f6bb0-a553-411d-83ff-a75bcff40fca/
   ├── audio/
   │   ├── 001.mp3 (287KB)
   │   └── 002.mp3 (360KB)
   ├── slides/
   │   ├── 001.png
   │   └── 002.png
   └── manifest.json (полный, с аудио и cues)
   ```

---

## ❌ ГЛАВНАЯ ПРОБЛЕМА:

### **Пользователь НЕ АВТОРИЗОВАН на фронтенде!**

**Симптомы:**
- Манифест не загружается (требует авторизацию)
- Фронтенд показывает слайды, но без аудио/субтитров/эффектов
- API возвращает `{"detail":"Not authenticated"}`

**Причина:**
- Endpoint `/lessons/{lesson_id}/manifest` требует JWT токен
- Пользователь не вошёл в систему через `/auth/login`
- `localStorage` не содержит токен `'slide-speaker-auth-token'`

---

## 🔧 РЕШЕНИЕ:

### Вариант 1: Войти в систему (РЕКОМЕНДУЕТСЯ)

1. **Откройте страницу логина**: http://localhost:3000/login

2. **Используйте учётные данные:**
   - **Email:** `admin@example.com`
   - **Пароль:** `admin123`
   
   ИЛИ
   
   - **Email:** `user@example.com`
   - **Пароль:** `user123`

3. **После входа перезагрузите страницу с уроком**

### Вариант 2: Убрать требование авторизации для манифеста (НЕ РЕКОМЕНДУЕТСЯ для прода)

Если хотите тестировать без авторизации, удалите `Depends(get_current_user)` из endpoint'а:

```python
# backend/app/main.py, строка 494
@app.get("/lessons/{lesson_id}/manifest")
@limiter.limit("100/minute")
async def get_manifest(
    request: Request, 
    lesson_id: str
    # Удалить: current_user: dict = Depends(get_current_user)
):
```

### Вариант 3: Проверить авторизацию в браузере

Откройте DevTools (F12) → Console и проверьте:
```javascript
// Проверить токен
localStorage.getItem('slide-speaker-auth-token')

// Если null - нужно войти в систему
```

---

## 📊 Логи обработки (для справки):

```
[2025-10-01 19:03:48] Parsed 2 slides for lesson 470f6bb0-a553-411d-83ff-a75bcff40fca
[2025-10-01 19:04:04] Generated SSML speaker notes for slide 1: 2026 chars SSML, 1027 chars plain
[2025-10-01 19:04:18] Generated SSML speaker notes for slide 2: 2351 chars SSML, 1327 chars plain
[2025-10-01 19:04:21] Synthesized SSML speech: 3237728 bytes
[2025-10-01 19:04:26] Generated audio for slide 1
[2025-10-01 19:04:30] Synthesized SSML speech: 4061290 bytes
[2025-10-01 19:04:30] Generated audio for slide 2
[2025-10-01 19:04:30] Generated cues for slide 1
[2025-10-01 19:04:30] Generated cues for slide 2
[2025-10-01 19:04:30] Manifest saved successfully with 2 slides
[2025-10-01 19:04:31] Successfully completed processing
```

---

## 🧪 Тестирование через curl:

### 1. Авторизация:
```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### 2. Получение манифеста:
```bash
curl -s "http://localhost:8000/lessons/470f6bb0-a553-411d-83ff-a75bcff40fca/manifest" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 3. Проверка аудио:
```bash
curl -I "http://localhost:8000/assets/470f6bb0-a553-411d-83ff-a75bcff40fca/audio/001.mp3"
# Должен вернуть: HTTP/1.1 200 OK
```

---

## 📋 Содержимое манифеста (с авторизацией):

```json
{
  "slides": [
    {
      "id": 1,
      "image": "/assets/470f6bb0-a553-411d-83ff-a75bcff40fca/slides/001.png",
      "audio": "/assets/470f6bb0-a553-411d-83ff-a75bcff40fca/audio/001.mp3",
      "speaker_notes": "... 1027 символов ...",
      "speaker_notes_ssml": "... 2026 символов с SSML тегами ...",
      "elements": [ ... 7 элементов ... ],
      "cues": [ ... 2 визуальных эффекта ... ]
    },
    {
      "id": 2,
      "image": "/assets/470f6bb0-a553-411d-83ff-a75bcff40fca/slides/002.png",
      "audio": "/assets/470f6bb0-a553-411d-83ff-a75bcff40fca/audio/002.mp3",
      "speaker_notes": "... 1327 символов ...",
      "speaker_notes_ssml": "... 2351 символов с SSML тегами ...",
      "elements": [ ... 22 элементов ... ],
      "cues": [ ... 2 визуальных эффекта ... ]
    }
  ],
  "metadata": { ... },
  "timeline": { ... }
}
```

---

## ✅ Чеклист для пользователя:

- [ ] Открыть http://localhost:3000/login
- [ ] Войти с учётными данными (admin@example.com / admin123)
- [ ] Вернуться к уроку
- [ ] Проверить, что аудио плеер появился
- [ ] Проверить, что субтитры отображаются
- [ ] Проверить, что визуальные эффекты работают
- [ ] Попробовать воспроизвести аудио

---

## 🐛 Если проблема остаётся:

1. **Проверьте консоль браузера (F12):**
   - Ищите ошибки 401 (Unauthorized)
   - Ищите ошибки загрузки ресурсов

2. **Проверьте Network tab в DevTools:**
   - Запрос к `/lessons/{id}/manifest` должен иметь заголовок `Authorization: Bearer ...`
   - Ответ должен быть 200 OK, а не 401

3. **Проверьте localStorage:**
   ```javascript
   console.log(localStorage.getItem('slide-speaker-auth-token'));
   ```

4. **Проверьте логи backend:**
   ```bash
   docker-compose logs backend --tail=50
   ```

---

## 📞 Дополнительная информация:

- **Lesson ID:** `470f6bb0-a553-411d-83ff-a75bcff40fca`
- **Slides count:** 2
- **Status:** completed
- **Audio format:** MP3
- **Image format:** PNG
- **OCR provider:** Google Vision API
- **TTS provider:** Google TTS with SSML
- **LLM provider:** OpenRouter with SSML

**Дата диагностики:** 1 октября 2025, 21:07
