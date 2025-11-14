# 📋 Implementation Guide - Обновление системы с новыми ценами

## 📁 Файлы для изменения

### 1. Backend: `backend/app/core/subscriptions.py`

Нужно обновить константы SubscriptionPlan с новыми ценами и лимитами.

**Текущее состояние:**
```python
# Lines 23-88
class SubscriptionPlan:
    FREE = {
        "name": "Free",
        "presentations_per_month": 3,  # ✅ OK
        "max_slides": 10,  # ✅ OK
        "max_file_size_mb": 10,  # ✅ OK
        "ai_quality": "basic",  # ✅ OK
        # ... остальные поля
    }
    
    PRO = {
        "name": "Professional",
        "price_monthly": 29.99,  # ❌ НУЖНО ИЗМЕНИТЬ НА 9.99
        "presentations_per_month": 50,  # ❌ НУЖНО ИЗМЕНИТЬ НА 30
        # ... остальные поля
    }
    
    ENTERPRISE = {
        "name": "Enterprise",
        "price_monthly": 99.99,  # ✅ можно оставить или сделать custom
        # ...
    }
```

**Новые значения:**
```python
FREE = {
    "name": "Free",
    "price_monthly": 0,
    "price_yearly": 0,
    "presentations_per_month": 3,
    "max_slides": 10,
    "max_file_size_mb": 10,
    "ai_quality": "basic",
    "export_formats": ["mp4"],
    "priority": "low",
    "custom_voices": False,
    "api_access": False,
    "concurrent_processing": 1,
    "api_calls_per_day": 100,
    "features": [
        "3 presentations per month",
        "Up to 10 slides per presentation",
        "Basic AI quality",
        "MP4 export only"
    ]
}

PRO = {
    "name": "Professional",
    "price_monthly": 9.99,
    "price_yearly": 99.99,
    "presentations_per_month": 30,
    "max_slides": 100,
    "max_file_size_mb": 100,
    "ai_quality": "premium",
    "export_formats": ["mp4", "webm", "gif"],
    "priority": "high",
    "custom_voices": True,
    "api_access": False,
    "concurrent_processing": 3,
    "api_calls_per_day": 1000,
    "features": [
        "30 presentations per month",
        "Up to 100 slides per presentation",
        "Premium AI quality",
        "Multiple export formats",
        "High priority processing",
        "Custom voice selection"
    ]
}

BUSINESS = {
    "name": "Business",
    "price_monthly": 24.99,
    "price_yearly": 249.99,
    "presentations_per_month": 100,
    "max_slides": 500,
    "max_file_size_mb": 300,
    "ai_quality": "premium",
    "export_formats": ["mp4", "webm", "gif", "pptx"],
    "priority": "critical",
    "custom_voices": True,
    "api_access": True,
    "concurrent_processing": 5,
    "api_calls_per_day": 5000,
    "features": [
        "100 presentations per month",
        "Up to 500 slides per presentation",
        "Premium AI quality",
        "All export formats",
        "Critical priority processing",
        "Custom voices",
        "API access",
        "Team collaboration (up to 5 users)",
        "Email + Chat support"
    ]
}

ENTERPRISE = {
    "name": "Enterprise",
    "price_monthly": None,  # Custom pricing
    "price_yearly": None,  # Custom pricing
    "presentations_per_month": -1,  # Unlimited
    "max_slides": -1,  # Unlimited
    "max_file_size_mb": -1,  # Unlimited
    "ai_quality": "premium+",
    "export_formats": ["all"],
    "priority": "critical",
    "custom_voices": True,
    "api_access": True,
    "sso": True,
    "concurrent_processing": -1,  # Unlimited
    "api_calls_per_day": -1,  # Unlimited
    "features": [
        "Unlimited presentations",
        "Premium support",
        "Dedicated account manager",
        "Custom SLA",
        "Single sign-on (SSO/SAML)",
        "Advanced analytics",
        "Team management",
        "Custom integration"
    ]
}
```

### 2. Frontend: `src/components/SubscriptionManager.tsx`

**Текущее:** Использует фиксированные планы  
**Изменить:** Отобразить правильные цены из бэкенда

```typescript
// Lines 19-31
interface SubscriptionPlan {
  name: string;
  presentations_per_month: number;
  max_slides: number;
  max_file_size_mb: number;
  ai_quality: string;
  export_formats: string[];
  priority: string;
  custom_voices: boolean;
  api_access: boolean;
  features: string[];
  price_monthly?: number;  // ✅ Уже есть
  price_yearly?: number;   // ❌ ДОБАВИТЬ
  concurrent_processing?: number;  // ❌ ДОБАВИТЬ
  api_calls_per_day?: number;  # ❌ ДОБАВИТЬ
}
```

### 3. Stripe Setup

**Новые Product IDs в Stripe:**

