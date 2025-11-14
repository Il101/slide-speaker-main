# Analytics Dashboard: Real Data vs Placeholders

**Last Updated:** 2025-01-08

---

## 📊 Overview

This document details which metrics in the Analytics Dashboard use **real data from the database** and which use **placeholder/estimated values**.

---

## ✅ **REAL DATA** (from Database)

### 1. User Metrics

| Metric | Source | SQL Query | Status |
|--------|--------|-----------|--------|
| **Total Users** | `users` table | `SELECT COUNT(*) FROM users` | ✅ REAL |
| **Active Users** | `users` table | `SELECT COUNT(*) FROM users WHERE updated_at >= (NOW() - 30 days)` | ✅ REAL |
| **Paid Users** | `users` table | `SELECT COUNT(*) FROM users WHERE subscription_tier != 'free'` | ✅ REAL |
| **Conversion Rate** | Calculated | `(paid_users / total_users) * 100` | ✅ REAL |

**Verification:**
```sql
-- Current values
SELECT 
    COUNT(*) as total_users,
    COUNT(CASE WHEN subscription_tier != 'free' THEN 1 END) as paid_users
FROM users;
-- Result: 2 total, 0 paid
```

---

### 2. Lecture Metrics

| Metric | Source | SQL Query | Status |
|--------|--------|-----------|--------|
| **Total Lectures** | `lessons` table | `SELECT COUNT(*) FROM lessons WHERE created_at >= start_date` | ✅ REAL |
| **Users with Lectures** | `lessons` table | `SELECT COUNT(DISTINCT user_id) FROM lessons` | ✅ REAL |

**Verification:**
```sql
-- Current values
SELECT COUNT(*) as total_lectures FROM lessons;
-- Result: 0 lectures
```

---

### 3. Events & Sessions

| Metric | Source | SQL Query | Status |
|--------|--------|-----------|--------|
| **Top Events** | `analytics_events` table | `SELECT event_name, COUNT(*) as count FROM analytics_events GROUP BY event_name ORDER BY count DESC LIMIT 10` | ✅ REAL |
| **Acquisition Sources** | `user_sessions` table | `SELECT utm_source, COUNT(*) FROM user_sessions GROUP BY utm_source` | ✅ REAL |
| **Session Data** | `user_sessions` table | All session tracking data | ✅ REAL |

**Verification:**
```sql
-- Current top events
SELECT event_name, COUNT(*) FROM analytics_events GROUP BY event_name ORDER BY COUNT(*) DESC LIMIT 5;
-- Result: Page View (26), Page Hidden (21), Session End (11), etc.
```

---

### 4. Cost Tracking

| Metric | Source | SQL Query | Status |
|--------|--------|-----------|--------|
| **Total Costs** | `cost_logs` table | `SELECT SUM(cost) FROM cost_logs WHERE timestamp >= start_date` | ✅ REAL |
| **Cost Breakdown** | `cost_logs` table | `SELECT operation, SUM(cost) FROM cost_logs GROUP BY operation` | ✅ REAL |
| **Cost per User** | Calculated | `total_costs / active_users` | ✅ REAL |
| **Cost per Lecture** | Calculated | `total_costs / total_lectures` | ✅ REAL |

**Verification:**
```sql
-- Current costs
SELECT operation, COUNT(*), SUM(cost) as total FROM cost_logs GROUP BY operation;
-- Result: OCR ($0.030), AI ($0.001), TTS ($0.008)
```

---

### 5. Daily Metrics (Charts)

| Chart | Source | Status | Notes |
|-------|--------|--------|-------|
| **User Growth Chart** | `daily_metrics.new_users` | ✅ REAL | Cumulative sum of new users |
| **Revenue Chart** | `daily_metrics.mrr` | ⚠️ PARTIAL | MRR in table, but populated with placeholder |
| **Lecture Activity Chart** | `daily_metrics.lectures_created` | ✅ REAL | Lectures created per day |

**Note:** `daily_metrics` table exists and structure is correct, but needs regular aggregation job to populate data.

---

## ⚠️ **PLACEHOLDER DATA** (Hardcoded/Estimated)

### 1. Revenue Metrics

| Metric | Current Value | Issue | Fix Needed |
|--------|---------------|-------|------------|
| **MRR (Monthly Recurring Revenue)** | `paid_users * 9.99` | ❌ Uses fixed $9.99 price | ✅ Query actual subscription prices from `subscriptions` table |
| **MRR Growth** | `12.0%` | ❌ Hardcoded | ✅ Calculate from historical `daily_metrics.mrr` |
| **User Growth** | `"+15%"` | ❌ Hardcoded string | ✅ Calculate from user count change |

