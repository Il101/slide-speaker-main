"""
Stage 2: Semantic Intelligence Layer  
LLM-based semantic analysis с multimodal vision
Using Factory AI with vision support (gpt-4o-mini or custom models)
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import os
import base64

logger = logging.getLogger(__name__)

class SemanticAnalyzer:
    """Анализирует слайды с помощью LLM"""
    
    def __init__(self):
        # Use configured LLM provider (Gemini/OpenRouter/etc)
        from app.services.provider_factory import ProviderFactory
        
        try:
            self.llm_worker = ProviderFactory.get_llm_provider()
            self.use_mock = False
            self.backend = os.getenv('LLM_PROVIDER', 'unknown')
            logger.info(f"✅ Using {self.backend} provider for semantic analysis")
        except Exception as e:
            logger.warning(f"LLM provider setup failed: {e}, using mock mode")
            self.llm_worker = None
            self.use_mock = True
            self.backend = 'mock'
    
    async def analyze_slide(
        self,
        slide_image_path: str,
        ocr_elements: List[Dict[str, Any]],
        presentation_context: Dict[str, Any],
        previous_slides: List[Dict[str, Any]] = None,
        slide_index: int = 0
    ) -> Dict[str, Any]:
        """
        Анализирует слайд с помощью multimodal LLM
        
        Args:
            slide_image_path: Путь к изображению слайда
            ocr_elements: OCR данные (текст + координаты)
            presentation_context: Контекст презентации из Stage 0
            previous_slides: Предыдущие слайды для контекста
            slide_index: Индекс текущего слайда
            
        Returns:
            Semantic map с группами, приоритетами и стратегиями
        """
        try:
            logger.info(f"Analyzing slide {slide_index + 1} with semantic intelligence")
            
            if self.use_mock:
                return self._analyze_slide_mock(ocr_elements, presentation_context, slide_index)
            
            # Encode image to base64
            image_base64 = self._encode_image(slide_image_path)
            
            # Prepare OCR data summary
            ocr_summary = self._prepare_ocr_summary(ocr_elements)
            
            # Create prompt with few-shot examples
            prompt = self._create_semantic_analysis_prompt(
                ocr_summary, 
                presentation_context, 
                previous_slides,
                slide_index
            )
            
            # Call LLM for semantic analysis with vision support
            # ✅ CRITICAL: Explain language situation to avoid confusion
            source_lang = ocr_elements[0].get('language_original', 'unknown') if ocr_elements else 'unknown'
            target_lang = ocr_elements[0].get('language_target', 'ru') if ocr_elements else 'ru'
            
            system_prompt = f"""You are an expert at analyzing presentation slides and understanding their semantic structure.

IMPORTANT - LANGUAGE HANDLING:
- The slide IMAGE contains text in {source_lang}
- The OCR data below is TRANSLATED to {target_lang}
- Use the TRANSLATED text ({target_lang}) for all your analysis and output
- The image is provided for VISUAL context only (layout, diagrams, emphasis)
- DO NOT extract text from the image - use the provided translated OCR data"""
            
            # Generate using LLM worker with image for multimodal analysis
            result_text = self.llm_worker.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=3000,
                image_base64=image_base64  # Pass image for vision analysis (Gemini will use it)
            )
            
            logger.info(f"✅ LLM analysis completed (backend: {self.backend}, vision: {bool(image_base64)})")
            
            # Extract JSON from response
            try:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                semantic_map = json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                semantic_map = self._analyze_slide_mock(ocr_elements, presentation_context, slide_index)
            
            logger.info(f"✅ Semantic analysis completed: {len(semantic_map.get('groups', []))} groups")
            return semantic_map
            
        except Exception as e:
            logger.error(f"Error in semantic analysis: {e}")
            return self._analyze_slide_mock(ocr_elements, presentation_context, slide_index)
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _prepare_ocr_summary(self, elements: List[Dict[str, Any]]) -> str:
        """Prepare OCR elements summary for prompt"""
        lines = []
        for i, elem in enumerate(elements[:20]):  # Limit to 20 elements
            # Use translated text if available, otherwise original
            text = elem.get('text_translated') or elem.get('text', '')
            bbox = elem.get('bbox', [0, 0, 0, 0])
            elem_type = elem.get('type', 'text')
            elem_id = elem.get('id', f'elem_{i}')
            
            lines.append(f"- {elem_id}: '{text[:80]}' | type:{elem_type} | bbox:{bbox}")
        
        return "\n".join(lines)
    
    def _create_semantic_analysis_prompt(
        self,
        ocr_summary: str,
        presentation_context: Dict[str, Any],
        previous_slides: List[Dict[str, Any]],
        slide_index: int
    ) -> str:
        """Create prompt for semantic analysis with few-shot examples"""
        
        # Add few-shot examples
        few_shot = self._get_few_shot_examples()
        
        prompt = f"""Analyze this slide and create a semantic map with intelligent grouping and highlight strategies.

