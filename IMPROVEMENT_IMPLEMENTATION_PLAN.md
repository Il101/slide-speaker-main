# 🚀 План Внедрения Улучшений Pipeline

**Дата создания:** 1 ноября 2025  
**Версия:** 1.0  
**Статус:** Ready for Implementation

---

## 📊 Executive Summary

**Цель:** Повысить качество лекций с 82% до 95%+  
**Срок реализации:** 3-4 недели (при 1 разработчике)  
**Приоритет:** HIGH → MEDIUM → LOW

---

## 🎯 Roadmap Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Week 1-2: Phase 1 (CRITICAL)                                   │
│  ├─ Diagram Recognition                                         │
│  ├─ Highlight Strategy Implementation                           │
│  └─ Priority-Based Timing                                       │
│                                                                  │
│  Week 2-3: Phase 2 (IMPORTANT)                                  │
│  ├─ Visual Hierarchy                                            │
│  ├─ Element Relationships                                       │
│  └─ Sequential Cascade Fix                                      │
│                                                                  │
│  Week 3-4: Phase 3 (NICE-TO-HAVE)                              │
│  ├─ Assessment Segments                                         │
│  ├─ Quality Metrics                                             │
│  └─ Pedagogical Metadata                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Phase 1: CRITICAL Improvements (Week 1-2)

### 🔥 1.1 Diagram Recognition & Processing

**Priority:** 🔴 CRITICAL  
**Impact:** HIGH (диаграммы составляют 30-50% контента научных презентаций)  
**Effort:** MEDIUM (3-4 дня)  
**Dependencies:** None

#### Проблема
```
Текущая ситуация:
- Диаграммы, графики, изображения не распознаются
- OCR извлекает только текст
- AI не может объяснить визуальный контент
- Лекция становится неполной
```

#### Решение
```
1. Vision API: определение типа элемента (text/diagram/image)
2. Добавление diagram_type в elements
3. Генерация специальных сегментов для диаграмм
4. Адаптация visual cues для диаграмм
```

#### Реализация

##### Step 1.1.1: Extend OCR to Detect Diagrams (1 день)

**Файл:** `backend/app/services/ocr_vision.py` (или создать новый)

