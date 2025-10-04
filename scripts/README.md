# Утилитные скрипты

## Структура

### 🧪 integration/
Интеграционные тесты и проверки:
- `test_*.py` - Тесты различных компонентов системы
- `check_*.py` - Проверка доступности и конфигурации сервисов
- `upload_*.py`, `generate_*.py` - Утилиты для работы с данными

**Примеры:**
```bash
# Тест полного pipeline
python scripts/integration/test_full_pipeline.py

# Проверка Google Cloud интеграции
python scripts/integration/test_google_cloud_integration.py

# Проверка доступных голосов
python scripts/integration/check_chirp_voices.py
```

### ⚙️ setup/
Скрипты настройки и инициализации:
- `create_*.py` - Создание ресурсов (процессоры, пользователи)
- `find_*.py` - Поиск существующих ресурсов
- `enable_*.py` - Включение API и сервисов

**Примеры:**
```bash
# Создание Document AI процессора
python scripts/setup/create_processor.py

# Включение GCP APIs
python scripts/setup/enable_gcp_apis.py
```

### 🔧 maintenance/
Скрипты обслуживания и отладки:
- `diagnose_*.py` - Диагностика проблем
- `clear_*.py` - Очистка данных
- `fix_*.py` - Исправление проблем
- `regenerate_*.py` - Регенерация данных
- `init_*.py` - Инициализация сервисов

**Примеры:**
```bash
# Диагностика GCP
python scripts/maintenance/diagnose_gcp.py

# Очистка блокировок Redis
python scripts/maintenance/clear_lesson_lock.py

# Инициализация MinIO
python scripts/maintenance/init_minio.py
```

## Использование

Все скрипты запускаются из корня проекта:

```bash
# Общий формат
python scripts/<категория>/<имя_скрипта>.py
```

Перед запуском убедитесь, что:
1. Установлены зависимости: `pip install -r backend/requirements.txt`
2. Настроены переменные окружения (`.env`)
3. Запущены необходимые сервисы (Redis, PostgreSQL, MinIO)
