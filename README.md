# Slide Speaker - AI Lecturer

Transform your presentations into interactive lectures with voiceovers and visual effects.

## 📁 Project Structure

```
slide-speaker-main/
├── backend/              # Backend application (FastAPI)
├── src/                  # Frontend application (React + TypeScript)
├── docs/                 # Documentation
│   ├── reports/          # Testing and integration reports
│   └── guides/           # User guides
├── scripts/              # Utility scripts
│   ├── integration/      # Integration tests
│   ├── setup/            # Setup scripts
│   └── maintenance/      # Maintenance scripts
├── tests/                # Tests
├── .github/              # GitHub Actions CI/CD
├── docker-compose.yml    # Docker orchestration
└── README.md             # This documentation
```

## Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python
- **Queues**: Redis + Celery
- **Storage**: S3-compatible (MinIO)
- **Video**: FFmpeg for MP4 rendering
- **Data**: Mock data with placeholder slides
- **Pipelines**: Classic (OCR+LLM), Vision (Multimodal LLM), Hybrid (Vision+OCR alignment)

## Processing Pipelines

Slide Speaker supports three presentation processing modes:

### 1. Classic Pipeline (Default)
- **Technology**: OCR (Document AI) + LLM + TTS
- **Use Case**: Accurate extraction of text and elements from slides
- **Pros**: High bbox accuracy, support for tables and complex layouts
- **Cons**: Depends on OCR quality

### 2. Vision Pipeline
- **Technology**: Multimodal LLM (GPT-4o, Gemini, Claude)
- **Use Case**: Image analysis of slides for explanation generation
- **Pros**: Context understanding, high-quality explanations, OCR independence
- **Cons**: Approximate element coordinates

### 3. Hybrid Pipeline
- **Technology**: Vision LLM + OCR alignment
- **Use Case**: Combination of the best of both approaches
- **Pros**: High-quality explanations + accurate coordinates
- **Cons**: More complex processing, requires alignment tuning

### Switching Pipelines

#### Via Environment Variable
```bash
# In the .env file
PIPELINE=classic    # classic | vision | hybrid
```

#### Via Query Parameter
```bash
# When uploading a file
curl -F "file=@presentation.pdf" "http://localhost:8000/upload?pipeline=vision"

# When generating audio
curl -X POST "http://localhost:8000/lessons/{id}/generate-audio" \
  -H "X-Pipeline: hybrid"
```

#### Via Frontend
```javascript
// In URL parameters
/?lesson=demo&pipeline=vision
```

### Vision Models Configuration

```bash
# In the .env file
VISION_MODEL=x-ai/grok-4-fast:free  # xAI Grok (via OpenRouter) - default
VISION_MODEL=gpt-4o-mini        # OpenAI
VISION_MODEL=gemini-1.5-flash   # Google
VISION_MODEL=claude-3-5-sonnet  # Anthropic

# API Keys
OPENROUTER_API_KEY=your_key     # For OpenAI/Claude/Grok via OpenRouter
GEMINI_API_KEY=your_key         # For Google Gemini
```

## Quick Start

### 1. Local Development (Recommended)

#### Backend
```bash
cd backend
pip install -r requirements.txt --break-system-packages
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend
```bash
npm install
npm run dev
```

Services will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 2. Running via Docker Compose (Recommended for Sprint 3)

```bash
# Start all services
docker-compose up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redis: localhost:6379
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- MinIO API: http://localhost:9000

#### Initial MinIO Setup

1. Open MinIO Console: http://localhost:9001
2. Login with credentials: `minioadmin` / `minioadmin`
3. Create a bucket named `slide-speaker`
4. Configure access policy for public reading (optional)

## API Endpoints

### POST /upload
Uploads a file (PPTX/PDF) and creates a lesson with mock data.

**Request**: `multipart/form-data` with the file
**Response**: `{"lesson_id": "uuid"}`

### GET /lessons/{lesson_id}/manifest
Returns manifest.json with data about slides and effects.

**Response**:
```json
{
  "slides": [
    {
      "id": 1,
      "image": "/assets/lesson_id/slides/001.svg",
      "audio": "/assets/lesson_id/audio/001.mp3",
      "cues": [
        {"t0": 0.6, "t1": 2.2, "action": "highlight", "bbox": [120, 80, 980, 150]},
        {"t0": 2.3, "t1": 5.0, "action": "underline", "bbox": [140, 220, 860, 260]},
        {"t0": 5.1, "t1": 6.5, "action": "laser_move", "to": [900, 520]}
      ]
    }
  ]
}
```

### POST /lessons/{lesson_id}/export
Triggers lesson export to MP4 video with visual effects.

**Request**:
```json
{
  "lesson_id": "uuid",
  "quality": "high",
  "include_audio": true,
  "include_effects": true
}
```

