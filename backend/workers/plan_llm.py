"""
LLM Worker for generating speaker notes and content analysis
"""
import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class LLMWorker:
    """Worker for generating content using LLM endpoints"""
    
    def __init__(self, llm_endpoint: str = "http://localhost:11434/api/generate"):
        self.llm_endpoint = llm_endpoint
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_speaker_notes(self, slide_content: Dict[str, Any], custom_prompt: Optional[str] = None) -> str:
        """
        Generate speaker notes for a slide using LLM
        
        Args:
            slide_content: Dictionary containing slide elements, text, and metadata
            custom_prompt: Optional custom prompt for generation
            
        Returns:
            Generated speaker notes text
        """
        try:
            # Extract text content from slide
            text_elements = []
            for element in slide_content.get('elements', []):
                if element.get('type') == 'text' and element.get('text'):
                    text_elements.append(element['text'])
            
            slide_text = ' '.join(text_elements)
            
            # Create prompt for speaker notes generation
            if custom_prompt:
                prompt = f"""
                {custom_prompt}
                
                Slide content: {slide_text}
                
                Generate comprehensive speaker notes for this slide that would help a presenter explain the content effectively.
                Include:
                1. Key points to emphasize
                2. Explanations and context
                3. Examples or analogies
                4. Transition phrases to next slide
                
                Keep the notes conversational and presenter-friendly.
                """
            else:
                prompt = f"""
                You are an expert presentation coach. Generate detailed speaker notes for this slide content:
                
                Slide text: {slide_text}
                
                Create comprehensive speaker notes that include:
                1. Main talking points (2-3 key messages)
                2. Detailed explanations for each point
                3. Examples, analogies, or stories to illustrate concepts
                4. Smooth transitions between topics
                5. Engagement techniques (questions, pauses, emphasis)
                
                Format the notes in a clear, easy-to-read structure.
                Aim for 150-300 words that would take 60-90 seconds to present.
                """
            
            # Call LLM endpoint
            notes = await self._call_llm(prompt)
            
            logger.info(f"Generated speaker notes for slide: {len(notes)} characters")
            return notes
            
        except Exception as e:
            logger.error(f"Error generating speaker notes: {e}")
            raise
    
    async def analyze_slide_content(self, slide_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze slide content to extract key information for timing and effects
        
        Args:
            slide_content: Dictionary containing slide elements and metadata
            
        Returns:
            Analysis results including timing suggestions and element priorities
        """
        try:
            # Extract structured content
            elements = slide_content.get('elements', [])
            text_elements = [e for e in elements if e.get('type') == 'text']
            
            # Create analysis prompt
            prompt = f"""
            Analyze this slide content for presentation timing and visual effects:
            
            Elements: {json.dumps(text_elements, indent=2)}
            
            Provide analysis in JSON format with:
            1. "key_concepts": List of main concepts (2-4 items)
            2. "reading_order": Suggested order for highlighting elements
            3. "timing_suggestions": Suggested durations for each concept (in seconds)
            4. "emphasis_levels": Priority levels (1-3) for each element
            5. "transition_points": Natural break points for visual effects
            
            Example format:
            {{
                "key_concepts": ["concept1", "concept2"],
                "reading_order": ["element_id_1", "element_id_2"],
                "timing_suggestions": {{"element_id_1": 3.0, "element_id_2": 2.5}},
                "emphasis_levels": {{"element_id_1": 1, "element_id_2": 2}},
                "transition_points": [1.5, 4.0]
            }}
            """
            
            # Call LLM and parse response
            response = await self._call_llm(prompt)
            
            # Try to parse JSON response
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                # Fallback if LLM doesn't return valid JSON
                analysis = self._create_fallback_analysis(elements)
            
            logger.info(f"Analyzed slide content: {len(analysis.get('key_concepts', []))} concepts")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing slide content: {e}")
            raise
    
    async def generate_timing_cues(self, speaker_notes: str, slide_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate timing cues based on speaker notes and slide analysis
        
        Args:
            speaker_notes: Generated speaker notes text
            slide_analysis: Analysis results from analyze_slide_content
            
        Returns:
            List of timing cues with t0, t1, action, and element references
        """
        try:
            prompt = f"""
            Generate precise timing cues for a presentation slide based on:
            
            Speaker Notes: {speaker_notes}
            
            Slide Analysis: {json.dumps(slide_analysis, indent=2)}
            
            Create timing cues in JSON format. Each cue should have:
            - "t0": start time in seconds
            - "t1": end time in seconds  
            - "action": "highlight", "underline", or "laser_move"
            - "element_id": reference to slide element
            - "bbox": bounding box coordinates [x, y, width, height] for highlight/underline
            - "to": target position [x, y] for laser_move
            
            Apply these rules:
            1. Minimum highlight duration: 0.8 seconds
            2. Minimum gap between effects: 0.2 seconds
            3. Total presentation should be 60-90 seconds
            4. Use highlight for main concepts, underline for details
            5. Use laser_move for transitions between elements
            
            Return as JSON array of cue objects.
            """
            
            response = await self._call_llm(prompt)
            
            try:
                cues = json.loads(response)
                # Validate and clean cues
                validated_cues = self._validate_timing_cues(cues)
                logger.info(f"Generated {len(validated_cues)} timing cues")
                return validated_cues
            except json.JSONDecodeError:
                logger.warning("LLM returned invalid JSON for timing cues, using fallback")
                return self._create_fallback_cues(slide_analysis)
                
        except Exception as e:
            logger.error(f"Error generating timing cues: {e}")
            raise
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM endpoint with the given prompt"""
        if not self.session:
            raise RuntimeError("LLMWorker session not initialized")
        
        payload = {
            "model": "llama3.2:latest",  # Default model
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000
            }
        }
        
        try:
            async with self.session.post(
                self.llm_endpoint,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '')
                else:
                    error_text = await response.text()
                    raise Exception(f"LLM API error {response.status}: {error_text}")
                    
        except asyncio.TimeoutError:
            raise Exception("LLM request timed out")
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def _create_fallback_analysis(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create fallback analysis when LLM fails"""
        text_elements = [e for e in elements if e.get('type') == 'text']
        
        return {
            "key_concepts": [f"Concept {i+1}" for i in range(min(3, len(text_elements)))],
            "reading_order": [e.get('id', f"elem_{i}") for i, e in enumerate(text_elements)],
            "timing_suggestions": {e.get('id', f"elem_{i}"): 3.0 for i, e in enumerate(text_elements)},
            "emphasis_levels": {e.get('id', f"elem_{i}"): 1 for i, e in enumerate(text_elements)},
            "transition_points": [2.0, 5.0, 8.0]
        }
    
    def _validate_timing_cues(self, cues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean timing cues"""
        validated = []
        current_time = 0.0
        
        for cue in cues:
            # Ensure minimum durations and gaps
            t0 = max(current_time, cue.get('t0', current_time))
            t1 = max(t0 + 0.8, cue.get('t1', t0 + 2.0))  # Min 0.8s duration
            
            validated_cue = {
                "t0": t0,
                "t1": t1,
                "action": cue.get('action', 'highlight'),
                "element_id": cue.get('element_id'),
                "bbox": cue.get('bbox'),
                "to": cue.get('to')
            }
            
            validated.append(validated_cue)
            current_time = t1 + 0.2  # Min 0.2s gap
        
        return validated
    
    def _create_fallback_cues(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create fallback timing cues when LLM fails"""
        cues = []
        current_time = 0.0
        
        reading_order = analysis.get('reading_order', [])
        
        for i, element_id in enumerate(reading_order):
            duration = analysis.get('timing_suggestions', {}).get(element_id, 3.0)
            
            cue = {
                "t0": current_time,
                "t1": current_time + duration,
                "action": "highlight",
                "element_id": element_id,
                "bbox": None  # Will be filled from slide elements
            }
            
            cues.append(cue)
            current_time += duration + 0.2  # Add gap
        
        return cues

# Utility functions for integration
async def generate_notes_for_slide(lesson_id: str, slide_id: int, slide_content: Dict[str, Any], custom_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate comprehensive notes and analysis for a slide
    
    Args:
        lesson_id: Lesson identifier
        slide_id: Slide number
        slide_content: Slide content dictionary
        custom_prompt: Optional custom generation prompt
        
    Returns:
        Dictionary containing speaker_notes, analysis, and timing_cues
    """
    async with LLMWorker() as worker:
        try:
            # Generate speaker notes
            speaker_notes = await worker.generate_speaker_notes(slide_content, custom_prompt)
            
            # Analyze slide content
            analysis = await worker.analyze_slide_content(slide_content)
            
            # Generate timing cues
            timing_cues = await worker.generate_timing_cues(speaker_notes, analysis)
            
            return {
                "speaker_notes": speaker_notes,
                "analysis": analysis,
                "timing_cues": timing_cues,
                "lesson_id": lesson_id,
                "slide_id": slide_id,
                "generated_at": str(uuid.uuid4())
            }
            
        except Exception as e:
            logger.error(f"Failed to generate notes for slide {slide_id}: {e}")
            raise

if __name__ == "__main__":
    # Test the worker
    async def test_worker():
        test_content = {
            "elements": [
                {"id": "elem_1", "type": "text", "text": "Welcome to our presentation", "bbox": [100, 100, 400, 50]},
                {"id": "elem_2", "type": "text", "text": "Today we will discuss AI technology", "bbox": [100, 200, 400, 50]}
            ]
        }
        
        async with LLMWorker() as worker:
            notes = await worker.generate_speaker_notes(test_content)
            print("Generated notes:", notes)
            
            analysis = await worker.analyze_slide_content(test_content)
            print("Analysis:", analysis)
            
            cues = await worker.generate_timing_cues(notes, analysis)
            print("Timing cues:", cues)
    
    asyncio.run(test_worker())