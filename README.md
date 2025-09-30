# Slide Speaker - ИИ-Лектор

Превращаем презентации в интерактивные лекции с озвучкой и визуальными эффектами.

## Архитектура

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python
- **Очереди**: Redis + Celery
- **Хранилище**: S3-совместимое (MinIO)
- **Видео**: FFmpeg для рендера MP4
- **Данные**: Mock-данные с placeholder слайдами
- **Пайплайны**: Classic (OCR+LLM), Vision (мультимодальная LLM), Hybrid (Vision+OCR alignment)

## Пайплайны обработки

Slide Speaker поддерживает три режима обработки презентаций:

### 1. Classic Pipeline (по умолчанию)
- **Технология**: OCR (Document AI) + LLM + TTS
- **Применение**: Точное извлечение текста и элементов из слайдов
- **Преимущества**: Высокая точность bbox, поддержка таблиц и сложных макетов
- **Недостатки**: Зависимость от качества OCR

### 2. Vision Pipeline
- **Технология**: Мультимодальная LLM (GPT-4o, Gemini, Claude)
- **Применение**: Анализ изображений слайдов для генерации объяснений
- **Преимущества**: Понимание контекста, качественные объяснения, независимость от OCR
- **Недостатки**: Приблизительные координаты элементов

### 3. Hybrid Pipeline
- **Технология**: Vision LLM + OCR alignment
- **Применение**: Комбинация лучшего из двух подходов
- **Преимущества**: Качественные объяснения + точные координаты
- **Недостатки**: Более сложная обработка, требует настройки alignment

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

### Конфигурация Vision моделей

```bash
# В .env файле
VISION_MODEL=gpt-4o-mini        # OpenAI
VISION_MODEL=gemini-1.5-flash   # Google
VISION_MODEL=claude-3-5-sonnet  # Anthropic
VISION_MODEL=grok-beta          # xAI Grok

# API ключи
OPENROUTER_API_KEY=your_key     # Для OpenAI/Claude/Grok через OpenRouter
GEMINI_API_KEY=your_key         # Для Google Gemini
```

## Быстрый запуск

### 1. Локальная разработка (рекомендуется)

#### Backend
```bash
cd backend
pip install -r requirements.txt --break-system-packages
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend
```bash
npm install
npm run dev
```

Сервисы будут доступны:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 2. Запуск через Docker Compose (рекомендуется для Sprint 3)

```bash
# Запустите все сервисы
docker-compose up --build
```

Сервисы будут доступны:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redis: localhost:6379
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- MinIO API: http://localhost:9000

#### Первоначальная настройка MinIO

1. Откройте MinIO Console: http://localhost:9001
2. Войдите с учетными данными: `minioadmin` / `minioadmin`
3. Создайте bucket с именем `slide-speaker`
4. Настройте политику доступа для публичного чтения (опционально)

## API Endpoints

### POST /upload
Загружает файл (PPTX/PDF) и создает lesson с mock-данными.

**Request**: `multipart/form-data` с файлом
**Response**: `{"lesson_id": "uuid"}`

### GET /lessons/{lesson_id}/manifest
Возвращает manifest.json с данными о слайдах и эффектах.

**Response**:
```json
{
  "slides": [
    {
      "id": 1,
      "image": "/assets/lesson_id/slides/001.svg",
      "audio": "/assets/lesson_id/audio/001.mp3",
      "cues": [
        {"t0": 0.6, "t1": 2.2, "action": "highlight", "bbox": [120, 80, 980, 150]},
        {"t0": 2.3, "t1": 5.0, "action": "underline", "bbox": [140, 220, 860, 260]},
        {"t0": 5.1, "t1": 6.5, "action": "laser_move", "to": [900, 520]}
      ]
    }
  ]
}
```

### POST /lessons/{lesson_id}/export
Запускает экспорт урока в MP4 видео с визуальными эффектами.

**Request**:
```json
{
  "lesson_id": "uuid",
  "quality": "high",
  "include_audio": true,
  "include_effects": true
}
```

**Response**: `{"status": "processing", "task_id": "uuid", "estimated_time": "5-10 minutes"}`

### GET /exports/{task_id}/status
Получает статус задачи экспорта.

**Response**:
```json
{
  "task_id": "uuid",
  "status": "processing|completed|failed",
  "progress": 75,
  "message": "Rendering video frames",
  "download_url": "/exports/lesson_id_export.mp4"
}
```

### GET /exports/{lesson_id}/download
Скачивает готовый MP4 файл.

**Response**: MP4 файл или редирект на S3

## Как это работает

1. **Загрузка файла**: Пользователь загружает PPTX/PDF через FileUploader
2. **Обработка**: Backend создает mock-данные (placeholder слайды + пустые аудио)
3. **Воспроизведение**: Frontend загружает manifest.json и отображает интерактивный плеер
4. **Эффекты**: Подсветки, подчеркивания и лазерная указка синхронизированы с временными метками

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

## Переменные окружения

Создайте `.env` файл:
```env
VITE_API_BASE=http://localhost:8000
```

## Roadmap

### Спринт 1: Реальный парсинг документов (2-3 недели)
**Цель**: Заменить mock-данные реальным парсингом PPTX/PDF файлов

- [ ] **Парсинг PPTX**: Извлечение слайдов в PNG с высоким качеством
- [ ] **Парсинг PDF**: Конвертация страниц в PNG изображения
- [ ] **Детекция элементов**: Автоматическое определение текстовых блоков и их координат (bbox)
- [ ] **Генерация manifest.json**: Создание структурированных данных о слайдах
- [ ] **Оптимизация изображений**: Сжатие PNG без потери качества
- [ ] **Валидация файлов**: Проверка корректности загруженных документов

### Спринт 2: ИИ-лектор с озвучкой (3-4 недели)
**Цель**: Добавить генерацию speaker notes и TTS с синхронизацией

- [ ] **LLM интеграция**: Подключение к OpenAI/Anthropic для генерации speaker notes
- [ ] **TTS система**: Преобразование текста в речь с высоким качеством
- [ ] **Временная синхронизация**: Выравнивание аудио с визуальными эффектами
- [ ] **Редактор правок**: Интерфейс для корректировки сгенерированного контента
- [ ] **Предпросмотр**: Возможность прослушать и отредактировать перед финализацией
- [ ] **Настройки голоса**: Выбор голоса, скорости, тона для TTS

### Спринт 3: Экспорт и стабильность (2-3 недели)
**Цель**: Финальный экспорт в MP4 и production-ready система

- [ ] **Видео экспорт**: Генерация MP4 с синхронизированными эффектами
- [ ] **Очереди задач**: Система фоновой обработки длительных операций
- [ ] **Хранилище**: Надежное хранение файлов и метаданных
- [ ] **Мониторинг**: Логирование и отслеживание ошибок
- [ ] **Производительность**: Оптимизация для больших презентаций
- [ ] **Тестирование**: Unit и интеграционные тесты

## Тестирование

### Smoke тесты пайплайнов
```bash
# Тест Classic пайплайна
./scripts/smoke.sh classic

