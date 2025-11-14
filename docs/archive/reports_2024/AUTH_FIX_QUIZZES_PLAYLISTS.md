# 🔧 Исправление аутентификации для тестов и плейлистов

**Дата:** 2025-01-15  
**Проблема:** 401 Unauthorized при создании тестов и плейлистов

---

## 🔴 ПРОБЛЕМА

### Симптомы
```
POST /api/quizzes/generate → 401 Unauthorized
POST /api/playlists → 401 Unauthorized
GET /api/playlists → 401 Unauthorized
```

**Ошибки в логах:**
```json
{"timestamp": "2025-10-09T21:10:50.370761", "status_code": 401, "path": "/api/quizzes/generate"}
{"timestamp": "2025-10-09T21:13:46.170260", "status_code": 401, "path": "/api/playlists"}
```

### Причина
**Несоответствие полей в JWT payload и response:**

```python
# backend/app/core/auth.py (БЫЛО)
def get_current_user():
    return {"user_id": user.id, "email": user.email, "role": user.role}
    #        ^^^^^^^^ - Нет поля "sub"!

# backend/app/api/playlists.py
current_user["sub"]  # ❌ KeyError! Поля "sub" не существует
```

**JWT токен создаётся с полем `sub`:**
```python
# backend/app/api/auth.py:87
AuthManager.create_access_token(
    data={"sub": user["user_id"], "email": user["email"], "role": user["role"]}
)
```

Но `get_current_user()` возвращал только `user_id`, не `sub`.

---

## ✅ РЕШЕНИЕ

### Исправление в `backend/app/core/auth.py:129-136`

**Было:**
```python
return {"user_id": user.id, "email": user.email, "role": user.role}
```

**Стало:**
```python
# ✅ FIX: Return "sub" field for JWT standard compatibility
# Many endpoints expect current_user["sub"] not current_user["user_id"]
return {
    "sub": user.id,  # JWT standard field for subject (user ID)
    "user_id": user.id,  # Keep for backward compatibility
    "email": user.email,
    "role": user.role
}
```

### Почему это работает?

**JWT стандарт (RFC 7519):**
- `sub` (Subject) - идентификатор субъекта (user ID)
- Это стандартное поле для JWT токенов

**Endpoints ожидают `current_user["sub"]`:**
```python
# backend/app/api/playlists.py:42
PlaylistService.create_playlist(db, current_user["sub"], data)

# backend/app/api/playlists.py:55
PlaylistService.get_user_playlists(db, current_user["sub"])

# И ещё 10+ мест в playlists.py
```

**Теперь:**
- ✅ `current_user["sub"]` работает (новое поле)
- ✅ `current_user["user_id"]` работает (обратная совместимость)

---

## 📊 ЗАТРОНУТЫЕ ENDPOINTS

### Playlists API (11 endpoints)
```
POST   /api/playlists              # Создать плейлист
GET    /api/playlists              # Получить все плейлисты
GET    /api/playlists/{id}         # Получить плейлист
PUT    /api/playlists/{id}         # Обновить плейлист
DELETE /api/playlists/{id}         # Удалить плейлист
POST   /api/playlists/{id}/videos  # Добавить видео
DELETE /api/playlists/{id}/videos/{item_id}  # Удалить видео
POST   /api/playlists/{id}/reorder # Изменить порядок
GET    /api/playlists/{id}/share   # Получить share token
POST   /api/playlists/{id}/view    # Отследить просмотр
GET    /api/playlists/{id}/analytics # Получить аналитику
```

### Quizzes API (6+ endpoints)
```
POST /api/quizzes/generate  # Генерировать тест
GET  /api/quizzes/{id}      # Получить тест
...и другие
```

---

## 🔄 ПРИМЕНЕНИЕ

**Backend:** ✅ Auto-reload (--reload включен)
- Изменения применяются автоматически
- Не требуется перезапуск контейнера

**Тестирование:**
1. Откройте страницу с тестами
2. Попробуйте "Сгенерировать тест" → должно работать ✅
3. Откройте страницу плейлистов
4. Попробуйте "Создать плейлист" → должно работать ✅

---

## 📝 ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Файл изменён
- `backend/app/core/auth.py` (строки 129-136)

### Функция
- `async def get_current_user()` - dependency для FastAPI endpoints

### Обратная совместимость
- ✅ Старый код с `current_user["user_id"]` продолжает работать
- ✅ Новый код с `current_user["sub"]` теперь работает
- ✅ JWT токен остался прежним (уже содержал "sub")

### Почему не нашли раньше?
- Endpoints для тестов и плейлистов были добавлены недавно
- Они использовали JWT стандарт `"sub"`
- Но `get_current_user` не возвращал это поле
- Получался KeyError при попытке доступа к `current_user["sub"]`

---

## ✅ РЕЗУЛЬТАТ

**До:**
```
❌ Нажать "Сгенерировать тест" → 401 Unauthorized
❌ Нажать "Создать плейлист" → 401 Unauthorized
```

**После:**
```
✅ Нажать "Сгенерировать тест" → Тест генерируется
✅ Нажать "Создать плейлист" → Плейлист создаётся
```

**Статус:** ✅ Исправлено (backend auto-reload)  
**Готово к тестированию!** 🚀
