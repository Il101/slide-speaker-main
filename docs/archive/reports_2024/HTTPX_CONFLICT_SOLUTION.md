# 🔧 Конфликт httpx версий - Решение

## Проблема

Конфликт зависимостей между Google Cloud и OpenAI библиотеками:

```
google-genai 1.39.1 → требует httpx>=0.28.1
openai 1.54.0 → требует httpx==0.25.2
```

## Причина

- **Docker** использует `LLM_PROVIDER=gemini` → нужен `google-cloud-aiplatform`
- **google-cloud-aiplatform 1.119.0** автоматически установил `google-genai 1.39.1`
- **google-genai** конфликтует с **openai** по версии httpx
- **openai** нужен для:
  - `openai-whisper` (распознавание речи)
  - `OpenRouterLLMWorker` (fallback провайдер)

## 🎯 Решение

### Вариант 1: Откатить google-cloud-aiplatform (РЕКОМЕНДУЕТСЯ)

Использовать версию **1.38.1** (как в requirements.txt):

```bash
# backend/requirements.txt уже правильный:
google-cloud-aiplatform==1.38.1  # ✅ Без google-genai

# Переустановить:
pip install google-cloud-aiplatform==1.38.1
```

**Преимущества:**
- ✅ Совместимо с openai
- ✅ Все функции Gemini работают
- ✅ Нет конфликтов

### Вариант 2: Обновить openai до версии с httpx 0.28

```bash
# Обновить до последней версии openai
pip install openai>=1.60.0
pip install httpx>=0.28.1
```

**НО:** Может сломать другие зависимости!

### Вариант 3: Разделить environments

**Для Docker (Gemini):**
```dockerfile
# Не ставить openai вообще
RUN pip install google-cloud-aiplatform==1.38.1
```

**Для локальной разработки (OpenRouter):**
```bash
# Ставить openai с httpx 0.25.2
pip install openai==1.54.0 httpx==0.25.2
```

## ✅ Исправление в requirements.txt

Проверить версию:

```txt
# backend/requirements.txt
google-cloud-aiplatform==1.38.1  # ✅ НЕ 1.119.0!
openai==1.54.0
httpx==0.25.2
```

## 🧪 Тестирование

```bash
# После исправления проверить:
cd backend
pip install -r requirements.txt

# Проверка Google Cloud
python3 -c "
from app.services.provider_factory import ProviderFactory
import os
os.environ['LLM_PROVIDER'] = 'gemini'
provider = ProviderFactory.get_llm_provider()
print(f'Gemini: {type(provider).__name__}')
"

# Проверка OpenRouter
python3 -c "
from app.services.provider_factory import ProviderFactory
import os
os.environ['LLM_PROVIDER'] = 'openrouter'
provider = ProviderFactory.get_llm_provider()
print(f'OpenRouter: {type(provider).__name__}')
"
```

## 📦 Docker Build

После исправления пересобрать:

```bash
docker-compose down
docker-compose build --no-cache backend
docker-compose up
```

## Итог

**Используйте google-cloud-aiplatform==1.38.1** как указано в requirements.txt, чтобы избежать конфликта с google-genai.
