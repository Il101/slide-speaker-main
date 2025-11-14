"""
Timing Engine V2 - Simplified, Predictable Timing Logic

Главная задача: получить точное время появления эффекта из talk_track/TTS данных.

Приоритеты (простая иерархия):
1. Talk track segments (calculated in pipeline from LLM estimated_duration) - BEST ✅
2. TTS sentence timings (fallback, often estimated) - MEDIUM ⚠️
3. Equal distribution (last resort fallback) - LOW ❌

Note: Since Gemini TTS doesn't provide real timing, talk_track is now the primary
      accurate source (calculated proportionally from LLM estimated_duration).
"""
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


@dataclass
class Timing:
    """
    Результат определения timing для группы/элемента
    
    Содержит:
    - Точное время (t0, t1)
    - Уверенность в точности (confidence)
    - Источник данных (source)
    - Точность (precision: word/sentence/segment)
    """
    t0: float  # Start time (seconds)
    t1: float  # End time (seconds)
    confidence: float  # 0.0 - 1.0
    source: str  # 'talk_track' | 'tts' | 'fallback'
    precision: str  # 'word' | 'sentence' | 'segment'
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def duration(self) -> float:
        return self.t1 - self.t0
    
    def __repr__(self) -> str:
        return (
            f"Timing(t0={self.t0:.2f}s, t1={self.t1:.2f}s, "
            f"conf={self.confidence:.2f}, source={self.source})"
        )


