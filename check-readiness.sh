#!/bin/bash

# Slide Speaker Deployment Readiness Check
# Проверка готовности к деплою

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
log_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_check() {
    echo -e "${BLUE}[?]${NC} $1"
}

echo "🔍 Slide Speaker - Проверка готовности к деплою"
echo "=============================================="

# Счетчики
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Подгружаем локальные переменные, если есть backend/.env
if [ -f "./backend/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source ./backend/.env
    set +a
fi

# Функция для проверки
check_item() {
    local description="$1"
    local command="$2"
    local required="$3"  # true/false
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if eval "$command" &> /dev/null; then
        log_info "$description"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        if [ "$required" = "true" ]; then
            log_error "$description"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            log_warn "$description"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
        fi
        return 1
    fi
}

check_env_var() {
    local var_name="$1"
    local required="$2"
    local value="${!var_name}"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -n "$value" ]; then
        log_info "Переменная $var_name задана"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        if [ "$required" = "true" ]; then
            log_error "Переменная $var_name не задана"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            log_warn "Переменная $var_name не задана (необязательно)"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
        fi
    fi
}

echo ""
echo "📋 Проверка файлов конфигурации..."

# Проверка файлов Railway
check_item "Dockerfile.railway существует" "[ -f 'Dockerfile.railway' ]" "true"
check_item "railway.json существует" "[ -f 'railway.json' ]" "true"
check_item ".railwayignore существует" "[ -f '.railwayignore' ]" "true"
check_item "railway.env.template существует" "[ -f 'railway.env.template' ]" "true"

# Проверка файлов Netlify
check_item "Dockerfile.netlify существует" "[ -f 'Dockerfile.netlify' ]" "true"
check_item "nginx.conf существует" "[ -f 'nginx.conf' ]" "true"
check_item "netlify.toml существует" "[ -f 'netlify.toml' ]" "true"
check_item "netlify.env.template существует" "[ -f 'netlify.env.template' ]" "true"
check_item "render.yaml существует" "[ -f 'render.yaml' ]" "true"

# Проверка скриптов
check_item "deploy.sh существует и исполняемый" "[ -x 'deploy.sh' ]" "true"

echo ""
echo "🔧 Проверка зависимостей..."

# Проверка Railway CLI
check_item "Railway CLI установлен" "command -v railway" "true"

# Проверка Google Cloud CLI (опционально)
check_item "Google Cloud CLI установлен" "command -v gcloud" "false"

# Проверка Node.js
check_item "Node.js установлен" "command -v node" "true"

# Проверка npm
check_item "npm установлен" "command -v npm" "true"

echo ""
echo "☁️ Проверка Google Cloud API..."

# Проверка API ключа
if [ -n "$GOOGLE_API_KEY" ]; then
    log_info "GOOGLE_API_KEY установлен"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_warn "GOOGLE_API_KEY не установлен (будет взят из railway.env.template)"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Проверка GCP Project ID
if [ -n "$GCP_PROJECT_ID" ]; then
    log_info "GCP_PROJECT_ID установлен"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_warn "GCP_PROJECT_ID не установлен (будет взят из railway.env.template)"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo "🔐 Критичные переменные окружения (Render)..."
check_env_var "JWT_SECRET_KEY" "true"
check_env_var "DATABASE_URL" "true"
check_env_var "REDIS_URL" "true"

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if [ -n "$GCP_SERVICE_ACCOUNT_JSON" ] || [ -f "./keys/gcp-sa.json" ]; then
    log_info "GCP credentials доступны (env или файл)"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "GCP credentials не найдены (нет GCP_SERVICE_ACCOUNT_JSON и keys/gcp-sa.json)"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""
echo "📊 Проверка конфигурации проекта..."

# Проверка CORS настроек
if grep -q "netlify.app" backend/app/core/config.py; then
    log_info "CORS настроен для Netlify"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "CORS не настроен для Netlify"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Проверка переменных окружения в шаблонах
if grep -q "VITE_API_BASE" netlify.env.template; then
    log_info "Netlify переменные настроены"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "Netlify переменные не настроены"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo "📋 Итоговая оценка готовности:"
echo "==============================="

echo "Всего проверок: $TOTAL_CHECKS"
echo -e "${GREEN}Пройдено: $PASSED_CHECKS${NC}"
echo -e "${YELLOW}Предупреждения: $WARNING_CHECKS${NC}"
echo -e "${RED}Ошибки: $FAILED_CHECKS${NC}"

echo ""
if [ $FAILED_CHECKS -eq 0 ]; then
    if [ $WARNING_CHECKS -eq 0 ]; then
        echo -e "${GREEN}🎉 ОТЛИЧНО! Проект полностью готов к деплою!${NC}"
        echo ""
        echo "Можете запускать деплой:"
        echo "  ./deploy.sh"
        exit 0
    else
        echo -e "${YELLOW}⚠️ ХОРОШО! Проект готов к деплою с предупреждениями.${NC}"
        echo ""
        echo "Рекомендуется исправить предупреждения, но деплой возможен:"
        echo "  ./deploy.sh"
        exit 0
    fi
else
    echo -e "${RED}❌ ОШИБКИ! Проект не готов к деплою.${NC}"
    echo ""
    echo "Исправьте ошибки перед деплоем:"
    echo "  1. Установите недостающие зависимости"
    echo "  2. Настройте конфигурационные файлы"
    echo "  3. Запустите проверку снова: ./check-readiness.sh"
    exit 1
fi
