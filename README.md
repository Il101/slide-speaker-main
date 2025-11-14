# 🎓 Slide Speaker - AI-Powered Presentation Intelligence Platform

> Превращаем статичные презентации в интерактивные обучающие видео с профессиональной озвучкой, визуальными эффектами и интеллектуальным анализом контента.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg)](https://reactjs.org)

## 🌟 О проекте

**Slide Speaker** - это комплексная платформа для автоматического создания обучающих видео из презентаций (PPTX/PDF) с использованием искусственного интеллекта. Система анализирует контент слайдов, генерирует профессиональные лекторские комментарии, создает озвучку и добавляет синхронизированные визуальные эффекты.

### ✨ Ключевые возможности

- 🤖 **Интеллектуальный анализ презентаций** - автоматическое извлечение текста, изображений и структурных элементов
- 🎙️ **Профессиональная озвучка** - генерация естественной речи с поддержкой множества языков и голосов
- 🎬 **Визуальные эффекты** - синхронизированные подсветки, анимации и переходы
- 📊 **Аналитика и отслеживание** - мониторинг использования, стоимости API и производительности
- 👥 **Многопользовательская система** - аутентификация, подписки и управление контентом
- 🎯 **Генерация квизов** - автоматическое создание тестов по содержанию презентации
- 📚 **Плейлисты** - организация и управление коллекциями видео-лекций
- 🌐 **Мультиязычность** - автоматическое определение языка и перевод контента
- 🔄 **Параллельная обработка** - оптимизированный pipeline с кэшированием результатов

## 🏗️ Архитектура

### Технологический стек

#### Backend
- **FastAPI** 0.115.0 - современный асинхронный веб-фреймворк
- **PostgreSQL** 15 - основная база данных
- **Redis** 7 - кэширование и очереди задач
- **Celery** - асинхронная обработка задач
- **SQLAlchemy** 2.0 - ORM с поддержкой async
- **Alembic** - миграции базы данных

#### Frontend
- **React** 18.3.1 + **TypeScript** 5.8.3
- **Vite** 7.1.7 - сборщик и dev-сервер
- **Tailwind CSS** 3.4.17 - utility-first CSS
- **Radix UI** - доступные компоненты
- **React Query** (@tanstack/react-query) - управление состоянием сервера
- **React Router** 6.30.1 - маршрутизация

#### AI & ML Services
- **Google Cloud Document AI** - OCR и анализ документов
- **Google Cloud Text-to-Speech** - синтез речи
- **OpenAI GPT** / **Anthropic Claude** - генерация контента
- **Google Gemini** / **xAI Grok** - мультимодальный анализ (через OpenRouter)
- **OpenAI Whisper** - распознавание речи для синхронизации
- **Silero TTS** - локальная альтернатива TTS

#### Storage & Infrastructure
- **MinIO** - S3-совместимое хранилище файлов
- **Google Cloud Storage** - опциональное облачное хранилище
- **Docker** + **Docker Compose** - контейнеризация
- **Prometheus** + **Grafana** - мониторинг и метрики
- **Sentry** - отслеживание ошибок

#### Video Processing
- **FFmpeg** - обработка видео и аудио
- **MoviePy** - генерация MP4 с эффектами
- **OpenCV** - обработка изображений (headless)
- **PyMuPDF** / **python-pptx** - парсинг PDF/PPTX

### Структура проекта

```
slide-speaker-main/
├── backend/                    # Backend приложение (FastAPI)
│   ├── app/
│   │   ├── api/               # API роутеры (auth, lessons, analytics, quizzes, etc.)
│   │   ├── core/              # Ядро (config, logging, auth, database)
│   │   ├── models/            # SQLAlchemy модели и Pydantic схемы
│   │   ├── pipeline/          # Система обработки презентаций
│   │   │   ├── base.py        # Базовый класс Pipeline
│   │   │   └── intelligent_optimized.py  # Оптимизированный pipeline
│   │   ├── services/          # Бизнес-логика
│   │   │   ├── providers/     # AI провайдеры (OCR, LLM, TTS)
│   │   │   ├── sprint1/       # Парсинг документов
│   │   │   ├── sprint2/       # AI генерация контента
│   │   │   └── sprint3/       # Экспорт видео и очереди
│   │   └── tasks.py           # Celery задачи
│   ├── alembic/               # Миграции БД
│   ├── requirements.txt       # Python зависимости
│   └── Dockerfile
│
├── src/                       # Frontend приложение (React + TS)
│   ├── components/            # React компоненты
│   │   ├── Player.tsx         # Основной плеер презентаций
│   │   ├── FileUploader.tsx   # Загрузка файлов
│   │   ├── QuizGenerator.tsx  # Генератор квизов
│   │   └── Navigation.tsx     # Навигация
│   ├── pages/                 # Страницы приложения
│   │   ├── Index.tsx          # Главная страница
│   │   ├── Analytics.tsx      # Аналитика
│   │   ├── PlaylistsPage.tsx  # Плейлисты
│   │   └── SubscriptionPage.tsx
│   ├── contexts/              # React контексты (AuthContext)
│   ├── hooks/                 # Custom hooks
│   ├── lib/                   # Утилиты (API client, analytics)
│   └── types/                 # TypeScript типы
│
├── docs/                      # Документация
│   ├── reports/               # Отчеты о разработке (48 файлов)
│   ├── guides/                # Руководства пользователя (12 файлов)
│   └── README.md
│
├── scripts/                   # Утилитные скрипты
│   ├── integration/           # Интеграционные тесты (55 файлов)
│   ├── setup/                 # Скрипты настройки (10 файлов)
│   └── maintenance/           # Обслуживание (8 файлов)
│
├── monitoring/                # Конфигурация мониторинга
│   ├── prometheus.yml
│   └── grafana/
│
├── tests/                     # Frontend тесты
├── keys/                      # Ключи и credentials
├── docker-compose.yml         # Оркестрация сервисов
└── README.md
```

## 🔄 Система обработки (Intelligent Pipeline)

**Slide Speaker** использует **OptimizedIntelligentPipeline** - продвинутую систему обработки презентаций с интеллектуальным анализом контента, параллельной обработкой и многоуровневым кэшированием.

### Основные этапы обработки

#### 1️⃣ **Парсинг документа** (Stage 1)
- Извлечение слайдов из PPTX/PDF с сохранением качества
- Конвертация в высококачественные PNG изображения
- OCR через Google Cloud Document AI с распознаванием структуры
- **Redis кэширование** результатов OCR для мгновенного повторного использования

#### 2️⃣ **Интеллектуальный анализ** (Stage 2-3)
- **PresentationIntelligence** - определение типа презентации, целевой аудитории и контекста
- **SemanticAnalyzer** - глубокий семантический анализ содержимого слайдов
- **ContentIntelligence** - извлечение ключевых концепций, терминов и взаимосвязей
- **SmartScriptGenerator** - генерация естественного лекторского текста с учетом контекста
- **Параллельная обработка** до 5 слайдов одновременно (настраивается)

#### 3️⃣ **Генерация речи** (Stage 4)
- Преобразование лекторского текста в SSML с маркерами произношения
- Синтез речи через:
  - Google Cloud Text-to-Speech (Wavenet, Neural2)
  - Azure Cognitive Services
  - Silero TTS (локально, бесплатно)
- **Whisper-based синхронизация** для точной привязки слов к времени
- **BulletPointSyncService** для синхронизации с маркерами списков

#### 4️⃣ **Визуальные эффекты** (Stage 5)
- **VisualEffectsEngine** - генерация cue points для анимации
- Создание подсветок (highlight), подчеркиваний (underline), указки (laser_move)
- Точная синхронизация эффектов с речью (< 200ms погрешность)
- Создание финального манифеста с тайминами

#### 5️⃣ **Экспорт видео** (опционально)
- Рендеринг MP4 с визуальными эффектами через FFmpeg/MoviePy
- Композитинг слайдов, аудио и анимаций
- Асинхронная обработка через **Celery** worker
- Сохранение в **MinIO** (S3-compatible) или **Google Cloud Storage**

### Ключевые оптимизации

- ✅ **Параллельная обработка** слайдов (5x ускорение)
- ✅ **Redis кэширование** OCR результатов (мгновенное повторное использование)
- ✅ **Batch запросы** к AI сервисам (снижение latency)
- ✅ **Умное кэширование** промежуточных результатов
- ✅ **Graceful degradation** при недоступности сервисов
- ✅ **Memory-efficient TTS** с учетом лимитов Docker (3.8GB)

**Результат:** До 77% улучшения производительности, снижение стоимости API на 30-50%.

### AI модели и провайдеры

#### LLM (генерация контента)
- **Google Gemini** (gemini-1.5-flash, gemini-1.5-pro) - основной
- **OpenAI** (gpt-4o-mini, gpt-4o) - через OpenRouter
- **Anthropic Claude** (claude-3-5-sonnet) - через OpenRouter
- **xAI Grok** (grok-beta) - через OpenRouter
- **Google Gemma-3-12b-it:free** - бесплатная альтернатива

#### OCR (распознавание текста)
- **Google Cloud Document AI** - production (высокое качество)
- **EasyOCR** / **Tesseract** - fallback для тестирования

#### TTS (синтез речи)
- **Google Cloud TTS** (Wavenet, Neural2) - рекомендуется
- **Azure Cognitive Services** - альтернатива
- **Silero TTS** - локально, бесплатно (torch-based)

#### Speech-to-Text (синхронизация)
- **OpenAI Whisper** (base, small, medium) - word-level timing


## 🚀 Быстрый запуск

### Требования

- **Docker** & **Docker Compose** (рекомендуется)
- **Node.js** 18+ и **npm** (для frontend)
- **Python** 3.10+ (для backend)
- **API ключи** (см. раздел "Настройка API ключей")

### Вариант 1: Docker Compose (рекомендуется)

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd slide-speaker-main

# 2. Настроить переменные окружения
cp docker.env.template docker.env
# Отредактируйте docker.env, добавьте API ключи

# 3. Запустить все сервисы
docker-compose up -d --build

# 4. Дождаться инициализации (~30 секунд)
docker-compose logs -f backend

# 5. Проверить статус
curl http://localhost:8000/health
```

**Доступные сервисы:**
- 🌐 Frontend: http://localhost:3000
- 📡 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs
- 📊 Grafana: http://localhost:3001 (admin/admin)
- 📈 Prometheus: http://localhost:9090
- 🪣 MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- 🔴 Redis: localhost:6379
- 🐘 PostgreSQL: localhost:5432

### Вариант 2: Локальная разработка

#### Backend
```bash
cd backend

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл
cp .env.template .env
# Отредактировать .env

# Запустить миграции
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend
```bash
# В корне проекта
npm install

# Создать .env файл
echo "VITE_API_BASE=http://localhost:8000" > .env

# Запустить dev сервер
npm run dev
```

**Доступ:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Первый запуск

1. **Откройте приложение**: http://localhost:3000
2. **Зарегистрируйтесь** или используйте демо
3. **Загрузите презентацию** (PPTX или PDF)
4. **Дождитесь обработки** (~30-60 сек для 10 слайдов)
5. **Просмотрите результат** в интерактивном плеере
6. **Экспортируйте видео** (опционально)

## 📡 API Reference

### Основные эндпоинты

#### Загрузка и обработка

**POST /upload**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@presentation.pptx" \
  -F "voice=ru-RU-SvetlanaNeural" \
  -F "speed=1.0"
```
Загружает презентацию (PPTX/PDF) и запускает обработку через Intelligent Pipeline.

**Response:**
```json
{
  "lesson_id": "397c66bc-55ac-460a-80e5-312c6255262b",
  "status": "processing",
  "message": "Presentation uploaded successfully",
  "estimated_time": "30-60 seconds"
}
```

**GET /lessons/{lesson_id}/status**
```bash
curl http://localhost:8000/lessons/{lesson_id}/status
```
Проверяет статус обработки презентации.

**Response:**
```json
{
  "lesson_id": "397c66bc...",
  "status": "completed",
  "progress": 100,
  "current_stage": "completed",
  "slides_processed": 10,
  "total_slides": 10
}
```

**GET /lessons/{lesson_id}/manifest**
```bash
curl http://localhost:8000/lessons/{lesson_id}/manifest
```
Возвращает полный манифест урока со слайдами, аудио и визуальными эффектами.

**Response:**
```json
{
  "lesson_id": "397c66bc...",
  "title": "Introduction to AI",
  "slides": [
    {
      "id": 1,
      "image": "https://storage.googleapis.com/.../slide_1.png",
      "audio": "https://storage.googleapis.com/.../audio_1.mp3",
      "duration": 12.5,
      "lecture_text": "Welcome to our course on Artificial Intelligence...",
      "talk_track": [
        {"text": "Welcome to our course", "start": 0.0, "end": 2.1},
        {"text": "on Artificial Intelligence", "start": 2.2, "end": 4.5}
      ],
      "cues": [
        {
          "cue_id": "cue_1",
          "t0": 0.5,
          "t1": 2.3,
          "action": "highlight",
          "bbox": [120, 80, 600, 150],
          "element_id": "elem_title"
        }
      ],
      "elements": [
        {
          "id": "elem_title",
          "type": "text",
          "bbox": [120, 80, 600, 150],
          "text": "Introduction to AI",
          "confidence": 0.98
        }
      ]
    }
  ],
  "metadata": {
    "total_duration": 125.5,
    "total_slides": 10,
    "pipeline_version": "intelligent_optimized",
    "created_at": "2025-10-30T12:00:00Z"
  }
}
```

#### Редактирование контента

**POST /lessons/{lesson_id}/patch**
```bash
curl -X POST "http://localhost:8000/lessons/{lesson_id}/patch" \
  -H "Content-Type: application/json" \
  -d '{
    "slide_patches": [
      {
        "slide_id": 1,
        "lecture_text": "Updated lecture text...",
        "regenerate_audio": true
      }
    ]
  }'
