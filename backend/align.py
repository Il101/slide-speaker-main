"""
Alignment module for synchronizing speaker notes, audio timing, and visual cues
"""
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import re

logger = logging.getLogger(__name__)

@dataclass
class TimingCue:
    """Represents a timing cue with validation"""
    t0: float
    t1: float
    action: str
    element_id: Optional[str] = None
    bbox: Optional[List[int]] = None
    to: Optional[List[int]] = None
    
    def __post_init__(self):
        """Validate timing cue data"""
        if self.t1 <= self.t0:
            raise ValueError(f"Invalid timing: t1 ({self.t1}) must be > t0 ({self.t0})")
        
        if self.action not in ['highlight', 'underline', 'laser_move']:
            raise ValueError(f"Invalid action: {self.action}")
        
        if self.action in ['highlight', 'underline'] and not self.bbox:
            raise ValueError(f"Action {self.action} requires bbox")
        
        if self.action == 'laser_move' and not self.to:
            raise ValueError("Action laser_move requires 'to' position")

@dataclass
class SentenceTiming:
    """Represents sentence-level timing information"""
    sentence: str
    t0: float
    t1: float
    duration: float
    index: int
    elements: List[str] = None
    suggested_cues: List[Dict[str, Any]] = None

class TimelineAligner:
    """Aligns speaker notes, audio timing, and visual cues"""
    
    def __init__(self, min_highlight_duration: float = 0.8, min_gap: float = 0.2):
        self.min_highlight_duration = min_highlight_duration
        self.min_gap = min_gap
    
    def align_slide_content(self, 
                          speaker_notes: str,
                          sentence_timings: List[Dict[str, Any]],
                          slide_elements: List[Dict[str, Any]],
                          existing_cues: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Align speaker notes with slide elements and generate synchronized cues
        
        Args:
            speaker_notes: Generated speaker notes text
            sentence_timings: Timing information from TTS
            slide_elements: List of slide elements with IDs and bboxes
            existing_cues: Optional existing cues to preserve/modify
            
        Returns:
            Dictionary containing aligned cues and metadata
        """
        try:
            # Parse sentence timings
            sentences = [SentenceTiming(**timing) for timing in sentence_timings]
            
            # Create element lookup
            element_lookup = {elem['id']: elem for elem in slide_elements}
            
            # Generate alignment mapping
            alignment_map = self._create_alignment_map(sentences, element_lookup)
            
            # Generate synchronized cues
            synchronized_cues = self._generate_synchronized_cues(
                sentences, alignment_map, element_lookup, existing_cues
            )
            
            # Apply timeline rules for smoothness
            smoothed_cues = self._apply_timeline_rules(synchronized_cues)
            
            # Create metadata
            metadata = self._create_alignment_metadata(sentences, smoothed_cues)
            
            logger.info(f"Aligned {len(sentences)} sentences with {len(smoothed_cues)} cues")
            
            return {
                "cues": [cue.__dict__ for cue in smoothed_cues],
                "metadata": metadata,
                "alignment_map": alignment_map,
                "total_duration": sentences[-1].t1 if sentences else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error aligning slide content: {e}")
            raise
    
    def _create_alignment_map(self, sentences: List[SentenceTiming], element_lookup: Dict[str, Any]) -> Dict[int, List[str]]:
        """Create mapping between sentences and slide elements"""
        alignment_map = {}
        
        for i, sentence in enumerate(sentences):
            associated_elements = []
            sentence_text = sentence.sentence.lower()
            
            # Find elements that match this sentence
            for element_id, element in element_lookup.items():
                if element.get('type') == 'text' and element.get('text'):
                    element_text = element['text'].lower()
                    
                    # Calculate similarity
                    similarity = self._calculate_text_similarity(sentence_text, element_text)
                    
                    if similarity > 0.3:  # Threshold for association
                        associated_elements.append(element_id)
            
            alignment_map[i] = associated_elements
        
        return alignment_map
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using word overlap"""
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _generate_synchronized_cues(self, 
                                  sentences: List[SentenceTiming],
                                  alignment_map: Dict[int, List[str]],
                                  element_lookup: Dict[str, Any],
                                  existing_cues: Optional[List[Dict[str, Any]]]) -> List[TimingCue]:
        """Generate synchronized visual cues"""
        cues = []
        
        for i, sentence in enumerate(sentences):
            associated_elements = alignment_map.get(i, [])
            
            if associated_elements:
                # Create highlight cues for associated elements
                for element_id in associated_elements:
                    element = element_lookup.get(element_id)
                    if element and element.get('bbox'):
                        cue = TimingCue(
                            t0=sentence.t0,
                            t1=sentence.t1,
                            action='highlight',
                            element_id=element_id,
                            bbox=element['bbox']
                        )
                        cues.append(cue)
            else:
                # Create laser movement for general content
                cue = TimingCue(
                    t0=sentence.t0,
                    t1=sentence.t1,
                    action='laser_move',
                    to=[400, 300]  # Center position
                )
                cues.append(cue)
        
        # Merge with existing cues if provided
        if existing_cues:
            existing_timing_cues = []
            for cue_data in existing_cues:
                try:
                    cue = TimingCue(**cue_data)
                    existing_timing_cues.append(cue)
                except Exception as e:
                    logger.warning(f"Invalid existing cue: {e}")
            
            cues = self._merge_cues(cues, existing_timing_cues)
        
        return cues
    
    def _merge_cues(self, new_cues: List[TimingCue], existing_cues: List[TimingCue]) -> List[TimingCue]:
        """Merge new cues with existing ones, avoiding conflicts"""
        all_cues = new_cues + existing_cues
        
        # Sort by start time
        all_cues.sort(key=lambda c: c.t0)
        
        # Remove overlapping cues (keep the one with higher priority)
        merged_cues = []
        for cue in all_cues:
            # Check for overlaps with already merged cues
            has_overlap = False
            for merged_cue in merged_cues:
                if self._cues_overlap(cue, merged_cue):
                    has_overlap = True
                    break
            
            if not has_overlap:
                merged_cues.append(cue)
        
        return merged_cues
    
    def _cues_overlap(self, cue1: TimingCue, cue2: TimingCue) -> bool:
        """Check if two cues overlap in time"""
        return not (cue1.t1 <= cue2.t0 or cue2.t1 <= cue1.t0)
    
    def _apply_timeline_rules(self, cues: List[TimingCue]) -> List[TimingCue]:
        """Apply timeline rules for smoothness"""
        if not cues:
            return cues
        
        # Sort cues by start time
        cues.sort(key=lambda c: c.t0)
        
        smoothed_cues = []
        current_time = 0.0
        
        for cue in cues:
            # Ensure minimum gap before cue
            cue_start = max(current_time, cue.t0)
            
            # Ensure minimum duration
            if cue.action in ['highlight', 'underline']:
                cue_end = max(cue_start + self.min_highlight_duration, cue.t1)
            else:
                cue_end = cue.t1
            
            # Create smoothed cue
            smoothed_cue = TimingCue(
                t0=cue_start,
                t1=cue_end,
                action=cue.action,
                element_id=cue.element_id,
                bbox=cue.bbox,
                to=cue.to
            )
            
            smoothed_cues.append(smoothed_cue)
            current_time = cue_end + self.min_gap
        
        return smoothed_cues
    
    def _create_alignment_metadata(self, sentences: List[SentenceTiming], cues: List[TimingCue]) -> Dict[str, Any]:
        """Create metadata about the alignment process"""
        total_duration = sentences[-1].t1 if sentences else 0.0
        
        # Count cue types
        cue_counts = {}
        for cue in cues:
            cue_counts[cue.action] = cue_counts.get(cue.action, 0) + 1
        
        # Calculate coverage
        covered_time = sum(cue.t1 - cue.t0 for cue in cues)
        coverage_ratio = covered_time / total_duration if total_duration > 0 else 0.0
        
        return {
            "total_duration": total_duration,
            "sentence_count": len(sentences),
            "cue_count": len(cues),
            "cue_types": cue_counts,
            "coverage_ratio": coverage_ratio,
            "min_highlight_duration": self.min_highlight_duration,
            "min_gap": self.min_gap
        }
    
    def validate_alignment(self, alignment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate alignment result and return issues"""
        issues = []
        warnings = []
        
        cues = alignment_result.get('cues', [])
        metadata = alignment_result.get('metadata', {})
        
        # Check for timing conflicts
        for i, cue1 in enumerate(cues):
            for j, cue2 in enumerate(cues[i+1:], i+1):
                if self._cues_overlap(TimingCue(**cue1), TimingCue(**cue2)):
                    issues.append(f"Cues {i} and {j} overlap in time")
        
        # Check minimum durations
        for i, cue in enumerate(cues):
            duration = cue['t1'] - cue['t0']
            if cue['action'] in ['highlight', 'underline'] and duration < self.min_highlight_duration:
                warnings.append(f"Cue {i} duration ({duration:.2f}s) is less than minimum ({self.min_highlight_duration}s)")
        
        # Check gaps
        sorted_cues = sorted(cues, key=lambda c: c['t0'])
        for i in range(len(sorted_cues) - 1):
            gap = sorted_cues[i+1]['t0'] - sorted_cues[i]['t1']
            if gap < self.min_gap:
                warnings.append(f"Gap between cues {i} and {i+1} ({gap:.2f}s) is less than minimum ({self.min_gap}s)")
        
        # Check coverage
        coverage = metadata.get('coverage_ratio', 0.0)
        if coverage < 0.5:
            warnings.append(f"Low coverage ratio: {coverage:.2f} (less than 50%)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "cue_count": len(cues),
            "total_duration": metadata.get('total_duration', 0.0)
        }

# Utility functions for integration
def align_lesson_slide(lesson_id: str, slide_id: int, 
                      speaker_notes: str,
                      sentence_timings: List[Dict[str, Any]],
                      slide_elements: List[Dict[str, Any]],
                      existing_cues: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Align a lesson slide with complete timing synchronization
    
    Args:
        lesson_id: Lesson identifier
        slide_id: Slide number
        speaker_notes: Speaker notes text
        sentence_timings: TTS timing information
        slide_elements: Slide elements
        existing_cues: Optional existing cues
        
    Returns:
        Complete alignment result with validation
    """
    try:
        aligner = TimelineAligner()
        
        # Perform alignment
        alignment_result = aligner.align_slide_content(
            speaker_notes, sentence_timings, slide_elements, existing_cues
        )
        
        # Validate result
        validation = aligner.validate_alignment(alignment_result)
        
        # Add validation to result
        alignment_result['validation'] = validation
        
        logger.info(f"Aligned slide {slide_id} for lesson {lesson_id}: {len(alignment_result['cues'])} cues, {validation['valid']}")
        
        return alignment_result
        
    except Exception as e:
        logger.error(f"Failed to align lesson slide: {e}")
        raise

def save_alignment_result(lesson_id: str, slide_id: int, alignment_result: Dict[str, Any], output_dir: Path) -> Path:
    """Save alignment result to file"""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        alignment_file = output_dir / f"{lesson_id}_slide_{slide_id:03d}_alignment.json"
        
        with open(alignment_file, 'w', encoding='utf-8') as f:
            json.dump(alignment_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved alignment result: {alignment_file}")
        return alignment_file
        
    except Exception as e:
        logger.error(f"Error saving alignment result: {e}")
        raise

if __name__ == "__main__":
    # Test the aligner
    def test_aligner():
        test_notes = "Welcome to our presentation. Today we will discuss AI technology and its applications."
        
        test_timings = [
            {"sentence": "Welcome to our presentation.", "t0": 0.0, "t1": 2.5, "duration": 2.5, "index": 0},
            {"sentence": "Today we will discuss AI technology and its applications.", "t0": 2.8, "t1": 6.0, "duration": 3.2, "index": 1}
        ]
        
        test_elements = [
            {"id": "elem_1", "type": "text", "text": "Welcome to our presentation", "bbox": [100, 100, 400, 50]},
            {"id": "elem_2", "type": "text", "text": "AI technology", "bbox": [100, 200, 300, 50]},
            {"id": "elem_3", "type": "text", "text": "Applications", "bbox": [100, 300, 200, 50]}
        ]
        
        aligner = TimelineAligner()
        result = aligner.align_slide_content(test_notes, test_timings, test_elements)
        
        print("Alignment result:")
        print(f"  Cues: {len(result['cues'])}")
        print(f"  Duration: {result['total_duration']:.2f}s")
        print(f"  Coverage: {result['metadata']['coverage_ratio']:.2f}")
        
        for i, cue in enumerate(result['cues']):
            print(f"  Cue {i}: {cue['t0']:.2f}s - {cue['t1']:.2f}s, {cue['action']}")
        
        validation = aligner.validate_alignment(result)
        print(f"  Valid: {validation['valid']}")
        if validation['warnings']:
            print(f"  Warnings: {validation['warnings']}")
    
    test_aligner()