You have access to:
1. The slide IMAGE (see attached image)
2. OCR-extracted text with coordinates (below)

Use BOTH the visual layout from the image AND the OCR data to understand the slide structure.

PRESENTATION CONTEXT:
- Theme: {presentation_context.get('theme', 'Unknown')}
- Level: {presentation_context.get('level', 'undergraduate')}
- Style: {presentation_context.get('presentation_style', 'academic')}
- Target Language: {os.getenv('LLM_LANGUAGE', 'ru')} (output language for scripts)
- Slide {slide_index + 1} of {presentation_context.get('total_slides', '?')}

OCR ELEMENTS (detected text with coordinates):
{ocr_summary}

{few_shot}

TASK:
Create a semantic map with:
1. **Semantic groups** - логические блоки контента
2. **Element classification** - title/content/example/decorative/noise
3. **Priority assignment** - high/medium/low/none
4. **Highlight strategy** - когда и как выделять
5. **Visual effect type** - какой эффект использовать

RETURN JSON in this format:
{{
  "slide_type": "title_slide | content_slide | table_slide | diagram_slide | summary_slide",
  "groups": [
    {{
      "id": "group_1",
      "name": "Main Title",
      "type": "title | heading | key_point | example | table | diagram | footer | watermark",
      "priority": "high | medium | low | none",
      "element_ids": ["elem_1", "elem_2"],
      "reading_order": [1, 2],
      "educational_intent": "What student should learn from this group",
      "highlight_strategy": {{
        "when": "start | during_explanation | during_detail | end | never",
        "effect_type": "spotlight | group_bracket | blur_others | sequential_cascade | highlight | underline | zoom_subtle | dimmed_spotlight",
        "duration": 2.5,
        "intensity": "subtle | normal | dramatic"
      }},
      "dependencies": {{
        "highlight_before": ["group_0"],
        "highlight_together_with": null,
        "highlight_after": null
      }}
    }}
  ],
  "noise_elements": ["elem_10", "elem_15"],
  "visual_density": "low | medium | high",
  "cognitive_load": "easy | medium | complex"
}}

RULES:
- Group related elements together (e.g., title + subtitle, bullet list items)
- Identify decorative elements (watermarks, logos, page numbers) as "noise"
- Set priority based on educational importance
- Choose effect_type based on content type:
  * spotlight: for key formulas, important definitions
  * group_bracket: for lists, multiple related items
  * blur_others: when need to focus on one element
  * sequential_cascade: for step-by-step lists
  * dimmed_spotlight: for high-priority content
- Consider cognitive load: don't highlight too many things at once

Respond ONLY with valid JSON."""
        
        return prompt
    
    def _get_few_shot_examples(self) -> str:
        """Get few-shot examples for better LLM understanding"""
        return """
FEW-SHOT EXAMPLES:

Example 1: Title Slide
Input: "Physics for Biology Students" (large text at top), "Christian Roos" (smaller text below)
Output:
{
  "slide_type": "title_slide",
  "groups": [
    {
      "id": "group_title",
      "type": "title",
      "priority": "high",
      "highlight_strategy": {"when": "start", "effect_type": "spotlight", "duration": 3.0}
    },
    {
      "id": "group_author",
      "type": "heading",
      "priority": "medium",
      "highlight_strategy": {"when": "during_detail", "effect_type": "highlight", "duration": 2.0}
    }
  ]
}

Example 2: Content with List
Input: "Key Concepts" (heading), "Force = mass × acceleration" (bullet 1), "Energy conservation" (bullet 2)
Output:
{
  "slide_type": "content_slide",
  "groups": [
    {
      "id": "group_heading",
      "type": "heading",
      "priority": "high",
      "highlight_strategy": {"when": "start", "effect_type": "spotlight", "duration": 2.0}
    },
    {
      "id": "group_list",
      "type": "key_point",
      "priority": "high",
      "element_ids": ["bullet_1", "bullet_2"],
      "highlight_strategy": {"when": "during_explanation", "effect_type": "sequential_cascade", "duration": 5.0}
    }
  ]
}

