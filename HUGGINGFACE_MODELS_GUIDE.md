# Hugging Face Inference API - Vision Models Guide

## 📋 Overview

Hugging Face предоставляет **Serverless Inference API** для доступа к 200+ моделям без управления инфраструктурой.

---

## 💰 Pricing & Limits

### **Free Tier**
- **Кредиты:** $0.10/месяц
- **Rate limit:** 50 запросов/час
- **Доступ:** Все публичные модели

### **PRO Account** ($9/месяц)
- **Кредиты:** $2.00/месяц
- **Rate limit:** 500 запросов/час  
- **Бонусы:** Приоритет GPU, больше ресурсов

### **Enterprise** (от $50/юзер/месяц)
- Неограниченные кредиты
- Высокие rate limits
- Поддержка 24/7

---

## 🎯 Top Vision Models на Hugging Face

### **Tier 1: Best Quality & Open Source**

#### **1. Meta LLaVA-v1.6-Mistral-7B** ⭐⭐⭐⭐⭐
```
Model: llava-hf/llava-v1.6-mistral-7b-hf
Size: 7B parameters
Context: 32k tokens
Vision: ✅ High quality
```
**Характеристики:**
- Основан на Mistral 7B (отличный backbone)
- Excellent vision understanding
- Открытая лицензия
- Топ на бенчмарках

**Использование:**
```python
from huggingface_hub import InferenceClient

client = InferenceClient(token="YOUR_HF_TOKEN")
result = client.visual_question_answering(
    image="slide.png",
    question="Describe the layout of this slide"
)
```

---

#### **2. Microsoft Phi-3-Vision-128k** ⭐⭐⭐⭐⭐
```
Model: microsoft/Phi-3-vision-128k-instruct
Size: 4.2B parameters
Context: 128k tokens (огромный!)
Vision: ✅ Excellent
```
**Характеристики:**
- Компактная (4.2B), но мощная
- 128k контекст (лучше всех!)
- Microsoft качество
- Fast inference

**Особенности:**
- Отлично для документов
- Понимает таблицы и графики
- Хорошо работает с text-heavy slides

---

#### **3. Qwen2-VL-7B-Instruct** ⭐⭐⭐⭐⭐
```
Model: Qwen/Qwen2-VL-7B-Instruct
Size: 7B parameters
Context: 32k tokens
Vision: ✅ State-of-the-art
```
**Характеристики:**
- Alibaba Cloud разработка
- Топовые результаты на бенчмарках
- Multiresolution support
- Excellent reasoning

---

#### **4. MiniCPM-V-2.6** ⭐⭐⭐⭐
```
Model: openbmb/MiniCPM-V-2_6
Size: 8B parameters
Context: 8k tokens
Vision: ✅ Very good
```
**Характеристики:**
- Компактная и быстрая
- Хорошее качество/размер
- OCR capabilities
- Multi-language support

---

### **Tier 2: Fast & Lightweight**

#### **5. Moondream2** ⭐⭐⭐
```
Model: vikhyatk/moondream2
Size: 1.8B parameters
Context: 2k tokens
Vision: ✅ Good for simple tasks
```
**Характеристики:**
- Очень быстрая
- Маленькая (1.8B)
- Хорошо для простых слайдов
- Low resource usage

**Best for:**
- Быстрый inference
- Простые презентации
- Ограниченные ресурсы

---

#### **6. IDEFICS2-8B** ⭐⭐⭐⭐
```
Model: HuggingFaceM4/idefics2-8b
Size: 8B parameters
Context: 8k tokens
Vision: ✅ Good
```
**Характеристики:**
- Hugging Face собственная модель
- Оптимизирована для HF API
- Хорошая документация
- Open source

---

## 💡 Стоимость через HF API

### **Расчет для нашего пайплайна:**

**Intelligent Pipeline использует:**
- Stage 0: 1 запрос (presentation context)
- Stage 2: 1 запрос/слайд (semantic analysis + vision)
- Stage 3: 1.5 запроса/слайд в среднем (script generation)

**Итого:** ~2.5 запроса/слайд

### **100 слайдов = 250 запросов**

#### **Free Tier** ($0.10/месяц):
- Rate limit: **50 запросов/час**
- 100 слайдов = **5 часов** обработки
- **Проблема:** Очень медленно!
- **Кредиты:** $0.10 покрывает ~1000 запросов (зависит от модели)
- **Вердикт:** ❌ Не подходит для production

