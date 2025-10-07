# Диагностика Slide Speaker - Полный Чеклист

## 🎯 Цель
Проверить работоспособность всех компонентов системы генерации презентаций с голосовым сопровождением.

---

## 1️⃣ Инфраструктура и Контейнеры

### Docker Services
```bash
# Проверить статус всех контейнеров
docker compose ps

# Ожидаемые сервисы (все должны быть Running/Healthy):
# - postgres (Healthy)
# - redis (Running)
# - minio (Running)
# - backend (Running)
# - celery (Running)
# - frontend (Running)
# - db-init (Exited 0)
# - prometheus (Running)
# - grafana (Running)
```

### Логи сервисов
```bash
# Проверить логи на ошибки
docker compose logs backend --tail 50
docker compose logs celery --tail 50
docker compose logs postgres --tail 20
docker compose logs db-init
```

**✅ Критерий успеха:**
- Все контейнеры запущены
- Нет критических ошибок в логах
- db-init завершился успешно (создал пользователей и миграции)

---

## 2️⃣ База Данных PostgreSQL

### Проверка подключения
```bash
# Подключение к БД
docker compose exec postgres psql -U slide_speaker -d slide_speaker -c "\dt"

# Должны быть таблицы:
# - users
# - lessons
# - slides
# - exports
# - alembic_version
```

### Проверка схемы таблицы lessons
```bash
docker compose exec postgres psql -U slide_speaker -d slide_speaker -c "\d lessons"

# Критические колонки для проверки:
# - id, title, description, status, user_id
# - file_path, file_size, file_type
# - slides_count, total_duration
# - manifest_data, processing_progress
# - created_at, updated_at, completed_at
```

### Проверка пользователей приложения
```bash
docker compose exec postgres psql -U slide_speaker -d slide_speaker -c "SELECT email, is_active FROM users"

# Должны быть:
# - admin@example.com (is_active: true)
# - user@example.com (is_active: true)
```

**✅ Критерий успеха:**
- Все таблицы созданы
- Таблица lessons содержит все необходимые колонки
- Пользователи admin и user существуют

---

## 3️⃣ Backend API

### Health Check
```bash
curl http://localhost:8000/health
# Ожидаемый ответ: {"status":"ok"}
```

### Документация API
```bash
# Откройте в браузере:
open http://localhost:8000/docs

# Проверьте наличие эндпоинтов:
# - POST /api/auth/login
# - POST /api/auth/register
# - POST /api/lessons/upload
# - GET /api/lessons
# - POST /api/lessons/{id}/process
```

### Аутентификация
```bash
# Тест логина admin
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Должен вернуть access_token
```

**✅ Критерий успеха:**
- Health endpoint возвращает OK
- Swagger UI доступен
- Аутентификация работает, возвращает JWT токен

---

## 4️⃣ Celery Worker

### Статус Celery
```bash
# Проверить логи Celery
docker compose logs celery --tail 50

# Ожидается:
# - Подключение к Redis успешно
# - Worker запущен
# - Registered tasks видны (process_lesson, generate_audio и т.д.)
```

### Тест задачи (опционально)
```bash
# Войти в backend контейнер
docker compose exec backend python -c "
from app.celery_app import celery_app
result = celery_app.send_task('app.tasks.test_task')
print(f'Task ID: {result.id}')
"
```

**✅ Критерий успеха:**
- Celery worker подключен к Redis
- Видны зарегистрированные задачи
- Нет ошибок подключения

---

## 5️⃣ MinIO (S3 Storage)

### Доступность MinIO
```bash
# Откройте консоль MinIO
open http://localhost:9001

# Credentials:
# - Username: minioadmin
# - Password: minioadmin
```

### Проверка бакетов
```bash
# Через mc (MinIO Client) или Web UI проверьте:
# - Бакет "slides" существует
# - Доступ на чтение/запись работает
```

**✅ Критерий успеха:**
- MinIO Console доступна
- Бакет создан
- Файлы можно загружать/скачивать

---

## 6️⃣ Frontend

### Доступность интерфейса
```bash
# Откройте приложение
open http://localhost:3000

# Проверьте:
# - Страница загружается
# - Форма логина отображается
# - Нет ошибок в консоли браузера (F12)
```

### Тест аутентификации через UI
1. Откройте http://localhost:3000
2. Войдите с учетными данными:
   - Email: `admin@example.com`
   - Password: `admin123`
3. Проверьте редирект на главную страницу

**✅ Критерий успеха:**
- Frontend загружается без ошибок
- Логин через UI работает
- Навигация функционирует

---

## 7️⃣ Загрузка и Обработка Файлов

### Тест загрузки PDF
```bash
# Получить токен
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' | jq -r '.access_token')

# Загрузить тестовый PDF
curl -X POST http://localhost:8000/api/lessons/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_presentation.pptx" \
  -F "title=Test Lesson" \
  -F "description=Diagnostic test"

# Должен вернуть lesson_id и status: "uploaded"
```

### Проверка записи в БД
```bash
docker compose exec postgres psql -U slide_speaker -d slide_speaker -c "
SELECT id, title, status, file_path, file_size, created_at 
FROM lessons 
ORDER BY created_at DESC 
LIMIT 5"
```

