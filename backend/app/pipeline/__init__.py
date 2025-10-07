"""Pipeline package for slide-speaker processing pipelines"""

from .base import BasePipeline
from .intelligent_optimized import OptimizedIntelligentPipeline

PIPELINES = {
    "intelligent": OptimizedIntelligentPipeline,  # Alias for backward compatibility
    "intelligent_optimized": OptimizedIntelligentPipeline,
    "optimized": OptimizedIntelligentPipeline,
}


def get_pipeline(name: str) -> type[BasePipeline]:
    """Get pipeline class by name"""
    # Always returns OptimizedIntelligentPipeline
    return PIPELINES.get(name, OptimizedIntelligentPipeline)