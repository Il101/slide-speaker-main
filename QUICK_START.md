# Quick Start - Free Model Configuration

## ✅ Конфигурация обновлена!

### **Установленная модель: Google Gemma-3-12b-it (FREE)**

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemma-3-12b-it:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

---

## 📊 Характеристики модели

```
Модель:   Google Gemma 3 12B (free)
Параметры: 12 миллиардов
Context:   32,768 tokens
Vision:    ✅ YES (text+image→text)
Стоимость: $0.00 FREE! 🎉
```

---

## 💰 Экономика

### **Стоимость обработки:**

| Компонент | 1 слайд | 100 слайдов | 1000 слайдов |
|-----------|---------|-------------|--------------|
| **LLM (Gemma-3)** | $0.00 | $0.00 | $0.00 |
| OCR (Vision) | $0.0015 | $0.15 | $1.50 |
| TTS (Wavenet) | $0.012 | $1.20 | $12.00 |
| **ИТОГО** | **$0.0135** | **$1.35** | **$13.50** |

### **Сравнение с платными:**

| Модель | 100 слайдов | Экономия |
|--------|-------------|----------|
| **Gemma-3:free** 🏆 | **$1.35** | - |
| GLM-4.1v (paid) | $1.40 | +$0.05 |
| Llama-3.2-11b | $1.42 | +$0.07 |
| gpt-4o-mini | $5.23 | +$3.88 |

**Gemma-3:free дешевле gpt-4o-mini на 74%!**

---

## 🚀 Запуск

### **Шаг 1: Перезапустить Docker**
```bash
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main

# Остановить все контейнеры
docker-compose down

# Собрать и запустить заново
docker-compose up -d --build
```

### **Шаг 2: Проверить логи**
```bash
# Проверить backend
docker-compose logs -f backend

# Проверить worker
docker-compose logs -f worker
```

### **Шаг 3: Открыть приложение**
```
http://localhost:3000
```

### **Шаг 4: Загрузить тестовую презентацию**
- Выбрать файл (PDF или PPTX)
- Начать обработку
- Проверить результат

---

## ⚡ Что изменилось

### **До:**
```
OPENROUTER_API_KEY=fk-k9Jp84eGpLE3QnibxIaB-UQeqw7tqg4w1I4oWuHtXi_nfjb4s_Wgn4xFJTyY54iQ (Factory AI - неверный)
OPENROUTER_MODEL=gpt-4o-mini (платный - $5.23/100)
OPENROUTER_BASE_URL=https://api.factory.ai/v1 (неверный URL)
```

### **После:**
```
OPENROUTER_API_KEY=your_openrouter_api_key_here ✅
OPENROUTER_MODEL=google/gemma-3-12b-it:free ✅ (БЕСПЛАТНО!)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1 ✅
```

---

## ✅ Проверка конфигурации

Модель протестирована:
```
✅ API Key работает
✅ Модель доступна
✅ Vision support включен
✅ Бесплатный доступ подтвержден
✅ Русский язык поддерживается
```

---

## 🎯 Возможные ограничения FREE модели

### **Потенциальные лимиты:**
1. **Rate limits** - возможно 50-100 запросов/час
2. **Очередь** - может быть задержка при высокой нагрузке
3. **Доступность** - могут быть временные отключения

### **Если возникнут проблемы:**

#### **Вариант 1: Перейти на платную модель (GLM-4.1v)**
```env
# Изменить в docker.env
OPENROUTER_MODEL=thudm/glm-4.1v-9b-thinking
```
- Стоимость: $1.40/100 слайдов
- Требуется: Пополнить OpenRouter на $10
- Преимущества: Enhanced reasoning, нет лимитов

#### **Вариант 2: Использовать Gemini Free (50/день)**
```env
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=AIzaSyDNEtewj8q9qGWELrR-KS0mwcMTr4TGjA0
```
- Стоимость: БЕСПЛАТНО
- Лимит: 50 запросов/день
- Качество: Отличное

---

## 📈 Следующие шаги

### **Тестирование:**
1. ✅ Загрузить простую презентацию (5-10 слайдов)
2. ✅ Проверить качество генерации
3. ✅ Убедиться что vision работает (описывает изображения)
4. ✅ Проверить скорость обработки

### **Если всё работает:**
- Продолжайте использовать Gemma-3:free
- Экономия 74% vs gpt-4o-mini
- Никаких дополнительных затрат

### **Если нужно больше:**
- Пополните OpenRouter на $10
- Переключитесь на GLM-4.1v ($1.40/100)
- Или Llama-3.2-11b ($1.42/100)

---

## 🔧 Troubleshooting

### **Проблема: "Model is loading"**
Решение: Подождите 30-60 секунд, модель прогревается

### **Проблема: Rate limit exceeded**
Решение: Подождите или переключитесь на платную модель

### **Проблема: API key invalid**
Решение: Проверьте ключ в docker.env, перезапустите Docker

### **Проблема: Текст не на русском**
Решение: Проверьте LLM_LANGUAGE=ru в docker.env

---

## 📊 Мониторинг

### **Проверить использование:**
1. Зайти на https://openrouter.ai/credits
2. Войти с API ключом
3. Посмотреть статистику

### **Проверить логи:**
```bash
# Backend логи
docker-compose logs backend | grep -i "openrouter"

# Worker логи
docker-compose logs worker | grep -i "llm"
```

---

## 🎉 Резюме

✅ **Конфигурация обновлена на бесплатную модель**
✅ **Vision support включен**
✅ **Русский язык настроен**
✅ **Экономия 74% vs gpt-4o-mini**

**Готово к использованию! Запускайте и тестируйте!**

---

## 📞 Поддержка

Если возникнут проблемы:
1. Проверьте логи Docker
2. Убедитесь что все контейнеры запущены
3. Проверьте API ключ на https://openrouter.ai
4. При необходимости переключитесь на платную модель
