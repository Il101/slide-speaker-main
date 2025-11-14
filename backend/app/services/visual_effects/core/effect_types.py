"""
Effect Types Definitions - Modern Visual Effects
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Literal
from enum import Enum


class EffectType(str, Enum):
    """Типы визуальных эффектов"""
    
    # Basic effects
    SPOTLIGHT = "spotlight"
    HIGHLIGHT = "highlight"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    
    # Advanced effects
    PARTICLE_HIGHLIGHT = "particle_highlight"
    MORPH = "morph"
    GLITCH = "glitch"
    RIPPLE = "ripple"
    HOLOGRAM = "hologram"
    
    # Motion effects
    SLIDE_IN = "slide_in"
    ZOOM_IN = "zoom_in"
    PULSE = "pulse"
    SHAKE = "shake"
    
    # Special effects
    BLUR_OTHERS = "blur_others"
    DIM_BACKGROUND = "dim_background"
    CIRCLE_DRAW = "circle_draw"
    ARROW_POINT = "arrow_point"


class IntensityLevel(str, Enum):
    """Уровни интенсивности эффектов"""
    SUBTLE = "subtle"
    NORMAL = "normal"
    DRAMATIC = "dramatic"


class EasingFunction(str, Enum):
    """Функции плавности (easing)"""
    LINEAR = "linear"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    CUBIC_IN = "cubic-in"
    CUBIC_OUT = "cubic-out"
    CUBIC_IN_OUT = "cubic-in-out"
    ELASTIC = "elastic"
    BOUNCE = "bounce"


@dataclass
class EffectParams:
    """Параметры визуального эффекта"""
    
    # Timing
    ease_in: EasingFunction = EasingFunction.CUBIC_OUT
    ease_out: EasingFunction = EasingFunction.CUBIC_IN
    
    # Intensity
    intensity: IntensityLevel = IntensityLevel.NORMAL
    opacity: float = 1.0
    
    # Colors
    color: str = "#3b82f6"  # Blue
    secondary_color: Optional[str] = None
    
    # Spotlight specific
    shadow_opacity: float = 0.7
    beam_width: float = 1.2
    
    # Particle specific
    particle_count: int = 500
    particle_size: tuple = (2, 5)
    gravity: float = 0.1
    spread: float = 2.0
    
    # Morphing specific
    morph_duration: float = 0.3
    elastic_factor: float = 1.2
    
    # Glitch specific
    glitch_intensity: float = 0.5
    rgb_split: float = 5.0
    
    # Motion specific
    direction: str = "center"  # left, right, top, bottom, center
    distance: float = 100.0
    
    # Custom parameters
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'ease_in': self.ease_in.value,
            'ease_out': self.ease_out.value,
            'intensity': self.intensity.value,
            'opacity': self.opacity,
            'color': self.color,
            'secondary_color': self.secondary_color,
            'shadow_opacity': self.shadow_opacity,
            'beam_width': self.beam_width,
            'particle_count': self.particle_count,
            'particle_size': list(self.particle_size),
            'gravity': self.gravity,
            'spread': self.spread,
            'morph_duration': self.morph_duration,
            'elastic_factor': self.elastic_factor,
            'glitch_intensity': self.glitch_intensity,
            'rgb_split': self.rgb_split,
            'direction': self.direction,
            'distance': self.distance,
            **self.custom
        }


@dataclass
class EffectTarget:
    """Цель визуального эффекта"""
    element_id: Optional[str] = None
    element_ids: Optional[List[str]] = None
    bbox: Optional[List[float]] = None  # [x, y, width, height]
    group_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {}
        if self.element_id:
            result['element_id'] = self.element_id
        if self.element_ids:
            result['element_ids'] = self.element_ids
        if self.bbox:
            result['bbox'] = self.bbox
        if self.group_id:
            result['group_id'] = self.group_id
        return result


@dataclass
class Effect:
    """
    Визуальный эффект V2
    
    Содержит всю информацию об эффекте:
    - Тип и параметры
    - Timing с confidence
    - Цель (элементы)
    - Metadata для отладки
    """
    
    id: str
    type: EffectType
    target: EffectTarget
    t0: float  # Start time (seconds)
    t1: float  # End time (seconds)
    params: EffectParams = field(default_factory=EffectParams)
    
    # Timing metadata
    confidence: float = 1.0  # 0.0 - 1.0
    source: str = "unknown"  # 'talk_track' | 'tts' | 'fallback'
    precision: str = "segment"  # 'word' | 'sentence' | 'segment'
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Duration in seconds"""
        return self.t1 - self.t0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'type': self.type.value,
            'target': self.target.to_dict(),
            'timing': {
                't0': round(self.t0, 3),
                't1': round(self.t1, 3),
                'duration': round(self.duration, 3),
                'confidence': round(self.confidence, 2),
                'source': self.source,
                'precision': self.precision,
            },
            'params': self.params.to_dict(),
            'metadata': self.metadata
        }
    
    def __repr__(self) -> str:
        return (
            f"Effect(id='{self.id}', type={self.type.value}, "
            f"t={self.t0:.2f}-{self.t1:.2f}s, "
            f"conf={self.confidence:.2f}, source={self.source})"
        )


