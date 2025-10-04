"""Celery tasks for background processing"""
import os
import uuid
import json
import logging
from typing import Dict, Any, Optional
from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from .celery_app import app
from .core.database import AsyncSessionLocal, Lesson, Slide, Export
from .core.logging import get_logger
from .core.config import settings
from .core.locks import with_distributed_lock, lesson_resource, slide_resource, export_resource, cleanup_resource
from .services.sprint1.document_parser import ParserFactory
from .services.sprint2.ai_generator import AIGenerator, TTSService
from .services.sprint3.video_exporter import VideoExporter

logger = get_logger(__name__)

@app.task(bind=True, name='app.tasks.process_lesson_full_pipeline')
@with_distributed_lock(lesson_resource, timeout=1800, blocking_timeout=30)  # 30 min lock, 30 sec wait
def process_lesson_full_pipeline(self, lesson_id: str, file_path: str, user_id: str):
    """Process lesson through full pipeline"""
    import asyncio
    
    try:
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'stage': 'initializing', 'lesson_id': lesson_id}
        )
        
        # Create new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def process_async():
            async with AsyncSessionLocal() as db:
                # Update lesson status
                await db.execute(
                    update(Lesson)
                    .where(Lesson.id == lesson_id)
                    .values(status='processing', processing_progress={'stage': 'initializing'})
                )
                await db.commit()
                
                # Parse document
                self.update_state(
                    state='PROGRESS',
                    meta={'progress': 20, 'stage': 'parsing', 'lesson_id': lesson_id}
                )
                
                parser = ParserFactory.create_parser(file_path)
                slides_data = parser.parse_document(file_path)
                
                # Save slides to database
                for i, slide_data in enumerate(slides_data):
                    slide = Slide(
                        id=str(uuid.uuid4()),
                        lesson_id=lesson_id,
                        slide_number=i + 1,
                        title=slide_data.get('title', f'Slide {i + 1}'),
                        elements_data=slide_data.get('elements', []),
                        image_file_path=slide_data.get('image_path')
                    )
                    db.add(slide)
                
                await db.commit()
                
                # Generate speaker notes
                self.update_state(
                    state='PROGRESS',
                    meta={'progress': 50, 'stage': 'generating_notes', 'lesson_id': lesson_id}
                )
                
                ai_generator = AIGenerator()
                for slide in slides_data:
                    if slide.get('elements'):
                        notes = await ai_generator.generate_speaker_notes(
                            slide['elements'], 
                            slide.get('title', '')
                        )
                        # Update slide with speaker notes
                        await db.execute(
                            update(Slide)
                            .where(Slide.lesson_id == lesson_id, Slide.slide_number == slide.get('slide_number', 1))
                            .values(speaker_notes=notes)
                        )
                
                await db.commit()
                
                # Generate audio
                self.update_state(
                    state='PROGRESS',
                    meta={'progress': 80, 'stage': 'generating_audio', 'lesson_id': lesson_id}
                )
                
                tts_service = TTSService()
                for slide in slides_data:
                    if slide.get('speaker_notes'):
                        audio_path = await tts_service.generate_audio(
                            slide['speaker_notes'],
                            f"{lesson_id}_slide_{slide.get('slide_number', 1)}"
                        )
                        # Update slide with audio path
                        await db.execute(
                            update(Slide)
                            .where(Slide.lesson_id == lesson_id, Slide.slide_number == slide.get('slide_number', 1))
                            .values(audio_file_path=audio_path)
                        )
                
                await db.commit()
                
                # Complete processing
                self.update_state(
                    state='PROGRESS',
                    meta={'progress': 100, 'stage': 'completed', 'lesson_id': lesson_id}
                )
                
                await db.execute(
                    update(Lesson)
                    .where(Lesson.id == lesson_id)
                    .values(
                        status='completed',
                        processing_progress={'stage': 'completed', 'progress': 100},
                        slides_count=len(slides_data)
                    )
                )
                await db.commit()
                
                return {'status': 'completed', 'lesson_id': lesson_id}
        
        result = loop.run_until_complete(process_async())
        loop.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing lesson {lesson_id}: {e}")
        
        # Update lesson status to failed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def update_failed():
            async with AsyncSessionLocal() as db:
                await db.execute(
                    update(Lesson)
                    .where(Lesson.id == lesson_id)
                    .values(
                        status='failed',
                        processing_progress={'stage': 'failed', 'error': str(e)}
                    )
                )
                await db.commit()
        
        loop.run_until_complete(update_failed())
        loop.close()
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'lesson_id': lesson_id}
        )
        raise

@app.task(bind=True, name='app.tasks.generate_speaker_notes_task')
@with_distributed_lock(slide_resource, timeout=600, blocking_timeout=10)  # 10 min lock, 10 sec wait
def generate_speaker_notes_task(self, lesson_id: str, slide_id: str, elements: list):
    """Generate speaker notes for a specific slide"""
    try:
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'stage': 'generating', 'lesson_id': lesson_id, 'slide_id': slide_id}
        )
        
        ai_generator = AIGenerator()
        notes = ai_generator.generate_speaker_notes(elements)
        
        # Update database
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def update_notes():
            async with AsyncSessionLocal() as db:
                await db.execute(
                    update(Slide)
                    .where(Slide.id == slide_id)
                    .values(speaker_notes=notes)
                )
                await db.commit()
        
        loop.run_until_complete(update_notes())
        loop.close()
        
        self.update_state(
            state='SUCCESS',
            meta={'progress': 100, 'stage': 'completed', 'lesson_id': lesson_id, 'slide_id': slide_id}
        )
        
        return {'status': 'completed', 'notes': notes}
        
    except Exception as e:
        logger.error(f"Error generating speaker notes for slide {slide_id}: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'lesson_id': lesson_id, 'slide_id': slide_id}
        )
        raise