```python
# backend/app/services/diagram_detector.py

from google.cloud import vision
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class DiagramDetector:
    """Detects and classifies non-text elements (diagrams, images, charts)"""
    
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
        
        # Thresholds for classification
        self.TEXT_AREA_THRESHOLD = 0.3  # If >30% area is text, it's likely text
        self.MIN_DIAGRAM_SIZE = 100  # Minimum bbox size
    
    def detect_diagrams(self, image_path: str, text_elements: List[Dict]) -> List[Dict]:
        """
        Detect non-text elements (diagrams, images, charts)
        
        Args:
            image_path: Path to slide image
            text_elements: Already detected text elements (from OCR)
            
        Returns:
            List of diagram elements with type, bbox, description
        """
        with open(image_path, 'rb') as f:
            content = f.read()
        
        image = vision.Image(content=content)
        
        # Step 1: Detect objects
        objects = self.client.object_localization(image=image).localized_object_annotations
        
        # Step 2: Detect labels (for classification)
        labels = self.client.label_detection(image=image).label_annotations
        
        # Step 3: Calculate text coverage
        text_coverage = self._calculate_text_coverage(text_elements)
        
        # Step 4: Find regions without text (potential diagrams)
        diagram_candidates = self._find_non_text_regions(
            image_path, text_elements, objects
        )
        
        # Step 5: Classify diagrams
        diagrams = []
        for candidate in diagram_candidates:
            diagram_type = self._classify_diagram(candidate, objects, labels)
            
            if diagram_type:
                diagrams.append({
                    "id": f"diagram_{len(diagrams)}",
                    "type": "diagram",
                    "diagram_type": diagram_type,
                    "bbox": candidate['bbox'],
                    "confidence": candidate['confidence'],
                    "description": self._generate_description(
                        diagram_type, objects, labels
                    ),
                    "visual_complexity": self._estimate_complexity(candidate),
                    "key_elements": self._extract_key_elements(
                        diagram_type, objects, labels
                    )
                })
        
        logger.info(f"Detected {len(diagrams)} diagrams")
        return diagrams
    
    def _calculate_text_coverage(self, text_elements: List[Dict]) -> float:
        """Calculate percentage of image covered by text"""
        if not text_elements:
            return 0.0
        
        # Assume image size (or get from metadata)
        image_area = 1440 * 1080  # Default slide size
        
        text_area = 0
        for elem in text_elements:
            bbox = elem.get('bbox', [])
            if len(bbox) == 4:
                x, y, w, h = bbox
                text_area += w * h
        
        return text_area / image_area
    
    def _find_non_text_regions(
        self, 
        image_path: str, 
        text_elements: List[Dict],
        objects: List
    ) -> List[Dict]:
        """Find image regions not covered by text"""
        # TODO: Implement region detection
        # For now, use object localization from Vision API
        
        candidates = []
        for obj in objects:
            vertices = obj.bounding_poly.normalized_vertices
            
            # Convert to bbox
            x_coords = [v.x for v in vertices]
            y_coords = [v.y for v in vertices]
            
            x = int(min(x_coords) * 1440)
            y = int(min(y_coords) * 1080)
            w = int((max(x_coords) - min(x_coords)) * 1440)
            h = int((max(y_coords) - min(y_coords)) * 1080)
            
            # Check if this region overlaps with text
            overlaps_text = self._overlaps_with_text([x, y, w, h], text_elements)
            
            if not overlaps_text and w > self.MIN_DIAGRAM_SIZE:
                candidates.append({
                    'bbox': [x, y, w, h],
                    'confidence': obj.score,
                    'name': obj.name
                })
        
        return candidates
    
    def _overlaps_with_text(
        self, 
        bbox: List[int], 
        text_elements: List[Dict]
    ) -> bool:
        """Check if bbox overlaps significantly with text elements"""
        x1, y1, w1, h1 = bbox
        
        for elem in text_elements:
            text_bbox = elem.get('bbox', [])
            if len(text_bbox) == 4:
                x2, y2, w2, h2 = text_bbox
                
                # Calculate overlap
                overlap_area = self._calculate_overlap(
                    x1, y1, w1, h1,
                    x2, y2, w2, h2
                )
                
                bbox_area = w1 * h1
                if overlap_area / bbox_area > 0.3:  # >30% overlap
                    return True
        
        return False
    
    def _calculate_overlap(
        self, 
        x1: int, y1: int, w1: int, h1: int,
        x2: int, y2: int, w2: int, h2: int
    ) -> float:
        """Calculate overlap area between two bboxes"""
        # Find intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        return (x_right - x_left) * (y_bottom - y_top)
    
    def _classify_diagram(
        self, 
        candidate: Dict, 
        objects: List,
        labels: List
    ) -> str:
        """Classify diagram type based on objects and labels"""
        name = candidate.get('name', '').lower()
        
        # Check label annotations
        label_names = [label.description.lower() for label in labels[:10]]
        
        # Classification logic
        if any(word in name or word in label_names 
               for word in ['chart', 'graph', 'plot']):
            return 'chart'
        
        elif any(word in name or word in label_names 
                 for word in ['diagram', 'flowchart', 'flow']):
            return 'flowchart'
        
        elif any(word in name or word in label_names 
                 for word in ['table', 'matrix']):
            return 'table'
        
        elif any(word in name or word in label_names 
                 for word in ['photo', 'image', 'picture']):
            return 'image'
        
        elif any(word in name or word in label_names 
                 for word in ['icon', 'symbol', 'logo']):
            return 'icon'
        
        else:
            return 'generic_diagram'
    
    def _generate_description(
        self, 
        diagram_type: str,
        objects: List,
        labels: List
    ) -> str:
        """Generate natural language description of diagram"""
        label_names = [label.description for label in labels[:5]]
        
        descriptions = {
            'chart': f"График или диаграмма, показывающая данные о {', '.join(label_names[:2])}",
            'flowchart': f"Блок-схема, иллюстрирующая процесс или алгоритм",
            'table': f"Таблица с данными",
            'image': f"Изображение: {', '.join(label_names[:3])}",
            'icon': f"Иконка или символ",
            'generic_diagram': f"Диаграмма, связанная с {', '.join(label_names[:2])}"
        }
        
        return descriptions.get(diagram_type, "Визуальный элемент")
    
    def _estimate_complexity(self, candidate: Dict) -> str:
        """Estimate visual complexity (low/medium/high)"""
        bbox = candidate['bbox']
        area = bbox[2] * bbox[3]
        
        if area > 500000:  # Large diagram
            return 'high'
        elif area > 200000:
            return 'medium'
        else:
            return 'low'
    
    def _extract_key_elements(
        self, 
        diagram_type: str,
        objects: List,
        labels: List
    ) -> List[str]:
        """Extract key elements visible in diagram"""
        # Use labels as proxy for key elements
        return [label.description for label in labels[:5]]
```

**Тестирование:**
```python
# backend/tests/test_diagram_detector.py

def test_diagram_detection():
    detector = DiagramDetector()
    
    # Test with slide containing diagram
    diagrams = detector.detect_diagrams(
        "test_slides/slide_with_diagram.png",
        text_elements=[...]  # Mock text elements
    )
    
    assert len(diagrams) > 0
    assert diagrams[0]['type'] == 'diagram'
    assert 'diagram_type' in diagrams[0]
```

---

##### Step 1.1.2: Integrate into Pipeline (0.5 дня)

**Файл:** `backend/app/pipeline/intelligent_optimized.py`

```python
def extract_elements_ocr(self, lesson_dir: str) -> None:
    """Stage 2: OCR + Diagram Detection"""
    # ... existing OCR code ...
    
    # NEW: Add diagram detection
    from app.services.diagram_detector import DiagramDetector
    detector = DiagramDetector()
    
    for slide in manifest["slides"]:
        slide_id = slide["id"]
        image_path = lesson_path / "slides" / f"{slide_id:03d}.png"
        
        # Detect diagrams
        diagrams = detector.detect_diagrams(
            str(image_path),
            text_elements=slide.get('elements', [])
        )
        
        # Add diagrams to elements
        slide['elements'].extend(diagrams)
        
        # Update metadata
        slide['has_diagrams'] = len(diagrams) > 0
        slide['diagram_count'] = len(diagrams)
    
    self.save_manifest(lesson_dir, manifest)
```

---

##### Step 1.1.3: Adapt Semantic Analyzer (0.5 дня)

