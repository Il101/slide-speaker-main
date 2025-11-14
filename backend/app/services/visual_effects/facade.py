"""
Visual Effects V2 Facade - Main Entry Point

Упрощённый интерфейс для генерации визуальных эффектов.
Заменяет старый VisualEffectsEngine.
"""
import logging
from typing import List, Dict, Any, Optional
from .generators.semantic_generator import SemanticEffectGenerator
from .generators.timeline_builder import TimelineBuilder
from .core.effect_types import Effect

logger = logging.getLogger(__name__)


class VisualEffectsEngineV2:
    """
    Главный класс для генерации визуальных эффектов V2
    
    Упрощённая архитектура:
    - SemanticEffectGenerator: создаёт Effect objects
    - TimelineBuilder: строит event-based timeline
    - Всё остальное убрано для простоты
    
    Usage:
        engine = VisualEffectsEngineV2()
        effects = engine.generate_effects(semantic_map, elements, ...)
        timeline = engine.build_timeline(effects, slide_duration)
        manifest = engine.build_manifest(effects, timeline, slide_id)
    """
    
    def __init__(self):
        self.semantic_generator = SemanticEffectGenerator()
        self.timeline_builder = TimelineBuilder()
        logger.info("✅ VisualEffectsEngineV2 initialized")
    
    def generate_effects(
        self,
        semantic_map: Dict[str, Any],
        elements: List[Dict[str, Any]],
        audio_duration: float,
        tts_words: Optional[Dict[str, Any]] = None,
        talk_track: Optional[List[Dict[str, Any]]] = None
    ) -> List[Effect]:
        """
        Генерация эффектов из semantic map
        
        Args:
            semantic_map: Semantic analysis from SemanticAnalyzer
            elements: OCR elements with bbox coordinates
            audio_duration: Total audio duration in seconds
            tts_words: TTS response with timing data
            talk_track: Talk track segments with timing
            
        Returns:
            List of Effect objects
        """
        logger.info("🎨 Generating visual effects V2...")
        
        try:
            effects = self.semantic_generator.generate_effects(
                semantic_map=semantic_map,
                elements=elements,
                audio_duration=audio_duration,
                tts_words=tts_words,
                talk_track=talk_track
            )
            
            logger.info(f"✅ Generated {len(effects)} effects")
            return effects
            
        except Exception as e:
            logger.error(f"Error generating effects: {e}", exc_info=True)
            return []
    
    def build_timeline(
        self,
        effects: List[Effect],
        slide_duration: float = 0.0
    ) -> Dict[str, Any]:
        """
        Построить event-based timeline из эффектов
        
        Args:
            effects: List of Effect objects
            slide_duration: Total slide duration
            
        Returns:
            Timeline dictionary with events
        """
        try:
            timeline = self.timeline_builder.build_timeline(
                effects=effects,
                slide_duration=slide_duration
            )
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error building timeline: {e}", exc_info=True)
            return {
                'total_duration': slide_duration,
                'events': [],
                'effects_count': 0,
                'error': str(e)
            }
    
    def build_manifest(
        self,
        effects: List[Effect],
        timeline: Dict[str, Any],
        slide_id: str,
        slide_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Построить manifest V2 для слайда
        
        Args:
            effects: List of Effect objects
            timeline: Timeline from build_timeline()
            slide_id: Slide identifier
            slide_data: Additional slide data (image path, etc)
            
        Returns:
            Manifest V2 dictionary
        """
        manifest = {
            'version': '2.0',
            'id': slide_id,
            'timeline': timeline,
            'effects': [effect.to_dict() for effect in effects],
        }
        
        # Add slide data if provided
        if slide_data:
            manifest.update(slide_data)
        
        # Add quality metrics
        manifest['quality'] = self._calculate_quality_metrics(effects)
        
        logger.info(f"✅ Built manifest V2 for {slide_id}")
        
        return manifest
    
    def _calculate_quality_metrics(
        self,
        effects: List[Effect]
    ) -> Dict[str, Any]:
        """Calculate quality metrics for effects"""
        if not effects:
            return {'score': 0, 'confidence_avg': 0}
        
        # Average confidence
        avg_confidence = sum(e.confidence for e in effects) / len(effects)
        
        # Count high-confidence effects
        high_conf = sum(1 for e in effects if e.confidence >= 0.8)
        
        # Calculate overall quality score (0-100)
        quality_score = int(avg_confidence * 100)
        
        return {
            'score': quality_score,
            'confidence_avg': round(avg_confidence, 2),
            'high_confidence_count': high_conf,
            'total_effects': len(effects),
        }
    
    def generate_slide_manifest(
        self,
        semantic_map: Dict[str, Any],
        elements: List[Dict[str, Any]],
        audio_duration: float,
        slide_id: str,
        tts_words: Optional[Dict[str, Any]] = None,
        talk_track: Optional[List[Dict[str, Any]]] = None,
        slide_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Комплексный метод: генерация эффектов + timeline + manifest
        
        Всё в одном вызове для простоты использования.
        
        Args:
            semantic_map: Semantic analysis
            elements: OCR elements
            audio_duration: Audio duration
            slide_id: Slide ID
            tts_words: TTS timing data
            talk_track: Talk track segments
            slide_data: Additional slide data
            
        Returns:
            Complete slide manifest V2
        """
        # Step 1: Generate effects
        effects = self.generate_effects(
            semantic_map=semantic_map,
            elements=elements,
            audio_duration=audio_duration,
            tts_words=tts_words,
            talk_track=talk_track
        )
        
        # Step 2: Build timeline
        timeline = self.build_timeline(
            effects=effects,
            slide_duration=audio_duration
        )
        
        # Step 3: Build manifest
        manifest = self.build_manifest(
            effects=effects,
            timeline=timeline,
            slide_id=slide_id,
            slide_data=slide_data
        )
        
        return manifest


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example data
    semantic_map = {
        'groups': [
            {
                'id': 'title_group',
                'type': 'title',
                'priority': 'high',
                'element_ids': ['elem_0'],
            }
        ]
    }
    
    elements = [
        {'id': 'elem_0', 'text': 'Title', 'bbox': [100, 50, 600, 80]}
    ]
    
    talk_track = [
        {
            'segment': 'introduction',
            'group_id': 'title_group',
            'text': 'Welcome',
            'start': 0.3,
            'end': 2.8
        }
    ]
    
    # Initialize engine
    engine = VisualEffectsEngineV2()
    
    # Generate complete manifest
    manifest = engine.generate_slide_manifest(
        semantic_map=semantic_map,
        elements=elements,
        audio_duration=10.0,
        slide_id='slide_0',
        talk_track=talk_track
    )
    
    print("\nManifest V2:")
    print(f"  Version: {manifest['version']}")
    print(f"  Effects: {len(manifest['effects'])}")
    print(f"  Quality score: {manifest['quality']['score']}/100")
    print(f"  Timeline events: {len(manifest['timeline']['events'])}")