```
Редактирует лекторский текст, визуальные эффекты или тайминги.

**POST /lessons/{lesson_id}/generate-audio**
```bash
curl -X POST "http://localhost:8000/lessons/{lesson_id}/generate-audio" \
  -H "Content-Type: application/json" \
  -d '{
    "voice": "ru-RU-DmitryNeural",
    "speed": 1.1,
    "regenerate_all": false
  }'
```
Перегенерирует аудио с новыми параметрами.

#### Экспорт видео

**POST /lessons/{lesson_id}/export**
```bash
curl -X POST "http://localhost:8000/lessons/{lesson_id}/export" \
  -H "Content-Type: application/json" \
  -d '{
    "quality": "high",
    "resolution": "1920x1080",
    "fps": 30,
    "format": "mp4"
  }'
```
Запускает асинхронную генерацию MP4 видео.

**Response:**
```json
{
  "export_id": "export_uuid",
  "status": "queued",
  "estimated_time": "5-10 minutes",
  "webhook_url": null
}
```

**GET /lessons/{lesson_id}/export/status**
```bash
curl http://localhost:8000/lessons/{lesson_id}/export/status?export_id=export_uuid
```
Проверяет статус экспорта видео.

**Response:**
```json
{
  "export_id": "export_uuid",
  "status": "completed",
  "progress": 100,
  "download_url": "https://storage.googleapis.com/.../video.mp4",
  "file_size": "45.2 MB",
  "duration": "3:25"
}
```

#### Аутентификация

**POST /auth/register**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'
```

