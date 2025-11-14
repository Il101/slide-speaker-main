# Analytics System Implementation Guide

## Overview

A complete analytics system has been implemented for your slide-speaker application with:
- **Event tracking** (user actions, page views, errors)
- **Session tracking** (user sessions, UTM parameters, acquisition sources)
- **Cost tracking** (OCR, AI, TTS, storage costs)
- **Admin dashboard** (metrics, charts, funnels, insights)
- **Automatic daily aggregation**

## Architecture

### Backend (FastAPI + SQLAlchemy)
- **Models**: 4 new database tables in `backend/app/core/database.py`
  - `AnalyticsEvent`: Individual event tracking
  - `UserSession`: Session tracking with UTM parameters
  - `DailyMetrics`: Aggregated daily metrics
  - `CostLog`: Individual cost tracking

- **API Endpoints**: `backend/app/api/analytics.py`
  - `POST /api/analytics/track` - Track events
  - `POST /api/analytics/session` - Track sessions
  - `GET /api/analytics/admin/dashboard` - Admin dashboard data

- **Cost Tracker**: `backend/app/services/cost_tracker.py`
  - Helper functions for tracking OCR, AI, TTS, storage costs
  - Automatic cost calculation based on usage

### Frontend (React + TypeScript)
- **Client SDK**: `src/lib/analytics.ts`
  - Automatic session management
  - Event tracking helpers
  - React hook `useAnalytics()`

- **Dashboard**: `src/pages/Analytics.tsx`
  - Beautiful charts (Chart.js)
  - Key metrics cards
  - Conversion funnel
  - Cost analysis
  - AI-powered insights

## Setup Instructions

### 1. Run Database Migration

```bash
cd backend
alembic upgrade head
```

This creates the 4 new analytics tables in your database.

### 2. Restart Backend

```bash
# In backend directory
uvicorn app.main:app --reload
```

The analytics API endpoints are now available.

### 3. Verify Frontend Build

```bash
# In root directory
npm run build
```

Analytics are automatically initialized in the app.

### 4. Access Analytics Dashboard

Navigate to: `http://localhost:5173/analytics` (or your production URL)

**Note**: You may want to add admin-only protection to this route.

## Usage Examples

### Tracking Events in Your Code

```typescript
import { trackEvent } from '@/lib/analytics';

// Track presentation upload
trackEvent.presentationUploaded({
  fileSize: file.size,
  fileName: file.name,
  fileType: file.type
});

// Track lecture generation
trackEvent.lectureGenerationCompleted({
  lectureId: lecture.id,
  processingTime: Date.now() - startTime,
  duration: lecture.duration
});

// Track errors
trackEvent.error({
  errorType: error.name,
  errorMessage: error.message,
  location: 'lecture_generation',
  fatal: true
});

// Track monetization
trackEvent.upgradeClicked({
  plan: 'pro',
  location: 'pricing_page'
});
```

### Tracking Costs in Backend

```python
from app.services.cost_tracker import track_ocr_cost, track_ai_generation_cost, track_tts_cost

# Track OCR cost
await track_ocr_cost(
    db=db,
    slide_count=len(slides),
    user_id=user_id,
    lesson_id=lesson_id,
    file_name=filename
)

# Track AI generation cost
await track_ai_generation_cost(
    db=db,
    model="gemini-1.5-flash",
    input_tokens=1500,
    output_tokens=500,
    user_id=user_id,
    lesson_id=lesson_id,
    slide_number=slide_num
)

# Track TTS cost
await track_tts_cost(
    db=db,
    character_count=len(text),
    voice="neural2-en-US",
    user_id=user_id,
    lesson_id=lesson_id,
    slide_number=slide_num
)
```

## Integration Points

### Where to Add Tracking

1. **User Authentication** (`src/pages/Login.tsx`, `src/pages/Register.tsx`)
   ```typescript
   trackEvent.signup('email');
   trackEvent.login('email');
   ```

