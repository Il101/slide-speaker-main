# 🚀 Инструкции по Развертыванию Критических Функций

## ✅ Выполненные Шаги

### 1. Создание Файлов ✅
Все критические функции реализованы и файлы созданы:
- ✅ WebSocket manager и API
- ✅ Content Editor API
- ✅ Subscription System
- ✅ Sentry Integration
- ✅ Database migration

### 2. Установка Зависимостей ✅
```bash
cd backend
pip install sentry-sdk[fastapi]==1.40.0
```

### 3. Тестирование ✅
```bash
cd backend
python3 test_critical_features.py
```
**Результат:** 6/6 тестов пройдено

---

## 📋 Оставшиеся Шаги

### Шаг 1: Запустить Docker Services

Для применения миграции БД нужно запустить PostgreSQL через Docker:

```bash
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main

# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps
```

Ожидаемый вывод:
```
NAME                    STATUS          PORTS
postgres                running         0.0.0.0:5432->5432/tcp
redis                   running         0.0.0.0:6379->6379/tcp
backend                 running         0.0.0.0:8000->8000/tcp
```

---

### Шаг 2: Применить Миграцию БД

После запуска Docker:

```bash
cd backend

# Проверить текущее состояние
alembic current

# Применить миграцию
alembic upgrade head

# Проверить что миграция применилась
alembic current
# Должно показать: 003 (head)
```

Миграция добавит поле `subscription_tier` в таблицу `users`.

---

### Шаг 3: Перезапустить Backend

```bash
# Если используется Docker
docker-compose restart backend

# Или если запускаете локально
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Шаг 4: Настроить Sentry (Опционально)

1. Создать проект на [sentry.io](https://sentry.io)
2. Получить DSN из настроек проекта
3. Добавить в `backend/.env`:

```bash
# Sentry Configuration
SENTRY_DSN=https://your-key@o123456.ingest.sentry.io/123456
ENVIRONMENT=production  # или development/staging
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
GIT_COMMIT=main  # или реальный commit hash
```

4. Перезапустить backend

---

### Шаг 5: Проверить Работоспособность

#### 5.1. Проверить WebSocket

Откройте консоль браузера на `http://localhost:3000`:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/progress/test-123');
ws.onopen = () => console.log('✅ WebSocket connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.onerror = (e) => console.error('❌ WebSocket error:', e);
```

#### 5.2. Проверить Content Editor API

```bash
# Получить auth token (замените на реальные данные)
TOKEN="your-jwt-token"

# Получить скрипт слайда
curl "http://localhost:8000/api/content/slide-script/test-lesson/1" \
  -H "Authorization: Bearer $TOKEN"
```

#### 5.3. Проверить Subscription System

```bash
# Проверить подключение к БД
docker-compose exec backend python3 -c "
from app.core.database import engine
from app.core.subscriptions import SubscriptionPlan
print('✅ DB connected')
print('Plans:', list(SubscriptionPlan.get_all_plans().keys()))
"
```

#### 5.4. Проверить Sentry

```bash
# Отправить тестовое событие
docker-compose exec backend python3 -c "
from app.core.sentry import capture_message
capture_message('Test message from deployment', level='info')
print('✅ Test event sent to Sentry')
"
```

Проверьте в Sentry dashboard что событие получено.

---

## 🔧 Troubleshooting

### Проблема: Docker не запускается

```bash
# Проверить что Docker Desktop запущен
docker --version

# Остановить старые контейнеры
docker-compose down

# Пересобрать и запустить
docker-compose up -d --build
```

### Проблема: База данных недоступна

```bash
# Проверить логи PostgreSQL
docker-compose logs postgres

# Проверить подключение
docker-compose exec postgres psql -U postgres -d slidespeaker -c "\dt"
```

### Проблема: Миграция не применяется

```bash
# Откатить миграцию
alembic downgrade -1

# Применить заново
alembic upgrade head

# Если не помогает, пересоздать БД
docker-compose down -v
docker-compose up -d
alembic upgrade head
```

### Проблема: Sentry не получает события

1. Проверить DSN в `.env`
2. Проверить что `sentry-sdk` установлен
3. Проверить логи при запуске:
   ```bash
   docker-compose logs backend | grep -i sentry
   ```
4. Если видите "Sentry initialized" - всё ок

### Проблема: WebSocket не подключается

1. Проверить CORS настройки в `main.py`
2. Проверить что используется правильный протокол (`ws://` а не `wss://` для локал)
3. Проверить логи:
   ```bash
   docker-compose logs backend | grep -i websocket
   ```

---

## 📊 Финальная Проверка

Запустите полный тест:

```bash
cd backend

# Запустить все тесты
python3 test_critical_features.py

# Ожидаемый результат:
# ============================================================
# TOTAL: 6/6 tests passed
# ============================================================
# 🎉 All critical features implemented and working!
```

---

## 🎯 Что Дальше?

После успешного развертывания:

1. **Frontend Integration:**
   - Добавить WebSocket клиент для прогресса
   - Создать UI для редактора контента
   - Добавить страницу управления подпиской

2. **Тестирование:**
   - End-to-end тесты с реальными презентациями
   - Нагрузочное тестирование WebSocket
   - Проверка всех тарифных лимитов

3. **Мониторинг:**
   - Настроить Grafana dashboards
   - Настроить alerts в Sentry
   - Мониторить WebSocket connections

4. **Документация:**
   - API документация (Swagger)
   - User guide для редактора
   - Pricing page для подписок

---

## 📞 Поддержка

**Документация:**
- `CRITICAL_FEATURES_IMPLEMENTATION_REPORT.md` - полное описание
- `CRITICAL_FEATURES_CHECKLIST.md` - быстрый справочник
- `DEPLOYMENT_INSTRUCTIONS.md` - этот файл

**Тесты:**
- `backend/test_critical_features.py` - автотесты

**Конфигурация:**
- `backend/.env` - переменные окружения
- `backend/alembic/versions/003_*` - миграция БД

---

## ✅ Чек-лист Развертывания

- [ ] Docker services запущены
- [ ] PostgreSQL доступна
- [ ] Redis доступен
- [ ] Миграция применена (003_add_subscription_tier)
- [ ] Sentry настроен (опционально)
- [ ] Backend перезапущен
- [ ] Все тесты проходят (6/6)
- [ ] WebSocket подключается
- [ ] Content Editor API работает
- [ ] Subscription система активна
- [ ] Sentry получает события

---

**Статус:** Готово к развертыванию ✅

Все критические функции реализованы, протестированы и готовы к использованию!