**POST /auth/login**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "subscription_tier": "free"
  }
}
```

#### Аналитика и мониторинг

**GET /api/analytics/dashboard**
```bash
curl http://localhost:8000/api/analytics/dashboard \
  -H "Authorization: Bearer {token}"
```
Возвращает метрики использования, стоимости API и производительности.

**POST /api/analytics/track**
```bash
curl -X POST "http://localhost:8000/api/analytics/track" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "lecture_generation_started",
    "session_id": "session_uuid",
    "properties": {"lesson_id": "lesson_uuid"}
  }'
```

#### Квизы

**POST /api/quizzes/generate**
```bash
curl -X POST "http://localhost:8000/api/quizzes/generate" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_id": "lesson_uuid",
    "num_questions": 10,
    "difficulty": "medium"
  }'
```

#### Плейлисты

**GET /api/playlists**
```bash
curl http://localhost:8000/api/playlists \
  -H "Authorization: Bearer {token}"
```

**POST /api/playlists**
```bash
curl -X POST "http://localhost:8000/api/playlists" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Machine Learning Course",
    "description": "Complete ML course lectures",
    "lesson_ids": ["lesson_1", "lesson_2", "lesson_3"]
  }'
```

### WebSocket (реальное время)

**WS /ws/lessons/{lesson_id}**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/lessons/{lesson_id}');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Processing update:', update);
};
```
Получает обновления статуса обработки в реальном времени.

