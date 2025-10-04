#!/bin/bash
# Build and run Slide Speaker project with Docker

set -e

echo "🚀 Building Slide Speaker project..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/.data/uploads
mkdir -p backend/.data/assets
mkdir -p backend/.data/exports
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend is not responding"
fi

# Check frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend is not responding"
fi

# Check Prometheus
if curl -f http://localhost:9090 > /dev/null 2>&1; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus is not responding"
fi

# Check Grafana
if curl -f http://localhost:3001 > /dev/null 2>&1; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana is not responding"
fi

echo ""
echo "🎉 Slide Speaker is now running!"
echo ""
echo "📊 Services:"
echo "  Frontend:     http://localhost:3000"
echo "  Backend API:  http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Prometheus:   http://localhost:9090"
echo "  Grafana:      http://localhost:3001 (admin/admin123)"
echo "  MinIO:        http://localhost:9001 (minioadmin/minioadmin123)"
echo ""
echo "🔧 Management commands:"
echo "  View logs:    docker-compose logs -f [service]"
echo "  Stop all:     docker-compose down"
echo "  Restart:      docker-compose restart [service]"
echo "  Scale:        docker-compose up -d --scale celery=3"
echo ""
echo "📈 Monitoring:"
echo "  Metrics:      http://localhost:8000/metrics"
echo "  Health:       http://localhost:8000/health"
echo ""
echo "🔐 Default credentials:"
echo "  Admin user:   admin@example.com / adminpassword"
echo "  Regular user: user@example.com / userpassword"
echo "  Grafana:      admin / admin123"
echo "  MinIO:        minioadmin / minioadmin123"
