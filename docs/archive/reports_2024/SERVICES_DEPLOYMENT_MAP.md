# 🏗️ Slide Speaker - Схема развертывания сервисов

## 📊 **Архитектура развертывания:**

### 🚂 **Railway (Backend сервисы):**
- **Backend API** (FastAPI + Python)
- **Celery Workers** (фоновые задачи)
- **PostgreSQL** (база данных)
- **Redis** (кэш и очереди)

### 🌐 **Netlify (Frontend):**
- **Frontend** (React + TypeScript)

### ☁️ **Google Cloud (AI сервисы):**
- **Cloud Storage** (файлы)
- **Vision API** (OCR)
- **Gemini AI** (генерация контента)
- **Text-to-Speech** (аудио)

### 📊 **Мониторинг (опционально):**
- **Prometheus** (метрики)
- **Grafana** (дашборды)

---

## 🚂 **Railway - Backend сервисы:**

### 1. **Backend API** (Основной сервис)
```yaml
# Что включает:
- FastAPI приложение
- REST API endpoints
- WebSocket сервер
- Аутентификация (JWT)
- Файловая обработка
- Интеграция с Google AI
```

**Конфигурация:**
- **Dockerfile**: `Dockerfile.railway`
- **Порт**: `8000` (Railway автоматически назначает)
- **Переменные**: `railway.env.template`

### 2. **PostgreSQL** (База данных)
```yaml
# Что включает:
- Пользователи и аутентификация
- Уроки и презентации
- Метаданные файлов
- История обработки
```

**Конфигурация:**
- **Провайдер**: Railway PostgreSQL
- **Автоматически**: создается Railway
- **URL**: `DATABASE_URL` (автоматически)

### 3. **Redis** (Кэш и очереди)
```yaml
# Что включает:
- OCR кэширование (7 дней)
- LRU кэш в памяти
- Celery очереди задач
- WebSocket соединения
```

**Конфигурация:**
- **Провайдер**: Railway Redis
- **Автоматически**: создается Railway
- **URL**: `REDIS_URL` (автоматически)

### 4. **Celery Workers** (Фоновые задачи)
```yaml
# Что включает:
- Обработка презентаций
- OCR извлечение текста
- AI генерация контента
- TTS создание аудио
- Экспорт видео
```

**Конфигурация:**
- **Интеграция**: в основной Backend сервис
- **Очереди**: `default`, `processing`, `ai_generation`, `tts`, `export`

---

## 🌐 **Netlify - Frontend:**

### **Frontend** (React приложение)
```yaml
# Что включает:
- React + TypeScript UI
- Tailwind CSS стили
- Аутентификация
- Загрузка файлов
- Real-time прогресс
- Плеер результатов
```

**Конфигурация:**
- **Dockerfile**: `Dockerfile.netlify`
- **Nginx**: статический сервер
- **CDN**: Netlify CDN
- **Переменные**: `netlify.env.template`

---

## ☁️ **Google Cloud - AI сервисы:**

### 1. **Cloud Storage** (Файловое хранилище)
```yaml
# Что включает:
- Загруженные презентации
- Обработанные изображения
- Экспортированные видео
- Временные файлы
```

**Конфигурация:**
- **Bucket**: `slide-speaker-production-storage`
- **Провайдер**: Google Cloud Storage
- **Доступ**: через Service Account

### 2. **Vision API** (OCR)
```yaml
# Что включает:
- Извлечение текста из слайдов
- Определение элементов
- Координаты текста
- Уверенность распознавания
```

**Конфигурация:**
- **Лимит**: 1000 запросов/месяц бесплатно
- **Кэширование**: Redis (7 дней)

### 3. **Gemini AI** (Генерация контента)
```yaml
# Что включает:
- Анализ слайдов
- Генерация заметок докладчика
- Создание сценария
- Оптимизация контента
```

**Конфигурация:**
- **Модель**: `gemini-2.0-flash`
- **Лимит**: 15 запросов/минуту бесплатно

### 4. **Text-to-Speech** (Аудио)
```yaml
# Что включает:
- Создание аудио из текста
- Настройка голоса
- Контроль скорости
- SSML разметка
```

**Конфигурация:**
- **Голос**: `ru-RU-Wavenet-D`
- **Лимит**: 1M символов/месяц бесплатно

---

## 📊 **Мониторинг (опционально):**

### **Prometheus + Grafana**
```yaml
# Что включает:
- Метрики производительности
- Мониторинг API
- Отслеживание ошибок
- Дашборды
```

**Конфигурация:**
- **Развертывание**: отдельно (Railway или другой провайдер)
- **Доступ**: через VPN или приватную сеть

---

## 🔄 **Поток данных:**

```
1. Пользователь → Netlify Frontend
2. Frontend → Railway Backend API
3. Backend → Google Cloud Storage (файлы)
4. Backend → Google Vision API (OCR)
5. Backend → Google Gemini AI (контент)
6. Backend → Google TTS (аудио)
7. Backend → Redis (кэш)
8. Backend → PostgreSQL (данные)
9. Backend → Celery Workers (фоновые задачи)
10. Backend → WebSocket → Frontend (прогресс)
```

---

## 💰 **Стоимость по сервисам:**

| Сервис | Провайдер | Стоимость | Лимиты |
|--------|-----------|-----------|--------|
| **Backend API** | Railway | $0 | $5 кредитов/месяц |
| **PostgreSQL** | Railway | $0 | Включено в план |
| **Redis** | Railway | $0 | Включено в план |
| **Celery Workers** | Railway | $0 | Включено в план |
| **Frontend** | Netlify | $0 | 100GB трафика/месяц |
| **Cloud Storage** | Google | $0 | 5GB бесплатно |
| **Vision API** | Google | $0 | 1000 запросов/месяц |
| **Gemini AI** | Google | $0 | 15 запросов/минуту |
| **TTS** | Google | $0 | 1M символов/месяц |

---

## 🚀 **Порядок развертывания:**

### 1. **Railway Backend:**
```bash
# Деплой основного сервиса
railway up --detach

# Railway автоматически создаст:
# - PostgreSQL базу данных
# - Redis кэш
# - Переменные окружения
```

### 2. **Google Cloud:**
```bash
# Настройка Service Account
# Создание GCS bucket
# Настройка API ключей
```

### 3. **Netlify Frontend:**
```bash
# Загрузка архива на Netlify
# Настройка переменных окружения
# Настройка CORS в Railway
```

---

## 🔧 **Конфигурация сервисов:**

### **Railway переменные:**
```bash
# Основные
GOOGLE_API_KEY=your-key
GCP_PROJECT_ID=your-project
OCR_PROVIDER=vision
LLM_PROVIDER=gemini
TTS_PROVIDER=google
STORAGE=gcs

# Оптимизация
PIPELINE_MAX_PARALLEL_SLIDES=5
PIPELINE_MAX_PARALLEL_TTS=10
OCR_CACHE_TTL=604800

# CORS
CORS_ORIGINS=https://*.netlify.app
```

### **Netlify переменные:**
```bash
# API подключение
VITE_API_BASE=https://your-app.up.railway.app
VITE_WS_URL=wss://your-app.up.railway.app
```

---

## ✅ **Итог:**

**Все сервисы развертываются автоматически:**

- ✅ **Railway**: Backend + Database + Cache + Workers
- ✅ **Netlify**: Frontend + CDN
- ✅ **Google Cloud**: AI сервисы + Storage
- ✅ **Интеграция**: автоматическая через API

**Вы получаете полнофункциональное приложение без сложной настройки!** 🚀
