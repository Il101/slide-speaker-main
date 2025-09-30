"""
Concept extraction and anti-reading logic for lecture generation
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class SlideConcepts:
    """Extracted concepts from a slide"""
    title: Optional[str] = None
    key_theses: List[str] = None
    visual_insight: Optional[str] = None
    terms_to_define: List[str] = None
    
    def __post_init__(self):
        if self.key_theses is None:
            self.key_theses = []
        if self.terms_to_define is None:
            self.terms_to_define = []

class ConceptExtractor:
    """Extract key concepts from slide elements instead of raw text"""
    
    def __init__(self):
        self.title_keywords = ['title', 'heading', 'header', 'main', 'topic']
        self.thesis_keywords = ['point', 'bullet', 'item', 'key', 'important', 'main']
        self.visual_keywords = ['diagram', 'chart', 'graph', 'figure', 'table', 'image']
    
    def extract_concepts(self, elements: List[Dict[str, Any]]) -> SlideConcepts:
        """Extract concepts from slide elements"""
        concepts = SlideConcepts()
        
        # Extract title (usually the largest text element or first heading)
        concepts.title = self._extract_title(elements)
        
        # Extract key theses (2-5 main points)
        concepts.key_theses = self._extract_key_theses(elements)
        
        # Extract visual insights (if any diagrams/tables)
        concepts.visual_insight = self._extract_visual_insight(elements)
        
        # Extract terms that need definition
        concepts.terms_to_define = self._extract_terms_to_define(elements)
        
        return concepts
    
    def _extract_title(self, elements: List[Dict[str, Any]]) -> Optional[str]:
        """Extract slide title"""
        # Look for largest text element or explicit title
        text_elements = [e for e in elements if e.get('type') == 'text' and e.get('text')]
        
        if not text_elements:
            return None
        
        # Sort by area (width * height) to find largest
        text_elements.sort(key=lambda e: e.get('bbox', [0, 0, 0, 0])[2] * e.get('bbox', [0, 0, 0, 0])[3], reverse=True)
        
        # Take the largest text element as title
        title_text = text_elements[0]['text'].strip()
        
        # Clean up title (remove extra whitespace, limit length)
        title_text = re.sub(r'\s+', ' ', title_text)
        if len(title_text) > 100:
            title_text = title_text[:100] + "..."
        
        return title_text
    
    def _extract_key_theses(self, elements: List[Dict[str, Any]]) -> List[str]:
        """Extract 2-5 key theses from slide elements"""
        theses = []
        
        # Look for bullet points, numbered lists, or key statements
        text_elements = [e for e in elements if e.get('type') == 'text' and e.get('text')]
        
        for element in text_elements:
            text = element['text'].strip()
            
            # Skip very short text (likely not a thesis)
            if len(text) < 10:
                continue
            
            # Skip if it looks like a title (too long, no bullet)
            if len(text) > 80 and not any(char in text for char in ['•', '-', '*', '1.', '2.', '3.']):
                continue
            
            # Clean up thesis text
            clean_text = self._clean_thesis_text(text)
            if clean_text and len(clean_text) > 5:
                theses.append(clean_text)
        
        # Limit to 2-5 theses
        return theses[:5]
    
    def _extract_visual_insight(self, elements: List[Dict[str, Any]]) -> Optional[str]:
        """Extract insight from visual elements (diagrams, tables, etc.)"""
        # Look for elements that might be visual
        visual_elements = []
        
        for element in elements:
            element_type = element.get('type', '').lower()
            if any(keyword in element_type for keyword in self.visual_keywords):
                visual_elements.append(element)
        
        if not visual_elements:
            return None
        
        # For now, return a generic insight
        # In a real implementation, this would use vision AI to analyze the visual
        return "This visual element shows important relationships and patterns"
    
    def _extract_terms_to_define(self, elements: List[Dict[str, Any]]) -> List[str]:
        """Extract technical terms that need definition"""
        terms = []
        
        # Look for technical terms (capitalized words, acronyms, etc.)
        text_elements = [e for e in elements if e.get('type') == 'text' and e.get('text')]
        
        for element in text_elements:
            text = element['text']
            
            # Find potential technical terms
            # Look for ALL CAPS words (acronyms)
            acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
            terms.extend(acronyms)
            
            # Look for capitalized technical terms
            tech_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            # Filter out common words
            common_words = {'The', 'This', 'That', 'These', 'Those', 'And', 'Or', 'But', 'For', 'With', 'By'}
            tech_terms = [term for term in tech_terms if term not in common_words]
            terms.extend(tech_terms)
        
        # Remove duplicates and limit
        unique_terms = list(set(terms))
        return unique_terms[:5]  # Limit to 5 terms
    
    def _clean_thesis_text(self, text: str) -> str:
        """Clean up thesis text"""
        # Remove bullet points and numbering
        text = re.sub(r'^[\s•\-\*\d+\.\)]\s*', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit length
        if len(text) > 80:
            text = text[:80] + "..."
        
        return text

class AntiReadingDetector:
    """Detect and prevent reading from slides"""
    
    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold
    
    def calculate_overlap(self, generated_text: str, slide_text: str) -> float:
        """Calculate Jaccard similarity between generated text and slide text"""
        if not generated_text or not slide_text:
            return 0.0
        
        # Convert to lowercase and split into words
        gen_words = set(generated_text.lower().split())
        slide_words = set(slide_text.lower().split())
        
        # Calculate Jaccard similarity
        intersection = gen_words.intersection(slide_words)
        union = gen_words.union(slide_words)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def should_regenerate(self, generated_text: str, slide_text: str) -> bool:
        """Check if text should be regenerated due to high overlap"""
        overlap = self.calculate_overlap(generated_text, slide_text)
        logger.info(f"Text overlap: {overlap:.3f} (threshold: {self.threshold})")
        return overlap > self.threshold
    
    def get_regeneration_prompt_addition(self) -> str:
        """Get additional prompt text to encourage explanation over reading"""
        return """
        IMPORTANT: Do not read or quote the slide text directly. Instead:
        - Explain the concepts in your own words
        - Provide examples and analogies
        - Add context and background information
        - Use different phrasing than what's on the slide
        - Focus on WHY this is important, not just WHAT it says
        """

class LectureOutlineGenerator:
    """Generate lecture outline for coherence"""
    
    def __init__(self):
        self.outline_prompt = """
        Build a concise outline (3-6 bullets) for lecture "{lecture_title}".
        Return JSON:
        {"outline":[{"idx":1,"goal":"..."},{"idx":2,"goal":"..."}],
         "narrative_rules":["keep throughline X","avoid duplication of Y","focus on Z"] }
        """
    
    def generate_outline(self, lecture_title: str, slide_concepts: List[SlideConcepts]) -> Dict[str, Any]:
        """Generate lecture outline based on slide concepts"""
        # Extract key themes from all slides
        all_themes = []
        for concepts in slide_concepts:
            if concepts.title:
                all_themes.append(concepts.title)
            all_themes.extend(concepts.key_theses)
        
        # Create a simple outline based on themes
        outline = []
        for i, theme in enumerate(all_themes[:6], 1):  # Limit to 6 goals
            outline.append({
                "idx": i,
                "goal": f"Explain {theme}"
            })
        
        narrative_rules = [
            "keep throughline of main concepts",
            "avoid repetition between slides",
            "focus on practical understanding"
        ]
        
        return {
            "outline": outline,
            "narrative_rules": narrative_rules
        }

# Integration functions
def extract_slide_concepts(elements: List[Dict[str, Any]]) -> SlideConcepts:
    """Extract concepts from slide elements"""
    extractor = ConceptExtractor()
    return extractor.extract_concepts(elements)

def check_anti_reading(generated_text: str, slide_text: str, threshold: float = 0.35) -> Tuple[bool, float]:
    """Check if generated text violates anti-reading rules"""
    detector = AntiReadingDetector(threshold)
    overlap = detector.calculate_overlap(generated_text, slide_text)
    should_regenerate = detector.should_regenerate(generated_text, slide_text)
    return should_regenerate, overlap

def generate_lecture_outline(lecture_title: str, slide_concepts: List[SlideConcepts]) -> Dict[str, Any]:
    """Generate lecture outline for coherence"""
    generator = LectureOutlineGenerator()
    return generator.generate_outline(lecture_title, slide_concepts)