**Файл:** `backend/app/services/semantic_analyzer_gemini.py`

```python
def _create_analysis_prompt(self, slide_data: Dict[str, Any]) -> str:
    """Create prompt for semantic analysis"""
    
    # ... existing code ...
    
    # NEW: Add diagram information
    diagrams = [e for e in elements if e.get('type') == 'diagram']
    
    if diagrams:
        prompt += "\n\n**Диаграммы и изображения:**\n"
        for diag in diagrams:
            prompt += f"- {diag['diagram_type']}: {diag['description']}\n"
            prompt += f"  Сложность: {diag['visual_complexity']}\n"
            prompt += f"  Ключевые элементы: {', '.join(diag['key_elements'])}\n"
    
    # Update instructions
    prompt += """
    
При группировке элементов:
- Диаграммы должны быть в отдельной группе с type='diagram'
- Для диаграмм используйте highlight_strategy: 'diagram_walkthrough'
- Educational intent для диаграмм: 'Visual explanation of diagram'
"""
    
    return prompt
```

---

##### Step 1.1.4: Generate Diagram Explanation Segments (1 день)

**Файл:** `backend/app/services/smart_script_generator.py`

```python
def _generate_diagram_explanation(
    self,
    diagram_element: Dict,
    semantic_group: Dict,
    context: Dict
) -> List[Dict]:
    """Generate special talk_track segments for diagrams"""
    
    diagram_type = diagram_element.get('diagram_type')
    description = diagram_element.get('description')
    key_elements = diagram_element.get('key_elements', [])
    complexity = diagram_element.get('visual_complexity')
    
    # Create prompt for LLM
    prompt = f"""
Ты объясняешь {diagram_type} студентам уровня {context['level']}.

Диаграмма: {description}
Ключевые элементы: {', '.join(key_elements)}
Сложность: {complexity}

Создай объяснение диаграммы в 3 сегмента:

1. OVERVIEW (5-10 сек): Что показывает эта диаграмма в целом?
2. WALKTHROUGH (15-30 сек): Пройдись по ключевым элементам слева направо / сверху вниз
3. CONCLUSION (5-10 сек): Какой главный вывод из этой диаграммы?

Используй простой, разговорный язык. Избегай чтения подписей.
"""
    
    # Generate with LLM
    result = self.llm_worker.generate(prompt)
    
    # Parse into segments
    segments = [
        {
            "segment": "diagram_overview",
            "text": result['overview'],
            "group_id": semantic_group['id'],
            "diagram_id": diagram_element['id']
        },
        {
            "segment": "diagram_walkthrough",
            "text": result['walkthrough'],
            "group_id": semantic_group['id'],
            "diagram_id": diagram_element['id']
        },
        {
            "segment": "diagram_conclusion",
            "text": result['conclusion'],
            "group_id": semantic_group['id'],
            "diagram_id": diagram_element['id']
        }
    ]
    
    return segments
```

---

##### Step 1.1.5: Adapt Visual Cues for Diagrams (0.5 дня)

**Файл:** `backend/app/services/visual_effects_engine.py`

```python
def _generate_diagram_cues(
    self,
    diagram_element: Dict,
    talk_track: List[Dict],
    tts_words: Dict
) -> List[Dict]:
    """Generate special cues for diagrams"""
    
    # Find diagram walkthrough segment
    walkthrough_seg = next(
        (seg for seg in talk_track 
         if seg.get('segment') == 'diagram_walkthrough'),
        None
    )
    
    if not walkthrough_seg:
        return []
    
    # Strategy: Progressive reveal
    # Highlight different parts of diagram as speaker explains them
    
    bbox = diagram_element['bbox']
    key_elements = diagram_element.get('key_elements', [])
    
    cues = []
    
    # 1. Initial spotlight on whole diagram
    cues.append({
        "action": "spotlight",
        "bbox": bbox,
        "t0": walkthrough_seg['start'],
        "t1": walkthrough_seg['start'] + 2.0,
        "element_id": diagram_element['id'],
        "intensity": "medium"
    })
    
    # 2. Pan/zoom effect during walkthrough
    duration = walkthrough_seg['end'] - walkthrough_seg['start']
    
    # Divide diagram into zones (left, center, right or top, middle, bottom)
    zones = self._divide_diagram_into_zones(bbox, len(key_elements))
    
    time_per_zone = duration / len(zones)
    
    for i, zone in enumerate(zones):
        start = walkthrough_seg['start'] + 2.0 + (i * time_per_zone)
        end = start + time_per_zone
        
        cues.append({
            "action": "zoom_to_region",
            "bbox": zone,
            "t0": start,
            "t1": end,
            "element_id": diagram_element['id'],
            "zone_index": i
        })
    
    return cues

def _divide_diagram_into_zones(
    self, 
    bbox: List[int], 
    num_zones: int
) -> List[List[int]]:
    """Divide diagram bbox into zones for progressive reveal"""
    x, y, w, h = bbox
    
    zones = []
    zone_width = w // num_zones
    
    for i in range(num_zones):
        zone_x = x + (i * zone_width)
        zones.append([zone_x, y, zone_width, h])
    
    return zones
```

---

##### Testing Plan (0.5 дня)