### Health & Metrics

**GET /health** - базовая проверка здоровья  
**GET /health/detailed** - детальная проверка всех сервисов  
**GET /health/ready** - готовность к обработке запросов  
**GET /metrics** - метрики Prometheus

Полная документация API: http://localhost:8000/docs (Swagger UI)



## ⚙️ Настройка и конфигурация

### API Ключи

Для полной функциональности необходимы API ключи для AI сервисов. Создайте файл `docker.env` или `backend/.env`:

```bash
# === AI Services (минимум один LLM провайдер) ===

# Google Gemini (рекомендуется, бесплатный tier)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# OpenRouter (для OpenAI, Claude, Grok)
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=google/gemma-3-12b-it:free  # бесплатная модель
# Альтернативы:
# OPENROUTER_MODEL=openai/gpt-4o-mini         # $0.15/1M tokens
# OPENROUTER_MODEL=anthropic/claude-3-5-sonnet # $3/1M tokens

# === Google Cloud (для production quality) ===

GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-sa.json
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
DOCUMENT_AI_PROCESSOR_ID=your-processor-id

# Google Text-to-Speech (высокое качество)
GOOGLE_TTS_VOICE=ru-RU-Wavenet-D
GOOGLE_TTS_SPEAKING_RATE=1.0
GOOGLE_TTS_PITCH=0.0

# Google Cloud Storage (опционально)
GCS_BUCKET_NAME=slide-speaker

# === Provider Selection ===

OCR_PROVIDER=google          # google | easyocr | tesseract
LLM_PROVIDER=gemini          # gemini | openai | anthropic
TTS_PROVIDER=google          # google | azure | silero
STORAGE=minio                # minio | gcs

# === Database ===

DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/slide_speaker
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=slide_speaker

# === Redis & Celery ===

REDIS_URL=redis://redis:6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# === MinIO (S3-compatible storage) ===

AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET=slide-speaker

# === Security ===

SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 1 week

# === Pipeline Optimization ===

PIPELINE_MAX_PARALLEL_SLIDES=5    # параллельная обработка слайдов
PIPELINE_MAX_PARALLEL_TTS=1       # TTS запросы (лимит памяти Docker)
ENABLE_OCR_CACHE=true             # Redis кэширование OCR
CACHE_TTL_HOURS=168               # 1 неделя

# === Monitoring (опционально) ===

SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# === Stripe (для подписок, опционально) ===

STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Получение API ключей

#### Google Gemini (бесплатно)
1. Перейдите на https://makersuite.google.com/app/apikey
2. Создайте API ключ
3. Лимиты: 15 запросов/минуту, бесплатно

#### OpenRouter
1. Регистрация: https://openrouter.ai/
2. Создайте API ключ в https://openrouter.ai/keys
3. Пополните баланс или используйте бесплатные модели (gemma-3-12b-it:free)

#### Google Cloud Platform
1. Создайте проект: https://console.cloud.google.com
2. Включите API:
   - Document AI API
   - Text-to-Speech API
   - Cloud Storage API (опционально)
   - Vertex AI API (опционально)
3. Создайте Service Account с ролями:
   - Document AI API User
   - Cloud Text-to-Speech API User
   - Storage Object Admin
4. Скачайте JSON ключ → сохраните как `keys/gcp-sa.json`

Подробная инструкция: [docs/guides/GCP_SETUP.md](docs/guides/)

### Переменные окружения Frontend

Создайте `.env` в корне проекта:

```bash
VITE_API_BASE=http://localhost:8000
```

### Docker Secrets

Для production рекомендуется использовать Docker Secrets:

```bash
# Создать secrets
echo "your_gemini_key" | docker secret create gemini_api_key -
echo "your_openrouter_key" | docker secret create openrouter_api_key -

# Обновить docker-compose.yml
services:
  backend:
    secrets:
      - gemini_api_key
      - openrouter_api_key
