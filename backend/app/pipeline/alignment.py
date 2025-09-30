"""Alignment module for matching rough vision elements to precise OCR elements"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import math

logger = logging.getLogger(__name__)

# Alignment parameters
ALIGN_IOU_THRESHOLD = 0.3
ALIGN_CENTER_THRESHOLD = 0.5
ALIGN_WEIGHTS = {
    "iou": 0.4,
    "center": 0.3,
    "kind": 0.3
}

def iou(bbox_a: List[float], bbox_b: List[float]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes
    
    Args:
        bbox_a: [x1, y1, x2, y2] or [x, y, w, h]
        bbox_b: [x1, y1, x2, y2] or [x, y, w, h]
    
    Returns:
        IoU value between 0 and 1
    """
    # Convert to [x1, y1, x2, y2] format if needed
    if len(bbox_a) == 4 and len(bbox_b) == 4:
        # Assume [x, y, w, h] format
        x1_a, y1_a, w_a, h_a = bbox_a
        x2_a, y2_a = x1_a + w_a, y1_a + h_a
        
        x1_b, y1_b, w_b, h_b = bbox_b
        x2_b, y2_b = x1_b + w_b, y1_b + h_b
    else:
        raise ValueError("Bounding boxes must have 4 coordinates")
    
    # Calculate intersection
    x1_i = max(x1_a, x1_b)
    y1_i = max(y1_a, y1_b)
    x2_i = min(x2_a, x2_b)
    y2_i = min(y2_a, y2_b)
    
    if x2_i <= x1_i or y2_i <= y1_i:
        return 0.0
    
    intersection = (x2_i - x1_i) * (y2_i - y1_i)
    
    # Calculate union
    area_a = w_a * h_a
    area_b = w_b * h_b
    union = area_a + area_b - intersection
    
    if union <= 0:
        return 0.0
    
    return intersection / union

def center_distance(bbox_a: List[float], bbox_b: List[float]) -> float:
    """
    Calculate normalized center distance between two bounding boxes
    
    Args:
        bbox_a: [x, y, w, h]
        bbox_b: [x, y, w, h]
    
    Returns:
        Normalized distance between 0 and 1
    """
    if len(bbox_a) != 4 or len(bbox_b) != 4:
        raise ValueError("Bounding boxes must have 4 coordinates")
    
    # Calculate centers
    center_a = (bbox_a[0] + bbox_a[2] / 2, bbox_a[1] + bbox_a[3] / 2)
    center_b = (bbox_b[0] + bbox_b[2] / 2, bbox_b[1] + bbox_b[3] / 2)
    
    # Calculate distance
    distance = math.sqrt((center_a[0] - center_b[0])**2 + (center_a[1] - center_b[1])**2)
    
    # Normalize by diagonal of slide (assume 1600x900)
    max_distance = math.sqrt(1600**2 + 900**2)
    
    return min(distance / max_distance, 1.0)

def kind_match_score(kind_a: str, kind_b: str) -> float:
    """
    Calculate kind matching score between element types
    
    Args:
        kind_a: Element kind from vision
        kind_b: Element kind from OCR
    
    Returns:
        Match score between 0 and 1
    """
    # Exact match
    if kind_a == kind_b:
        return 1.0
    
    # Semantic matches
    semantic_matches = {
        ("title", "heading"): 0.9,
        ("title", "text"): 0.7,
        ("key_point", "text"): 0.8,
        ("key_point", "list_item"): 0.9,
        ("figure", "image"): 0.9,
        ("table", "table"): 1.0,
        ("placeholder", "text"): 0.3,
        ("placeholder", "heading"): 0.3,
    }
    
    # Check both directions
    key = (kind_a, kind_b)
    if key in semantic_matches:
        return semantic_matches[key]
    
    key = (kind_b, kind_a)
    if key in semantic_matches:
        return semantic_matches[key]
    
    # Default: low score for different kinds
    return 0.1

def calculate_alignment_score(
    rough_element: Dict[str, Any],
    precise_element: Dict[str, Any],
    weights: Dict[str, float] = None
) -> float:
    """
    Calculate alignment score between rough and precise elements
    
    Args:
        rough_element: Element from vision with rough bbox
        precise_element: Element from OCR with precise bbox
        weights: Weights for different scoring components
    
    Returns:
        Alignment score between 0 and 1
    """
    if weights is None:
        weights = ALIGN_WEIGHTS
    
    try:
        # Get bounding boxes
        rough_bbox = rough_element.get("bbox", [0, 0, 100, 100])
        precise_bbox = precise_element.get("bbox", [0, 0, 100, 100])
        
        # Calculate component scores
        iou_score = iou(rough_bbox, precise_bbox)
        center_score = 1.0 - center_distance(rough_bbox, precise_bbox)
        kind_score = kind_match_score(
            rough_element.get("kind", "placeholder"),
            precise_element.get("type", "text")
        )
        
        # Weighted combination
        total_score = (
            weights["iou"] * iou_score +
            weights["center"] * center_score +
            weights["kind"] * kind_score
        )
        
        return total_score
        
    except Exception as e:
        logger.warning(f"Error calculating alignment score: {e}")
        return 0.0

