#!/bin/bash
# Stop Slide Speaker project

echo "🛑 Stopping Slide Speaker project..."

# Stop all services
docker-compose down

echo "✅ All services stopped"

# Optional: Remove volumes (uncomment if you want to reset data)
# echo "🗑️ Removing volumes..."
# docker-compose down -v

echo "🎯 Project stopped successfully!"
