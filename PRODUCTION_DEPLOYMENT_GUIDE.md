# 🚀 Slide Speaker - Production Deployment Guide

## 📋 **Обзор архитектуры:**

- **Backend (Railway)**: FastAPI + Python + Google Cloud AI
- **Frontend (Netlify)**: React + TypeScript + Tailwind CSS
- **Storage**: Google Cloud Storage
- **Database**: PostgreSQL (Railway)
- **Cache**: Redis (Railway)

---

## 🔧 **Шаг 1: Подготовка Google Cloud**

### 1.1 Создайте Service Account:
```bash
# В Google Cloud Console
gcloud iam service-accounts create slide-speaker-production \
    --display-name="Slide Speaker Production Service Account"
```

### 1.2 Назначьте роли:
```bash
gcloud projects add-iam-policy-binding inspiring-keel-473421-j2 \
    --member="serviceAccount:slide-speaker-production@inspiring-keel-473421-j2.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding inspiring-keel-473421-j2 \
    --member="serviceAccount:slide-speaker-production@inspiring-keel-473421-j2.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding inspiring-keel-473421-j2 \
    --member="serviceAccount:slide-speaker-production@inspiring-keel-473421-j2.iam.gserviceaccount.com" \
    --role="roles/ml.developer"
```

### 1.3 Создайте JSON ключ:
```bash
gcloud iam service-accounts keys create gcp-sa-production.json \
    --iam-account=slide-speaker-production@inspiring-keel-473421-j2.iam.gserviceaccount.com
```

### 1.4 Создайте GCS bucket:
```bash
gsutil mb gs://slide-speaker-production-storage
gsutil iam ch serviceAccount:slide-speaker-production@inspiring-keel-473421-j2.iam.gserviceaccount.com:objectAdmin gs://slide-speaker-production-storage
```

---

## 🚂 **Шаг 2: Деплой Backend на Railway**

### 2.1 Создайте проект в Railway:
```bash
# Установите Railway CLI
npm install -g @railway/cli

# Войдите в аккаунт
railway login

# Создайте новый проект
railway init --name slide-speaker-backend
```

### 2.2 Настройте переменные окружения:
```bash
# Скопируйте переменные из railway.env.template
railway variables set GOOGLE_API_KEY="AIzaSyDNEtewj8q9qGWELrR-KS0mwcMTr4TGjA0"
railway variables set GCP_PROJECT_ID="inspiring-keel-473421-j2"
railway variables set OCR_PROVIDER="vision"
railway variables set LLM_PROVIDER="gemini"
railway variables set TTS_PROVIDER="google"
railway variables set STORAGE="gcs"
railway variables set CORS_ORIGINS="https://*.netlify.app,https://*.netlify.com"
```

### 2.3 Загрузите Service Account ключ:
```bash
# Загрузите JSON ключ в Railway
railway variables set GOOGLE_APPLICATION_CREDENTIALS_JSON="$(cat gcp-sa-production.json)"
```

### 2.4 Деплой:
```bash
# Деплой backend
railway up --detach
```

### 2.5 Получите URL:
```bash
# Получите URL вашего Railway приложения
railway status --json | jq '.services.edges[0].node.serviceInstances.edges[0].node.latestDeployment.url'
```

---

## 🌐 **Шаг 3: Деплой Frontend на Netlify**

### 3.1 Подготовьте фронтенд:
```bash
# Обновите переменные окружения в netlify.toml
# Замените your-railway-app на реальный URL из Railway
```

### 3.2 Деплой через веб-интерфейс Netlify:

#### Вариант A: Drag & Drop
1. Откройте [netlify.com](https://netlify.com)
2. Нажмите "Add new site" → "Deploy manually"
3. Перетащите папку проекта в область загрузки
4. Настройте переменные окружения в Site Settings

#### Вариант B: GitHub Integration
1. Загрузите код в GitHub репозиторий
2. Подключите репозиторий к Netlify
3. Настройте переменные окружения

### 3.3 Настройте переменные окружения в Netlify:
```bash
VITE_API_BASE=https://your-railway-app.up.railway.app
VITE_WS_URL=wss://your-railway-app.up.railway.app
```

---

## 🔗 **Шаг 4: Настройка интеграции**

### 4.1 Обновите CORS в Railway:
```bash
# Добавьте ваш Netlify URL в CORS
railway variables set CORS_ORIGINS="https://your-netlify-app.netlify.app,https://*.netlify.app"
```

### 4.2 Обновите переменные в Netlify:
```bash
# Обновите API URL в Netlify
VITE_API_BASE=https://your-railway-app.up.railway.app
VITE_WS_URL=wss://your-railway-app.up.railway.app
```

---

## ✅ **Шаг 5: Тестирование**

### 5.1 Проверьте Backend:
```bash
# Проверьте API
curl https://your-railway-app.up.railway.app/health

# Проверьте WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" https://your-railway-app.up.railway.app/api/ws/progress/test
```

### 5.2 Проверьте Frontend:
1. Откройте ваш Netlify URL
2. Попробуйте загрузить тестовую презентацию
3. Проверьте real-time обновления

---

## 📊 **Мониторинг и оптимизация**

### 6.1 Railway мониторинг:
- Откройте Railway Dashboard
- Проверьте логи и метрики
- Настройте алерты при превышении лимитов

### 6.2 Netlify мониторинг:
- Откройте Netlify Dashboard
- Проверьте аналитику трафика
- Настройте формы и функции

### 6.3 Google Cloud мониторинг:
- Откройте Google Cloud Console
- Проверьте использование API
- Настройте алерты при превышении квот

---

## 💰 **Стоимость и лимиты**

### Railway (Backend):
- **Бесплатно**: $5 кредитов в месяц (≈ 500 часов)
- **Платно**: $5/месяц за дополнительные ресурсы

### Netlify (Frontend):
- **Бесплатно**: 100GB трафика в месяц
- **Платно**: $19/месяц за дополнительные функции

### Google Cloud:
- **Бесплатно**: $300 кредитов для новых пользователей
- **Vision API**: 1000 запросов/месяц бесплатно
- **Gemini AI**: 15 запросов/минуту бесплатно
- **TTS**: 1M символов/месяц бесплатно
- **Storage**: 5GB бесплатно

---

## 🎯 **Ожидаемая производительность**

### Без оптимизации:
- **22-33 пользователя** в месяц
- **66 презентаций** в месяц

### С оптимизациями:
- **26-92 пользователя** в месяц
- **132 презентации** в месяц

### С дополнительными оптимизациями:
- **55-185 пользователей** в месяц
- **277 презентаций** в месяц

---

## 🚨 **Устранение неполадок**

### Проблема: CORS ошибки
```bash
# Решение: Обновите CORS_ORIGINS в Railway
railway variables set CORS_ORIGINS="https://your-netlify-app.netlify.app"
```

### Проблема: API не отвечает
```bash
# Решение: Проверьте логи Railway
railway logs --tail 50
```

### Проблема: WebSocket не работает
```bash
# Решение: Проверьте переменные окружения
railway variables
```

---

## 🎉 **Готово!**

После выполнения всех шагов у вас будет:
- ✅ Полнофункциональное приложение Slide Speaker
- ✅ Backend на Railway с Google AI
- ✅ Frontend на Netlify с современным UI
- ✅ Real-time обновления через WebSocket
- ✅ Масштабируемая архитектура
- ✅ Мониторинг и алерты

**Ваш Slide Speaker готов к продакшену!** 🚀
