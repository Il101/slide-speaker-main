# Slide Speaker - ИИ-Лектор

Превращаем презентации в интерактивные лекции с озвучкой и визуальными эффектами.

## 📁 Структура проекта

```
slide-speaker-main/
├── backend/              # Backend приложение (FastAPI)
│   ├── app/              # Основное приложение
│   │   ├── pipeline/     # Пайплайны обработки презентаций
│   │   ├── services/     # Сервисы ИИ и обработки
│   │   ├── api/          # API endpoints
│   │   └── core/         # Конфигурация и утилиты
│   ├── workers/          # Celery workers для фоновых задач
│   └── requirements.txt  # Python зависимости
├── src/                  # Frontend приложение (React + TypeScript)
│   ├── components/       # React компоненты
│   │   └── Player/       # Интерактивный плеер
│   ├── pages/            # Страницы приложения
│   └── lib/              # Утилиты и API клиент
├── docs/                 # Документация
├── monitoring/           # Prometheus и Grafana конфигурация
├── docker-compose.yml    # Оркестрация Docker
└── README.md             # Эта документация
```

## Архитектура

### Общая архитектура
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python 3.11+
- **Очереди**: Redis + Celery для фоновой обработки
- **База данных**: PostgreSQL для метаданных
- **Хранилище**: S3-совместимое (MinIO) для файлов
- **Видео**: FFmpeg для рендера MP4
- **Мониторинг**: Prometheus + Grafana

### Пайплайн обработки презентаций

Slide Speaker использует **интеллектуальный пайплайн обработки** с поддержкой множественных режимов:

#### 1. **Intelligent Optimized Pipeline** (по умолчанию)
- **Технология**: PPTX/PDF → PNG → OCR → Semantic Analysis → TTS → Visual Effects
- **Особенности**: Параллельная обработка, кэширование, умная синхронизация
- **Производительность**: -77% времени обработки благодаря параллелизации
- **Применение**: Production-ready обработка с высоким качеством

#### 2. **Classic Pipeline** (legacy)
- **Технология**: OCR (Document AI) + LLM + TTS
- **Применение**: Точное извлечение текста и элементов из слайдов
- **Преимущества**: Высокая точность bbox, поддержка таблиц и сложных макетов
- **Недостатки**: Зависимость от качества OCR

#### 3. **Vision Pipeline**
- **Технология**: Мультимодальная LLM (GPT-4o, Gemini, Claude)
- **Применение**: Анализ изображений слайдов для генерации объяснений
- **Преимущества**: Понимание контекста, качественные объяснения, независимость от OCR
- **Недостатки**: Приблизительные координаты элементов

#### 4. **Hybrid Pipeline**
- **Технология**: Vision LLM + OCR alignment
- **Применение**: Комбинация лучшего из двух подходов
- **Преимущества**: Качественные объяснения + точные координаты
- **Недостатки**: Более сложная обработка, требует настройки alignment

## 🚀 Пайплайн обработки презентаций

### Этапы обработки

#### **Stage 1: Ingest (Конвертация)**
- **PPTX/PDF → PNG**: Конвертация презентации в изображения высокого качества
- **Поддержка форматов**: PPTX (через LibreOffice), PDF (через PyMuPDF)
- **Качество**: 2x разрешение для четкости текста
- **Результат**: PNG файлы слайдов + начальный manifest.json

#### **Stage 2: OCR Extraction (Извлечение элементов)**
- **Технология**: Google Document AI, EasyOCR, PaddleOCR
- **Функции**: Извлечение текста, координат, типов элементов
- **Кэширование**: Результаты OCR кэшируются для ускорения
- **Результат**: Структурированные данные элементов с bbox

#### **Stage 3: Semantic Analysis (Семантический анализ)**
- **Анализ контекста**: Глобальный анализ всей презентации
- **Группировка элементов**: Умная группировка связанных элементов
- **Приоритизация**: Определение важности и порядка объяснения
- **Результат**: Semantic map с группами и стратегиями выделения

