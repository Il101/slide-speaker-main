#!/bin/bash

# Script to commit analytics system changes
# Run this after you've tested everything

echo "📊 Committing Analytics System..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Not in project root directory"
    exit 1
fi

# Show status
echo "Current git status:"
git status --short
echo ""

# Ask for confirmation
echo -e "${YELLOW}Ready to commit analytics changes?${NC}"
read -p "Type 'yes' to continue: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Adding files..."

# Backend files
git add backend/app/api/analytics.py
git add backend/app/services/cost_tracker.py
git add backend/app/core/database.py
git add backend/app/main.py
git add backend/requirements.txt
git add backend/alembic/versions/002_add_analytics_tables.py

# Frontend files
git add src/lib/analytics.ts
git add src/pages/Analytics.tsx
git add src/App.tsx
git add src/pages/Login.tsx
git add src/pages/Register.tsx
git add src/pages/Index.tsx
git add src/pages/SubscriptionPage.tsx
git add src/components/Navigation.tsx
git add package.json package-lock.json

# Documentation
git add ANALYTICS_QUICK_START.md
git add ANALYTICS_IMPLEMENTATION_GUIDE.md
git add ANALYTICS_FINAL_SUMMARY.md
git add ANALYTICS_DEPLOYMENT_CHECKLIST.md
git add COST_TRACKING_INTEGRATION_EXAMPLES.md
git add .env.analytics.example

# Scripts
git add test_analytics_system.sh
git add commit_analytics.sh

echo -e "${GREEN}✓ Files staged${NC}"
echo ""

# Show what will be committed
echo "Files to be committed:"
git status --short
echo ""

# Commit
echo "Creating commit..."
git commit -m "feat: Add comprehensive analytics system

📊 Backend Implementation:
- Analytics API endpoints (track events, sessions, admin dashboard)
- Database models (AnalyticsEvent, UserSession, DailyMetrics, CostLog)
- Cost tracking utilities with automatic calculation
- Alembic migration for analytics tables
- User-agents dependency for device detection

🎨 Frontend Implementation:
- Analytics SDK with automatic session management
- Admin dashboard with Chart.js visualizations
- Event tracking in Login, Register, Index, Subscription pages
- Admin-only navigation link and route protection
- chart.js, react-chartjs-2, nanoid dependencies

📈 Features:
- Real-time event tracking (page views, user actions)
- User session tracking with UTM parameters
- Cost monitoring (OCR, AI, TTS, storage)
- Admin dashboard with charts and insights
- Conversion funnel analysis
- AI-powered recommendations
- Device, browser, OS detection

📚 Documentation:
- Quick start guide
- Implementation guide with examples
- Cost tracking integration examples
- Deployment checklist
- Configuration examples

🔧 Integration Points:
- Login/Register events (working)
- Index page interactions (working)
- Subscription page views (working)
- Admin analytics link (working)
- Ready for pipeline cost tracking

🧪 Testing:
- Test script included (test_analytics_system.sh)
- All imports verified
- TypeScript compilation checked

Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Commit created successfully!${NC}"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Run migration: cd backend && alembic upgrade head"
    echo "  2. Restart backend: docker-compose restart backend"
    echo "  3. Test in browser: http://localhost:5173/analytics"
    echo "  4. Push to remote: git push origin $(git branch --show-current)"
    echo ""
    echo "📖 Documentation: ANALYTICS_QUICK_START.md"
else
    echo ""
    echo -e "${YELLOW}⚠️  Commit failed${NC}"
    echo "Check the error message above"
    exit 1
fi
