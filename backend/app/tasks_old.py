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
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_max_retries=3,
)

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def export_video_task(self, lesson_id: str, export_request: dict):
    """Background task for video export"""
    try:
        logger.info(f"Starting video export task for lesson {lesson_id}")
        
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "message": "Initializing export"}
        )
        
        # Initialize services
        video_exporter = VideoExporter()
        
        # Convert dict to ExportRequest
        from .models.schemas import ExportRequest
        request = ExportRequest(**export_request)
        
        # Load manifest
        manifest_path = settings.DATA_DIR / lesson_id / "manifest.json"
        if not manifest_path.exists():
            raise Exception(f"Manifest not found for lesson {lesson_id}")
        
        import json
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        from .models.schemas import Manifest
        manifest = Manifest(**manifest_data)
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"progress": 20, "message": "Generating video frames"}
        )
        
        # Generate video frames
        import tempfile
        import shutil
        temp_dir = Path(tempfile.gettempdir()) / f"export_{lesson_id}_{self.request.id}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Generate video frames with effects
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(video_exporter._generate_video_frames(lesson_id, manifest, temp_dir, request))
            finally:
                loop.close()
            
            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={"progress": 60, "message": "Rendering final video"}
            )
            
            # Combine frames with audio
            output_path = settings.EXPORTS_DIR / f"{lesson_id}_export.mp4"
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(video_exporter._render_final_video(lesson_id, manifest, temp_dir, output_path, request))
            finally:
                loop.close()
            
            # Upload to S3 if configured
            if video_exporter.s3_storage.s3_client:
                self.update_state(
                    state="PROGRESS",
                    meta={"progress": 80, "message": "Uploading to S3"}
                )
                
                s3_key = f"exports/{lesson_id}_export.mp4"
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(video_exporter.s3_storage.upload_file(output_path, s3_key, "video/mp4"))
                finally:
                    loop.close()
                logger.info(f"Video uploaded to S3: {s3_key}")
            
            # Final progress update
            self.update_state(
                state="PROGRESS",
                meta={"progress": 100, "message": "Export completed successfully"}
            )
            
            logger.info(f"Video export completed: {output_path}")
            
            return {
                "status": "completed",
                "output_path": str(output_path),
                "download_url": f"/exports/{lesson_id}_export.mp4"
            }
            
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
        
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
        logger.info(f"Starting AI generation task for lesson {lesson_id}, slide {slide_id}")
        
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "message": "Initializing AI generation"}
        )
        
        # Initialize services
        ai_generator = AIGenerator()
        tts_service = TTSService()
        
        if content_type == "speaker_notes":
            # Generate speaker notes
            self.update_state(
                state="PROGRESS",
                meta={"progress": 50, "message": "Generating speaker notes"}
            )
            
            slide_content = f"Slide {slide_id} content"  # Placeholder
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                speaker_notes = loop.run_until_complete(ai_generator.generate_speaker_notes(slide_content))
            finally:
                loop.close()
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 100, "message": "Speaker notes generated"}
            )
            
            return {
                "status": "completed",
                "content_type": "speaker_notes",
                "content": speaker_notes
            }
            
        elif content_type == "audio":
            # Generate audio
            self.update_state(
                state="PROGRESS",
                meta={"progress": 50, "message": "Generating audio"}
            )
            
            text = f"Speaker notes for slide {slide_id}"  # Placeholder
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                audio_data = loop.run_until_complete(tts_service.generate_audio(text))
            finally:
                loop.close()
            
            # Save audio file
            audio_path = settings.DATA_DIR / lesson_id / "audio" / f"{slide_id:03d}.mp3"
            audio_path.parent.mkdir(exist_ok=True)
            
            with open(audio_path, "wb") as f:
                f.write(audio_data)
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 100, "message": "Audio generated"}
            )
            
            return {
                "status": "completed",
                "content_type": "audio",
                "audio_url": f"/assets/{lesson_id}/audio/{slide_id:03d}.mp3"
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
    """Render lesson to MP4 video"""
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
        
        # Load manifest
        manifest_path = settings.DATA_DIR / lesson_id / "manifest.json"
        if not manifest_path.exists():
            raise Exception(f"Manifest not found for lesson {lesson_id}")
        
        import json
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        slides = manifest_data.get("slides", [])
        if not slides:
            raise Exception(f"No slides found in lesson {lesson_id}")
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"progress": 20, "message": "Processing slides"}
        )
        
        # Import MoviePy
        from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
        from PIL import Image
        import tempfile
        import shutil
        
        # Create temporary directory
        temp_dir = Path(tempfile.gettempdir()) / f"render_{lesson_id}_{self.request.id}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            video_clips = []
            total_duration = 0
            
            for i, slide in enumerate(slides):
                slide_id = slide["id"]
                image_path = slide["image"]
                audio_path = slide["audio"]
                
                # Convert image path to absolute path
                if image_path.startswith("/assets/"):
                    # Remove /assets/ prefix and use .data directory
                    relative_path = image_path[8:]  # Remove "/assets/"
                    full_image_path = settings.DATA_DIR / relative_path
                else:
                    full_image_path = Path(image_path)
                
                # Check if image exists, if not use placeholder
                if not full_image_path.exists():
                    logger.warning(f"Image not found: {full_image_path}, using placeholder")
                    # Create a simple placeholder image
                    placeholder_path = temp_dir / f"placeholder_{slide_id}.png"
                    img = Image.new('RGB', (1920, 1080), color='white')
                    img.save(placeholder_path)
                    full_image_path = placeholder_path
                
                # Convert SVG to PNG if needed
                if full_image_path.suffix.lower() == '.svg':
                    png_path = temp_dir / f"slide_{slide_id}.png"
                    # For now, create a placeholder PNG
                    img = Image.new('RGB', (1920, 1080), color='lightblue')
                    img.save(png_path)
                    full_image_path = png_path
                
                # Calculate slide duration from cues
                slide_duration = 5.0  # Default duration
                if slide.get("cues"):
                    max_cue_end = max(cue.get("t1", 0) for cue in slide["cues"])
                    slide_duration = max(slide_duration, max_cue_end + 1.0)
                
                # Create video clip from image
                try:
                    video_clip = ImageSequenceClip([str(full_image_path)], durations=[slide_duration])
                except Exception as e:
                    logger.error(f"Error creating video clip for slide {slide_id}: {e}")
                    # Create a simple colored clip as fallback
                    from moviepy.editor import ColorClip
                    video_clip = ColorClip(size=(1920, 1080), color=(200, 200, 200), duration=slide_duration)
                
                # Add audio if available
                if audio_path and audio_path.startswith("/assets/"):
                    relative_audio_path = audio_path[8:]  # Remove "/assets/"
                    full_audio_path = settings.DATA_DIR / relative_audio_path
                    
                    if full_audio_path.exists():
                        try:
                            audio_clip = AudioFileClip(str(full_audio_path))
                            # Adjust video duration to match audio
                            if audio_clip.duration > slide_duration:
                                slide_duration = audio_clip.duration
                                video_clip = video_clip.set_duration(slide_duration)
                            video_clip = video_clip.set_audio(audio_clip)
                        except Exception as e:
                            logger.warning(f"Error loading audio for slide {slide_id}: {e}")
                
                video_clips.append(video_clip)
                total_duration += slide_duration
                
                # Update progress
                progress = 20 + (i + 1) * 60 / len(slides)
                self.update_state(
                    state="PROGRESS",
                    meta={"progress": progress, "message": f"Processed slide {slide_id}"}
                )
            
            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={"progress": 80, "message": "Rendering final video"}
            )
            
            # Concatenate all video clips
            if len(video_clips) > 1:
                final_video = concatenate_videoclips(video_clips)
            else:
                final_video = video_clips[0]
            
            # Set video properties
            final_video = final_video.resize((1920, 1080))
            
            # Save output
            output_path = settings.DATA_DIR / lesson_id / "export.mp4"
            final_video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Clean up video clips
            for clip in video_clips:
                clip.close()
            final_video.close()
            
            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={"progress": 100, "message": "Export completed"}
            )
            
            logger.info(f"MP4 export completed: {output_path}")
            
            return {
                "status": "completed",
                "output_path": str(output_path),
                "download_url": f"/assets/{lesson_id}/export.mp4",
                "duration": total_duration
            }
            
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
        
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