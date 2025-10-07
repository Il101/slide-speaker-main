"""Sentry integration for error tracking and monitoring"""
import os
import logging
from typing import Optional, Dict, Any
from fastapi import Request
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Sentry is optional - check if installed
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None
    logger.warning("Sentry SDK not installed. Install with: pip install sentry-sdk[fastapi]")


def init_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1
):
    """
    Initialize Sentry for error tracking
    
    Args:
        dsn: Sentry DSN (Data Source Name). Get from Sentry project settings.
        environment: Environment name (e.g., "production", "staging", "development")
        release: Release version (e.g., git commit hash)
        traces_sample_rate: Sample rate for performance monitoring (0.0 to 1.0)
        profiles_sample_rate: Sample rate for profiling (0.0 to 1.0)
        
    Example:
        # In main.py or startup:
        from app.core.sentry import init_sentry
        
        init_sentry(
            dsn=os.getenv("SENTRY_DSN"),
            environment=os.getenv("ENVIRONMENT", "development"),
            release=os.getenv("GIT_COMMIT", "unknown")
        )
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry not available - skipping initialization")
        return
    
    # Get DSN from env if not provided
    if not dsn:
        dsn = os.getenv("SENTRY_DSN")
    
    if not dsn:
        logger.info("SENTRY_DSN not configured - Sentry disabled")
        return
    
    # Get environment from env if not provided
    if not environment:
        environment = os.getenv("ENVIRONMENT", "development")
    
    # Get release from env if not provided
    if not release:
        release = os.getenv("GIT_COMMIT") or os.getenv("RELEASE_VERSION", "unknown")
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            # Performance monitoring
            traces_sample_rate=traces_sample_rate,
            # Profiling
            profiles_sample_rate=profiles_sample_rate,
            # Integrations
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint"  # Group by endpoint, not URL
                ),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration(
                    monitor_beat_tasks=True  # Monitor Celery beat tasks
                ),
                LoggingIntegration(
                    level=logging.INFO,        # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors and above as events
                ),
            ],
            # Send default PII (Personally Identifiable Information)
            send_default_pii=False,  # Set to True to include user IP, cookies, etc.
            # Attach stack traces to log messages
            attach_stacktrace=True,
            # Maximum breadcrumbs to keep
            max_breadcrumbs=50,
            # Before send hook to modify events
            before_send=before_send_hook,
            # Before breadcrumb hook
            before_breadcrumb=before_breadcrumb_hook,
        )
        
        logger.info(f"✅ Sentry initialized: environment={environment}, release={release}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_hook(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook to modify or filter events before sending to Sentry
    
    Args:
        event: Sentry event dict
        hint: Additional context
        
    Returns:
        Modified event or None to drop the event
    """
    # Example: Filter out certain errors
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        
        # Don't send HTTPException 404s to Sentry
        if exc_type.__name__ == 'HTTPException':
            if hasattr(exc_value, 'status_code') and exc_value.status_code == 404:
                return None
    
    # Add custom tags
    event.setdefault('tags', {})
    event['tags']['service'] = 'slide-speaker'
    
    return event


