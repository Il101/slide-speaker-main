# 🚀 Инструкции по Деплою Аналитики

## ⚠️ Текущая Проблема

База данных PostgreSQL запущена, но authentication fails:
```
psycopg2.OperationalError: password authentication failed for user "postgres"
```

## ✅ Что Уже Готово

- ✅ Весь код написан (47 файлов)
- ✅ Зависимости установлены
- ✅ Миграция создана
- ✅ Docker контейнеры запущены
- ⚠️ Нужно настроить credentials БД

## 🔧 Решение

### Вариант 1: Проверить Пароль БД (Рекомендуется)

```bash
# 1. Проверить пароль в docker-compose.yml
cat docker-compose.yml | grep POSTGRES

# 2. Проверить .env backend
cat backend/.env | grep DATABASE

# 3. Обновить пароль если нужно
# Отредактировать backend/.env и docker-compose.yml

# 4. Пересоздать контейнеры
docker-compose down
docker-compose up -d

# 5. Подождать пока БД полностью запустится (30 сек)
sleep 30

# 6. Запустить миграцию
docker-compose exec backend alembic upgrade head
```

### Вариант 2: Тест Без БД

Можно протестировать фронтенд без миграции:

```bash
# 1. Запустить frontend
npm run dev

# 2. Открыть в браузере
open http://localhost:5173

# 3. Посмотреть что трекинг работает (в консоли браузера)
# Будут ошибки от API, но события будут отправляться

# 4. Попробовать открыть /analytics 
# (будет ошибка загрузки данных, но интерфейс будет виден)
```

### Вариант 3: Использовать SQLite для Теста

Временно можно переключиться на SQLite:

```bash
# В backend/.env измените DATABASE_URL на:
# DATABASE_URL=sqlite:///./slide_speaker.db

# Запустить миграцию локально
cd backend
python3 -m alembic upgrade head

# Запустить backend локально
uvicorn app.main:app --reload
```

## 📊 Проверка После Миграции

Когда миграция пройдет успешно:

```bash
# 1. Проверить таблицы
docker-compose exec postgres psql -U postgres -d slide_speaker -c "\dt analytics_*"

# Должно показать:
# analytics_events
# user_sessions  
# daily_metrics
# cost_logs

# 2. Проверить backend логи
docker-compose logs backend | grep analytics

# 3. Тестовый запрос
curl http://localhost:8000/api/analytics/track \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Test Event",
    "session_id": "test-123",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'

# Должно вернуть: {"success": true}

# 4. Проверить запись в БД
docker-compose exec postgres psql -U postgres -d slide_speaker \
  -c "SELECT * FROM analytics_events ORDER BY timestamp DESC LIMIT 1;"
```

## 🧪 Запуск Тестов

```bash
# Тест системы (без БД)
./test_analytics_system.sh

# Ожидаемый результат:
# ✓ Database models OK
# ✓ API endpoints OK  
# ✓ Cost tracker OK
# ✓ Frontend files exist
# ✓ NPM packages installed
# ✓ Python packages installed
# ✓ Migration file exists
```

## 📦 Коммит Изменений

Когда все работает:

```bash
# Автоматический коммит
./commit_analytics.sh

# ИЛИ вручную:
git add backend/ src/ *.md package.json scripts/
git commit -m "feat: Add comprehensive analytics system"
git push origin $(git branch --show-current)
```

## 🎯 Что Дальше

### После Успешной Миграции:

1. **Откройте приложение**
   ```bash
   open http://localhost:5173
   ```

2. **Войдите как админ**
   - Email: `admin@example.com`
   - Password: `admin123`

3. **Перейдите на /analytics**
   ```bash
   open http://localhost:5173/analytics
   ```

4. **Проверьте что данные появляются**
   - Походите по сайту (login, register и т.д.)
   - Обновите дашборд
   - Должны появиться события в Overview → Top Events

5. **Добавьте Cost Tracking** (опционально)
   - Смотрите примеры в `COST_TRACKING_INTEGRATION_EXAMPLES.md`
   - Добавьте в pipeline code

## 🐛 Troubleshooting

### Backend Unhealthy

```bash
# Проверить логи
docker-compose logs backend --tail=100

# Перезапустить
docker-compose restart backend

# Если не помогает - пересоздать
docker-compose down
docker-compose up -d --build backend
```

### Миграция Fails

```bash
# Проверить подключение к БД
docker-compose exec postgres pg_isready

# Проверить что БД существует
docker-compose exec postgres psql -U postgres -l

# Создать БД если нет
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE slide_speaker;"

# Попробовать миграцию снова
docker-compose exec backend alembic upgrade head
```

### События Не Трекаются

```bash
# 1. Проверить что backend запущен
curl http://localhost:8000/health

# 2. Проверить endpoint analytics
curl http://localhost:8000/api/analytics/track -X POST

# 3. Проверить консоль браузера (F12)
# Должны быть POST запросы к /api/analytics/*

# 4. Проверить CORS
# В backend/.env должно быть:
# CORS_ORIGINS=http://localhost:5173
```

## 📚 Полезные Команды

```bash
# Статус контейнеров
docker-compose ps

# Логи всех сервисов
docker-compose logs -f

# Подключение к БД
docker-compose exec postgres psql -U postgres -d slide_speaker

# Перезапуск backend
docker-compose restart backend

# Полный рестарт
docker-compose down && docker-compose up -d

# Проверка миграций
docker-compose exec backend alembic history

# Откат миграции
docker-compose exec backend alembic downgrade -1
```

## ✅ Финальный Чек-лист

- [ ] PostgreSQL запущен и здоров
- [ ] Backend запущен и здоров
- [ ] Миграция прошла успешно
- [ ] Таблицы созданы (analytics_events, user_sessions, daily_metrics, cost_logs)
- [ ] Frontend запущен
- [ ] Events трекаются (проверить в консоли)
- [ ] Дашборд открывается (/analytics)
- [ ] Нет ошибок в логах
- [ ] Изменения закоммичены

## 🎉 Готово!

Когда все пункты выполнены - система полностью работает!

**Документация:**
- `АНАЛИТИКА_ГОТОВА.md` - быстрый старт на русском
- `ANALYTICS_README.md` - полная документация
- `ANALYTICS_QUICK_START.md` - 5-минутный гайд

**Помощь:**
- Читайте документацию
- Проверяйте логи
- Тестируйте с curl

---

**Вопросы?** → Смотрите `АНАЛИТИКА_ГОТОВА.md`