@app.task(bind=True, name='app.tasks.generate_audio_task')
@with_distributed_lock(slide_resource, timeout=900, blocking_timeout=15)  # 15 min lock, 15 sec wait
def generate_audio_task(self, lesson_id: str, slide_id: str, text: str, voice_settings: dict):
    """Generate audio for speaker notes"""
    try:
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'stage': 'generating', 'lesson_id': lesson_id, 'slide_id': slide_id}
        )
        
        tts_service = TTSService()
        audio_path = tts_service.generate_audio(text, f"{lesson_id}_slide_{slide_id}", voice_settings)
        
        # Update database
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def update_audio():
            async with AsyncSessionLocal() as db:
                await db.execute(
                    update(Slide)
                    .where(Slide.id == slide_id)
                    .values(audio_file_path=audio_path)
                )
                await db.commit()
        
        loop.run_until_complete(update_audio())
        loop.close()
        
        self.update_state(
            state='SUCCESS',
            meta={'progress': 100, 'stage': 'completed', 'lesson_id': lesson_id, 'slide_id': slide_id}
        )
        
        return {'status': 'completed', 'audio_path': audio_path}
        
    except Exception as e:
        logger.error(f"Error generating audio for slide {slide_id}: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'lesson_id': lesson_id, 'slide_id': slide_id}
        )
        raise

@app.task(bind=True, name='app.tasks.export_video_task')
@with_distributed_lock(export_resource, timeout=3600, blocking_timeout=30)  # 1 hour lock, 30 sec wait
def export_video_task(self, lesson_id: str, user_id: str, quality: str = 'high'):
    """Export lesson to video"""
    try:
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'stage': 'initializing', 'lesson_id': lesson_id}
        )
        
        # Create export record
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def create_export():
            async with AsyncSessionLocal() as db:
                export = Export(
                    id=str(uuid.uuid4()),
                    lesson_id=lesson_id,
                    user_id=user_id,
                    status='processing',
                    quality=quality,
                    progress={'stage': 'initializing', 'progress': 0}
                )
                db.add(export)
                await db.commit()
                return export.id
        
        export_id = loop.run_until_complete(create_export())
        
        # Export video
        self.update_state(
            state='PROGRESS',
            meta={'progress': 20, 'stage': 'exporting', 'lesson_id': lesson_id, 'export_id': export_id}
        )
        
        exporter = VideoExporter()
        video_path = exporter.export_lesson(lesson_id, quality)
        
        # Update export record
        async def update_export():
            async with AsyncSessionLocal() as db:
                await db.execute(
                    update(Export)
                    .where(Export.id == export_id)
                    .values(
                        status='completed',
                        file_path=video_path,
                        progress={'stage': 'completed', 'progress': 100}
                    )
                )
                await db.commit()
        
        loop.run_until_complete(update_export())
        loop.close()
        
        self.update_state(
            state='SUCCESS',
            meta={'progress': 100, 'stage': 'completed', 'lesson_id': lesson_id, 'export_id': export_id}
        )
        
        return {'status': 'completed', 'video_path': video_path, 'export_id': export_id}
        
    except Exception as e:
        logger.error(f"Error exporting lesson {lesson_id}: {e}")
        
        # Update export status to failed
        async def update_failed():
            async with AsyncSessionLocal() as db:
                await db.execute(
                    update(Export)
                    .where(Export.lesson_id == lesson_id)
                    .values(
                        status='failed',
                        error_message=str(e),
                        progress={'stage': 'failed', 'error': str(e)}
                    )
                )
                await db.commit()
        
        loop.run_until_complete(update_failed())
        loop.close()
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'lesson_id': lesson_id}
        )
        raise

@app.task(bind=True, name='app.tasks.cleanup_task')
@with_distributed_lock(cleanup_resource, timeout=300, blocking_timeout=5)  # 5 min lock, 5 sec wait
def cleanup_task(self, lesson_id: Optional[str] = None):
    """Cleanup old files and data"""
    try:
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'stage': 'cleaning', 'lesson_id': lesson_id}
        )
        
        import shutil
        import os
        from pathlib import Path
        
        if lesson_id:
            # Cleanup specific lesson
            lesson_dir = settings.DATA_DIR / lesson_id
            if lesson_dir.exists():
                shutil.rmtree(lesson_dir)
                logger.info(f"Cleaned up lesson directory: {lesson_dir}")
        else:
            # Cleanup old exports
            exports_dir = settings.EXPORTS_DIR
            if exports_dir.exists():
                for export_file in exports_dir.glob("*.mp4"):
                    if export_file.stat().st_mtime < (os.time() - 7 * 24 * 3600):  # 7 days old
                        export_file.unlink()
                        logger.info(f"Cleaned up old export: {export_file}")
        
        self.update_state(
            state='SUCCESS',
            meta={'progress': 100, 'stage': 'completed', 'lesson_id': lesson_id}
        )
        
        return {'status': 'completed', 'cleaned': True}
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'lesson_id': lesson_id}
        )
        raise