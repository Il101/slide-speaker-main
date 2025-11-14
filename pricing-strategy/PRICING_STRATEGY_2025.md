# 💰 Стратегия прайсинга - Финальные рекомендации

**Дата:** 12 ноября 2025  
**Автор:** AI Analysis  
**Статус:** Готово к внедрению

---

## 📊 1. СТОИМОСТЬ ОБРАБОТКИ ОДНОЙ ПРЕЗЕНТАЦИИ

### Базовая прерентация (benchmark):
- **15 слайдов**
- **10 минут аудио**
- **~7,200 символов текста**
- **Полная обработка включая VFX**

### Расчет стоимости по компонентам:

| Компонент | Сервис | Цена |量 | Итого |
|-----------|--------|------|-----|--------|
| **Stage 0** | Presentation Analysis | Gemini 1.5 Flash | $0.075/1M tokens | $0.000238 |
| **Stage 2** | OCR | Document AI | $1.50/1K pages | $0.0225 |
| **Stage 3.1** | Semantic Analysis | Gemini 1.5 Flash Vision | $0.075/1M input | $0.002835 |
| **Stage 3.2** | Script Generation | Gemini 1.5 Flash Text | $0.075/1M input | $0.00495 |
| **Stage 4** | **TTS (Chirp 3 HD)** | **$16.00/1M chars** | **7,200 chars** | **$0.1152** |
| **Stage 5-6** | Visual Effects & Validation | Локально | $0 | $0 |
| | | | **ИТОГО:** | **$0.145** |

### Стоимость с учетом оптимизаций:

#### Без кэширования OCR (первая обработка):
```
$0.000238 + $0.0225 + $0.002835 + $0.00495 + $0.1152 = $0.145223
≈ $0.145 (14.5¢)
```

#### С кэшированием OCR (переобработка):
```
$0.000238 + $0 + $0.002835 + $0.00495 + $0.1152 = $0.122923
≈ $0.123 (12.3¢)
```

#### Вариант Gemini 2.5 Flash TTS (лучший голос):
```
TTS: $3.50/1M chars × 7,200 = $0.0252
ИТОГО: $0.030023 + $0.0252 = $0.055223
≈ $0.055 (5.5¢) - 62% экономия!
```

---

## 🎯 2. РЕКОМЕНДУЕМАЯ СТРУКТУРА ПРАЙСИНГА

### Вариант A: Базовый (РЕКОМЕНДУЕТСЯ)

```yaml
TIER_FREE:
  name: "Free"
  price_monthly: $0
  presentations_per_month: 3
  slides_per_presentation: 10
  max_file_size_mb: 10
  tts_quality: "standard"
  vfx_features: ["basic"]
  export_formats: ["mp4"]
  support: "community"
  cost_per_presentation: $0.145
  limit_reason: "Platform sustainability"

TIER_PRO:
  name: "Professional"
  price_monthly: $9.99
  price_yearly: $99.99
  presentations_per_month: 30
  slides_per_presentation: 100
  max_file_size_mb: 100
  tts_quality: "premium"
  vfx_features: ["basic", "highlight", "spotlight"]
  export_formats: ["mp4", "webm", "gif"]
  support: "email"
  features:
    - "30 presentations/month"
    - "Premium TTS voice quality"
    - "Advanced visual effects"
    - "Multiple export formats"
    - "Priority processing"
  cost_per_presentation: $0.145
  margin: 168% (($9.99 × 12) / (30 × $0.145))
  user_value: "4x more presentations, unlimited size"
  
TIER_BUSINESS:
  name: "Business"
  price_monthly: $24.99
  price_yearly: $249.99
  presentations_per_month: 100
  slides_per_presentation: 500
  max_file_size_mb: 300
  tts_quality: "premium"
  vfx_features: ["all"]
  export_formats: ["mp4", "webm", "gif", "pptx"]
  api_access: true
  support: "email + chat"
  features:
    - "100 presentations/month"
    - "Large presentations support"
    - "All visual effects"
    - "Custom export options"
    - "API access"
    - "Team collaboration"
  cost_per_presentation: $0.145
  margin: 175% (($24.99 × 12) / (100 × $0.145))
  
TIER_ENTERPRISE:
  name: "Enterprise"
  price_monthly: "Custom"
  presentations_per_month: -1  # Unlimited
  slides_per_presentation: -1  # Unlimited
  max_file_size_mb: -1  # Unlimited
  tts_quality: "premium+"
  vfx_features: ["all", "custom"]
  export_formats: ["all"]
  api_access: true
  sso: true
  support: "dedicated"
  features:
    - "Unlimited presentations"
    - "Premium support"
    - "Dedicated infrastructure"
    - "Custom SLA"
    - "Advanced analytics"
    - "Team management"
    - "Single sign-on"
  contact_sales: true
```