@dataclass
class TimelineEvent:
    """
    Событие в timeline для event-driven синхронизации
    """
    time: float  # Seconds
    type: Literal["START", "END", "SLIDE_START", "SLIDE_END"]
    effect: Optional[Effect] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For sorting events by time"""
        return self.time < other.time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'time': round(self.time, 3),
            'type': self.type,
        }
        if self.effect:
            result['effect_id'] = self.effect.id
        if self.metadata:
            result['metadata'] = self.metadata
        return result


# Effect type configurations
EFFECT_CONFIGS: Dict[EffectType, Dict[str, Any]] = {
    EffectType.SPOTLIGHT: {
        'description': 'Dynamic spotlight with soft shadows',
        'default_duration': 2.5,
        'intensity': IntensityLevel.DRAMATIC,
        'gpu_accelerated': True,
    },
    EffectType.HIGHLIGHT: {
        'description': 'Classic highlight with border',
        'default_duration': 2.0,
        'intensity': IntensityLevel.NORMAL,
        'gpu_accelerated': False,
    },
    EffectType.PARTICLE_HIGHLIGHT: {
        'description': 'GPU-accelerated particle system',
        'default_duration': 3.0,
        'intensity': IntensityLevel.DRAMATIC,
        'gpu_accelerated': True,
        'particle_count': 500,
    },
    EffectType.MORPH: {
        'description': 'Smooth morphing animation',
        'default_duration': 1.5,
        'intensity': IntensityLevel.NORMAL,
        'gpu_accelerated': True,
    },
    EffectType.GLITCH: {
        'description': 'Digital glitch effect',
        'default_duration': 1.0,
        'intensity': IntensityLevel.DRAMATIC,
        'gpu_accelerated': True,
    },
    EffectType.RIPPLE: {
        'description': 'Wave ripple effect',
        'default_duration': 2.0,
        'intensity': IntensityLevel.NORMAL,
        'gpu_accelerated': True,
    },
    EffectType.HOLOGRAM: {
        'description': '3D hologram effect',
        'default_duration': 3.0,
        'intensity': IntensityLevel.DRAMATIC,
        'gpu_accelerated': True,
    },
}


def get_default_params(effect_type: EffectType) -> EffectParams:
    """Get default parameters for effect type"""
    config = EFFECT_CONFIGS.get(effect_type, {})
    params = EffectParams()
    
    # Set defaults based on config
    if 'intensity' in config:
        params.intensity = config['intensity']
    if 'particle_count' in config:
        params.particle_count = config['particle_count']
    
    return params