#### **Stage 4: Script Generation (Генерация скриптов)**
- **Talk Track**: Детализированная речь с маркерами синхронизации
- **Speaker Notes**: Краткие заметки для каждого слайда
- **SSML**: Разметка для точного произношения и синхронизации
- **Результат**: Структурированный контент для озвучки

#### **Stage 5: TTS Generation (Синтез речи)**
- **Провайдеры**: Google TTS, Azure Speech, OpenRouter
- **SSML поддержка**: Точное произношение и word-level timing
- **Параллелизация**: Одновременная генерация для всех слайдов
- **Результат**: Аудио файлы + точные временные метки

#### **Stage 6: Visual Effects (Визуальные эффекты)**
- **Умная синхронизация**: Синхронизация с произносимыми словами
- **Множественные эффекты**: Подсветка, подчеркивание, лазер, spotlight
- **Адаптивность**: Автоматический выбор эффектов по контексту
- **Результат**: Cues с точными временными метками

#### **Stage 7: Validation & Manifest (Валидация и финализация)**
- **Проверка качества**: Валидация всех компонентов
- **Timeline построение**: Создание общей временной шкалы
- **Fallback данные**: Резервные данные при ошибках
- **Результат**: Финальный manifest.json для плеера

### Конфигурация пайплайнов

#### Переключение пайплайнов

**Через переменную окружения:**
```bash
# В .env файле
PIPELINE=intelligent_optimized  # intelligent_optimized | classic | vision | hybrid
```

**Через параметр запроса:**
```bash
# При загрузке файла
curl -F "file=@presentation.pdf" "http://localhost:8000/upload?pipeline=vision"

# При генерации аудио
curl -X POST "http://localhost:8000/lessons/{id}/generate-audio" \
  -H "X-Pipeline: hybrid"
```

**Через фронтенд:**
```javascript
// В URL параметрах
/?lesson=demo&pipeline=vision
```

#### Настройка провайдеров

**OCR Провайдеры:**
- `google` - Google Cloud Document AI (лучшее качество)
- `easyocr` - EasyOCR (локальный, бесплатный)
- `paddle` - PaddleOCR (альтернативный локальный)

**LLM Провайдеры:**
- `openrouter` - OpenRouter (GPT-4o, Claude, Gemini через единый API)
- `gemini` - Google Gemini (через Vertex AI)
- `openai` - OpenAI GPT
- `anthropic` - Anthropic Claude

**TTS Провайдеры:**
- `google` - Google Cloud Text-to-Speech
- `azure` - Azure Speech Services
- `mock` - Mock TTS (для тестирования)

**Storage Провайдеры:**
- `gcs` - Google Cloud Storage
- `minio` - MinIO (локальный S3-совместимый)

### Переключение пайплайнов

#### Через переменную окружения
```bash
# В .env файле
PIPELINE=classic    # classic | vision | hybrid
```

#### Через параметр запроса
```bash
# При загрузке файла
curl -F "file=@presentation.pdf" "http://localhost:8000/upload?pipeline=vision"

# При генерации аудио
curl -X POST "http://localhost:8000/lessons/{id}/generate-audio" \
  -H "X-Pipeline: hybrid"
```

#### Через фронтенд
```javascript
// В URL параметрах
/?lesson=demo&pipeline=vision
```

### Конфигурация AI моделей

#### OpenRouter (рекомендуется)
```bash
# В .env файле
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=meta-llama/llama-3.3-8b-instruct:free  # Бесплатная модель
# OPENROUTER_MODEL=x-ai/grok-4-fast:free  # xAI Grok
# OPENROUTER_MODEL=openai/gpt-4o-mini     # OpenAI GPT-4o
# OPENROUTER_MODEL=anthropic/claude-3-5-sonnet  # Claude
```

#### Google Cloud
```bash
# В .env файле
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-1.5-flash
GEMINI_LOCATION=us-central1
```

#### OpenAI
```bash
# В .env файле
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
```

#### Anthropic
```bash
# В .env файле
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key
```

## 🚀 Быстрый запуск

### 1. Docker Compose (рекомендуется)

