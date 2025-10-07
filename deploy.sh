#!/bin/bash

# Slide Speaker Production Deployment Script
# Автоматический деплой на Railway и Netlify

set -e

echo "🚀 Slide Speaker Production Deployment"
echo "======================================"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI не установлен. Установите: npm install -g @railway/cli"
        exit 1
    fi
    
    if ! command -v gcloud &> /dev/null; then
        log_warn "Google Cloud CLI не установлен. Установите: https://cloud.google.com/sdk/docs/install"
    fi
    
    log_info "✅ Зависимости проверены"
}

# Настройка Google Cloud
setup_google_cloud() {
    log_info "Настройка Google Cloud..."
    
    if [ ! -f "gcp-sa-production.json" ]; then
        log_warn "Service Account ключ не найден. Создайте его вручную:"
        echo "gcloud iam service-accounts keys create gcp-sa-production.json \\"
        echo "    --iam-account=slide-speaker-production@inspiring-keel-473421-j2.iam.gserviceaccount.com"
        read -p "Продолжить без Service Account ключа? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_info "✅ Service Account ключ найден"
    fi
}

# Деплой на Railway
deploy_railway() {
    log_info "Деплой Backend на Railway..."
    
    # Проверка авторизации Railway
    if ! railway whoami &> /dev/null; then
        log_error "Не авторизован в Railway. Выполните: railway login"
        exit 1
    fi
    
    # Создание проекта если не существует
    if ! railway status &> /dev/null; then
        log_info "Создание нового Railway проекта..."
        railway init --name slide-speaker-backend
    fi
    
    # Настройка переменных окружения
    log_info "Настройка переменных окружения..."
    
    if [ -f "gcp-sa-production.json" ]; then
        railway variables set GOOGLE_APPLICATION_CREDENTIALS_JSON="$(cat gcp-sa-production.json)"
    fi
    
    railway variables set GOOGLE_API_KEY="AIzaSyDNEtewj8q9qGWELrR-KS0mwcMTr4TGjA0"
    railway variables set GCP_PROJECT_ID="inspiring-keel-473421-j2"
    railway variables set OCR_PROVIDER="vision"
    railway variables set LLM_PROVIDER="gemini"
    railway variables set TTS_PROVIDER="google"
    railway variables set STORAGE="gcs"
    railway variables set CORS_ORIGINS="https://*.netlify.app,https://*.netlify.com"
    railway variables set PIPELINE_MAX_PARALLEL_SLIDES="5"
    railway variables set PIPELINE_MAX_PARALLEL_TTS="10"
    railway variables set OCR_CACHE_TTL="604800"
    
    # Деплой
    log_info "Запуск деплоя..."
    railway up --detach
    
    # Получение URL
    log_info "Получение URL приложения..."
    RAILWAY_URL=$(railway status --json | jq -r '.services.edges[0].node.serviceInstances.edges[0].node.latestDeployment.url')
    
    if [ "$RAILWAY_URL" != "null" ] && [ -n "$RAILWAY_URL" ]; then
        log_info "✅ Railway URL: $RAILWAY_URL"
        echo "RAILWAY_URL=$RAILWAY_URL" > .env.production
    else
        log_error "Не удалось получить Railway URL"
        exit 1
    fi
}

# Подготовка фронтенда для Netlify
prepare_netlify() {
    log_info "Подготовка фронтенда для Netlify..."
    
    # Обновление переменных окружения
    if [ -f ".env.production" ]; then
        source .env.production
        sed -i.bak "s|https://your-railway-app.up.railway.app|$RAILWAY_URL|g" netlify.toml
        sed -i.bak "s|wss://your-railway-app.up.railway.app|wss://${RAILWAY_URL#https://}|g" netlify.toml
        log_info "✅ Переменные окружения обновлены"
    else
        log_warn "Файл .env.production не найден. Обновите netlify.toml вручную"
    fi
    
    # Создание архива для деплоя
    log_info "Создание архива для Netlify..."
    tar -czf netlify-deploy.tar.gz \
        src/ public/ package.json package-lock.json \
        vite.config.ts tailwind.config.ts postcss.config.js \
        tsconfig*.json components.json netlify.toml nginx.conf \
        Dockerfile.netlify
    
    log_info "✅ Архив создан: netlify-deploy.tar.gz"
}

# Тестирование деплоя
test_deployment() {
    log_info "Тестирование деплоя..."
    
    if [ -f ".env.production" ]; then
        source .env.production
        
        # Тест API
        log_info "Тестирование API..."
        if curl -f "$RAILWAY_URL/health" &> /dev/null; then
            log_info "✅ API работает"
        else
            log_error "❌ API не отвечает"
        fi
        
        # Тест WebSocket
        log_info "Тестирование WebSocket..."
        if curl -f "$RAILWAY_URL/api/ws/progress/test" &> /dev/null; then
            log_info "✅ WebSocket работает"
        else
            log_warn "⚠️ WebSocket может не работать (это нормально для curl)"
        fi
    else
        log_warn "Не удалось протестировать деплой (нет .env.production)"
    fi
}

# Основная функция
main() {
    echo "Выберите действие:"
    echo "1) Полный деплой (Railway + подготовка Netlify)"
    echo "2) Только Railway"
    echo "3) Только подготовка Netlify"
    echo "4) Тестирование"
    read -p "Введите номер (1-4): " choice
    
    case $choice in
        1)
            check_dependencies
            setup_google_cloud
            deploy_railway
            prepare_netlify
            test_deployment
            ;;
        2)
            check_dependencies
            setup_google_cloud
            deploy_railway
            test_deployment
            ;;
        3)
            prepare_netlify
            ;;
        4)
            test_deployment
            ;;
        *)
            log_error "Неверный выбор"
            exit 1
            ;;
    esac
    
    log_info "🎉 Деплой завершен!"
    echo ""
    echo "Следующие шаги:"
    echo "1. Загрузите netlify-deploy.tar.gz на Netlify"
    echo "2. Настройте переменные окружения в Netlify"
    echo "3. Обновите CORS_ORIGINS в Railway с вашим Netlify URL"
    echo "4. Протестируйте приложение"
}

# Запуск
main "$@"
