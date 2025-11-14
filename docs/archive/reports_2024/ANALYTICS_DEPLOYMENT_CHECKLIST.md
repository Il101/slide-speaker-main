# 📋 Analytics Deployment Checklist

## Pre-Deployment

### ✅ Code Review
- [ ] All analytics files created
  - [ ] `backend/app/api/analytics.py`
  - [ ] `backend/app/services/cost_tracker.py`
  - [ ] `backend/alembic/versions/002_add_analytics_tables.py`
  - [ ] `src/lib/analytics.ts`
  - [ ] `src/pages/Analytics.tsx`
- [ ] Database models added to `backend/app/core/database.py`
- [ ] Analytics router registered in `backend/app/main.py`
- [ ] Dependencies added to `requirements.txt` and `package.json`
- [ ] Event tracking integrated in:
  - [ ] `src/pages/Login.tsx`
  - [ ] `src/pages/Register.tsx`
  - [ ] `src/pages/Index.tsx`
  - [ ] `src/pages/SubscriptionPage.tsx`
- [ ] Admin navigation link added to `src/components/Navigation.tsx`
- [ ] Admin-only protection on `/analytics` route

### ✅ Testing
- [ ] Run test script: `./test_analytics_system.sh`
- [ ] All imports work correctly
- [ ] No TypeScript errors: `npm run type-check`
- [ ] Frontend builds successfully: `npm run build`
- [ ] Backend starts without errors

## Deployment Steps

### 1. Database Migration
```bash
# Check current migration status
cd backend
alembic current

# Run migration
alembic upgrade head

# Verify tables created
psql $DATABASE_URL -c "\dt analytics_*"
psql $DATABASE_URL -c "\dt user_sessions"
psql $DATABASE_URL -c "\dt daily_metrics"
psql $DATABASE_URL -c "\dt cost_logs"
```

**Expected output:**
```
analytics_events
user_sessions
daily_metrics
cost_logs
```

- [ ] Migration ran successfully
- [ ] All 4 tables created
- [ ] Indexes created

### 2. Backend Deployment

#### Docker
```bash
# Rebuild containers
docker-compose down
docker-compose build backend
docker-compose up -d

# Check logs
docker-compose logs -f backend | grep analytics
```

#### Local
```bash
cd backend
uvicorn app.main:app --reload
```

**Verify:**
- [ ] Backend started without errors
- [ ] Analytics router registered (check logs)
- [ ] API endpoints accessible:
  - `curl http://localhost:8000/api/analytics/track -X POST`
  - `curl http://localhost:8000/api/analytics/session -X POST`
  - `curl http://localhost:8000/api/analytics/admin/dashboard -H "Authorization: Bearer TOKEN"`

### 3. Frontend Deployment

```bash
# Install dependencies (if needed)
npm install

# Build
npm run build

# Test locally
npm run dev
```

**Verify:**
- [ ] No build errors
- [ ] Analytics SDK loaded
- [ ] Dashboard page renders
- [ ] No console errors

### 4. Smoke Tests

#### Test Event Tracking
1. Open browser console
2. Navigate to the app
3. Check Network tab for:
   - `POST /api/analytics/session` (on page load)
   - `POST /api/analytics/track` (on actions)

**Expected:**
```javascript
// Session tracked
{
  "success": true
}

// Event tracked
{
  "success": true
}
```

- [ ] Session tracking works
- [ ] Page view tracking works
- [ ] Events sent successfully

#### Test Login/Register Tracking
1. Register new user
2. Login with user
3. Check database:
```sql
SELECT * FROM analytics_events 
WHERE event_name IN ('User Signed Up', 'User Logged In')
ORDER BY timestamp DESC 
LIMIT 5;
```

**Expected:** Events appear in database

- [ ] Signup event tracked
- [ ] Login event tracked
- [ ] User ID captured correctly

#### Test Admin Dashboard
1. Login as admin (admin@example.com / admin123)
2. Navigate to `/analytics`
3. Check dashboard loads

**Verify:**
- [ ] Dashboard loads successfully
- [ ] Charts render
- [ ] Data appears (even if zeros initially)
- [ ] No console errors

### 5. Integration Tests

#### Test Cost Tracking (if integrated)
```python
# Run from backend directory
python3 -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.services.cost_tracker import track_ocr_cost

async def test():
    async with AsyncSessionLocal() as db:
        await track_ocr_cost(
            db=db,
            slide_count=10,
            user_id='test-user',
            lesson_id='test-lesson'
        )
        await db.commit()
    print('✅ Cost tracking works!')

asyncio.run(test())
"
```

**Check database:**
```sql
SELECT * FROM cost_logs ORDER BY timestamp DESC LIMIT 1;
```

