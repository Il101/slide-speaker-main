"""
Semantic Effect Generator - Generate Effects from Semantic Map

Главный генератор визуальных эффектов V2.
Использует semantic_map + TimingEngine для создания точно синхронизированных эффектов.
"""
import logging
import uuid
from typing import List, Dict, Any, Optional
from ..core.timing_engine import TimingEngine, Timing
from ..core.effect_types import (
    Effect, EffectType, EffectParams, EffectTarget,
    IntensityLevel, get_default_params
)

logger = logging.getLogger(__name__)


class SemanticEffectGenerator:
    """
    Генератор эффектов из semantic_map
    
    Упрощённая логика:
    1. Читаем groups из semantic_map
    2. Для каждой группы получаем timing через TimingEngine
    3. Выбираем подходящий эффект based on group type/priority
    4. Создаём Effect object
    """
    
    def __init__(self):
        self.timing_engine = TimingEngine()
        
        # Mapping: semantic group type → effect type
        self.type_to_effect = {
            'title': EffectType.SPOTLIGHT,
            'subtitle': EffectType.HIGHLIGHT,
            'bullet_list': EffectType.FADE_IN,
            'diagram': EffectType.PARTICLE_HIGHLIGHT,
            'formula': EffectType.SPOTLIGHT,
            'body': EffectType.HIGHLIGHT,
            'emphasis': EffectType.PULSE,
            'quote': EffectType.HOLOGRAM,
        }
        
        # Mapping: priority → intensity
        self.priority_to_intensity = {
            'critical': IntensityLevel.DRAMATIC,
            'high': IntensityLevel.DRAMATIC,
            'medium': IntensityLevel.NORMAL,
            'low': IntensityLevel.SUBTLE,
            'none': IntensityLevel.SUBTLE,
        }
    
    def generate_effects(
        self,
        semantic_map: Dict[str, Any],
        elements: List[Dict[str, Any]],
        audio_duration: float,
        tts_words: Optional[Dict[str, Any]] = None,
        talk_track: Optional[List[Dict[str, Any]]] = None
    ) -> List[Effect]:
        """
        Главный метод: генерация эффектов из semantic_map
        
        Args:
            semantic_map: Semantic analysis from SemanticAnalyzer
            elements: OCR elements with bbox
            audio_duration: Total audio duration
            tts_words: TTS response with timings
            talk_track: Talk track segments with timing
            
        Returns:
            List of Effect objects
        """
        logger.info("🎨 Generating effects from semantic map...")
        
        groups = semantic_map.get('groups', [])
        if not groups:
            logger.warning("No groups in semantic_map")
            return []
        
        # Create element lookup
        elements_by_id = {
            elem.get('id', f'elem_{i}'): elem 
            for i, elem in enumerate(elements)
        }
        
        effects = []
        
        for index, group in enumerate(groups):
            # Skip noise groups
            if group.get('priority') == 'none':
                continue
            
            # Generate effect for this group
            effect = self._generate_group_effect(
                group,
                elements_by_id,
                index,
                len(groups),
                audio_duration,
                tts_words,
                talk_track
            )
            
            if effect:
                effects.append(effect)
        
        logger.info(f"✅ Generated {len(effects)} effects")
        return effects
    
    def _generate_group_effect(
        self,
        group: Dict[str, Any],
        elements_by_id: Dict[str, Any],
        index: int,
        total_groups: int,
        audio_duration: float,
        tts_words: Optional[Dict[str, Any]],
        talk_track: Optional[List[Dict[str, Any]]]
    ) -> Optional[Effect]:
        """Generate effect for a single group"""
        
        group_id = group.get('id', f'group_{index}')
        group_type = group.get('type', 'body')
        priority = group.get('priority', 'medium')
        
        # Get timing through TimingEngine
        timing = self.timing_engine.get_timing(
            group_id=group_id,
            talk_track=talk_track,
            tts_words=tts_words,
            audio_duration=audio_duration,
            fallback_index=index,
            total_groups=total_groups
        )
        
        # Validate timing
        if not self.timing_engine.validate_timing(timing):
            logger.warning(f"Invalid timing for group {group_id}: {timing}")
            return None
        
        # Select effect type based on group
        effect_type = self._select_effect_type(group)
        
        # Get elements for this group
        element_ids = group.get('element_ids', [])
        group_elements = [
            elements_by_id[eid] 
            for eid in element_ids 
            if eid in elements_by_id
        ]
        
        if not group_elements:
            logger.warning(f"No elements found for group {group_id}")
            return None
        
        # Create target
        target = self._create_target(group_id, group_elements)
        
        # Create parameters
        params = self._create_params(group, effect_type)
        
        # Create Effect
        effect = Effect(
            id=f"effect_{uuid.uuid4().hex[:8]}",
            type=effect_type,
            target=target,
            t0=timing.t0,
            t1=timing.t1,
            params=params,
            confidence=timing.confidence,
            source=timing.source,
            precision=timing.precision,
            metadata={
                'group_id': group_id,
                'group_type': group_type,
                'priority': priority,
                'element_count': len(group_elements),
            }
        )
        
        logger.debug(f"  Created {effect}")
        
        return effect
    
    def _select_effect_type(self, group: Dict[str, Any]) -> EffectType:
        """
        Выбрать тип эффекта based on group properties
        
        Logic:
        1. Check explicit effect in highlight_strategy
        2. Map group type to effect type
        3. Consider priority level
        4. Default to HIGHLIGHT
        """
        # Check explicit effect in highlight_strategy
        strategy = group.get('highlight_strategy', {})
        explicit_effect = strategy.get('effect_type')
        
        if explicit_effect:
            try:
                return EffectType(explicit_effect)
            except ValueError:
                logger.warning(f"Unknown effect type: {explicit_effect}")
        
        # Map group type to effect
        group_type = group.get('type', 'body')
        if group_type in self.type_to_effect:
            return self.type_to_effect[group_type]
        
        # Consider priority
        priority = group.get('priority', 'medium')
        if priority in ['critical', 'high']:
            return EffectType.SPOTLIGHT
        
        # Default
        return EffectType.HIGHLIGHT
    
    def _create_target(
        self,
        group_id: str,
        elements: List[Dict[str, Any]]
    ) -> EffectTarget:
        """Create EffectTarget from group elements"""
        
        if len(elements) == 1:
            # Single element
            elem = elements[0]
            return EffectTarget(
                element_id=elem.get('id'),
                bbox=elem.get('bbox'),
                group_id=group_id
            )
        else:
            # Multiple elements - use bounding box
            element_ids = [e.get('id') for e in elements]
            bbox = self._calculate_group_bbox(elements)
            
            return EffectTarget(
                element_ids=element_ids,
                bbox=bbox,
                group_id=group_id
            )
    
    def _calculate_group_bbox(
        self,
        elements: List[Dict[str, Any]]
    ) -> List[float]:
        """Calculate bounding box containing all elements"""
        
        # Filter elements with valid bbox
        valid_elements = [
            e for e in elements 
            if e.get('bbox') and len(e['bbox']) >= 4
        ]
        
        if not valid_elements:
            return [0, 0, 100, 100]  # Default
        
        # Calculate bounding box
        min_x = min(e['bbox'][0] for e in valid_elements)
        min_y = min(e['bbox'][1] for e in valid_elements)
        max_x = max(e['bbox'][0] + e['bbox'][2] for e in valid_elements)
        max_y = max(e['bbox'][1] + e['bbox'][3] for e in valid_elements)
        
        # Add padding
        padding = 10
        min_x = max(0, min_x - padding)
        min_y = max(0, min_y - padding)
        max_x += padding
        max_y += padding
        
        return [min_x, min_y, max_x - min_x, max_y - min_y]
    
    def _create_params(
        self,
        group: Dict[str, Any],
        effect_type: EffectType
    ) -> EffectParams:
        """Create effect parameters based on group properties"""
        
        # Start with defaults for this effect type
        params = get_default_params(effect_type)
        
        # Get strategy from group
        strategy = group.get('highlight_strategy', {})
        priority = group.get('priority', 'medium')
        
        # Set intensity based on priority
        if priority in self.priority_to_intensity:
            params.intensity = self.priority_to_intensity[priority]
        
        # Apply strategy overrides
        if 'intensity' in strategy:
            try:
                params.intensity = IntensityLevel(strategy['intensity'])
            except ValueError:
                pass
        
        # Effect-specific customizations
        if effect_type == EffectType.SPOTLIGHT:
            params.shadow_opacity = 0.8 if priority == 'critical' else 0.7
            params.beam_width = 1.5 if priority == 'critical' else 1.2
        
        elif effect_type == EffectType.PARTICLE_HIGHLIGHT:
            params.particle_count = 1000 if priority == 'critical' else 500
            params.gravity = 0.05
            params.spread = 2.5
        
        elif effect_type == EffectType.PULSE:
            params.custom['pulse_count'] = 3
            params.custom['pulse_speed'] = 0.5
        
        return params


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example semantic_map
    semantic_map = {
        'groups': [
            {
                'id': 'title_group',
                'type': 'title',
                'priority': 'high',
                'element_ids': ['elem_0'],
                'highlight_strategy': {
                    'when': 'start',
                    'effect_type': 'spotlight',
                    'intensity': 'dramatic'
                }
            },
            {
                'id': 'body_group',
                'type': 'body',
                'priority': 'medium',
                'element_ids': ['elem_1', 'elem_2'],
            }
        ]
    }
    
    elements = [
        {'id': 'elem_0', 'text': 'Title', 'bbox': [100, 50, 600, 80]},
        {'id': 'elem_1', 'text': 'Point 1', 'bbox': [100, 150, 400, 40]},
        {'id': 'elem_2', 'text': 'Point 2', 'bbox': [100, 200, 400, 40]},
    ]
    
    talk_track = [
        {
            'segment': 'introduction',
            'group_id': 'title_group',
            'text': 'Welcome to presentation',
            'start': 0.3,
            'end': 2.8
        },
        {
            'segment': 'body',
            'group_id': 'body_group',
            'text': 'Let me explain two points',
            'start': 3.0,
            'end': 6.0
        }
    ]
    
    generator = SemanticEffectGenerator()
    effects = generator.generate_effects(
        semantic_map=semantic_map,
        elements=elements,
        audio_duration=10.0,
        talk_track=talk_track
    )
    
    print(f"\nGenerated {len(effects)} effects:")
    for effect in effects:
        print(f"  {effect}")
        print(f"    Target: {effect.target.to_dict()}")
        print(f"    Params: intensity={effect.params.intensity.value}")