#### **PRO Account** ($9/месяц):
- Rate limit: **500 запросов/час**
- 100 слайдов = **30 минут** обработки
- **Кредиты:** $2.00/месяц
- **Стоимость сверх кредитов:** ~$0.01-0.05 за запрос (зависит от модели)
- **Вердикт:** ⚠️ Лучше, но дорого

---

## 📊 Сравнение: HF vs OpenRouter

### **100 слайдов (Intelligent Pipeline)**

| Провайдер | Модель | Стоимость | Rate Limit | Setup |
|-----------|--------|-----------|------------|-------|
| **HF Free** | Phi-3-vision | ~$2.50 | 50/час (5ч) | HF token |
| **HF PRO** | LLaVA-v1.6 | ~$3.00 + $9 | 500/час (30м) | $9/мес |
| **OpenRouter** | GLM-4.1v | **$1.40** | Unlimited | $10 пополнение |
| **OpenRouter** | Llama-3.2-11b | **$1.42** | Unlimited | $10 пополнение |
| **OpenRouter** | gpt-4o-mini | $5.23 | Unlimited | $10 пополнение |

**Вывод:** OpenRouter дешевле и быстрее для production!

---

## 🎯 Когда использовать HF API

### ✅ **Хорошие случаи:**

1. **Экспериментирование** (Free tier)
   - Тестирование разных моделей
   - Proof of concept
   - Небольшие объемы (<10 слайдов)

2. **Доступ к эксклюзивным моделям**
   - Модели доступные только на HF
   - Новые экспериментальные модели
   - Специализированные fine-tuned модели

3. **Privacy-first подход**
   - Можно развернуть Inference Endpoints (private)
   - Контроль над данными
   - GDPR compliance

### ❌ **Плохие случаи:**

1. **Production с высокой нагрузкой**
   - Rate limits ограничивают скорость
   - Дороже чем OpenRouter
   - Меньше контроля

2. **Batch processing**
   - 50/500 запросов/час слишком медленно
   - OpenRouter нет лимитов

3. **Budget-sensitive проекты**
   - HF PRO = $9/мес + per-request costs
   - OpenRouter = $10 одноразово, хватит на 700 слайдов

---

## 🚀 Как интегрировать HF в ваш проект

### **Шаг 1: Получить HF Token**
```bash
# 1. Регистрация на https://huggingface.co
# 2. Settings → Access Tokens → Create New Token
# 3. Выбрать "Read" права
```

### **Шаг 2: Установить библиотеку**
```bash
pip install huggingface-hub
```

### **Шаг 3: Код для замены OpenRouter**

```python
# backend/app/services/semantic_analyzer_hf.py

from huggingface_hub import InferenceClient
import os
import base64

class SemanticAnalyzerHF:
    def __init__(self):
        self.client = InferenceClient(
            token=os.getenv("HF_TOKEN")
        )
        self.model = os.getenv("HF_MODEL", "microsoft/Phi-3-vision-128k-instruct")
    
    async def analyze_slide(self, slide_image_path, ocr_elements, context):
        # Кодируем изображение
        with open(slide_image_path, "rb") as f:
            image_data = f.read()
        
        # Создаем промпт
        prompt = self._create_prompt(ocr_elements, context)
        
        # Вызываем HF API
        try:
            response = self.client.visual_question_answering(
                image=image_data,
                question=prompt
            )
            
            # Парсим ответ
            semantic_map = self._parse_response(response)
            return semantic_map
            
        except Exception as e:
            logger.error(f"HF API error: {e}")
            return self._mock_response()
```

### **Шаг 4: Конфигурация**
```env
# .env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
HF_MODEL=microsoft/Phi-3-vision-128k-instruct
LLM_PROVIDER=huggingface
```

---

## 📈 Рекомендуемые модели по категориям

### **Best Overall: Phi-3-Vision-128k**
```
✅ 128k контекст (огромный)
✅ Компактная (4.2B)
✅ Microsoft quality
✅ Отлично для документов
✅ Fast inference

Использовать когда:
- Сложные слайды с большим текстом
- Нужен большой контекст
- Важна скорость
```

### **Best Quality: LLaVA-v1.6-Mistral**
```
✅ 7B параметров
✅ Топ бенчмарки
✅ Mistral backbone
✅ Excellent vision

Использовать когда:
- Нужно лучшее качество
- Сложные visual понимание
- Презентации с графиками
```

