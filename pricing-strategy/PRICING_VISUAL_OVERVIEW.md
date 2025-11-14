# 📊 PRICING STRATEGY - VISUAL OVERVIEW

---

## 1. COST BREAKDOWN (Разбор стоимости)

```
Одна презентация (15 слайдов, 10 минут, ~7,200 символов)
│
├─ Stage 0: Presentation Analysis
│  └─ Google Gemini 1.5 Flash (125 tokens × $0.075/1M)
│     └─ $0.000238 (negligible)
│
├─ Stage 1: Ingest
│  └─ Local processing (PDF/PPTX to PNG)
│     └─ $0 (free)
│
├─ Stage 2: OCR
│  └─ Google Document AI (15 pages × $1.50/1K)
│     └─ $0.0225 ⭐ (can be cached)
│
├─ Stage 3: AI Intelligence
│  ├─ 3.1 Semantic Analysis (15 slides × $0.000189)
│  │  └─ $0.002835
│  │
│  └─ 3.2 Script Generation (15 slides × $0.000330)
│     └─ $0.00495
│
├─ Stage 4: Text-to-Speech ⭐⭐ LARGEST COST
│  │
│  ├─ Option A: Chirp 3 HD (current)
│  │  └─ 7,200 chars × $16.00/1M = $0.1152 (79% of total)
│  │
│  └─ Option B: Gemini 2.5 Flash TTS (better voice)
│     └─ 7,200 chars × $3.50/1M = $0.0252 (only 46% of total)
│
├─ Stage 4.5: Speech-to-Text (optional)
│  └─ 10 minutes × $0.024/min = $0.24 (for word-level timing)
│
├─ Stage 5: Visual Effects
│  └─ Local VisualEffectsEngine v2
│     └─ $0 (free)
│
└─ Stage 6: Validation
   └─ Local ValidationEngine
      └─ $0 (free)

═════════════════════════════════════════════════════
TOTAL (Current - Chirp 3 HD):     $0.145 ✅ BASE PRICE
═════════════════════════════════════════════════════

Optimization Scenarios:

1️⃣ With OCR Cache (repeat processing):
   $0.145 - $0.0225 = $0.1227 (-15% cheaper)
   
2️⃣ With Gemini TTS (better voice):
   $0.030 + $0.0252 = $0.0552 (-62% cheaper! ⚡)
   
3️⃣ With Gemini TTS + STT (word-level VFX):
   $0.030 + $0.0252 + $0.24 = $0.2952 (+103% more expensive)
```

---

## 2. PRICING TIERS (Ценовые уровни)

```
                USER SEGMENT → 
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│                    FREE TIER (Marketing)                 │
├──────────────────────────────────────────────────────────┤
│ Price:           $0/month                                │
│ Presentations:   3/month                                │
│ Slides:          10 per presentation                    │
│ Storage:         1 GB                                    │
│ Target:          Getting users to try                   │
│ Margin:          ✗ Loss (cost $0.435/month)            │
│ Value Prop:      "Try for free, no credit card"         │
└──────────────────────────────────────────────────────────┘
           ↓ (when user wants more)
           
┌──────────────────────────────────────────────────────────┐
│               PRO TIER ⭐ (Recommended)                   │
├──────────────────────────────────────────────────────────┤
│ Price:           $9.99/month ($99.99/year = -17%)       │
│ Presentations:   30/month                               │
│ Slides:          100 per presentation                   │
│ Storage:         50 GB                                   │
│ Export:          MP4, WebM, GIF                         │
│ API:             ✗ Not included                          │
│ Target:          Active creators, teachers              │
│ Margin:          ✓✓ 130% profit (ROI: 2.2x)            │
│ Value Prop:      "10x more, cheaper per presentation"  │
│ Conversion:      Expected 25-30% from Free             │
└──────────────────────────────────────────────────────────┘
           ↓ (when user needs more features)
           
┌──────────────────────────────────────────────────────────┐
│               BUSINESS TIER 🚀 (Popular)                 │
├──────────────────────────────────────────────────────────┤
│ Price:           $24.99/month ($249.99/year = -17%)     │
│ Presentations:   100/month                              │
│ Slides:          500 per presentation                   │
│ Storage:         500 GB                                 │
│ Export:          ALL formats + PPTX                     │
│ API:             ✓ Full access                          │
│ Target:          Professionals, growing businesses      │
│ Margin:          ✓ 72% profit (ROI: 1.7x)              │
│ Value Prop:      "Professional features + API"         │
│ Conversion:      Expected 10% from Pro                 │
│ Team:            Collaboration (up to 5 users)         │
└──────────────────────────────────────────────────────────┘
           ↓ (enterprise scaling)
           
┌──────────────────────────────────────────────────────────┐
│              ENTERPRISE TIER 💎 (Revenue)                │
├──────────────────────────────────────────────────────────┤
│ Price:           Custom (typically $100+/month)         │
│ Presentations:   Unlimited                              │
│ Slides:          Unlimited                              │
│ Storage:         Unlimited                              │
│ Export:          Everything                             │
│ API:             ✓ Unlimited                            │
│ SSO/SAML:        ✓ Included                             │
│ Target:          Large corporations                     │
│ Margin:          ✓✓✓ Variable (often >100%)            │
│ Value Prop:      "Dedicated support + custom SLA"       │
│ LTV:             ~$5,000+ (vs $239 for Pro)            │
│ Contact:         "Contact sales" page                  │
└──────────────────────────────────────────────────────────┘
```

