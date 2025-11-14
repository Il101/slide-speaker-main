#!/bin/bash
set -e

echo "🔒 Fixing security vulnerabilities..."
echo ""

# Frontend
echo "📦 Updating frontend dependencies..."
npm audit fix
npm install vite@latest

echo ""
echo "---"
echo ""

# Backend
echo "🐍 Updating backend dependencies..."
cd backend

pip install --upgrade \
    python-multipart>=0.0.18 \
    starlette>=0.49.1 \
    fastapi>=0.115.0 \
    sentry-sdk>=1.45.1 \
    urllib3>=2.5.0

# Update requirements.txt
echo ""
echo "📝 Updating requirements.txt..."
pip freeze > requirements.txt.new
echo "✅ New requirements saved to requirements.txt.new"
echo "⚠️  Please review and manually update requirements.txt"

echo ""
echo "✅ Security updates completed!"
echo ""
echo "⚠️  IMPORTANT: Please test the application before deploying to production"
echo ""
echo "Next steps:"
echo "1. Review backend/requirements.txt.new"
echo "2. Run tests: npm test && cd backend && pytest"
echo "3. Test manually in development environment"
echo "4. Deploy to production after validation"
