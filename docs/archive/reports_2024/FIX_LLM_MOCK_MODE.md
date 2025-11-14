# Исправление проблемы: ИИ не генерирует текст презентации

## Проблема
ИИ использовал mock-режим (заглушки) вместо реальной генерации текста через OpenRouter API.

## Причина
В файле `backend_env_final.env` был установлен провайдер `LLM_PROVIDER=gemini`, но:
1. Gemini требует активации Vertex AI API в Google Cloud
2. Регион europe-west1 может не поддерживать Gemini
3. Вместо этого у нас настроен и готов к работе OpenRouter с API ключом

## Что было исправлено

### 1. Файл `backend_env_final.env`
**Изменено:**
- `LLM_PROVIDER=gemini` → `LLM_PROVIDER=openrouter`
- Добавлены настройки OpenRouter:
  ```env
  OPENROUTER_API_KEY=your_openrouter_api_key_here
  OPENROUTER_MODEL=x-ai/grok-4-fast:free
  OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
  LLM_LANGUAGE=ru
  ```

### 2. Файл `backend/.env`
**Добавлено:**
- `LLM_LANGUAGE=ru` для русскоязычной генерации

## Как проверить исправление

### 1. Перезапустить бэкенд
```bash
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main
./stop.sh  # Если запущен
./start.sh
```

### 2. Загрузить презентацию заново
- Откройте веб-интерфейс (обычно http://localhost:5173)
- Загрузите презентацию
- Дождитесь обработки

### 3. Проверить логи
```bash
cd backend
tail -f .data/logs/app.log | grep -i "llm\|openrouter\|mock"
```

**Ожидаемое поведение:**
- Не должно быть сообщений "will use mock mode"
- Должны быть сообщения "Generated SSML lecture text" с реальным количеством символов
- Текст презентации должен быть осмысленным, а не шаблонным

## Проверка работы OpenRouter

Тестовая команда:
```bash
cd backend
python3 -c "
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, './workers')

# Загрузить .env
from dotenv import load_dotenv
load_dotenv('.env')

from workers.llm_openrouter_ssml import OpenRouterLLMWorkerSSML

worker = OpenRouterLLMWorkerSSML()
print('✅ Worker initialized')
print(f'use_mock: {worker.use_mock}')
print(f'API key: {worker.api_key[:20]}...' if worker.api_key else 'NOT FOUND')
print(f'Model: {worker.model}')

if not worker.use_mock:
    print('✅ OpenRouter is ACTIVE (not using mock mode)')
else:
    print('❌ OpenRouter is in MOCK mode - check configuration')
"
```

## Техническая информация

### Как работает выбор провайдера
1. `backend/app/main.py` загружает `backend_env_final.env`
2. В нем установлен `LLM_PROVIDER=openrouter`
3. `backend/app/services/provider_factory.py` создает экземпляр `OpenRouterLLMWorker`
4. Worker проверяет наличие `OPENROUTER_API_KEY` и библиотеки `openai`
5. Если все ОК → использует реальный API, иначе → mock mode

### Проверка mock-режима в коде
Файл: `backend/workers/llm_openrouter_ssml.py`
```python
if not self.api_key or not OPENAI_AVAILABLE:
    logger.warning("OpenRouter API key not provided or OpenAI client not available, will use mock mode")
    self.use_mock = True
```

## Дополнительные настройки

### Для других провайдеров LLM

#### Вариант 1: Использовать Gemini (требует настройки)
1. Активировать Vertex AI API в Google Cloud Console
2. Выбрать регион us-central1 вместо europe-west1
3. Изменить в `.env`:
   ```env
   LLM_PROVIDER=gemini
   GEMINI_LOCATION=us-central1
   ```

#### Вариант 2: Использовать другую модель OpenRouter
Список доступных моделей: https://openrouter.ai/models
```env
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
# или
OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct
```

## Статус после исправления
✅ TTS (Google Cloud Text-to-Speech) - РАБОТАЕТ
✅ LLM (OpenRouter) - РАБОТАЕТ  
⚠️ Document AI - работает в fallback режиме
⚠️ Gemini - в резерве (fallback)

## Контакты для проверки
- Backend URL: http://localhost:8000
- Frontend URL: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
