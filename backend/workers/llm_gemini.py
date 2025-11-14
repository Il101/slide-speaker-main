"""
Google Cloud Vertex AI Gemini LLM Worker
"""
import asyncio
import json
import logging
import os
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid

try:
    from google.cloud import aiplatform
    try:
        from vertexai.generative_models import GenerativeModel, Part
    except ImportError:
        # Fallback to preview API
        from vertexai.preview.generative_models import GenerativeModel, Part
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning("Google Cloud Vertex AI not available. Install google-cloud-aiplatform")

logger = logging.getLogger(__name__)

class GeminiLLMWorker:
    """Worker for generating speaker notes and content analysis using Google Gemini"""
    
    def __init__(self, project_id: str = None, location: str = None, model: str = None):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.location = location or os.getenv("GEMINI_LOCATION", "us-central1")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        
        # ✅ FIX: Check environment to prevent mock mode in production
        environment = os.getenv("ENVIRONMENT", "development")
        
        if not VERTEX_AI_AVAILABLE:
            if environment == "production":
                raise RuntimeError("Vertex AI library not available in production! Install google-cloud-aiplatform")
            logger.warning("Vertex AI not available, will use mock mode (development only)")
            self.use_mock = True
        elif not self.project_id:
            if environment == "production":
                raise ValueError("GCP Project ID required in production! Set GCP_PROJECT_ID")
            logger.warning("GCP Project ID not provided, will use mock mode (development only)")
            self.use_mock = True
        else:
            self.use_mock = False
            # Initialize Vertex AI
            try:
                aiplatform.init(project=self.project_id, location=self.location)
                self.generative_model = GenerativeModel(self.model)
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                self.use_mock = True
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.2, 
                max_tokens: int = 2000, image_base64: str = None, timeout: float = 30.0) -> str:
        """
        Generate text using Gemini model (supports multimodal with images)
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (prepended to user prompt)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            image_base64: Optional base64-encoded image for vision analysis
            timeout: Timeout in seconds (default: 30.0)
            
        Returns:
            Generated text
        """
        import concurrent.futures
        
        try:
            if self.use_mock:
                return self._generate_mock(prompt)
            
            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            # ✅ FIX: Add timeout to prevent hanging requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                # Call appropriate method based on whether we have an image
                if image_base64:
                    future = executor.submit(
                        self._generate_with_gemini_vision,
                        full_prompt,
                        image_base64,
                        temperature,
                        max_tokens
                    )
                else:
                    future = executor.submit(
                        self._generate_with_gemini,
                        full_prompt,
                        temperature,
                        max_tokens
                    )
                
                try:
                    response = future.result(timeout=timeout)
                    return response
                except concurrent.futures.TimeoutError:
                    logger.error(f"LLM request timed out after {timeout}s")
                    raise TimeoutError(f"Gemini API request exceeded {timeout}s timeout")
            
        except TimeoutError:
            raise  # Re-raise timeout to be caught by caller
        except Exception as e:
            logger.error(f"Error generating with Gemini: {e}")
            return self._generate_mock(prompt)
    
    def _generate_mock(self, prompt: str) -> str:
        """Mock generation for testing"""
        return '{"mock": true, "message": "Mock generation mode"}'
    
    def plan_slide_with_gemini(self, elements: List[Dict], model: str = None, 
                              location: str = None, temperature: float = 0.2) -> List[Dict]:
        """
        Генерирует notes (2–4 коротких фразы) с targetId или table_region (список ячеек).
        
        Args:
            elements: Список элементов слайда (включая table_cell и figure с alt_text)
            model: Модель Gemini для использования
            location: GCP Location
            temperature: Температура генерации
            
        Returns:
            [
              {"text":"...", "targetId":"b1"}, 
              {"text":"...", "target":{"type":"table_region","tableId":"tbl1","cells":["r2c3","r2c4"]}}
            ]
            Строгий JSON, без постороннего текста. Делай автопочинку JSON при парсинге.
        """
        try:
            if self.use_mock:
                return self._plan_slide_mock(elements)
            
            # Use provided parameters or fallback to instance settings
            model = model or self.model
            location = location or self.location
            temperature = temperature or self.temperature
            
            # Prepare prompt
            prompt = self._create_planning_prompt(elements)
            
            # Generate with Gemini
            response = self._generate_with_gemini(prompt, temperature)
            
            # Parse and validate response
            notes = self._parse_gemini_response(response)
            
            logger.info(f"Generated {len(notes)} speaker notes for slide")
            return notes
            
        except Exception as e:
            logger.error(f"Error planning slide with Gemini: {e}")
            # Fallback to mock mode
            logger.info("Falling back to mock LLM")
            return self._plan_slide_mock(elements)
    
    def _create_planning_prompt(self, elements: List[Dict]) -> str:
        """Create prompt for slide planning"""
        
        # Categorize elements
        headings = [e for e in elements if e.get('type') == 'heading']
        paragraphs = [e for e in elements if e.get('type') == 'paragraph']
        tables = [e for e in elements if e.get('type') == 'table']
        table_cells = [e for e in elements if e.get('type') == 'table_cell']
        figures = [e for e in elements if e.get('type') == 'figure']
        
        prompt = f"""
You are an expert presentation coach. Analyze this slide content and generate 2-4 concise speaker notes that would help a presenter explain the content effectively.

Slide Elements:
"""
        
        # Add headings
        if headings:
            prompt += "\nHeadings:\n"
            for heading in headings:
                prompt += f"- {heading['text']} (ID: {heading['id']})\n"
        
        # Add paragraphs
        if paragraphs:
            prompt += "\nParagraphs:\n"
            for para in paragraphs:
                prompt += f"- {para['text']} (ID: {para['id']})\n"
        
        # Add tables
        if tables:
            prompt += "\nTables:\n"
            for table in tables:
                prompt += f"- Table {table.get('table_id', 'unknown')} with {table.get('rows', 0)} rows, {table.get('cols', 0)} columns (ID: {table['id']})\n"
        
        # Add table cells
        if table_cells:
            prompt += "\nTable Cells:\n"
            for cell in table_cells:
                prompt += f"- Cell {cell.get('row', '?')},{cell.get('col', '?')}: {cell['text']} (Table: {cell.get('table_id', 'unknown')}, ID: {cell['id']})\n"
        
        # Add figures
        if figures:
            prompt += "\nFigures:\n"
            for figure in figures:
                prompt += f"- {figure.get('alt_text', figure['text'])} (ID: {figure['id']})\n"
        
        prompt += """

Generate speaker notes in JSON format. Each note should:
1. Be 1-2 sentences that explain or emphasize key content
2. Reference specific elements using their IDs
3. For table content, use table_region format with specific cells

Return ONLY valid JSON array with this exact structure:
[
  {
    "text": "Brief explanation of the main concept",
    "targetId": "element_id"
  },
  {
    "text": "Explanation of table data",
    "target": {
      "type": "table_region",
      "tableId": "table_id",
      "cells": ["r1c1", "r2c3"]
    }
  }
]

Rules:
- Use "targetId" for individual elements (headings, paragraphs, figures)
- Use "target" with "table_region" for table content
- Cell references format: "r{row}c{col}" (e.g., "r1c1", "r2c3")
- Generate 2-4 notes maximum
- Keep explanations concise but informative
- Return ONLY the JSON array, no other text
"""
        
        return prompt
    
    def _generate_with_gemini(self, prompt: str, temperature: float, max_tokens: int = 1000) -> str:
        """Generate response using Gemini model (text-only)"""
        try:
            # Configure generation parameters
            generation_config = {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": max_tokens,
            }
            
            # Generate response
            response = self.generative_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating with Gemini: {e}")
            raise
    
    def _generate_with_gemini_vision(self, prompt: str, image_base64: str, temperature: float, max_tokens: int = 3000) -> str:
        """Generate response using Gemini model with vision (multimodal)"""
        try:
            import base64
            
            # Configure generation parameters
            generation_config = {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": max_tokens,
            }
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_base64)
            
            # Create image part
            image_part = Part.from_data(data=image_bytes, mime_type="image/png")
            
            # Generate response with text + image
            response = self.generative_model.generate_content(
                [prompt, image_part],
                generation_config=generation_config
            )
            
            logger.info("✅ Generated with vision (multimodal)")
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating with Gemini vision: {e}")
            # Fallback to text-only
            logger.warning("Falling back to text-only generation")
            return self._generate_with_gemini(prompt, temperature, max_tokens)
    
    def _parse_gemini_response(self, response: str) -> List[Dict]:
        """Parse and validate Gemini response"""
        try:
            # Clean response text
            response = response.strip()
            
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response
            
            # Parse JSON
            try:
                notes = json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common JSON issues
                json_str = self._fix_json(json_str)
                notes = json.loads(json_str)
            
            # Validate structure
            if not isinstance(notes, list):
                raise ValueError("Response must be a JSON array")
            
            # Validate each note
            validated_notes = []
            for note in notes:
                if not isinstance(note, dict):
                    continue
                
                if 'text' not in note:
                    continue
                
                # Must have either targetId or target
                if 'targetId' not in note and 'target' not in note:
                    continue
                
                validated_notes.append(note)
            
            if not validated_notes:
                raise ValueError("No valid notes found in response")
            
            return validated_notes
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            # Try one retry with instruction
            try:
                retry_prompt = f"""
The previous response was invalid. Please return ONLY a valid JSON array with this exact format:

[
  {{
    "text": "Brief explanation",
    "targetId": "element_id"
  }}
]

Return ONLY the JSON array, no other text.
"""
                retry_response = self._generate_with_gemini(retry_prompt, 0.1)
                return self._parse_gemini_response(retry_response)
            except:
                raise ValueError("Failed to parse Gemini response after retry")
    
    def _fix_json(self, json_str: str) -> str:
        """Fix common JSON formatting issues"""
        # Remove any text before/after JSON array
        json_str = json_str.strip()
        
        # Fix common issues
        json_str = re.sub(r'```json\s*', '', json_str)
        json_str = re.sub(r'```\s*$', '', json_str)
        
        # Ensure proper array brackets
        if not json_str.startswith('['):
            json_str = '[' + json_str
        if not json_str.endswith(']'):
            json_str = json_str + ']'
        
        return json_str
    
    def _plan_slide_mock(self, elements: List[Dict]) -> List[Dict]:
        """Mock slide planning for testing"""
        notes = []
        
        # Find headings
        headings = [e for e in elements if e.get('type') == 'heading']
        if headings:
            notes.append({
                "text": f"Let's discuss {headings[0]['text']}",
                "targetId": headings[0]['id']
            })
        
        # Find paragraphs
        paragraphs = [e for e in elements if e.get('type') == 'paragraph']
        if paragraphs:
            notes.append({
                "text": f"This section covers {paragraphs[0]['text'][:50]}...",
                "targetId": paragraphs[0]['id']
            })
        
        # Find tables
        tables = [e for e in elements if e.get('type') == 'table']
        if tables:
            table_cells = [e for e in elements if e.get('type') == 'table_cell' and e.get('table_id') == tables[0].get('table_id')]
            if table_cells:
                cell_refs = [f"r{cell.get('row', 0)}c{cell.get('col', 0)}" for cell in table_cells[:4]]  # First 4 cells
                notes.append({
                    "text": f"Let's examine the data in this table",
                    "target": {
                        "type": "table_region",
                        "tableId": tables[0].get('table_id', 'table_1'),
                        "cells": cell_refs
                    }
                })
        
        # If no specific elements, create generic notes
        if not notes:
            notes = [
                {
                    "text": "This slide contains important information",
                    "targetId": elements[0]['id'] if elements else "slide_area"
                },
                {
                    "text": "Let's review the key points",
                    "targetId": elements[1]['id'] if len(elements) > 1 else "slide_area"
                }
            ]
        
        logger.info(f"Mock LLM generated {len(notes)} speaker notes")
        return notes