class TimingEngine:
    """
    Упрощённый движок для определения timing визуальных эффектов
    
    Только 3 источника (вместо 4+ в старой версии):
    1. Talk track segments - timing calculated in pipeline (BEST - accurate)
    2. TTS sentences - timing from TTS API (FALLBACK - often estimated)
    3. Equal distribution - равномерное распределение (LAST RESORT)
    
    Простая, понятная логика без сложных fallbacks.
    """
    
    def __init__(self):
        self.min_duration = 0.8  # Minimum effect duration
        self.max_duration = 5.0  # Maximum effect duration
        self.default_duration = 2.5  # Default if cannot determine
    
    def get_timing(
        self,
        group_id: str,
        talk_track: Optional[List[Dict[str, Any]]] = None,
        tts_words: Optional[Dict[str, Any]] = None,
        audio_duration: float = 0.0,
        fallback_index: int = 0,
        total_groups: int = 1
    ) -> Timing:
        """
        Главный метод: получить timing для группы
        
        Args:
            group_id: ID группы из semantic_map
            talk_track: Segments from talk_track with timing
            tts_words: TTS response with sentences and timings
            audio_duration: Total audio duration
            fallback_index: Index for equal distribution fallback
            total_groups: Total number of groups for fallback
            
        Returns:
            Timing object with t0, t1, confidence, source
        """
        
        # Priority 1: Talk track segments (BEST)
        timing = self._from_talk_track(group_id, talk_track)
        if timing and timing.confidence >= 0.8:
            logger.info(f"✅ {group_id}: Talk track timing {timing.t0:.2f}-{timing.t1:.2f}s (conf={timing.confidence:.2f})")
            return timing
        
        # Priority 2: TTS sentences (FALLBACK - estimated timing)
        # Note: Gemini TTS doesn't provide real timing, so this is also estimated
        timing = self._from_tts_sentences(group_id, talk_track, tts_words)
        if timing and timing.confidence >= 0.6:
            logger.info(f"✅ {group_id}: TTS timing {timing.t0:.2f}-{timing.t1:.2f}s (conf={timing.confidence:.2f})")
            return timing
        
        # Priority 3: Equal distribution (LAST RESORT)
        logger.warning(f"⚠️  {group_id}: Using fallback timing (no good match)")
        return self._equal_distribution(
            fallback_index, 
            total_groups, 
            audio_duration
        )
    
    def _from_talk_track(
        self,
        group_id: str,
        talk_track: Optional[List[Dict[str, Any]]]
    ) -> Optional[Timing]:
        """
        Извлечь timing из talk_track segments
        
        Talk track содержит segments с calculated timing:
        {
            "segment": "introduction",
            "group_id": "title_group",
            "text": "...",
            "start": 0.3,
            "end": 2.8,
            "duration": 2.5
        }
        
        Returns:
            Timing if found, else None
        """
        if not talk_track or not group_id:
            return None
        
        # Find all segments with matching group_id
        matching_segments = [
            seg for seg in talk_track
            if seg.get('group_id') == group_id
            and 'start' in seg and 'end' in seg
        ]
        
        if not matching_segments:
            return None
        
        # If multiple segments, take the first one (most important)
        # Note: Could merge multiple segments, but keep it simple for now
        segment = matching_segments[0]
        
        t0 = float(segment['start'])
        t1 = float(segment['end'])
        
        # Validate timing
        if t1 <= t0 or (t1 - t0) < self.min_duration:
            logger.warning(f"Invalid timing from talk_track: {t0}-{t1}")
            return None
        
        # Clamp duration to max
        if (t1 - t0) > self.max_duration:
            t1 = t0 + self.max_duration
        
        return Timing(
            t0=t0,
            t1=t1,
            confidence=0.95,  # High confidence - calculated by LLM
            source='talk_track',
            precision='segment',
            metadata={
                'segment_type': segment.get('segment', 'unknown'),
                'text_preview': segment.get('text', '')[:50]
            }
        )
    
    def _from_tts_sentences(
        self,
        group_id: str,
        talk_track: Optional[List[Dict[str, Any]]],
        tts_words: Optional[Dict[str, Any]]
    ) -> Optional[Timing]:
        """
        Извлечь timing из TTS sentence timings
        
        Strategy:
        1. Get text for group_id from talk_track
        2. Find matching sentence in TTS sentences
        3. Return timing of that sentence
        
        Returns:
            Timing if found, else None
        """
        if not tts_words or not talk_track or not group_id:
            return None
        
        # Get group text from talk_track
        group_text = self._get_group_text(group_id, talk_track)
        if not group_text or len(group_text) < 5:
            return None
        
        # Get TTS sentences
        sentences = tts_words.get('sentences', [])
        if not sentences:
            return None
        
        # Find best matching sentence
        best_match = None
        best_score = 0.0
        
        # Extract first significant words from group text (for matching)
        group_words = self._extract_significant_words(group_text, max_words=7)
        
        for sentence in sentences:
            sent_text = sentence.get('text', '')
            if not sent_text:
                continue
            
            # Calculate match score
            score = self._calculate_match_score(group_words, sent_text)
            
            if score > best_score and score > 0.3:  # Require 30%+ match
                best_score = score
                best_match = sentence
        
        if not best_match:
            return None
        
        t0 = float(best_match.get('t0', 0))
        t1 = float(best_match.get('t1', t0 + self.default_duration))
        
        # Validate
        if t1 <= t0 or (t1 - t0) < self.min_duration:
            return None
        
        # Clamp duration
        duration = min(t1 - t0, self.max_duration)
        t1 = t0 + duration
        
        # Confidence based on match score
        confidence = min(0.6 + best_score * 0.3, 0.9)
        
        return Timing(
            t0=t0,
            t1=t1,
            confidence=confidence,
            source='tts',
            precision='sentence',
            metadata={
                'match_score': best_score,
                'sentence_preview': best_match.get('text', '')[:50]
            }
        )
    
    def _equal_distribution(
        self,
        index: int,
        total: int,
        audio_duration: float
    ) -> Timing:
        """
        Fallback: равномерное распределение эффектов
        
        Simple, predictable fallback when no timing data available.
        """
        if audio_duration <= 0 or total == 0:
            # No audio duration provided, use default
            t0 = 0.5 + index * (self.default_duration + 0.5)
            t1 = t0 + self.default_duration
        else:
            # Distribute evenly across audio duration
            slot_duration = audio_duration / max(total, 1)
            t0 = 0.5 + index * slot_duration
            
            # Duration: 80% of slot or default
            duration = min(slot_duration * 0.8, self.default_duration)
            duration = max(duration, self.min_duration)
            
            t1 = t0 + duration
        
        return Timing(
            t0=t0,
            t1=t1,
            confidence=0.3,  # Low confidence - just a guess
            source='fallback',
            precision='segment',
            metadata={'index': index, 'total': total}
        )
    
    # Helper methods
    
    def _get_group_text(
        self,
        group_id: str,
        talk_track: List[Dict[str, Any]]
    ) -> str:
        """Get text for group_id from talk_track"""
        for segment in talk_track:
            if segment.get('group_id') == group_id:
                text = segment.get('text', '').strip()
                # Remove markers: [lang:XX]...[/lang], [visual:XX]...[/visual]
                text = re.sub(r'\[(?:lang|visual|phoneme):[^\]]*\]', '', text)
                text = re.sub(r'\[/(?:lang|visual|phoneme)\]', '', text)
                return text
        return ''
    
    def _extract_significant_words(
        self,
        text: str,
        max_words: int = 7
    ) -> List[str]:
        """Extract first N significant words from text"""
        # Lowercase and extract words
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter short words (articles, prepositions)
        significant = [w for w in words if len(w) > 2]
        return significant[:max_words]
    
    def _calculate_match_score(
        self,
        target_words: List[str],
        sentence: str
    ) -> float:
        """
        Calculate how well target words match sentence
        
        Returns:
            Score 0.0 - 1.0
        """
        if not target_words:
            return 0.0
        
        sentence_lower = sentence.lower()
        sentence_words = re.findall(r'\b\w+\b', sentence_lower)
        
        matched = 0
        for word in target_words:
            # Check exact match or substring for long words
            if word in sentence_words:
                matched += 1
            elif len(word) > 4 and any(word in sw for sw in sentence_words):
                matched += 0.5
        
        return matched / len(target_words)
    
    def validate_timing(self, timing: Timing) -> bool:
        """Validate timing object"""
        if timing.t1 <= timing.t0:
            return False
        if timing.duration < self.min_duration:
            return False
        if timing.duration > self.max_duration * 2:  # Allow some flexibility
            return False
        if not 0.0 <= timing.confidence <= 1.0:
            return False
        return True


# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = TimingEngine()
    
    # Example 1: From talk_track
    talk_track = [
        {
            "segment": "introduction",
            "group_id": "title_group",
            "text": "Welcome to our presentation",
            "start": 0.3,
            "end": 2.8,
            "duration": 2.5
        }
    ]
    
    timing = engine.get_timing("title_group", talk_track=talk_track)
    print(f"Example 1: {timing}")
    
    # Example 2: From TTS
    tts_words = {
        "sentences": [
            {"text": "Welcome to our presentation", "t0": 0.3, "t1": 2.5}
        ]
    }
    
    timing = engine.get_timing(
        "title_group",
        talk_track=talk_track,
        tts_words=tts_words
    )
    print(f"Example 2: {timing}")
    
    # Example 3: Fallback
    timing = engine.get_timing(
        "unknown_group",
        fallback_index=0,
        total_groups=5,
        audio_duration=20.0
    )
    print(f"Example 3 (fallback): {timing}")