**Response**: `{"status": "processing", "task_id": "uuid", "estimated_time": "5-10 minutes"}`

### GET /exports/{task_id}/status
Gets the status of the export task.

**Response**:
```json
{
  "task_id": "uuid",
  "status": "processing|completed|failed",
  "progress": 75,
  "message": "Rendering video frames",
  "download_url": "/exports/lesson_id_export.mp4"
}
```

### GET /exports/{lesson_id}/download
Downloads the final MP4 file.

**Response**: MP4 file or redirect to S3

## How It Works

1. **File Upload**: User uploads PPTX/PDF via FileUploader
2. **Processing**: Backend creates mock data (placeholder slides + empty audio)
3. **Playback**: Frontend loads manifest.json and displays an interactive player
4. **Effects**: Highlights, underlines, and a laser pointer are synced with timestamps

## Mock Data

For the MVP, the following are used:
- Placeholder slides from `public/placeholder-slide-*.svg`
- Empty audio files (placeholders)
- Predefined cue effects in manifest.json

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Backend container
│   └── .data/              # Lesson data
├── src/
│   ├── components/
│   │   ├── FileUploader.tsx # File uploading
│   │   └── Player.tsx       # Interactive player
│   ├── lib/
│   │   └── api.ts          # API client
│   └── pages/
│       └── Index.tsx       # Main page
├── docker-compose.yml      # Service orchestration
└── Dockerfile             # Frontend container
```

## Google Cloud Setup

### Google Cloud Services Setup

Slide Speaker supports integration with Google Cloud services for enhanced OCR, LLM, and TTS quality.

#### 1. Creating a Service Account

1. **Go to Google Cloud Console**: https://console.cloud.google.com
2. **Select the project** or create a new one
3. **Navigate to IAM & Admin > Service Accounts**
4. **Create a Service Account**:
   - Name: `slide-speaker-sa`
   - Description: `Service account for Slide Speaker application`
5. **Assign roles**:
   - `Document AI API User`
   - `Vertex AI User`
   - `Cloud Text-to-Speech API User`
   - `Storage Object Admin` (for GCS)
6. **Create a key**:
   - Go to the created Service Account
   - "Keys" tab → "Add Key" → "Create new key"
   - Select JSON format
   - Save the file as `gcp-sa.json`

#### 2. Document AI Setup

1. **Enable Document AI API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Document AI API" and enable it
2. **Create a processor**:
   - Go to Document AI → "Processors"
   - Create a new processor of type "Form Parser" or "OCR"
   - Copy the Processor ID

#### 3. Vertex AI Setup

1. **Enable Vertex AI API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Vertex AI API" and enable it
2. **Configure region**:
   - Choose a region (e.g., `us-central1`)

#### 4. Text-to-Speech Setup

1. **Enable Cloud Text-to-Speech API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Cloud Text-to-Speech API" and enable it

#### 5. Cloud Storage Setup (Optional)

1. **Create a bucket**:
   - Go to Cloud Storage
   - Create a bucket named `slide-speaker`
   - Configure public access for reading

#### 6. Environment Variables Setup

Create a `.env` file based on `.env.example`:

```env
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-sa.json
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1

# Provider Selection
OCR_PROVIDER=google          # google|easyocr|paddle
LLM_PROVIDER=gemini          # gemini|openai|ollama|anthropic
TTS_PROVIDER=google          # google|azure|mock
STORAGE=gcs                  # gcs|minio

# Document AI
GCP_DOC_AI_PROCESSOR_ID=your-processor-id
OCR_BATCH_SIZE=10

# Gemini LLM
GEMINI_MODEL=gemini-1.5-flash
GEMINI_LOCATION=us-central1
LLM_TEMPERATURE=0.2

# Google TTS
GOOGLE_TTS_VOICE=ru-RU-Neural2-B
GOOGLE_TTS_SPEAKING_RATE=1.0
GOOGLE_TTS_PITCH=0.0

# Google Cloud Storage
GCS_BUCKET=slide-speaker
GCS_BASE_URL=https://storage.googleapis.com/slide-speaker
```

#### 7. Key Placement

```bash
# Create a keys directory
mkdir -p keys

# Copy the Service Account key
cp path/to/your/gcp-sa.json keys/gcp-sa.json

