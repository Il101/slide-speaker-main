"""Simplified Celery tasks for background processing"""
import os
import sys
import uuid
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from celery import current_task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add workers directory to Python path for imports in Celery worker
current_dir = Path(__file__).parent
workers_dir = current_dir.parent.parent / "workers"
if str(workers_dir) not in sys.path:
    sys.path.insert(0, str(workers_dir))

from .celery_app import celery_app
from .core.logging import get_logger
from .core.config import settings
from .core.locks import with_distributed_lock, lesson_resource
from .core.websocket_manager import get_ws_manager
# Legacy import - only used when USE_NEW_PIPELINE=false
# from .services.sprint1.document_parser import ParserFactory
from .services.sprint2.ai_generator import AIGenerator, TTSService
from .services.sprint3.video_exporter import VideoExporter
from .models.schemas import ExportRequest

logger = get_logger(__name__)

# Create synchronous database engine for Celery tasks
engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', '+psycopg2'))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(bind=True, name='app.tasks.process_lesson_full_pipeline')
@with_distributed_lock(lesson_resource, timeout=600, blocking_timeout=5)
def process_lesson_full_pipeline(self, lesson_id: str, file_path: str, user_id: str):
    """Process lesson through full pipeline - simplified version"""
    import asyncio
    
    # Get WebSocket manager for progress updates
    ws_manager = get_ws_manager()
    
    async def send_progress(stage: str, percent: float, message: str, **kwargs):
        """Helper to send progress via WebSocket"""
        try:
            await ws_manager.send_progress(
                lesson_id=lesson_id,
                stage=stage,
                percent=percent,
                message=message,
                **kwargs
            )
        except Exception as e:
            logger.warning(f"Failed to send WebSocket progress: {e}")
    
    try:
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'stage': 'initializing', 'lesson_id': lesson_id}
        )
        
        # Send WebSocket progress
        asyncio.run(send_progress('initializing', 0, 'Initializing processing...'))
        
        with SessionLocal() as db:
            # Update lesson status
            db.execute(text("""
                UPDATE lessons 
                SET status = 'processing', 
                    processing_progress = :progress
                WHERE id = :lesson_id
            """), {
                'progress': json.dumps({'stage': 'initializing', 'progress': 0}),
                'lesson_id': lesson_id
            })
            db.commit()
            
            # Use NEW pipeline for all processing
            lesson_dir = Path(".data") / lesson_id
            
            logger.info(f"✅ Using NEW pipeline for lesson {lesson_id}")
            
            # Define progress callback to update DB and WebSocket
            def update_progress(stage: str, progress: int, message: str):
                """Update progress in DB and send WebSocket notification"""
                try:
                    # Update Celery task state
                    self.update_state(
                        state='PROGRESS',
                        meta={'progress': progress, 'stage': stage, 'lesson_id': lesson_id}
                    )
                    
                    # Update DB
                    db.execute(text("""
                        UPDATE lessons 
                        SET processing_progress = :progress
                        WHERE id = :lesson_id
                    """), {
                        'progress': json.dumps({'stage': stage, 'progress': progress, 'message': message}),
                        'lesson_id': lesson_id
                    })
                    db.commit()
                    
                    # Send WebSocket update
                    asyncio.run(send_progress(stage, progress, message))
                    
                    logger.info(f"📊 Progress: {stage} - {progress}% - {message}")
                except Exception as e:
                    logger.warning(f"Failed to update progress: {e}")
            
            # Run FULL pipeline (PPTX→PNG→OCR→Plan→TTS→Effects)
            try:
                from app.pipeline import get_pipeline
                
                pipeline_name = os.getenv("PIPELINE", "intelligent_optimized")
                pipeline = get_pipeline(pipeline_name)()
                
                logger.info(f"🚀 Starting {pipeline_name}.process_full_pipeline()")
                result = pipeline.process_full_pipeline(str(lesson_dir), progress_callback=update_progress)
                logger.info(f"✅ Pipeline completed: {result}")
                
                # Load final manifest
                manifest_path = lesson_dir / "manifest.json"
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                slides_data = manifest_data.get('slides', [])
                
                # Update slides count in DB
                db.execute(text("""
                    UPDATE lessons 
                    SET slides_count = :count,
                        processing_progress = :progress
                    WHERE id = :lesson_id
                """), {
                    'count': len(slides_data),
                    'progress': json.dumps({'stage': 'completed', 'progress': 100}),
                    'lesson_id': lesson_id
                })
                db.commit()
                
                logger.info(f"✅ Pipeline completed: {len(slides_data)} slides processed")
                
            except Exception as e:
                logger.error(f"❌ Pipeline failed: {e}")
                raise
            
                        # Load final manifest
            manifest_path = Path(".data") / lesson_id / "manifest.json"
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_dict = json.load(f)
            slides_data = manifest_dict.get('slides', [])
            
            # Calculate total duration from all slides
            
            # Load final manifest (works for both NEW and OLD pipeline)
            manifest_path = Path(".data") / lesson_id / "manifest.json"
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_dict = json.load(f)
            
            # Load final manifest (works for both NEW and OLD pipeline)
            manifest_path = Path(".data") / lesson_id / "manifest.json"
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_dict = json.load(f)
            slides_data = manifest_dict.get('slides', [])
            
            # Calculate total duration from all slides
            total_duration = sum(
                slide.get('duration', 0) or 0
                for slide in slides_data
            )
            logger.info(f"Calculated total duration: {total_duration:.2f}s from {len(slides_data)} slides")
            
            # Update final status
            self.update_state(
                state='PROGRESS',
                meta={'progress': 100, 'stage': 'completed', 'lesson_id': lesson_id}
            )
            
            db.execute(text("""
                UPDATE lessons 
                SET status = 'completed', 
                    processing_progress = :progress,
                    slides_count = :slides_count,
                    total_duration = :total_duration,
                    manifest_data = :manifest_data
                WHERE id = :lesson_id
            """), {
                'progress': json.dumps({'stage': 'completed', 'progress': 100}),
                'slides_count': len(slides_data),
                'total_duration': total_duration if total_duration > 0 else None,
                'manifest_data': json.dumps(manifest_dict),
                'lesson_id': lesson_id
            })
            db.commit()
            
            logger.info(f"Successfully completed processing lesson {lesson_id}")
            return {'status': 'completed', 'lesson_id': lesson_id}
            
    except Exception as e:
        logger.error(f"Error processing lesson {lesson_id}: {e}")
        
        # Update lesson status to failed
        try:
            with SessionLocal() as db:
                db.execute(text("""
                    UPDATE lessons 
                    SET status = 'failed', 
                        processing_progress = :progress
                    WHERE id = :lesson_id
                """), {
                    'progress': json.dumps({'stage': 'failed', 'error': str(e)}),
                    'lesson_id': lesson_id
                })
                db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update lesson status: {update_error}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'lesson_id': lesson_id}
        )
        raise