**Current Code:**
```python
# Line 301 - PLACEHOLDER
mrr = paid_users * 9.99  # Should query actual subscription prices

# Line 370 - PLACEHOLDER
"mrrGrowth": 12.0,  # Should calculate from historical data

# Line 371 - PLACEHOLDER
"userGrowth": "+15%",  # Should calculate from user count change
```

**Fix Required:**
```python
# Proper MRR calculation
mrr_result = await db.execute(
    select(func.sum(Subscription.price))
    .where(Subscription.status == "active")
)
mrr = float(mrr_result.scalar() or 0)

# Proper MRR growth
last_month_mrr = await db.execute(
    select(DailyMetrics.mrr)
    .where(DailyMetrics.date == datetime.utcnow() - timedelta(days=30))
)
last_month = float(last_month_mrr.scalar() or 0)
mrr_growth = ((mrr - last_month) / last_month * 100) if last_month > 0 else 0
```

---

### 2. Conversion Funnel

| Step | Data Source | Status | Notes |
|------|-------------|--------|-------|
| **Signed Up** | `users` count | ✅ REAL | Total users |
| **Email Verified** | `total_users * 0.8` | ❌ PLACEHOLDER | No email verification tracking |
| **Created Lecture** | `lessons` distinct user_id | ✅ REAL | Real data |
| **Downloaded** | `has_lectures * 0.7` | ❌ PLACEHOLDER | No download tracking |
| **Upgraded to Paid** | `paid_users` | ✅ REAL | Real data |

**Current Code:**
```python
# Line 335 - PLACEHOLDER
email_verified = int(total_users * 0.8)  # No email verification table

# Line 341 - PLACEHOLDER
has_downloads = int(has_lectures * 0.7)  # No download tracking
```

**Fix Required:**
```python
# Option 1: Add email_verified column to users table
email_verified_result = await db.execute(
    select(func.count(User.id)).where(User.email_verified == True)
)
email_verified = email_verified_result.scalar() or 0

# Option 2: Track downloads in exports table
downloads_result = await db.execute(
    select(func.count(func.distinct(Export.user_id)))
    .where(Export.status == "completed")
)
has_downloads = downloads_result.scalar() or 0
```

---

### 3. Plan Distribution

| Plan Type | Current Calculation | Status | Notes |
|-----------|-------------------|--------|-------|
| **Free** | `total_users - paid_users` | ✅ REAL | Correct |
| **Starter** | `paid_users * 0.6` | ❌ PLACEHOLDER | Assumes 60% on starter |
| **Pro** | `paid_users * 0.3` | ❌ PLACEHOLDER | Assumes 30% on pro |
| **Business** | `paid_users * 0.1` | ❌ PLACEHOLDER | Assumes 10% on business |

**Current Code:**
```python
# Lines 330-334 - PLACEHOLDERS
plan_distribution = [
    total_users - paid_users,  # free - REAL
    int(paid_users * 0.6),     # starter - PLACEHOLDER
    int(paid_users * 0.3),     # pro - PLACEHOLDER
    int(paid_users * 0.1)      # business - PLACEHOLDER
]
```

**Fix Required:**
```python
# Query actual subscription tiers
plan_dist_result = await db.execute(
    select(User.subscription_tier, func.count(User.id))
    .group_by(User.subscription_tier)
)
plan_counts = {tier: count for tier, count in plan_dist_result.all()}

plan_distribution = [
    plan_counts.get('free', 0),
    plan_counts.get('starter', 0),
    plan_counts.get('pro', 0),
    plan_counts.get('business', 0)
]
```

---

## 📋 Summary Table

| Category | Real Metrics | Placeholder Metrics | Accuracy |
|----------|--------------|---------------------|----------|
| **Users** | 4/4 | 0/4 | 100% ✅ |
| **Lectures** | 2/2 | 0/2 | 100% ✅ |
| **Events** | 3/3 | 0/3 | 100% ✅ |
| **Costs** | 4/4 | 0/4 | 100% ✅ |
| **Revenue** | 1/4 | 3/4 | 25% ⚠️ |
| **Funnel** | 3/5 | 2/5 | 60% ⚠️ |
| **Charts** | 2/3 | 1/3 | 67% ⚠️ |
| **Plan Distribution** | 1/4 | 3/4 | 25% ⚠️ |
| **TOTAL** | **20/29** | **9/29** | **69%** |