**Запуск всех сервисов:**
```bash
# Клонируйте репозиторий
git clone <repository-url>
cd slide-speaker

# Создайте .env файл
cp .env.example .env

# Запустите все сервисы
docker-compose up --build
```

**Сервисы будут доступны:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redis: localhost:6379
- PostgreSQL: localhost:5432
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

### 2. Локальная разработка

#### Backend
```bash
cd backend

# Установите зависимости
pip install -r requirements.txt --break-system-packages

# Создайте .env файл
cp .env.example .env

# Запустите сервер
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend
```bash
# Установите зависимости
npm install

# Запустите dev сервер
npm run dev
```

**Сервисы будут доступны:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. Первоначальная настройка

#### MinIO (для хранения файлов)
1. Откройте MinIO Console: http://localhost:9001
2. Войдите с учетными данными: `minioadmin` / `minioadmin`
3. Создайте bucket с именем `slide-speaker`
4. Настройте политику доступа для публичного чтения (опционально)

#### База данных (автоматически)
- PostgreSQL автоматически инициализируется при первом запуске
- Создаются необходимые таблицы и пользователи
- Данные сохраняются в Docker volume

#### Мониторинг (опционально)
- Prometheus собирает метрики производительности
- Grafana предоставляет дашборды для мониторинга
- Доступны метрики: обработка файлов, время ответа, ошибки

## 📡 API Endpoints

### Аутентификация
Все endpoints (кроме демо) требуют аутентификации через JWT токен.

### Основные endpoints

#### **POST /upload**
Загружает файл (PPTX/PDF) и запускает обработку через пайплайн.

**Request**: `multipart/form-data` с файлом
**Headers**: `Authorization: Bearer <jwt_token>`
**Query Parameters**: 
- `pipeline` (optional): `intelligent_optimized` | `classic` | `vision` | `hybrid`

**Response**:
```json
{
  "lesson_id": "uuid",
  "status": "processing"
}
```

#### **GET /lessons/{lesson_id}/status**
Получает статус обработки урока.

**Headers**: `Authorization: Bearer <jwt_token>`
**Response**:
```json
{
  "lesson_id": "uuid",
  "status": "processing|completed|failed",
  "stage": "ocr_complete|ai_processing|completed",
  "progress": 75,
  "message": "Generating audio for slides...",
  "slides_processed": 5,
  "slides_with_notes": 3,
  "slides_with_audio": 2
}
```

#### **GET /lessons/{lesson_id}/manifest**
Возвращает manifest.json с данными о слайдах и эффектах.

**Headers**: `Authorization: Bearer <jwt_token>` (optional для демо)
**Response**:
```json
{
  "slides": [
    {
      "id": 1,
      "image": "/assets/lesson_id/slides/001.png",
      "audio": "/assets/lesson_id/audio/001.wav",
      "duration": 45.2,
      "elements": [
        {
          "id": "elem_1",
          "type": "text",
          "text": "Заголовок слайда",
          "bbox": [120, 80, 980, 150],
          "confidence": 0.95
        }
      ],
      "cues": [
        {
          "cue_id": "cue_123",
          "t0": 0.6,
          "t1": 2.2,
          "action": "highlight",
          "bbox": [120, 80, 980, 150],
          "element_id": "elem_1",
          "group_id": "group_title_0"
        }
      ],
      "talk_track": [
        {
          "text": "Добро пожаловать на наш слайд",
          "start": 0.0,
          "end": 2.5,
          "group_id": "group_title_0"
        }
      ],
      "speaker_notes": "Краткие заметки для слайда"
    }
  ],
  "metadata": {
    "source_file": "presentation.pptx",
    "total_slides": 10,
    "slide_width": 1920,
    "slide_height": 1080,
    "presentation_context": {
      "theme": "Физика для биологов",
      "subject_area": "Physics",
      "level": "undergraduate"
    }
  }
}
```

#### **POST /lessons/{lesson_id}/export**
Запускает экспорт урока в MP4 видео.

**Headers**: `Authorization: Bearer <jwt_token>`
**Response**:
```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

#### **GET /lessons/{lesson_id}/export/status**
Получает статус задачи экспорта.