@celery_app.task(bind=True, name='app.tasks.export_video_task')
@with_distributed_lock(lesson_resource, timeout=1800, blocking_timeout=10)
def export_video_task(self, lesson_id: str, quality: str = "high"):
    """Export lesson to MP4 video"""
    try:
        logger.info(f"Starting video export for lesson {lesson_id} with quality {quality}")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'stage': 'initializing', 'lesson_id': lesson_id}
        )
        
        # Check if lesson exists and is completed
        with SessionLocal() as db:
            result = db.execute(text("""
                SELECT status, slides_count 
                FROM lessons 
                WHERE id = :lesson_id
            """), {'lesson_id': lesson_id}).fetchone()
            
            if not result:
                raise Exception(f"Lesson {lesson_id} not found")
            
            status, slides_count = result
            if status != 'completed':
                raise Exception(f"Lesson {lesson_id} is not completed (status: {status})")
            
            if not slides_count or slides_count == 0:
                raise Exception(f"Lesson {lesson_id} has no slides")
        
        # Load manifest
        manifest_path = settings.DATA_DIR / lesson_id / "manifest.json"
        if not manifest_path.exists():
            raise Exception(f"Manifest not found for lesson {lesson_id}")
        
        logger.info(f"Loading manifest from {manifest_path}")
        
        # Load and fix manifest format
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        
        # Convert bbox format from {x, y, width, height} to [x, y, width, height]
        if 'slides' in manifest_data:
            for slide in manifest_data['slides']:
                if 'elements' in slide:
                    for element in slide['elements']:
                        if 'bbox' in element and isinstance(element['bbox'], dict):
                            bbox = element['bbox']
                            if all(k in bbox for k in ['x', 'y', 'width', 'height']):
                                element['bbox'] = [
                                    bbox['x'],
                                    bbox['y'],
                                    bbox['width'],
                                    bbox['height']
                                ]
                                logger.debug(f"Converted bbox for element {element.get('id', 'unknown')}")
                
                # Convert cue bboxes
                if 'cues' in slide:
                    for cue in slide['cues']:
                        if 'bbox' in cue and isinstance(cue['bbox'], dict):
                            bbox = cue['bbox']
                            if all(k in bbox for k in ['x', 'y', 'width', 'height']):
                                cue['bbox'] = [
                                    bbox['x'],
                                    bbox['y'],
                                    bbox['width'],
                                    bbox['height']
                                ]
        
        # Save fixed manifest back
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Manifest format fixed and saved")
        
        # Create export request
        export_request = ExportRequest(
            lesson_id=lesson_id,
            quality=quality,
            include_audio=True,
            include_effects=True
        )
        
        # Initialize video exporter
        video_exporter = VideoExporter()
        
        # Use asyncio to run async export function
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'stage': 'loading_manifest', 'lesson_id': lesson_id}
        )
        
        # Run the export (the VideoExporter already handles background processing)
        export_response = loop.run_until_complete(
            video_exporter.export_lesson(lesson_id, export_request)
        )
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 50, 'stage': 'rendering_video', 'lesson_id': lesson_id}
        )
        
        logger.info(f"Video export task initiated: {export_response.task_id}")
        
        # Note: The actual video generation happens in background
        # This task just initiates it and returns the task_id
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'stage': 'completed', 'lesson_id': lesson_id}
        )
        
        return {
            'status': 'processing',
            'lesson_id': lesson_id,
            'task_id': export_response.task_id,
            'message': 'Video export started successfully'
        }
        
    except Exception as e:
        logger.error(f"Error exporting video for lesson {lesson_id}: {e}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'lesson_id': lesson_id}
        )
        raise
