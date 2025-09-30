# Sprint 3: Экспорт в MP4, очереди и хранилище

## 🎯 Цель спринта
Реализовать полный цикл экспорта презентаций в MP4 видео с визуальными эффектами, очередями задач и надежным хранилищем.

## ✅ Что реализовано

### 1. Рендер MP4 из Manifest
- **FFmpeg интеграция**: Полноценный рендер видео с визуальными эффектами
- **Визуальные эффекты**: Подсветка, подчеркивание, лазерная указка, fade in/out
- **Синхронизация**: Точная синхронизация эффектов с аудио
- **Качество**: Настройки качества (low/medium/high) с разными разрешениями и битрейтами

### 2. API Endpoints
- **POST /lessons/{id}/export**: Запуск экспорта с параметрами качества
- **GET /exports/{task_id}/status**: Отслеживание прогресса экспорта
- **GET /exports/{lesson_id}/download**: Скачивание готового MP4

### 3. Очереди задач (Redis + Celery)
- **Фоновая обработка**: Экспорт выполняется в фоне
- **Прогресс**: Реальное отслеживание прогресса (10% → 20% → 60% → 80% → 100%)
- **Надежность**: Retry механизм и обработка ошибок
- **Масштабируемость**: Возможность добавления воркеров

### 4. S3-хранилище (MinIO)
- **Локальное хранилище**: MinIO для разработки
- **Загрузка в S3**: Автоматическая загрузка экспортированных видео
- **Presigned URLs**: Безопасные ссылки для скачивания
- **Очистка**: Автоматическая очистка старых файлов

### 5. Надежность
- **Лимиты размера**: Максимальный размер файла 500MB
- **Таймауты**: 30 минут на экспорт
- **Ретраи**: 3 попытки при ошибках
- **Структурированные логи**: Подробное логирование всех операций

### 6. CI/CD (GitHub Actions)
- **Тестирование**: Автоматические тесты при push/PR
- **Сборка**: Docker образы для всех сервисов
- **Безопасность**: Проверка уязвимостей
- **Деплой**: Автоматический деплой на staging

### 7. Docker Compose
- **Все сервисы**: Backend, Frontend, Redis, Celery, MinIO
- **Сетевое взаимодействие**: Правильная настройка сети
- **Volumes**: Персистентное хранилище данных
- **Health checks**: Проверка здоровья сервисов

## 🚀 Быстрый запуск

### 1. Запуск всех сервисов
```bash
# Клонируйте репозиторий
git clone <repository-url>
cd slide-speaker

# Запустите все сервисы
docker-compose up --build
```

### 2. Настройка MinIO
1. Откройте MinIO Console: http://localhost:9001
2. Войдите: `minioadmin` / `minioadmin`
3. Создайте bucket: `slide-speaker`

### 3. Тестирование экспорта
```bash
# Запустите smoke test
python smoke_test.py
```

### 4. Ручное тестирование
1. Откройте фронтенд: http://localhost:3000
2. Нажмите "Посмотреть демо"
3. Нажмите "Export"
4. Дождитесь завершения (5-10 минут)
5. Скачайте MP4

## 📊 Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Celery        │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Worker        │
│   Port: 3000    │    │   Port: 8000    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Redis       │    │     MinIO       │
                       │   Port: 6379    │    │   Port: 9000    │
                       └─────────────────┘    └─────────────────┘
```

## 🔧 Конфигурация

### Переменные окружения
```env
# Queue
REDIS_URL=redis://redis:6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# S3 Storage
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET=slide-speaker

# Export Settings
MAX_EXPORT_SIZE_MB=500
EXPORT_RETRY_ATTEMPTS=3
EXPORT_TIMEOUT_SECONDS=1800
```

## 📈 Мониторинг

### Логи
- **Backend**: Структурированные логи с уровнем INFO
- **Celery**: Подробные логи выполнения задач
- **MinIO**: Логи доступа к хранилищу

### Метрики
- **Storage stats**: `/admin/storage-stats`
- **Task status**: `/exports/{task_id}/status`
- **Health check**: `/health`

## 🧪 Тестирование

### Smoke Test
```bash
python smoke_test.py
```

Проверяет:
- ✅ API health check
- ✅ Demo lesson manifest
- ✅ Export request
- ✅ Export status polling
- ✅ MP4 download
- ✅ Storage statistics

### Unit Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Tests
```bash
npm run test:ci
```

## 🚨 Troubleshooting

### Проблемы с экспортом
1. **Проверьте FFmpeg**: `docker exec backend ffmpeg -version`
2. **Проверьте Redis**: `docker exec redis redis-cli ping`
3. **Проверьте Celery**: `docker logs celery`
4. **Проверьте MinIO**: http://localhost:9001

### Проблемы с хранилищем
1. **Bucket не существует**: Создайте bucket в MinIO Console
2. **Права доступа**: Проверьте AWS credentials
3. **Сеть**: Убедитесь, что сервисы могут общаться

### Проблемы с очередями
1. **Redis недоступен**: `docker restart redis`
2. **Celery воркер**: `docker restart celery`
3. **Задачи зависли**: Очистите Redis: `docker exec redis redis-cli FLUSHALL`

## 📝 API Examples

### Запуск экспорта
```bash
curl -X POST "http://localhost:8000/lessons/demo-lesson/export" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_id": "demo-lesson",
    "quality": "high",
    "include_audio": true,
    "include_effects": true
  }'
```

### Проверка статуса
```bash
curl "http://localhost:8000/exports/{task_id}/status"
```

### Скачивание видео
```bash
curl -O "http://localhost:8000/exports/demo-lesson/download"
```

## 🎉 Результат

После завершения Sprint 3 у вас есть:

1. **Полноценный экспорт в MP4** с визуальными эффектами
2. **Надежная система очередей** для фоновой обработки
3. **S3-хранилище** для масштабируемого хранения
4. **CI/CD pipeline** для автоматического деплоя
5. **Comprehensive testing** с smoke tests
6. **Production-ready** архитектура

**Smoke-test**: Нажимаю Export → получаю MP4, повторяющий плеер ✅