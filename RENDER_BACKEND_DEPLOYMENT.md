# Деплой backend `slide-speaker` на Render

Этот гайд гарантирует, что backend и Celery worker поднимутся без ошибок проверки окружения. Используйте его вместе с файлом `render.yaml`, который описывает всю инфраструктуру (web-сервис, Celery worker, PostgreSQL и Redis).

## 1. Что входит в blueprint

- **Web**: `slide-speaker-backend` (Docker, `backend/Dockerfile`, healthcheck `/health/live`)
- **Worker**: `slide-speaker-worker` (тот же образ, стартует `celery -A app.celery_app worker …`)
- **PostgreSQL**: `slide-speaker-db` (free plan, внутренняя строка подключается автоматически)
- **Redis (Key Value)**: `slide-speaker-cache` (free plan, `REDIS_URL` прокидывается в оба сервиса)
- **Env группы**:
  - `slide-speaker-shared`: безопасные значения (CORS, pipeline лимиты, пути к GCP creds и т. д.)
  - `slide-speaker-secrets`: чувствительные параметры, которые Render либо сгенерирует (`JWT_SECRET_KEY`), либо попросит ввести вручную.

## 2. Подготовьте секреты

Создайте значения до запуска blueprint:

| Переменная | Где взять |
|------------|-----------|
| `GCP_SERVICE_ACCOUNT_JSON` | Содержимое файла `keys/gcp-sa.json` (service account с доступом к Vision/GCS/DocAI). Скопируйте **весь JSON** в один env var. |
| `GOOGLE_API_KEY` | Gemini API key из Google AI Studio. |
| `OPENROUTER_API_KEY` (опционально) | Если хотите использовать OpenRouter fallback. |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Нужны, только если выгружаете экспорты в S3; иначе оставьте пустыми. |

> `JWT_SECRET_KEY` генерится автоматически (Render создаёт base64 значение один раз при первом деплое). При необходимости можно заменить на собственное значение через Dashboard.

## 3. Запуск blueprint

1. Убедитесь, что Render CLI настроен (`render login`) или используйте Dashboard → **Blueprints**.
2. В корне репозитория выполните:
   ```bash
   render blueprints launch --from render.yaml
   ```
   CLI попросит ввести значения для переменных с `sync: false`.
3. Дождитесь создания `slide-speaker-db` и `slide-speaker-cache`. После готовности Render автоматически задеплоит web + worker.

## 4. Проверка перед деплоем

Локально запустите чек-лист:

```bash
./check-readiness.sh
```

Скрипт проверит наличие всех критичных переменных (`JWT_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, GCP ключи) и требуемых файлов. Исправьте ошибки до пуша или ручного триггера деплоя.

## 5. Пост-деплой

1. Откройте `https://dashboard.render.com/web/<service>` → **Logs**: убедитесь, что нет ошибок `API validation failed`.
2. Прогоните smoke-тесты:
   ```bash
   curl https://slide-speaker-backend.onrender.com/health
   curl https://slide-speaker-backend.onrender.com/ready
   ```
3. Запустите любой пайплайн (upload PPTX) и проверьте, что прогресс доходит до завершения, а Celery worker сообщает статус в логах.

## 6. Частые вопросы

- **Нужно ли загружать файл `gcp-sa.json` в образ?**  
  Нет. Сервис сам создаёт временный файл на старте, если задана `GCP_SERVICE_ACCOUNT_JSON`. Мы также прописываем `GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-sa.json`, чтобы код использовал единый путь.

- **Можно ли использовать существующие Postgres/Redis?**  
  Да. Просто удалите блоки `databases`/`slide-speaker-cache` в `render.yaml` и пропишите `DATABASE_URL`/`REDIS_URL` со значениями `sync: false`. Скрипт `check-readiness.sh` всё равно проверит их наличие.

- **Что делать при ошибке `JWT_SECRET_KEY must be set`?**  
  Значит секрет не был создан или удалён вручную. Зайдите в настройки обоих сервисов на Render, добавьте одинаковое значение `JWT_SECRET_KEY`, перезапустите деплой.

Теперь весь стек задекларирован кодом, а критичные переменные и сервисы проверяются до деплоя, что исключает повторение прошлых ошибок.

