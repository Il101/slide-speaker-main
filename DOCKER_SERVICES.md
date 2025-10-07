# 🐳 Docker Services - Slide Speaker

## ✅ All Services Running

```bash
docker compose ps
```

| Service | Status | Port | URL |
|---------|--------|------|-----|
| **Frontend** | ✅ Running | 3000 | http://localhost:3000 |
| **Backend API** | ✅ Healthy | 8000 | http://localhost:8000 |
| **Celery Worker** | ✅ Healthy | - | - |
| **PostgreSQL** | ✅ Healthy | 5432 | localhost:5432 |
| **Redis** | ✅ Running | 6379 | localhost:6379 |
| **MinIO** | ✅ Healthy | 9000-9001 | http://localhost:9001 |
| **Prometheus** | ✅ Running | 9090 | http://localhost:9090 |
| **Grafana** | ✅ Running | 3001 | http://localhost:3001 |

## 🎯 Quick Access

### Main Application
```
🌐 Frontend:  http://localhost:3000
📡 Backend:   http://localhost:8000
📚 API Docs:  http://localhost:8000/docs
```

### Monitoring & Storage
```
📊 Grafana:    http://localhost:3001 (admin/admin)
📈 Prometheus: http://localhost:9090
🪣 MinIO:      http://localhost:9001 (minioadmin/minioadmin)
```

### Health Check
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"slide-speaker-api"}
```

## 📤 Upload Presentation

### Via Web UI
1. Open http://localhost:3000
2. Click "Upload" button
3. Select your .pptx or .pdf file
4. Wait for processing

### Via API (with Gemini Intelligent Pipeline)
```bash
curl -X POST "http://localhost:8000/upload?pipeline=intelligent" \
  -F "file=@your-presentation.pptx"
```

Response:
```json
{
  "lesson_id": "397c66bc-55ac-460a-80e5-312c6255262b",
  "status": "processing",
  "message": "Presentation uploaded successfully"
}
```

### Check Processing Status
```bash
LESSON_ID="your-lesson-id"
curl http://localhost:8000/lessons/$LESSON_ID/status
```

### View Processed Presentation
```
http://localhost:3000/?lesson=YOUR_LESSON_ID
```

## 🔧 Service Management

### Start All Services
```bash
docker compose up -d
```

### Stop All Services
```bash
docker compose down
```

### Restart Specific Service
```bash
docker compose restart backend
docker compose restart celery
docker compose restart frontend
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery
docker compose logs -f frontend

# Last 100 lines
docker compose logs --tail=100 celery
```

### Rebuild After Code Changes
```bash
# Backend changes
docker compose build backend celery
docker compose restart backend celery

# Frontend changes
docker compose build frontend
docker compose restart frontend
```

## 🔍 Debugging

### Check Backend Health
```bash
curl http://localhost:8000/health
```

### Test Gemini API in Container
```bash
docker compose exec celery python3 << 'EOF'
import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content("Test")
print("✅ Gemini API:", response.text)
EOF
```

### Check Database Connection
```bash
docker compose exec backend python3 -c "from app.core.database import engine; print('✅ DB Connected' if engine else '❌ DB Failed')"
```

### Check Redis Connection
```bash
docker compose exec backend python3 -c "import redis; r=redis.from_url('redis://redis:6379'); r.ping(); print('✅ Redis Connected')"
```

## 📊 Monitoring

### Prometheus Metrics
- Backend metrics: http://localhost:8000/metrics
- All targets: http://localhost:9090/targets

### Grafana Dashboards
1. Open http://localhost:3001
2. Login: admin/admin
3. Navigate to Dashboards

### Celery Tasks
```bash
# Active tasks
docker compose exec celery celery -A app.celery_app inspect active

# Registered tasks
docker compose exec celery celery -A app.celery_app inspect registered
```

## 🗄️ Database

### Connect to PostgreSQL
```bash
docker compose exec postgres psql -U slideuser -d slidedb
```

### View Tables
```sql
\dt
```

### Check Lessons
```sql
SELECT lesson_id, status, created_at FROM lessons ORDER BY created_at DESC LIMIT 10;
```

## 💾 Storage

### MinIO Console
- URL: http://localhost:9001
- Login: minioadmin / minioadmin
- Bucket: slide-speaker-storage

### List Processed Lessons (Local)
```bash
ls -lh .data/
```

## 🔐 Environment Variables

### Current Configuration
- **Pipeline**: intelligent (Gemini-powered)
- **LLM Provider**: Gemini
- **OCR Provider**: Google Document AI
- **TTS Provider**: Google Text-to-Speech
- **Storage**: Local filesystem (.data/)

### Key Variables (docker.env)
```bash
# Gemini API
GOOGLE_API_KEY=AIzaSyDNEtewj8q9qGWELrR-KS0mwcMTr4TGjA0

# Pipeline
PIPELINE=intelligent

# Providers
LLM_PROVIDER=gemini
OCR_PROVIDER=google
TTS_PROVIDER=google
```

## 📦 Data Volumes

### Persistent Data
- PostgreSQL: Docker volume `postgres_data`
- MinIO: Docker volume `minio_data`
- Redis: Docker volume `redis_data`
- Processed files: Local `.data/` directory

### Backup Data
```bash
# Backup database
docker compose exec postgres pg_dump -U slideuser slidedb > backup.sql

# Backup processed files
tar -czf data-backup.tar.gz .data/
```

## 🚀 Production Deployment

### Build Production Images
```bash
docker compose -f docker-compose.yml build
```

### Environment for Production
1. Copy `docker.env` to `.env.production`
2. Update credentials and API keys
3. Set `DEBUG=False`
4. Configure external storage (GCS/S3)

### Deploy
```bash
docker compose -f docker-compose.yml --env-file .env.production up -d
```

## 📝 Notes

### Frontend Dev Server
- Vite dev server with HMR (Hot Module Replacement)
- Auto-reloads on file changes
- Proxy API requests to backend:8000

### Backend ASGI Server
- Uvicorn with auto-reload (in dev mode)
- 4 workers in production
- Health checks enabled

### Celery Worker
- Concurrent workers: 4
- Task timeout: 30 minutes
- Results backend: Redis

## 🐛 Common Issues

### Frontend can't connect to Backend
```bash
# Check backend is running
curl http://localhost:8000/health

# Check frontend logs
docker compose logs frontend
```

### Celery tasks not processing
```bash
# Check celery worker
docker compose logs celery

# Check Redis connection
docker compose exec celery redis-cli -h redis ping
```

### Out of memory
```bash
# Check container resources
docker stats

# Increase Docker memory limit in Docker Desktop
```

### Port conflicts
```bash
# Check ports in use
lsof -i :3000
lsof -i :8000

# Stop conflicting processes or change ports in docker-compose.yml
```

## 📚 Additional Resources

- API Documentation: http://localhost:8000/docs
- Gemini Integration: `GEMINI_SUCCESS.md`
- Project Structure: `PROJECT_STRUCTURE.md`
- Architecture: `ARCHITECTURE_DIAGRAM.md`

---

**Last Updated**: 2025-10-06  
**Docker Compose Version**: 2.x  
**All Services**: ✅ Running