---

## 🔧 Required Fixes (Priority Order)

### HIGH PRIORITY

1. **MRR Calculation** ❗
   - Current: `paid_users * 9.99`
   - Fix: Query actual subscription prices
   - Impact: Revenue metrics completely wrong

2. **Email Verification Tracking** ❗
   - Current: `total_users * 0.8`
   - Fix: Add `email_verified` boolean to `users` table
   - Impact: Funnel accuracy

3. **Download Tracking** ❗
   - Current: `has_lectures * 0.7`
   - Fix: Use `exports` table with status="completed"
   - Impact: Funnel accuracy

### MEDIUM PRIORITY

4. **Plan Distribution**
   - Current: Percentages (60/30/10)
   - Fix: Query actual subscription_tier from users
   - Impact: User segmentation

5. **MRR Growth**
   - Current: Hardcoded `12.0`
   - Fix: Calculate from historical daily_metrics
   - Impact: Trend analysis

6. **User Growth**
   - Current: Hardcoded `"+15%"`
   - Fix: Calculate from user count change
   - Impact: Growth metrics

### LOW PRIORITY

7. **Daily Metrics Aggregation**
   - Current: Manual/empty
   - Fix: Add cron job to populate `daily_metrics` table
   - Impact: Historical charts accuracy

---

## 💡 Implementation Recommendations

### 1. Add Missing Database Columns

```sql
-- Add email verification tracking
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN email_verified_at TIMESTAMP;

-- Add subscription price tracking
CREATE TABLE IF NOT EXISTS subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    tier VARCHAR(50),
    price DECIMAL(10,2),
    status VARCHAR(50),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Create Daily Aggregation Job

```python
# Create scheduled task (Celery/cron)
@app.task
async def aggregate_daily_metrics():
    """Run daily at midnight to aggregate metrics"""
    async with AsyncSessionLocal() as db:
        today = datetime.utcnow().date()
        
        # Get counts
        total_users = await db.execute(select(func.count(User.id)))
        new_users = await db.execute(
            select(func.count(User.id))
            .where(func.date(User.created_at) == today)
        )
        lectures_created = await db.execute(
            select(func.count(Lesson.id))
            .where(func.date(Lesson.created_at) == today)
        )
        
        # Calculate MRR
        active_subscriptions = await db.execute(
            select(func.sum(Subscription.price))
            .where(Subscription.status == "active")
        )
        
        # Save to daily_metrics
        metric = DailyMetrics(
            id=str(uuid.uuid4()),
            date=today,
            total_users=total_users.scalar(),
            new_users=new_users.scalar(),
            lectures_created=lectures_created.scalar(),
            mrr=active_subscriptions.scalar() or 0
        )
        db.add(metric)
        await db.commit()
```

### 3. Update Analytics Endpoint

Replace all placeholders with real queries as shown in the "Fix Required" sections above.

---

## 📊 Current Data Status

### Database Tables Population

| Table | Records | Last Updated | Status |
|-------|---------|--------------|--------|
| `users` | 2 | Active | ✅ |
| `lessons` | 0 | Empty | ⚠️ |
| `analytics_events` | 73+ | Real-time | ✅ |
| `user_sessions` | 6 | Real-time | ✅ |
| `cost_logs` | 5 | Real-time | ✅ |
| `daily_metrics` | 1 | Manual | ⚠️ Needs cron job |
| `subscriptions` | N/A | Missing table | ❌ |
| `exports` | 0 | Empty | ⚠️ |

---

## ✅ Conclusion

**Current Analytics Accuracy: 69% (20/29 metrics)**

### What Works ✅
- User counting and segmentation
- Event tracking (73+ events)
- Session tracking (6 sessions)
- Cost tracking ($0.039 total)
- Basic funnel (3/5 steps)
- Charts structure (needs data)

### What Needs Fixing ⚠️
- Revenue calculations (MRR)
- Growth metrics (trends)
- Plan distribution (detailed breakdown)
- Email verification tracking
- Download tracking
- Daily metrics aggregation

### Impact
- **For Demo/MVP:** Current state is acceptable (69% real data)
- **For Production:** Need to implement HIGH priority fixes
- **For Investors:** Should fix revenue metrics first

---

**Next Steps:**
1. Create `subscriptions` table
2. Add `email_verified` to users
3. Implement daily aggregation cron job
4. Update analytics queries to use real data
5. Add download tracking

---

**Generated:** 2025-01-08  
**Status:** Under Development  
**Version:** 1.0
