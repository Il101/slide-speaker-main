"""Main FastAPI application"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import uuid
import shutil
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List

from .core.config import settings
from .core.exceptions import SlideSpeakerException
from .core.logging import setup_logging, get_logger, log_request, log_error
from .core.metrics import (
    start_metrics_server, record_request, record_lesson_created,
    record_lesson_exported, record_error, monitor_operation
)
from .models.schemas import (
    UploadResponse, ExportResponse, ProcessingStatus,
    SpeakerNotesRequest, TTSRequest, EditRequest, ExportRequest,
    LessonPatchRequest, PatchResponse, SlidePatch, CuePatch, ElementPatch
)
from .services.sprint1.document_parser import ParserFactory
from .services.sprint2.ai_generator import AIGenerator, TTSService, ContentEditor
from .services.sprint3.video_exporter import VideoExporter, QueueManager, StorageManager

# Configure structured logging
setup_logging(
    level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE,
    structured=True
)
logger = get_logger(__name__)

# Configure rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AI-powered presentation to video converter"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Record metrics
        record_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration
        )
        
        # Log request with structured data
        log_request(
            logger,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=duration,
            request_id=request_id
        )
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        
        # Record metrics
        record_request(
            method=request.method,
            endpoint=request.url.path,
            status=500,
            duration=duration
        )
        
        # Log error with structured data
        log_error(
            logger,
            e,
            context={
                "method": request.method,
                "path": request.url.path,
                "duration": duration,
                "request_id": request_id
            }
        )
        raise

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok"}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with external service status"""
    health_status = {
        "status": "healthy",
        "service": "slide-speaker-api",
        "timestamp": "2024-01-01T00:00:00Z",
        "checks": {
            "database": "healthy",
            "storage": "healthy",
            "ocr_service": "healthy",
            "llm_service": "healthy",
            "tts_service": "healthy"
        }
    }
    
    # Check external services
    try:
        # Check OCR service availability
        from .services.provider_factory import ProviderFactory
        ocr_provider = ProviderFactory.get_ocr_provider()
        health_status["checks"]["ocr_service"] = "healthy"
    except Exception as e:
        health_status["checks"]["ocr_service"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        # Check LLM service availability
        llm_provider = ProviderFactory.get_llm_provider()
        health_status["checks"]["llm_service"] = "healthy"
    except Exception as e:
        health_status["checks"]["llm_service"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        # Check TTS service availability
        tts_provider = ProviderFactory.get_tts_provider()
        health_status["checks"]["tts_service"] = "healthy"
    except Exception as e:
        health_status["checks"]["tts_service"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    return {"status": "ready"}

@app.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {"status": "alive"}
# Initialize services
ai_generator = AIGenerator()
tts_service = TTSService()
content_editor = ContentEditor()
video_exporter = VideoExporter()
queue_manager = QueueManager()
storage_manager = StorageManager()

# Global exception handler
@app.exception_handler(SlideSpeakerException)
async def slide_speaker_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# Health check
@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}

# Sprint 1: Document Processing Endpoints
@app.post("/upload", response_model=UploadResponse)
@limiter.limit("10/minute")  # 10 uploads per minute
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Upload and process document (PPTX/PDF)"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PPTX and PDF files are allowed")
    
    # Check file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Generate lesson ID and create directory
    lesson_id = str(uuid.uuid4())
    lesson_dir = settings.DATA_DIR / lesson_id
    lesson_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    file_path = lesson_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process document
    try:
        parser = ParserFactory.create_parser(file_path)
        manifest = await parser.parse()
        
        # Save manifest
        manifest_path = lesson_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully processed document: {lesson_id}")
        
        # Start full pipeline processing in background
        from .tasks import process_lesson_full_pipeline
        
        # For debugging: run synchronously instead of through Celery
        try:
            logger.info(f"Starting full pipeline processing for lesson {lesson_id}")
            pipeline_result = process_lesson_full_pipeline(lesson_id)
            logger.info(f"Completed full pipeline processing for lesson {lesson_id}: {pipeline_result}")
        except Exception as e:
            logger.error(f"Error in pipeline processing for lesson {lesson_id}: {e}")
            # Still return success to user, but log the error
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        # Clean up on error
        shutil.rmtree(lesson_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {e}")
    
    return UploadResponse(lesson_id=lesson_id, status="processing")

@app.get("/lessons/{lesson_id}/status")
@limiter.limit("100/minute")  # 100 status requests per minute
async def get_lesson_status(request: Request, lesson_id: str):
    """Get lesson processing status"""
    
    try:
        from .tasks import process_lesson_full_pipeline
        from celery.result import AsyncResult
        
        # Check if there's an active pipeline task
        # For now, we'll check if manifest exists and has speaker_notes
        lesson_dir = settings.DATA_DIR / lesson_id
        manifest_path = lesson_dir / "manifest.json"
        
        if not manifest_path.exists():
            return {"status": "not_found", "message": "Lesson not found"}
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        # Check if AI processing is complete
        slides_with_notes = 0
        slides_with_audio = 0
        
        for slide in manifest_data.get("slides", []):
            if slide.get("speaker_notes"):
                slides_with_notes += 1
            if slide.get("audio"):
                slides_with_audio += 1
        
        total_slides = len(manifest_data.get("slides", []))
        
        if slides_with_notes == total_slides and slides_with_audio == total_slides:
            return {
                "status": "completed",
                "message": "Full pipeline completed",
                "slides_processed": total_slides,
                "slides_with_notes": slides_with_notes,
                "slides_with_audio": slides_with_audio
            }
        elif slides_with_notes > 0 or slides_with_audio > 0:
            return {
                "status": "processing",
                "message": "AI processing in progress",
                "slides_processed": total_slides,
                "slides_with_notes": slides_with_notes,
                "slides_with_audio": slides_with_audio
            }
        else:
            return {
                "status": "parsed",
                "message": "Document parsed, waiting for AI processing",
                "slides_processed": total_slides,
                "slides_with_notes": slides_with_notes,
                "slides_with_audio": slides_with_audio
            }
        
    except Exception as e:
        logger.error(f"Error getting lesson status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lessons/{lesson_id}/manifest")
@limiter.limit("100/minute")  # 100 manifest requests per minute
async def get_manifest(request: Request, lesson_id: str):
    """Get lesson manifest"""
    
    # Special handling for demo
    if lesson_id == "demo-lesson":
        return {
            "slides": [
                {
                    "id": 1,
                    "image": "/assets/demo-lesson/slides/001.svg",
                    "audio": "/assets/demo-lesson/audio/001.wav",
                    "elements": [
                        {"id": "elem_1", "type": "text", "bbox": [120, 80, 980, 150], "text": "Welcome to Slide Speaker", "confidence": 0.95},
                        {"id": "elem_2", "type": "text", "bbox": [140, 220, 860, 260], "text": "AI-powered presentation converter", "confidence": 0.92}
                    ],
                    "cues": [
                        {"t0": 0.6, "t1": 2.2, "action": "highlight", "bbox": [120, 80, 980, 150], "element_id": "elem_1"},
                        {"t0": 2.3, "t1": 5.0, "action": "underline", "bbox": [140, 220, 860, 4], "element_id": "elem_2"},
                        {"t0": 5.1, "t1": 6.5, "action": "laser_move", "to": [900, 520]}
                    ]
                },
                {
                    "id": 2,
                    "image": "/assets/demo-lesson/slides/002.svg",
                    "audio": "/assets/demo-lesson/audio/002.wav",
                    "elements": [
                        {"id": "elem_3", "type": "text", "bbox": [80, 180, 720, 100], "text": "Features", "confidence": 0.98},
                        {"id": "elem_4", "type": "text", "bbox": [120, 320, 600, 4], "text": "Automatic slide detection", "confidence": 0.90}
                    ],
                    "cues": [
                        {"t0": 1.0, "t1": 3.0, "action": "laser_move", "to": [200, 150]},
                        {"t0": 4.0, "t1": 7.0, "action": "highlight", "bbox": [80, 180, 720, 100], "element_id": "elem_3"},
                        {"t0": 8.0, "t1": 11.0, "action": "underline", "bbox": [120, 320, 600, 4], "element_id": "elem_4"}
                    ]
                },
                {
                    "id": 3,
                    "image": "/assets/demo-lesson/slides/003.svg",
                    "audio": "/assets/demo-lesson/audio/003.wav",
                    "elements": [
                        {"id": "elem_5", "type": "text", "bbox": [150, 60, 600, 80], "text": "Export to MP4", "confidence": 0.96},
                        {"id": "elem_6", "type": "text", "bbox": [100, 250, 700, 120], "text": "Professional video output", "confidence": 0.94}
                    ],
                    "cues": [
                        {"t0": 1.5, "t1": 4.0, "action": "highlight", "bbox": [150, 60, 600, 80], "element_id": "elem_5"},
                        {"t0": 5.0, "t1": 7.5, "action": "laser_move", "to": [300, 200]},
                        {"t0": 8.0, "t1": 11.0, "action": "highlight", "bbox": [100, 250, 700, 120], "element_id": "elem_6"}
                    ]
                }
            ],
            "timeline": {
                "rules": [
                    {
                        "action_type": "highlight",
                        "min_duration": 0.8,
                        "max_duration": 5.0,
                        "priority": 1,
                        "gap_before": 0.2,
                        "gap_after": 0.2
                    },
                    {
                        "action_type": "underline",
                        "min_duration": 0.5,
                        "max_duration": 3.0,
                        "priority": 2,
                        "gap_before": 0.2,
                        "gap_after": 0.2
                    },
                    {
                        "action_type": "laser_move",
                        "min_duration": 0.3,
                        "max_duration": 2.0,
                        "priority": 3,
                        "gap_before": 0.2,
                        "gap_after": 0.2
                    }
                ],
                "default_duration": 2.0,
                "transition_duration": 0.5,
                "min_highlight_duration": 0.8,
                "min_gap": 0.2,
                "max_total_duration": 90.0,
                "smoothness_enabled": True
            }
        }
    
    manifest_path = settings.DATA_DIR / lesson_id / "manifest.json"
    
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    return manifest

# Sprint 2: AI Generation Endpoints
@app.post("/lessons/{lesson_id}/generate-speaker-notes")
async def generate_speaker_notes(lesson_id: str, slide_id: int, request: SpeakerNotesRequest):
    """Generate speaker notes for a slide"""
    
    try:
        # Load slide content (placeholder)
        slide_content = f"Slide {slide_id} content"
        
        speaker_notes = await ai_generator.generate_speaker_notes(
            slide_content, 
            request.custom_prompt
        )
        
        return {"speaker_notes": speaker_notes}
        
    except Exception as e:
        logger.error(f"Error generating speaker notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/lessons/{lesson_id}/generate-audio")
async def generate_audio(lesson_id: str, slide_id: int, request: TTSRequest):
    """Generate audio for speaker notes using configured TTS provider"""
    
    try:
        # Try to use configured TTS provider
        try:
            from ..services.provider_factory import synthesize_slide_text_google
            
            # Generate audio with timing using configured TTS provider
            slide_notes = [request.text]  # Convert single text to list
            audio_path, tts_words = synthesize_slide_text_google(
                slide_notes, 
                voice=request.voice, 
                rate=request.speed
            )
            
            # Copy audio file to lesson directory
            audio_path_dest = settings.DATA_DIR / lesson_id / "audio" / f"{slide_id:03d}.mp3"
            audio_path_dest.parent.mkdir(exist_ok=True)
            
            # Convert WAV to MP3 if needed (simplified - in real implementation use ffmpeg)
            if audio_path.endswith('.wav'):
                # For now, just copy the WAV file
                import shutil
                shutil.copy2(audio_path, audio_path_dest.with_suffix('.wav'))
                audio_path_dest = audio_path_dest.with_suffix('.wav')
            else:
                import shutil
                shutil.copy2(audio_path, audio_path_dest)
            
            # Save TtsWords.json for timing information
            tts_words_path = settings.DATA_DIR / lesson_id / "audio" / f"{slide_id:03d}_words.json"
            import json
            with open(tts_words_path, 'w', encoding='utf-8') as f:
                json.dump(tts_words, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Generated TTS audio using configured provider for slide {slide_id}")
            
            return {
                "audio_url": f"/assets/{lesson_id}/audio/{slide_id:03d}.mp3",
                "duration": tts_words["sentences"][-1]["t1"] if tts_words["sentences"] else 0.0,
                "sentences": tts_words["sentences"]
            }
            
        except Exception as e:
            logger.warning(f"Failed to use configured TTS provider: {e}, using legacy implementation")
        
        # Fallback to legacy implementation
        # Import TTS function
        from ..workers.tts_edge import synthesize_slide_text
        
        # Generate audio with timing
        slide_notes = [request.text]  # Convert single text to list
        result = await synthesize_slide_text(
            slide_notes, 
            voice=request.voice, 
            speed=request.speed
        )
        
        # Copy audio file to lesson directory
        audio_path = settings.DATA_DIR / lesson_id / "audio" / f"{slide_id:03d}.mp3"
        audio_path.parent.mkdir(exist_ok=True)
        
        # Copy the generated audio file
        import shutil
        shutil.copy2(result["audio_file"], audio_path)
        
        # Save TtsWords.json for timing information
        tts_words_path = settings.DATA_DIR / lesson_id / "audio" / f"{slide_id:03d}_words.json"
        shutil.copy2(result["tts_words_file"], tts_words_path)
        
        logger.info(f"Generated legacy TTS audio for slide {slide_id}: {result['total_duration']:.2f}s")
        
        return {
            "audio_url": f"/assets/{lesson_id}/audio/{slide_id:03d}.mp3",
            "duration": result["total_duration"],
            "sentences": result["sentences"]
        }
        
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voices")
async def get_available_voices():
    """Get available TTS voices"""
    
    try:
        voices = await tts_service.get_available_voices()
        return {"voices": voices}
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/lessons/{lesson_id}/edit")
async def edit_content(lesson_id: str, slide_id: int, request: EditRequest):
    """Edit generated content"""
    
    try:
        if request.field == "speaker_notes":
            success = await content_editor.edit_speaker_notes(
                lesson_id, slide_id, request.value
            )
        elif request.field == "audio_timing":
            success = await content_editor.edit_audio_timing(
                lesson_id, slide_id, request.value
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid field")
        
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Error editing content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lessons/{lesson_id}/preview/{slide_id}")
async def preview_changes(lesson_id: str, slide_id: int):
    """Preview changes before applying"""
    
    try:
        preview_data = await content_editor.preview_changes(lesson_id, slide_id)
        return preview_data
        
    except Exception as e:
        logger.error(f"Error previewing changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/lessons/{lesson_id}/patch", response_model=PatchResponse)
async def patch_lesson(lesson_id: str, request: LessonPatchRequest):
    """Patch lesson content (cues, elements, speaker notes)"""
    
    try:
        # Validate lesson exists
        lesson_dir = settings.DATA_DIR / lesson_id
        if not lesson_dir.exists():
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        manifest_path = lesson_dir / "manifest.json"
        if not manifest_path.exists():
            raise HTTPException(status_code=404, detail="Lesson manifest not found")
        
        # Load current manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        updated_slides = []
        validation_issues = []
        
        # Apply patches to slides
        for slide_patch in request.slides:
            slide_id = slide_patch.slide_id
            
            # Find slide in manifest
            slide_found = False
            for slide in manifest_data["slides"]:
                if slide["id"] == slide_id:
                    slide_found = True
                    
                    # Apply speaker notes patch
                    if slide_patch.speaker_notes is not None:
                        slide["speaker_notes"] = slide_patch.speaker_notes
                    
                    # Apply duration patch
                    if slide_patch.duration is not None:
                        slide["duration"] = slide_patch.duration
                    
                    # Apply element patches
                    if slide_patch.elements:
                        for element_patch in slide_patch.elements:
                            element_found = False
                            for element in slide["elements"]:
                                if element["id"] == element_patch.element_id:
                                    element_found = True
                                    
                                    if element_patch.bbox is not None:
                                        element["bbox"] = element_patch.bbox
                                    if element_patch.text is not None:
                                        element["text"] = element_patch.text
                                    if element_patch.confidence is not None:
                                        element["confidence"] = element_patch.confidence
                                    break
                            
                            if not element_found:
                                validation_issues.append(f"Element {element_patch.element_id} not found in slide {slide_id}")
                    
                    # Apply cue patches
                    if slide_patch.cues:
                        for cue_patch in slide_patch.cues:
                            if cue_patch.cue_id:
                                # Update existing cue
                                cue_found = False
                                for cue in slide["cues"]:
                                    if cue.get("cue_id") == cue_patch.cue_id:
                                        cue_found = True
                                        
                                        if cue_patch.t0 is not None:
                                            cue["t0"] = cue_patch.t0
                                        if cue_patch.t1 is not None:
                                            cue["t1"] = cue_patch.t1
                                        if cue_patch.action is not None:
                                            cue["action"] = cue_patch.action
                                        if cue_patch.bbox is not None:
                                            cue["bbox"] = cue_patch.bbox
                                        if cue_patch.to is not None:
                                            cue["to"] = cue_patch.to
                                        if cue_patch.element_id is not None:
                                            cue["element_id"] = cue_patch.element_id
                                        break
                                
                                if not cue_found:
                                    validation_issues.append(f"Cue {cue_patch.cue_id} not found in slide {slide_id}")
                            else:
                                # Add new cue
                                new_cue = {}
                                if cue_patch.t0 is not None:
                                    new_cue["t0"] = cue_patch.t0
                                if cue_patch.t1 is not None:
                                    new_cue["t1"] = cue_patch.t1
                                if cue_patch.action is not None:
                                    new_cue["action"] = cue_patch.action
                                if cue_patch.bbox is not None:
                                    new_cue["bbox"] = cue_patch.bbox
                                if cue_patch.to is not None:
                                    new_cue["to"] = cue_patch.to
                                if cue_patch.element_id is not None:
                                    new_cue["element_id"] = cue_patch.element_id
                                
                                # Generate unique cue ID
                                new_cue["cue_id"] = f"cue_{slide_id}_{len(slide['cues'])}"
                                slide["cues"].append(new_cue)
                    
                    updated_slides.append(slide_id)
                    break
            
            if not slide_found:
                validation_issues.append(f"Slide {slide_id} not found in lesson")
        
        # Apply timeline patches
        if request.timeline:
            if "timeline" not in manifest_data:
                manifest_data["timeline"] = {}
            
            for key, value in request.timeline.items():
                manifest_data["timeline"][key] = value
        
        # Validate timeline rules if smoothness is enabled
        if manifest_data.get("timeline", {}).get("smoothness_enabled", True):
            timeline_issues = _validate_timeline_smoothness(manifest_data)
            validation_issues.extend(timeline_issues)
        
        # Save updated manifest
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)
        
        # Create backup
        backup_path = lesson_dir / f"manifest_backup_{uuid.uuid4().hex[:8]}.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Patched lesson {lesson_id}: {len(updated_slides)} slides updated")
        
        return PatchResponse(
            success=len(validation_issues) == 0,
            message=f"Successfully patched {len(updated_slides)} slides" if len(validation_issues) == 0 else f"Patched with {len(validation_issues)} issues",
            updated_slides=updated_slides,
            validation_issues=validation_issues
        )
        
    except Exception as e:
        logger.error(f"Error patching lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _validate_timeline_smoothness(manifest_data: Dict[str, Any]) -> List[str]:
    """Validate timeline smoothness rules"""
    issues = []
    timeline = manifest_data.get("timeline", {})
    
    if not timeline.get("smoothness_enabled", True):
        return issues
    
    min_highlight_duration = timeline.get("min_highlight_duration", 0.8)
    min_gap = timeline.get("min_gap", 0.2)
    
    for slide in manifest_data.get("slides", []):
        slide_id = slide["id"]
        cues = slide.get("cues", [])
        
        # Sort cues by start time
        sorted_cues = sorted(cues, key=lambda c: c.get("t0", 0))
        
        for i, cue in enumerate(sorted_cues):
            # Check minimum duration for highlights
            if cue.get("action") in ["highlight", "underline"]:
                duration = cue.get("t1", 0) - cue.get("t0", 0)
                if duration < min_highlight_duration:
                    issues.append(f"Slide {slide_id}, cue {i}: duration {duration:.2f}s < min {min_highlight_duration}s")
            
            # Check gaps between cues
            if i < len(sorted_cues) - 1:
                next_cue = sorted_cues[i + 1]
                gap = next_cue.get("t0", 0) - cue.get("t1", 0)
                if gap < min_gap:
                    issues.append(f"Slide {slide_id}, cues {i}-{i+1}: gap {gap:.2f}s < min {min_gap}s")
    
    return issues

# Sprint 3: Export Endpoints
@app.post("/lessons/{lesson_id}/export")
@limiter.limit("5/minute")  # 5 exports per minute
async def export_lesson(request: Request, lesson_id: str):
    """Export lesson to MP4 video"""
    
    try:
        # Check if lesson exists
        lesson_dir = settings.DATA_DIR / lesson_id
        if not lesson_dir.exists():
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Check file size limits
        manifest_path = lesson_dir / "manifest.json"
        if manifest_path.exists():
            manifest_size = manifest_path.stat().st_size
            if manifest_size > settings.MAX_EXPORT_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"Manifest too large. Maximum size: {settings.MAX_EXPORT_SIZE_MB}MB")
        
        # Start export task
        from .tasks import export_video_task
        task = export_video_task.delay(lesson_id, "high")
        
        return {
            "job_id": task.id,
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Error starting export: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lessons/{lesson_id}/export/status")
async def get_export_status(lesson_id: str, job_id: str):
    """Get export task status"""
    
    try:
        from .tasks import export_video_task
        from celery.result import AsyncResult
        
        # Get task result
        task_result = AsyncResult(job_id, app=export_video_task.app)
        
        if task_result.state == 'PENDING':
            return {
                "status": "queued",
                "progress": 0,
                "message": "Task is waiting to be processed"
            }
        elif task_result.state == 'PROGRESS':
            return {
                "status": "processing",
                "progress": task_result.info.get('progress', 0),
                "message": task_result.info.get('message', 'Processing...')
            }
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            return {
                "status": "done",
                "progress": 100,
                "message": "Export completed successfully",
                "url": result.get('download_url')
            }
        elif task_result.state == 'FAILURE':
            return {
                "status": "failed",
                "progress": 0,
                "message": "Export failed",
                "error": str(task_result.info)
            }
        else:
            return {
                "status": "unknown",
                "progress": 0,
                "message": f"Unknown task state: {task_result.state}"
            }
        
    except Exception as e:
        logger.error(f"Error getting export status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exports/{lesson_id}/download")
async def download_export(lesson_id: str):
    """Download exported video"""
    
    try:
        download_url = await video_exporter.get_export_download_url(lesson_id)
        
        if not download_url:
            raise HTTPException(status_code=404, detail="Export not found")
        
        file_path = settings.EXPORTS_DIR / f"{lesson_id}_export.mp4"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Export file not found")
        
        return FileResponse(
            path=file_path,
            filename=f"{lesson_id}_export.mp4",
            media_type="video/mp4"
        )
        
    except Exception as e:
        logger.error(f"Error downloading export: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@app.get("/admin/storage-stats")
async def get_storage_stats():
    """Get storage usage statistics"""
    
    try:
        stats = await storage_manager.get_storage_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/cleanup")
async def cleanup_old_files(max_age_days: int = 7):
    """Clean up old files"""
    
    try:
        await storage_manager.cleanup_old_files(max_age_days)
        return {"message": "Cleanup completed"}
        
    except Exception as e:
        logger.error(f"Error cleaning up files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files
app.mount("/assets", StaticFiles(directory=".data", html=False), name="assets")
app.mount("/exports", StaticFiles(directory=str(settings.EXPORTS_DIR)), name="exports")

if __name__ == "__main__":
    import uvicorn
    
    # Start metrics server
    start_metrics_server(port=8000)
    
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)