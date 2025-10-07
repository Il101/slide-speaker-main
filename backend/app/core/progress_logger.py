"""
Progress Logger - оптимизированное логирование для циклов
✅ FIX: Уменьшает объём логов в 10 раз
"""
import logging
import time
from typing import Optional


class ProgressLogger:
    """
    Логгер прогресса для больших циклов
    
    ✅ FIX: Вместо логирования каждого элемента (100 строк для 100 слайдов)
    логирует только каждые N элементов (10 строк для 100 слайдов).
    
    Уменьшение объёма логов в 10 раз + небольшое ускорение (5-10%).
    """
    
    def __init__(
        self, 
        total: int, 
        log_interval: int = 10,
        logger: Optional[logging.Logger] = None,
        task_name: str = "Processing"
    ):
        """
        Args:
            total: Общее количество элементов
            log_interval: Логировать каждые N элементов (default: 10)
            logger: Logger instance (если None, создаётся новый)
            task_name: Название задачи для логов
        """
        self.total = total
        self.log_interval = log_interval
        self.logger = logger or logging.getLogger(__name__)
        self.task_name = task_name
        
        self.last_logged = 0
        self.start_time = time.time()
        self.last_log_time = self.start_time
    
    def log_progress(self, current: int, message: Optional[str] = None):
        """
        Логировать прогресс
        
        Args:
            current: Текущий номер элемента (1-based)
            message: Дополнительное сообщение (опционально)
        """
        # Логируем если:
        # 1. Прошло достаточно элементов
        # 2. Это последний элемент
        should_log = (
            current - self.last_logged >= self.log_interval or 
            current == self.total
        )
        
        if not should_log:
            return
        
        # Вычисляем статистику
        elapsed = time.time() - self.start_time
        percent = (current / self.total * 100) if self.total > 0 else 0
        
        # Оценка оставшегося времени
        if current > 0:
            items_per_sec = current / elapsed if elapsed > 0 else 0
            remaining_items = self.total - current
            eta_seconds = remaining_items / items_per_sec if items_per_sec > 0 else 0
            eta_str = self._format_time(eta_seconds)
        else:
            eta_str = "unknown"
        
        # Формируем сообщение
        base_msg = f"{self.task_name}: {current}/{self.total} ({percent:.1f}%) | Elapsed: {self._format_time(elapsed)} | ETA: {eta_str}"
        
        if message:
            base_msg += f" | {message}"
        
        self.logger.info(base_msg)
        
        self.last_logged = current
        self.last_log_time = time.time()
    
    def log_item(self, current: int, item_name: str, status: str = "✓"):
        """
        Логировать отдельный элемент с кратким статусом
        
        Args:
            current: Текущий номер (1-based)
            item_name: Название элемента
            status: Статус (✓, ✗, ⚠, ⏭)
        """
        message = f"{status} {item_name}"
        self.log_progress(current, message)
    
    def log_completion(self, success_count: Optional[int] = None):
        """
        Логировать завершение
        
        Args:
            success_count: Количество успешных (если отличается от total)
        """
        elapsed = time.time() - self.start_time
        
        if success_count is not None and success_count < self.total:
            success_rate = (success_count / self.total * 100) if self.total > 0 else 0
            self.logger.info(
                f"✅ {self.task_name} completed: {success_count}/{self.total} "
                f"({success_rate:.1f}%) in {self._format_time(elapsed)}"
            )
        else:
            self.logger.info(
                f"✅ {self.task_name} completed: {self.total} items "
                f"in {self._format_time(elapsed)}"
            )
    
    def log_error(self, current: int, item_name: str, error: Exception):
        """
        Логировать ошибку
        
        Args:
            current: Текущий номер
            item_name: Название элемента
            error: Exception
        """
        self.logger.error(
            f"❌ {self.task_name} [{current}/{self.total}] {item_name}: {str(error)}"
        )
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Форматировать время в читаемый вид"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def __enter__(self):
        """Context manager support"""
        self.logger.info(f"🚀 Starting {self.task_name}: {self.total} items")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        if exc_type is None:
            self.log_completion()
        else:
            elapsed = time.time() - self.start_time
            self.logger.error(
                f"❌ {self.task_name} failed after {self._format_time(elapsed)}: {exc_val}"
            )


# Пример использования:
"""
# Было (100 строк в логе):
for i, slide in enumerate(slides):
    logger.info(f"Processing slide {i+1}/{len(slides)}")
    process_slide(slide)

# Стало (10 строк в логе):
progress = ProgressLogger(total=len(slides), log_interval=10, task_name="Processing slides")
for i, slide in enumerate(slides):
    process_slide(slide)
    progress.log_progress(i + 1)

# Или с context manager:
with ProgressLogger(len(slides), log_interval=10, task_name="Slides") as progress:
    for i, slide in enumerate(slides):
        try:
            process_slide(slide)
            progress.log_item(i + 1, f"slide_{slide.id}", "✓")
        except Exception as e:
            progress.log_error(i + 1, f"slide_{slide.id}", e)
"""
