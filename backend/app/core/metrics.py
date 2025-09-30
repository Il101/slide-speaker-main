"""Prometheus metrics for monitoring"""
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import logging

logger = logging.getLogger(__name__)

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Business metrics
LESSONS_CREATED = Counter(
    'lessons_created_total',
    'Total number of lessons created'
)

LESSONS_EXPORTED = Counter(
    'lessons_exported_total',
    'Total number of lessons exported'
)

SLIDES_PROCESSED = Counter(
    'slides_processed_total',
    'Total number of slides processed',
    ['parser_type']
)

OCR_REQUESTS = Counter(
    'ocr_requests_total',
    'Total OCR requests',
    ['provider', 'status']
)

TTS_REQUESTS = Counter(
    'tts_requests_total',
    'Total TTS requests',
    ['provider', 'status']
)

LLM_REQUESTS = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['provider', 'status']
)

# System metrics
ACTIVE_TASKS = Gauge(
    'active_tasks',
    'Number of active background tasks',
    ['task_type']
)

QUEUE_SIZE = Gauge(
    'celery_queue_size',
    'Number of tasks in Celery queue',
    ['queue_name']
)

MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

DISK_USAGE = Gauge(
    'disk_usage_bytes',
    'Disk usage in bytes',
    ['path']
)

# Error metrics
ERROR_COUNT = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'component']
)

# Performance metrics
PROCESSING_TIME = Histogram(
    'processing_time_seconds',
    'Processing time for various operations',
    ['operation', 'component']
)

# Cache metrics
CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

def start_metrics_server(port: int = 8000):
    """Start Prometheus metrics server"""
    try:
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")

def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

def record_lesson_created():
    """Record lesson creation"""
    LESSONS_CREATED.inc()

def record_lesson_exported():
    """Record lesson export"""
    LESSONS_EXPORTED.inc()

def record_slide_processed(parser_type: str):
    """Record slide processing"""
    SLIDES_PROCESSED.labels(parser_type=parser_type).inc()

def record_ocr_request(provider: str, status: str):
    """Record OCR request"""
    OCR_REQUESTS.labels(provider=provider, status=status).inc()

def record_tts_request(provider: str, status: str):
    """Record TTS request"""
    TTS_REQUESTS.labels(provider=provider, status=status).inc()

def record_llm_request(provider: str, status: str):
    """Record LLM request"""
    LLM_REQUESTS.labels(provider=provider, status=status).inc()

def record_error(error_type: str, component: str):
    """Record error"""
    ERROR_COUNT.labels(error_type=error_type, component=component).inc()

def record_processing_time(operation: str, component: str, duration: float):
    """Record processing time"""
    PROCESSING_TIME.labels(operation=operation, component=component).observe(duration)

def record_cache_hit(cache_type: str):
    """Record cache hit"""
    CACHE_HITS.labels(cache_type=cache_type).inc()

def record_cache_miss(cache_type: str):
    """Record cache miss"""
    CACHE_MISSES.labels(cache_type=cache_type).inc()

def update_active_tasks(task_type: str, count: int):
    """Update active tasks count"""
    ACTIVE_TASKS.labels(task_type=task_type).set(count)

def update_queue_size(queue_name: str, size: int):
    """Update queue size"""
    QUEUE_SIZE.labels(queue_name=queue_name).set(size)

def update_memory_usage():
    """Update memory usage"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        MEMORY_USAGE.set(memory_info.rss)
    except ImportError:
        logger.warning("psutil not available for memory monitoring")

def update_disk_usage(path: str):
    """Update disk usage for a path"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        DISK_USAGE.labels(path=path).set(used)
    except Exception as e:
        logger.warning(f"Failed to update disk usage for {path}: {e}")

# Decorator for automatic metrics collection
def monitor_operation(operation: str, component: str):
    """Decorator to monitor operation execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                record_processing_time(operation, component, time.time() - start_time)
                return result
            except Exception as e:
                record_error(type(e).__name__, component)
                record_processing_time(operation, component, time.time() - start_time)
                raise
        return wrapper
    return decorator