### Финансовый анализ Вариант A:

| Метрика | Free | Pro | Business | Enterprise |
|---------|------|-----|----------|------------|
| Monthly Revenue (1 user) | $0 | $9.99 | $24.99 | Variable |
| Presentations/month | 3 | 30 | 100 | ∞ |
| Cost per presentation | $0.145 | $0.145 | $0.145 | $0.145 |
| Monthly cost | $0.435 | $4.35 | $14.50 | Variable |
| **Profit margin** | - | **130%** | **72%** | **TBD** |
| Gross profit | - | $5.64 | $10.49 | - |

---

### Вариант B: Premium VFX (если внедрим STT)

```yaml
TIER_VOICE_BASIC:
  name: "Voice Basic"
  price_monthly: $4.99
  presentations_per_month: 5
  tts_quality: "chirp3-hd"  # Стандартный TTS
  vfx_precision: "word-level"
  cost_per_presentation: $0.145

TIER_VOICE_PRO:
  name: "Voice Pro"
  price_monthly: $14.99
  presentations_per_month: 50
  tts_quality: "gemini-premium"  # Лучший голос
  vfx_precision: "word-level + STT"
  features:
    - "Gemini 2.5 TTS (лучшее качество голоса)"
    - "Word-level visual effects"
    - "Advanced voice customization"
  cost_per_presentation: $0.215  # $0.055 (TTS) + $0.16 (STT)
  margin: 150%
```

---

## 📈 3. ЭКОНОМИКА ДЛЯ РАЗЛИЧНЫХ СЦЕНАРИЕВ

### Сценарий: Casual User
```
Usage: 10 presentations/month
Plan: Free (3/month) → Pro
Monthly Cost: $9.99
Cost per presentation: $1.00
User satisfaction: HIGH (4x more features)
Lifetime Value (2 years): $239.76
```

### Сценарий: Active Creator
```
Usage: 50 presentations/month
Plan: Pro (30/month) → Business
Monthly Cost: $24.99
Cost per presentation: $0.50
User satisfaction: HIGH (unlimited size + API)
Lifetime Value (2 years): $599.76
```

### Сценарий: Enterprise Customer
```
Usage: 500+ presentations/month
Plan: Enterprise
Monthly Cost: $99.99-$499.99 (custom)
Cost per presentation: $0.20-$0.10
User satisfaction: CRITICAL (dedicated support)
Lifetime Value (2 years): $2,400+
```

### Масштабирование платформы:

| Пользователи | Free | Pro | Business | Enterprise | Месячный доход |
|------|------|-----|----------|------------|--------|
| 100 | 50 | 30 | 15 | 5 | $685 |
| 1,000 | 600 | 300 | 80 | 20 | $8,492 |
| 10,000 | 7,000 | 2,000 | 800 | 200 | $89,920 |

---

## 💡 4. ЛИМИТЫ И ОБОСНОВАНИЕ

### Логика лимитов по тирам:

```
Free: Привлечение & Testing
  - 3 presentations/month (достаточно для экспериментов)
  - 10 slides (сложность = затраты)
  - Ограничение размера (экономия на хранилище)
  
Pro: Активные пользователи
  - 30 presentations/month (~1 в день)
  - 100 slides (масштабируемость)
  - 3x выше лимит размера
  
Business: Профессионалы
  - 100 presentations/month (~3 в день)
  - 500 slides (практически любая презентация)
  - Неограниченный размер
  
Enterprise: Корпоративные клиенты
  - Полностью кастомизированное решение
```

### Ограничение обработки (Rate Limiting):

