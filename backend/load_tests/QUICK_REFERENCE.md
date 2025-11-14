# ⚡ Load Testing Quick Reference

Быстрая справка по нагрузочному тестированию Slide Speaker.

## 🚀 Команды быстрого запуска

```bash
# Переход в директорию
cd backend/load_tests

# Первая установка
pip install -r requirements.txt

# Проверка готовности
python3 validate_setup.py

# Быстрый тест (2 минуты)
./quickstart.sh

# Легкая нагрузка
./run_load_tests.sh light http://localhost:8000

# Средняя нагрузка (рекомендуется)
./run_load_tests.sh medium http://localhost:8000

# Тяжелая нагрузка
./run_load_tests.sh heavy http://localhost:8000
```

## 📊 Сценарии

| Команда | Пользователи | Время | Назначение |
|---------|--------------|-------|------------|
| `light` | 10 | 5 мин | Baseline |
| `medium` | 50 | 10 мин | Peak hours |
| `heavy` | 100 | 15 мин | High traffic |
| `stress` | 500 | 20 мин | Breaking point |
| `spike` | 200 | 5 мин | Sudden surge |
| `endurance` | 30 | 2 часа | Stability |
| `api-only` | 100 | 10 мин | API only |
| `resource-intensive` | 20 | 15 мин | Heavy ops |

## 🎯 Целевые метрики

```
Error Rate:      < 1%
API Read P95:    < 500ms
API Write P95:   < 1000ms
Throughput:      > 50 req/s
CPU:             < 80%
Memory:          < 85%
```

## 📁 Результаты

```bash
# Последний отчет
open backend/load_tests/reports/latest/report.html

# Все отчеты
ls -lh backend/load_tests/reports/
```

## 🔧 Утилиты

```bash
# Генерация тестовых данных
python3 generate_test_data.py --users 50 --presentations 2

# Мониторинг ресурсов
./monitor_resources.sh ./reports/my_test &

# Проверка порогов
python3 check_thresholds.py reports/latest/results_stats.csv

# Анализ результатов
python3 analyze_results.py reports/latest/
```

## 🐳 Docker

```bash
# Распределенное тестирование (4 воркера)
docker-compose -f docker-compose.loadtest.yml up --scale worker=4

# Открыть Web UI
open http://localhost:8089

# Остановить
docker-compose -f docker-compose.loadtest.yml down
```

## 🌐 Web UI режим

```bash
# Запустить с Web интерфейсом
locust -f locustfile.py --host http://localhost:8000

# Открыть браузер
open http://localhost:8089
```

## 📚 Документация

- `README.md` - Полное руководство
- `EXAMPLES.md` - 12 практических примеров
- `LOAD_TESTING_SUMMARY.md` - Сводка проекта
- `LOAD_TESTING_IMPLEMENTATION.md` - Отчет

## ⚠️ Troubleshooting

```bash
# Backend не отвечает
docker-compose up -d backend
curl http://localhost:8000/health

# Locust не установлен
pip install -r requirements.txt

# Скрипты не executable
chmod +x *.sh

# Много ошибок в тестах
# 1. Проверьте логи backend
docker-compose logs backend

# 2. Уменьшите нагрузку
./run_load_tests.sh light

# 3. Проверьте ресурсы
docker stats
```

## 💡 Best Practices

1. **Всегда начинайте с light теста**
2. **Тестируйте на staging перед production**
3. **Мониторьте ресурсы во время тестов**
4. **Сохраняйте baseline результаты**
5. **Анализируйте все ошибки**

## 🔗 Полезные ссылки

- Locust Docs: https://docs.locust.io/
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- Backend API: http://localhost:8000/docs

---

**Быстрая помощь:** `python3 validate_setup.py`