# Utility functions for integration
def plan_slide_with_gemini(elements: List[Dict], model: str = None, 
                          location: str = None, temperature: float = 0.2) -> List[Dict]:
    """
    Генерирует notes (2–4 коротких фразы) с targetId или table_region (список ячеек).
    
    Args:
        elements: Список элементов слайда (включая table_cell и figure с alt_text)
        model: Модель Gemini для использования
        location: GCP Location
        temperature: Температура генерации
        
    Returns:
        [
          {"text":"...", "targetId":"b1"}, 
          {"text":"...", "target":{"type":"table_region","tableId":"tbl1","cells":["r2c3","r2c4"]}}
        ]
        Строгий JSON, без постороннего текста. Делай автопочинку JSON при парсинге.
    """
    worker = GeminiLLMWorker()
    return worker.plan_slide_with_gemini(elements, model, location, temperature)

if __name__ == "__main__":
    # Test the worker
    async def test_worker():
        test_elements = [
            {
                "id": "elem_1",
                "type": "heading",
                "text": "Machine Learning Fundamentals",
                "bbox": [100, 50, 600, 80],
                "confidence": 0.95
            },
            {
                "id": "elem_2", 
                "type": "paragraph",
                "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
                "bbox": [100, 150, 600, 100],
                "confidence": 0.90
            },
            {
                "id": "elem_3",
                "type": "table",
                "text": "ML Types Comparison",
                "bbox": [100, 300, 600, 200],
                "table_id": "table_1",
                "rows": 3,
                "cols": 2
            },
            {
                "id": "elem_4",
                "type": "table_cell",
                "text": "Supervised Learning",
                "bbox": [100, 300, 300, 50],
                "table_id": "table_1",
                "row": 0,
                "col": 0
            },
            {
                "id": "elem_5",
                "type": "table_cell", 
                "text": "Uses labeled data",
                "bbox": [400, 300, 300, 50],
                "table_id": "table_1",
                "row": 0,
                "col": 1
            }
        ]
        
        worker = GeminiLLMWorker()
        notes = worker.plan_slide_with_gemini(test_elements)
        
        print(f"Generated {len(notes)} speaker notes:")
        for i, note in enumerate(notes):
            print(f"  {i+1}. {note['text']}")
            if 'targetId' in note:
                print(f"     Target: {note['targetId']}")
            elif 'target' in note:
                print(f"     Target: {note['target']}")
    
    asyncio.run(test_worker())