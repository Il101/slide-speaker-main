"""Pipeline package for slide-speaker processing pipelines"""

from .base import BasePipeline
from .classic import ClassicPipeline
from .vision_only import VisionPipeline
from .hybrid import HybridPipeline

PIPELINES = {
    "classic": ClassicPipeline,
    "vision": VisionPipeline,
    "hybrid": HybridPipeline,
}

def get_pipeline(name: str) -> type[BasePipeline]:
    """Get pipeline class by name"""
    return PIPELINES.get(name, ClassicPipeline)