```bash
# Test with presentations containing diagrams
pytest backend/tests/test_diagram_detector.py -v
pytest backend/tests/test_semantic_analyzer.py::test_diagram_grouping -v
pytest backend/tests/test_visual_effects.py::test_diagram_cues -v

# Integration test
python test_pipeline_detailed.py  # Use presentation with diagrams
```

---

**Deliverables:**
- [ ] `DiagramDetector` class implemented
- [ ] Integration into `extract_elements_ocr()`
- [ ] Semantic Analyzer adapted for diagrams
- [ ] Diagram explanation segments generator
- [ ] Special visual cues for diagrams
- [ ] Tests passing
- [ ] Documentation updated

---

### 🔥 1.2 Implement Highlight Strategy Effects

**Priority:** 🟠 HIGH  
**Impact:** MEDIUM (улучшает визуальное разнообразие)  
**Effort:** LOW (1-2 дня)  
**Dependencies:** None

#### Проблема
```
Semantic Map: spotlight, sequential_cascade, highlight
Reality: все "underline"
```

#### Решение
```
Реализовать разные визуальные эффекты:
- spotlight: затемнить фон, подсветить элемент
- sequential_cascade: последовательная подсветка элементов
- highlight: цветная рамка вокруг элемента
- underline: подчеркивание (текущее)
```

#### Реализация

##### Step 1.2.1: Define Effect Types (0.5 дня)

**Файл:** `backend/app/services/visual_effects_engine.py`

```python
# Add effect type mapping
EFFECT_TYPE_MAPPING = {
    "spotlight": "spotlight",  # Затемнить фон, подсветить элемент
    "sequential_cascade": "sequential_highlight",  # Последовательная подсветка
    "highlight": "highlight_box",  # Цветная рамка
    "none": "none",  # Нет эффекта
    # Fallback
    "underline": "underline"
}

def _map_effect_type(self, strategy_effect: str) -> str:
    """Map semantic strategy to cue action"""
    return EFFECT_TYPE_MAPPING.get(strategy_effect, "underline")
```

##### Step 1.2.2: Implement Effect Generators (1 день)

```python
def _generate_cues_for_group(
    self,
    group: Dict,
    talk_track: List[Dict],
    elements: List[Dict],
    tts_words: Dict
) -> List[Dict]:
    """Generate cues based on highlight_strategy"""
    
    strategy = group.get('highlight_strategy', {})
    effect_type = strategy.get('effect_type', 'underline')
    when = strategy.get('when', 'during_explanation')
    duration = strategy.get('duration', 3.0)
    
    # Map to cue action
    action = self._map_effect_type(effect_type)
    
    # Find relevant talk_track segments
    group_segments = [
        seg for seg in talk_track 
        if seg.get('group_id') == group['id']
    ]
    
    if not group_segments:
        return []
    
    # Generate cues based on effect type
    if action == "spotlight":
        return self._generate_spotlight_cues(
            group, group_segments, elements, duration
        )
    
    elif action == "sequential_highlight":
        return self._generate_sequential_cues(
            group, group_segments, elements, duration
        )
    
    elif action == "highlight_box":
        return self._generate_highlight_box_cues(
            group, group_segments, elements, duration
        )
    
    else:
        # Default: underline
        return self._generate_underline_cues(
            group, group_segments, elements, duration
        )

def _generate_spotlight_cues(
    self,
    group: Dict,
    segments: List[Dict],
    elements: List[Dict],
    duration: float
) -> List[Dict]:
    """Generate spotlight effect (darken background, highlight element)"""
    cues = []
    
    # Get elements in this group
    element_ids = group.get('element_ids', [])
    group_elements = [e for e in elements if e['id'] in element_ids]
    
    if not group_elements:
        return []
    
    # Calculate combined bbox
    combined_bbox = self._calculate_combined_bbox(group_elements)
    
    # Create spotlight cue
    start_time = segments[0]['start']
    
    cues.append({
        "action": "spotlight",
        "bbox": combined_bbox,
        "t0": start_time,
        "t1": start_time + duration,
        "group_id": group['id'],
        "element_ids": element_ids,
        "timing_source": "semantic_strategy",
        "intensity": "high"  # Darken background 70%
    })
    
    return cues

def _generate_sequential_cues(
    self,
    group: Dict,
    segments: List[Dict],
    elements: List[Dict],
    total_duration: float
) -> List[Dict]:
    """Generate sequential cascade (highlight elements one by one)"""
    cues = []
    
    # Get elements in reading order
    reading_order = group.get('reading_order', [])
    element_ids = group.get('element_ids', [])
    
    # Sort elements by reading order
    ordered_elements = []
    for idx in reading_order:
        elem_id = element_ids[idx - 1] if idx <= len(element_ids) else None
        if elem_id:
            elem = next((e for e in elements if e['id'] == elem_id), None)
            if elem:
                ordered_elements.append(elem)
    
    if not ordered_elements:
        return []
    
    # Calculate timing
    start_time = segments[0]['start']
    duration_per_element = total_duration / len(ordered_elements)
    
    # Generate cascading cues
    for i, elem in enumerate(ordered_elements):
        t0 = start_time + (i * duration_per_element)
        t1 = t0 + duration_per_element
        
        cues.append({
            "action": "highlight_cascade",
            "bbox": elem['bbox'],
            "t0": t0,
            "t1": t1,
            "group_id": group['id'],
            "element_id": elem['id'],
            "sequence_number": i,
            "total_in_sequence": len(ordered_elements),
            "timing_source": "semantic_strategy"
        })
    
    return cues

def _generate_highlight_box_cues(
    self,
    group: Dict,
    segments: List[Dict],
    elements: List[Dict],
    duration: float
) -> List[Dict]:
    """Generate highlight box (colored border around element)"""
    cues = []
    
    element_ids = group.get('element_ids', [])
    group_elements = [e for e in elements if e['id'] in element_ids]
    
    if not group_elements:
        return []
    
    # Calculate combined bbox
    combined_bbox = self._calculate_combined_bbox(group_elements)
    
    # Create highlight box cue
    start_time = segments[0]['start']
    
    cues.append({
        "action": "highlight_box",
        "bbox": combined_bbox,
        "t0": start_time,
        "t1": start_time + duration,
        "group_id": group['id'],
        "element_ids": element_ids,
        "timing_source": "semantic_strategy",
        "color": self._get_priority_color(group.get('priority', 'medium')),
        "border_width": 3
    })
    
    return cues

def _calculate_combined_bbox(self, elements: List[Dict]) -> List[int]:
    """Calculate bounding box that covers all elements"""
    if not elements:
        return [0, 0, 0, 0]
    
    min_x = min(e['bbox'][0] for e in elements)
    min_y = min(e['bbox'][1] for e in elements)
    max_x = max(e['bbox'][0] + e['bbox'][2] for e in elements)
    max_y = max(e['bbox'][1] + e['bbox'][3] for e in elements)
    
    return [min_x, min_y, max_x - min_x, max_y - min_y]

def _get_priority_color(self, priority: str) -> str:
    """Get color based on priority"""
    colors = {
        "high": "#FF6B6B",  # Red
        "medium": "#4ECDC4",  # Teal
        "low": "#95E1D3",  # Light green
        "none": "#F0F0F0"  # Gray
    }
    return colors.get(priority, "#4ECDC4")
```

