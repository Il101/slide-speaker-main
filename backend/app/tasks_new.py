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
        result = exporter.export_lesson_to_video(lesson_id, quality)
        
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
            "output_path": result.get("output_path"),
            "download_url": result.get("download_url"),
            "duration": result.get("duration", 0)
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