- [ ] Cost log created
- [ ] Cost calculated correctly
- [ ] Metadata stored

### 6. Performance Check

```bash
# Check analytics endpoint performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/analytics/track
```

**Expected:**
- Response time < 100ms
- No errors

- [ ] Tracking endpoint fast (< 100ms)
- [ ] Dashboard loads in < 2s
- [ ] No memory leaks

## Post-Deployment

### 1. Monitor Logs

**Backend:**
```bash
docker-compose logs -f backend | grep -E "analytics|cost"
```

**Look for:**
- [ ] No error messages
- [ ] Events being tracked
- [ ] No database connection issues

### 2. Verify Data Collection

**After 1 hour:**
```sql
-- Check events collected
SELECT COUNT(*) as event_count FROM analytics_events;

-- Check sessions
SELECT COUNT(*) as session_count FROM user_sessions;

-- Top events
SELECT event_name, COUNT(*) as count 
FROM analytics_events 
GROUP BY event_name 
ORDER BY count DESC;
```

**Expected:**
- Event count > 0
- Session count > 0
- Various event types tracked

- [ ] Events accumulating
- [ ] Sessions being tracked
- [ ] No duplicate events

### 3. Dashboard Validation

**After 24 hours:**
1. Visit `/analytics` as admin
2. Select "Last 7d"
3. Check all tabs:
   - [ ] Overview: metrics populated
   - [ ] Costs: data if cost tracking integrated
   - [ ] Funnel: conversion data
   - [ ] Insights: recommendations appear

### 4. Alert Setup (Optional)

**Set up monitoring for:**
- [ ] High cost spikes (> $X per day)
- [ ] Low conversion rate (< 2%)
- [ ] Error rate increase (> 5%)
- [ ] No events for 1 hour (system down?)

**Tools:**
- Grafana + Prometheus
- Custom scripts querying database
- Email notifications

## Rollback Plan

If something goes wrong:

### 1. Rollback Database
```bash
cd backend
alembic downgrade -1  # Rollback one migration
```

### 2. Rollback Code
```bash
git revert HEAD  # Revert analytics commit
git push origin main
```

### 3. Restart Services
```bash
docker-compose restart
```

## Maintenance

### Weekly
- [ ] Check analytics dashboard for anomalies
- [ ] Review top errors
- [ ] Monitor cost trends

### Monthly
- [ ] Clean old analytics data (if retention policy exists)
- [ ] Review insights and act on recommendations
- [ ] Update cost pricing if APIs change

### Quarterly
- [ ] Analyze conversion funnel improvements
- [ ] A/B test based on analytics insights
- [ ] Update KPIs and targets

## Troubleshooting

### Events not appearing in database
```sql
-- Check if tables exist
\dt analytics_*

-- Check for errors in events
SELECT * FROM analytics_events ORDER BY timestamp DESC LIMIT 10;

-- Check session IDs
SELECT DISTINCT session_id FROM analytics_events LIMIT 5;
```

**Solutions:**
- Verify migration ran
- Check backend logs for errors
- Ensure browser isn't blocking requests (CORS)

### Dashboard not loading
**Check:**
1. User has admin role: `SELECT email, role FROM users WHERE email = 'your@email';`
2. API endpoint works: `curl http://localhost:8000/api/analytics/admin/dashboard`
3. Frontend console for errors
4. Network tab for failed requests

### Cost tracking not working
**Check:**
1. `track_cost` functions imported in pipeline
2. Database session passed to pipeline
3. `await db.commit()` called after tracking
4. Check `cost_logs` table: `SELECT * FROM cost_logs LIMIT 10;`

## Success Criteria

### Day 1
- ✅ Migration successful
- ✅ Services running without errors
- ✅ Events being tracked
- ✅ Dashboard accessible

### Week 1
- ✅ 100+ events tracked
- ✅ Multiple event types captured
- ✅ Funnel data populated
- ✅ No performance issues

### Month 1
- ✅ Insights actionable
- ✅ Cost tracking operational (if integrated)
- ✅ Dashboard used for decisions
- ✅ ROI measurable

## Documentation Links

- 📖 [Quick Start Guide](./ANALYTICS_QUICK_START.md)
- 📖 [Implementation Guide](./ANALYTICS_IMPLEMENTATION_GUIDE.md)
- 📖 [Cost Tracking Examples](./COST_TRACKING_INTEGRATION_EXAMPLES.md)
- 📖 [Final Summary](./ANALYTICS_FINAL_SUMMARY.md)

## Support

If you encounter issues:
1. Check documentation
2. Review logs
3. Verify configuration
4. Test with curl
5. Check database state

---

**Ready to deploy?** Follow this checklist step by step! ✅