---

##### Step 1.2.3: Update Frontend (if needed) (0.5 дня)

**Файл:** `src/components/LecturePlayer.tsx` (или аналогичный)

```typescript
// Add support for new cue actions

interface Cue {
  action: 'spotlight' | 'sequential_highlight' | 'highlight_box' | 'underline';
  bbox: [number, number, number, number];
  t0: number;
  t1: number;
  intensity?: string;
  color?: string;
  // ...
}

function applyCueEffect(cue: Cue, slideElement: HTMLElement) {
  switch (cue.action) {
    case 'spotlight':
      applySpotlightEffect(cue, slideElement);
      break;
    
    case 'highlight_cascade':
    case 'sequential_highlight':
      applySequentialHighlight(cue, slideElement);
      break;
    
    case 'highlight_box':
      applyHighlightBox(cue, slideElement);
      break;
    
    case 'underline':
    default:
      applyUnderlineEffect(cue, slideElement);
  }
}

function applySpotlightEffect(cue: Cue, slideElement: HTMLElement) {
  // Create dark overlay
  const overlay = document.createElement('div');
  overlay.style.position = 'absolute';
  overlay.style.top = '0';
  overlay.style.left = '0';
  overlay.style.width = '100%';
  overlay.style.height = '100%';
  overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';  // 70% dark
  overlay.style.pointerEvents = 'none';
  
  // Create spotlight hole (SVG mask or clip-path)
  const [x, y, w, h] = cue.bbox;
  overlay.style.clipPath = `polygon(
    0% 0%, 100% 0%, 100% 100%, 0% 100%,
    ${x}px ${y}px, ${x+w}px ${y}px, ${x+w}px ${y+h}px, ${x}px ${y+h}px
  )`;
  
  slideElement.appendChild(overlay);
  
  // Animate in
  overlay.animate([
    { opacity: 0 },
    { opacity: 1 }
  ], {
    duration: 300,
    fill: 'forwards'
  });
  
  // Remove after duration
  setTimeout(() => {
    overlay.animate([
      { opacity: 1 },
      { opacity: 0 }
    ], {
      duration: 300,
      fill: 'forwards'
    }).onfinish = () => overlay.remove();
  }, (cue.t1 - cue.t0) * 1000);
}

// Similar for other effects...
```

---

**Testing:**
```bash
# Test different effect types
pytest backend/tests/test_visual_effects.py::test_spotlight_effect -v
pytest backend/tests/test_visual_effects.py::test_sequential_cascade -v
pytest backend/tests/test_visual_effects.py::test_highlight_box -v

# Visual test in browser
npm run dev  # Start frontend
# Upload presentation and check effects
```

---

**Deliverables:**
- [ ] Effect type mapping implemented
- [ ] Spotlight effect generator
- [ ] Sequential cascade generator
- [ ] Highlight box generator
- [ ] Frontend support (if needed)
- [ ] Tests passing
- [ ] Documentation

---

### 🔥 1.3 Priority-Based Time Distribution

**Priority:** 🟠 HIGH  
**Impact:** MEDIUM (улучшает фокус на важном)  
**Effort:** LOW (1 день)  
**Dependencies:** None

#### Проблема
```
High priority groups не получают больше времени, чем medium
```

#### Решение
```
Распределение времени по priority:
- high: 60%
- medium: 30%
- low: 10%
- none: 0% (watermark)
```

