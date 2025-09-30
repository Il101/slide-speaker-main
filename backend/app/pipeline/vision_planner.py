"""Vision planner for multimodal LLM processing"""

import json
import logging
import hashlib
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Vision prompt template
VISION_PROMPT = """
You are an expert presentation analyst. Analyze this slide image and generate a structured response.

CRITICAL RULES:
1. DO NOT READ the slide text verbatim - explain and discuss the content instead
2. Avoid quoting more than 10-15 words from the slide
3. Structure your response as: Hook → Core → Example → Contrast → Takeaway + 1 question
4. Generate 45-90 seconds of engaging lecture content
5. Return STRICT JSON format only

Slide Context:
- Course: {course_title}
- Lecture: {lecture_title}
- Previous slide summary: {prev_summary}

Return JSON with this exact structure:
{{
  "lecture_text": "Engaging 45-90 second explanation that teaches rather than reads...",
  "rough_elements": [
    {{"id": "t1", "kind": "title|key_point|figure|table", "bbox": [x, y, w, h]}},
    {{"id": "t2", "kind": "key_point", "bbox": [x, y, w, h]}}
  ],
  "rough_cues": [
    {{"t0": 0.0, "t1": 3.0, "action": "highlight", "targetId": "t1"}},
    {{"t0": 3.0, "t1": 3.4, "action": "laser_move", "targetId": "t1"}}
  ]
}

Guidelines:
- bbox coordinates are in original slide size: {orig_size}
- If unsure about elements, create one placeholder: {{"id": "slide_area", "kind": "placeholder", "bbox": [0, 0, w, h]}}
- Actions: highlight, underline, laser_move, slide_change
- Avoid center-screen effects unless necessary
- Focus on teaching, not reading
"""

def vision_plan_for_slide(
    slide_png_path: str,
    orig_size: dict,
    course_title: str,
    lecture_title: str,
    prev_summary: Optional[str],
    provider: str,
    model: str,
) -> dict:
    """
    Generate vision-based lecture plan for a slide
    
    Args:
        slide_png_path: Path to slide PNG image
        orig_size: Original slide dimensions {"w": 1600, "h": 900}
        course_title: Course title for context
        lecture_title: Lecture title for context
        prev_summary: Previous slide summary for context
        provider: LLM provider (openrouter|gemini)
        model: Model name (e.g., gpt-4o-mini, gemini-1.5-flash)
    
    Returns:
        Dict with lecture_text, rough_elements, rough_cues
    """
    logger.info(f"Vision planning for slide: {slide_png_path}")
    
    # Check cache first
    cache_key = _get_cache_key(slide_png_path, orig_size, course_title, lecture_title, prev_summary)
    cached_result = _load_from_cache(cache_key)
    if cached_result:
        logger.info(f"Using cached vision result for {slide_png_path}")
        return cached_result
    
    try:
        # Encode image to base64
        with open(slide_png_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Prepare prompt
        prompt = VISION_PROMPT.format(
            course_title=course_title,
            lecture_title=lecture_title,
            prev_summary=prev_summary or "First slide",
            orig_size=f"{orig_size['w']}x{orig_size['h']}"
        )
        
        # Call appropriate provider
        if provider == "openrouter":
            result = _call_openrouter_vision(prompt, image_data, model)
        elif provider == "gemini":
            result = _call_gemini_vision(prompt, image_data, model)
        else:
            raise ValueError(f"Unsupported vision provider: {provider}")
        
        # Validate and clean result
        validated_result = _validate_vision_result(result, orig_size)
        
        # Cache result
        _save_to_cache(cache_key, validated_result)
        
        logger.info(f"Vision planning completed for {slide_png_path}")
        return validated_result
        
    except Exception as e:
        logger.error(f"Vision planning failed for {slide_png_path}: {e}")
        # Return fallback result
        return {
            "lecture_text": "Let's discuss the content of this slide.",
            "rough_elements": [{
                "id": "slide_area",
                "kind": "placeholder",
                "bbox": [0, 0, orig_size["w"], orig_size["h"]]
            }],
            "rough_cues": []
        }

def _get_cache_key(slide_png_path: str, orig_size: dict, course_title: str, lecture_title: str, prev_summary: Optional[str]) -> str:
    """Generate cache key for vision result"""
    content = f"{slide_png_path}:{orig_size}:{course_title}:{lecture_title}:{prev_summary}"
    return hashlib.sha256(content.encode()).hexdigest()

def _load_from_cache(cache_key: str) -> Optional[dict]:
    """Load vision result from cache"""
    cache_dir = Path(".data/vision_cache")
    cache_dir.mkdir(exist_ok=True)
    
    cache_file = cache_dir / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    
    return None

def _save_to_cache(cache_key: str, result: dict) -> None:
    """Save vision result to cache"""
    cache_dir = Path(".data/vision_cache")
    cache_dir.mkdir(exist_ok=True)
    
    cache_file = cache_dir / f"{cache_key}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")