```


SILERO_TTS_SPEAKER=aidar     # ru: aidar|baya|kseniya|xenia|eugene
SILERO_TTS_SAMPLE_RATE=48000 # 8000|24000|48000

# Document AI
GCP_DOC_AI_PROCESSOR_ID=your-processor-id
OCR_BATCH_SIZE=10

# Gemini LLM
GEMINI_MODEL=gemini-1.5-flash
GEMINI_LOCATION=us-central1
LLM_TEMPERATURE=0.2

# Google TTS
GOOGLE_TTS_VOICE=ru-RU-Neural2-B
GOOGLE_TTS_SPEAKING_RATE=1.0
GOOGLE_TTS_PITCH=0.0

# Google Cloud Storage
GCS_BUCKET=slide-speaker
GCS_BASE_URL=https://storage.googleapis.com/slide-speaker
```

#### 7. Размещение ключей

```bash
# Создайте директорию для ключей
mkdir -p keys

# Скопируйте Service Account ключ
cp path/to/your/gcp-sa.json keys/gcp-sa.json

# Установите правильные права доступа
chmod 600 keys/gcp-sa.json
```

### Переключение провайдеров

Вы можете легко переключаться между различными провайдерами:

#### OCR Провайдеры
- `google` - Google Cloud Document AI (лучшее качество)
- `easyocr` - EasyOCR (локальный, бесплатный)


## 🎨 Основные возможности

### 1. Интеллектуальная обработка презентаций

- **Автоматический парсинг** PPTX и PDF файлов
- **OCR с высокой точностью** через Google Document AI
- **Распознавание структуры** - заголовки, списки, таблицы, изображения
- **Извлечение элементов** с точными координатами (bbox)
- **Кэширование результатов** для мгновенного повторного использования

### 2. AI-генерация контента

- **Семантический анализ** слайдов для понимания контекста
- **Автоматическая генерация лекторского текста** естественным языком
- **Адаптивная подача материала** с учетом типа презентации
- **Определение ключевых концепций** и терминов
- **Мультиязычная поддержка** с автоопределением языка

### 3. Профессиональная озвучка

- **Google Cloud TTS** (Wavenet, Neural2) - студийное качество
- **Силеро TTS** - бесплатная локальная альтернатива
- **Множество голосов** - мужские и женские, разные языки
- **Настройка параметров** - скорость, тон, интонация
- **SSML разметка** - точное управление произношением
- **Whisper синхронизация** - точная привязка слов к времени

### 4. Визуальные эффекты

- **Highlight** - подсветка важных элементов
- **Underline** - подчеркивание текста
- **Laser pointer** - движущаяся указка
- **Fade in/out** - плавные переходы
- **Синхронизация с речью** - эффекты появляются точно в момент упоминания
- **Настраиваемые тайминги** - полный контроль над анимацией

### 5. Интерактивный плеер

- **Воспроизведение аудио** с автоматической сменой слайдов
- **Scale-aware рендеринг** - адаптация к любому разрешению
- **Субтитры** - синхронизированный текст
- **Навигация** - быстрый переход между слайдами
- **Прогресс бар** - отслеживание воспроизведения
- **Управление скоростью** - ускорение/замедление

### 6. Экспорт видео

- **MP4 генерация** с визуальными эффектами
- **Качество до Full HD** (1920x1080)
- **Настраиваемый FPS** (24, 30, 60)
- **Асинхронная обработка** через Celery worker
- **Отслеживание прогресса** в реальном времени
- **Хранение в S3/GCS** - надежное облачное хранилище

### 7. Генерация квизов

- **Автоматическое создание вопросов** по содержанию презентации
- **Разные типы вопросов** - множественный выбор, правда/ложь
- **Настройка сложности** - легкий, средний, сложный
- **Экспорт квизов** в различные форматы
- **Интеграция с LMS** (планируется)

### 8. Система управления

- **Аутентификация** - JWT-based с refresh tokens
- **Подписки и тарифы** - Free, Pro, Enterprise
- **Плейлисты** - организация лекций в курсы
- **История обработки** - доступ к предыдущим проектам
- **Аналитика использования** - отслеживание метрик
- **Cost tracking** - контроль расходов на API

### 9. Мониторинг и аналитика

- **Prometheus метрики** - производительность API
- **Grafana дашборды** - визуализация данных
- **Sentry integration** - отслеживание ошибок
- **Event tracking** - аналитика пользовательских действий
- **Cost monitoring** - расходы на AI сервисы
- **Performance insights** - оптимизация обработки

## 🧪 Тестирование

### Unit тесты (Backend)

```bash
cd backend

# Запустить все тесты
pytest

# С покрытием кода
pytest --cov=app --cov-report=html

# Конкретный модуль
pytest app/tests/test_pipeline.py

# С логированием
pytest -v -s
```

### Integration тесты

```bash
# Тест полного pipeline
./scripts/integration/test_full_pipeline.sh

# Тест с реальными AI сервисами
python backend/app/tests/test_ai_integration.py

# Проверка всех провайдеров
./scripts/integration/test_providers.sh
```

### E2E тесты (Frontend)

```bash
cd tests/e2e

# Установить зависимости
npm install

# Запустить тесты
npm test

# Интерактивный режим
npm run test:ui
```

