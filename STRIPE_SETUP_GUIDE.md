# 💳 Stripe Setup Guide

Краткая инструкция по настройке Stripe для приема платежей.

---

## 📋 Что Нужно

1. Аккаунт Stripe (бесплатная регистрация)
2. 10-15 минут времени
3. Доступ к backend `.env` файлу

---

## 🚀 Шаги Настройки

### 1. Регистрация в Stripe

1. Перейти на https://stripe.com
2. Нажать "Sign up"
3. Заполнить данные (email, пароль)
4. Подтвердить email

---

### 2. Получить API Keys

1. Войти в Dashboard: https://dashboard.stripe.com
2. Перейти в раздел **Developers** → **API keys**
3. Скопировать:
   - **Secret key** (начинается с `sk_test_...` для тестового режима)
   - **Publishable key** (начинается с `pk_test_...`)

**Важно:** 
- `sk_test_...` - для разработки/тестирования
- `sk_live_...` - для продакшена (после активации аккаунта)

---

### 3. Создать Products и Prices

#### Создать PRO Plan

1. Перейти в **Products** → **Add product**
2. Заполнить:
   - **Name:** Professional Plan
   - **Description:** 50 presentations per month, up to 100 slides
   - **Pricing model:** Recurring
   - **Price:** $29.99
   - **Billing period:** Monthly
3. Нажать **Save product**
4. **Скопировать Price ID** (начинается с `price_...`)

#### Создать Enterprise Plan

1. Повторить шаги выше
2. Заполнить:
   - **Name:** Enterprise Plan
   - **Description:** Unlimited presentations, up to 500 slides
   - **Price:** $99.99
   - **Billing period:** Monthly
3. **Скопировать Price ID**

---

### 4. Настроить Webhook

1. Перейти в **Developers** → **Webhooks**
2. Нажать **Add endpoint**
3. Заполнить:
   - **Endpoint URL:** `https://your-domain.com/api/subscription/webhook/stripe`
   - Для локального тестирования: используйте ngrok (см. ниже)
4. Select events to listen to:
   - ✅ `checkout.session.completed`
   - ✅ `customer.subscription.created`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
5. Нажать **Add endpoint**
6. **Скопировать Signing secret** (начинается с `whsec_...`)

---

### 5. Обновить Backend .env

Добавить в `backend/.env`:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# Frontend URL for redirect after payment
FRONTEND_URL=http://localhost:5173
```

---

### 6. Обновить Price IDs в Коде

Открыть `backend/app/api/subscriptions.py` и заменить:

```python
price_map = {
    "pro": "price_1234567890",        # ← Вставить свой Price ID для PRO
    "enterprise": "price_0987654321"  # ← Вставить свой Price ID для Enterprise
}
```

---

### 7. Установить Stripe Library

```bash
cd backend
pip install stripe==7.0.0
```

Или пересобрать Docker:
```bash
docker-compose build backend
docker-compose up -d
```

---

### 8. Перезапустить Backend

```bash
# Если локально
cd backend
uvicorn app.main:app --reload

# Если Docker
docker-compose restart backend
```

---

## 🧪 Тестирование

### Локальное тестирование с ngrok

Для тестирования webhooks локально используйте ngrok:

```bash
# Установить ngrok
brew install ngrok  # MacOS
# или скачать с https://ngrok.com

# Запустить туннель
ngrok http 8000

# Скопировать URL (например: https://abc123.ngrok.io)
# Использовать его в Stripe webhook URL:
# https://abc123.ngrok.io/api/subscription/webhook/stripe
```

### Тестовые карты Stripe

Для тестирования используйте:

- **Успешная оплата:**
  - Card: `4242 4242 4242 4242`
  - Expiry: любая будущая дата (например, `12/34`)
  - CVC: любые 3 цифры (например, `123`)

- **Отклоненная оплата:**
  - Card: `4000 0000 0000 0002`

Полный список: https://stripe.com/docs/testing

### Проверка интеграции

1. **Проверить, что Stripe инициализировался:**
```bash
curl http://localhost:8000/health

