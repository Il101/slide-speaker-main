"""
Timeline Builder - Event-Based Timeline Generation

Создаёт event-driven timeline из списка эффектов для:
- Точной синхронизации (событийная модель вместо polling)
- Предзагрузки эффектов
- Буферизации с опережением
"""
import logging
from typing import List, Dict, Any
from ..core.effect_types import Effect, TimelineEvent

logger = logging.getLogger(__name__)


class TimelineBuilder:
    """
    Строит event-based timeline из эффектов
    
    Преобразует эффекты в:
    - START/END events для каждого эффекта
    - SLIDE_START/SLIDE_END events
    - Сортированный список событий по времени
    """
    
    def __init__(self):
        self.buffer_time = 0.1  # 100ms buffer for preloading
    
    def build_timeline(
        self,
        effects: List[Effect],
        slide_duration: float = 0.0
    ) -> Dict[str, Any]:
        """
        Создать timeline из списка эффектов
        
        Args:
            effects: List of Effect objects
            slide_duration: Total slide duration
            
        Returns:
            Timeline dictionary with events and metadata
        """
        events: List[TimelineEvent] = []
        
        # Add SLIDE_START event
        events.append(TimelineEvent(
            time=0.0,
            type="SLIDE_START",
            metadata={'slide_duration': slide_duration}
        ))
        
        # Create START/END events for each effect
        for effect in effects:
            # START event
            events.append(TimelineEvent(
                time=effect.t0,
                type="START",
                effect=effect,
                metadata={
                    'effect_id': effect.id,
                    'effect_type': effect.type.value,
                    'confidence': effect.confidence
                }
            ))
            
            # END event
            events.append(TimelineEvent(
                time=effect.t1,
                type="END",
                effect=effect,
                metadata={
                    'effect_id': effect.id,
                    'effect_type': effect.type.value
                }
            ))
        
        # Add SLIDE_END event if duration known
        if slide_duration > 0:
            events.append(TimelineEvent(
                time=slide_duration,
                type="SLIDE_END",
                metadata={}
            ))
        
        # Sort events by time
        events.sort(key=lambda e: e.time)
        
        # Build timeline dict
        timeline = {
            'total_duration': slide_duration,
            'events': [event.to_dict() for event in events],
            'effects_count': len(effects),
            'metadata': {
                'buffer_time': self.buffer_time,
                'version': '2.0',
            }
        }
        
        # Add statistics
        timeline['statistics'] = self._calculate_statistics(effects)
        
        logger.info(f"✅ Built timeline: {len(events)} events, {len(effects)} effects")
        
        return timeline
    
    def _calculate_statistics(self, effects: List[Effect]) -> Dict[str, Any]:
        """Calculate statistics about effects"""
        if not effects:
            return {}
        
        # Confidence distribution
        high_conf = sum(1 for e in effects if e.confidence >= 0.8)
        medium_conf = sum(1 for e in effects if 0.6 <= e.confidence < 0.8)
        low_conf = sum(1 for e in effects if e.confidence < 0.6)
        
        # Source distribution
        sources = {}
        for effect in effects:
            sources[effect.source] = sources.get(effect.source, 0) + 1
        
        # Type distribution
        types = {}
        for effect in effects:
            type_name = effect.type.value
            types[type_name] = types.get(type_name, 0) + 1
        
        # Timing stats
        durations = [e.duration for e in effects]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_effects': len(effects),
            'confidence': {
                'high': high_conf,
                'medium': medium_conf,
                'low': low_conf,
            },
            'sources': sources,
            'types': types,
            'avg_duration': round(avg_duration, 2),
            'min_duration': round(min(durations), 2) if durations else 0,
            'max_duration': round(max(durations), 2) if durations else 0,
        }
    
    def validate_timeline(self, timeline: Dict[str, Any]) -> bool:
        """Validate timeline structure"""
        required_keys = ['total_duration', 'events', 'effects_count']
        
        if not all(key in timeline for key in required_keys):
            logger.error("Timeline missing required keys")
            return False
        
        events = timeline.get('events', [])
        if not isinstance(events, list):
            logger.error("Timeline events must be a list")
            return False
        
        # Check events are sorted
        times = [e['time'] for e in events if 'time' in e]
        if times != sorted(times):
            logger.warning("Timeline events not sorted by time")
            return False
        
        return True
    
    def merge_timelines(
        self,
        timelines: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge multiple slide timelines into one
        
        Useful for full presentation timeline
        """
        if not timelines:
            return {'total_duration': 0, 'events': [], 'effects_count': 0}
        
        merged_events = []
        total_duration = 0
        total_effects = 0
        
        for i, timeline in enumerate(timelines):
            slide_events = timeline.get('events', [])
            slide_duration = timeline.get('total_duration', 0)
            
            # Offset events by accumulated duration
            for event in slide_events:
                offset_event = event.copy()
                offset_event['time'] = round(total_duration + event['time'], 3)
                offset_event['slide_index'] = i
                merged_events.append(offset_event)
            
            total_duration += slide_duration
            total_effects += timeline.get('effects_count', 0)
        
        # Sort merged events
        merged_events.sort(key=lambda e: e['time'])
        
        return {
            'total_duration': total_duration,
            'events': merged_events,
            'effects_count': total_effects,
            'slides_count': len(timelines),
            'metadata': {
                'version': '2.0',
                'merged': True
            }
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from ..core.effect_types import Effect, EffectType, EffectTarget, EffectParams
    
    # Create example effects
    effects = [
        Effect(
            id="effect_001",
            type=EffectType.SPOTLIGHT,
            target=EffectTarget(element_id="title", bbox=[100, 50, 600, 80]),
            t0=0.3,
            t1=2.5,
            confidence=0.95,
            source='talk_track',
            precision='word'
        ),
        Effect(
            id="effect_002",
            type=EffectType.PARTICLE_HIGHLIGHT,
            target=EffectTarget(element_ids=["item1", "item2"]),
            t0=3.0,
            t1=5.5,
            confidence=0.88,
            source='tts',
            precision='sentence'
        ),
    ]
    
    builder = TimelineBuilder()
    timeline = builder.build_timeline(effects, slide_duration=10.0)
    
    print("Timeline:")
    print(f"  Duration: {timeline['total_duration']}s")
    print(f"  Events: {len(timeline['events'])}")
    print(f"  Effects: {timeline['effects_count']}")
    print(f"  Statistics: {timeline['statistics']}")
