"""
Stage 0: Presentation Intelligence
Глобальный анализ всей презентации для понимания контекста
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import os

logger = logging.getLogger(__name__)

class PresentationIntelligence:
    """Анализирует презентацию целиком для понимания контекста"""
    
    def __init__(self):
        # Use configured LLM provider (Gemini/OpenRouter/etc)
        from app.services.provider_factory import ProviderFactory
        
        try:
            self.llm_worker = ProviderFactory.get_llm_provider()
            self.use_mock = False
            logger.info(f"✅ PresentationIntelligence: Using {os.getenv('LLM_PROVIDER', 'unknown')} provider")
        except Exception as e:
            logger.warning(f"LLM provider setup failed: {e}, using mock mode")
            self.llm_worker = None
            self.use_mock = True
    
    async def analyze_presentation(
        self,
        slides_data: List[Dict[str, Any]],
        filename: str = "presentation"
    ) -> Dict[str, Any]:
        """
        Анализирует всю презентацию для извлечения контекста
        
        Args:
            slides_data: Список слайдов с elements
            filename: Имя файла презентации
            
        Returns:
            Presentation context с темой, уровнем, структурой и связями
        """
        try:
            logger.info(f"Analyzing presentation: {filename} ({len(slides_data)} slides)")
            
            if self.use_mock:
                return self._analyze_presentation_mock(slides_data, filename)
            
            # Prepare slides summary for LLM
            slides_summary = self._prepare_slides_summary(slides_data)
            
            # Call LLM for global analysis
            prompt = self._create_presentation_analysis_prompt(slides_summary, filename)
            
            system_prompt = "You are an expert presentation analyst. Analyze the structure and context of presentations."
            
            # Generate using LLM worker
            result_text = self.llm_worker.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=2000
            )
            
            # Try to parse as JSON
            try:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                context = json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                context = self._parse_text_response(result_text)
            
            logger.info(f"✅ Presentation analysis completed: {context.get('theme', 'unknown theme')}")
            return context
            
        except Exception as e:
            logger.error(f"Error analyzing presentation: {e}")
            return self._analyze_presentation_mock(slides_data, filename)
    
    def _prepare_slides_summary(self, slides_data: List[Dict[str, Any]]) -> str:
        """Подготовка краткого содержания слайдов для LLM"""
        summary_lines = []
        
        for i, slide in enumerate(slides_data, 1):
            elements = slide.get('elements', [])
            
            # Extract main text from elements
            texts = []
            for element in elements[:5]:  # Первые 5 элементов
                if element.get('text'):
                    texts.append(element['text'][:100])  # Первые 100 символов
            
            slide_text = " | ".join(texts)
            summary_lines.append(f"Slide {i}: {slide_text}")
        
        return "\n".join(summary_lines)
    
    def _create_presentation_analysis_prompt(self, slides_summary: str, filename: str) -> str:
        """Создание промпта для анализа презентации"""
        target_language = os.getenv("LLM_LANGUAGE", "ru")
        return f"""Analyze this presentation and provide structured context.

Presentation: {filename}

Slides summary:
{slides_summary}

IMPORTANT: The "language" field should be set to "{target_language}" (target output language), NOT the source presentation language.

Provide the following analysis in JSON format:
{{
  "theme": "Main theme of the presentation (e.g., 'Physics for Biology Students')",
  "subject_area": "Subject area (e.g., 'Physics', 'Biology', 'Computer Science')",
  "level": "Education level (e.g., 'undergraduate', 'high_school', 'graduate', 'professional')",
  "language": "{target_language}",
  "structure": ["intro", "main_content_1", "main_content_2", "summary"],
  "key_concepts": ["concept1", "concept2", "concept3"],
  "presentation_style": "Style (e.g., 'academic', 'corporate', 'casual')",
  "slide_relationships": {{
    "slide_3_references": "slide_1",
    "slide_5_continues": "slide_4"
  }},
  "reference_slides": {{
    "table_of_contents": [2],
    "summary_slides": [10, 20]
  }},
  "estimated_duration_per_slide": 45
}}

Respond ONLY with valid JSON, no additional text."""
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """Parse non-JSON text response as fallback"""
        return {
            "theme": "Unknown presentation",
            "subject_area": "General",
            "level": "undergraduate",
            "language": "ru",
            "structure": ["intro", "content", "summary"],
            "key_concepts": [],
            "presentation_style": "academic",
            "slide_relationships": {},
            "reference_slides": {},
            "estimated_duration_per_slide": 45
        }
    
    def _analyze_presentation_mock(
        self, 
        slides_data: List[Dict[str, Any]], 
        filename: str
    ) -> Dict[str, Any]:
        """Mock analysis для тестирования без API"""
        logger.info("Using mock presentation analysis")
        
        # Use target language from environment instead of detecting from slides
        language = os.getenv("LLM_LANGUAGE", "ru")
        logger.info(f"Using target language from LLM_LANGUAGE: {language}")
        
        # Extract theme from filename or first slide
        theme = filename.replace('.pdf', '').replace('.pptx', '').replace('_', ' ').replace('-', ' ')
        
        # Detect subject area
        subject_area = "General"
        theme_lower = theme.lower()
        if 'physik' in theme_lower or 'physics' in theme_lower:
            subject_area = "Physics"
        elif 'bio' in theme_lower:
            subject_area = "Biology"
        elif 'math' in theme_lower:
            subject_area = "Mathematics"
        
        return {
            "theme": theme,
            "subject_area": subject_area,
            "level": "undergraduate",
            "language": language,
            "structure": ["intro"] + ["content"] * (len(slides_data) - 2) + ["summary"],
            "key_concepts": [],
            "presentation_style": "academic",
            "slide_relationships": {},
            "reference_slides": {},
            "estimated_duration_per_slide": 45,
            "total_slides": len(slides_data),
            "mock": True
        }