#### Реализация

##### Step 1.3.1: Calculate Priority-Based Duration (0.5 дня)

**Файл:** `backend/app/services/smart_script_generator.py`

```python
def _calculate_group_durations(
    self,
    semantic_groups: List[Dict],
    total_duration: float
) -> Dict[str, float]:
    """
    Calculate duration for each group based on priority
    
    Priority distribution:
    - high: 60%
    - medium: 30%
    - low: 10%
    - none: 0%
    """
    # Count groups by priority
    priority_counts = {
        'high': 0,
        'medium': 0,
        'low': 0,
        'none': 0
    }
    
    for group in semantic_groups:
        priority = group.get('priority', 'medium')
        priority_counts[priority] += 1
    
    # Calculate total weights
    total_weight = (
        priority_counts['high'] * 0.60 +
        priority_counts['medium'] * 0.30 +
        priority_counts['low'] * 0.10 +
        priority_counts['none'] * 0.00
    )
    
    # Calculate duration per group
    group_durations = {}
    
    for group in semantic_groups:
        priority = group.get('priority', 'medium')
        group_id = group['id']
        
        if priority == 'high':
            weight = 0.60
        elif priority == 'medium':
            weight = 0.30
        elif priority == 'low':
            weight = 0.10
        else:  # none
            weight = 0.00
        
        # Duration for this group
        if total_weight > 0:
            duration = (weight / total_weight) * total_duration
        else:
            duration = 0.0
        
        group_durations[group_id] = duration
    
    return group_durations

def generate_script(
    self,
    semantic_map: Dict,
    elements: List[Dict],
    context: Dict
) -> Dict[str, Any]:
    """Generate talk track script with priority-based timing"""
    
    groups = semantic_map.get('groups', [])
    
    # Calculate optimal total duration
    total_duration = self._calculate_optimal_duration(semantic_map, context)
    
    # Calculate duration per group based on priority
    group_durations = self._calculate_group_durations(groups, total_duration)
    
    # Generate segments for each group
    talk_track = []
    
    for group in groups:
        group_id = group['id']
        target_duration = group_durations.get(group_id, 0.0)
        
        if target_duration > 0:
            segments = self._generate_group_segments(
                group,
                elements,
                context,
                target_duration=target_duration  # ← Pass target duration
            )
            talk_track.extend(segments)
    
    return {
        'talk_track_raw': talk_track,
        'estimated_duration': total_duration,
        'group_durations': group_durations
    }

def _generate_group_segments(
    self,
    group: Dict,
    elements: List[Dict],
    context: Dict,
    target_duration: float  # ← NEW parameter
) -> List[Dict]:
    """Generate segments for a group with target duration"""
    
    # Create prompt with duration constraint
    prompt = f"""
Generate explanation for this group.

Group: {group['name']}
Priority: {group['priority']}
Educational intent: {group['educational_intent']}

TARGET DURATION: {target_duration:.0f} seconds
- Generate content that takes approximately {target_duration:.0f} seconds to read
- Word count target: {int(target_duration * 2.5)} words (assuming 150 WPM)

{'High priority - provide detailed explanation with examples' if group['priority'] == 'high' else ''}
{'Medium priority - provide concise explanation' if group['priority'] == 'medium' else ''}
{'Low priority - provide brief mention' if group['priority'] == 'low' else ''}

Elements: ...
"""
    
    # Generate with LLM
    result = self.llm_worker.generate(prompt)
    
    # Parse into segments
    segments = self._parse_into_segments(result, group)
    
    return segments
```

---

**Testing:**
```python
# backend/tests/test_smart_script_generator.py

def test_priority_based_duration():
    """Test that high priority groups get more time"""
    
    semantic_groups = [
        {"id": "group_1", "priority": "high", "name": "Main Concept"},
        {"id": "group_2", "priority": "medium", "name": "Supporting Detail"},
        {"id": "group_3", "priority": "low", "name": "Side Note"}
    ]
    
    generator = SmartScriptGenerator(...)
    durations = generator._calculate_group_durations(semantic_groups, 100.0)
    
    # Verify distribution
    assert durations["group_1"] > durations["group_2"]  # high > medium
    assert durations["group_2"] > durations["group_3"]  # medium > low
    
    # Verify total
    total = sum(durations.values())
    assert abs(total - 100.0) < 0.1  # Allow small rounding error
    
    # Verify approximate ratios
    high_percent = durations["group_1"] / total
    assert 0.55 < high_percent < 0.65  # ~60%
```

---

**Deliverables:**
- [ ] Priority-based duration calculator
- [ ] Integration into script generator
- [ ] LLM prompts updated with duration targets
- [ ] Tests passing
- [ ] Documentation

---

## 📋 Phase 2: IMPORTANT Improvements (Week 2-3)

### 🟡 2.1 Visual Hierarchy Detection

**Priority:** 🟡 MEDIUM  
**Impact:** MEDIUM  
**Effort:** MEDIUM (2 дня)  
**Dependencies:** None

#### Implementation