**Query Parameters**: `job_id` (required)
**Response**:
```json
{
  "status": "processing|done|failed",
  "progress": 75,
  "message": "Rendering video frames...",
  "url": "/exports/lesson_id_export.mp4"
}
```

#### **GET /exports/{lesson_id}/download**
Скачивает готовый MP4 файл.

**Response**: MP4 файл или редирект на S3

### WebSocket endpoints

#### **WS /ws/lesson/{lesson_id}**
WebSocket для real-time обновлений прогресса обработки.

**Events**:
- `progress_update`: Обновление прогресса обработки
- `stage_complete`: Завершение этапа обработки
- `error`: Ошибка обработки

## 🔄 Как это работает

### Полный цикл обработки

1. **Загрузка файла**: Пользователь загружает PPTX/PDF через веб-интерфейс
2. **Конвертация**: PPTX/PDF автоматически конвертируется в PNG изображения высокого качества
3. **OCR анализ**: Извлекается текст и координаты элементов с помощью AI
4. **Семантический анализ**: ИИ анализирует контекст и группирует связанные элементы
5. **Генерация контента**: Создается детализированная речь и заметки для каждого слайда
6. **Синтез речи**: Генерируется естественная озвучка с точными временными метками
7. **Визуальные эффекты**: Создаются синхронизированные подсветки и анимации
8. **Воспроизведение**: Интерактивный плеер воспроизводит лекцию с эффектами
9. **Экспорт**: Возможность экспорта в MP4 видео для распространения

### Технические особенности

- **Параллельная обработка**: Несколько слайдов обрабатываются одновременно
- **Умная синхронизация**: Визуальные эффекты синхронизированы с произносимыми словами
- **Кэширование**: Результаты OCR и LLM кэшируются для ускорения
- **Fallback механизмы**: Система gracefully деградирует при ошибках
- **Real-time обновления**: WebSocket уведомления о прогрессе обработки

## Mock-данные

Для MVP используются:
- Placeholder слайды из `public/placeholder-slide-*.svg`
- Пустые аудио файлы (заглушки)
- Предопределенные cue-эффекты в manifest.json

## Структура проекта

```
├── backend/
│   ├── main.py              # FastAPI приложение
│   ├── requirements.txt     # Python зависимости
│   ├── Dockerfile          # Backend контейнер
│   └── .data/              # Данные уроков
├── src/
│   ├── components/
│   │   ├── FileUploader.tsx # Загрузка файлов
│   │   └── Player.tsx       # Интерактивный плеер
│   ├── lib/
│   │   └── api.ts          # API клиент
│   └── pages/
│       └── Index.tsx       # Главная страница
├── docker-compose.yml      # Оркестрация сервисов
└── Dockerfile             # Frontend контейнер
```

## Google Cloud Setup

### Настройка Google Cloud Services

Slide Speaker поддерживает интеграцию с Google Cloud сервисами для улучшенного качества OCR, LLM и TTS.

#### 1. Создание Service Account

1. **Перейдите в Google Cloud Console**: https://console.cloud.google.com
2. **Выберите проект** или создайте новый
3. **Перейдите в IAM & Admin > Service Accounts**
4. **Создайте Service Account**:
   - Название: `slide-speaker-sa`
   - Описание: `Service account for Slide Speaker application`
5. **Назначьте роли**:
   - `Document AI API User`
   - `Vertex AI User`
   - `Cloud Text-to-Speech API User`
   - `Storage Object Admin` (для GCS)
6. **Создайте ключ**:
   - Перейдите в созданный Service Account
   - Вкладка "Keys" → "Add Key" → "Create new key"
   - Выберите JSON формат
   - Сохраните файл как `gcp-sa.json`

#### 2. Настройка Document AI

1. **Включите Document AI API**:
   - Перейдите в "APIs & Services" → "Library"
   - Найдите "Document AI API" и включите
2. **Создайте процессор**:
   - Перейдите в Document AI → "Processors"
   - Создайте новый процессор типа "Form Parser" или "OCR"
   - Скопируйте Processor ID