# В логах должно быть:
# "Stripe integration enabled"
```

2. **Создать checkout session:**
```bash
curl -X POST http://localhost:8000/api/subscription/create-checkout \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier": "pro"}'

# Ответ:
# {
#   "session_id": "cs_test_...",
#   "session_url": "https://checkout.stripe.com/..."
# }
```

3. **Открыть session_url в браузере**
4. **Ввести тестовую карту**
5. **Завершить оплату**
6. **Проверить webhook:**
```bash
# В логах backend должно появиться:
# "Received Stripe webhook: checkout.session.completed"
# "User {user_id} subscription updated to pro via webhook"
```

7. **Проверить, что tier обновился:**
```bash
curl http://localhost:8000/api/subscription/info \
  -H "Authorization: Bearer YOUR_TOKEN"

# Ответ:
# {
#   "tier": "pro"  ← Должен быть "pro"!
# }
```

---

## 🔒 Production Deployment

### 1. Активировать Stripe аккаунт

1. Перейти в **Settings** → **Activate your account**
2. Заполнить бизнес-информацию
3. Дождаться одобрения (обычно мгновенно)

### 2. Получить Production Keys

1. Переключиться с "Test mode" на "Live mode" в Dashboard
2. Скопировать новые ключи:
   - `sk_live_...`
   - `pk_live_...`
   - `whsec_...` (для production webhook)

### 3. Обновить Production .env

```env
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_LIVE_WEBHOOK_SECRET_HERE
FRONTEND_URL=https://your-production-domain.com
```

### 4. Настроить Production Webhook

1. Создать новый webhook endpoint в Live mode
2. URL: `https://your-production-domain.com/api/subscription/webhook/stripe`
3. Скопировать новый signing secret

---

## 💡 Полезные Ссылки

- **Stripe Dashboard:** https://dashboard.stripe.com
- **API Keys:** https://dashboard.stripe.com/apikeys
- **Webhooks:** https://dashboard.stripe.com/webhooks
- **Test Cards:** https://stripe.com/docs/testing
- **Documentation:** https://stripe.com/docs/api
- **Webhook Events:** https://stripe.com/docs/api/events/types

---

## ❓ FAQ

### Q: Можно ли использовать без Stripe?

**A:** Да! Система работает в demo mode. Кнопка "Обновить" показывает confirm() и обновляет tier напрямую. Но для приема реальных платежей нужен Stripe.

### Q: Сколько стоит Stripe?

**A:** 
- Регистрация бесплатна
- Комиссия за транзакцию: 2.9% + $0.30 (США)
- Комиссия варьируется по странам: https://stripe.com/pricing

### Q: Какие страны поддерживаются?

**A:** Stripe работает в 46+ странах. Полный список: https://stripe.com/global

### Q: Нужно ли верифицировать аккаунт для тестирования?

**A:** Нет, test mode работает сразу после регистрации без верификации.

### Q: Как отменить подписку пользователя?

**A:** В Stripe Dashboard → Customers → найти пользователя → Cancel subscription. Webhook автоматически обновит tier в вашей БД.

---

## 🐛 Troubleshooting

### Ошибка: "Stripe not configured"

**Решение:** 
1. Проверить, что `STRIPE_SECRET_KEY` в `.env`
2. Перезапустить backend
3. Проверить логи: должно быть "Stripe integration enabled"

### Ошибка: "Invalid signature" в webhook

**Решение:**
1. Проверить, что `STRIPE_WEBHOOK_SECRET` правильный
2. Убедиться, что используется secret от правильного webhook endpoint
3. Проверить, что webhook URL доступен (не localhost без ngrok)

### Checkout session создается, но ничего не происходит после оплаты

**Решение:**
1. Проверить, что webhook endpoint доступен
2. Проверить логи backend на наличие webhook событий
3. Проверить в Stripe Dashboard → Webhooks → ваш endpoint → Recent events

### Price ID не работает

**Решение:**
1. Убедиться, что используете правильный Price ID (не Product ID)
2. Проверить, что Price ID соответствует режиму (test/live)
3. Проверить, что Price существует в Stripe Dashboard

---

**Дата:** 2025-01-15  
**Версия:** 1.0
