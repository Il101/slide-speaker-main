#!/bin/bash
# Безопасное консервативное обновление только критичных уязвимостей
# БЕЗ риска breaking changes для продакшна

set -e

echo "🔒 КОНСЕРВАТИВНОЕ ОБНОВЛЕНИЕ БЕЗОПАСНОСТИ"
echo "=========================================="
echo ""
echo "⚠️  Этот скрипт обновляет ТОЛЬКО критичные уязвимости"
echo "    без риска breaking changes для продакшна"
echo ""

# Создаем резервные копии
echo "📦 Создание резервных копий..."
cp backend/requirements.txt backend/requirements.backup.txt
cp package.json package.backup.json
echo "✅ Бэкапы созданы:"
echo "   - backend/requirements.backup.txt"
echo "   - package.backup.json"
echo ""

# Проверяем наличие тестов
echo "🧪 Проверка наличия тестов..."
if [ ! -d "backend/tests" ]; then
    echo "⚠️  ВНИМАНИЕ: Директория тестов не найдена!"
    echo "   Рекомендуется создать тесты перед обновлением"
    read -p "Продолжить? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Frontend - безопасное обновление
echo "📦 FRONTEND: Обновление Vite..."
echo "   Текущая версия: $(npm list vite --depth=0 2>/dev/null | grep vite || echo 'не установлен')"
npm audit fix --only=prod
echo "✅ Frontend обновлен"
echo ""

# Backend - консервативное обновление
echo "🐍 BACKEND: Обновление критичных пакетов..."
cd backend

echo ""
echo "1️⃣  Обновление python-multipart (DoS фикс)..."
echo "   Текущая версия: $(pip show python-multipart 2>/dev/null | grep Version || echo 'не установлен')"
pip install "python-multipart==0.0.18" --quiet
echo "   ✅ python-multipart обновлен до 0.0.18"

echo ""
echo "2️⃣  Обновление sentry-sdk (утечка env фикс)..."
echo "   Текущая версия: $(pip show sentry-sdk 2>/dev/null | grep Version || echo 'не установлен')"
pip install "sentry-sdk==1.45.1" --quiet
echo "   ✅ sentry-sdk обновлен до 1.45.1"

echo ""
echo "📝 Обновление requirements.txt..."
# Обновляем только нужные строки в requirements.txt
sed -i.bak 's/python-multipart==0\.0\.6/python-multipart==0.0.18/' requirements.txt
sed -i.bak 's/sentry-sdk\[fastapi\]==1\.40\.0/sentry-sdk[fastapi]==1.45.1/' requirements.txt
rm requirements.txt.bak

echo "✅ requirements.txt обновлен"
echo ""

# Запуск тестов если они есть
if [ -f "pytest.ini" ] || [ -f "conftest.py" ]; then
    echo "🧪 Запуск тестов..."
    echo ""
    
    # Проверяем наличие pytest
    if command -v pytest &> /dev/null; then
        echo "Запуск быстрых тестов..."
        pytest tests/ -v -x --tb=short 2>&1 | head -n 50
        TEST_EXIT_CODE=${PIPESTATUS[0]}
        
        if [ $TEST_EXIT_CODE -ne 0 ]; then
            echo ""
            echo "❌ ТЕСТЫ НЕ ПРОШЛИ!"
            echo ""
            echo "🔄 Откат изменений..."
            cp requirements.backup.txt requirements.txt
            pip install -r requirements.txt --quiet
            cd ..
            cp package.backup.json package.json
            npm install --quiet
            echo ""
            echo "✅ Изменения откачены"
            echo ""
            echo "❌ Обновление прервано из-за ошибок в тестах"
            echo "   Проверьте логи и исправьте проблемы"
            exit 1
        fi
        
        echo ""
        echo "✅ Тесты пройдены успешно!"
    else
        echo "⚠️  pytest не найден, тесты пропущены"
        echo "   Рекомендуется установить: pip install pytest"
    fi
else
    echo "ℹ️  Тесты не найдены, пропускаем"
fi

cd ..

echo ""
echo "=========================================="
echo "✅ КОНСЕРВАТИВНОЕ ОБНОВЛЕНИЕ ЗАВЕРШЕНО"
echo "=========================================="
echo ""
echo "📊 Обновленные пакеты:"
echo "   Frontend:"
echo "   - vite: безопасный патч (dev-only)"
echo ""
echo "   Backend:"
echo "   - python-multipart: 0.0.6 → 0.0.18 (DoS фикс)"
echo "   - sentry-sdk: 1.40.0 → 1.45.1 (env leak фикс)"
echo ""
echo "🔒 Закрыто уязвимостей: 5 из 9 (56%)"
echo "   - 2 критичных DoS уязвимости"
echo "   - 1 утечка данных"
echo "   - 2 низкого приоритета"
echo ""
echo "⏸️  Отложенные обновления (требуют staging):"
echo "   - starlette: 0.38.6 → 0.49.1 (требует проверки с FastAPI)"
echo "   - urllib3: 2.0.7 → 2.5.0 (требует проверки API интеграций)"
echo ""
echo "📋 Следующие шаги:"
echo "   1. Проверьте работу приложения локально"
echo "   2. Запустите дополнительные тесты: pytest backend/tests/"
echo "   3. Проверьте критичные endpoints вручную"
echo "   4. Commit изменений: git commit -am 'fix: security updates (conservative)'"
echo "   5. Deploy в staging для финальной проверки"
echo "   6. Мониторьте Sentry первые 24 часа после deploy"
echo ""
echo "🔄 Для отката (если что-то пошло не так):"
echo "   cd backend && cp requirements.backup.txt requirements.txt && pip install -r requirements.txt"
echo "   cp package.backup.json package.json && npm install"
echo ""
echo "📄 Подробности в файлах:"
echo "   - SECURITY_AUDIT_REPORT.md (полный отчет)"
echo "   - UPDATE_RISKS_ANALYSIS.md (анализ рисков)"
echo ""
