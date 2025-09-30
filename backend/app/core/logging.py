"""Structured logging configuration"""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'lesson_id'):
            log_entry["lesson_id"] = record.lesson_id
        
        return json.dumps(log_entry, ensure_ascii=False)

class ContextFilter(logging.Filter):
    """Filter to add context to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add default context fields
        record.request_id = getattr(record, 'request_id', None)
        record.user_id = getattr(record, 'user_id', None)
        record.lesson_id = getattr(record, 'lesson_id', None)
        return True

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = True
) -> None:
    """Setup structured logging configuration"""
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ContextFilter())
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(ContextFilter())
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with structured logging"""
    return logging.getLogger(name)

def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context: Any
) -> None:
    """Log a message with additional context"""
    extra_fields = context
    getattr(logger, level.lower())(message, extra={'extra_fields': extra_fields})

def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration: float,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> None:
    """Log HTTP request with structured data"""
    log_with_context(
        logger,
        "info",
        f"{method} {path} {status_code}",
        method=method,
        path=path,
        status_code=status_code,
        duration=duration,
        request_id=request_id,
        user_id=user_id,
        event_type="http_request"
    )

def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Log error with structured data"""
    error_context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "event_type": "error"
    }
    
    if context:
        error_context.update(context)
    
    log_with_context(
        logger,
        "error",
        f"Error: {type(error).__name__}: {str(error)}",
        **error_context
    )

def log_business_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    **context: Any
) -> None:
    """Log business event with structured data"""
    log_with_context(
        logger,
        "info",
        message,
        event_type=event_type,
        **context
    )

def log_performance(
    logger: logging.Logger,
    operation: str,
    duration: float,
    **context: Any
) -> None:
    """Log performance metrics"""
    log_with_context(
        logger,
        "info",
        f"Performance: {operation} took {duration:.3f}s",
        operation=operation,
        duration=duration,
        event_type="performance",
        **context
    )

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    setup_logging(level="DEBUG", structured=True)
    
    # Get logger
    logger = get_logger(__name__)
    
    # Test different log levels
    logger.info("Application started")
    logger.warning("This is a warning")
    logger.error("This is an error")
    
    # Test structured logging
    log_with_context(
        logger,
        "info",
        "User uploaded file",
        user_id="user123",
        file_size=1024,
        file_type="pdf"
    )
    
    # Test request logging
    log_request(
        logger,
        "POST",
        "/upload",
        200,
        1.5,
        request_id="req123",
        user_id="user123"
    )
    
    # Test business event logging
    log_business_event(
        logger,
        "lesson_created",
        "New lesson created",
        lesson_id="lesson123",
        slide_count=10
    )
    
    # Test performance logging
    log_performance(
        logger,
        "document_parsing",
        2.3,
        file_type="pptx",
        slide_count=10
    )