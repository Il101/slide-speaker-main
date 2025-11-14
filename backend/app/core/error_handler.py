"""
Centralized error handling with circuit breaker and retry logic
Follows industry best practices from Netflix Hystrix and AWS SDK
"""
import logging
import asyncio
from typing import TypeVar, Callable, Any, Optional
from functools import wraps
import time
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    logger.warning("tenacity not installed - retry functionality disabled")

try:
    from circuitbreaker import circuit
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False
    logger.warning("circuitbreaker not installed - circuit breaker disabled")


T = TypeVar('T')


class ErrorCategory(Enum):
    """Error categories for handling strategy"""
    TRANSIENT = "transient"  # Temporary errors (network, rate limit)
    PERMANENT = "permanent"  # Permanent errors (invalid input, auth)
    TIMEOUT = "timeout"      # Timeout errors
    RESOURCE = "resource"    # Resource exhaustion (memory, disk)
    UNKNOWN = "unknown"      # Unknown errors


class RetryableError(Exception):
    """Base exception for errors that should be retried"""
    pass


class RateLimitError(RetryableError):
    """API rate limit exceeded"""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class ServiceUnavailableError(RetryableError):
    """External service temporarily unavailable"""
    pass


class TimeoutError(RetryableError):
    """Operation timed out"""
    pass


class PermanentError(Exception):
    """Error that should NOT be retried"""
    pass


class ErrorHandler:
    """Centralized error handler with circuit breaker and retry"""
    
    def __init__(
        self,
        max_retries: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 10.0,
        circuit_failure_threshold: int = 5,
        circuit_recovery_timeout: int = 60
    ):
        self.max_retries = max_retries
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.circuit_failure_threshold = circuit_failure_threshold
        self.circuit_recovery_timeout = circuit_recovery_timeout
    
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error to determine handling strategy"""
        if isinstance(error, RateLimitError):
            return ErrorCategory.TRANSIENT
        elif isinstance(error, ServiceUnavailableError):
            return ErrorCategory.TRANSIENT
        elif isinstance(error, TimeoutError):
            return ErrorCategory.TIMEOUT
        elif isinstance(error, PermanentError):
            return ErrorCategory.PERMANENT
        elif isinstance(error, (ConnectionError, OSError)):
            return ErrorCategory.TRANSIENT
        else:
            return ErrorCategory.UNKNOWN
    
    def with_retry(
        self,
        func: Optional[Callable] = None,
        max_attempts: Optional[int] = None,
        exceptions: tuple = (RetryableError,)
    ):
        """
        Decorator for automatic retry with exponential backoff
        
        Example:
            @error_handler.with_retry(max_attempts=3)
            async def call_api():
                ...
        """
        if not TENACITY_AVAILABLE:
            # Fallback: no retry
            def decorator(f):
                return f
            return decorator(func) if func else decorator
        
        max_attempts = max_attempts or self.max_retries
        
        def decorator(f):
            @retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(
                    multiplier=1,
                    min=self.min_wait,
                    max=self.max_wait
                ),
                retry=retry_if_exception_type(exceptions),
                before_sleep=before_sleep_log(logger, logging.WARNING)
            )
            @wraps(f)
            async def wrapper(*args, **kwargs):
                return await f(*args, **kwargs)
            
            return wrapper
        
        return decorator(func) if func else decorator
    
    def with_circuit_breaker(
        self,
        func: Optional[Callable] = None,
        failure_threshold: Optional[int] = None,
        recovery_timeout: Optional[int] = None,
        expected_exception: type = Exception
    ):
        """
        Decorator for circuit breaker pattern
        
        Prevents cascading failures by failing fast when service is down
        
        Example:
            @error_handler.with_circuit_breaker(failure_threshold=5)
            async def call_external_api():
                ...
        """
        if not CIRCUIT_BREAKER_AVAILABLE:
            # Fallback: no circuit breaker
            def decorator(f):
                return f
            return decorator(func) if func else decorator
        
        failure_threshold = failure_threshold or self.circuit_failure_threshold
        recovery_timeout = recovery_timeout or self.circuit_recovery_timeout
        
        def decorator(f):
            @circuit(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception
            )
            @wraps(f)
            async def wrapper(*args, **kwargs):
                return await f(*args, **kwargs)
            
            return wrapper
        
        return decorator(func) if func else decorator
    
    async def safe_execute(
        self,
        func: Callable[..., T],
        *args,
        fallback_value: Optional[T] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        **kwargs
    ) -> T:
        """
        Safely execute function with error handling
        
        Args:
            func: Function to execute
            *args: Function arguments
            fallback_value: Value to return on error
            on_error: Optional error callback
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or fallback value
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            
            # Report error to monitoring
            if on_error:
                try:
                    on_error(e)
                except Exception as callback_error:
                    logger.error(f"Error callback failed: {callback_error}")
            
            # Report to Sentry if available
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(e)
            except ImportError:
                pass
            
            # Return fallback
            if fallback_value is not None:
                logger.info(f"Returning fallback value for {func.__name__}")
                return fallback_value
            
            # Re-raise if no fallback
            raise