def best_match(
    rough_element: Dict[str, Any],
    precise_elements: List[Dict[str, Any]],
    params: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    Find best matching precise element for a rough element
    
    Args:
        rough_element: Element from vision
        precise_elements: List of elements from OCR
        params: Alignment parameters
    
    Returns:
        Best matching precise element or None
    """
    if params is None:
        params = {
            "iou_threshold": ALIGN_IOU_THRESHOLD,
            "center_threshold": ALIGN_CENTER_THRESHOLD,
            "min_score": 0.3
        }
    
    best_element = None
    best_score = 0.0
    
    for precise_element in precise_elements:
        score = calculate_alignment_score(rough_element, precise_element)
        
        if score > best_score and score >= params["min_score"]:
            best_score = score
            best_element = precise_element
    
    # Additional threshold checks
    if best_element:
        rough_bbox = rough_element.get("bbox", [0, 0, 100, 100])
        precise_bbox = best_element.get("bbox", [0, 0, 100, 100])
        
        iou_score = iou(rough_bbox, precise_bbox)
        center_score = 1.0 - center_distance(rough_bbox, precise_bbox)
        
        # Must meet minimum thresholds
        if iou_score < params["iou_threshold"] and center_score < params["center_threshold"]:
            return None
    
    return best_element

def align_cues(
    rough_cues: List[Dict[str, Any]],
    mapping: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Align rough cues to precise elements using mapping
    
    Args:
        rough_cues: Cues from vision with rough targetId
        mapping: Mapping from rough element IDs to precise element IDs
    
    Returns:
        Aligned cues with precise targetId
    """
    aligned_cues = []
    
    for cue in rough_cues:
        aligned_cue = cue.copy()
        
        # Map targetId if available
        if "targetId" in cue:
            rough_id = cue["targetId"]
            precise_id = mapping.get(rough_id)
            
            if precise_id:
                aligned_cue["targetId"] = precise_id
                aligned_cue["element_id"] = precise_id  # Also set element_id for compatibility
            else:
                # Fallback: use slide_area placeholder
                aligned_cue["targetId"] = "slide_area"
                aligned_cue["element_id"] = "slide_area"
        
        aligned_cues.append(aligned_cue)
    
    return aligned_cues

def align_slide_elements(
    rough_elements: List[Dict[str, Any]],
    precise_elements: List[Dict[str, Any]],
    params: Dict[str, Any] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Align rough elements to precise elements for a slide
    
    Args:
        rough_elements: Elements from vision
        precise_elements: Elements from OCR
        params: Alignment parameters
    
    Returns:
        Tuple of (aligned_elements, mapping)
    """
    if params is None:
        params = {
            "iou_threshold": ALIGN_IOU_THRESHOLD,
            "center_threshold": ALIGN_CENTER_THRESHOLD,
            "min_score": 0.3
        }
    
    aligned_elements = []
    mapping = {}
    used_precise_ids = set()
    
    # Process each rough element
    for rough_element in rough_elements:
        rough_id = rough_element.get("id", f"rough_{len(aligned_elements)}")
        
        # Find best match
        best_match_element = best_match(rough_element, precise_elements, params)
        
        if best_match_element and best_match_element["id"] not in used_precise_ids:
            # Use precise element
            aligned_elements.append(best_match_element)
            mapping[rough_id] = best_match_element["id"]
            used_precise_ids.add(best_match_element["id"])
            
            logger.debug(f"Mapped rough element {rough_id} to precise element {best_match_element['id']}")
        else:
            # Create placeholder element
            placeholder_element = {
                "id": f"slide_area_{len(aligned_elements)}",
                "type": "placeholder",
                "bbox": rough_element.get("bbox", [0, 0, 1600, 900]),
                "text": "Slide area",
                "confidence": 0.5
            }
            aligned_elements.append(placeholder_element)
            mapping[rough_id] = placeholder_element["id"]
            
            logger.debug(f"Created placeholder for rough element {rough_id}")
    
    # Add unused precise elements
    for precise_element in precise_elements:
        if precise_element["id"] not in used_precise_ids:
            aligned_elements.append(precise_element)
    
    return aligned_elements, mapping