```python
# backend/app/services/visual_hierarchy_detector.py

class VisualHierarchyDetector:
    """Detect visual hierarchy: main_title, subtitles, body_text"""
    
    def detect_hierarchy(self, elements: List[Dict]) -> Dict[str, List[str]]:
        """
        Classify elements into hierarchy levels
        
        Returns:
            {
                "main_title": ["element_id"],
                "subtitles": ["element_id", ...],
                "body_text": ["element_id", ...],
                "captions": ["element_id", ...],
                "labels": ["element_id", ...]
            }
        """
        hierarchy = {
            "main_title": [],
            "subtitles": [],
            "body_text": [],
            "captions": [],
            "labels": []
        }
        
        # Sort by font size (if available) or bbox area
        sorted_elements = sorted(
            elements,
            key=lambda e: self._estimate_font_size(e),
            reverse=True
        )
        
        # Classify based on size, position, type
        for elem in sorted_elements:
            category = self._classify_element(elem, sorted_elements)
            hierarchy[category].append(elem['id'])
        
        return hierarchy
    
    def _estimate_font_size(self, element: Dict) -> float:
        """Estimate font size from bbox height"""
        bbox = element.get('bbox', [0, 0, 0, 0])
        return bbox[3]  # height
    
    def _classify_element(self, elem: Dict, all_elements: List[Dict]) -> str:
        """Classify element into hierarchy level"""
        
        elem_type = elem.get('type', 'paragraph')
        bbox = elem.get('bbox', [0, 0, 0, 0])
        text = elem.get('text', '')
        
        # Main title: largest text, top of slide, heading type
        if (elem_type == 'heading' and 
            bbox[1] < 200 and  # Top of slide
            len(text) < 100):  # Not too long
            return 'main_title'
        
        # Subtitle: medium size, after title
        elif (elem_type in ['heading', 'paragraph'] and
              200 < bbox[1] < 400 and
              len(text) < 80):
            return 'subtitles'
        
        # Caption: small text near images
        elif (bbox[3] < 30 and  # Small height
              len(text) < 50):
            return 'captions'
        
        # Label: very small, single word
        elif (bbox[3] < 25 and
              len(text.split()) <= 3):
            return 'labels'
        
        # Body text: everything else
        else:
            return 'body_text'
```

**Integration:**
```python
# In extract_elements_ocr()
from app.services.visual_hierarchy_detector import VisualHierarchyDetector

detector = VisualHierarchyDetector()
hierarchy = detector.detect_hierarchy(slide['elements'])
slide['visual_hierarchy'] = hierarchy
```

---

### 🟡 2.2 Element Relationships Detection

**Priority:** 🟡 MEDIUM  
**Impact:** LOW-MEDIUM  
**Effort:** HIGH (3 дня)  
**Dependencies:** Diagram Recognition

**Status:** DEFER to Phase 3 or later (low ROI for effort)

---

### 🟡 2.3 Fix Sequential Cascade Overlapping

**Priority:** 🟡 MEDIUM  
**Impact:** LOW (уже auto-fixed, но можно улучшить)  
**Effort:** LOW (0.5 дня)  

#### Implementation

```python
# In visual_effects_engine.py

def _prevent_cue_overlaps(self, cues: List[Dict]) -> List[Dict]:
    """Prevent cue overlaps using reading_order"""
    
    # Sort by t0
    sorted_cues = sorted(cues, key=lambda c: c['t0'])
    
    # Adjust overlapping cues
    for i in range(len(sorted_cues) - 1):
        current = sorted_cues[i]
        next_cue = sorted_cues[i + 1]
        
        if current['t1'] > next_cue['t0']:
            # Overlap detected
            # Option 1: Shorten current cue
            current['t1'] = next_cue['t0'] - 0.1
            
            # Option 2: Delay next cue
            # next_cue['t0'] = current['t1'] + 0.1
    
    return sorted_cues
```

---

## 📋 Phase 3: NICE-TO-HAVE (Week 3-4)

### 🟢 3.1 Assessment Segments

**Priority:** 🟢 LOW  
**Impact:** LOW-MEDIUM  
**Effort:** MEDIUM (2 дня)  

```python
# backend/app/services/assessment_generator.py

class AssessmentGenerator:
    """Generate quiz questions and check understanding segments"""
    
    def generate_quiz_for_slide(
        self,
        semantic_map: Dict,
        talk_track: List[Dict],
        context: Dict
    ) -> Dict:
        """Generate quiz question after slide"""
        
        # Extract key concepts
        key_concepts = self._extract_key_concepts(semantic_map, talk_track)
        
        # Generate question with LLM
        prompt = f"""
Create a quiz question to check understanding of:
{', '.join(key_concepts)}

Level: {context['level']}
Type: multiple choice (4 options, 1 correct)

Format:
Question: ...
A) ...
B) ...
C) ...
D) ...
Correct: A
Explanation: ...
"""
        
        result = self.llm_worker.generate(prompt)
        
        return {
            "type": "quiz",
            "position": "after_slide",
            "question": result['question'],
            "options": result['options'],
            "correct_answer": result['correct'],
            "explanation": result['explanation']
        }
```

---

### 🟢 3.2 Quality Metrics

**Priority:** 🟢 LOW  
**Impact:** LOW (полезно для monitoring, не критично)  
**Effort:** MEDIUM (2 дня)  