# Global error handler instance
error_handler = ErrorHandler()


# Convenience decorators
def with_retry(
    max_attempts: int = 3,
    exceptions: tuple = (RetryableError,)
):
    """Convenience decorator for retry"""
    return error_handler.with_retry(max_attempts=max_attempts, exceptions=exceptions)


def with_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
):
    """Convenience decorator for circuit breaker"""
    return error_handler.with_circuit_breaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception
    )


async def safe_execute(
    func: Callable[..., T],
    *args,
    fallback_value: Optional[T] = None,
    **kwargs
) -> T:
    """Convenience function for safe execution"""
    return await error_handler.safe_execute(
        func,
        *args,
        fallback_value=fallback_value,
        **kwargs
    )


# Context manager for error handling
class ErrorContext:
    """Context manager for structured error handling"""
    
    def __init__(
        self,
        operation: str,
        fallback_value: Any = None,
        reraise: bool = False
    ):
        self.operation = operation
        self.fallback_value = fallback_value
        self.reraise = reraise
        self.start_time = None
        self.error = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.debug(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        
        if exc_type is None:
            logger.debug(f"Operation '{self.operation}' completed in {elapsed:.2f}s")
            return True
        
        # Error occurred
        self.error = exc_val
        logger.error(
            f"Operation '{self.operation}' failed after {elapsed:.2f}s: {exc_val}",
            exc_info=(exc_type, exc_val, exc_tb)
        )
        
        # Report to monitoring
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc_val)
        except ImportError:
            pass
        
        # Suppress exception if not reraising
        return not self.reraise


# Example usage in services
class ExampleServiceWithErrorHandling:
    """Example service demonstrating error handling"""
    
    @with_retry(max_attempts=3, exceptions=(RateLimitError, ServiceUnavailableError))
    @with_circuit_breaker(failure_threshold=5, recovery_timeout=60)
    async def call_external_api(self, endpoint: str) -> dict:
        """Call external API with retry and circuit breaker"""
        # Simulate API call
        import httpx
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(endpoint, timeout=10.0)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise RateLimitError(
                        f"Rate limit exceeded for {endpoint}",
                        retry_after=retry_after
                    )
                
                # Handle service unavailable
                if response.status_code in [502, 503, 504]:
                    raise ServiceUnavailableError(
                        f"Service unavailable: {endpoint}"
                    )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.TimeoutException:
                raise TimeoutError(f"Request to {endpoint} timed out")
            except httpx.HTTPError as e:
                logger.error(f"HTTP error calling {endpoint}: {e}")
                raise
    
    async def process_with_fallback(self, data: dict) -> dict:
        """Process data with fallback"""
        return await safe_execute(
            self._process_complex_data,
            data,
            fallback_value={"status": "fallback", "data": {}}
        )
    
    async def _process_complex_data(self, data: dict) -> dict:
        """Complex processing that might fail"""
        # Simulate processing
        if not data:
            raise ValueError("Empty data")
        return {"status": "success", "data": data}


# Async context manager
class AsyncErrorContext:
    """Async context manager for error handling"""
    
    def __init__(
        self,
        operation: str,
        fallback_value: Any = None
    ):
        self.operation = operation
        self.fallback_value = fallback_value
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        logger.debug(f"Starting async operation: {self.operation}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        
        if exc_type is None:
            logger.debug(f"Async operation '{self.operation}' completed in {elapsed:.2f}s")
            return False
        
        logger.error(
            f"Async operation '{self.operation}' failed: {exc_val}",
            exc_info=(exc_type, exc_val, exc_tb)
        )
        
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc_val)
        except ImportError:
            pass
        
        return False  # Don't suppress exception