2. **Presentation Upload** (wherever file upload happens)
   ```typescript
   trackEvent.presentationUploaded({ fileSize, fileName, fileType });
   ```

3. **Lecture Generation** (backend pipeline)
   ```python
   # Start tracking
   await track_ai_generation_cost(...)
   await track_tts_cost(...)
   ```

4. **Downloads** (when user downloads lecture)
   ```typescript
   trackEvent.lectureDownloaded({
     lectureId: id,
     format: 'mp4',
     lectureNumber: index
   });
   ```

5. **Errors** (in error boundaries, API error handlers)
   ```typescript
   trackEvent.error({
     errorType: error.name,
     errorMessage: error.message,
     location: 'api_call'
   });
   ```

6. **Monetization** (pricing, checkout, payments)
   ```typescript
   trackEvent.pricingPageViewed();
   trackEvent.checkoutStarted({ plan: 'pro', price: 29.99 });
   trackEvent.paymentSucceeded({ plan: 'pro', amount: 29.99 });
   ```

## Cost Tracking Configuration

Current pricing in `cost_tracker.py`:

- **OCR**: $1.50 per 1,000 slides (Google Vision API)
- **AI Generation**: 
  - Gemini 1.5 Flash: $0.15/$0.60 per 1M tokens (input/output)
  - Gemini 1.5 Pro: $1.25/$5.00 per 1M tokens
  - GPT-4o-mini: $0.15/$0.60 per 1M tokens
- **TTS**: 
  - Standard voices: $4 per 1M characters
  - Neural/WaveNet: $16 per 1M characters
- **Storage**: $0.020 per GB per month (GCS)

You can adjust these in `backend/app/services/cost_tracker.py`.

## Dashboard Features

### Overview Tab
- User growth chart
- Revenue (MRR) chart
- Lecture activity
- Plan distribution
- Top events
- User acquisition sources

### Costs Tab
- Total costs
- Cost per user
- Cost per lecture
- Gross margin
- Cost breakdown by operation

### Funnel Tab
- Conversion funnel visualization
- Signup → Email Verified → Lecture Created → Download → Paid

### Insights Tab
- AI-powered recommendations
- Warnings for low conversion/activation
- Success indicators
- Actionable advice

## Performance Considerations

1. **Async Tracking**: Events are sent asynchronously and don't block the UI
2. **Batch Processing**: Daily metrics are aggregated automatically
3. **Indexes**: All tables have proper indexes for fast queries
4. **Caching**: Consider adding Redis caching for dashboard queries
5. **Beacon API**: Uses `navigator.sendBeacon` for reliable event delivery

## Privacy & Security

1. **IP Anonymization**: Consider hashing IP addresses
2. **PII Protection**: Don't track sensitive user data in properties
3. **Admin Only**: Protect `/analytics` route with admin role check
4. **GDPR Compliance**: Add data retention policies
5. **User Consent**: Add analytics opt-out if required

## Monitoring & Alerts

Consider adding:
1. **High Cost Alerts**: Email when daily costs exceed threshold
2. **Low Conversion Alerts**: Notify when conversion drops below target
3. **Error Spike Detection**: Alert on sudden error rate increase
4. **Daily Reports**: Email digest of key metrics

## Next Steps

1. ✅ **Run Migration**: `alembic upgrade head`
2. ✅ **Test Tracking**: Open app, navigate pages, check database
3. ✅ **Add Cost Tracking**: Integrate in your pipeline code
4. ✅ **View Dashboard**: Navigate to `/analytics`
5. 📝 **Add Admin Protection**: Require admin role for dashboard
6. 📝 **Set Up Alerts**: Configure monitoring rules
7. 📝 **Export Data**: Add CSV export functionality

## Troubleshooting

### Events Not Tracking
- Check browser console for errors
- Verify API endpoint is accessible: `curl http://localhost:8000/api/analytics/track`
- Check network tab for failed requests

