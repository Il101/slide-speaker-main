# 🐳 Slide Speaker - Docker Deployment

## 🚀 Быстрый старт

### Предварительные требования
- Docker и Docker Compose
- Минимум 4GB RAM
- Минимум 10GB свободного места

### Запуск проекта

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd slide-speaker-main

# Запустите проект
./start.sh
```

### Остановка проекта

```bash
./stop.sh
```

## 📊 Сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| Frontend | http://localhost:3000 | React приложение |
| Backend API | http://localhost:8000 | FastAPI сервер |
| API Docs | http://localhost:8000/docs | Swagger документация |
| Prometheus | http://localhost:9090 | Метрики и мониторинг |
| Grafana | http://localhost:3001 | Дашборды и визуализация |
| MinIO | http://localhost:9001 | Объектное хранилище |

## 🔐 Учетные данные по умолчанию

### Пользователи приложения
- **Администратор**: `admin@example.com` / `adminpassword`
- **Пользователь**: `user@example.com` / `userpassword`

### Системные сервисы
- **Grafana**: `admin` / `admin123`
- **MinIO**: `minioadmin` / `minioadmin123`

## 🏗️ Архитектура

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │────│   Backend   │────│  PostgreSQL │
│  (React)    │    │  (FastAPI)  │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                    ┌─────────────┐
                    │    Redis    │
                    │ (Cache/Queue)│
                    └─────────────┘
                           │
                    ┌─────────────┐
                    │   Celery    │
                    │  (Workers)  │
                    └─────────────┘
                           │
                    ┌─────────────┐
                    │    MinIO    │
                    │ (Storage)   │
                    └─────────────┘

┌─────────────┐    ┌─────────────┐
│ Prometheus  │────│   Grafana   │
│ (Metrics)   │    │ (Dashboards)│
└─────────────┘    └─────────────┘
```

## 🔧 Управление

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f celery
docker-compose logs -f frontend
```

### Перезапуск сервисов
```bash
# Все сервисы
docker-compose restart

# Конкретный сервис
docker-compose restart backend
```

### Масштабирование
```bash
# Увеличить количество Celery воркеров
docker-compose up -d --scale celery=3
```

### Обновление
```bash
# Пересобрать и перезапустить
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📈 Мониторинг

### Метрики Prometheus
- **HTTP запросы**: `slide_speaker_requests_total`
- **Время обработки**: `slide_speaker_request_duration_seconds`
- **Ошибки**: `slide_speaker_errors_total`
- **Celery задачи**: `slide_speaker_celery_task_failures_total`
- **База данных**: `slide_speaker_database_connections`
- **Redis**: `slide_speaker_redis_connections`

### Алерты
- Высокий уровень ошибок
- Высокая задержка запросов
- Неудачные Celery задачи
- Высокое использование соединений
- Высокое время обработки

## 🛠️ Разработка

### Локальная разработка
```bash
# Запуск только инфраструктуры
docker-compose up -d postgres redis minio prometheus grafana

# Запуск backend в режиме разработки
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Запуск frontend в режиме разработки
npm run dev
```

### Тестирование
```bash
# Запуск тестов
docker-compose exec backend pytest

# Проверка здоровья сервисов
curl http://localhost:8000/health
curl http://localhost:9090/-/healthy
```

## 🔒 Безопасность

### Реализованные меры безопасности
- ✅ JWT аутентификация
- ✅ CSRF защита
- ✅ Rate limiting
- ✅ Валидация файлов
- ✅ Санитизация данных
- ✅ HTTP Security Headers
- ✅ Secrets management
- ✅ Non-root пользователи в контейнерах

### Рекомендации для production
1. Измените все пароли по умолчанию
2. Используйте HTTPS
3. Настройте файрвол
4. Регулярно обновляйте зависимости
5. Мониторьте логи и метрики

## 📝 Конфигурация

### Переменные окружения
Основные настройки находятся в файле `docker.env`:

```bash
# База данных
POSTGRES_DB=slide_speaker
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123

# Redis
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
```

### Secrets Management
Для production используйте proper secrets management:

```bash
# Инициализация secrets
python -m app.core.secrets init "your-master-key"

# Установка секретов
python -m app.core.secrets set DATABASE_URL "postgresql://..."
python -m app.core.secrets set JWT_SECRET_KEY "your-secret-key"

# Миграция из переменных окружения
python -m app.core.secrets migrate
```

## 🆘 Устранение неполадок

### Проблемы с запуском
```bash
# Проверка статуса сервисов
docker-compose ps

# Проверка логов
docker-compose logs backend

# Перезапуск проблемного сервиса
docker-compose restart backend
```

### Проблемы с базой данных
```bash
# Проверка подключения к PostgreSQL
docker-compose exec postgres psql -U postgres -d slide_speaker

# Пересоздание базы данных
docker-compose down -v
docker-compose up -d
```

### Проблемы с производительностью
```bash
# Мониторинг ресурсов
docker stats

# Увеличение количества воркеров
docker-compose up -d --scale celery=3
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус сервисов: `docker-compose ps`
3. Проверьте метрики: http://localhost:9090
4. Проверьте дашборды: http://localhost:3001
