# 🚀 QUICK PRICING SUMMARY (Быстрая справка)

---

## 💰 СТОИМОСТЬ ОДНОЙ ПРЕЗЕНТАЦИИ

**Базовая презентация:** 15 слайдов, 10 минут аудио, ~7,200 символов

### Полная стоимость обработки (ТЕКУЩАЯ):

```
┌─────────────────────────────────────────────┐
│  AI Analysis (Stages 0-3): $0.060           │
│  OCR (Document AI):         $0.0225         │
│  TTS (Gemini Flash 2.5):    $0.1509         │
│  Visual Effects (local):    $0              │
│  ────────────────────────────────────────   │
│  ИТОГО:                     $0.2334         │
│  ≈ 23 цента                 ($0.23)        │
└─────────────────────────────────────────────┘
```

**Используется:** Gemini 2.5 Flash TTS ($10/1M audio tokens)  
⚠️ **Проблема:** НЕТ word-level timepoints (нужен для точного VFX)

### С ОПТИМИЗАЦИЯМИ (Flash-Lite + Batch):

```
┌─────────────────────────────────────────────┐
│  AI Analysis (Flash-Lite):  $0.0112         │
│  OCR (с кэшем ~50%):        $0.0113         │
│  TTS (Gemini Flash 2.5):    $0.1509         │
│  Visual Effects (local):    $0              │
│  ────────────────────────────────────────   │
│  ИТОГО:                     $0.1734         │
│  ≈ 18 центов                ($0.18)        │
└─────────────────────────────────────────────┘
```

**Экономия:** 22% ($0.23 → $0.18)

---

## 🎯 РЕКОМЕНДУЕМЫЕ ЦЕНЫ

### СЦЕНАРИЙ 1: Без оптимизаций (себестоимость $0.23)

```
FREE        →  $0/месяц      (3 презентации)
PRO         →  $12.99/месяц  (30 презентаций) +30% к текущей
BUSINESS    →  $34.99/месяц  (80 презентаций) +40% к текущей
ENTERPRISE  →  Custom pricing
```

**Margin Analysis:**
```
PRO:      $12.99 - (30 × $0.23) = $6.09 (47% маржа) ✅
BUSINESS: $34.99 - (80 × $0.23) = $16.59 (47% маржа) ✅
```

### СЦЕНАРИЙ 2: С оптимизациями (себестоимость $0.18) 🏆

```
FREE        →  $0/месяц      (3 презентации)
PRO         →  $12.99/месяц  (30 презентаций)
BUSINESS    →  $34.99/месяц  (100 презентаций)
ENTERPRISE  →  Custom pricing
```

**Margin Analysis:**
```
PRO:      $12.99 - (30 × $0.18) = $7.59 (58% маржа) ✅✅
BUSINESS: $34.99 - (100 × $0.18) = $16.99 (49% маржа) ✅✅
```

---



## 📈 REVENUE PROJECTIONS

### При 1,000 активных пользователей/месяц:

```
Distribution: 60% Free, 30% Pro, 10% Business
Presentations: 20,800 total

Revenue:
- Pro: 300 × $9.99 = $2,997
- Biz: 100 × $24.99 = $2,499
- TOTAL: $5,496/month

Cost (TTS): 20,800 × $0.15 = $3,120
Gross Profit: $5,496 - $3,120 = $2,376/month ✅
Margin: 43%
```

### Scaling to 10,000 users:

```
Revenue: $54,960/month
Cost: $31,200/month
Profit: $23,760/month 🚀
Margin: 43% (stays same, scales!)
```

---

## ⚡ KEY INSIGHTS

1. **Cost per presentation is FIXED:** $0.15 regardless of plan
2. **Pro is the "sweet spot":** Best conversion rate (~25-30%)
3. **Business has best margin:** Only 10% of users but 20% of revenue
4. **Free is marketing:** No revenue but gets users to try
5. **Enterprise is goldmine:** 1 customer = 50 Free users value!

---

## 🎯 NEXT STEPS

1. ✅ Approve pricing: Free / $9.99 / $24.99 / Custom
2. ✅ Set up Stripe with new plans
3. ✅ Update limiter in backend/app/core/subscriptions.py
4. ✅ Update UI in src/components/SubscriptionManager.tsx
5. ✅ Launch "Pro Trial" campaign to Free users
6. ✅ Monitor conversion rates daily for first month

---

## 📞 CONTACTS & DOCS

Full analysis: `PRICING_STRATEGY_2025.md`  
Detailed price list: `PRICE_LIST_2025.md`  
Cost breakdown: `PIPELINE_COST_ANALYSIS.md`

---

**Last Updated:** November 12, 2025  
**Status:** ✅ Ready for Implementation