### Dashboard Not Loading
- Verify user is authenticated
- Check `/api/analytics/admin/dashboard` endpoint
- Look for errors in backend logs

### Cost Tracking Not Working
- Verify database connection
- Check if `CostLog` table exists
- Review backend logs for errors

### Charts Not Rendering
- Verify Chart.js is installed: `npm list chart.js`
- Check browser console for Chart.js errors
- Ensure data format matches chart expectations

## API Reference

### Track Event
```typescript
POST /api/analytics/track
{
  "event_name": "User Signed Up",
  "user_id": "uuid",
  "session_id": "session_id",
  "properties": { "method": "email" },
  "timestamp": "2025-01-08T12:00:00Z"
}
```

### Track Session
```typescript
POST /api/analytics/session
{
  "session_id": "session_id",
  "user_id": "uuid",
  "landing_page": "/",
  "utm_source": "google",
  "utm_medium": "cpc",
  "utm_campaign": "launch"
}
```

### Get Dashboard Data
```typescript
GET /api/analytics/admin/dashboard?range=30d
Authorization: Bearer <token>
```

## Database Schema

```sql
-- AnalyticsEvent
CREATE TABLE analytics_events (
    id VARCHAR(36) PRIMARY KEY,
    event_name VARCHAR(255),
    user_id VARCHAR(36),
    session_id VARCHAR(100),
    timestamp TIMESTAMP,
    properties JSON,
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    country VARCHAR(100),
    device VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100)
);

-- UserSession
CREATE TABLE user_sessions (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE,
    user_id VARCHAR(36),
    start_time TIMESTAMP,
    last_activity TIMESTAMP,
    page_views INTEGER DEFAULT 0,
    landing_page VARCHAR(500),
    referrer VARCHAR(500),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    country VARCHAR(100)
);

-- DailyMetrics
CREATE TABLE daily_metrics (
    id VARCHAR(36) PRIMARY KEY,
    date TIMESTAMP UNIQUE,
    total_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    lectures_created INTEGER DEFAULT 0,
    presentations_uploaded INTEGER DEFAULT 0,
    downloads_count INTEGER DEFAULT 0,
    new_subscriptions INTEGER DEFAULT 0,
    cancelled_subscriptions INTEGER DEFAULT 0,
    mrr FLOAT DEFAULT 0.0,
    total_costs FLOAT DEFAULT 0.0,
    ocr_costs FLOAT DEFAULT 0.0,
    ai_costs FLOAT DEFAULT 0.0,
    tts_costs FLOAT DEFAULT 0.0,
    signup_to_lecture_rate FLOAT,
    free_to_paid_rate FLOAT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- CostLog
CREATE TABLE cost_logs (
    id VARCHAR(36) PRIMARY KEY,
    operation VARCHAR(50),
    cost FLOAT,
    user_id VARCHAR(36),
    lesson_id VARCHAR(36),
    timestamp TIMESTAMP,
    metadata JSON
);
```

## Files Modified/Created

### Backend
- ✅ `backend/app/core/database.py` - Added 4 analytics models
- ✅ `backend/app/api/analytics.py` - New analytics API endpoints
- ✅ `backend/app/main.py` - Registered analytics router
- ✅ `backend/app/services/cost_tracker.py` - Cost tracking utilities
- ✅ `backend/alembic/versions/002_add_analytics_tables.py` - Migration
- ✅ `backend/requirements.txt` - Added user-agents

### Frontend
- ✅ `src/lib/analytics.ts` - Client SDK
- ✅ `src/pages/Analytics.tsx` - Admin dashboard
- ✅ `src/App.tsx` - Analytics initialization
- ✅ `package.json` - Added chart.js, react-chartjs-2, nanoid

## Support

For questions or issues:
1. Check this guide
2. Review code comments
3. Check database logs
4. Test with curl/Postman
5. Review browser console

## License

Same as your main application.