# Set correct permissions
chmod 600 keys/gcp-sa.json
```

### Switching Providers

You can easily switch between different providers:

#### OCR Providers
- `google` - Google Cloud Document AI (best quality)
- `easyocr` - EasyOCR (local, free)
- `paddle` - PaddleOCR (alternative local)

#### LLM Providers
- `gemini` - Google Gemini (via Vertex AI)
- `openai` - OpenAI GPT
- `anthropic` - Anthropic Claude
- `ollama` - Local Ollama

#### TTS Providers
- `google` - Google Cloud Text-to-Speech
- `azure` - Azure Speech Services
- `mock` - Mock TTS (for testing)

#### Storage Providers
- `gcs` - Google Cloud Storage
- `minio` - MinIO (local S3-compatible)

### Cost and Optimization

#### Google Cloud Pricing (estimates)

- **Document AI**: $1.50 per 1000 pages
- **Vertex AI Gemini**: $0.075 per 1M tokens (input), $0.30 per 1M tokens (output)
- **Text-to-Speech**: $4.00 per 1M characters
- **Cloud Storage**: $0.020 per GB per month

#### Cost Optimization

1. **Caching**: OCR/LLM/TTS results are cached by content hash
2. **Batching**: OCR processes multiple pages at once
3. **Mock Mode**: Falls back to mock mode if keys are missing
4. **Local Alternatives**: You can use EasyOCR and Ollama for cost savings

### Google Cloud Integration Testing

```bash
# Run tests with Google Cloud
python test_google_cloud_integration.py

# Or with Docker
docker-compose up --build
python test_google_cloud_integration.py
```

## Environment Variables

Create a `.env` file:
```env
VITE_API_BASE=http://localhost:8000
```

## Roadmap

### Sprint 1: Real Document Parsing (2-3 weeks)
**Goal**: Replace mock data with actual parsing of PPTX/PDF files

- [ ] **PPTX Parsing**: High-quality slide extraction to PNG
- [ ] **PDF Parsing**: Conversion of pages to PNG images
- [ ] **Element Detection**: Automatic identification of text blocks and their bounding boxes (bbox)
- [ ] **manifest.json Generation**: Creation of structured data about slides
- [ ] **Image Optimization**: Lossless PNG compression
- [ ] **File Validation**: Checking the correctness of uploaded documents

### Sprint 2: AI Lecturer with Voiceover (3-4 weeks)
**Goal**: Add speaker notes generation and TTS with synchronization

- [ ] **LLM Integration**: Connection to OpenAI/Anthropic for speaker notes generation
- [ ] **TTS System**: High-quality text-to-speech conversion
- [ ] **Time Synchronization**: Aligning audio with visual effects
- [ ] **Edit Editor**: Interface for correcting generated content
- [ ] **Preview**: Ability to listen and edit before finalizing
- [ ] **Voice Settings**: Choice of voice, speed, pitch for TTS

### Sprint 3: Export and Stability (2-3 weeks)
**Goal**: Final MP4 export and production-ready system

- [ ] **Video Export**: MP4 generation with synchronized effects
- [ ] **Task Queues**: Background processing system for long operations
- [ ] **Storage**: Reliable storage for files and metadata
- [ ] **Monitoring**: Error logging and tracking
- [ ] **Performance**: Optimization for large presentations
- [ ] **Testing**: Unit and integration tests

## Testing

### Pipeline Smoke Tests
```bash
# Classic Pipeline test
./scripts/smoke.sh classic

# Vision Pipeline test
./scripts/smoke.sh vision

# Hybrid Pipeline test
./scripts/smoke.sh hybrid

# With custom API
API=http://localhost:8000 ./scripts/smoke.sh vision
```

### E2E Tests
```bash
cd tests/e2e
npm install
npm test
```

E2E tests automatically verify all three pipelines:
- Audio playback
- Highlight appearance
- Automatic slide transitions
- Subtitle display

### Unit Tests
```bash
cd backend
python -m pytest app/tests/
```

### Smoke Test

#### Running via Docker
```bash
# Start all services
docker-compose up --build

# Check API health
curl http://localhost:8000/health
# Expected response: {"status":"ok"}

# Check static files availability
curl http://localhost:8000/assets/demo-lesson/manifest.json
```

#### Running locally
```bash
# Backend
cd backend
pip install -r requirements.txt --break-system-packages
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (in a different terminal)
npm install
npm run dev

# Check API health
curl http://localhost:8000/health
# Expected response: {"status":"ok"}
```

#### Full Smoke Test
```bash
# Ensure all services are running
docker-compose up -d

# Run the smoke test
python smoke_test.py
```

The smoke test verifies:
- ✅ API health check
- ✅ Demo lesson manifest
- ✅ Export request
- ✅ Export status polling
- ✅ MP4 download
- ✅ Storage statistics
- ✅ Frontend accessibility

### Export test

```bash
# Start all services
docker-compose up --build

# Start export for demo-lesson
curl -X POST http://localhost:8000/lessons/demo-lesson/export
# Expected response: {"job_id": "uuid", "status": "queued"}

