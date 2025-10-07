"""
Pipeline Result - для отслеживания частичного успеха
"""
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SlideResult:
    """Результат обработки одного слайда"""
    slide_index: int
    slide_id: int
    status: str  # "success", "failed", "skipped"
    error: str = None
    processing_time: float = 0.0
    warnings: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Результат обработки презентации с поддержкой частичного успеха"""
    
    lesson_id: str
    total_slides: int
    successful_slides: List[SlideResult] = field(default_factory=list)
    failed_slides: List[SlideResult] = field(default_factory=list)
    skipped_slides: List[SlideResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime = None
    
    def add_success(self, slide_index: int, slide_id: int, processing_time: float = 0.0, warnings: List[str] = None):
        """Добавить успешно обработанный слайд"""
        result = SlideResult(
            slide_index=slide_index,
            slide_id=slide_id,
            status="success",
            processing_time=processing_time,
            warnings=warnings or []
        )
        self.successful_slides.append(result)
    
    def add_failure(self, slide_index: int, slide_id: int, error: Exception, processing_time: float = 0.0):
        """Добавить неудавшийся слайд"""
        result = SlideResult(
            slide_index=slide_index,
            slide_id=slide_id,
            status="failed",
            error=str(error),
            processing_time=processing_time
        )
        self.failed_slides.append(result)
    
    def add_skip(self, slide_index: int, slide_id: int, reason: str):
        """Добавить пропущенный слайд"""
        result = SlideResult(
            slide_index=slide_index,
            slide_id=slide_id,
            status="skipped",
            error=reason,
            processing_time=0.0
        )
        self.skipped_slides.append(result)
    
    @property
    def success_count(self) -> int:
        """Количество успешно обработанных слайдов"""
        return len(self.successful_slides)
    
    @property
    def failed_count(self) -> int:
        """Количество неудавшихся слайдов"""
        return len(self.failed_slides)
    
    @property
    def success_rate(self) -> float:
        """Процент успешно обработанных слайдов"""
        if self.total_slides == 0:
            return 0.0
        return self.success_count / self.total_slides
    
    def is_usable(self, min_success_rate: float = 0.5) -> bool:
        """
        Можно ли использовать результат?
        По умолчанию требуется минимум 50% успешных слайдов
        """
        return self.success_rate >= min_success_rate
    
    def get_overall_status(self) -> str:
        """Получить общий статус обработки"""
        if self.failed_count == 0 and self.success_count == self.total_slides:
            return "success"
        elif self.is_usable():
            return "partial_success"
        else:
            return "failed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь для API response"""
        return {
            "lesson_id": self.lesson_id,
            "status": self.get_overall_status(),
            "total_slides": self.total_slides,
            "successful": self.success_count,
            "failed": self.failed_count,
            "skipped": len(self.skipped_slides),
            "success_rate": round(self.success_rate, 3),
            "usable": self.is_usable(),
            "processing_time": round(self.processing_time, 2),
            "warnings": self.warnings,
            "failed_slides": [
                {
                    "slide_index": s.slide_index,
                    "slide_id": s.slide_id,
                    "error": s.error
                }
                for s in self.failed_slides
            ],
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    def get_detailed_report(self) -> str:
        """Получить детальный текстовый отчёт"""
        lines = [
            f"📊 Pipeline Result: {self.lesson_id}",
            f"Status: {self.get_overall_status().upper()}",
            f"",
            f"✅ Successful: {self.success_count}/{self.total_slides} ({self.success_rate*100:.1f}%)",
            f"❌ Failed: {self.failed_count}",
            f"⏭️  Skipped: {len(self.skipped_slides)}",
            f"⏱️  Processing time: {self.processing_time:.1f}s",
        ]
        
        if self.warnings:
            lines.append(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.failed_slides:
            lines.append("\nFailed slides:")
            for fail in self.failed_slides:
                lines.append(f"  - Slide {fail.slide_id} (#{fail.slide_index}): {fail.error[:100]}")
        
        return "\n".join(lines)
    
    def mark_completed(self):
        """Пометить как завершённый"""
        self.completed_at = datetime.utcnow()
        self.processing_time = (self.completed_at - self.started_at).total_seconds()