def before_breadcrumb_hook(crumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook to modify or filter breadcrumbs before adding to event
    
    Args:
        crumb: Breadcrumb dict
        hint: Additional context
        
    Returns:
        Modified breadcrumb or None to drop it
    """
    # Example: Filter out noisy logs
    if crumb.get('category') == 'httpx':
        # Don't track all HTTP requests as breadcrumbs
        return None
    
    return crumb


def capture_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
):
    """
    Manually capture an exception to Sentry
    
    Args:
        error: Exception to capture
        context: Additional context dict
        level: Severity level ("fatal", "error", "warning", "info", "debug")
        
    Example:
        try:
            risky_operation()
        except Exception as e:
            capture_exception(e, context={
                "user_id": user_id,
                "operation": "presentation_upload"
            })
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        logger.error(f"Exception captured (Sentry not available): {error}", exc_info=True)
        return
    
    with sentry_sdk.push_scope() as scope:
        scope.level = level
        
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        sentry_sdk.capture_exception(error)


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[Dict[str, Any]] = None
):
    """
    Manually capture a message to Sentry
    
    Args:
        message: Message to capture
        level: Severity level
        context: Additional context dict
        
    Example:
        capture_message(
            "User exceeded rate limit",
            level="warning",
            context={"user_id": user_id, "endpoint": "/upload"}
        )
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        logger.log(getattr(logging, level.upper(), logging.INFO), f"Message: {message}")
        return
    
    with sentry_sdk.push_scope() as scope:
        scope.level = level
        
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        sentry_sdk.capture_message(message)


def set_user_context(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    """
    Set user context for Sentry events
    
    Args:
        user_id: User ID
        email: User email (optional)
        username: Username (optional)
        
    Example:
        # In authentication middleware
        set_user_context(
            user_id=current_user.id,
            email=current_user.email,
            username=current_user.username
        )
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return
    
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username
    })


def set_context(key: str, value: Dict[str, Any]):
    """
    Set custom context for Sentry events
    
    Args:
        key: Context key
        value: Context data dict
        
    Example:
        set_context("presentation", {
            "id": lesson_id,
            "slides": 10,
            "format": "pptx"
        })
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return
    
    sentry_sdk.set_context(key, value)


def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None
):
    """
    Add a breadcrumb to track application flow
    
    Args:
        message: Breadcrumb message
        category: Category (e.g., "auth", "processing", "api")
        level: Severity level
        data: Additional data dict
        
    Example:
        add_breadcrumb(
            message="Starting presentation processing",
            category="processing",
            level="info",
            data={"lesson_id": lesson_id, "slides": 10}
        )
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return
    
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


@contextmanager
def sentry_transaction(name: str, op: str = "function"):
    """
    Context manager for manual transaction tracking
    
    Args:
        name: Transaction name
        op: Operation type (e.g., "function", "task", "query")
        
    Example:
        with sentry_transaction("process_presentation", op="task"):
            process_full_pipeline(lesson_id)
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        yield None
        return
    
    with sentry_sdk.start_transaction(name=name, op=op) as transaction:
        yield transaction


# FastAPI middleware to add request context to Sentry
async def sentry_middleware(request: Request, call_next):
    """
    Middleware to add request context to Sentry events
    
    Add to FastAPI app:
        from app.core.sentry import sentry_middleware
        app.middleware("http")(sentry_middleware)
    """
    if SENTRY_AVAILABLE and sentry_sdk:
        with sentry_sdk.configure_scope() as scope:
            # Add request info
            scope.set_context("request", {
                "url": str(request.url),
                "method": request.method,
                "headers": dict(request.headers),
                "query_params": dict(request.query_params)
            })
            
            # Add user info if available
            if hasattr(request.state, 'user'):
                user = request.state.user
                set_user_context(
                    user_id=user.get('user_id', 'anonymous'),
                    email=user.get('email'),
                    username=user.get('username')
                )
    
    response = await call_next(request)
    return response


# Performance monitoring helpers
class SentrySpan:
    """Helper class for performance monitoring spans"""
    
    def __init__(self, operation: str, description: Optional[str] = None):
        self.operation = operation
        self.description = description
        self.span = None
    
    def __enter__(self):
        if SENTRY_AVAILABLE and sentry_sdk:
            self.span = sentry_sdk.start_span(
                op=self.operation,
                description=self.description
            )
            self.span.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.__exit__(exc_type, exc_val, exc_tb)


def monitor_performance(operation: str):
    """
    Decorator to monitor function performance
    
    Args:
        operation: Operation name
        
    Example:
        @monitor_performance("database.query")
        async def get_user(user_id: str):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with SentrySpan(operation, description=func.__name__):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
