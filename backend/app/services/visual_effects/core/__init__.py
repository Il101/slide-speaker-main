"""Core components for Visual Effects V2"""
from .timing_engine import TimingEngine, Timing
from .effect_types import (
    Effect,
    EffectType,
    EffectParams,
    EffectTarget,
    TimelineEvent,
    IntensityLevel,
    EasingFunction,
    get_default_params,
    EFFECT_CONFIGS,
)

__all__ = [
    'TimingEngine',
    'Timing',
    'Effect',
    'EffectType',
    'EffectParams',
    'EffectTarget',
    'TimelineEvent',
    'IntensityLevel',
    'EasingFunction',
    'get_default_params',
    'EFFECT_CONFIGS',
]