#### 3. Настройка Vertex AI

1. **Включите Vertex AI API**:
   - Перейдите в "APIs & Services" → "Library"
   - Найдите "Vertex AI API" и включите
2. **Настройте регион**:
   - Выберите регион (например, `us-central1`)

#### 4. Настройка Text-to-Speech

1. **Включите Cloud Text-to-Speech API**:
   - Перейдите в "APIs & Services" → "Library"
   - Найдите "Cloud Text-to-Speech API" и включите

#### 5. Настройка Cloud Storage (опционально)

1. **Создайте bucket**:
   - Перейдите в Cloud Storage
   - Создайте bucket с именем `slide-speaker`
   - Настройте публичный доступ для чтения

#### 6. Настройка переменных окружения

Создайте `.env` файл на основе `.env.example`:

```env
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-sa.json
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1

# Provider Selection
OCR_PROVIDER=google          # google|easyocr|paddle
LLM_PROVIDER=gemini          # gemini|openai|ollama|anthropic
TTS_PROVIDER=google          # google|azure|mock
STORAGE=gcs                  # gcs|minio

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
- `paddle` - PaddleOCR (альтернативный локальный)

#### LLM Провайдеры
- `gemini` - Google Gemini (через Vertex AI)
- `openai` - OpenAI GPT
- `anthropic` - Anthropic Claude
- `ollama` - Локальный Ollama

#### TTS Провайдеры
- `google` - Google Cloud Text-to-Speech
- `azure` - Azure Speech Services
- `mock` - Mock TTS (для тестирования)

#### Storage Провайдеры
- `gcs` - Google Cloud Storage
- `minio` - MinIO (локальный S3-совместимый)

### Стоимость и оптимизация

#### Google Cloud Pricing (примерные цены)

- **Document AI**: $1.50 за 1000 страниц
- **Vertex AI Gemini**: $0.075 за 1M токенов (вход), $0.30 за 1M токенов (выход)
- **Text-to-Speech**: $4.00 за 1M символов
- **Cloud Storage**: $0.020 за GB в месяц

#### Оптимизация затрат

1. **Кэширование**: Результаты OCR/LLM/TTS кэшируются по хэшу контента
2. **Батчинг**: OCR обрабатывает несколько страниц за раз
3. **Мок-режим**: При отсутствии ключей используется мок-режим
4. **Локальные альтернативы**: Можно использовать EasyOCR и Ollama для экономии

### Тестирование Google Cloud интеграции

```bash
# Запустите тесты с Google Cloud
python test_google_cloud_integration.py

# Или с Docker
docker-compose up --build
python test_google_cloud_integration.py
```

## ⚙️ Переменные окружения

### Основная конфигурация

Создайте `.env` файл в корне проекта:

```env
# API Configuration
VITE_API_BASE=http://localhost:8000
API_HOST=0.0.0.0
API_PORT=8000

# Pipeline Configuration
PIPELINE=intelligent_optimized
USE_NEW_PIPELINE=true
PIPELINE_MAX_PARALLEL_SLIDES=5
PIPELINE_MAX_PARALLEL_TTS=10

# AI Providers
LLM_PROVIDER=openrouter
TTS_PROVIDER=google
OCR_PROVIDER=google
STORAGE=minio

# OpenRouter (рекомендуется)
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=meta-llama/llama-3.3-8b-instruct:free

# Google Cloud (альтернатива)
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-1.5-flash
GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-sa.json
GCP_PROJECT_ID=your-project-id

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/slide_speaker
REDIS_URL=redis://redis:6379

# Storage
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET=slide-speaker

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production
CSRF_SECRET_KEY=your-csrf-secret-key