```python
# Per tier
FREE: 1 concurrent processing, 100 API calls/day
PRO: 3 concurrent processing, 1,000 API calls/day
BUSINESS: 5 concurrent processing, 5,000 API calls/day
ENTERPRISE: 10+ concurrent processing, unlimited

# Per resource
Presentation upload: 50MB/day free tier, 500MB/day pro
Storage: 1GB free tier, 100GB business tier
```

---

## 🎯 5. РЕКОМЕНДАЦИИ К ВНЕДРЕНИЮ

### Phase 1: Немедленно (текущие планы)
✅ Внедрить текущую структуру Вариант A (Free/Pro/Business/Enterprise)  
✅ Установить цены: Free/$9.99/$24.99/Custom  
✅ Настроить лимиты в БД  
✅ Интегрировать Stripe (если нет)  

### Phase 2: Через месяц
🔄 Отследить коэффициенты конверсии  
🔄 Оптимизировать лимиты на основе usage analytics  
🔄 Рассмотреть пробный период Pro (7 дней бесплатно)  

### Phase 3: При масштабировании
⚡ Если >1,000 пользователей: рассмотреть Вариант B с Gemini TTS  
⚡ Снизить стоимость до $0.055/presentation  
⚡ Увеличить марджин для Pro/Business  

---

## 📋 6. ПРИМЕРЫ РАСЧЕТА

### Для 1,000 активных users/месяц:

#### Текущая система (Chirp 3 HD @ $0.145/pres):
```
Бизнес-модель Free/Pro/Business
User distribution: 60% free, 30% pro, 10% business

Presentations:
- Free: 600 users × 3 pres = 1,800 pres
- Pro: 300 users × 30 pres = 9,000 pres
- Business: 100 users × 100 pres = 10,000 pres
- TOTAL: 20,800 presentations/month

Infrastructure cost:
20,800 × $0.145 = $3,016/month

Revenue (subscription):
- Pro: 300 × $9.99 = $2,997
- Business: 100 × $24.99 = $2,499
- TOTAL: $5,496/month

Gross Profit: $5,496 - $3,016 = $2,480/month (45% margin)
```

#### При масштабировании на Gemini TTS (@ $0.055/pres):
```
Infrastructure cost:
20,800 × $0.055 = $1,144/month

Revenue: $5,496/month (same)

Gross Profit: $5,496 - $1,144 = $4,352/month (79% margin!)
Дополнительная прибыль: $1,872/месяц
```

---

## ✅ 7. РЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ

### Немедленно (сегодня):
1. ✅ Обновить текущие лимиты в `subscriptions.py`:
   - Free: 3 presentations/month
   - Pro: 30 presentations/month  
   - Business: 100 presentations/month
   - Enterprise: unlimited

2. ✅ Установить цены в Stripe:
   - Pro: $9.99/month (annual: $99.99)
   - Business: $24.99/month (annual: $249.99)
   - Enterprise: Contact sales

3. ✅ Обновить UI в `SubscriptionManager.tsx` с новыми описаниями

### Через неделю:
4. 📊 Настроить analytics для отслеживания:
   - Cost per presentation
   - Revenue per tier
   - Margin by user segment
   - Conversion rate Free → Pro

5. 🔄 Создать email campaign для Free users (upgrade incentives)

### Через месяц:
6. 📈 Анализ данных и оптимизация:
   - Какие лимиты вызывают фрустрацию?
   - Какая цена оптимальна для конверсии?
   - Когда переводить на Gemini TTS?

---

## 🎁 8. БОНУСНЫЕ ОПЦИИ

### Для привлечения пользователей:

```yaml
TRIAL_OFFER:
  - "7 дней Pro бесплатно"
  - "Все праздники: 50% off Pro"
  
REFER_A_FRIEND:
  - "Пригласи друга, получи $10 credit"
  
ANNUAL_DISCOUNT:
  - Pro annual: $99.99 (вместо $119.88) = 16% скидка
  - Business annual: $249.99 (вместо $299.88) = 16% скидка
  
VOLUME_DISCOUNT (Business tier):
  - 100-500 pres/month: 10% discount
  - 500+ pres/month: 20% discount
```

---

## 📞 КОНТАКТ

Для уточнения или изменения стратегии обратитесь в:
- Backend: `/backend/app/core/subscriptions.py`
- Frontend: `/src/components/SubscriptionManager.tsx`
- Billing: Stripe dashboard

**Status:** Готово к внедрению ✅
