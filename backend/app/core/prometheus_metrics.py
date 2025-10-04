"""Enhanced monitoring and metrics with Prometheus"""
import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
    make_asgi_app, multiprocess, disable_created_metrics
)
from prometheus_client.multiprocess import MultiProcessCollector
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse

logger = logging.getLogger(__name__)

# Disable _created metrics to reduce noise
disable_created_metrics()

# Create custom registry for multiprocess support
def create_registry():
    """Create a registry with multiprocess support if available"""
    registry = CollectorRegistry()
    
    # Try to add multiprocess support if PROMETHEUS_MULTIPROC_DIR is set
    try:
        import os
        multiproc_dir = os.environ.get('PROMETHEUS_MULTIPROC_DIR')
        if multiproc_dir and os.path.isdir(multiproc_dir):
            MultiProcessCollector(registry)
            logger.info(f"Multiprocess metrics enabled with dir: {multiproc_dir}")
        else:
            logger.info("Multiprocess metrics disabled - PROMETHEUS_MULTIPROC_DIR not set or invalid")
    except Exception as e:
        logger.warning(f"Failed to enable multiprocess metrics: {e}")
    
    return registry

# Global registry
REGISTRY = create_registry()

# Application metrics
REQUEST_COUNT = Counter(
    'slide_speaker_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    'slide_speaker_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY
)

REQUEST_SIZE = Histogram(
    'slide_speaker_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=[1024, 10240, 102400, 1048576, 10485760],  # 1KB, 10KB, 100KB, 1MB, 10MB
    registry=REGISTRY
)

RESPONSE_SIZE = Histogram(
    'slide_speaker_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    buckets=[1024, 10240, 102400, 1048576, 10485760],
    registry=REGISTRY
)

# Business metrics
LESSONS_CREATED = Counter(
    'slide_speaker_lessons_created_total',
    'Total number of lessons created',
    ['user_id', 'file_type'],
    registry=REGISTRY
)

LESSONS_PROCESSED = Counter(
    'slide_speaker_lessons_processed_total',
    'Total number of lessons processed',
    ['status', 'user_id'],
    registry=REGISTRY
)

SLIDES_GENERATED = Counter(
    'slide_speaker_slides_generated_total',
    'Total number of slides generated',
    ['lesson_id', 'user_id'],
    registry=REGISTRY
)

AUDIO_GENERATED = Counter(
    'slide_speaker_audio_generated_total',
    'Total number of audio files generated',
    ['lesson_id', 'voice_type'],
    registry=REGISTRY
)

EXPORTS_CREATED = Counter(
    'slide_speaker_exports_created_total',
    'Total number of video exports created',
    ['lesson_id', 'quality', 'user_id'],
    registry=REGISTRY
)

# System metrics
ACTIVE_USERS = Gauge(
    'slide_speaker_active_users',
    'Number of active users',
    registry=REGISTRY
)

ACTIVE_LESSONS = Gauge(
    'slide_speaker_active_lessons',
    'Number of lessons currently being processed',
    registry=REGISTRY
)

QUEUE_SIZE = Gauge(
    'slide_speaker_queue_size',
    'Number of tasks in processing queue',
    ['queue_name'],
    registry=REGISTRY
)

DATABASE_CONNECTIONS = Gauge(
    'slide_speaker_database_connections',
    'Number of active database connections',
    registry=REGISTRY
)

REDIS_CONNECTIONS = Gauge(
    'slide_speaker_redis_connections',
    'Number of active Redis connections',
    registry=REGISTRY
)

# Error metrics
ERROR_COUNT = Counter(
    'slide_speaker_errors_total',
    'Total number of errors',
    ['error_type', 'endpoint', 'severity'],
    registry=REGISTRY
)

CELERY_TASK_FAILURES = Counter(
    'slide_speaker_celery_task_failures_total',
    'Total number of Celery task failures',
    ['task_name', 'error_type'],
    registry=REGISTRY
)

# Performance metrics
PROCESSING_TIME = Histogram(
    'slide_speaker_processing_time_seconds',
    'Time spent processing lessons',
    ['stage'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800],  # 1s to 30min
    registry=REGISTRY
)

FILE_SIZE = Histogram(
    'slide_speaker_file_size_bytes',
    'Size of uploaded files',
    ['file_type'],
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600],  # 1KB to 100MB
    registry=REGISTRY
)