```
Free Plan:
  - SKU: free-monthly
  - Price: $0
  - Recurring: Monthly (но платеж не требуется)
  - Setup: Simple data tracking

Pro Plan Monthly:
  - SKU: pro-monthly
  - Price: $9.99
  - Recurring: Monthly
  - Trial: 7 days

Pro Plan Yearly:
  - SKU: pro-yearly
  - Price: $99.99
  - Recurring: Yearly (discount 17%)

Business Plan Monthly:
  - SKU: business-monthly
  - Price: $24.99
  - Recurring: Monthly

Business Plan Yearly:
  - SKU: business-yearly
  - Price: $249.99
  - Recurring: Yearly (discount 17%)

Enterprise:
  - Custom quote via sales
  - No automatic billing
```

### 4. Analytics Update

**Добавить отслеживание в Analytics:**

```python
# backend/app/api/analytics.py

analytics_data = {
    "costs": {
        "total": 0,
        "perUser": 0,
        "perLecture": 0,
        "margin": 0,
        "breakdown": {
            "ocr": 0.0225,
            "ai": 0.030023,
            "tts": 0.1152,  # или $0.0252 если Gemini
            "storage": 0,
            "other": 0
        }
    },
    "revenue": {
        "monthly": 0,
        "perPlan": {
            "free": 0,
            "pro": user_count_pro * 9.99,
            "business": user_count_business * 24.99,
            "enterprise": custom_amount
        }
    },
    "profitability": {
        "margin_percentage": 0,
        "cac_payback_months": 0,
        "ltv_ratio": 0
    }
}
```

---

## 🔄 MIGRATION STEPS

### Step 1: Backup Current Data
```bash
# Backup database
mysqldump slide_speaker_db > backup_$(date +%Y%m%d).sql

# Backup code
git commit -am "Backup before pricing update"
git tag pricing-v1
```

### Step 2: Update Backend (File: backend/app/core/subscriptions.py)
```python
# Simply replace the SubscriptionPlan class with new values
# No database migration needed - uses new constants
```

### Step 3: Update Frontend (File: src/components/SubscriptionManager.tsx)
```typescript
// Update pricing display
// Update feature lists
// Add annual vs monthly toggle
```

### Step 4: Update Stripe
```bash
# In Stripe dashboard:
# 1. Create new products for each plan
# 2. Set correct prices
# 3. Add trial periods (7 days for Pro)
# 4. Update subscription link URLs
```

### Step 5: Test in Staging
```bash
# Test checkout flow
# Test limit enforcement
# Test analytics reporting
# Test Free user upgrade path
```

### Step 6: Deploy to Production
```bash
# Deploy backend with new subscriptions.py
# Deploy frontend with updated UI
# Update Stripe webhook handlers
# Monitor adoption rate
```

---

## 📊 VERIFICATION CHECKLIST

- [ ] Free plan shows correctly in UI
- [ ] Pro plan shows $9.99/month in UI
- [ ] Business plan shows $24.99/month in UI
- [ ] Enterprise shows "Contact Sales"
- [ ] Price yearly shows 17% discount
- [ ] Stripe trial 7 days for Pro works
- [ ] Upgrade flow works without errors
- [ ] Free users see "Upgrade to Pro" CTA
- [ ] Usage limits are enforced:
  - [ ] Free: 3 presentations limit
  - [ ] Pro: 30 presentations limit
  - [ ] Business: 100 presentations limit
- [ ] Export formats available per plan
- [ ] API access restricted correctly
- [ ] Analytics shows correct costs

---

## 🚨 ROLLBACK PLAN

If issues occur:

```bash
# 1. Revert code
git checkout pricing-v1  # Go back to previous tag

# 2. Restore database if needed
mysql slide_speaker_db < backup_20251112.sql

# 3. Restart services
docker-compose restart
```

---

## 📈 POST-LAUNCH MONITORING

### First Week:
- [ ] Monitor conversion Free → Pro (target: 25%)
- [ ] Check error rates in subscription API (target: <0.1%)
- [ ] Verify payment processing (0 failed transactions)
- [ ] Monitor support tickets (expect 5-10 about pricing)

### First Month:
- [ ] Calculate actual revenue
- [ ] Analyze plan distribution (60/30/10 target?)
- [ ] Identify top churn causes
- [ ] Prepare promotional offers if needed

### Ongoing:
- [ ] Monthly revenue reporting
- [ ] CAC vs LTV analysis
- [ ] A/B test pricing if conversion <15%
- [ ] Quarterly price review

---

## 📞 QUESTIONS & ANSWERS

**Q: Do we need database migration?**  
A: No! The new prices are in code constants, not in DB.

**Q: How to handle existing Pro users at old price?**  
A: Grandfather them - keep their old $29.99 price, new signups get $9.99.

**Q: What about Free trial users?**  
A: After trial expires, they become Free tier (3/month).

**Q: Can users downgrade?**  
A: Yes, downgrade is allowed anytime (no refunds).

**Q: Do we need to notify users?**  
A: Yes, email all Free users about new $9.99 Pro plan with limited-time offer (save 20% first month).

---

**Prepared:** November 12, 2025  
**Version:** 1.0  
**Status:** Ready for implementation
