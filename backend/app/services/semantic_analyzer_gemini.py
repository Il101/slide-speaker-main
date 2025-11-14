"""
Optimized Semantic Analyzer using Google AI Studio Gemini
Cost: ~$0.01 per 30 slides (vs $1.50 with GPT-4o-mini)
Savings: 99.3%
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import os
import re

logger = logging.getLogger(__name__)

class SemanticAnalyzer:
    """Semantic analysis using Google Gemini 2.0 Flash"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.use_mock = not self.api_key
        
        if not self.use_mock:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.genai = genai
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("✅ Gemini 2.0 Flash configured")
            except Exception as e:
                logger.warning(f"Gemini setup failed: {e}, using mock mode")
                self.use_mock = True
    
    async def analyze_slide(
        self,
        slide_image_path: str,
        ocr_elements: List[Dict[str, Any]],
        presentation_context: Dict[str, Any],
        previous_slides: List[Dict[str, Any]] = None,
        slide_index: int = 0
    ) -> Dict[str, Any]:
        """
        Analyze slide with Gemini vision model
        
        Args:
            slide_image_path: Path to slide image
            ocr_elements: OCR data with text + coordinates
            presentation_context: Global presentation context
            previous_slides: Previous slides for context
            slide_index: Current slide index
            
        Returns:
            Semantic map with groups, priorities, highlight strategies
        """
        try:
            logger.info(f"🔍 Analyzing slide {slide_index + 1} with Gemini 2.0 Flash")
            
            if self.use_mock:
                return self._analyze_slide_mock(ocr_elements, presentation_context, slide_index)
            
            # Prepare prompt
            prompt = self._create_prompt(ocr_elements, presentation_context, slide_index)
            
            # Load image if available
            inputs = [prompt]
            if os.path.exists(slide_image_path):
                try:
                    from PIL import Image
                    img = Image.open(slide_image_path)
                    inputs.append(img)
                    logger.info(f"   📸 Image loaded: {slide_image_path}")
                except Exception as e:
                    logger.warning(f"Could not load image: {e}")
            
            # Generate with Gemini
            response = self.model.generate_content(inputs)
            
            # Parse response
            result = self._parse_response(response.text)
            result['mock'] = False
            
            logger.info(f"   ✅ Found {len(result.get('groups', []))} semantic groups")
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}, using mock")
            return self._analyze_slide_mock(ocr_elements, presentation_context, slide_index)
    
    def _create_prompt(
        self,
        ocr_elements: List[Dict[str, Any]],
        presentation_context: Dict[str, Any],
        slide_index: int
    ) -> str:
        """Create optimized prompt for Gemini"""
        
        # Separate text and diagram elements
        text_elements = []
        diagram_elements = []
        
        for i, el in enumerate(ocr_elements[:30]):
            if el.get('type') == 'diagram':
                diagram_elements.append((i, el))
            else:
                text_elements.append((i, el))
        
        # Format text elements
        elements_text = []
        for i, el in text_elements:
            text = el.get('text', '')[:100]  # Limit text length
            el_type = el.get('type', 'text')
            elements_text.append(f"{i}. [{el_type}] {text}")
        
        elements_str = "\n".join(elements_text) if elements_text else "No text elements"
        
        # Format diagram elements
        diagrams_text = []
        for i, el in diagram_elements:
            diagram_type = el.get('diagram_type', 'unknown')
            description = el.get('description', '')
            complexity = el.get('visual_complexity', 'medium')
            key_elements = el.get('key_elements', [])
            
            diagrams_text.append(
                f"{i}. [DIAGRAM: {diagram_type}] {description}\n"
                f"   Complexity: {complexity}, Key elements: {', '.join(key_elements[:3])}"
            )
        
        diagrams_str = "\n".join(diagrams_text) if diagrams_text else "No diagrams"
        
        # Context info
        theme = presentation_context.get('theme', 'unknown')
        level = presentation_context.get('level', 'general')
        
        prompt = f"""Analyze this presentation slide and group elements semantically.

**Presentation:** {theme} (level: {level})
**Slide:** {slide_index + 1}

**Text Elements:**
{elements_str}

**Diagrams and Visual Elements:**
{diagrams_str}

**Task:** Group related elements and assign priorities.

**Rules:**
1. Titles/headings: HIGH priority
2. Diagrams/charts/tables: HIGH priority (need detailed explanation)
3. Key content: MEDIUM priority  
4. Supporting text: LOW priority
5. Decorations (logos, watermarks): NONE priority

**Special handling for diagrams:**
- Each diagram should be in a separate group with type='diagram'
- Use highlight_strategy='diagram_walkthrough' for diagrams
- Priority should be HIGH or MEDIUM depending on importance

**Return JSON format:**
```json
{{
  "groups": [
    {{
      "type": "heading|body|diagram|decoration",
      "priority": "high|medium|low|none",
      "elements": [0, 1, 2],
      "highlight_strategy": "spotlight|group_bracket|highlight|sequential|blur_others|diagram_walkthrough"
    }}
  ]
}}
```

Return ONLY the JSON, no extra text."""

        return prompt
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse Gemini JSON response"""
        try:
            # Extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without markdown
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate structure
            if 'groups' not in data:
                raise ValueError("Missing 'groups' in response")
            
            # Ensure all groups have required fields
            for group in data['groups']:
                if 'type' not in group:
                    group['type'] = 'body'
                if 'priority' not in group:
                    group['priority'] = 'medium'
                if 'elements' not in group:
                    group['elements'] = []
                if 'highlight_strategy' not in group:
                    group['highlight_strategy'] = 'highlight'
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.debug(f"Response text: {text[:500]}")
            
            # Return minimal valid structure
            return {
                "groups": [
                    {
                        "type": "body",
                        "priority": "medium",
                        "elements": list(range(min(5, len(text.split())))),
                        "highlight_strategy": "highlight"
                    }
                ]
            }
    
    def _analyze_slide_mock(
        self,
        ocr_elements: List[Dict[str, Any]],
        presentation_context: Dict[str, Any],
        slide_index: int
    ) -> Dict[str, Any]:
        """Mock analysis for testing"""
        logger.info(f"   ⚠️  Using mock semantic analysis")
        
        # Simple heuristic grouping
        groups = []
        
        # Find title (first large text)
        title_elements = []
        body_elements = []
        decoration_elements = []
        diagram_elements = []
        
        for i, el in enumerate(ocr_elements[:20]):
            text = el.get('text', '').lower()
            el_type = el.get('type', 'text')
            
            # Diagrams
            if el_type == 'diagram':
                diagram_elements.append((i, el))
            # Decorations
            elif any(word in text for word in ['logo', 'watermark', 'copyright', '©']):
                decoration_elements.append(i)
            # Titles (first few, or large text)
            elif i < 3 and len(text) > 5:
                title_elements.append(i)
            # Body
            else:
                body_elements.append(i)
        
        # Create groups
        if title_elements:
            groups.append({
                "type": "heading",
                "priority": "high",
                "elements": title_elements,
                "highlight_strategy": "spotlight"
            })
        
        # Create separate groups for each diagram (important!)
        for i, (elem_idx, diagram_el) in enumerate(diagram_elements):
            diagram_type = diagram_el.get('diagram_type', 'unknown')
            groups.append({
                "type": "diagram",
                "priority": "high",  # Diagrams are important
                "elements": [elem_idx],
                "highlight_strategy": "diagram_walkthrough",
                "diagram_type": diagram_type
            })
        
        if body_elements:
            groups.append({
                "type": "body",
                "priority": "medium",
                "elements": body_elements,
                "highlight_strategy": "sequential"
            })
        
        if decoration_elements:
            groups.append({
                "type": "decoration",
                "priority": "none",
                "elements": decoration_elements,
                "highlight_strategy": "highlight"
            })
        
        return {
            "groups": groups,
            "mock": True
        }
