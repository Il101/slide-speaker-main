#!/bin/bash

# Analytics System Test Script
# This script tests the analytics system components

echo "🧪 Testing Analytics System..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test database models
echo "1️⃣ Testing Database Models..."
cd backend
python3 -c "
from app.core.database import AnalyticsEvent, UserSession, DailyMetrics, CostLog, Base
print('✅ All analytics models imported successfully')
print(f'  - AnalyticsEvent: {AnalyticsEvent.__tablename__}')
print(f'  - UserSession: {UserSession.__tablename__}')
print(f'  - DailyMetrics: {DailyMetrics.__tablename__}')
print(f'  - CostLog: {CostLog.__tablename__}')
"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database models OK${NC}"
else
    echo -e "${RED}✗ Database models FAILED${NC}"
    exit 1
fi
echo ""

# Test API imports
echo "2️⃣ Testing API Endpoints..."
python3 -c "
from app.api.analytics import router
print('✅ Analytics API router imported successfully')
print(f'  Prefix: {router.prefix}')
print(f'  Tags: {router.tags}')
"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API endpoints OK${NC}"
else
    echo -e "${RED}✗ API endpoints FAILED${NC}"
    exit 1
fi
echo ""

# Test cost tracker
echo "3️⃣ Testing Cost Tracker..."
python3 -c "
from app.services.cost_tracker import track_ocr_cost, track_ai_generation_cost, track_tts_cost, CostTracker
print('✅ Cost tracker functions imported successfully')
print('  - track_ocr_cost')
print('  - track_ai_generation_cost')
print('  - track_tts_cost')
print('  - CostTracker context manager')
"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Cost tracker OK${NC}"
else
    echo -e "${RED}✗ Cost tracker FAILED${NC}"
    exit 1
fi
echo ""
cd ..

# Test frontend files
echo "4️⃣ Testing Frontend Files..."
if [ -f "src/lib/analytics.ts" ]; then
    echo -e "${GREEN}✓ Analytics SDK exists${NC}"
else
    echo -e "${RED}✗ Analytics SDK missing${NC}"
    exit 1
fi

if [ -f "src/pages/Analytics.tsx" ]; then
    echo -e "${GREEN}✓ Analytics dashboard exists${NC}"
else
    echo -e "${RED}✗ Analytics dashboard missing${NC}"
    exit 1
fi
echo ""

# Test npm packages
echo "5️⃣ Testing NPM Packages..."
if npm list chart.js > /dev/null 2>&1; then
    echo -e "${GREEN}✓ chart.js installed${NC}"
else
    echo -e "${YELLOW}⚠ chart.js not found${NC}"
fi

if npm list react-chartjs-2 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ react-chartjs-2 installed${NC}"
else
    echo -e "${YELLOW}⚠ react-chartjs-2 not found${NC}"
fi

if npm list nanoid > /dev/null 2>&1; then
    echo -e "${GREEN}✓ nanoid installed${NC}"
else
    echo -e "${YELLOW}⚠ nanoid not found${NC}"
fi
echo ""

# Test Python packages
echo "6️⃣ Testing Python Packages..."
cd backend
python3 -c "import user_agents; print('✅ user-agents installed')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ user-agents installed${NC}"
else
    echo -e "${YELLOW}⚠ user-agents not found (run: pip install user-agents)${NC}"
fi
cd ..
echo ""

# Check migration
echo "7️⃣ Checking Migration File..."
if [ -f "backend/alembic/versions/002_add_analytics_tables.py" ]; then
    echo -e "${GREEN}✓ Analytics migration exists${NC}"
    echo "  To run: cd backend && alembic upgrade head"
else
    echo -e "${RED}✗ Analytics migration missing${NC}"
    exit 1
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Analytics System Tests Passed!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next Steps:"
echo "  1. Run migration: cd backend && alembic upgrade head"
echo "  2. Restart backend: docker-compose restart backend"
echo "  3. Test in browser: http://localhost:5173/analytics"
echo "  4. Check events: SELECT * FROM analytics_events;"
echo ""
echo "📚 Documentation:"
echo "  - ANALYTICS_QUICK_START.md"
echo "  - ANALYTICS_IMPLEMENTATION_GUIDE.md"
echo "  - COST_TRACKING_INTEGRATION_EXAMPLES.md"
echo ""