---

## 3. CUSTOMER JOURNEY (Путь пользователя)

```
┌─────────────┐
│   New User  │
└──────┬──────┘
       │
       ▼
   ╔═════════╗
   ║  FREE   ║ ◄──── No credit card
   ║ 3/month ║       Start here
   ╚────┬────╝
        │
        │ "This is awesome!"
        │ ↓ (User wants more presentations)
        │ Friction point: Hit 3 presentation limit
        │
        ▼
   ┌─────────────────────────────┐
   │ "Upgrade to Pro?" Modal     │
   │                             │
   │ [Benefits]                  │
   │ • 30 presentations/month    │
   │ • Premium TTS quality       │
   │ • All export formats        │
   │                             │
   │ [Offer]                     │
   │ Try 7 days free!            │
   │ Then $9.99/month            │
   │                             │
   │ [CTA Button]                │
   │ START FREE TRIAL ──► Stripe │
   └─────────────────────────────┘
        │
        │ CONVERSION POINT
        │ (Target: 25-30% convert)
        │
        ├─ YES (70-75% of users)
        │   └─► CHURN (no payment)
        │       Reason: "Not ready to pay"
        │       Action: Re-engagement campaign
        │
        └─ NO (25-30% of users) ✅
            └─► PRO SUBSCRIBER
                │
                ├─ Happy with 30/month
                │  └─► Keep paying ($119.88/year)
                │
                └─ Wants more features
                   │ (API access, 100 slides, etc)
                   │
                   ▼
                ┌────────────────────────┐
                │ "Upgrade to Business?" │
                │ $24.99/month offer     │
                │ (additional $14.99)    │
                └────────────────────────┘
                   │
                   ├─ NO (80% of Pro)
                   │  └─► Stay on Pro
                   │
                   └─ YES (20% of Pro) ✅
                      └─► BUSINESS SUBSCRIBER
                          (highest ROI tier)
                          │
                          └─ Eventually:
                             Enterprise or Team Plans
```

---

## 4. REVENUE MATH (Финансовая модель)

```
SCENARIO: 1,000 Active Users/Month

User Distribution:
┌─────────────────────────────────────────┐
│ Free:       600 users (60%)              │
│ Pro:        300 users (30%)              │
│ Business:   80 users (10%)              │
│ Enterprise: 20 users (1 contact = 20)   │
└─────────────────────────────────────────┘

REVENUE CALCULATION:
═════════════════════════════════════════════
Pro:        300 × $9.99/month = $2,997
Business:   80 × $24.99/month = $1,999
Enterprise: 20 × $200/month*  = $4,000
───────────────────────────────────────────
MONTHLY REVENUE:              $8,996

COST CALCULATION:
═════════════════════════════════════════════
Free:       600 × 3 × $0.145  = $261
Pro:        300 × 30 × $0.145 = $1,305
Business:   80 × 100 × $0.145 = $1,160
Enterprise: 20 × 300 × $0.145 = $870
───────────────────────────────────────────
MONTHLY AI/TTS COST:          $3,596

OTHER COSTS:
═════════════════════════════════════════════
Storage:              $300
Infrastructure:       $1,200
Support/Operations:   $800
───────────────────────────────────────────
TOTAL OTHER COSTS:    $2,300

PROFITABILITY:
═════════════════════════════════════════════
Total Revenue:        $8,996
Total Costs:          $5,896
───────────────────────────────────────────
GROSS PROFIT:         $3,100 ✅
MARGIN:               34%

* Enterprise price varies, using average
```