# Custom metrics for specific features
AI_GENERATION_TIME = Histogram(
    'slide_speaker_ai_generation_time_seconds',
    'Time spent on AI generation tasks',
    ['task_type', 'model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=REGISTRY
)

TTS_GENERATION_TIME = Histogram(
    'slide_speaker_tts_generation_time_seconds',
    'Time spent on TTS generation',
    ['voice_type', 'text_length'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=REGISTRY
)

VIDEO_EXPORT_TIME = Histogram(
    'slide_speaker_video_export_time_seconds',
    'Time spent on video export',
    ['quality', 'duration'],
    buckets=[10, 30, 60, 300, 600, 1800, 3600],  # 10s to 1h
    registry=REGISTRY
)

# Application info
APP_INFO = Info(
    'slide_speaker_app_info',
    'Application information',
    registry=REGISTRY
)

# Set application info
APP_INFO.info({
    'version': '1.0.0',
    'environment': 'production',
    'python_version': '3.11',
    'fastapi_version': '0.115.0'
})

class MetricsCollector:
    """Enhanced metrics collector for Slide Speaker"""
    
    def __init__(self):
        self.registry = REGISTRY
    
    def record_request(self, request: Request, response: Response, duration: float):
        """Record HTTP request metrics"""
        method = request.method
        endpoint = request.url.path
        status_code = str(response.status_code)
        
        # Record request count
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        # Record request duration
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        # Record request size if available
        if hasattr(request, 'content_length') and request.content_length:
            REQUEST_SIZE.labels(
                method=method,
                endpoint=endpoint
            ).observe(request.content_length)
        
        # Record response size if available
        if hasattr(response, 'content_length') and response.content_length:
            RESPONSE_SIZE.labels(
                method=method,
                endpoint=endpoint
            ).observe(response.content_length)
    
    def record_lesson_created(self, lesson_id: str, user_id: str, file_type: str, file_size: int):
        """Record lesson creation metrics"""
        LESSONS_CREATED.labels(
            user_id=user_id,
            file_type=file_type
        ).inc()
        
        FILE_SIZE.labels(file_type=file_type).observe(file_size)
    
    def record_lesson_processed(self, lesson_id: str, user_id: str, status: str, processing_time: float):
        """Record lesson processing metrics"""
        LESSONS_PROCESSED.labels(
            status=status,
            user_id=user_id
        ).inc()
        
        PROCESSING_TIME.labels(stage='total').observe(processing_time)
    
    def record_slides_generated(self, lesson_id: str, user_id: str, count: int):
        """Record slides generation metrics"""
        SLIDES_GENERATED.labels(
            lesson_id=lesson_id,
            user_id=user_id
        ).inc(count)
    
    def record_audio_generated(self, lesson_id: str, voice_type: str, generation_time: float):
        """Record audio generation metrics"""
        AUDIO_GENERATED.labels(
            lesson_id=lesson_id,
            voice_type=voice_type
        ).inc()
        
        TTS_GENERATION_TIME.labels(
            voice_type=voice_type,
            text_length='unknown'  # Could be enhanced to track text length
        ).observe(generation_time)
    
    def record_export_created(self, lesson_id: str, user_id: str, quality: str, export_time: float):
        """Record export creation metrics"""
        EXPORTS_CREATED.labels(
            lesson_id=lesson_id,
            quality=quality,
            user_id=user_id
        ).inc()
        
        VIDEO_EXPORT_TIME.labels(
            quality=quality,
            duration='unknown'  # Could be enhanced to track video duration
        ).observe(export_time)
    
    def record_error(self, error_type: str, endpoint: str, severity: str = 'error'):
        """Record error metrics"""
        ERROR_COUNT.labels(
            error_type=error_type,
            endpoint=endpoint,
            severity=severity
        ).inc()
    
    def record_celery_task_failure(self, task_name: str, error_type: str):
        """Record Celery task failure metrics"""
        CELERY_TASK_FAILURES.labels(
            task_name=task_name,
            error_type=error_type
        ).inc()
    
    def update_active_users(self, count: int):
        """Update active users count"""
        ACTIVE_USERS.set(count)
    
    def update_active_lessons(self, count: int):
        """Update active lessons count"""
        ACTIVE_LESSONS.set(count)
    
    def update_queue_size(self, queue_name: str, size: int):
        """Update queue size"""
        QUEUE_SIZE.labels(queue_name=queue_name).set(size)
    
    def update_database_connections(self, count: int):
        """Update database connections count"""
        DATABASE_CONNECTIONS.set(count)
    
    def update_redis_connections(self, count: int):
        """Update Redis connections count"""
        REDIS_CONNECTIONS.set(count)
    
    def record_ai_generation(self, task_type: str, model: str, generation_time: float):
        """Record AI generation metrics"""
        AI_GENERATION_TIME.labels(
            task_type=task_type,
            model=model
        ).observe(generation_time)

# Global metrics collector instance
metrics_collector = MetricsCollector()

# FastAPI middleware for automatic request metrics
async def metrics_middleware(request: Request, call_next):
    """Middleware to automatically collect request metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    metrics_collector.record_request(request, response, duration)
    
    return response

# Health check metrics
def get_health_metrics() -> Dict[str, Any]:
    """Get health check metrics"""
    return {
        'status': 'healthy',
        'timestamp': time.time(),
        'metrics_endpoint': '/metrics',
        'registry_size': len(list(REGISTRY.collect()))
    }

# Export metrics endpoint
def export_metrics():
    """Export metrics in Prometheus format"""
    return FastAPIResponse(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )

# Create ASGI app for metrics
metrics_app = make_asgi_app(registry=REGISTRY)
