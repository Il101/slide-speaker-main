"""Celery tasks for background processing"""
from celery import Celery
import logging
from pathlib import Path

from .core.config import settings
from .services.sprint3.video_exporter import VideoExporter
from .services.sprint2.ai_generator import AIGenerator, TTSService

# Configure Celery
celery_app = Celery(
    "slide_speaker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Concurrency settings
    worker_concurrency=4,  # Number of concurrent workers
    worker_prefetch_multiplier=1,  # Prefetch only 1 task per worker
    task_acks_late=True,  # Acknowledge tasks only after completion
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    # Rate limiting
    task_routes={
        'export_video_task': {'queue': 'video_export'},
        'generate_ai_content_task': {'queue': 'ai_generation'},
        'render_lesson_mp4': {'queue': 'video_export'},
        'cleanup_files_task': {'queue': 'maintenance'},
    },
    # Queue configuration
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'video_export': {
            'exchange': 'video_export',
            'routing_key': 'video_export',
        },
        'ai_generation': {
            'exchange': 'ai_generation',
            'routing_key': 'ai_generation',
        },
        'maintenance': {
            'exchange': 'maintenance',
            'routing_key': 'maintenance',
        },
    },
    # Task time limits
    task_time_limit=1800,  # 30 minutes
    task_soft_time_limit=1500,  # 25 minutes
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    # Worker settings
    worker_disable_rate_limits=False,
    worker_hijack_root_logger=False,
    worker_log_color=False,
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Configure logging
logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def export_video_task(self, lesson_id: str, quality: str = "high"):
    """Background task for video export"""
    try:
        logger.info(f"Starting video export task for lesson {lesson_id}")
        
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "message": "Starting export"}
        )
        
        # Initialize video exporter
        exporter = VideoExporter()
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"progress": 30, "message": "Processing slides"}
        )
        
        # Export video
        import asyncio
        from .models.schemas import ExportRequest
        
        request = ExportRequest(lesson_id=lesson_id, quality=quality)
        
        # Run async method in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(exporter.export_lesson(lesson_id, request))
        finally:
            loop.close()
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"progress": 90, "message": "Finalizing export"}
        )
        
        # Update final status
        self.update_state(
            state="PROGRESS",
            meta={"progress": 100, "message": "Export completed"}
        )
        
        logger.info(f"Video export completed for lesson {lesson_id}")
        
        return {
            "status": "completed",
            "output_path": None,  # ExportResponse doesn't have output_path
            "download_url": result.download_url if hasattr(result, 'download_url') else None,
            "duration": 0  # ExportResponse doesn't have duration
        }
        
    except Exception as e:
        logger.error(f"Error in video export task: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "error_type": type(e).__name__,
                "progress": 0,
                "message": f"Video export failed: {str(e)}"
            }
        )
        raise

@celery_app.task(bind=True)
def generate_ai_content_task(self, lesson_id: str, slide_id: int, content_type: str):
    """Background task for AI content generation"""
    try:
        logger.info(f"Starting AI generation task for lesson {lesson_id}, slide {slide_id}, type {content_type}")
        
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "message": "Starting AI generation"}
        )
        
        # Initialize AI generator
        generator = AIGenerator()
        
        if content_type == "speaker_notes":
            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={"progress": 50, "message": "Generating speaker notes"}
            )
            
            # Generate speaker notes
            notes = generator.generate_speaker_notes(f"Slide {slide_id} content")
            
            return {
                "status": "completed",
                "content_type": "speaker_notes",
                "content": notes,
                "slide_id": slide_id
            }
            
        elif content_type == "audio":
            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={"progress": 50, "message": "Generating audio"}
            )
            
            # Initialize TTS service
            tts_service = TTSService()
            
            # Generate audio
            audio_result = tts_service.generate_audio(f"Slide {slide_id} content")
            
            return {
                "status": "completed",
                "content_type": "audio",
                "audio_url": audio_result.get("audio_url"),
                "duration": audio_result.get("duration"),
                "slide_id": slide_id
            }
        
        else:
            raise ValueError(f"Unknown content type: {content_type}")
        
    except Exception as e:
        logger.error(f"Error in AI generation task: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "error_type": type(e).__name__,
                "progress": 0,
                "message": f"AI generation failed: {str(e)}"
            }
        )
        raise

