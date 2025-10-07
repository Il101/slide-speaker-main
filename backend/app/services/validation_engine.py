"""
Stage 6: Multi-Layer Validation Engine
Проверка и исправление ошибок в semantic map и cues
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class ValidationEngine:
    """Многослойная валидация для защиты от галлюцинаций и ошибок"""
    
    def __init__(self):
        self.fuzzy_match_threshold = 0.85
        self.min_coverage = 0.90
        self.max_cognitive_load = 4  # Не больше 4 элементов одновременно
    
    def validate_semantic_map(
        self,
        semantic_map: Dict[str, Any],
        ocr_elements: List[Dict[str, Any]],
        slide_size: Tuple[int, int] = (1440, 1080)
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Многослойная валидация semantic map
        
        Args:
            semantic_map: Semantic map из LLM
            ocr_elements: Оригинальные OCR элементы
            slide_size: Размер слайда (width, height)
            
        Returns:
            (fixed_semantic_map, validation_errors)
        """
        errors = []
        
        logger.info("Starting multi-layer validation")
        
        # Layer 1: Semantic Validation
        semantic_errors = self._validate_semantic_structure(semantic_map)
        errors.extend(semantic_errors)
        
        # Layer 2: Geometric Validation
        geometric_errors = self._validate_geometry(semantic_map, slide_size)
        errors.extend(geometric_errors)
        
        # Layer 3: Hallucination Check
        hallucination_errors, fixed_map = self._check_hallucinations(semantic_map, ocr_elements)
        errors.extend(hallucination_errors)
        semantic_map = fixed_map
        
        # Layer 4: Coverage Analysis
        coverage_errors, fixed_map = self._check_coverage(semantic_map, ocr_elements)
        errors.extend(coverage_errors)
        semantic_map = fixed_map
        
        # Layer 5: Cognitive Load Check
        cognitive_errors = self._check_cognitive_load(semantic_map)
        errors.extend(cognitive_errors)
        
        if errors:
            logger.warning(f"Validation found {len(errors)} issues (auto-fixed where possible)")
        else:
            logger.info("✅ Validation passed with no errors")
        
        return semantic_map, errors
    
    def _validate_semantic_structure(self, semantic_map: Dict[str, Any]) -> List[str]:
        """Layer 1: Validate semantic structure"""
        errors = []
        
        # Check required fields
        if 'groups' not in semantic_map:
            errors.append("Missing 'groups' field in semantic map")
            semantic_map['groups'] = []
        
        groups = semantic_map.get('groups', [])
        
        # Check each group
        for i, group in enumerate(groups):
            # Check required group fields
            if 'id' not in group:
                errors.append(f"Group {i} missing 'id' field")
                group['id'] = f"group_{i}"
            
            if 'priority' not in group:
                errors.append(f"Group {group['id']} missing 'priority' field")
                group['priority'] = 'medium'
            
            if 'element_ids' not in group:
                errors.append(f"Group {group['id']} missing 'element_ids' field")
                group['element_ids'] = []
            
            # Check highlight strategy
            if 'highlight_strategy' not in group:
                errors.append(f"Group {group['id']} missing 'highlight_strategy'")
                group['highlight_strategy'] = {
                    'when': 'during_explanation',
                    'effect_type': 'highlight',
                    'duration': 2.0,
                    'intensity': 'normal'
                }
        
        return errors
    
    def _validate_geometry(
        self,
        semantic_map: Dict[str, Any],
        slide_size: Tuple[int, int]
    ) -> List[str]:
        """Layer 2: Validate geometric constraints"""
        errors = []
        width, height = slide_size
        
        groups = semantic_map.get('groups', [])
        
        for group in groups:
            # Check if group has bbox (optional)
            if 'bbox' in group:
                bbox = group['bbox']
                
                # Validate bbox format
                if not isinstance(bbox, list) or len(bbox) != 4:
                    errors.append(f"Group {group['id']} has invalid bbox format")
                    continue
                
                x, y, w, h = bbox
                
                # Check boundaries
                if x < 0 or y < 0:
                    errors.append(f"Group {group['id']} bbox has negative coordinates")
                
                if x + w > width or y + h > height:
                    errors.append(f"Group {group['id']} bbox exceeds slide boundaries")
        
        return errors
    
    def _check_hallucinations(
        self,
        semantic_map: Dict[str, Any],
        ocr_elements: List[Dict[str, Any]]
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Layer 3: Check for hallucinated elements"""
        errors = []
        
        # Create set of valid element IDs from OCR
        valid_element_ids = set()
        element_texts = {}
        
        for elem in ocr_elements:
            elem_id = elem.get('id', '')
            valid_element_ids.add(elem_id)
            element_texts[elem_id] = elem.get('text', '')
        
        groups = semantic_map.get('groups', [])
        fixed_groups = []
        
        for group in groups:
            element_ids = group.get('element_ids', [])
            fixed_element_ids = []
            
            for elem_id in element_ids:
                if elem_id in valid_element_ids:
                    # Valid element
                    fixed_element_ids.append(elem_id)
                else:
                    # Try fuzzy matching
                    match, similarity = self._fuzzy_match_element(elem_id, valid_element_ids)
                    
                    if match and similarity >= self.fuzzy_match_threshold:
                        # Found close match
                        logger.info(f"Fuzzy matched '{elem_id}' -> '{match}' (similarity: {similarity:.2f})")
                        fixed_element_ids.append(match)
                    else:
                        # Hallucinated element
                        errors.append(f"Hallucinated element '{elem_id}' in group {group['id']} (removed)")
            
            # Update group with fixed element IDs
            group['element_ids'] = fixed_element_ids
            
            # Only keep groups with at least one valid element
            if fixed_element_ids:
                fixed_groups.append(group)
            else:
                errors.append(f"Group {group['id']} has no valid elements (removed)")
        
        semantic_map['groups'] = fixed_groups
        
        return errors, semantic_map
    
    def _fuzzy_match_element(
        self,
        elem_id: str,
        valid_ids: set
    ) -> Tuple[Optional[str], float]:
        """Find fuzzy match for element ID"""
        best_match = None
        best_similarity = 0.0
        
        for valid_id in valid_ids:
            similarity = SequenceMatcher(None, elem_id, valid_id).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = valid_id
        
        return best_match, best_similarity
    
    def _check_coverage(
        self,
        semantic_map: Dict[str, Any],
        ocr_elements: List[Dict[str, Any]]
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Layer 4: Check coverage of OCR elements"""
        errors = []
        
        # Get all element IDs covered by groups
        covered_elements = set()
        for group in semantic_map.get('groups', []):
            covered_elements.update(group.get('element_ids', []))
        
        # Get noise elements
        noise_elements = set(semantic_map.get('noise_elements', []))
        covered_elements.update(noise_elements)
        
        # Get all OCR element IDs
        all_element_ids = {elem.get('id', f'elem_{i}') for i, elem in enumerate(ocr_elements)}
        
        # Find missed elements
        missed_elements = all_element_ids - covered_elements
        
        # Calculate coverage
        if all_element_ids:
            coverage = len(covered_elements) / len(all_element_ids)
        else:
            coverage = 1.0
        
        if coverage < self.min_coverage:
            errors.append(f"Low coverage: {coverage*100:.1f}% (threshold: {self.min_coverage*100:.0f}%)")
            
            # Auto-add missed elements to "uncategorized" group
            if missed_elements:
                logger.info(f"Auto-adding {len(missed_elements)} missed elements to uncategorized group")
                
                uncategorized_group = {
                    "id": "group_uncategorized",
                    "name": "Uncategorized Content",
                    "type": "content",
                    "priority": "low",
                    "element_ids": list(missed_elements),
                    "reading_order": list(range(1, len(missed_elements) + 1)),
                    "educational_intent": "Additional content",
                    "highlight_strategy": {
                        "when": "during_detail",
                        "effect_type": "highlight",
                        "duration": 1.5,
                        "intensity": "subtle"
                    },
                    "dependencies": {
                        "highlight_before": None,
                        "highlight_together_with": None,
                        "highlight_after": None
                    }
                }
                
                semantic_map['groups'].append(uncategorized_group)
        
        return errors, semantic_map
    
    def _check_cognitive_load(self, semantic_map: Dict[str, Any]) -> List[str]:
        """Layer 5: Check cognitive load (not too many highlights at once)"""
        errors = []
        
        groups = semantic_map.get('groups', [])
        
        # Count high-priority groups
        high_priority_count = sum(1 for g in groups if g.get('priority') == 'high')
        
        if high_priority_count > self.max_cognitive_load:
            errors.append(
                f"Too many high-priority groups ({high_priority_count} > {self.max_cognitive_load}). "
                "Consider reducing priority for some groups."
            )
        
        return errors
    
    def validate_cues(
        self,
        cues: List[Dict[str, Any]],
        audio_duration: float,
        elements: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Validate visual cues
        
        Args:
            cues: List of cues
            audio_duration: Duration of audio
            elements: OCR elements
            
        Returns:
            (fixed_cues, validation_errors)
        """
        errors = []
        fixed_cues = []
        
        logger.info("Validating visual cues")
        
        element_ids = {elem.get('id', f'elem_{i}') for i, elem in enumerate(elements)}
        
        for i, cue in enumerate(cues):
            # Check timing
            t0 = cue.get('t0', 0)
            t1 = cue.get('t1', 0)
            
            if t0 < 0:
                errors.append(f"Cue {i}: negative t0 ({t0})")
                cue['t0'] = 0
            
            if t1 <= t0:
                errors.append(f"Cue {i}: t1 <= t0 ({t1} <= {t0})")
                cue['t1'] = t0 + 0.5
            
            if t1 > audio_duration:
                errors.append(f"Cue {i}: t1 exceeds audio duration ({t1} > {audio_duration})")
                cue['t1'] = audio_duration
            
            # Check element_id exists
            elem_id = cue.get('element_id')
            if elem_id and elem_id not in element_ids:
                # Try to find in noise_elements or remove
                errors.append(f"Cue {i}: references non-existent element '{elem_id}'")
                # Keep the cue but mark as invalid
                cue['invalid_element'] = True
            
            fixed_cues.append(cue)
        
        # ✅ Fix overlapping cues
        fixed_cues, overlap_errors = self._fix_overlapping_cues(fixed_cues)
        errors.extend(overlap_errors)
        
        if errors:
            logger.warning(f"Cue validation found {len(errors)} issues")
        else:
            logger.info("✅ Cue validation passed")
        
        return fixed_cues, errors
    
    def _fix_overlapping_cues(self, cues: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Fix overlapping cues by adjusting their timing
        
        Args:
            cues: List of cues
            
        Returns:
            (fixed_cues, errors_list)
        """
        if not cues:
            return cues, []
        
        errors = []
        
        # Sort by t0
        sorted_cues = sorted(cues, key=lambda c: c.get('t0', 0))
        
        # Fix overlaps
        for i in range(len(sorted_cues) - 1):
            current = sorted_cues[i]
            next_cue = sorted_cues[i + 1]
            
            current_t1 = current.get('t1', 0)
            next_t0 = next_cue.get('t0', 0)
            
            if current_t1 > next_t0:
                # Overlap detected
                overlap_duration = current_t1 - next_t0
                errors.append(f"Cue overlap: {i} and {i+1} overlap by {overlap_duration:.2f}s")
                
                # Strategy: reduce t1 of current cue with small gap
                min_gap = 0.05  # 50ms gap between cues
                current['t1'] = next_t0 - min_gap
                
                # Ensure cue still has minimum duration (0.3s)
                min_duration = 0.3
                if current['t1'] - current['t0'] < min_duration:
                    # If reducing t1 makes duration too short, shift next_t0 instead
                    required_t1 = current['t0'] + min_duration
                    if required_t1 < next_t0:
                        current['t1'] = required_t1
                    else:
                        # Keep original timing - overlap is necessary
                        current['t1'] = current_t1
                        logger.debug(f"Keeping overlap for cue {i} (necessary for minimum duration)")
                
                logger.debug(f"Fixed overlap: cue {i} t1 adjusted to {current['t1']:.3f}s")
        
        if errors:
            logger.info(f"✅ Fixed {len(errors)} overlapping cues")
        
        return sorted_cues, errors
