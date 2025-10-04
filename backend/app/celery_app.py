"""Celery configuration and tasks"""
from celery import Celery
from celery.signals import worker_init, worker_shutdown
import os
from .core.config import settings

# Create Celery app
celery_app = Celery('slide_speaker')

# Configure Celery
celery_app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_routes={
        'app.tasks.process_lesson_full_pipeline': {'queue': 'processing'},
        'app.tasks.generate_speaker_notes_task': {'queue': 'ai_generation'},
        'app.tasks.generate_audio_task': {'queue': 'tts'},
        'app.tasks.export_video_task': {'queue': 'export'},
        'app.tasks.cleanup_task': {'queue': 'maintenance'},
    },
    task_default_queue='default',
    task_create_missing_queues=True,
    # Redis specific settings
    broker_transport_options={
        'visibility_timeout': 3600,  # 1 hour
        'priority_steps': list(range(10)),
        'queue_order_strategy': 'priority',
    },
    result_backend_transport_options={
        'visibility_timeout': 3600,
        'result_chord_ordered': True,
    }
)

# Import tasks to ensure they are registered
from . import tasks

@worker_init.connect
def init_worker(**kwargs):
    """Initialize worker"""
    print("Celery worker initialized")

@worker_shutdown.connect
def shutdown_worker(**kwargs):
    """Shutdown worker"""
    print("Celery worker shutting down")
