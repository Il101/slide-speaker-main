# ⚠️ Gemini API Quota Exceeded

## Проблема

При обработке презентаций возникает ошибка:

```
429 You exceeded your current quota, please check your plan and billing details.
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
Limit: 50 requests per day
Model: gemini-2.0-flash-exp
```

**Результат**: Система автоматически переключается на **mock fallback** с generic текстом:
- "Let's explore an important concept"
- "This relates to what we discussed earlier"
- "The key idea here is..."
- "Imagine a situation where..."

## Почему это произошло

### Free Tier Limits (Gemini API)

| Модель | Запросов в день | Запросов в минуту |
|--------|----------------|-------------------|
| gemini-2.0-flash-exp | **50** | 15 |
| gemini-1.5-flash | 1,500 | 15 |
| gemini-1.5-pro | 50 | 2 |

**Наш случай**: 
- Обработано несколько презентаций с десятками слайдов
- Каждый слайд требует 2-3 Gemini API вызова (Stage 0, 2, 3)
- Презентация на 34 слайда = ~100+ запросов
- Квота 50 запросов/день исчерпана за 1 презентацию!

## Решения

### 🔥 Немедленное решение (переключение на stable model)

Используйте `gemini-1.5-flash` вместо `gemini-2.0-flash-exp`:

**docker.env**:
```bash
# Изменить
GEMINI_MODEL=gemini-2.0-flash-exp

# На
GEMINI_MODEL=gemini-1.5-flash
```

**Преимущества**:
- ✅ Квота: **1,500 запросов/день** (вместо 50)
- ✅ Стабильная модель (не experimental)
- ✅ Тот же уровень качества

**Недостатки**:
- Чуть медленнее чем 2.0-flash-exp

### 💰 Долгосрочное решение (paid plan)

#### Option 1: Pay-as-you-go

Активировать платный план на Google AI Studio:

**Цены**:
- `gemini-1.5-flash`: $0.075 / $0.30 per 1M tokens
- `gemini-1.5-pro`: $1.25 / $5.00 per 1M tokens

**Квоты**:
- gemini-1.5-flash: **2,000 RPM** / unlimited RPD
- gemini-1.5-pro: **1,000 RPM** / unlimited RPD

**Стоимость для типичной презентации (30 слайдов)**:
- Input: ~50k tokens = $0.0037
- Output: ~30k tokens = $0.009
- **Total: ~$0.01 per presentation**

#### Option 2: Vertex AI

Переключиться на Vertex AI Gemini:

**Преимущества**:
- ✅ Enterprise-grade quotas
- ✅ Более высокие rate limits
- ✅ SLA guarantees
- ✅ Regional deployment (EU, US, Asia)

**Изменения в коде**:
```python
# Вместо
import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Использовать
from google.cloud import aiplatform
aiplatform.init(
    project=os.getenv("GCP_PROJECT_ID"),
    location=os.getenv("GEMINI_LOCATION")
)
```

### 🔄 Оптимизация использования (reduce API calls)

#### 1. Batch Processing для Stage 0

Вместо анализа каждого слайда отдельно, анализировать всю презентацию один раз:

```python
# Сейчас: 34 слайда = 34 вызова Stage 0
# Оптимизация: 1 вызов для всей презентации
```

**Экономия**: ~30 запросов на презентацию

#### 2. Кеширование презентаций

Если презентация уже обрабатывалась, использовать кешированные результаты:

```python
# Check cache before API call
cache_key = f"{lesson_id}_{slide_index}_semantic_map"
if cache.exists(cache_key):
    return cache.get(cache_key)
```

#### 3. Fallback на менее частотные операции

Stage 3 (script generation) можно сделать опциональным:

```python
# Если квота исчерпана для Stage 3
# Использовать шаблонные скрипты с подстановкой текста слайдов
```

## Как применить исправление

### Быстрое решение (5 минут)

```bash
# 1. Обновить модель
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main
sed -i '' 's/GEMINI_MODEL=gemini-2.0-flash-exp/GEMINI_MODEL=gemini-1.5-flash/' docker.env

# 2. Пересоздать контейнеры
docker compose down
docker compose up -d

# 3. Подождать 24 часа для сброса квоты
# Или переключиться на paid plan
```

### Проверка статуса квоты

```bash
# Проверить сколько запросов осталось
docker compose logs celery | grep -i "quota\|rate limit"
```

### Когда квота сбросится

Free tier квоты сбрасываются:
- **Daily limit**: В 00:00 UTC (midnight Pacific Time)
- **Per-minute limit**: Каждую минуту

## Мониторинг

Добавить алерты на quota errors:

```python
# В celery logs
if "quota exceeded" in error_message:
    notify_admin("Gemini quota exceeded - switching to fallback")
```

## Статус исправлений

- ✅ Stage 0, 2, 3 используют Gemini (код обновлен)
- ⚠️ Квота исчерпана → automatic mock fallback
- 🔄 Решение: изменить модель или активировать paid plan

## Рекомендации

### Для production:

1. **Используйте `gemini-1.5-flash`** (stable + 1,500 RPD)
2. **Активируйте paid plan** для unlimited requests
3. **Добавьте мониторинг квот** в Grafana
4. **Кешируйте результаты** для повторных обработок

### Для development:

1. Используйте меньшие тестовые презентации (3-5 слайдов)
2. Переключайтесь между API keys для тестирования
3. Локальный mock mode для быстрого тестирования UI

---

**Текущий статус**: 
- Код ✅ исправлен
- Gemini интеграция ✅ работает
- API квота ⚠️ исчерпана (50/50 за сегодня)
- Fallback на mock ⚠️ активен

**Следующий шаг**: Изменить `GEMINI_MODEL=gemini-1.5-flash` или дождаться сброса квоты в 00:00 UTC.