---

## 5. SCALING SCENARIOS (Сценарии масштабирования)

```
TIMELINE: What happens as you grow?

Month 1:    100 users
├─ 60 free (no revenue)
├─ 30 pro ($299.70)
└─ 10 biz ($249.90)
   REVENUE: $549.60
   COST: $360
   PROFIT: $189.60 ✓

Month 3:    500 users
├─ 300 free (no revenue)
├─ 150 pro ($1,498.50)
├─ 40 biz ($999.60)
└─ 10 ent ($2,000)
   REVENUE: $4,498.10
   COST: $1,798
   PROFIT: $2,700.10 ✓✓

Month 12:   2,000 users
├─ 1,200 free
├─ 600 pro ($5,994)
├─ 160 biz ($3,998)
└─ 40 ent ($8,000)
   REVENUE: $17,992
   COST: $7,192
   PROFIT: $10,800 ✓✓✓

At this point:
- Reconsider: Switch to Gemini TTS ($0.055)
- New COST: $2,872 (60% reduction)
- New PROFIT: $15,120 (40% increase!)
```

---

## 6. KEY METRICS DASHBOARD (Метрики для отслеживания)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              DAILY TRACKING BOARD               ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Metric               │ Target  │ Actual  │ Status ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Free → Pro Conv      │ 25%     │ ???     │ 📊 TBD ┃
┃ Pro Churn Rate       │ <5%/mo  │ ???     │ 📊 TBD ┃
┃ Business Conversion  │ 10%     │ ???     │ 📊 TBD ┃
┃ Trial Completion     │ 70%     │ ???     │ 📊 TBD ┃
┃ Monthly Revenue      │ $5K+    │ ???     │ 📊 TBD ┃
┃ Average ARPU         │ $2-3    │ ???     │ 📊 TBD ┃
┃ CAC Payback Period   │ <2 mo   │ ???     │ 📊 TBD ┃
┃ Support Tickets      │ <5/day  │ ???     │ 📊 TBD ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

When collecting data:
✓ Daily: Revenue, new signups, churn
✓ Weekly: Conversion rates, support tickets
✓ Monthly: ARPU, LTV, CAC, margin
✓ Quarterly: Business health scorecard
```

---

## 7. COMPETITIVE POSITIONING (Конкурентное позиционирование)

```
Price vs Features:

$0 ┤ FREE
   │
$10┤              PRO ⭐
   │              
$25┤                    BUSINESS 🚀
   │
$50┤                          
   │                          ENTERPRISE 💎
$100┤                         
   │                         
   └────────────────────────────────────────
     3     30     100    250    500+
     presentations/month (log scale)

Our positioning:
- FREE:   "Lowest barrier to entry" ✓
- PRO:    "Best value for creators" ✓✓
- BUSINESS: "Professional features" ✓✓✓
- ENTERPRISE: "Whatever you need" ✓✓✓✓

Competitor price range:
- Competitor A: FREE + $19.99/mo
  → We beat with lower Pro price
  
- Competitor B: $29.99/mo minimum
  → We beat with FREE tier + cheaper Pro
  
- Competitor C: Custom only
  → We beat with transparent pricing
```

---

## 8. DECISION TREE (Дерево решений для выбора плана)

```
Are you a new user?
    │
    ├─ YES → Start FREE
    │       Can you create 3 presentations/month?
    │       ├─ YES → Keep FREE
    │       └─ NO → Upgrade to PRO ($9.99)
    │
    └─ NO → Already using system
            Do you need 30+ presentations/month?
            ├─ NO → Keep FREE
            ├─ MAYBE → Try PRO trial (7 days free)
            └─ YES → 
                    Need API access?
                    ├─ NO → Use PRO ($9.99)
                    ├─ YES → Use BUSINESS ($24.99)
                    └─ MAYBE + Large org → ENTERPRISE
```

---

**Visual Summary Created:** November 12, 2025  
**All Diagrams Ready:** ✅  
**Status:** Ready for Presentation