**Что тестируется:**
- Загрузка презентаций
- Воспроизведение плеера
- Синхронизация эффектов
- Смена слайдов
- Отображение субтитров
- Навигация

### Smoke тесты

```bash
# Проверка health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed

# Тест загрузки файла
curl -X POST http://localhost:8000/upload \
  -F "file=@test_presentation.pptx"

# Полный smoke test
docker-compose up -d
python scripts/integration/smoke_test.py
```

### Performance тесты

```bash
# Load testing с Apache Bench
ab -n 100 -c 10 http://localhost:8000/health

# Stress testing pipeline
python scripts/integration/test_pipeline_performance.py
```

### 📊 Нагрузочное тестирование (Load Testing)

**Slide Speaker** включает комплексную систему нагрузочного тестирования на базе **Locust** для проверки масштабируемости и надежности.

#### Быстрый старт

```bash
# Перейти в директорию тестов
cd backend/load_tests

# Запустить быструю проверку
./quickstart.sh
```

#### Доступные сценарии

```bash
# Легкая нагрузка (10 пользователей, 5 минут)
./run_load_tests.sh light http://localhost:8000

# Средняя нагрузка (50 пользователей, 10 минут)
./run_load_tests.sh medium http://localhost:8000

# Высокая нагрузка (100 пользователей, 15 минут)
./run_load_tests.sh heavy http://localhost:8000

# Стресс-тест (500 пользователей, 20 минут)
./run_load_tests.sh stress http://localhost:8000

# Тест на пиковую нагрузку (200 пользователей, быстро)
./run_load_tests.sh spike http://localhost:8000

# Длительный тест (30 пользователей, 2 часа)
./run_load_tests.sh endurance http://localhost:8000
```

#### Что тестируется

- ✅ **API эндпоинты** - производительность всех REST API
- ✅ **Аутентификация** - регистрация и логин пользователей
- ✅ **Загрузка файлов** - upload презентаций различных размеров
- ✅ **Обработка контента** - генерация заметок и аудио
- ✅ **Экспорт видео** - ресурсоемкие операции
- ✅ **База данных** - производительность запросов
- ✅ **Кэширование** - эффективность Redis

#### Результаты

После запуска тестов создается детальный отчет:
- **HTML отчет** - интерактивные графики и метрики
- **CSV данные** - статистика для анализа
- **Мониторинг ресурсов** - CPU, память, сеть
- **Рекомендации** - автоматические советы по оптимизации

```bash
# Просмотр результатов
open backend/load_tests/reports/latest/report.html
```

#### Порги производительности

| Метрика | Целевое значение | Критическое |
|---------|------------------|-------------|
| Error Rate | < 1% | > 5% |
| P95 (Read) | < 500ms | > 2000ms |
| P95 (Write) | < 1000ms | > 5000ms |
| Throughput | > 50 req/s | < 10 req/s |

#### Документация

Полная документация по нагрузочному тестированию:
- 📘 **Руководство:** `backend/load_tests/README.md`
- 📝 **Примеры:** `backend/load_tests/EXAMPLES.md`
- 📊 **Сводка:** `LOAD_TESTING_SUMMARY.md`

#### CI/CD интеграция

Автоматическое тестирование настроено через GitHub Actions:
- ✅ Тесты при каждом Pull Request
- ✅ Еженедельные проверки производительности
- ✅ Сравнение с baseline метриками

### Тестирование в Docker

```bash
# Запустить все сервисы
docker-compose up -d

# Подождать инициализации
sleep 30

# Запустить тесты
docker-compose exec backend pytest

# Проверить логи
docker-compose logs backend
docker-compose logs celery
```

## 🚢 Развертывание

### Локальное развертывание (Development)

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd slide-speaker-main

# 2. Настроить переменные окружения
cp docker.env.template docker.env
# Отредактировать docker.env

# 3. Запустить сервисы
docker-compose up -d

# 4. Проверить статус
docker-compose ps
curl http://localhost:8000/health
```

### Production развертывание

#### На VPS/VDS сервере

```bash
# 1. Установить Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 2. Клонировать репозиторий
git clone <repo-url>
cd slide-speaker-main

# 3. Настроить production конфиг
cp docker.env.template docker.env
nano docker.env  # Добавить production API ключи

# 4. Настроить HTTPS (с Let's Encrypt)
# Отредактировать nginx.conf

# 5. Запустить с production профилем
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 6. Настроить автозапуск
sudo systemctl enable docker
```

#### Railway Deploy

```bash
# 1. Установить Railway CLI
npm install -g @railway/cli

# 2. Войти в аккаунт
railway login

# 3. Создать новый проект
railway init

# 4. Добавить переменные окружения
railway variables set GEMINI_API_KEY=your_key
railway variables set DATABASE_URL=postgresql://...

# 5. Deploy
railway up
```

См. подробную инструкцию: [DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md)

#### Netlify Deploy (Frontend)

```bash
# 1. Установить Netlify CLI
npm install -g netlify-cli

# 2. Войти
netlify login

# 3. Деплой
netlify deploy --prod
```

См. конфигурацию: [netlify.toml](netlify.toml)

### Kubernetes Deployment (Enterprise)

```bash
# 1. Применить манифесты
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# 2. Проверить статус
kubectl get pods -n slide-speaker