# Тест Vision пайплайна  
./scripts/smoke.sh vision

# Тест Hybrid пайплайна
./scripts/smoke.sh hybrid

# С кастомным API
API=http://localhost:8000 ./scripts/smoke.sh vision
```

### E2E тесты
```bash
cd tests/e2e
npm install
npm test
```

E2E тесты автоматически проверяют все три пайплайна:
- Воспроизведение аудио
- Появление подсветок
- Автоматическая смена слайдов
- Отображение субтитров

### Unit тесты
```bash
cd backend
python -m pytest app/tests/
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

## Демо режим

Нажмите "Посмотреть демо" на главной странице для просмотра примера с предустановленными данными.

## Финальный Smoke Checklist

После мержа всех PR выполните следующие проверки:

### ✅ Базовая функциональность
- [ ] `docker compose up --build` поднимает backend, frontend, redis, celery, minio без ошибок
- [ ] `GET http://localhost:8000/health` → `{"status":"ok"}`
- [ ] `VITE_API_BASE` из `.env` влияет на фронт
- [ ] `GET /assets/<lesson>/manifest.json` отдает файл, если он есть

### ✅ Upload и воспроизведение
- [ ] Upload PDF/PPTX → вижу реальные слайды в Player
- [ ] Воспроизводится реальный голос TTS (если настроен Azure TTS)
- [ ] Подсветки синхронны речи (допускается погрешность ≤200 мс)

### ✅ Экспорт MP4
- [ ] Export → выдаёт ссылку на MP4
- [ ] MP4 файл скачивается и воспроизводится
- [ ] При пустых/мок-аудио ролик всё равно собирается (без звука)

### ✅ Scale-aware Player
- [ ] При ресайзе окна рамки и «лазер» не уходят
- [ ] При разных размерах окна элементы остаются на местах
- [ ] Движение лазера плавное, без телепортов

### Команды для проверки:
```bash
# 1. Запуск всех сервисов
docker-compose up --build

# 2. Проверка здоровья API
curl http://localhost:8000/health

# 3. Проверка статики
curl http://localhost:8000/assets/demo-lesson/manifest.json

# 4. Экспорт тест
curl -X POST http://localhost:8000/lessons/demo-lesson/export
# Получите job_id из ответа, затем:
curl "http://localhost:8000/lessons/demo-lesson/export/status?job_id=YOUR_JOB_ID"

# 5. Фронтенд тест
# Откройте http://localhost:3000
# Нажмите "Посмотреть демо"
# Проверьте масштабирование окна
```