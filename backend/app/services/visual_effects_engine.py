"""
Stage 5: Smart Visual Effects Engine
Выбор и применение визуальных эффектов на основе semantic map
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
import re
import os

logger = logging.getLogger(__name__)

# ✅ Try to import Google Translate API (optional dependency)
try:
    from google.cloud import translate_v2 as translate
    GOOGLE_TRANSLATE_AVAILABLE = True
    logger.info("✅ Google Translate API available")
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False
    logger.warning("⚠️ Google Translate API not available, using static dictionary only")

class VisualEffectsEngine:
    """Умный выбор визуальных эффектов на основе semantic analysis"""
    
    # Определение доступных эффектов
    EFFECTS = {
        "spotlight": {
            "description": "Луч света на элемент (драматично)",
            "good_for": ["key_formula", "important_definition", "critical_point"],
            "intensity": "dramatic"
        },
        "group_bracket": {
            "description": "Скобка вокруг группы элементов",
            "good_for": ["bullet_list", "related_items", "steps"],
            "intensity": "normal"
        },
        "blur_others": {
            "description": "Размыть все кроме выделенного",
            "good_for": ["focus_element", "complex_slide"],
            "intensity": "dramatic"
        },
        "sequential_cascade": {
            "description": "Последовательное выделение элементов",
            "good_for": ["bullet_list", "step_by_step", "timeline"],
            "intensity": "normal"
        },
        "highlight": {
            "description": "Классическое выделение цветом",
            "good_for": ["text", "default"],
            "intensity": "normal"
        },
        "underline": {
            "description": "Подчёркивание",
            "good_for": ["text", "emphasis"],
            "intensity": "subtle"
        },
        "zoom_subtle": {
            "description": "Лёгкое увеличение",
            "good_for": ["small_text", "detail"],
            "intensity": "subtle"
        },
        "dimmed_spotlight": {
            "description": "Приглушить фон + spotlight",
            "good_for": ["high_priority", "key_concept"],
            "intensity": "dramatic"
        },
        "glow": {
            "description": "Мягкое свечение",
            "good_for": ["important", "attention"],
            "intensity": "normal"
        },
        "pointer_animated": {
            "description": "Анимированный указатель",
            "good_for": ["diagram", "specific_location"],
            "intensity": "subtle"
        },
        "laser_move": {
            "description": "Движение лазерной указки",
            "good_for": ["transition", "connection"],
            "intensity": "subtle"
        },
        "ken_burns": {
            "description": "Медленный zoom и pan (эффект Кена Бёрнса)",
            "good_for": ["image", "photo", "diagram"],
            "intensity": "subtle",
            "duration": 8.0
        },
        "typewriter": {
            "description": "Печатание текста по буквам",
            "good_for": ["title", "quote", "key_message"],
            "intensity": "normal",
            "chars_per_second": 15
        },
        "particle_highlight": {
            "description": "Частицы и свечение вокруг элемента",
            "good_for": ["key_concept", "breakthrough", "important"],
            "intensity": "dramatic",
            "particle_count": 30
        },
        "slide_in": {
            "description": "Появление элемента со стороны",
            "good_for": ["list_item", "new_element"],
            "intensity": "subtle",
            "directions": ["left", "right", "top", "bottom"]
        },
        "fade_in": {
            "description": "Плавное появление",
            "good_for": ["text", "any"],
            "intensity": "subtle"
        },
        "pulse": {
            "description": "Пульсирующее свечение",
            "good_for": ["alert", "warning", "attention"],
            "intensity": "normal",
            "pulse_count": 3
        },
        "circle_draw": {
            "description": "Обводка элемента кругом",
            "good_for": ["diagram_element", "attention", "focus"],
            "intensity": "normal"
        },
        "arrow_point": {
            "description": "Анимированная стрелка указывает на элемент",
            "good_for": ["diagram", "important_detail", "connection"],
            "intensity": "normal"
        },
        "shake": {
            "description": "Лёгкая встряска для привлечения внимания",
            "good_for": ["warning", "alert", "emphasis"],
            "intensity": "dramatic",
            "shake_intensity": "medium"
        },
        "morph": {
            "description": "Плавная трансформация формы/размера",
            "good_for": ["transition", "change", "comparison"],
            "intensity": "normal"
        }
    }
    
    def __init__(self):
        self.min_highlight_duration = 0.8
        self.max_highlight_duration = 5.0
        self.min_gap_between_effects = 0.2
        
        # ✅ Initialize Google Translate client if available
        self.translate_client = None
        if GOOGLE_TRANSLATE_AVAILABLE:
            try:
                self.translate_client = translate.Client()
                logger.info("✅ Google Translate client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize Google Translate: {e}")
        
        # ✅ Translation cache: {term_key: [translations]}
        # Speeds up repeated translations
        self.translation_cache = {}
        
        # ✅ Dictionary of common scientific term translations (static fallback)
        # Format: {foreign_term_lowercase: [russian_equivalents]}
        # This is a FALLBACK for common terms when API is unavailable
        self.term_translations = {
            # German botanical terms
            'epidermis': ['эпидермис', 'эпидерма'],
            'hypodermis': ['гиподермис', 'гиподерма'],
            'mesophyll': ['мезофилл'],
            'chlorenchym': ['хлоренхима', 'хлоренхим'],
            'palisadenparenchym': ['палисадная паренхима', 'палисадный паренхим', 'столбчатая паренхима'],
            'palisaden': ['палисадн', 'столбчат'],
            'parenchym': ['паренхима', 'паренхим'],
            'schwammparenchym': ['губчатая паренхима', 'губчатый паренхим'],
            'schwamm': ['губчат'],
            'cuticula': ['кутикула'],
            'assimilationsgewebe': ['ассимиляционная ткань', 'ассимиляцион'],
            'blattoberseite': ['верхн', 'сторон', 'лист'],
            'blattunterseite': ['нижн', 'сторон', 'лист'],
            'blatt': ['лист'],
            'zelle': ['клетк'],
            'gewebe': ['ткан'],
            'stomata': ['устьиц', 'устье'],
            'spaltöffnung': ['устьиц', 'устье'],
            'leitbündel': ['провод', 'пучок', 'жилк'],
            'xylem': ['ксилема', 'древесина'],
            'phloem': ['флоэма', 'луб'],
            'trichom': ['трихома', 'волосок'],
            
            # Latin/English terms
            'vascular': ['васкулярн', 'сосудист', 'провод'],
            'bundle': ['пучок'],
            'tissue': ['ткан'],
            'cell': ['клетк'],
            'layer': ['слой'],
        }
    
    def generate_cues_from_semantic_map(
        self,
        semantic_map: Dict[str, Any],
        elements: List[Dict[str, Any]],
        audio_duration: float,
        tts_words: Optional[Dict[str, Any]] = None,
        talk_track: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Генерирует visual cues на основе semantic map
        
        Args:
            semantic_map: Semantic map из SemanticAnalyzer
            elements: OCR элементы с координатами
            audio_duration: Длительность аудио
            tts_words: Timing information from TTS
            
        Returns:
            List of cues с улучшенными эффектами
        """
        try:
            logger.info("Generating visual cues from semantic map")
            
            # Extract word timings from TTS
            word_timings = self._extract_word_timings(tts_words)
            if word_timings:
                logger.info(f"Using {len(word_timings)} word timings from TTS for synchronization")
            else:
                logger.warning("No TTS word timings available, using time-based distribution")
            
            groups = semantic_map.get('groups', [])
            if not groups:
                logger.warning("No groups in semantic map, using fallback")
                return self._generate_fallback_cues(elements, audio_duration)
            
            # Create element lookup
            elements_by_id = {elem.get('id', f'elem_{i}'): elem for i, elem in enumerate(elements)}
            
            # Generate cues for each group
            all_cues = []
            current_time = 0.5  # Start with 0.5s delay
            
            for group in groups:
                # Skip noise groups
                if group.get('priority') == 'none':
                    continue
                
                # Get highlight strategy
                strategy = group.get('highlight_strategy', {})
                when = strategy.get('when', 'during_explanation')
                effect_type = strategy.get('effect_type', 'highlight')
                duration = strategy.get('duration', 2.0)
                intensity = strategy.get('intensity', 'normal')
                
                # Skip 'never' strategy
                if when == 'never':
                    continue
                
                # Adjust timing based on 'when'
                if when == 'start':
                    current_time = 0.3
                elif when == 'end':
                    current_time = max(current_time, audio_duration - duration - 0.5)
                
                # Get elements for this group
                group_element_ids = group.get('element_ids', [])
                group_elements = [elements_by_id[eid] for eid in group_element_ids if eid in elements_by_id]
                
                if not group_elements:
                    continue
                
                # ✅ Try to find timing from talk_track segments (with calculated timing)
                group_id = group.get('id')
                timing_intervals = self._find_timing_from_talk_track_segments(group_id, talk_track)
                
                # ✅ FIX: Handle multiple timing intervals for the same group
                if timing_intervals:
                    # Create cues for each interval where the group is mentioned
                    for interval in timing_intervals:
                        current_time = interval['start']
                        original_duration = interval['duration']  # Original interval length
                        duration = min(original_duration, self.max_highlight_duration)  # Clamped for single cue
                        logger.debug(f"✅ Group '{group_id}' synced to TTS interval: {current_time:.2f}s - {current_time + duration:.2f}s")
                        
                        # ✅ NEW: If ORIGINAL interval is very long, split into multiple shorter cues for individual elements
                        # Note: Check original_duration, not clamped duration!
                        LONG_SEGMENT_THRESHOLD = 10.0  # seconds
                        if original_duration > LONG_SEGMENT_THRESHOLD and len(group_elements) > 1:
                            logger.info(f"🔪 Long segment ({original_duration:.1f}s) - splitting into element-level cues")
                            # ✅ Try smart word-based timing first
                            # Use ORIGINAL duration for splitting, not clamped!
                            group_cues = self._generate_smart_element_cues(
                                group,
                                group_elements,
                                current_time,
                                original_duration,  # Use original, not clamped!
                                effect_type,
                                intensity,
                                tts_words,
                                talk_track
                            )
                        else:
                            # Normal: generate single group cue
                            group_cues = self._generate_group_cues(
                                group,
                                group_elements,
                                current_time,
                                duration,
                                effect_type,
                                intensity
                            )
                        all_cues.extend(group_cues)
                else:
                    # No timing from talk_track, try fallbacks
                    timing_info = None
                    
                    # Fallback 1: Try to find from TTS words using group_id
                    timing_info = self._find_group_timing(group_id, word_timings, audio_duration)
                    
                    if not timing_info:
                        # Fallback 2: Try to find first words from talk_track in word_timings (extended search)
                        group_text = self._get_talk_track_text(group_id, talk_track)
                        if group_text:
                            logger.info(f"🔄 Fallback: searching first 5-7 words from talk_track for group '{group_id}'")
                            # Try with 7 words first (more precise)
                            timing_info = self._find_timing_by_first_words(group_text, tts_words, audio_duration, num_words=7)
                            # If not found, try with 5 words
                            if not timing_info:
                                timing_info = self._find_timing_by_first_words(group_text, tts_words, audio_duration, num_words=5)
                        
                        # Fallback 3: Try sentence-based text matching if first words failed
                        if not timing_info:
                            if not group_text:
                                # Use slide element text as last resort
                                group_text = self._get_group_text(group, elements_by_id)
                            if group_text:
                                logger.info(f"🔄 Fallback: trying sentence matching for group '{group_id}'")
                                timing_info = self._find_text_timing_from_sentences(group_text, tts_words, audio_duration)
                    
                    if timing_info:
                        # Use real TTS timing!
                        current_time = timing_info['start']
                        original_duration = timing_info['duration']  # Original timing length
                        duration = min(original_duration, self.max_highlight_duration)  # Clamped for single cue
                        logger.debug(f"✅ Group '{group_id}' synced to TTS: {current_time:.2f}s - {current_time + duration:.2f}s")
                    
                    # ✅ NEW: Check if ORIGINAL segment is long and split if needed
                    # Note: Check original_duration, not clamped duration!
                    LONG_SEGMENT_THRESHOLD = 10.0
                    if timing_info and original_duration > LONG_SEGMENT_THRESHOLD and len(group_elements) > 1:
                        logger.info(f"🔪 Long segment ({original_duration:.1f}s) - splitting into element-level cues")
                        group_cues = self._generate_smart_element_cues(
                            group,
                            group_elements,
                            current_time,
                            original_duration,  # Use original, not clamped!
                            effect_type,
                            intensity,
                            tts_words,
                            talk_track
                        )
                    else:
                        # Generate cues based on effect type
                        group_cues = self._generate_group_cues(
                            group,
                            group_elements,
                            current_time,
                            duration,
                            effect_type,
                            intensity
                        )
                    
                    all_cues.extend(group_cues)
                
                # Update current time
                current_time += duration + self.min_gap_between_effects
                
                # Don't exceed audio duration
                if current_time >= audio_duration:
                    break
            
            # Sort cues by time
            all_cues = sorted(all_cues, key=lambda c: c.get('t0', 0))
            
            # Validate and fix overlaps
            all_cues = self._validate_and_fix_cues(all_cues, audio_duration)
            
            logger.info(f"✅ Generated {len(all_cues)} visual cues")
            return all_cues
            
        except Exception as e:
            logger.error(f"Error generating cues: {e}")
            return self._generate_fallback_cues(elements, audio_duration)
    
    def _generate_smart_element_cues(
        self,
        group: Dict[str, Any],
        elements: List[Dict[str, Any]],
        start_time: float,
        total_duration: float,
        effect_type: str,
        intensity: str,
        tts_words: Optional[Dict[str, Any]],
        talk_track: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Generate element cues with SMART word-based timing
        
        Strategy:
        1. For each element, find when its text is mentioned in talk_track
        2. Use TTS word_timings to get precise timing
        3. Create cue at the moment of mention
        4. Fallback to sequential if no mentions found
        
        Args:
            group: Group information
            elements: List of elements in the group
            start_time: Segment start time
            total_duration: Segment duration
            effect_type: Type of effect
            intensity: Effect intensity
            tts_words: TTS timing data
            talk_track: Talk track segments
            
        Returns:
            List of visual cues synced to word mentions
        """
        cues = []
        group_id = group.get('id', 'unknown')
        
        if not elements:
            return cues
        
        # Filter tiny elements
        MIN_WIDTH, MIN_HEIGHT = 20, 10
        filtered_elements = [e for e in elements if 
                           e.get('bbox') and len(e.get('bbox', [])) >= 4 and
                           e['bbox'][2] >= MIN_WIDTH and e['bbox'][3] >= MIN_HEIGHT]
        
        if not filtered_elements:
            filtered_elements = [max(elements, key=lambda e: (e.get('bbox', [0,0,0,0])[2] * e.get('bbox', [0,0,0,0])[3]))]
        
        # Try to find mentions for each element
        element_timings = []
        
        for elem in filtered_elements:
            elem_text = elem.get('text', '').strip()
            if not elem_text or len(elem_text) < 3:
                continue
            
            # Search for element text in talk_track
            timing = self._find_element_mention_timing(
                elem_text, 
                talk_track, 
                tts_words, 
                start_time, 
                start_time + total_duration
            )
            
            if timing:
                element_timings.append({
                    'element': elem,
                    'timing': timing,
                    'found': True
                })
                logger.info(f"   ✅ Found '{elem_text[:30]}...' at {timing['start']:.1f}s")
            else:
                element_timings.append({
                    'element': elem,
                    'timing': None,
                    'found': False
                })
                logger.debug(f"   ⚠️ Not found: '{elem_text[:30]}...'")
        
        # Generate cues for found elements
        found_count = sum(1 for et in element_timings if et['found'])
        
        if found_count > 0:
            logger.info(f"   📍 Word-based timing: {found_count}/{len(element_timings)} elements")
            
            # Create cues for elements with found timing
            for et in element_timings:
                if et['found']:
                    timing = et['timing']
                    elem = et['element']
                    
                    cues.append({
                        "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                        "t0": round(timing['start'], 3),
                        "t1": round(timing['end'], 3),
                        "action": "highlight",
                        "bbox": elem.get('bbox'),
                        "group_id": group_id,
                        "element_id": elem.get('id'),
                        "target_element_ids": [elem.get('id')],
                        "effect_type": "word_synced",
                        "intensity": intensity,
                        "sync_method": "word_mention"
                    })
            
            # For elements not found, distribute in gaps
            not_found_elements = [et['element'] for et in element_timings if not et['found']]
            if not_found_elements:
                logger.info(f"   ⏱️ Distributing {len(not_found_elements)} unfound elements in gaps")
                fallback_cues = self._distribute_elements_in_gaps(
                    not_found_elements,
                    cues,
                    start_time,
                    total_duration,
                    group_id,
                    intensity
                )
                cues.extend(fallback_cues)
        else:
            # No elements found, fallback to sequential
            logger.warning(f"   ⚠️ No word mentions found, using sequential fallback")
            return self._generate_sequential_element_cues(
                group,
                filtered_elements,
                start_time,
                total_duration,
                effect_type,
                intensity
            )
        
        return sorted(cues, key=lambda c: c['t0'])
    
    def _generate_sequential_element_cues(
        self,
        group: Dict[str, Any],
        elements: List[Dict[str, Any]],
        start_time: float,
        total_duration: float,
        effect_type: str,
        intensity: str
    ) -> List[Dict[str, Any]]:
        """
        Generate sequential cues for individual elements in a group over a long duration
        
        Strategy:
        - Distribute elements evenly across total_duration
        - Each element gets 2-3 seconds of highlight
        - Small gaps between elements for natural flow
        
        Args:
            group: Group information
            elements: List of elements in the group
            start_time: When to start
            total_duration: Total time available
            effect_type: Type of effect
            intensity: Effect intensity
            
        Returns:
            List of visual cues
        """
        cues = []
        group_id = group.get('id', 'unknown')
        
        if not elements:
            return cues
        
        # Filter tiny elements
        MIN_WIDTH, MIN_HEIGHT = 20, 10
        filtered_elements = [e for e in elements if 
                           e.get('bbox') and len(e.get('bbox', [])) >= 4 and
                           e['bbox'][2] >= MIN_WIDTH and e['bbox'][3] >= MIN_HEIGHT]
        
        if not filtered_elements:
            filtered_elements = [max(elements, key=lambda e: (e.get('bbox', [0,0,0,0])[2] * e.get('bbox', [0,0,0,0])[3]))]
        
        num_elements = len(filtered_elements)
        
        # Calculate timing for each element
        ELEMENT_DURATION = 2.5  # Each element highlighted for 2.5s
        GAP_BETWEEN = 0.5  # 0.5s gap between elements
        
        # If we have more time than needed, spread elements out
        time_per_element = ELEMENT_DURATION + GAP_BETWEEN
        total_needed = num_elements * time_per_element
        
        if total_needed > total_duration:
            # Too many elements, reduce duration
            time_per_element = total_duration / num_elements
            ELEMENT_DURATION = max(1.5, time_per_element - 0.3)  # Minimum 1.5s per element
            GAP_BETWEEN = time_per_element - ELEMENT_DURATION
        else:
            # We have extra time, distribute evenly
            time_per_element = total_duration / num_elements
            ELEMENT_DURATION = min(3.0, time_per_element * 0.85)  # Max 3s per element
            GAP_BETWEEN = time_per_element - ELEMENT_DURATION
        
        logger.info(f"   Splitting into {num_elements} elements: {ELEMENT_DURATION:.1f}s each, {GAP_BETWEEN:.1f}s gaps")
        
        # Generate cue for each element
        current_time = start_time
        for i, elem in enumerate(filtered_elements):
            t0 = current_time
            t1 = current_time + ELEMENT_DURATION
            
            cues.append({
                "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                "t0": round(t0, 3),
                "t1": round(t1, 3),
                "action": "highlight",
                "bbox": elem.get('bbox'),
                "group_id": group_id,
                "element_id": elem.get('id'),
                "target_element_ids": [elem.get('id')],
                "effect_type": "sequential_element",
                "intensity": intensity,
                "sequence_index": i,
                "sequence_total": num_elements
            })
            
            current_time += ELEMENT_DURATION + GAP_BETWEEN
        
        return cues
    
    def _generate_group_cues(
        self,
        group: Dict[str, Any],
        elements: List[Dict[str, Any]],
        start_time: float,
        duration: float,
        effect_type: str,
        intensity: str
    ) -> List[Dict[str, Any]]:
        """Generate cues for a specific group"""
        cues = []
        group_id = group.get('id', 'unknown')
        
        # Filter out tiny elements (bullets, dots, etc) - keep only meaningful content
        MIN_WIDTH = 20   # minimum 20 pixels width
        MIN_HEIGHT = 10  # minimum 10 pixels height
        
        filtered_elements = []
        for elem in elements:
            bbox = elem.get('bbox')
            if bbox and len(bbox) >= 4:
                width, height = bbox[2], bbox[3]
                if width >= MIN_WIDTH and height >= MIN_HEIGHT:
                    filtered_elements.append(elem)
                else:
                    logger.debug(f"Skipping tiny element {elem.get('id')} ({width}x{height}px)")
        
        # If all elements were filtered out, use the largest one
        if not filtered_elements and elements:
            filtered_elements = [max(elements, key=lambda e: (e.get('bbox', [0,0,0,0])[2] * e.get('bbox', [0,0,0,0])[3]))]
        
        elements = filtered_elements
        
        if effect_type == "sequential_cascade":
            # Последовательное выделение элементов
            element_duration = duration / len(elements) if elements else duration
            for i, elem in enumerate(elements):
                t0 = start_time + i * element_duration
                t1 = t0 + element_duration
                
                cues.append({
                    "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                    "t0": round(t0, 3),
                    "t1": round(t1, 3),
                    "action": "highlight",
                    "bbox": elem.get('bbox'),
                    "group_id": group_id,  # ✅ Added group_id
                    "element_id": elem.get('id'),
                    "effect_type": "sequential",
                    "intensity": intensity
                })
        
        elif effect_type == "group_bracket":
            # Скобка вокруг всей группы
            group_bbox = self._calculate_group_bbox(elements)
            element_ids = [e.get('id') for e in elements]
            
            cues.append({
                "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                "t0": round(start_time, 3),
                "t1": round(start_time + duration, 3),
                "action": "group_bracket",
                "bbox": group_bbox,
                "group_id": group_id,  # ✅ Added group_id
                "element_id": element_ids[0] if len(element_ids) == 1 else None,
                "group_elements": element_ids if len(element_ids) > 1 else None,
                "effect_type": "bracket",
                "intensity": intensity
            })
        
        elif effect_type == "blur_others":
            # Blur everything except this group
            group_bbox = self._calculate_group_bbox(elements)
            element_ids = [e.get('id') for e in elements]
            
            cues.append({
                "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                "t0": round(start_time, 3),
                "t1": round(start_time + duration, 3),
                "action": "blur_others",
                "bbox": group_bbox,
                "group_id": group_id,  # ✅ Added group_id
                "element_id": element_ids[0] if len(element_ids) == 1 else None,
                "group_elements": element_ids if len(element_ids) > 1 else None,
                "effect_type": "blur_focus",
                "intensity": intensity
            })
        
        elif effect_type == "spotlight":
            # Драматичный spotlight
            group_bbox = self._calculate_group_bbox(elements)
            element_ids = [e.get('id') for e in elements]
            
            cues.append({
                "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                "t0": round(start_time, 3),
                "t1": round(start_time + duration, 3),
                "action": "spotlight",
                "bbox": group_bbox,
                "group_id": group_id,  # ✅ Added group_id
                "element_id": element_ids[0] if len(element_ids) == 1 else None,
                "group_elements": element_ids if len(element_ids) > 1 else None,
                "effect_type": "spotlight",
                "intensity": "dramatic"
            })
        
        elif effect_type == "dimmed_spotlight":
            # Комбо: приглушить фон + spotlight
            group_bbox = self._calculate_group_bbox(elements)
            
            # First dim the background
            cues.append({
                "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                "t0": round(start_time, 3),
                "t1": round(start_time + duration, 3),
                "action": "dim_background",
                "bbox": None,
                "group_id": group_id,  # ✅ Added group_id (for background dim)
                "element_id": None,
                "effect_type": "dim",
                "intensity": "subtle"
            })
            
            # Then spotlight the group
            element_ids = [e.get('id') for e in elements]
            cues.append({
                "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                "t0": round(start_time + 0.2, 3),
                "t1": round(start_time + duration, 3),
                "action": "spotlight",
                "bbox": group_bbox,
                "group_id": group_id,  # ✅ Added group_id
                "element_id": element_ids[0] if len(element_ids) == 1 else None,
                "group_elements": element_ids if len(element_ids) > 1 else None,
                "effect_type": "spotlight",
                "intensity": "dramatic"
            })
        
        else:
            # Default: highlight каждый элемент
            for elem in elements:
                cues.append({
                    "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                    "t0": round(start_time, 3),
                    "t1": round(start_time + duration, 3),
                    "action": effect_type,
                    "bbox": elem.get('bbox'),
                    "group_id": group_id,  # ✅ Added group_id
                    "element_id": elem.get('id'),
                    "effect_type": effect_type,
                    "intensity": intensity
                })
        
        return cues
    
    def _find_element_mention_timing(
        self,
        elem_text: str,
        talk_track: Optional[List[Dict[str, Any]]],
        tts_words: Optional[Dict[str, Any]],
        segment_start: float,
        segment_end: float
    ) -> Optional[Dict[str, float]]:
        """
        Find when element text is mentioned in talk_track
        
        Strategy:
        1. Clean element text (remove noise)
        2. Search in talk_track segments (especially in [lang:XX] markers)
        3. Use sentence timing or word timing from TTS
        4. Return timing with небольшим буфером
        
        Args:
            elem_text: Text from element (e.g. "Epidermis der Blattoberseite")
            talk_track: Talk track segments
            tts_words: TTS timing data
            segment_start: Start time of current segment
            segment_end: End time of current segment
            
        Returns:
            Dict with 'start' and 'end' timing, or None if not found
        """
        if not talk_track or not elem_text:
            return None
        
        # Clean element text: lowercase, remove special chars
        import re
        clean_elem = elem_text.lower().strip()
        # Extract key words (min 3 chars)
        elem_words = [w for w in re.findall(r'\w+', clean_elem) if len(w) >= 3]
        
        if not elem_words:
            return None
        
        # ✅ NEW: Get Russian translations for foreign terms (static dict + API)
        # Detect source language from element text
        source_lang = self._detect_language(elem_text)
        
        search_terms = set(elem_words)  # Start with original words
        for word in elem_words:
            # Get translations (tries dict → cache → API → fallback)
            translations = self._translate_term_to_russian(word, source_lang)
            if translations:
                search_terms.update(translations)
        
        logger.debug(f"      Searching for {len(search_terms)} terms (lang={source_lang}): {list(search_terms)[:10]}...")
        
        # Search in talk_track segments within time range
        for segment in talk_track:
            seg_start = segment.get('start', 0)
            seg_end = segment.get('end', 0)
            
            # Skip if outside our time range
            if seg_end < segment_start or seg_start > segment_end:
                continue
            
            text = segment.get('text', '')
            
            # ✅ NEW: Priority 1 - Extract original terms from parentheses (LLM-added for visual sync)
            # Pattern: (Foreign Term) or ([lang:XX]Foreign Term[/lang])
            # Examples: 
            # - "эпидермис (Epidermis) верхней стороны"
            # - "мезофилл ([lang:de]Mesophyll[/lang]) листа"
            parentheses_pattern = r'\(([^)]+)\)'
            parentheses_raw_matches = re.findall(parentheses_pattern, text)
            
            # Clean up extracted terms (remove [lang:XX] markers if present)
            parentheses_matches = []
            for match in parentheses_raw_matches:
                # Remove [lang:XX] markers: [lang:de]Term[/lang] → Term
                clean_match = re.sub(r'\[lang:[a-z]{2}\](.*?)\[/lang\]', r'\1', match, flags=re.IGNORECASE)
                # Remove [visual:XX] markers: [visual:de]Term[/visual] → Term
                clean_match = re.sub(r'\[visual:[a-z]{2}\](.*?)\[/visual\]', r'\1', clean_match, flags=re.IGNORECASE)
                clean_match = clean_match.strip()
                if clean_match:
                    parentheses_matches.append(clean_match)
            
            # Priority 2 - Extract text from [lang:XX] markers (where foreign terms are)
            lang_pattern = r'\[lang:[a-z]{2}\](.*?)\[/lang\]'
            lang_matches = re.findall(lang_pattern, text, re.IGNORECASE)
            
            # Priority 3 - Also check in [visual:XX] markers
            visual_pattern = r'\[visual:[a-z]{2}\](.*?)\[/visual\]'
            visual_matches = re.findall(visual_pattern, text, re.IGNORECASE)
            
            # ✅ Combine all candidates with priority (parentheses first!)
            candidates = parentheses_matches + lang_matches + visual_matches + [text]
            
            for candidate in candidates:
                candidate_lower = candidate.lower()
                
                # ✅ IMPROVED: Check if ANY search term (original or translated) appears in candidate
                # Use fuzzy matching on all search terms
                found_terms = [term for term in search_terms if term.lower() in candidate_lower]
                
                # Calculate match ratio based on original words
                # If any translation matches, count as found
                matched_original_words = 0
                for word in elem_words:
                    word_lower = word.lower()
                    # Check if original word found
                    if word_lower in candidate_lower:
                        matched_original_words += 1
                    # Or check if any translation found
                    elif word_lower in self.term_translations:
                        translations = self.term_translations[word_lower]
                        if any(trans.lower() in candidate_lower for trans in translations):
                            matched_original_words += 1
                
                match_ratio = matched_original_words / len(elem_words) if elem_words else 0
                
                # ✅ Lower threshold since translations might be partial matches
                if match_ratio >= 0.5 or len(found_terms) >= 2:  # 50% match or 2+ terms found
                    logger.info(f"      ✅ Found match: '{elem_text[:40]}' in '{candidate[:60]}...' ({match_ratio:.0%}, {len(found_terms)} terms)")
                    
                    # Use segment timing - NO BUFFER (sync exactly to speech)
                    # User requested: effect should appear when word is spoken, not before
                    DURATION = 2.5  # Default highlight duration
                    
                    # Start exactly when segment starts (no advance buffer)
                    start = max(segment_start, seg_start)
                    end = min(start + DURATION, seg_end)
                    
                    return {
                        'start': start,
                        'end': end,
                        'duration': end - start,
                        'match_ratio': match_ratio,
                        'found_terms': found_terms
                    }
        
        return None
    
    def _translate_term_to_russian(self, term: str, source_lang: str = 'auto') -> List[str]:
        """
        Translate a term to Russian using Google Translate API or static dictionary
        
        Strategy:
        1. Check static dictionary first (fast, reliable for common terms)
        2. Check translation cache
        3. Use Google Translate API if available
        4. Return [term] if translation fails (fallback to original)
        
        Args:
            term: Term to translate (e.g. "epidermis", "mesophyll")
            source_lang: Source language code ('de', 'en', 'auto')
            
        Returns:
            List of Russian translation variants
        """
        term_lower = term.lower().strip()
        
        if not term_lower or len(term_lower) < 3:
            return []
        
        # ✅ 1. Check static dictionary first (fastest)
        if term_lower in self.term_translations:
            translations = self.term_translations[term_lower]
            logger.debug(f"      📖 Dict: '{term}' → {translations}")
            return translations
        
        # ✅ 2. Check cache
        cache_key = f"{source_lang}:{term_lower}"
        if cache_key in self.translation_cache:
            translations = self.translation_cache[cache_key]
            logger.debug(f"      💾 Cache: '{term}' → {translations}")
            return translations
        
        # ✅ 3. Try Google Translate API
        if self.translate_client:
            try:
                result = self.translate_client.translate(
                    term,
                    target_language='ru',
                    source_language=source_lang if source_lang != 'auto' else None
                )
                
                translated = result.get('translatedText', '').strip()
                if translated and translated.lower() != term_lower:
                    # Success! Cache it
                    translations = [translated]
                    self.translation_cache[cache_key] = translations
                    logger.info(f"      🌐 API: '{term}' → {translations}")
                    return translations
                else:
                    logger.debug(f"      ⚠️ API returned same term: '{term}'")
            except Exception as e:
                logger.debug(f"      ❌ Translation API error for '{term}': {e}")
        
        # ✅ 4. Fallback: return original term
        # Maybe it's already in Russian or it's a proper name
        logger.debug(f"      ⚠️ No translation for '{term}', using original")
        return [term_lower]
    
    def _detect_language(self, text: str) -> str:
        """
        Detect language of text
        
        Simple heuristic-based detection:
        - Cyrillic chars → Russian
        - Umlauts (ä,ö,ü) → German
        - Otherwise → English
        
        Args:
            text: Text to detect language from
            
        Returns:
            Language code: 'ru', 'de', 'en', 'auto'
        """
        # Check for Cyrillic
        if re.search(r'[а-яА-ЯёЁ]', text):
            return 'ru'
        
        # Check for German umlauts
        if re.search(r'[äöüÄÖÜß]', text):
            return 'de'
        
        # Check for Latin alphabet (English by default)
        if re.search(r'[a-zA-Z]', text):
            return 'en'
        
        return 'auto'
    
    def _distribute_elements_in_gaps(
        self,
        elements: List[Dict[str, Any]],
        existing_cues: List[Dict[str, Any]],
        start_time: float,
        total_duration: float,
        group_id: str,
        intensity: str
    ) -> List[Dict[str, Any]]:
        """
        Distribute unfound elements in time gaps between existing cues
        
        Strategy:
        - Find gaps between existing cues
        - Distribute elements evenly in those gaps
        - Each element gets 2s
        
        Args:
            elements: Elements without timing
            existing_cues: Already created cues
            start_time: Segment start
            total_duration: Segment duration
            group_id: Group ID
            intensity: Effect intensity
            
        Returns:
            List of cues for unfound elements
        """
        if not elements:
            return []
        
        cues = []
        end_time = start_time + total_duration
        
        # Sort existing cues by time
        sorted_cues = sorted(existing_cues, key=lambda c: c['t0'])
        
        # Find gaps
        gaps = []
        last_end = start_time
        
        for cue in sorted_cues:
            if cue['t0'] > last_end + 1.0:  # At least 1s gap
                gaps.append((last_end, cue['t0']))
            last_end = cue['t1']
        
        # Add final gap if exists
        if end_time > last_end + 1.0:
            gaps.append((last_end, end_time))
        
        # Distribute elements in gaps
        ELEMENT_DURATION = 2.0
        
        for i, elem in enumerate(elements):
            if i >= len(gaps):
                break  # No more gaps
            
            gap_start, gap_end = gaps[i]
            gap_duration = gap_end - gap_start
            
            # Center element in gap
            available = min(ELEMENT_DURATION, gap_duration * 0.8)
            t0 = gap_start + (gap_duration - available) / 2
            t1 = t0 + available
            
            cues.append({
                "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                "t0": round(t0, 3),
                "t1": round(t1, 3),
                "action": "highlight",
                "bbox": elem.get('bbox'),
                "group_id": group_id,
                "element_id": elem.get('id'),
                "target_element_ids": [elem.get('id')],
                "effect_type": "gap_distributed",
                "intensity": intensity,
                "sync_method": "gap_fallback"
            })
        
        return cues
    
    def _calculate_group_bbox(self, elements: List[Dict[str, Any]]) -> List[float]:
        """Calculate bounding box that encompasses all elements in a group"""
        if not elements:
            return [0, 0, 0, 0]
        
        # Extract all bboxes
        bboxes = [elem.get('bbox', [0, 0, 0, 0]) for elem in elements]
        
        # Find min x, min y, max x, max y
        min_x = min(bbox[0] for bbox in bboxes)
        min_y = min(bbox[1] for bbox in bboxes)
        max_x = max(bbox[0] + bbox[2] for bbox in bboxes)
        max_y = max(bbox[1] + bbox[3] for bbox in bboxes)
        
        # Add padding
        padding = 10
        min_x = max(0, min_x - padding)
        min_y = max(0, min_y - padding)
        max_x += padding
        max_y += padding
        
        return [min_x, min_y, max_x - min_x, max_y - min_y]
    
    def _validate_and_fix_cues(
        self,
        cues: List[Dict[str, Any]],
        audio_duration: float
    ) -> List[Dict[str, Any]]:
        """Validate cues and fix timing issues"""
        fixed_cues = []
        
        for i, cue in enumerate(cues):
            # Ensure t1 > t0
            if cue.get('t1', 0) <= cue.get('t0', 0):
                cue['t1'] = cue['t0'] + self.min_highlight_duration
            
            # Ensure duration within limits
            duration = cue['t1'] - cue['t0']
            if duration < self.min_highlight_duration:
                cue['t1'] = cue['t0'] + self.min_highlight_duration
            elif duration > self.max_highlight_duration:
                cue['t1'] = cue['t0'] + self.max_highlight_duration
            
            # Ensure within audio duration
            if cue['t1'] > audio_duration:
                cue['t1'] = audio_duration
            if cue['t0'] >= audio_duration:
                continue  # Skip this cue
            
            # Fix overlaps with previous cue
            if i > 0 and fixed_cues:
                prev_cue = fixed_cues[-1]
                if cue['t0'] < prev_cue['t1']:
                    cue['t0'] = prev_cue['t1'] + self.min_gap_between_effects
            
            fixed_cues.append(cue)
        
        return fixed_cues
    
    def _generate_fallback_cues(
        self,
        elements: List[Dict[str, Any]],
        audio_duration: float
    ) -> List[Dict[str, Any]]:
        """Fallback cue generation if semantic map is not available"""
        logger.info("Using fallback cue generation")
        
        cues = []
        element_duration = audio_duration / max(len(elements), 1)
        
        for i, elem in enumerate(elements[:10]):  # Limit to 10 elements
            t0 = i * element_duration
            t1 = min(t0 + element_duration * 0.8, audio_duration)
            
            cues.append({
                "cue_id": f"cue_{uuid.uuid4().hex[:8]}",
                "t0": round(t0, 3),
                "t1": round(t1, 3),
                "action": "highlight",
                "bbox": elem.get('bbox'),
                "group_id": None,  # ✅ Fallback mode, no group
                "element_id": elem.get('id'),
                "effect_type": "highlight",
                "intensity": "normal"
            })
        
        return cues
    
    def _extract_word_timings(self, tts_words: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract word-level timings from TTS response (supports SSML word_timings)"""
        if not tts_words:
            return []
        
        timings = []
        
        # ✅ Priority 1: Check for SSML word_timings (from GoogleTTSWorkerSSML)
        if 'word_timings' in tts_words and tts_words['word_timings']:
            # Convert mark-based timings to word timings
            for wt in tts_words['word_timings']:
                timings.append({
                    'word': wt.get('mark_name', ''),  # mark_0, mark_1, etc
                    'time_seconds': wt.get('time_seconds', 0),
                    't0': wt.get('time_seconds', 0),
                    't1': wt.get('time_seconds', 0) + 0.5  # Approximate duration
                })
            logger.info(f"✅ Using {len(timings)} SSML word timings")
            return timings
        
        # Priority 2: Check sentence-level words
        if 'sentences' in tts_words:
            for sentence in tts_words['sentences']:
                # Try word-level timings first
                if 'words' in sentence and sentence['words']:
                    timings.extend(sentence['words'])
                # Fallback to sentence-level timings
                elif 'text' in sentence and 't0' in sentence:
                    # Treat whole sentence as one "word" for timing purposes
                    timings.append({
                        'word': sentence['text'],
                        'time_seconds': sentence['t0'],
                        't0': sentence['t0'],
                        't1': sentence.get('t1', sentence['t0'] + 1.0)
                    })
        
        # Priority 3: Check for direct 'words' key
        elif 'words' in tts_words:
            timings = tts_words['words']
        
        return timings
    
    def _find_group_timing(
        self,
        group_id: str,
        word_timings: List[Dict[str, Any]],
        audio_duration: float
    ) -> Optional[Dict[str, float]]:
        """
        Find timing for a group using group marker from SSML
        
        Args:
            group_id: ID of the group (e.g., "group_title_0")
            word_timings: List of word timings from TTS
            audio_duration: Total audio duration
            
        Returns:
            Dict with 'start' and 'duration' or None if not found
        """
        if not word_timings or not group_id:
            return None
        
        # Normalize marker name to match SSML - don't double "group_" prefix
        marker_name = group_id if group_id.startswith('group_') else f"group_{group_id}"
        logger.debug(f"🔍 Looking for group marker: '{marker_name}'")
        logger.debug(f"   Available marks: {[t.get('mark_name', t.get('word', '?')) for t in word_timings[:10]]}")
        
        for i, timing in enumerate(word_timings):
            mark_name = timing.get('mark_name', timing.get('word', ''))
            
            if mark_name == marker_name:
                # Found the group marker!
                start_time = timing.get('time_seconds', timing.get('t0', 0))
                
                # Calculate duration: use next group marker or end of audio
                duration = self.max_highlight_duration
                
                # Look for next group marker
                for j in range(i + 1, len(word_timings)):
                    next_mark = word_timings[j].get('mark_name', '')
                    if next_mark.startswith('group_'):
                        # Found next group
                        end_time = word_timings[j].get('time_seconds', start_time + duration)
                        duration = min(end_time - start_time, self.max_highlight_duration)
                        break
                
                # Ensure duration is reasonable
                duration = max(self.min_highlight_duration, min(duration, self.max_highlight_duration))
                
                logger.info(f"✅ Found group marker '{marker_name}' at {start_time:.2f}s, duration {duration:.2f}s")
                
                return {
                    'start': start_time,
                    'duration': duration,
                    'end': start_time + duration
                }
        
        # Not found
        logger.warning(f"⚠️  Group marker '{marker_name}' NOT FOUND in {len(word_timings)} TTS timings")
        return None
    
    def _find_timing_from_talk_track_segments(
        self,
        group_id: str,
        talk_track: List[Dict[str, Any]]
    ) -> List[Dict[str, float]]:
        """
        Find ALL timing intervals for a group (может быть несколько несмежных упоминаний)
        
        ✅ FIX: Returns LIST of intervals instead of single range to avoid
        visual effects "sticking" during unrelated segments.
        
        Returns:
            List of timing intervals [{'start': float, 'duration': float}, ...]
        """
        if not talk_track or not group_id:
            return []
        
        # Find all segments with this group_id with their indices
        matching_segments = [
            (idx, seg) for idx, seg in enumerate(talk_track)
            if seg.get('group_id') == group_id
            and 'start' in seg and 'end' in seg
        ]
        
        if not matching_segments:
            return []
        
        # ✅ FIX: Group consecutive segments into intervals
        intervals = []
        current_interval = None
        
        for idx, seg in matching_segments:
            start = seg['start']
            end = seg['end']
            
            if current_interval is None:
                # Start new interval
                current_interval = {'start': start, 'end': end, 'last_idx': idx}
            elif idx == current_interval['last_idx'] + 1:
                # Continue current interval (consecutive segments)
                current_interval['end'] = end
                current_interval['last_idx'] = idx
            else:
                # Gap detected! Save current interval and start new one
                intervals.append({
                    'start': current_interval['start'],
                    'duration': current_interval['end'] - current_interval['start']
                })
                current_interval = {'start': start, 'end': end, 'last_idx': idx}
        
        # Add last interval
        if current_interval:
            intervals.append({
                'start': current_interval['start'],
                'duration': current_interval['end'] - current_interval['start']
            })
        
        # ✅ NO PADDING - sync exactly to speech timing
        # User requested: effects should appear when word is spoken, not before
        # Intervals used as-is without advance timing
        
        logger.info(f"✅ Found {len(intervals)} timing interval(s) for '{group_id}'")
        for i, interval in enumerate(intervals):
            logger.info(f"   Interval {i+1}: {interval['start']:.1f}s - {interval['start']+interval['duration']:.1f}s (Δ{interval['duration']:.1f}s)")
        
        return intervals
    
    def _find_timing_from_talk_track_segments_legacy(
        self,
        group_id: str,
        talk_track: List[Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """
        Legacy method: returns single interval spanning all mentions
        (kept for backward compatibility but not recommended)
        """
        intervals = self._find_timing_from_talk_track_segments(group_id, talk_track)
        if not intervals:
            return None
        
        # Return first interval or merged range
        if len(intervals) == 1:
            return {
                'start': intervals[0]['start'],
                'duration': intervals[0]['duration'],
                'end': adjusted_end
            }
        
        return None
    
    def _extract_original_terms(self, text: str) -> str:
        """
        Extract original terms from markers for visual effects matching:
        - [visual:XX]term[/visual] → term (for visual sync, not spoken)
        - [lang:XX]term[/lang] → term
        - [phoneme:ipa:...]term[/phoneme] → term
        
        Example: "рассмотрим [visual:de]Das Blatt[/visual] — строение листа"
        Returns: "рассмотрим Das Blatt — строение листа"
        
        This allows fallback search to find original terms in audio timing.
        """
        import re
        # Replace [visual:XX]term[/visual] with just term (highest priority)
        visual_pattern = r'\[visual:[a-z]{2}\](.*?)\[/visual\]'
        text = re.sub(visual_pattern, r'\1', text)
        # Replace [phoneme:ipa:...]term[/phoneme] with just term
        phoneme_pattern = r'\[phoneme:ipa:.*?\](.*?)\[/phoneme\]'
        text = re.sub(phoneme_pattern, r'\1', text)
        # Replace [lang:XX]term[/lang] with just term
        lang_pattern = r'\[lang:[a-z]{2}\](.*?)\[/lang\]'
        text = re.sub(lang_pattern, r'\1', text)
        return text
    
    def _get_talk_track_text(self, group_id: str, talk_track: Optional[List[Dict[str, Any]]]) -> str:
        """Get narration text from talk_track for given group_id"""
        if not talk_track:
            return ''
        
        for segment in talk_track:
            if segment.get('group_id') == group_id:
                raw_text = segment.get('text', '').strip()
                # Extract original terms from [original|pronunciation] markers
                return self._extract_original_terms(raw_text)
        
        return ''
    
    def _find_timing_by_first_words(
        self,
        text: str,
        tts_words: Optional[Dict[str, Any]],
        audio_duration: float,
        num_words: int = 3
    ) -> Optional[Dict[str, float]]:
        """
        Find timing by searching for first N words from text in TTS word_timings
        
        This is more reliable than sentence matching because it uses word-level timings
        from Google TTS directly.
        
        Args:
            text: Text to search (from talk_track)
            tts_words: TTS response with word_timings
            audio_duration: Total audio duration
            num_words: Number of first words to search for (default 3)
            
        Returns:
            Dict with 'start' and 'duration' or None if not found
        """
        if not tts_words or not text:
            return None
        
        word_timings = tts_words.get('word_timings', [])
        if not word_timings:
            logger.warning("⚠️  No word_timings available for first words search")
            return None
        
        # Extract first N significant words from text
        import re
        # Remove markers before extracting words
        clean_text = re.sub(r'\[(visual|lang|phoneme|emphasis|pitch|rate|pause):[^\]]*\]', '', text)
        clean_text = re.sub(r'\[/(visual|lang|phoneme|emphasis|pitch|rate)\]', '', clean_text)
        
        words = re.findall(r'\b\w+\b', clean_text.lower())
        # Filter out very short words (articles, prepositions) and take first N
        significant_words = [w for w in words if len(w) > 2][:num_words]
        
        if not significant_words:
            logger.warning(f"⚠️  No significant words found in text: '{text[:50]}'")
            return None
        
        logger.info(f"🔍 Searching for {num_words} words: {significant_words}")
        
        # Search for these words in word_timings
        # word_timings has marks like 'w0', 'w1', etc - we need to reconstruct words
        # Actually, Google TTS returns word timepoints but we mark them as w0, w1...
        # We need to check if there's actual word text in timings
        
        # ✅ IMPROVED: Better timing search with fuzzy matching
        # Check structure of word_timings
        if word_timings and isinstance(word_timings[0], dict):
            # Look for word marks that correspond to our first words
            # Since we don't have actual word text in timings (only mark names),
            # we need a different approach
            
            # Use sentences to find approximate position
            sentences = tts_words.get('sentences', [])
            if sentences:
                best_match = None
                best_match_count = 0
                best_score = 0
                
                for sentence in sentences:
                    sentence_text = sentence.get('text', '').lower()
                    
                    # Improved word matching with sequence consideration
                    found_words = []
                    score = 0
                    sentence_words = re.findall(r'\b\w+\b', sentence_text)
                    
                    # Try to find our words in the sentence
                    for target_word in significant_words:
                        for i, sent_word in enumerate(sentence_words):
                            # Fuzzy match: exact or substring
                            if target_word == sent_word or (len(target_word) > 4 and target_word in sent_word):
                                found_words.append(target_word)
                                # Higher score for words found early in sentence
                                score += max(10 - i, 1)
                                break
                    
                    match_count = len(found_words)
                    
                    # Require at least 50% of words to match (or minimum 1 word)
                    min_required = max(1, len(significant_words) * 0.5)
                    if match_count >= min_required and score > best_score:
                        best_score = score
                        best_match_count = match_count
                        t0 = sentence.get('t0', 0)
                        t1 = sentence.get('t1', t0 + 3.0)
                        
                        # Smart duration calculation
                        base_duration = t1 - t0
                        duration = min(base_duration, self.max_highlight_duration)
                        duration = max(duration, self.min_highlight_duration)
                        
                        # ✅ NO PADDING - sync exactly to speech timing
                        # User requested: effects should appear when word is spoken, not before
                        
                        best_match = {
                            'start': max(0, t0),  # Start exactly when word starts
                            'duration': duration,  # No padding added
                            'end': min(audio_duration, t1),  # End exactly when word ends
                            'found_words': found_words,
                            'match_ratio': match_count / len(significant_words),
                            'confidence': score / (len(significant_words) * 10)  # Normalized confidence
                        }
                
                if best_match:
                    logger.info(f"✅ Found {best_match_count}/{len(significant_words)} words {best_match['found_words']} at {best_match['start']:.2f}s (confidence: {best_match['confidence']:.0%})")
                    return best_match
        
        logger.warning(f"⚠️  Could not find first words {significant_words} in TTS data")
        return None
    
    def _get_group_text(self, group: Dict[str, Any], elements_by_id: Dict[str, Dict]) -> str:
        """Get combined text from all elements in group"""
        element_ids = group.get('element_ids', [])
        texts = []
        
        for eid in element_ids:
            if eid in elements_by_id:
                text = elements_by_id[eid].get('text', '')
                if text:
                    texts.append(text)
        
        return ' '.join(texts).strip()
    
    def _find_text_timing(
        self, 
        text: str, 
        word_timings: List[Dict[str, Any]], 
        audio_duration: float
    ) -> Optional[Dict[str, float]]:
        """
        Find when specific text is spoken in TTS
        
        Args:
            text: Text to find
            word_timings: List of word timings from TTS
            audio_duration: Total audio duration
            
        Returns:
            Dict with 'start' and 'duration' or None if not found
        """
        if not word_timings or not text:
            return None
        
        # Normalize text for matching
        text_normalized = text.lower().strip()
        text_words = text_normalized.split()
        
        if not text_words:
            return None
        
        # Try to find the first few words of the text in TTS timings
        search_words = text_words[:min(3, len(text_words))]  # First 3 words
        
        for i, timing in enumerate(word_timings):
            word = timing.get('word', timing.get('mark_name', '')).lower().strip()
            
            # Check if this is the start of our text
            if self._normalize_word(word) == self._normalize_word(search_words[0]):
                # Found potential start, verify next words
                match_length = 1
                
                for j in range(1, len(search_words)):
                    if i + j >= len(word_timings):
                        break
                    
                    next_word = word_timings[i + j].get('word', '').lower().strip()
                    if self._normalize_word(next_word) == self._normalize_word(search_words[j]):
                        match_length += 1
                    else:
                        break
                
                # If we matched at least 2 words (or all search words), consider it a match
                if match_length >= min(2, len(search_words)):
                    start_time = timing.get('time_seconds', timing.get('t0', 0))
                    
                    # Calculate duration: try to find end of text
                    end_idx = min(i + len(text_words), len(word_timings) - 1)
                    end_time = word_timings[end_idx].get('time_seconds', start_time + 2.0)
                    
                    duration = max(1.0, min(end_time - start_time, 5.0))
                    
                    return {
                        'start': start_time,
                        'duration': duration,
                        'end': start_time + duration
                    }
        
        return None
    
    def _find_text_timing_from_sentences(
        self, 
        text: str, 
        tts_words: Optional[Dict[str, Any]], 
        audio_duration: float
    ) -> Optional[Dict[str, float]]:
        """
        Find timing by matching text to TTS sentences (fallback for SSML mode)
        
        This is used when group markers are not available in SSML.
        Uses sentence-level timings instead of word-level marks.
        
        Args:
            text: Text to find
            tts_words: Full TTS response with 'sentences' key
            audio_duration: Total audio duration
            
        Returns:
            Dict with 'start' and 'duration' or None if not found
        """
        if not tts_words or not text:
            return None
        
        sentences = tts_words.get('sentences', [])
        if not sentences:
            logger.warning(f"⚠️  No sentences in tts_words for fallback matching (tts_words keys: {list(tts_words.keys()) if tts_words else 'None'})")
            return None
        
        # Normalize search text - use first 50 chars for matching
        search_text = self._normalize_word(text.strip()[:50])
        
        if not search_text:
            logger.warning(f"⚠️  Empty search text after normalization: '{text[:50]}'")
            return None
        
        logger.info(f"🔍 Fallback: searching for '{search_text[:30]}...' in {len(sentences)} sentences")
        
        for sentence in sentences:
            sentence_text = sentence.get('text', '').strip()
            normalized_sentence = self._normalize_word(sentence_text)
            
            # Check if search text appears in sentence (first 20 chars for fuzzy match)
            if search_text[:20] in normalized_sentence:
                t0 = sentence.get('t0', 0)
                t1 = sentence.get('t1', t0 + 2.0)
                duration = min(t1 - t0, self.max_highlight_duration)
                
                logger.info(f"✅ Fallback match found: '{sentence_text[:50]}...' at {t0:.2f}s")
                
                return {
                    'start': t0,
                    'duration': max(self.min_highlight_duration, duration),
                    'end': t1
                }
        
        logger.warning("⚠️  No fallback match found in sentences")
        return None
    
    def _normalize_word(self, word: str) -> str:
        """Normalize word for matching (remove punctuation, etc.)"""
        import re
        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', '', word.lower())
        return normalized.strip()
