"""Cost tracking utility for analytics"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

from ..core.database import CostLog

async def track_cost(
    db: AsyncSession,
    operation: str,  # 'ocr', 'ai_generation', 'tts', 'storage'
    cost: float,
    user_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    meta_data: Optional[Dict[str, Any]] = None
):
    """
    Track a cost event to the database
    
    Args:
        db: Database session
        operation: Type of operation ('ocr', 'ai_generation', 'tts', 'storage')
        cost: Cost in dollars
        user_id: Optional user ID
        lesson_id: Optional lesson ID
        meta_data: Optional additional metadata
    """
    try:
        cost_log = CostLog(
            id=str(uuid.uuid4()),
            operation=operation,
            cost=cost,
            user_id=user_id,
            lesson_id=lesson_id,
            timestamp=datetime.utcnow(),
            meta_data=meta_data or {}
        )
        
        db.add(cost_log)
        await db.commit()
    except Exception as e:
        print(f"Cost tracking error: {e}")
        # Don't raise - we don't want cost tracking to break the main flow

# Helper functions for common operations

async def track_ocr_cost(
    db: AsyncSession,
    slide_count: int,
    user_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    file_name: Optional[str] = None
):
    """Track OCR operation cost"""
    # Google Vision API: $1.50 per 1,000 units
    cost = (slide_count * 1.50) / 1000
    
    await track_cost(
        db=db,
        operation="ocr",
        cost=cost,
        user_id=user_id,
        lesson_id=lesson_id,
        meta_data={
            "slide_count": slide_count,
            "file_name": file_name,
            "unit_price": 1.50,
            "provider": "google_vision"
        }
    )

async def track_ai_generation_cost(
    db: AsyncSession,
    model: str,
    input_tokens: int,
    output_tokens: int,
    user_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    slide_number: Optional[int] = None
):
    """Track AI generation cost (Gemini, OpenAI, etc.)"""
    # Pricing varies by model
    pricing = {
        "gemini-1.5-flash": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        "gemini-1.5-pro": {"input": 1.25 / 1_000_000, "output": 5.00 / 1_000_000},
        "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        "gpt-4": {"input": 30.00 / 1_000_000, "output": 60.00 / 1_000_000},
    }
    
    model_pricing = pricing.get(model, {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000})
    cost = (input_tokens * model_pricing["input"]) + (output_tokens * model_pricing["output"])
    
    await track_cost(
        db=db,
        operation="ai_generation",
        cost=cost,
        user_id=user_id,
        lesson_id=lesson_id,
        meta_data={
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "slide_number": slide_number
        }
    )

async def track_tts_cost(
    db: AsyncSession,
    character_count: int,
    voice: str,
    user_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    slide_number: Optional[int] = None
):
    """Track TTS operation cost"""
    # Google TTS: $4 per 1 million characters for WaveNet
    # Standard voices: $4 per 1 million characters
    # Neural2 voices: $16 per 1 million characters
    
    if "neural" in voice.lower() or "wavenet" in voice.lower():
        unit_price = 16.00
    else:
        unit_price = 4.00
    
    cost = (character_count * unit_price) / 1_000_000
    
    await track_cost(
        db=db,
        operation="tts",
        cost=cost,
        user_id=user_id,
        lesson_id=lesson_id,
        meta_data={
            "character_count": character_count,
            "voice": voice,
            "unit_price": unit_price,
            "slide_number": slide_number,
            "provider": "google_tts"
        }
    )

async def track_storage_cost(
    db: AsyncSession,
    file_size_bytes: int,
    storage_days: int = 30,
    user_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    file_type: Optional[str] = None
):
    """Track storage cost"""
    # Google Cloud Storage: $0.020 per GB per month
    file_size_gb = file_size_bytes / (1024 ** 3)
    cost = (file_size_gb * 0.020 * storage_days) / 30
    
    await track_cost(
        db=db,
        operation="storage",
        cost=cost,
        user_id=user_id,
        lesson_id=lesson_id,
        meta_data={
            "file_size_bytes": file_size_bytes,
            "file_size_gb": file_size_gb,
            "storage_days": storage_days,
            "file_type": file_type,
            "provider": "gcs"
        }
    )

# Context manager for automatic cost tracking
class CostTracker:
    """Context manager for cost tracking"""
    
    def __init__(
        self,
        db: AsyncSession,
        operation: str,
        user_id: Optional[str] = None,
        lesson_id: Optional[str] = None
    ):
        self.db = db
        self.operation = operation
        self.user_id = user_id
        self.lesson_id = lesson_id
        self.meta_data: Dict[str, Any] = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Calculate cost based on collected meta_data
        if self.operation == "ocr" and "slide_count" in self.meta_data:
            await track_ocr_cost(
                self.db,
                self.meta_data["slide_count"],
                self.user_id,
                self.lesson_id,
                self.meta_data.get("file_name")
            )
        elif self.operation == "ai_generation" and "input_tokens" in self.meta_data:
            await track_ai_generation_cost(
                self.db,
                self.meta_data.get("model", "gemini-1.5-flash"),
                self.meta_data["input_tokens"],
                self.meta_data["output_tokens"],
                self.user_id,
                self.lesson_id,
                self.meta_data.get("slide_number")
            )
        elif self.operation == "tts" and "character_count" in self.meta_data:
            await track_tts_cost(
                self.db,
                self.meta_data["character_count"],
                self.meta_data.get("voice", "standard"),
                self.user_id,
                self.lesson_id,
                self.meta_data.get("slide_number")
            )
    
    def add_metadata(self, **kwargs):
        """Add meta_data for cost calculation"""
        self.meta_data.update(kwargs)
