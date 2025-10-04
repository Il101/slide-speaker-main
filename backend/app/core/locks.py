"""Distributed locks using Redis for Celery tasks"""
import redis
import time
import uuid
import logging
from typing import Optional, ContextManager
from contextlib import contextmanager
from .config import settings

logger = logging.getLogger(__name__)

class DistributedLock:
    """Redis-based distributed lock implementation with improved reliability"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis.from_url(settings.REDIS_URL)
        self.default_timeout = 600  # 10 minutes default timeout (reduced from 30 min)
        self.default_blocking_timeout = 5  # 5 seconds to wait for lock (reduced from 30 sec)
    
    def _get_lock_key(self, resource: str) -> str:
        """Generate lock key for resource"""
        return f"lock:{resource}"
    
    def _get_lock_value(self) -> str:
        """Generate unique lock value"""
        return str(uuid.uuid4())
    
    def acquire(self, resource: str, timeout: Optional[int] = None, 
                blocking_timeout: Optional[int] = None) -> Optional[str]:
        """
        Acquire a distributed lock
        
        Args:
            resource: Resource identifier to lock
            timeout: Lock expiration time in seconds (default: 300)
            blocking_timeout: Time to wait for lock acquisition (default: 10)
            
        Returns:
            Lock value if acquired, None if failed
        """
        lock_key = self._get_lock_key(resource)
        lock_value = self._get_lock_value()
        timeout = timeout or self.default_timeout
        blocking_timeout = blocking_timeout or self.default_blocking_timeout
        
        end_time = time.time() + blocking_timeout
        
        while time.time() < end_time:
            # Try to acquire lock using SET with NX and EX
            if self.redis_client.set(lock_key, lock_value, nx=True, ex=timeout):
                logger.info(f"Acquired lock for resource: {resource}")
                return lock_value
            
            # Wait a bit before retrying
            time.sleep(0.1)
        
        logger.warning(f"Failed to acquire lock for resource: {resource}")
        return None
    
    def release(self, resource: str, lock_value: str) -> bool:
        """
        Release a distributed lock
        
        Args:
            resource: Resource identifier
            lock_value: Lock value returned by acquire()
            
        Returns:
            True if released successfully, False otherwise
        """
        lock_key = self._get_lock_key(resource)
        
        # Use Lua script to atomically check and delete lock
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        
        result = self.redis_client.eval(lua_script, 1, lock_key, lock_value)
        
        if result:
            logger.info(f"Released lock for resource: {resource}")
            return True
        else:
            logger.warning(f"Failed to release lock for resource: {resource} (lock value mismatch)")
            return False
    
    def extend(self, resource: str, lock_value: str, additional_time: int) -> bool:
        """
        Extend lock expiration time
        
        Args:
            resource: Resource identifier
            lock_value: Lock value returned by acquire()
            additional_time: Additional time in seconds
            
        Returns:
            True if extended successfully, False otherwise
        """
        lock_key = self._get_lock_key(resource)
        
        # Use Lua script to atomically check and extend lock
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("EXPIRE", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        
        result = self.redis_client.eval(lua_script, 1, lock_key, lock_value, additional_time)
        
        if result:
            logger.info(f"Extended lock for resource: {resource} by {additional_time}s")
            return True
        else:
            logger.warning(f"Failed to extend lock for resource: {resource}")
            return False
    
    def is_locked(self, resource: str) -> bool:
        """
        Check if resource is currently locked
        
        Args:
            resource: Resource identifier
            
        Returns:
            True if locked, False otherwise
        """
        lock_key = self._get_lock_key(resource)
        return self.redis_client.exists(lock_key) > 0
    
    def cleanup_expired_locks(self) -> int:
        """
        Clean up expired locks (TTL <= 0)
        
        Returns:
            Number of locks cleaned up
        """
        cleaned_count = 0
        try:
            # Get all lock keys
            lock_keys = self.redis_client.keys("lock:*")
            
            for key in lock_keys:
                ttl = self.redis_client.ttl(key)
                # If TTL is -1 (no expiration) or -2 (expired), delete the key
                if ttl <= 0:
                    self.redis_client.delete(key)
                    cleaned_count += 1
                    logger.info(f"Cleaned up expired lock: {key.decode('utf-8')}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired locks")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired locks: {e}")
        
        return cleaned_count
    
    def force_release_lock(self, resource: str) -> bool:
        """
        Force release a lock (use with caution)
        
        Args:
            resource: Resource identifier
            
        Returns:
            True if released, False otherwise
        """
        lock_key = self._get_lock_key(resource)
        try:
            result = self.redis_client.delete(lock_key)
            if result:
                logger.warning(f"Force released lock for resource: {resource}")
                return True
            else:
                logger.info(f"No lock found for resource: {resource}")
                return False
        except Exception as e:
            logger.error(f"Error force releasing lock for {resource}: {e}")
            return False
    
    @contextmanager
    def lock(self, resource: str, timeout: Optional[int] = None, 
             blocking_timeout: Optional[int] = None):
        """
        Context manager for distributed lock
        
        Args:
            resource: Resource identifier to lock
            timeout: Lock expiration time in seconds
            blocking_timeout: Time to wait for lock acquisition
            
        Yields:
            Lock value if acquired
            
        Raises:
            TimeoutError: If lock cannot be acquired within blocking_timeout
        """
        lock_value = self.acquire(resource, timeout, blocking_timeout)
        
        if not lock_value:
            raise TimeoutError(f"Could not acquire lock for resource: {resource}")
        
        try:
            yield lock_value
        finally:
            self.release(resource, lock_value)

# Global lock instance
distributed_lock = DistributedLock()

# Decorator for Celery tasks with distributed locks
def with_distributed_lock(resource_func, timeout: Optional[int] = None, 
                         blocking_timeout: Optional[int] = None):
    """
    Decorator to add distributed locking to Celery tasks with improved reliability
    
    Args:
        resource_func: Function that returns resource identifier from task args
        timeout: Lock expiration time in seconds
        blocking_timeout: Time to wait for lock acquisition
        
    Returns:
        Decorated task function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get resource identifier
            resource = resource_func(*args, **kwargs)
            
            # Clean up expired locks before attempting to acquire
            distributed_lock.cleanup_expired_locks()
            
            # Check if resource is already locked
            if distributed_lock.is_locked(resource):
                logger.warning(f"Resource {resource} is already locked, attempting cleanup...")
                # Try to force release if it's been locked too long
                distributed_lock.force_release_lock(resource)
            
            # Acquire lock
            lock_value = distributed_lock.acquire(resource, timeout, blocking_timeout)
            if not lock_value:
                logger.warning(f"Task {func.__name__} skipped - could not acquire lock for {resource}")
                return {"status": "skipped", "reason": "lock_not_acquired", "resource": resource}
            
            logger.info(f"Task {func.__name__} acquired lock for {resource}")
            
            try:
                # Execute task
                result = func(*args, **kwargs)
                logger.info(f"Task {func.__name__} completed successfully for {resource}")
                return result
            except Exception as e:
                logger.error(f"Task {func.__name__} failed for {resource}: {e}")
                raise
            finally:
                # Release lock
                released = distributed_lock.release(resource, lock_value)
                if released:
                    logger.info(f"Task {func.__name__} released lock for {resource}")
                else:
                    logger.warning(f"Task {func.__name__} failed to release lock for {resource}")
        
        return wrapper
    return decorator

# Common resource functions for different task types
def lesson_resource(lesson_id: str, *args, **kwargs) -> str:
    """Resource function for lesson processing tasks"""
    return f"lesson:{lesson_id}"

def slide_resource(lesson_id: str, slide_id: str, *args, **kwargs) -> str:
    """Resource function for slide processing tasks"""
    return f"slide:{lesson_id}:{slide_id}"

def export_resource(lesson_id: str, *args, **kwargs) -> str:
    """Resource function for export tasks"""
    return f"export:{lesson_id}"

def cleanup_resource(lesson_id: Optional[str] = None, *args, **kwargs) -> str:
    """Resource function for cleanup tasks"""
    if lesson_id:
        return f"cleanup:lesson:{lesson_id}"
    return "cleanup:global"