# Logging
LOG_LEVEL=INFO
```

### Docker Compose переменные

Создайте `docker.env` файл:

```env
# Database
POSTGRES_DB=slide_speaker
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# Grafana
GRAFANA_PASSWORD=admin
```

## 🗺️ Roadmap

### ✅ Завершенные этапы

#### Спринт 1: Реальный парсинг документов ✅
- [x] **Парсинг PPTX**: Извлечение слайдов в PNG с высоким качеством
- [x] **Парсинг PDF**: Конвертация страниц в PNG изображения
- [x] **Детекция элементов**: Автоматическое определение текстовых блоков и их координат (bbox)
- [x] **Генерация manifest.json**: Создание структурированных данных о слайдах
- [x] **Оптимизация изображений**: Сжатие PNG без потери качества
- [x] **Валидация файлов**: Проверка корректности загруженных документов

#### Спринт 2: ИИ-лектор с озвучкой ✅
- [x] **LLM интеграция**: Подключение к OpenAI/Anthropic/OpenRouter для генерации speaker notes
- [x] **TTS система**: Преобразование текста в речь с высоким качеством
- [x] **Временная синхронизация**: Выравнивание аудио с визуальными эффектами
- [x] **SSML поддержка**: Точное произношение и word-level timing
- [x] **Параллельная обработка**: Одновременная генерация для всех слайдов
- [x] **Умная синхронизация**: Синхронизация эффектов с произносимыми словами

#### Спринт 3: Экспорт и стабильность ✅
- [x] **Видео экспорт**: Генерация MP4 с синхронизированными эффектами
- [x] **Очереди задач**: Система фоновой обработки длительных операций
- [x] **Хранилище**: Надежное хранение файлов и метаданных
- [x] **Мониторинг**: Логирование и отслеживание ошибок
- [x] **Производительность**: Оптимизация для больших презентаций
- [x] **Тестирование**: Unit и интеграционные тесты

### 🚧 Текущие задачи

#### Улучшения пайплайна
- [ ] **Многоязычная поддержка**: Автоматическое определение языка и перевод
- [ ] **Улучшенная синхронизация**: Более точная синхронизация эффектов с речью
- [ ] **Адаптивные эффекты**: Выбор эффектов на основе типа контента
- [ ] **Кэширование результатов**: Ускорение повторной обработки

#### Пользовательский интерфейс
- [ ] **Редактор контента**: Интерфейс для редактирования сгенерированного контента
- [ ] **Предпросмотр**: Возможность прослушать и отредактировать перед финализацией
- [ ] **Настройки голоса**: Выбор голоса, скорости, тона для TTS
- [ ] **Темы оформления**: Различные стили визуальных эффектов

### 🔮 Планируемые функции

#### Расширенные возможности
- [ ] **Интерактивные элементы**: Кликабельные элементы в презентации
- [ ] **Адаптивная скорость**: Автоматическая подстройка скорости под контент
- [ ] **Аналитика**: Статистика просмотров и взаимодействий
- [ ] **Коллаборация**: Совместное редактирование презентаций

#### Интеграции
- [ ] **Google Slides**: Прямой импорт из Google Slides
- [ ] **PowerPoint Online**: Интеграция с Microsoft 365
- [ ] **YouTube**: Прямая загрузка на YouTube
- [ ] **LMS интеграция**: Поддержка Moodle, Canvas и других LMS

## 🧪 Тестирование

### Быстрые тесты

#### Smoke тест пайплайна
```bash
# Тест Intelligent Optimized пайплайна (по умолчанию)
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@test-presentation.pdf"

# Тест с различными пайплайнами
curl -X POST "http://localhost:8000/upload?pipeline=vision" \
  -H "Authorization: Bearer <token>" \
  -F "file=@test-presentation.pdf"
```

#### Проверка статуса обработки
```bash
# Получить статус урока
curl "http://localhost:8000/lessons/{lesson_id}/status" \
  -H "Authorization: Bearer <token>"

# Получить manifest
curl "http://localhost:8000/lessons/{lesson_id}/manifest" \
  -H "Authorization: Bearer <token>"
```

### Автоматизированные тесты

#### Backend тесты
```bash
cd backend

# Unit тесты
python -m pytest app/tests/ -v

# Тесты пайплайна
python -m pytest app/tests/test_pipeline.py -v

# Тесты API
python -m pytest app/tests/test_api.py -v
```

#### Frontend тесты
```bash
# Unit тесты
npm test

