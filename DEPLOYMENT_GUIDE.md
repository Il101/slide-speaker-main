# Slide Speaker - Deployment Guide

## 🎯 Project Overview

Slide Speaker - это MVP «ИИ-лектор» для превращения презентаций в интерактивные лекции с озвучкой и визуальными эффектами.

## 📋 Roadmap Status

✅ **Спринт 1**: Реальный парсинг PPTX/PDF → PNG + bbox + manifest.json  
🔄 **Спринт 2**: LLM speaker notes + TTS с таймингами → выравнивание → редактор правок  
🔄 **Спринт 3**: Экспорт в MP4 + очереди/хранилище + стабильность  

## 🏗️ Project Structure

```
slide-speaker/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuration and exceptions
│   │   ├── models/         # Pydantic schemas
│   │   ├── services/       # Business logic by sprint
│   │   │   ├── sprint1/   # Document parsing
│   │   │   ├── sprint2/   # AI generation
│   │   │   └── sprint3/   # Video export
│   │   ├── main.py        # FastAPI application
│   │   └── tasks.py      # Celery background tasks
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile        # Backend container
│   └── main.py          # Legacy entry point
├── src/                  # Frontend (React + Vite + Tailwind)
├── docker-compose.yml   # Full stack orchestration
├── github_issues.json  # Generated GitHub issues
└── README.md           # Updated with roadmap
```

## 🚀 Quick Start

### 1. Local Development

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

#### Frontend Setup
```bash
npm install
npm run dev
```

#### Redis (for Sprint 3)
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 2. Docker Compose (Recommended)

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up --build
```

Services will be available:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redis: localhost:6379

## 🔧 Configuration

### Environment Variables (.env)

```env
# AI Services (Sprint 2)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
TTS_SERVICE=openai

# Queue Configuration (Sprint 3)
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Video Export (Sprint 3)
FFMPEG_PATH=ffmpeg
VIDEO_QUALITY=high
```

## 📊 API Endpoints

### Sprint 1: Document Processing
- `POST /upload` - Upload PPTX/PDF files
- `GET /lessons/{lesson_id}/manifest` - Get lesson manifest

### Sprint 2: AI Generation
- `POST /lessons/{lesson_id}/generate-speaker-notes` - Generate speaker notes
- `POST /lessons/{lesson_id}/generate-audio` - Generate TTS audio
- `GET /voices` - Get available TTS voices
- `POST /lessons/{lesson_id}/edit` - Edit generated content
- `GET /lessons/{lesson_id}/preview/{slide_id}` - Preview changes

### Sprint 3: Video Export
- `POST /lessons/{lesson_id}/export` - Start video export
- `GET /exports/{task_id}/status` - Get export status
- `GET /exports/{lesson_id}/download` - Download exported video

## 🎫 GitHub Issues

16 GitHub issues have been generated and saved to `github_issues.json`:

- **3 Epics** (one per sprint)
- **13 Detailed Issues** with acceptance criteria
- **Estimated Timeline**: 7-10 weeks total

To create issues on GitHub:
1. Go to repository → Issues tab
2. Click "New issue"
3. Copy content from `github_issues.json`
4. Or use GitHub CLI: `gh issue create --title "Title" --body "Body"`

## 🧪 Testing

### Backend Testing
```bash
cd backend
python3 -m pytest tests/ -v
```

### Frontend Testing
```bash
npm test
```

### Integration Testing
```bash
# Test API endpoints
python3 test_api.py
```

## 📈 Development Workflow

### Sprint 1 (2-3 weeks)
1. Implement PPTX parsing with python-pptx
2. Implement PDF parsing with PyMuPDF/pdf2image
3. Add OCR text detection with Tesseract/EasyOCR
4. Generate structured manifest.json files

### Sprint 2 (3-4 weeks)
1. Integrate OpenAI/Anthropic for speaker notes
2. Implement TTS with multiple voices
3. Create timing synchronization system
4. Build content editing interface

### Sprint 3 (2-3 weeks)
1. Implement MP4 export with FFmpeg
2. Add Celery/Redis background processing
3. Create reliable file storage system
4. Add monitoring and comprehensive testing

## 🔍 Monitoring

### Health Checks
- `GET /health` - API health status
- `GET /admin/storage-stats` - Storage usage statistics
- `POST /admin/cleanup` - Clean up old files

### Logging
- Application logs: `backend/logs/`
- Error tracking: Integrated exception handling
- Performance monitoring: Built-in timing

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Redis Connection**: Make sure Redis is running
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

3. **File Permissions**: Check .data directory permissions
   ```bash
   chmod -R 755 backend/.data
   ```

4. **Port Conflicts**: Change ports in docker-compose.yml if needed

### Debug Mode
```bash
# Backend debug
cd backend
PYTHONPATH=. python3 -m uvicorn app.main:app --reload --log-level debug

# Frontend debug
npm run dev -- --debug
```

## 📚 Next Steps

1. **Review GitHub Issues**: Check `github_issues.json` for detailed tasks
2. **Set up Environment**: Copy `.env.example` to `.env` and configure
3. **Start Development**: Begin with Sprint 1 issues
4. **Monitor Progress**: Use GitHub project boards for tracking

## 🤝 Contributing

1. Create feature branch from main
2. Implement changes following sprint structure
3. Add tests for new functionality
4. Update documentation as needed
5. Submit pull request with issue reference

---

**Ready to start development!** 🚀

The project is now structured for all 3 sprints with a clear roadmap, comprehensive backend architecture, and detailed GitHub issues for tracking progress.