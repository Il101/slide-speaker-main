"""
Visual Effects System V2 - Modern, Timeline-Based Effects
"""

from .facade import VisualEffectsEngineV2
from .core.timing_engine import TimingEngine, Timing
from .core.effect_types import Effect, EffectType, EffectParams
from .generators.timeline_builder import TimelineBuilder
from .generators.semantic_generator import SemanticEffectGenerator

__all__ = [
    'VisualEffectsEngineV2',
    'TimingEngine',
    'Timing',
    'Effect',
    'EffectType',
    'EffectParams',
    'TimelineBuilder',
    'SemanticEffectGenerator',
]

__version__ = '2.0.0'