### **Best Speed: Moondream2**
```
✅ Очень быстрая (1.8B)
✅ Низкое потребление
✅ Good enough качество

Использовать когда:
- Простые слайды
- Нужна скорость
- Ограниченный бюджет
```

### **Best for Asian Languages: Qwen2-VL**
```
✅ Multilingual (включая китайский/японский)
✅ State-of-the-art results
✅ Alibaba Cloud backing

Использовать когда:
- Non-English презентации
- Asian characters
- Нужна универсальность
```

---

## 💰 Итоговое сравнение стоимости

### **Сценарий: 1000 слайдов/месяц**

| Провайдер | Модель | Месячная стоимость | Примечание |
|-----------|--------|-------------------|------------|
| **HF Free** | Любая | ~$25 + TIME | 50/час = 50 часов! |
| **HF PRO** | Phi-3 | ~$30 + $9 | 500/час = 5 часов |
| **OpenRouter** | **GLM-4.1v** | **$14** | Нет ограничений ⭐ |
| **OpenRouter** | Llama-3.2 | $14.20 | Нет ограничений |
| **OpenRouter** | gpt-4o-mini | $52 | Лучшее качество |

**Вывод: OpenRouter выгоднее для production!**

---

## 🎯 **Финальная рекомендация**

### **Для вашего проекта:**

#### **Production use: OpenRouter** 🏆
```
Модель: thudm/glm-4.1v-9b-thinking
Стоимость: $1.40 за 100 слайдов
Плюсы:
✅ Дешевле всего
✅ Нет rate limits
✅ Отличное качество
✅ Vision support
✅ Простая интеграция (уже настроено)
```

#### **Экспериментирование: HF Free**
```
Модель: microsoft/Phi-3-vision-128k-instruct
Стоимость: Бесплатно (до лимита)
Плюсы:
✅ Бесплатно для тестов
✅ Доступ к разным моделям
✅ Хорошо для PoC

Минусы:
❌ 50 запросов/час (медленно)
❌ Ограниченные кредиты
```

#### **Privacy & Control: HF Inference Endpoints**
```
Dedicated endpoints (от $0.60/час)
Плюсы:
✅ Приватный inference
✅ Нет rate limits
✅ Полный контроль

Минусы:
❌ Дорого ($432/месяц при 24/7)
❌ Нужно управлять
```

---

## 🚀 Quick Start с HF API

### **Вариант 1: Тестирование (бесплатно)**
```bash
# 1. Получить токен на https://huggingface.co
# 2. Запустить тест
export HF_TOKEN="hf_xxxxx"
python test_huggingface_models.py
```

### **Вариант 2: Интеграция в проект**
```bash
# 1. Добавить в docker.env
echo "HF_TOKEN=hf_xxxxx" >> docker.env
echo "HF_MODEL=microsoft/Phi-3-vision-128k-instruct" >> docker.env

# 2. Модифицировать код (создать semantic_analyzer_hf.py)
# 3. Обновить provider_factory.py
```

---

## 📊 Summary

| Критерий | HF Free | HF PRO | OpenRouter |
|----------|---------|---------|------------|
| **Цена/100** | ~$2.50 | ~$12 | **$1.40** 🏆 |
| **Скорость** | Медленно | Средне | **Быстро** 🏆 |
| **Rate Limits** | 50/ч | 500/ч | **None** 🏆 |
| **Setup** | Простой | Простой | Простой |
| **Quality** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Models** | 200+ | 200+ | 300+ |

**Победитель: OpenRouter с GLM-4.1v-9b-thinking**

---

## 🎯 Мой вердикт

**НЕ переходите на HF API для production**

**Причины:**
1. ❌ Rate limits (50-500/час) vs OpenRouter (unlimited)
2. ❌ Дороже ($12+ vs $1.40 за 100 слайдов)
3. ❌ Медленнее (часы vs минуты)
4. ✅ OpenRouter уже работает с вашим ключом
5. ✅ GLM-4.1v дешевле И лучше

**HF API использовать для:**
- 🧪 Экспериментов с новыми моделями
- 📝 PoC и демо
- 🔒 Privacy-critical приложений (Inference Endpoints)

**Рекомендация: Оставайтесь на OpenRouter + GLM-4.1v!**