Example 3: Slide with Watermark
Input: "Main content", "Company Logo 2024" (small text at bottom)
Output:
{
  "groups": [
    {
      "id": "group_content",
      "type": "key_point",
      "priority": "high"
    }
  ],
  "noise_elements": ["watermark_elem"],
  "cognitive_load": "easy"
}
"""
    
    def _analyze_slide_mock(
        self,
        ocr_elements: List[Dict[str, Any]],
        presentation_context: Dict[str, Any],
        slide_index: int
    ) -> Dict[str, Any]:
        """Mock semantic analysis без API"""
        logger.info("Using mock semantic analysis")
        
        # Simple heuristic-based grouping
        groups = []
        noise_elements = []
        
        for i, elem in enumerate(ocr_elements):
            elem_id = elem.get('id', f'elem_{i}')
            text = elem.get('text', '')
            bbox = elem.get('bbox', [0, 0, 0, 0])
            
            # Simple heuristics
            is_large = bbox[2] * bbox[3] > 100000  # Large area
            is_top = bbox[1] < 300  # Top of slide
            is_bottom = bbox[1] > 700  # Bottom of slide
            is_short = len(text) < 30
            
            # Detect noise (watermarks, page numbers)
            if is_bottom and is_short and any(x in text.lower() for x in ['©', 'page', 'slide', '2024', '2023']):
                noise_elements.append(elem_id)
                continue
            
            # Create groups
            if is_large and is_top:
                # Likely title
                groups.append({
                    "id": f"group_{i}",
                    "name": "Title",
                    "type": "title",
                    "priority": "high",
                    "element_ids": [elem_id],
                    "reading_order": [1],
                    "educational_intent": "Introduce topic",
                    "highlight_strategy": {
                        "when": "start",
                        "effect_type": "spotlight",
                        "duration": 2.5,
                        "intensity": "dramatic"
                    },
                    "dependencies": {
                        "highlight_before": None,
                        "highlight_together_with": None,
                        "highlight_after": None
                    }
                })
            else:
                # Content
                groups.append({
                    "id": f"group_{i}",
                    "name": f"Content {i}",
                    "type": "key_point",
                    "priority": "medium",
                    "element_ids": [elem_id],
                    "reading_order": [i + 1],
                    "educational_intent": "Explain concept",
                    "highlight_strategy": {
                        "when": "during_explanation",
                        "effect_type": "highlight",
                        "duration": 2.0,
                        "intensity": "normal"
                    },
                    "dependencies": {
                        "highlight_before": None,
                        "highlight_together_with": None,
                        "highlight_after": None
                    }
                })
        
        return {
            "slide_type": "content_slide",
            "groups": groups,
            "noise_elements": noise_elements,
            "visual_density": "medium",
            "cognitive_load": "medium",
            "mock": True
        }
    
    def _create_gemini_prompt(
        self,
        ocr_elements: List[Dict[str, Any]],
        presentation_context: Dict[str, Any],
        slide_index: int
    ) -> str:
        """Create optimized prompt for Gemini"""
        
        # Format elements (limit to 30)
        # ✅ Use translated text for Gemini analysis (matches target language)
        elements_text = []
        for i, el in enumerate(ocr_elements[:30]):
            text = (el.get('text_translated') or el.get('text', ''))[:100]
            el_type = el.get('type', 'text')
            elements_text.append(f"{i}. [{el_type}] {text}")
        
        elements_str = "\n".join(elements_text)
        theme = presentation_context.get('theme', 'unknown')
        
        return f"""Analyze this slide and group elements semantically.

**Presentation:** {theme}
**Slide:** {slide_index + 1}

**Elements:**
{elements_str}

**Return JSON:**
```json
{{
  "groups": [
    {{
      "type": "heading|body|visual|decoration",
      "priority": "high|medium|low|none",
      "elements": [0, 1],
      "highlight_strategy": "spotlight|highlight|sequential"
    }}
  ]
}}
```

Rules: Titles=high, Content=medium, Decorations=none"""