# 3. Настроить ingress
kubectl apply -f k8s/ingress.yaml
```

### Мониторинг Production

```bash
# Prometheus метрики
curl http://your-domain.com/metrics

# Grafana дашборды
# http://your-domain.com:3001

# Sentry error tracking
# https://sentry.io/organizations/your-org/projects/

# Health checks
curl http://your-domain.com/health
curl http://your-domain.com/health/ready
```

### Backup и восстановление

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U postgres slide_speaker > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres slide_speaker < backup.sql

# Backup MinIO data
docker-compose exec minio mc mirror minio/slide-speaker ./backup/

# Restore
docker-compose exec minio mc mirror ./backup/ minio/slide-speaker
```

## 💰 Стоимость и оптимизация

### Примерная стоимость обработки 100 слайдов

| Компонент | Провайдер | Стоимость |
|-----------|-----------|-----------|
| OCR | Google Document AI | $0.15 |
| LLM | Google Gemini Flash | $0.00-0.01 |
| TTS | Google Wavenet | $1.20 |
| Storage | MinIO/GCS | $0.02 |
| **ИТОГО** | | **$1.37** |

### Оптимизация затрат

1. **Кэширование OCR** - Redis кэш на 7 дней (-90% повторных затрат)
2. **Бесплатные LLM модели** - Gemini Flash или Gemma-3-12b-it:free
3. **Локальный TTS** - Silero вместо Google TTS (-100% затрат на TTS)
4. **Batch обработка** - группировка запросов к API
5. **Smart caching** - кэширование на всех уровнях pipeline

### Мониторинг стоимости

```bash
# Просмотр расходов через API
curl http://localhost:8000/api/analytics/costs \
  -H "Authorization: Bearer {token}"

# Grafana дашборд "API Costs"
# http://localhost:3001/d/costs
```


```bash
# Убедитесь, что все сервисы запущены
docker-compose up -d

# Запустите smoke test
python smoke_test.py
```

Smoke test проверяет:
- ✅ API health check
- ✅ Demo lesson manifest
- ✅ Export request
- ✅ Export status polling
- ✅ MP4 download
- ✅ Storage statistics
- ✅ Frontend accessibility

### Export test

```bash
# Запустите все сервисы
docker-compose up --build

# Запустите экспорт для demo-lesson
curl -X POST http://localhost:8000/lessons/demo-lesson/export
# Ожидаемый ответ: {"job_id": "uuid", "status": "queued"}

# Проверьте статус экспорта (замените JOB_ID на полученный выше)
curl "http://localhost:8000/lessons/demo-lesson/export/status?job_id=JOB_ID"
# Ожидаемый ответ: {"status": "processing", "progress": 50, "message": "..."}

# Когда статус станет "done", скачайте MP4
curl -O http://localhost:8000/assets/demo-lesson/export.mp4
```

### Ручное тестирование

1. **Запустите сервисы**: `docker-compose up --build`
2. **Откройте фронтенд**: http://localhost:3000
3. **Нажмите "Посмотреть демо"** для загрузки demo-lesson
4. **Нажмите "Export"** для запуска экспорта
5. **Дождитесь завершения** (5-10 минут)
6. **Скачайте MP4** файл

### Проверка scale-aware Player

```bash
# Запустите сервисы
docker-compose up --build

# Откройте фронтенд: http://localhost:3000
# Загрузите demo-lesson

# Проверьте масштабирование:
# 1. Сузьте окно браузера → рамки и лазер остаются на местах
# 2. Разверните окно на полный экран → элементы не "уезжают"
# 3. Измените размер окна во время воспроизведения → плавная адаптация
```

**Ожидаемое поведение:**
- При разных размерах окна рамки и указка совпадают с визуальными объектами слайда
- Движение указки плавное, без телепортов
- Элементы масштабируются пропорционально размеру контейнера

## Переменные окружения

### Backend (.env)
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Queue Configuration
REDIS_URL=redis://redis:6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# S3 Storage (MinIO)
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET=slide-speaker

# Export Settings
MAX_EXPORT_SIZE_MB=500
EXPORT_RETRY_ATTEMPTS=3
EXPORT_TIMEOUT_SECONDS=1800

# AI Services (Sprint 2)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Azure TTS Configuration
AZURE_TTS_KEY=your_azure_speech_key
AZURE_TTS_REGION=your_azure_region
TTS_VOICE=ru-RU-SvetlanaNeural
TTS_SPEED=1.0
```

### Frontend (.env)
```env
VITE_API_BASE=http://localhost:8000
```

## TTS Setup

### Получение ключей Azure Speech Services

1. **Создайте ресурс Speech Services в Azure Portal**:
   - Перейдите в [Azure Portal](https://portal.azure.com)
   - Создайте новый ресурс "Speech Services"
   - Выберите регион (например, "West Europe")

2. **Получите ключ и регион**:
   - В разделе "Keys and Endpoint" скопируйте ключ
   - Скопируйте регион из "Location"

3. **Настройте переменные окружения**:
   ```bash
   # Создайте .env файл
   cp .env.example .env
   
   # Отредактируйте .env
   AZURE_TTS_KEY=your_actual_key_here
   AZURE_TTS_REGION=your_actual_region_here
   ```

4. **Доступные голоса**:
   - `ru-RU-SvetlanaNeural` - женский русский голос
   - `ru-RU-DmitryNeural` - мужской русский голос
   - `en-US-AriaNeural` - женский английский голос
   - `en-US-GuyNeural` - мужской английский голос

### Пример использования

```python
# В коде Python
from workers.tts_edge import synthesize_slide_text

