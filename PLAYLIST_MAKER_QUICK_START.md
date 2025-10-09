# 🚀 Playlist Maker - Quick Start

## Быстрый Запуск за 5 Минут

### ⚡ Шаг 1: Запустить БД и Применить Миграцию

```bash
# Убедитесь что PostgreSQL запущен
docker-compose up -d postgres
# ИЛИ проверьте локальную БД

# Примените миграцию
cd backend
python3 -m alembic upgrade head
```

**Ожидаемый вывод:**
```
INFO  [alembic.runtime.migration] Running upgrade 004 -> 005, Add playlists tables
```

---

### ⚡ Шаг 2: Перезапустить Backend

```bash
# В папке backend
python3 -m uvicorn app.main:app --reload --port 8000
```

**Проверьте логи - должна быть строка:**
```
INFO: Application startup complete.
```

---

### ⚡ Шаг 3: Запустить Frontend (если не запущен)

```bash
# В корне проекта
npm run dev
```

Откройте: http://localhost:5173

---

### ⚡ Шаг 4: Тестирование

#### 4.1 Создание Плейлиста

1. **Войдите** в систему
2. Откройте **"Мои видео"** (должно быть хотя бы 2 видео)
3. Нажмите **"Плейлист"** на любом видео
4. В диалоге нажмите **"Создать новый плейлист"**
5. Введите название: `"Тестовый плейлист"`
6. Нажмите **✓**

✅ **Результат:** Плейлист создан, видео добавлено

---

#### 4.2 Просмотр Плейлистов

1. Кликните **"Плейлисты"** в верхнем меню
2. Увидите карточку вашего плейлиста
3. Нажмите **"Играть"**

✅ **Результат:** Откроется плеер, видео начнет воспроизводиться

---

#### 4.3 Редактирование Плейлиста

1. На странице **"Плейлисты"** нажмите **✏️ Edit**
2. Перетащите видео для изменения порядка (drag-and-drop)
3. Добавьте еще видео из списка "Доступные видео"
4. Измените название/описание
5. Включите **"Публичный плейлист"**
6. Нажмите **"Сохранить"**

✅ **Результат:** Плейлист обновлен, порядок изменен

---

#### 4.4 Поделиться Плейлистом

1. Нажмите **🔗 Share**
2. Скопируйте ссылку
3. Откройте в **приватном окне** (incognito)
4. Вставьте ссылку
5. Если установлен пароль - введите его

✅ **Результат:** Плейлист доступен по ссылке

---

#### 4.5 Bulk Add (Массовое добавление)

1. В **"Мои видео"** включите **режим выбора** (галочка в углу)
2. Выберите **несколько видео**
3. Нажмите **"Добавить в плейлист"** (внизу)
4. Выберите существующий плейлист

✅ **Результат:** Все выбранные видео добавлены в плейлист

---

### ⚡ Шаг 5: Проверка API

Откройте Swagger UI: http://localhost:8000/docs

Найдите секцию **"playlists"** - там должно быть 13 endpoints:

- ✅ `POST /api/playlists` - Create
- ✅ `GET /api/playlists` - List
- ✅ `GET /api/playlists/{id}` - Get
- ✅ `PUT /api/playlists/{id}` - Update
- ✅ `DELETE /api/playlists/{id}` - Delete
- ✅ `POST /api/playlists/{id}/videos` - Add videos
- ✅ `DELETE /api/playlists/{id}/videos/{item_id}` - Remove video
- ✅ `POST /api/playlists/{id}/reorder` - Reorder
- ✅ `GET /api/playlists/{id}/share` - Get share info
- ✅ `POST /api/playlists/{id}/view` - Track view
- ✅ `GET /api/playlists/{id}/analytics` - Get analytics
- ✅ `GET /api/playlists/shared/{token}` - Public access
- ✅ `POST /api/playlists/shared/{token}/access` - Protected access

---

## 🎨 UI Компоненты

### Где Найти:

1. **Кнопка "Плейлисты"** - Верхнее меню (десктоп) или бургер-меню (мобильное)
2. **"Мои видео"** - Кнопка "Плейлист" на каждом видео
3. **Страница плейлистов** - `/playlists`
4. **Плеер плейлиста** - `/playlists/:id/play`

### Иконки:
- 📋 **ListVideo** - плейлисты
- ➕ **Plus** - добавить
- ✏️ **Edit** - редактировать
- 🔗 **Share2** - поделиться
- 🗑️ **Trash2** - удалить
- ▶️ **Play** - играть
- ⏮️ **SkipBack** - предыдущее
- ⏭️ **SkipForward** - следующее
- 🔁 **Repeat** - повтор

---

## 🐛 Troubleshooting

### Проблема: Миграция не применяется

**Ошибка:** `could not translate host name "postgres"`

**Решение:**
```bash
# Проверьте что PostgreSQL запущен
docker-compose ps postgres

# Если не запущен
docker-compose up -d postgres

# Подождите 5 секунд и повторите миграцию
cd backend && python3 -m alembic upgrade head
```

---

### Проблема: 404 на /api/playlists

**Причина:** Backend не перезапущен

**Решение:**
```bash
# Остановите backend (Ctrl+C)
# Запустите заново
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

---

### Проблема: Компонент не найден

**Ошибка:** `Module not found: Can't resolve './playlists/...'`

**Решение:**
```bash
# Убедитесь что все файлы созданы
ls -la src/components/playlists/
# Должно быть 3 файла:
# - AddToPlaylistDialog.tsx
# - PlaylistEditor.tsx
# - SharePlaylistDialog.tsx

# Перезапустите dev server
npm run dev
```

---

### Проблема: TypeScript ошибки

**Ошибка:** `Property 'X' does not exist on type 'Y'`

**Решение:**
```bash
# Убедитесь что типы созданы
cat src/types/playlist.ts

# Перезапустите TypeScript server в VSCode
# Cmd+Shift+P → "TypeScript: Restart TS server"
```

---

## 📊 Тестовые Данные

### Создать тестовые плейлисты:

```python
# В Python REPL (опционально)
from backend.app.services.playlist_service import PlaylistService
from backend.app.models.playlist import PlaylistCreate

# Пример создания плейлиста через API
# См. Swagger UI для примеров запросов
```

---

## ✅ Готово!

Теперь у вас работает полноценная система плейлистов! 🎉

**Что дальше?**
- Создайте несколько плейлистов
- Протестируйте drag-and-drop
- Поделитесь плейлистом с другом
- Встройте плейлист на свой сайт

**Нужна помощь?**
- Полная документация: `PLAYLIST_MAKER_IMPLEMENTATION.md`
- API документация: http://localhost:8000/docs
- Issues: создайте issue в репозитории

---

**Happy Playlist Making! 🎵**