def _call_openrouter_vision(prompt: str, image_data: str, model: str) -> dict:
    """Call OpenRouter vision API"""
    import requests
    import os
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.2
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # Parse JSON from response
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            raise ValueError(f"Could not parse JSON from response: {content}")

def _call_gemini_vision(prompt: str, image_data: str, model: str) -> dict:
    """Call Gemini vision API"""
    try:
        import google.generativeai as genai
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        import os
        
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        model_instance = genai.GenerativeModel(model)
        
        # Prepare content
        content = [prompt, {
            "mime_type": "image/png",
            "data": image_data
        }]
        
        # Generate response
        response = model_instance.generate_content(
            content,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Parse JSON from response
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from response: {response.text}")
                
    except ImportError:
        raise ImportError("google-generativeai package not installed")
    except Exception as e:
        raise Exception(f"Gemini API error: {e}")

def _validate_vision_result(result: dict, orig_size: dict) -> dict:
    """Validate and clean vision result"""
    # Ensure required fields
    if "lecture_text" not in result:
        result["lecture_text"] = "Let's discuss the content of this slide."
    
    if "rough_elements" not in result:
        result["rough_elements"] = []
    
    if "rough_cues" not in result:
        result["rough_cues"] = []
    
    # Validate elements
    validated_elements = []
    for element in result["rough_elements"]:
        if not isinstance(element, dict):
            continue
        
        # Ensure required fields
        if "id" not in element:
            element["id"] = f"elem_{len(validated_elements)}"
        
        if "kind" not in element:
            element["kind"] = "placeholder"
        
        if "bbox" not in element:
            element["bbox"] = [0, 0, orig_size["w"], orig_size["h"]]
        
        # Validate bbox
        bbox = element["bbox"]
        if len(bbox) != 4:
            element["bbox"] = [0, 0, orig_size["w"], orig_size["h"]]
        else:
            # Ensure bbox is within slide bounds
            x, y, w, h = bbox
            x = max(0, min(x, orig_size["w"]))
            y = max(0, min(y, orig_size["h"]))
            w = max(10, min(w, orig_size["w"] - x))
            h = max(10, min(h, orig_size["h"] - y))
            element["bbox"] = [x, y, w, h]
        
        validated_elements.append(element)
    
    result["rough_elements"] = validated_elements
    
    # Validate cues
    validated_cues = []
    for cue in result["rough_cues"]:
        if not isinstance(cue, dict):
            continue
        
        # Ensure required fields
        if "t0" not in cue:
            cue["t0"] = 0.0
        if "t1" not in cue:
            cue["t1"] = 3.0
        if "action" not in cue:
            cue["action"] = "highlight"
        
        # Validate timing
        if cue["t0"] >= cue["t1"]:
            cue["t1"] = cue["t0"] + 1.0
        
        # Validate targetId exists in elements
        if "targetId" in cue:
            target_id = cue["targetId"]
            if not any(elem["id"] == target_id for elem in validated_elements):
                # Map to slide_area if target not found
                cue["targetId"] = "slide_area"
        
        validated_cues.append(cue)
    
    result["rough_cues"] = validated_cues
    
    return result