@celery_app.task(bind=True)
def render_lesson_mp4(self, lesson_id: str):
    """Render lesson to MP4 video - simplified version"""
    try:
        logger.info(f"Starting MP4 render task for lesson {lesson_id}")
        
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "message": "Loading manifest"}
        )
        
        # For now, return a mock result to test the system
        logger.info(f"Mock MP4 render completed for lesson {lesson_id}")
        
        self.update_state(
            state="PROGRESS",
            meta={"progress": 100, "message": "Export completed (mock)"}
        )
        
        return {
            "status": "completed",
            "output_path": f"/app/.data/exports/{lesson_id}_export.mp4",
            "download_url": f"/assets/{lesson_id}/export.mp4",
            "duration": 30.0
        }
        
    except Exception as e:
        logger.error(f"Error in MP4 render task: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "error_type": type(e).__name__,
                "progress": 0,
                "message": f"Export failed: {str(e)}"
            }
        )
        raise

@celery_app.task(bind=True)
def process_lesson_full_pipeline(self, lesson_id: str):
    """Full pipeline task: OCR -> LLM -> TTS -> Video Export"""
    try:
        logger.info(f"Starting full pipeline processing for lesson {lesson_id}")
        
        # Update task status (only if running as Celery task)
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state="PROGRESS",
                meta={"progress": 5, "message": "Starting full pipeline"}
            )
        
        from .core.config import settings
        from .services.provider_factory import plan_slide_with_gemini, synthesize_slide_text_google
        import json
        import os
        from pathlib import Path
        
        # Import lecture text generation function
        try:
            from ...workers.llm_openrouter import generate_lecture_text
        except ImportError:
            try:
                from workers.llm_openrouter import generate_lecture_text
            except ImportError:
                logger.warning("Could not import generate_lecture_text, will use speaker notes as lecture text")
                generate_lecture_text = None
        
        # Load manifest
        lesson_dir = settings.DATA_DIR / lesson_id
        manifest_path = lesson_dir / "manifest.json"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found for lesson {lesson_id}")
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state="PROGRESS",
                meta={"progress": 10, "message": "Processing slides with AI"}
            )
        
        # Process each slide with AI - LOGICAL PIPELINE
        for slide in manifest_data["slides"]:
            slide_id = slide["id"]
            elements = slide.get("elements", [])
            
            logger.info(f"=== Processing slide {slide_id} ===")
            
            # STEP 1: Generate speaker notes using LLM
            logger.info(f"Step 1: Generating speaker notes for slide {slide_id}")
            logger.info(f"Elements for slide {slide_id}: {elements}")
            try:
                speaker_notes = plan_slide_with_gemini(elements)
                slide["speaker_notes"] = speaker_notes
                logger.info(f"✅ Generated {len(speaker_notes)} speaker notes for slide {slide_id}")
                
                # Log speaker notes for debugging
                for i, note in enumerate(speaker_notes):
                    logger.debug(f"  Note {i+1}: {note.get('text', '')[:50]}...")
                    
            except Exception as e:
                logger.error(f"❌ Failed to generate speaker notes for slide {slide_id}: {e}")
                logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                slide["speaker_notes"] = []
                # Don't continue - try to generate audio anyway
            
            # STEP 1.5: Generate lecture text for subtitles
            logger.info(f"Step 1.5: Generating lecture text for slide {slide_id}")
            try:
                if generate_lecture_text:
                    lecture_text = generate_lecture_text(elements)
                    slide["lecture_text"] = lecture_text
                    logger.info(f"✅ Generated lecture text for slide {slide_id}: {len(lecture_text)} characters")
                else:
                    # Fallback: use speaker notes as lecture text
                    if slide.get("speaker_notes"):
                        lecture_text = " ".join([note.get("text", "") for note in slide["speaker_notes"]])
                        slide["lecture_text"] = lecture_text
                        logger.info(f"✅ Used speaker notes as lecture text for slide {slide_id}")
                    else:
                        slide["lecture_text"] = "Let's discuss the content of this slide."
                        logger.info(f"✅ Used fallback lecture text for slide {slide_id}")
                        
            except Exception as e:
                logger.error(f"❌ Failed to generate lecture text for slide {slide_id}: {e}")
                slide["lecture_text"] = "Let's discuss the content of this slide."
            
            # STEP 2: Generate audio using TTS (from lecture text)
            logger.info(f"Step 2: Generating audio for slide {slide_id}")
            try:
                # Use lecture_text for TTS instead of speaker_notes
                lecture_text = slide.get("lecture_text", "")
                if not lecture_text:
                    logger.warning(f"⚠️ No lecture text found for slide {slide_id}, using speaker notes as fallback")
                    # Fallback to speaker notes if lecture_text is not available
                    slide_texts = []
                    for note in slide.get("speaker_notes", []):
                        if note.get("text"):
                            slide_texts.append(note.get("text"))
                    lecture_text = " ".join(slide_texts)
                
                if not lecture_text:
                    logger.warning(f"⚠️ No text found for slide {slide_id}")
                    slide["audio"] = None
                    slide["duration"] = 0.0
                    continue
                
                logger.info(f"TTS input (lecture text): {lecture_text[:100]}...")
                
                # Generate audio using lecture text
                audio_path, tts_words = synthesize_slide_text_google([lecture_text])
                
                # Verify audio file was created
                import os
                if not audio_path or not os.path.exists(audio_path):
                    logger.error(f"❌ TTS failed to create audio file for slide {slide_id}")
                    slide["audio"] = None
                    slide["duration"] = 0.0
                    continue
                
                # Copy audio to lesson directory with consistent format
                audio_dest = lesson_dir / "audio" / f"{slide_id:03d}.wav"  # Use .wav consistently
                audio_dest.parent.mkdir(exist_ok=True)
                
                import shutil
                shutil.copy2(audio_path, audio_dest)
                
                # Verify file was copied successfully
                if not audio_dest.exists():
                    logger.error(f"❌ Failed to copy audio file for slide {slide_id}")
                    slide["audio"] = None
                    slide["duration"] = 0.0
                    continue
                
                # Update slide with audio info
                slide["audio"] = f"/assets/{lesson_id}/audio/{slide_id:03d}.wav"
                duration = tts_words.get("sentences", [{}])[-1].get("t1", 0.0) if tts_words.get("sentences") else 0.0
                slide["duration"] = duration
                
                logger.info(f"✅ Generated audio for slide {slide_id}: {duration:.2f}s, file: {audio_dest.name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to generate audio for slide {slide_id}: {e}")
                slide["audio"] = None
                slide["duration"] = 0.0
        
        # Save updated manifest
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)
        
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state="PROGRESS",
                meta={"progress": 80, "message": "AI processing completed"}
            )
        
        # Start video export
        export_task = export_video_task.delay(lesson_id, "high")
        
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state="PROGRESS",
                meta={"progress": 90, "message": "Starting video export"}
            )
        
        logger.info(f"Full pipeline processing completed for lesson {lesson_id}")
        
        return {
            "status": "completed",
            "lesson_id": lesson_id,
            "export_task_id": export_task.id,
            "slides_processed": len(manifest_data["slides"]),
            "message": "Full pipeline completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in full pipeline task: {e}")
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "progress": 0,
                    "message": f"Full pipeline failed: {str(e)}"
                }
            )
        raise

@celery_app.task(bind=True)
def cleanup_files_task(self, max_age_days: int = 7):
    """Background task for file cleanup"""
    try:
        logger.info(f"Starting cleanup task for files older than {max_age_days} days")
        
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "message": "Starting cleanup"}
        )
        
        # TODO: Implement actual cleanup logic
        # - Find old files
        # - Remove expired exports
        # - Clean up temporary files
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"progress": 50, "message": "Cleaning up files"}
        )
        
        # Update final status
        self.update_state(
            state="PROGRESS",
            meta={"progress": 100, "message": "Cleanup completed"}
        )
        
        return {
            "status": "completed",
            "files_removed": 0,  # Placeholder
            "space_freed": "0 MB"  # Placeholder
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "error_type": type(e).__name__,
                "progress": 0,
                "message": f"Cleanup failed: {str(e)}"
            }
        )
        raise