# Генерация аудио для слайда
slide_notes = [
    "Добро пожаловать в нашу презентацию",
    "Сегодня мы обсудим искусственный интеллект"
]

result = await synthesize_slide_text(slide_notes, voice="ru-RU-SvetlanaNeural", speed=1.0)
print(f"Аудио файл: {result['audio_file']}")
print(f"Длительность: {result['total_duration']} секунд")
```

## 📚 Дополнительная документация

- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - детальная структура проекта
- **[QUICK_START.md](QUICK_START.md)** - быстрый старт с бесплатными моделями
- **[DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md)** - инструкции по развертыванию
- **[DOCKER_SERVICES.md](DOCKER_SERVICES.md)** - описание Docker сервисов
- **[HOW_TO_GET_API_KEY.md](HOW_TO_GET_API_KEY.md)** - получение API ключей
- **[SECRETS_SETUP.md](SECRETS_SETUP.md)** - настройка секретов
- **[docs/reports/](docs/reports/)** - отчеты о разработке и тестировании (48 файлов)
- **[docs/guides/](docs/guides/)** - руководства пользователя (12 файлов)

## 🤝 Участие в разработке

Мы приветствуем вклад в проект! 

### Как внести вклад

1. **Fork** репозиторий
2. Создайте **feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit** изменения (`git commit -m 'Add some AmazingFeature'`)
4. **Push** в branch (`git push origin feature/AmazingFeature`)
5. Откройте **Pull Request**

### Стандарты кода

- **Python**: следуйте PEP 8, используйте type hints
- **TypeScript**: следуйте ESLint конфигурации
- **Commit messages**: используйте Conventional Commits
- **Тесты**: добавляйте тесты для новых функций
- **Документация**: обновляйте README и документацию

### Приоритетные направления

- 🎯 Поддержка новых языков и голосов
- 🎨 Улучшение UI/UX плеера
- 🚀 Оптимизация производительности pipeline
- 🔌 Интеграция с новыми AI провайдерами
- 📱 Мобильная версия
- 🌐 Интеграция с LMS системами

## 🐛 Известные проблемы и ограничения

### Текущие ограничения

- **Память Docker**: TTS обработка ограничена 3.8GB, параллелизм = 1
- **OCR качество**: зависит от качества исходных слайдов
- **Поддержка языков**: основная поддержка русского и английского
- **Размер файлов**: рекомендуется презентации до 50 слайдов
- **Экспорт видео**: может занимать 5-10 минут для 10 слайдов

### Roadmap улучшений

- ✨ **V2.0** - Поддержка видео в презентациях
- ✨ **V2.1** - Интерактивные элементы (кнопки, ссылки)
- ✨ **V2.2** - Голосовое управление плеером
- ✨ **V2.3** - Мобильное приложение
- ✨ **V3.0** - AI аватар лектора
- ✨ **V3.1** - Мультиязычные субтитры
- ✨ **V3.2** - Live streaming поддержка

## ⚠️ Troubleshooting

### Проблема: PostgreSQL authentication failed
```bash
# Решение: проверить пароль в docker.env
cat docker.env | grep POSTGRES_PASSWORD

# Пересоздать контейнер
docker-compose down -v
docker-compose up -d postgres
```

### Проблема: Google Cloud credentials not found
```bash
# Решение: проверить путь к credentials
ls -la keys/gcp-sa.json

# Установить переменную окружения
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-sa.json
```

### Проблема: MinIO bucket not found
```bash
# Решение: создать bucket вручную
docker-compose exec minio mc mb minio/slide-speaker
```

### Проблема: Celery worker не запускается
```bash
# Проверить логи
docker-compose logs celery

# Перезапустить worker
docker-compose restart celery
```

### Проблема: Frontend не подключается к backend
```bash
# Проверить .env файл
cat .env | grep VITE_API_BASE

# Должно быть: VITE_API_BASE=http://localhost:8000
# Перезапустить frontend
npm run dev
```

## 📊 Статистика проекта

- **Дата начала**: Сентябрь 2024
- **Последнее обновление**: Октябрь 2025
- **Языки кода**: Python (60%), TypeScript (35%), Shell (5%)
- **Строк кода**: ~50,000
- **Файлов**: 200+
- **Тестов**: 150+
- **Документации**: 60+ страниц

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- **Google Cloud** - за предоставление AI сервисов
- **OpenRouter** - за доступ к множеству LLM моделей
- **FastAPI** - за отличный веб-фреймворк
- **React** - за мощную UI библиотеку
- **Сообщество разработчиков** - за вклад и обратную связь

## 📞 Контакты и поддержка

- **GitHub Issues**: [Issues](https://github.com/your-org/slide-speaker/issues)
- **Email**: support@slide-speaker.com
- **Documentation**: [docs/](docs/)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/slide-speaker/discussions)

---

**Сделано с ❤️ командой Slide Speaker**

