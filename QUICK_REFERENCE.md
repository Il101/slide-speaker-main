# 🚀 Quick Reference Guide

Быстрый справочник по навигации в проекте Slide Speaker.

---

## 📂 Где что находится?

### Хочу запустить проект
```bash
./start.sh
# или
docker-compose up --build
```
📖 Подробнее: `README.md`

---

### Хочу посмотреть код

| Что ищу | Где найти |
|---------|-----------|
| Backend API | `backend/app/main.py` |
| Celery задачи | `backend/app/tasks.py` |
| База данных | `backend/app/core/database.py` |
| Аутентификация | `backend/app/core/auth.py` |
| Frontend компоненты | `src/components/` |
| Страницы | `src/pages/` |
| React хуки | `src/hooks/` |
| Типы TypeScript | `src/types/` |

---

### Хочу запустить тесты

```bash
# Smoke test
python scripts/integration/smoke_test.py

# Полный pipeline test
python scripts/integration/test_full_pipeline.py

# Тест Google Cloud
python scripts/integration/test_google_cloud_integration.py

# Тест голосов
python scripts/integration/test_google_voices.py
```

📁 Все тесты: `scripts/integration/`

---

### Хочу настроить что-то

| Задача | Скрипт |
|--------|--------|
| Создать Document AI процессор | `scripts/setup/create_processor.py` |
| Включить GCP APIs | `scripts/setup/enable_gcp_apis.py` |
| Найти процессор | `scripts/setup/find_processor.py` |
| Создать начальных пользователей | `backend/create_initial_users.py` |

📁 Все скрипты настройки: `scripts/setup/`

---

### Хочу исправить проблему

| Проблема | Решение |
|----------|---------|
| Диагностика GCP | `scripts/maintenance/diagnose_gcp.py` |
| Очистить блокировки уроков | `scripts/maintenance/clear_lesson_lock.py` |
| Диагностика Redis locks | `scripts/maintenance/diagnose_redis_locks.py` |
| Инициализировать MinIO | `scripts/maintenance/init_minio.py` |
| Исправить права доступа | `scripts/maintenance/fix_permissions.py` |

📁 Все скрипты обслуживания: `scripts/maintenance/`

---

### Хочу прочитать документацию

| Тема | Документ |
|------|----------|
| Быстрый старт | `README.md` |
| Деплой на сервер | `docs/guides/DEPLOYMENT_GUIDE.md` |
| Docker инструкции | `docs/guides/DOCKER_README.md` |
| Настройка аутентификации | `docs/guides/AUTH_INSTRUCTIONS.md` |
| Тестирование frontend | `docs/guides/FRONTEND_TESTING_GUIDE.md` |
| Sprint 1, 2, 3 | `docs/guides/SPRINT*.md` |

📁 Все руководства: `docs/guides/`

---

### Хочу посмотреть отчеты о разработке

| Категория | Где искать |
|-----------|------------|
| Отчеты по функционалу | `docs/reports/*_REPORT.md` |
| Исправления багов | `docs/reports/*_FIX_*.md` |
| Решенные проблемы | `docs/reports/*_SOLVED_*.md` |
| Тестирование | `docs/reports/*_TESTING_*.md` |
| Интеграции | `docs/reports/*_INTEGRATION_*.md` |

📁 Все отчеты: `docs/reports/`

---

## 🔧 Конфигурационные файлы

| Файл | Назначение |
|------|-----------|
| `.env.example` | Пример переменных окружения |
| `docker-compose.yml` | Оркестрация Docker контейнеров |
| `package.json` | Frontend зависимости |
| `backend/requirements.txt` | Backend зависимости |
| `vite.config.ts` | Конфигурация Vite |
| `tailwind.config.ts` | Конфигурация Tailwind CSS |
| `tsconfig.json` | Конфигурация TypeScript |
| `eslint.config.js` | Конфигурация ESLint |

---

## 🎯 Типичные задачи

### Добавить новый endpoint в API
1. Редактировать `backend/app/main.py`
2. Добавить модели в `backend/app/models/`
3. Создать сервисы в `backend/app/services/`
4. Добавить тесты в `scripts/integration/`

### Добавить новую страницу во frontend
1. Создать файл в `src/pages/`
2. Добавить компоненты в `src/components/`
3. Настроить роутинг в `src/App.tsx`
4. Добавить типы в `src/types/`

### Добавить новую фичу в pipeline
1. Редактировать `backend/app/tasks.py`
2. Добавить сервисы в `backend/app/services/sprint*/`
3. Обновить тесты в `scripts/integration/`
4. Создать отчет в `docs/reports/`

### Деплой на production
1. Прочитать `docs/guides/DEPLOYMENT_GUIDE.md`
2. Настроить `.env` по `docs/gcp_env_template.txt`
3. Запустить `docker-compose up --build`
4. Проверить `scripts/integration/smoke_test.py`

---

## 📞 Быстрые ссылки

- **API Docs**: http://localhost:8000/docs (после запуска)
- **Frontend**: http://localhost:5173 (локально) или http://localhost:3000 (Docker)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Redis**: localhost:6379
- **PostgreSQL**: localhost:5432

---

## 🆘 Проблемы?

1. **Проект не запускается** → `docs/guides/DEPLOYMENT_GUIDE.md`
2. **Ошибки в Docker** → `docs/guides/DOCKER_README.md`
3. **Проблемы с GCP** → `scripts/maintenance/diagnose_gcp.py`
4. **Проблемы с Redis** → `scripts/maintenance/diagnose_redis_locks.py`
5. **Ошибки аутентификации** → `docs/guides/AUTH_INSTRUCTIONS.md`

---

## 📚 Полная документация

- `PROJECT_STRUCTURE.md` - Полная структура проекта
- `PROJECT_FILES_CLASSIFICATION.md` - Классификация всех файлов
- `CLEANUP_REPORT.md` - Отчет об очистке проекта
- `README.md` - Главная документация

---

**Последнее обновление:** 1 октября 2025
