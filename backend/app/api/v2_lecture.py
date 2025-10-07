"""
New API endpoints for concept-based lecture generation
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..core.config import settings
from ..models.schemas import (
    SpeakerNotesRequest, 
    LectureOutlineRequest, 
    TalkTrackResponse,
    Manifest
)
from ..services.sprint2.ai_generator import AIGenerator
from ..services.sprint2.concept_extractor import SlideConcepts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["lecture-generation"])

# Dependency to get AI generator
def get_ai_generator() -> AIGenerator:
    return AIGenerator()

@router.post("/lecture-outline", response_model=Dict[str, Any])
async def generate_lecture_outline(
    request: LectureOutlineRequest,
    ai_generator: AIGenerator = Depends(get_ai_generator)
):
    """Generate lecture outline for coherence"""
    try:
        logger.info(f"Generating lecture outline for: {request.lecture_title}")
        
        # For now, create mock slide concepts
        # In a real implementation, this would extract concepts from all slides
        mock_concepts = [
            SlideConcepts(
                title="Introduction",
                key_theses=["Overview of topic", "Key concepts"],
                visual_insight=None,
                terms_to_define=["Term1", "Term2"]
            ),
            SlideConcepts(
                title="Main Content",
                key_theses=["Detailed explanation", "Examples"],
                visual_insight="Chart shows relationship",
                terms_to_define=["Term3"]
            )
        ]
        
        outline = await ai_generator.generate_lecture_outline(
            request.lecture_title, 
            mock_concepts
        )
        
        return outline
        
    except Exception as e:
        logger.error(f"Error generating lecture outline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/speaker-notes", response_model=TalkTrackResponse)
async def generate_speaker_notes(
    request: SpeakerNotesRequest,
    ai_generator: AIGenerator = Depends(get_ai_generator)
):
    """Generate speaker notes using new anti-reading approach"""
    try:
        logger.info(f"Generating speaker notes for slide {request.slide_id}")
        
        # Mock slide content for now
        # In a real implementation, this would come from the database
        mock_slide_content = [
            {
                "id": "title_element",
                "type": "text",
                "text": "Introduction to Machine Learning",
                "bbox": [100, 100, 800, 100],
                "confidence": 0.95
            },
            {
                "id": "bullet_1",
                "type": "text", 
                "text": "Supervised learning uses labeled data",
                "bbox": [150, 250, 600, 50],
                "confidence": 0.9
            },
            {
                "id": "bullet_2",
                "type": "text",
                "text": "Unsupervised learning finds patterns",
                "bbox": [150, 320, 600, 50],
                "confidence": 0.9
            }
        ]
        
        # Generate speaker notes
        result = await ai_generator.generate_speaker_notes(
            slide_content=mock_slide_content,
            course_title=request.course_title or "Computer Science",
            lecture_title=request.lecture_title or "Machine Learning Basics",
            slide_index=request.slide_id - 1,
            total_slides=5,  # Mock total
            prev_summary="Previous slide covered basic concepts",
            audience_level=request.audience_level,
            style_preset=request.style_preset
        )
        
        # Convert to response format
        response = TalkTrackResponse(
            talk_track=result["talk_track"],
            visual_cues=result["visual_cues"],
            terms_to_define=result["terms_to_define"],
            concepts=result["concepts"],
            overlap_score=0.15,  # Mock overlap score
            regeneration_attempts=1
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating speaker notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/manifest/{lesson_id}", response_model=Manifest)
async def get_manifest_with_concepts(lesson_id: str):
    """Get manifest with concept-based data"""
    try:
        logger.info(f"Getting manifest for lesson: {lesson_id}")
        
        # Mock manifest with new structure
        # In a real implementation, this would come from the database
        mock_manifest = {
            "slides": [
                {
                    "id": 1,
                    "image": "/assets/test/slides/001.png",
                    "audio": "/assets/test/audio/001.mp3",
                    "elements": [
                        {
                            "id": "title_element",
                            "type": "text",
                            "bbox": [100, 100, 800, 100],
                            "text": "Introduction to Machine Learning",
                            "confidence": 0.95
                        }
                    ],
                    "cues": [],
                    "talk_track": [
                        {"kind": "hook", "text": "Let's explore machine learning together."},
                        {"kind": "core", "text": "Machine learning is a powerful tool for data analysis."},
                        {"kind": "example", "text": "Think of it like teaching a computer to recognize patterns."},
                        {"kind": "contrast", "text": "Unlike traditional programming, ML learns from data."},
                        {"kind": "takeaway", "text": "Remember: ML finds patterns in data automatically."},
                        {"kind": "question", "text": "Can you think of examples where ML might help?"}
                    ],
                    "visual_cues": [
                        {"at": "hook", "targetId": "title_element"},
                        {"at": "core", "targetId": "title_element"}
                    ],
                    "concepts": {
                        "title": "Introduction to Machine Learning",
                        "key_theses": ["Supervised learning", "Unsupervised learning"],
                        "visual_insight": "Chart shows learning types"
                    },
                    "terms_to_define": ["Machine Learning", "Supervised Learning"],
                    "lecture_text": "Let's explore machine learning together. Machine learning is a powerful tool for data analysis. Think of it like teaching a computer to recognize patterns. Unlike traditional programming, ML learns from data. Remember: ML finds patterns in data automatically. Can you think of examples where ML might help?",
                    "duration": 45.0
                }
            ],
            "timeline": {
                "rules": [],
                "default_duration": 2.0,
                "transition_duration": 0.5,
                "slide_change_events": []
            },
            "lecture_outline": {
                "outline": [
                    {"idx": 1, "goal": "Introduce machine learning concepts"},
                    {"idx": 2, "goal": "Explain supervised vs unsupervised learning"},
                    {"idx": 3, "goal": "Provide practical examples"}
                ],
                "narrative_rules": [
                    "keep throughline of learning types",
                    "avoid repetition between slides", 
                    "focus on practical understanding"
                ]
            },
            "course_title": "Computer Science",
            "lecture_title": "Machine Learning Basics",
            "audience_level": "undergrad",
            "style_preset": "explanatory",
            "metadata": {
                "source_file": "test.pptx",
                "parser": "pptx",
                "total_slides": 1
            }
        }
        
        return mock_manifest
        
    except Exception as e:
        logger.error(f"Error getting manifest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regenerate-speaker-notes", response_model=TalkTrackResponse)
async def regenerate_speaker_notes(
    lesson_id: str,
    slide_id: int,
    ai_generator: AIGenerator = Depends(get_ai_generator)
):
    """Regenerate speaker notes with enhanced anti-reading"""
    try:
        logger.info(f"Regenerating speaker notes for slide {slide_id}")
        
        # This would trigger regeneration with enhanced anti-reading prompts
        # For now, return a mock response
        response = TalkTrackResponse(
            talk_track=[
                {"kind": "hook", "text": "Let's dive deeper into this fascinating topic."},
                {"kind": "core", "text": "This concept builds on what we've learned previously."},
                {"kind": "example", "text": "Imagine you're teaching someone new to this field."},
                {"kind": "contrast", "text": "This approach differs from the traditional method."},
                {"kind": "takeaway", "text": "The key insight is understanding the underlying principles."},
                {"kind": "question", "text": "How might you apply this in your own work?"}
            ],
            visual_cues=[],
            terms_to_define=["Concept1", "Concept2"],
            concepts={
                "title": "Advanced Concepts",
                "key_theses": ["Advanced topic 1", "Advanced topic 2"],
                "visual_insight": "Diagram shows relationships"
            },
            overlap_score=0.12,  # Lower overlap after regeneration
            regeneration_attempts=2
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error regenerating speaker notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))