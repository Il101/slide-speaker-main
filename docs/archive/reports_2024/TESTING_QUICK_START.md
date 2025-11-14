# Testing Quick Start 🚀

**3-минутный гайд для запуска тестов**

---

## ⚡ Быстрый Старт

### Backend

```bash
# 1. Установить зависимости
cd backend
pip install -r requirements-test.txt

# 2. Запустить тесты
pytest

# 3. Посмотреть coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Frontend

```bash
# 1. Установить зависимости
npm install

# 2. Запустить тесты
npm test

# 3. Посмотреть coverage
npm run test:coverage
```

### Pre-commit Hooks

```bash
# 1. Установить
pip install pre-commit
pre-commit install

# 2. Использовать
git commit -m "message"  # Автоматически запустятся проверки
```

---

## 📁 Что Создано

### Конфигурация
```
✅ backend/pytest.ini         - Pytest config
✅ backend/conftest.py        - Test fixtures  
✅ .github/workflows/ci.yml   - CI/CD pipeline
✅ .pre-commit-config.yaml    - Pre-commit hooks
```

### Тесты
```
✅ backend/tests/unit/test_provider_factory.py  (15 tests)
✅ backend/tests/unit/test_pipeline_base.py     (12 tests)
✅ backend/tests/integration/               (готово к добавлению)
✅ backend/tests/e2e/                       (готово к добавлению)
```

### Документация
```
✅ TESTING_GUIDE.md                   - Полное руководство
✅ TESTING_IMPLEMENTATION_COMPLETE.md - Отчет о реализации
✅ CODE_QUALITY_AUDIT_2025.md         - Аудит качества
```

---

## 🎯 Команды для Ежедневной Работы

### Запуск Тестов

```bash
# Все тесты
pytest

# Только unit
pytest tests/unit

# Только integration
pytest tests/integration

# С coverage
pytest --cov=app --cov-report=term-missing

# Параллельно (быстрее)
pytest -n auto

# Остановиться на первой ошибке
pytest -x

# Показать print statements
pytest -s

# Самые медленные тесты
pytest --durations=10
```

### Проверка Coverage

```bash
# Проверить threshold (70%)
pytest --cov=app --cov-fail-under=70

# HTML отчет
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Terminal отчет
pytest --cov=app --cov-report=term-missing
```

### Pre-commit

```bash
# Запустить на всех файлах
pre-commit run --all-files

# Запустить конкретный hook
pre-commit run black
pre-commit run pytest-check

# Пропустить (экстренный случай!)
git commit --no-verify
```

---

## 🔍 Примеры Тестов

### Unit Test

```python
# tests/unit/test_my_service.py
import pytest

class TestMyService:
    def test_basic_function(self):
        from app.services.my_service import my_function
        
        result = my_function("input")
        
        assert result == "expected"
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        from app.services.my_service import my_async_function
        
        result = await my_async_function("input")
        
        assert result == "expected"
```

### Integration Test

```python
# tests/integration/test_api.py
import pytest

@pytest.mark.integration
async def test_create_lesson(test_client, test_user):
    response = await test_client.post(
        "/api/lessons",
        json={"title": "Test"},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 201
    assert response.json()["title"] == "Test"
```

---

## 🚨 Troubleshooting

### Проблема: Тесты не запускаются

```bash
# Решение 1: Переустановить зависимости
pip install --force-reinstall -r requirements-test.txt

# Решение 2: Очистить cache
pytest --cache-clear
rm -rf .pytest_cache
```

### Проблема: Coverage не работает

```bash
# Удалить старые данные
rm .coverage coverage.xml

# Переустановить pytest-cov
pip install --force-reinstall pytest-cov
```

### Проблема: Pre-commit ломается

```bash
# Переустановить
pre-commit uninstall
pre-commit install

# Обновить
pre-commit autoupdate
```

---

## 📊 Текущий Статус

### ✅ Готово
- Pytest конфигурация
- Conftest с fixtures
- 27+ unit тестов
- CI/CD pipeline (7 jobs)
- Pre-commit hooks (20+ проверок)
- Полная документация

### 🔄 В Процессе
- API integration тесты
- Frontend unit тесты
- E2E тесты

### 🎯 Цели
- **Coverage**: 70%+ (текущий: ~40%)
- **Tests**: 100+ unit тестов
- **CI/CD**: Все проверки зелёные

---

## 📖 Полная Документация

- **TESTING_GUIDE.md** - Детальное руководство (200+ строк)
- **TESTING_IMPLEMENTATION_COMPLETE.md** - Отчет о реализации
- **CODE_QUALITY_AUDIT_2025.md** - Аудит и рекомендации

---

## ✅ Checklist Перед Коммитом

```bash
□ Написаны тесты для нового кода
□ Тесты проходят: pytest
□ Coverage не упал: pytest --cov
□ Pre-commit hooks прошли
□ Код отформатирован (black)
```

---

## 🎉 Быстрый Старт - TL;DR

```bash
# 1. Установить всё
cd backend && pip install -r requirements-test.txt
cd .. && npm install
pip install pre-commit && pre-commit install

# 2. Запустить тесты
cd backend && pytest
cd .. && npm test

# 3. Коммитить
git add .
git commit -m "feat: my feature"  # Pre-commit запустится автоматически

# 4. Push (CI/CD запустится автоматически)
git push
```

**Готово! Теперь у вас профессиональное тестирование** 🎊

---

**Вопросы?** Смотрите `TESTING_GUIDE.md` или создайте issue!