# E2E тесты
npm run test:e2e

# Тесты компонентов
npm run test:components
```

#### Интеграционные тесты
```bash
# Тест полного пайплайна
python test_full_pipeline.py

# Тест экспорта видео
python test_video_export.py

# Тест WebSocket соединений
python test_websocket.py
```

### Тестирование производительности

#### Нагрузочное тестирование
```bash
# Тест параллельной обработки
python test_parallel_processing.py --slides=10 --parallel=5

# Тест памяти
python test_memory_usage.py --slides=50

# Тест времени отклика
python test_response_times.py --requests=100
```

#### Мониторинг ресурсов
```bash
# Мониторинг через Prometheus
curl http://localhost:9090/metrics

# Дашборд Grafana
open http://localhost:3001
```

### Тестирование пайплайнов

#### Тест всех пайплайнов
```bash
# Создайте тестовую презентацию
python create_test_presentation.py

# Тест Intelligent Optimized
python test_pipeline.py --pipeline=intelligent_optimized

# Тест Classic
python test_pipeline.py --pipeline=classic

# Тест Vision
python test_pipeline.py --pipeline=vision

# Тест Hybrid
python test_pipeline.py --pipeline=hybrid
```

#### Тест провайдеров
```bash
# Тест OCR провайдеров
python test_ocr_providers.py

# Тест LLM провайдеров
python test_llm_providers.py

# Тест TTS провайдеров
python test_tts_providers.py
```

### Smoke Test

#### Запуск через Docker
```bash
# Запустите все сервисы
docker-compose up --build

# Проверьте здоровье API
curl http://localhost:8000/health
# Ожидаемый ответ: {"status":"ok"}

# Проверьте доступность статики
curl http://localhost:8000/assets/demo-lesson/manifest.json
```

#### Запуск локально
```bash
# Backend
cd backend
pip install -r requirements.txt --break-system-packages
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (в другом терминале)
npm install
npm run dev

# Проверьте здоровье API
curl http://localhost:8000/health
# Ожидаемый ответ: {"status":"ok"}
```

#### Полный smoke test
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

## 🔧 Устранение неполадок

### Проблемы с пайплайном

#### Ошибка "Pipeline failed"
```bash
# Проверьте логи
docker-compose logs backend

# Проверьте статус Celery workers
docker-compose exec celery celery -A app.celery_app inspect active

# Перезапустите workers
docker-compose restart celery
```

#### Ошибка "OCR extraction failed"
```bash
# Проверьте Google Cloud credentials
ls -la keys/gcp-sa.json

# Проверьте переменные окружения
docker-compose exec backend env | grep -E "(GOOGLE|GCP)"

# Переключитесь на локальный OCR
echo "OCR_PROVIDER=easyocr" >> .env
docker-compose restart backend
```

#### Ошибка "TTS generation failed"
```bash
# Проверьте API ключи
docker-compose exec backend env | grep -E "(OPENROUTER|GEMINI|OPENAI)"

# Переключитесь на mock TTS для тестирования
echo "TTS_PROVIDER=mock" >> .env
docker-compose restart backend
```

#### Ошибка "Visual effects failed"
```bash
# Проверьте manifest.json
docker-compose exec backend cat .data/{lesson_id}/manifest.json

# Проверьте элементы слайдов
docker-compose exec backend ls -la .data/{lesson_id}/slides/
```

### Проблемы с производительностью

#### Медленная обработка
```bash
# Увеличьте параллелизм
echo "PIPELINE_MAX_PARALLEL_SLIDES=10" >> .env
echo "PIPELINE_MAX_PARALLEL_TTS=20" >> .env
docker-compose restart backend celery
```

#### Высокое потребление памяти
```bash
# Уменьшите параллелизм
echo "PIPELINE_MAX_PARALLEL_SLIDES=3" >> .env
echo "PIPELINE_MAX_PARALLEL_TTS=5" >> .env
docker-compose restart backend celery
```

### Проблемы с Docker

#### Ошибка "Port already in use"
```bash
# Остановите конфликтующие сервисы
sudo lsof -i :8000
sudo kill -9 <PID>