# Check export status (replace JOB_ID with the one obtained above)
curl "http://localhost:8000/lessons/demo-lesson/export/status?job_id=JOB_ID"
# Expected response: {"status": "processing", "progress": 50, "message": "..."}

# When status becomes "done", download MP4
curl -O http://localhost:8000/assets/demo-lesson/export.mp4
```

### Manual Testing

1. **Start services**: `docker-compose up --build`
2. **Open frontend**: http://localhost:3000
3. **Click "View Demo"** to load the demo lesson
4. **Click "Export"** to start exporting
5. **Wait for completion** (5-10 minutes)
6. **Download MP4** file

### Checking the scale-aware Player

```bash
# Start services
docker-compose up --build

# Open frontend: http://localhost:3000
# Load demo-lesson

# Test scaling:
# 1. Narrow the browser window → borders and laser stay in place
# 2. Maximize the window to full screen → elements do not "drift"
# 3. Resize the window during playback → smooth adaptation
```

**Expected behavior:**
- At different window sizes, frames and pointers match visual objects on the slide
- Laser movement is smooth, without teleports
- Elements scale proportionally to the container size

## Environment Variables

### Backend (.env)
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Queue Configuration
REDIS_URL=redis://redis:6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# S3 Storage (MinIO)
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET=slide-speaker

# Export Settings
MAX_EXPORT_SIZE_MB=500
EXPORT_RETRY_ATTEMPTS=3
EXPORT_TIMEOUT_SECONDS=1800

# AI Services (Sprint 2)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Azure TTS Configuration
AZURE_TTS_KEY=your_azure_speech_key
AZURE_TTS_REGION=your_azure_region
TTS_VOICE=ru-RU-SvetlanaNeural
TTS_SPEED=1.0
```

### Frontend (.env)
```env
VITE_API_BASE=http://localhost:8000
```

## TTS Setup

### Obtaining Azure Speech Services Keys

1. **Create a Speech Services resource in the Azure Portal**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new "Speech Services" resource
   - Choose a region (e.g., "West Europe")

2. **Get the key and region**:
   - In the "Keys and Endpoint" section, copy the key
   - Copy the region from "Location"

3. **Configure environment variables**:
   ```bash
   # Create a .env file
   cp .env.example .env
   
   # Edit .env
   AZURE_TTS_KEY=your_actual_key_here
   AZURE_TTS_REGION=your_actual_region_here
   ```

4. **Available voices**:
   - `ru-RU-SvetlanaNeural` - female Russian voice
   - `ru-RU-DmitryNeural` - male Russian voice
   - `en-US-AriaNeural` - female English voice
   - `en-US-GuyNeural` - male English voice

### Usage Example

```python
# In Python code
from workers.tts_edge import synthesize_slide_text

# Generate audio for a slide
slide_notes = [
    "Welcome to our presentation",
    "Today we will discuss artificial intelligence"
]

result = await synthesize_slide_text(slide_notes, voice="ru-RU-SvetlanaNeural", speed=1.0)
print(f"Audio file: {result['audio_file']}")
print(f"Duration: {result['total_duration']} seconds")
```

## Demo Mode

Click "View Demo" on the main page to view an example with pre-installed data.

## Final Smoke Checklist

After merging all PRs, perform the following checks:

### ✅ Basic Functionality
- [ ] `docker compose up --build` brings up backend, frontend, redis, celery, minio without errors
- [ ] `GET http://localhost:8000/health` → `{"status":"ok"}`
- [ ] `VITE_API_BASE` from `.env` affects the frontend
- [ ] `GET /assets/<lesson>/manifest.json` returns the file if it exists

### ✅ Upload and Playback
- [ ] Upload PDF/PPTX → see real slides in Player
- [ ] Real TTS voice plays (if Azure TTS is configured)
- [ ] Highlights are synced with speech (tolerance ≤200 ms)

### ✅ MP4 Export
- [ ] Export → returns link to MP4
- [ ] MP4 file downloads and plays
- [ ] Even with empty/mock audio, the video is still assembled (without sound)

### ✅ Scale-aware Player
- [ ] On window resize, frames and "laser" do not drift
- [ ] Elements stay in place at different window sizes
- [ ] Laser movement is smooth, no teleports

### Commands for checking:
```bash
# 1. Start all services
docker-compose up --build

# 2. Check API health
curl http://localhost:8000/health

# 3. Check static files
curl http://localhost:8000/assets/demo-lesson/manifest.json

# 4. Export test
curl -X POST http://localhost:8000/lessons/demo-lesson/export
# Get the job_id from the response, then:
curl "http://localhost:8000/lessons/demo-lesson/export/status?job_id=YOUR_JOB_ID"

# 5. Frontend test
# Open http://localhost:3000
# Click "View Demo"
# Check window scaling
```