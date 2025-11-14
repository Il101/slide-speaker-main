# 📊 Analytics System

Comprehensive analytics and cost tracking system for slide-speaker application.

## 🎯 Quick Links

- 🚀 **[Quick Start](./ANALYTICS_QUICK_START.md)** - Get started in 5 minutes
- 📖 **[Implementation Guide](./ANALYTICS_IMPLEMENTATION_GUIDE.md)** - Detailed documentation
- 💰 **[Cost Tracking Examples](./COST_TRACKING_INTEGRATION_EXAMPLES.md)** - Integration examples
- ✅ **[Deployment Checklist](./ANALYTICS_DEPLOYMENT_CHECKLIST.md)** - Pre-flight checks
- 📝 **[Final Summary](./ANALYTICS_FINAL_SUMMARY.md)** - What's been implemented

## ⚡ Quick Start

### 1. Run Migration
```bash
cd backend
alembic upgrade head
```

### 2. Restart Backend
```bash
docker-compose restart backend
```

### 3. Test System
```bash
./test_analytics_system.sh
```

### 4. Access Dashboard
Navigate to: `http://localhost:5173/analytics` (admin login required)

## 🌟 Features

### Event Tracking
- ✅ Page views and sessions
- ✅ User actions (login, register, upload, download)
- ✅ UTM parameters and acquisition sources
- ✅ Device, browser, OS detection
- ✅ Error tracking

### Cost Monitoring
- 💰 OCR costs (Google Vision API)
- 💰 AI generation costs (Gemini, GPT)
- 💰 TTS costs (Google TTS)
- 💰 Storage costs (GCS)
- 💰 Automatic cost calculation

### Admin Dashboard
- 📈 User growth charts
- 💵 Revenue (MRR) tracking
- 📊 Lecture activity
- 🎯 Conversion funnel
- 💡 AI-powered insights
- 📉 Cost analysis

## 📁 Structure

```
backend/
├── app/
│   ├── api/
│   │   └── analytics.py           # API endpoints
│   ├── services/
│   │   └── cost_tracker.py        # Cost tracking utilities
│   ├── core/
│   │   └── database.py            # Analytics models (updated)
│   └── alembic/
│       └── versions/
│           └── 002_*.py           # Migration

frontend/
├── src/
│   ├── lib/
│   │   └── analytics.ts           # Analytics SDK
│   ├── pages/
│   │   └── Analytics.tsx          # Dashboard
│   └── components/
│       └── Navigation.tsx         # Admin link (updated)

docs/
├── ANALYTICS_QUICK_START.md
├── ANALYTICS_IMPLEMENTATION_GUIDE.md
├── COST_TRACKING_INTEGRATION_EXAMPLES.md
├── ANALYTICS_DEPLOYMENT_CHECKLIST.md
└── ANALYTICS_FINAL_SUMMARY.md

scripts/
├── test_analytics_system.sh       # Test runner
└── commit_analytics.sh            # Commit helper
```

## 🔧 Configuration

Copy `.env.analytics.example` to `.env` and configure:

```bash
VITE_API_URL=http://localhost:8000/api
ANALYTICS_ENABLED=true
```

## 📊 Database Tables

| Table | Purpose |
|-------|---------|
| `analytics_events` | Individual event tracking |
| `user_sessions` | Session tracking with UTM |
| `daily_metrics` | Aggregated daily stats |
| `cost_logs` | Cost tracking per operation |

## 🎨 Dashboard Sections

### Overview
- Key metrics cards (users, MRR, lectures, conversion)
- User growth line chart
- Revenue line chart
- Lecture activity bar chart
- Plan distribution doughnut chart
- Top events list
- User acquisition sources

### Costs
- Total costs summary
- Cost per user/lecture
- Gross margin
- Cost breakdown by operation

### Funnel
- Signup → Email Verified → Lecture Created → Download → Paid
- Conversion rates at each step

### Insights
- AI-powered recommendations
- Warnings for low metrics
- Success highlights

## 🚀 Usage Examples

### Track Event (Frontend)
```typescript
import { trackEvent } from '@/lib/analytics';

// Track upload
trackEvent.presentationUploaded({
  fileSize: file.size,
  fileName: file.name
});

// Track error
trackEvent.error({
  errorType: 'UploadError',
  errorMessage: error.message,
  location: 'file_uploader'
});
```

### Track Cost (Backend)
```python
from app.services.cost_tracker import track_ocr_cost

await track_ocr_cost(
    db=db,
    slide_count=20,
    user_id=user_id,
    lesson_id=lesson_id
)
```

## 🧪 Testing

Run the test suite:
```bash
./test_analytics_system.sh
```

Tests check:
- ✅ Database models
- ✅ API endpoints
- ✅ Cost tracker
- ✅ Frontend files
- ✅ Dependencies

## 📈 Metrics Tracked

| Metric | Description |
|--------|-------------|
| Total Users | All registered users |
| Active Users | Active in last 30 days |
| MRR | Monthly Recurring Revenue |
| Conversion Rate | Free → Paid % |
| Cost per User | Average cost per active user |
| Cost per Lecture | Average cost per lecture |
| Gross Margin | Revenue - Costs % |

## 🔐 Security

- ✅ Admin-only dashboard access
- ✅ JWT authentication for API
- ✅ IP address anonymization ready
- ✅ GDPR opt-out ready
- ⚠️ Consider adding privacy policy

## 🐛 Troubleshooting

### Events not tracking
1. Check browser console for errors
2. Verify network requests succeed
3. Check backend logs
4. Ensure database migration ran

### Dashboard empty
1. Wait for data to accumulate
2. Check if events are being saved: `SELECT COUNT(*) FROM analytics_events;`
3. Verify admin role: `SELECT role FROM users WHERE email = 'your@email';`

### Cost tracking not working
1. Ensure DB session passed to pipeline
2. Check `cost_logs` table exists
3. Verify `track_cost` functions imported
4. Review backend logs for errors

## 📚 API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/analytics/track` | POST | Optional | Track event |
| `/api/analytics/session` | POST | Optional | Track session |
| `/api/analytics/admin/dashboard` | GET | Admin | Get dashboard data |

## 💡 Best Practices

1. **Always track errors** - helps debugging
2. **Add context to events** - include relevant IDs
3. **Don't track PII** - respect privacy
4. **Monitor costs daily** - catch spikes early
5. **Act on insights** - don't just collect data

## 🎯 Roadmap

### Phase 1 (Completed)
- ✅ Basic event tracking
- ✅ Admin dashboard
- ✅ Cost monitoring

### Phase 2 (Future)
- ⏳ Real-time dashboard updates
- ⏳ Email reports
- ⏳ Custom date ranges
- ⏳ Cohort analysis
- ⏳ A/B testing framework

### Phase 3 (Future)
- ⏳ Predictive analytics
- ⏳ Anomaly detection
- ⏳ Automated alerts
- ⏳ CSV export

## 🤝 Contributing

When adding new events:
1. Use existing `trackEvent` helpers
2. Add meaningful properties
3. Document in guide
4. Test in staging first

When adding cost tracking:
1. Follow examples in `COST_TRACKING_INTEGRATION_EXAMPLES.md`
2. Use provided utility functions
3. Always include user_id and lesson_id
4. Add relevant metadata

## 📞 Support

- 📖 Check documentation first
- 🐛 Review troubleshooting section
- 💬 Ask in team chat
- 📧 Email: support@slide-speaker.com

## ⚖️ License

Same as main project.

---

**Ready to deploy?** Follow the [Quick Start Guide](./ANALYTICS_QUICK_START.md)!
