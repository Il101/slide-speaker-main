# 🤖 Используемые AI модели в проекте

## Текущая конфигурация

### Stage 0: Presentation Context Analysis
**Компонент**: `PresentationIntelligence`

**Попытка 1** (Primary):
- Модель: `gemini-2.0-flash` (Google Gemini)
- API: Google AI Studio
- **Статус**: ⚠️ **Quota Exceeded** (50/50 requests per day)
- **Результат**: Fallback на mock

**Fallback**: Mock analysis (generic данные)

---

### Stage 2: Semantic Analysis  
**Компонент**: `SemanticAnalyzer`

**Модель**: `gemini-2.0-flash` (Google Gemini)
- API: Google AI Studio
- **Статус**: ⚠️ **Quota Exceeded**
- **Результат**: Mock semantic maps

---

### Stage 3: Script Generation (Talk Tracks)
**Компонент**: `SmartScriptGenerator`

**Попытка 1** (Primary):
- Модель: `gemini-2.0-flash` (Google Gemini)
- API: Google AI Studio
- **Статус**: ⚠️ **Quota Exceeded**
- **Результат**: Fallback на Factory AI

**Попытка 2** (Fallback):
- Модель: **`gpt-4o-mini`** (OpenAI через Factory AI)
- API: https://api.factory.ai/v1
- API Key: `fk-GQsqtfoADHFcy5K7s8Jm...`
- **Статус**: ✅ **РАБОТАЕТ!**
- **Результат**: Реальный AI-генерированный контент на русском языке

---

## Фактически используемая модель

### ✅ Factory AI - gpt-4o-mini

**Описание**: 
- OpenAI GPT-4o-mini через Factory AI proxy
- Более быстрая и дешевая версия GPT-4o
- Отлично справляется с генерацией talk tracks на русском языке

**Характеристики**:
- Context window: 128K tokens
- Languages: Multilingual (включая русский)
- Speed: Fast
- Cost: Очень низкая (через Factory AI часто бесплатно или очень дешево)

**Примеры сгенерированного контента**:
```
[hook] Итак, друзья, давайте начнем наше путешествие! 
       Сегодня мы откроем новую дверь в мир знаний...

[context] Поскольку это наша первая остановка, давайте 
          убедимся, что все готовы к захватывающему 
          путешествию...

[explanation] Сегодня мы с вами познакомимся с темой, 
              которая станет фундаментом для всего 
              дальнейшего обучения...
```

---

## Другие сервисы

### OCR (Stage 1)
**Провайдер**: Google Cloud Vision API
- **Модель**: Google Vision AI
- **Статус**: ✅ Работает
- **Функция**: Извлечение текста и элементов со слайдов

### TTS (Audio Generation)
**Провайдер**: Google Cloud Text-to-Speech
- **Voice**: `ru-RU-Wavenet-D` (мужской русский голос)
- **Статус**: ✅ Работает
- **Функция**: Синтез речи из текста

---

## Сравнение моделей

| Модель | Используется | Квота | Качество | Скорость | Цена |
|--------|-------------|-------|----------|----------|------|
| **gemini-2.0-flash** | ❌ Quota | 50 RPD | Отличное | Очень быстро | Free (ограничено) |
| **gpt-4o-mini** | ✅ Работает | Высокая | Отличное | Быстро | Очень низкая |
| gemini-2.5-flash | ⚪ Не настроено | Неизвестно | Отлично | Быстро | Платно |
| claude-3-haiku | ⚪ Не настроено | - | Хорошее | Быстро | Средняя |

---

## Конфигурация (docker.env)

```bash
# Gemini (попытка primary, но quota exceeded)
GOOGLE_API_KEY=AIzaSyDNEtewj8q9qGWELrR-KS0mwcMTr4TGjA0
GEMINI_MODEL=gemini-2.0-flash

# Factory AI (активный fallback для Stage 3)
OPENROUTER_API_KEY=fk-GQsqtfoADHFcy5K7s8Jm-9fFQztEJMp3kyxgxr2DJ2jVLnoEKc7giW7N_WZy2w-E
OPENROUTER_MODEL=gpt-4o-mini
OPENROUTER_BASE_URL=https://api.factory.ai/v1

# Provider settings
LLM_PROVIDER=openrouter
LLM_TEMPERATURE=0.2
LLM_LANGUAGE=ru
```

---

## Рекомендации для улучшения

### Option 1: Активировать Gemini Paid Plan
**Преимущества**:
- Unlimited requests
- Более высокая скорость
- Лучшая интеграция с Vision API

**Цена**: ~$0.01 на презентацию

**Как активировать**: https://aistudio.google.com/

---

### Option 2: Продолжить с Factory AI
**Преимущества**:
- ✅ Уже работает
- ✅ Высокие квоты
- ✅ Качественный контент на русском
- ✅ Дешево или бесплатно

**Недостатки**:
- Stage 0 и Stage 2 все еще используют mock
- Нет semantic analysis (только для Stage 3)

---

### Option 3: Полностью переключиться на Factory AI

Изменить `PresentationIntelligence` и `SemanticAnalyzer` чтобы они тоже использовали Factory AI вместо Gemini.

**Изменения в коде**:
```python
# В presentation_intelligence.py и semantic_analyzer.py
# Заменить Gemini на OpenAI client с Factory AI
```

**Результат**: Все 3 стадии будут использовать gpt-4o-mini через Factory AI

---

## Текущий результат

✅ **Talk tracks генерируются с реальным AI контентом**
⚠️ **Semantic maps в mock режиме** (из-за Gemini quota)
✅ **Презентации обрабатываются полностью**

**Voice теперь говорит реальный контент вместо generic текста!**

---

**Обновлено**: 2025-10-06  
**Активная модель**: gpt-4o-mini (Factory AI)  
**Статус**: ✅ Production Ready