# Или измените порты в docker-compose.yml
```

#### Ошибка "Volume mount failed"
```bash
# Создайте необходимые директории
mkdir -p .data
mkdir -p keys
chmod 755 .data keys
```

### Проблемы с базой данных

#### Ошибка подключения к PostgreSQL
```bash
# Проверьте статус базы данных
docker-compose ps postgres

# Перезапустите базу данных
docker-compose restart postgres db-init

# Проверьте логи
docker-compose logs postgres
```

#### Ошибка миграций
```bash
# Запустите миграции вручную
docker-compose exec backend alembic upgrade head

# Сбросьте базу данных (ВНИМАНИЕ: удалит все данные)
docker-compose down -v
docker-compose up -d postgres db-init
```

## 🎯 Демо режим

Нажмите "Посмотреть демо" на главной странице для просмотра примера с предустановленными данными.

**Демо включает:**
- 3 слайда с различными типами контента
- Полную озвучку с синхронизацией
- Визуальные эффекты (подсветки, подчеркивания, лазер)
- Интерактивный плеер с контролами

## ✅ Финальный Smoke Checklist

### 🚀 Запуск системы
- [ ] `docker-compose up --build` поднимает все сервисы без ошибок
- [ ] `GET http://localhost:8000/health` → `{"status":"ok"}`
- [ ] `GET http://localhost:8000/health/detailed` → детальная информация о сервисах
- [ ] Frontend доступен на http://localhost:3000
- [ ] API Docs доступны на http://localhost:8000/docs

### 📁 Загрузка и обработка
- [ ] Upload PDF/PPTX → файл принимается и начинается обработка
- [ ] WebSocket уведомления о прогрессе работают
- [ ] Статус обработки обновляется в реальном времени
- [ ] Manifest.json создается после завершения обработки

### 🎵 Воспроизведение
- [ ] Демо лекция загружается без ошибок
- [ ] Аудио воспроизводится (если настроен TTS)
- [ ] Слайды переключаются автоматически
- [ ] Визуальные эффекты синхронизированы с речью
- [ ] Player контролы работают (play/pause, перемотка)

### 🎨 Визуальные эффекты
- [ ] Подсветки появляются в нужное время
- [ ] Подчеркивания синхронизированы с речью
- [ ] Лазерная указка движется плавно
- [ ] Эффекты масштабируются при изменении размера окна
- [ ] Нет "телепортов" или скачков элементов

### 📤 Экспорт видео
- [ ] Export запускается без ошибок
- [ ] Статус экспорта отслеживается
- [ ] MP4 файл генерируется и скачивается
- [ ] Видео содержит аудио и визуальные эффекты

### 🔧 Мониторинг
- [ ] Prometheus метрики доступны на http://localhost:9090
- [ ] Grafana дашборды работают на http://localhost:3001
- [ ] Логи не содержат критических ошибок
- [ ] Celery workers обрабатывают задачи

### 🧪 Команды для проверки

```bash
# 1. Запуск всех сервисов
docker-compose up --build

# 2. Проверка здоровья API
curl http://localhost:8000/health

# 3. Проверка демо данных
curl http://localhost:8000/lessons/demo-lesson/manifest.json

# 4. Тест загрузки файла
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@test-presentation.pdf"

# 5. Тест экспорта
curl -X POST "http://localhost:8000/lessons/demo-lesson/export" \
  -H "Authorization: Bearer <token>"

# 6. Проверка метрик
curl http://localhost:9090/metrics

# 7. Фронтенд тест
# Откройте http://localhost:3000
# Нажмите "Посмотреть демо"
# Проверьте все функции плеера
```

### 🐛 Устранение проблем

Если что-то не работает:

1. **Проверьте логи**: `docker-compose logs backend`
2. **Проверьте статус сервисов**: `docker-compose ps`
3. **Перезапустите проблемный сервис**: `docker-compose restart <service>`
4. **Проверьте переменные окружения**: `docker-compose exec backend env`
5. **Очистите данные**: `docker-compose down -v && docker-compose up --build`