**✅ Критерий успеха:**
- Файл успешно загружен
- Запись создана в таблице lessons
- Поля file_path, file_size, file_type заполнены
- Статус "uploaded" или "processing"

---

## 8️⃣ Pipeline Обработки

### Запуск обработки
```bash
# Получить ID урока из предыдущего шага
LESSON_ID="<ваш_lesson_id>"

# Запустить обработку
curl -X POST http://localhost:8000/api/lessons/$LESSON_ID/process \
  -H "Authorization: Bearer $TOKEN"
```

### Мониторинг обработки
```bash
# Следить за логами Celery
docker compose logs celery --follow

# Проверять статус урока
curl http://localhost:8000/api/lessons/$LESSON_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.status, .processing_progress'
```

**✅ Критерий успеха:**
- Задача запущена в Celery
- Статус меняется: uploaded → processing → completed
- processing_progress обновляется
- Нет ошибок в Celery логах

---

## 9️⃣ AI/LLM Интеграция

### Проверка переменных окружения
```bash
# Проверить наличие API ключей
docker compose exec backend env | grep -E "(OPENAI|GOOGLE|GEMINI|ANTHROPIC)"

# Должны быть настроены:
# - OPENAI_API_KEY или
# - GOOGLE_APPLICATION_CREDENTIALS или
# - Другие LLM провайдеры
```

### Тест генерации контента
```bash
# Проверить, что LLM worker может генерировать текст
docker compose logs celery | grep -i "llm\|gemini\|openai"
```

**✅ Критерий успеха:**
- API ключи настроены
- LLM запросы выполняются без ошибок квот
- Генерация текста для слайдов работает

---

## 🔟 Monitoring & Metrics

### Prometheus
```bash
open http://localhost:9090

# Проверьте метрики:
# - Targets (должны быть UP)
# - Queries для API метрик
```

### Grafana
```bash
open http://localhost:3001

# Credentials:
# - Username: admin
# - Password: admin

# Проверьте дашборды:
# - System metrics
# - Application metrics
```

**✅ Критерий успеха:**
- Prometheus собирает метрики
- Grafana показывает данные
- Нет недоступных targets

---

## 🔍 Типичные Проблемы и Решения

### ❌ Проблема: PostgreSQL role doesn't exist
**Решение:**
```bash
docker compose down -v
docker compose build backend db-init --no-cache
docker compose up -d
```

### ❌ Проблема: Column 'file_path' doesn't exist
**Решение:**
```bash
# Пересоздать миграцию
docker compose exec backend alembic downgrade base
docker compose exec backend alembic upgrade head
```

### ❌ Проблема: Import errors в backend
**Решение:**
```bash
# Проверить относительные импорты
# Пересобрать образ
docker compose build backend --no-cache
docker compose restart backend
```

### ❌ Проблема: Celery не видит задачи
**Решение:**
```bash
# Перезапустить Celery worker
docker compose restart celery
docker compose logs celery --tail 100
```

### ❌ Проблема: Frontend не подключается к backend
**Решение:**
```bash
# Проверить переменные окружения
# В docker-compose.yml для frontend:
# VITE_API_BASE=http://localhost:8000

docker compose restart frontend
```

---

## 📊 Итоговый Чеклист

| Компонент | Статус | Примечания |
|-----------|--------|------------|
| Docker Containers | ⬜ |  |
| PostgreSQL | ⬜ | Схема lessons |
| Backend API | ⬜ | Health + Auth |
| Celery Worker | ⬜ | Tasks registered |
| MinIO Storage | ⬜ | Buckets created |
| Frontend | ⬜ | UI accessible |
| File Upload | ⬜ | PDF/PPTX upload |
| Processing Pipeline | ⬜ | End-to-end |
| LLM Integration | ⬜ | Text generation |
| Monitoring | ⬜ | Prometheus/Grafana |

---

## 🚀 Быстрая Диагностика (One-liner)

```bash
# Полная проверка системы
echo "=== Docker Services ===" && \
docker compose ps && \
echo -e "\n=== Backend Health ===" && \
curl -s http://localhost:8000/health && \
echo -e "\n\n=== Database Tables ===" && \
docker compose exec -T postgres psql -U slide_speaker -d slide_speaker -c "\dt" && \
echo -e "\n=== Lessons Schema ===" && \
docker compose exec -T postgres psql -U slide_speaker -d slide_speaker -c "\d lessons" | head -20 && \
echo -e "\n=== Users ===" && \
docker compose exec -T postgres psql -U slide_speaker -d slide_speaker -c "SELECT email FROM users" && \
echo -e "\n=== Recent Errors ===" && \
docker compose logs backend --tail 10 | grep -i error
```

---

## 📝 Лог Диагностики

**Дата:** ___________  
**Версия:** ___________  
**Проверил:** ___________  

**Найденные проблемы:**
1. 
2. 
3. 

**Примененные исправления:**
1. 
2. 
3. 

**Результат:** ✅ Система работает / ⚠️ Требуются доработки / ❌ Критические ошибки