```python
# backend/app/services/quality_analyzer.py

class QualityAnalyzer:
    """Analyze lecture quality and provide metrics"""
    
    def analyze_lecture_quality(self, manifest: Dict) -> Dict:
        """Generate quality metrics"""
        
        metrics = {
            "information_density": self._calculate_info_density(manifest),
            "pacing_score": self._calculate_pacing_score(manifest),
            "visual_text_balance": self._calculate_balance(manifest),
            "engagement_score": self._calculate_engagement(manifest),
            "accessibility_score": self._calculate_accessibility(manifest)
        }
        
        return metrics
```

---

### 🟢 3.3 Pedagogical Metadata

**Priority:** 🟢 LOW  
**Impact:** LOW  
**Effort:** LOW (1 день)  

```python
# Add to presentation_context

{
  "pedagogical_metadata": {
    "bloom_taxonomy_level": "comprehension",
    "learning_objectives": [...],
    "difficulty_level": 3,
    "student_engagement_strategy": "problem_based"
  }
}
```

---

## 📊 Implementation Timeline

```
Week 1:
├─ Mon-Tue: Diagram Recognition (Step 1.1.1 - 1.1.3)
├─ Wed-Thu: Diagram Explanation & Cues (Step 1.1.4 - 1.1.5)
└─ Fri: Testing & Bug Fixes

Week 2:
├─ Mon-Tue: Highlight Strategy Effects (Step 1.2)
├─ Wed: Priority-Based Timing (Step 1.3)
├─ Thu: Visual Hierarchy (Step 2.1)
└─ Fri: Testing & Integration

Week 3:
├─ Mon-Tue: Sequential Cascade Fix (Step 2.3)
├─ Wed-Thu: Assessment Segments (Step 3.1)
└─ Fri: Quality Metrics (Step 3.2)

Week 4:
├─ Mon: Pedagogical Metadata (Step 3.3)
├─ Tue-Wed: Full Integration Testing
├─ Thu: Performance Optimization
└─ Fri: Documentation & Deployment
```

---

## ✅ Success Metrics

### Target Quality Score: 95%+

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Полнота данных | 85% | 95% | All fields populated |
| Интеллектуальное использование | 75% | 90% | Priority adherence, effect mapping |
| Педагогическое качество | 80% | 95% | Assessment presence, variety |
| Техническая синхронизация | 95% | 98% | Zero overlaps, perfect timing |

---

## 🧪 Testing Strategy

### Unit Tests
```bash
pytest backend/tests/test_diagram_detector.py -v
pytest backend/tests/test_visual_effects.py -v
pytest backend/tests/test_smart_script_generator.py -v
```

### Integration Tests
```bash
python test_pipeline_detailed.py  # Full pipeline test
```

### Manual QA
- [ ] Upload presentation with diagrams
- [ ] Verify diagram detection and explanation
- [ ] Check highlight effects (spotlight, cascade, box)
- [ ] Verify priority-based timing
- [ ] Check visual hierarchy detection
- [ ] Test assessment questions

---

## 📝 Documentation Updates

- [ ] Update `PIPELINE_STAGES.md` with new stages
- [ ] Update `API.md` with new manifest fields
- [ ] Create `DIAGRAM_PROCESSING.md` guide
- [ ] Update `CONTRIBUTING.md` with development guidelines

---

## 🚀 Deployment Plan

### Staging Deployment (Week 3)
```bash
# Deploy to staging
git checkout staging
git merge production-deploy
docker-compose up --build -d

# Run smoke tests
./scripts/smoke_test.sh

# Monitor metrics
./scripts/monitor_quality.sh
```

### Production Deployment (Week 4)
```bash
# Feature flag rollout
ENABLE_DIAGRAM_DETECTION=true
ENABLE_NEW_EFFECTS=true

# Gradual rollout: 10% → 50% → 100%
./scripts/feature_flag.sh diagram_detection 0.1
# Monitor for 24h
./scripts/feature_flag.sh diagram_detection 0.5
# Monitor for 24h
./scripts/feature_flag.sh diagram_detection 1.0
```

---

## 📊 Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Diagram detection false positives | Medium | Medium | Confidence threshold, manual review mode |
| LLM generates poor diagram explanations | Medium | High | Prompt engineering, fallback templates |
| New effects break frontend | Low | High | Comprehensive frontend tests, gradual rollout |
| Performance degradation | Low | Medium | Benchmarking, optimization, caching |

---

## 💰 Resource Requirements

**Development:**
- 1 Backend Engineer (3-4 weeks full-time)
- 0.5 Frontend Engineer (1 week)
- 0.25 QA Engineer (testing support)

**Infrastructure:**
- Vision API quota increase (+50%)
- LLM API quota increase (+30%)
- Storage for diagram metadata

**Budget Estimate:**
- Development: 3-4 weeks × $2000/week = $6,000-$8,000
- API costs increase: +$200/month
- **Total: ~$8,000 one-time + $200/month**

---

## 🎉 Expected Outcomes

### Quantitative
- ✅ Quality score: 82% → 95% (+13%)
- ✅ Diagram coverage: 0% → 90%
- ✅ Visual variety: 1 effect → 4 effects
- ✅ Priority adherence: 50% → 95%

### Qualitative
- ✅ Лекции становятся более полными (диаграммы объясняются)
- ✅ Визуальное разнообразие увеличивается
- ✅ Фокус на важном контенте улучшается
- ✅ Студенты лучше понимают материал

---

_План составлен: 1 ноября 2025_  
_Ready for implementation 🚀_
