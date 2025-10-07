"""Content Editor API - Edit and regenerate slide content"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..core.auth import get_current_user
from ..core.database import get_db, Lesson, Slide as DBSlide
from ..services.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content", tags=["content-editor"])


class RegenerateRequest(BaseModel):
    """Request to regenerate a segment of slide content"""
    lesson_id: str = Field(..., description="Lesson ID")
    slide_number: int = Field(..., description="Slide number (1-based)")
    segment_type: str = Field(..., description="Segment type: 'intro', 'main', 'conclusion', 'full'")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for regeneration")
    style: Optional[str] = Field(None, description="Style: 'casual', 'formal', 'technical'")


class EditScriptRequest(BaseModel):
    """Request to edit slide script"""
    lesson_id: str = Field(..., description="Lesson ID")
    slide_number: int = Field(..., description="Slide number (1-based)")
    new_script: str = Field(..., description="New script text")
    regenerate_audio: bool = Field(True, description="Regenerate audio after edit")


class RegenerateAudioRequest(BaseModel):
    """Request to regenerate audio for a slide"""
    lesson_id: str = Field(..., description="Lesson ID")
    slide_number: int = Field(..., description="Slide number (1-based)")
    voice_speed: Optional[float] = Field(None, description="Voice speed (0.5-2.0)")
    voice_pitch: Optional[float] = Field(None, description="Voice pitch adjustment")


class SlideScriptResponse(BaseModel):
    """Response with slide script"""
    lesson_id: str
    slide_number: int
    script: str
    audio_duration: Optional[float] = None
    status: str


@router.post("/regenerate-segment", response_model=SlideScriptResponse)
async def regenerate_segment(
    request: RegenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate a specific segment of slide content
    
    Args:
        request: Regeneration request with lesson_id, slide_number, segment_type
        
    Returns:
        Updated slide script
        
    Example:
        POST /api/content/regenerate-segment
        {
            "lesson_id": "abc-123",
            "slide_number": 1,
            "segment_type": "intro",
            "style": "casual"
        }
    """
    try:
        # Verify lesson exists and belongs to user
        result = await db.execute(
            select(Lesson).where(
                Lesson.id == request.lesson_id,
                Lesson.user_id == current_user["user_id"]
            )
        )
        lesson = result.scalar_one_or_none()
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Load manifest to get slide data
        lesson_dir = Path(".data") / request.lesson_id
        manifest_path = lesson_dir / "manifest.json"
        
        if not manifest_path.exists():
            raise HTTPException(status_code=404, detail="Manifest not found")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        slides = manifest.get('slides', [])
        
        # Find the slide (1-based indexing)
        if request.slide_number < 1 or request.slide_number > len(slides):
            raise HTTPException(status_code=400, detail="Invalid slide number")
        
        slide_data = slides[request.slide_number - 1]
        
        # Get LLM provider
        llm_provider = ProviderFactory.get_llm_provider()
        
        # Get current script
        current_script = slide_data.get('lecture_text', '')
        slide_image_path = lesson_dir / slide_data['image']
        
        # Build regeneration prompt based on segment type
        if request.segment_type == "full":
            prompt = f"""Regenerate the ENTIRE presentation script for this slide.
            
Current script:
{current_script}

Requirements:
- Maintain the same information and key points
- Use a {request.style or 'professional'} style
- Make it engaging and clear
{f'- {request.custom_prompt}' if request.custom_prompt else ''}

Generate a completely new script:"""
        
        elif request.segment_type in ["intro", "main", "conclusion"]:
            # Split script into segments (simple heuristic)
            lines = current_script.split('. ')
            
            if request.segment_type == "intro":
                segment = '. '.join(lines[:2]) if len(lines) >= 2 else current_script
                segment_desc = "introduction/opening"
            elif request.segment_type == "conclusion":
                segment = '. '.join(lines[-2:]) if len(lines) >= 2 else current_script
                segment_desc = "conclusion/closing"
            else:  # main
                segment = '. '.join(lines[2:-2]) if len(lines) > 4 else current_script
                segment_desc = "main content"
            
            prompt = f"""Regenerate only the {segment_desc} of this slide script.

Current {segment_desc}:
{segment}

Full context:
{current_script}

Requirements:
- Keep the same key information
- Use a {request.style or 'professional'} style
- Make it flow naturally with the rest of the script
{f'- {request.custom_prompt}' if request.custom_prompt else ''}

Generate new {segment_desc}:"""
        
        else:
            raise HTTPException(status_code=400, detail="Invalid segment_type")
        
        # Generate new content
        logger.info(f"Regenerating {request.segment_type} for slide {request.slide_number}")
        
        new_content = await llm_provider.generate_simple(prompt)
        
        # If regenerating segment, merge with existing script
        if request.segment_type != "full":
            # Simple merge - replace the segment
            lines = current_script.split('. ')
            
            if request.segment_type == "intro" and len(lines) >= 2:
                new_script = new_content + '. '.join(lines[2:])
            elif request.segment_type == "conclusion" and len(lines) >= 2:
                new_script = '. '.join(lines[:-2]) + new_content
            elif request.segment_type == "main" and len(lines) > 4:
                new_script = '. '.join(lines[:2]) + new_content + '. '.join(lines[-2:])
            else:
                new_script = new_content
        else:
            new_script = new_content
        
        # Update manifest
        slides[request.slide_number - 1]['lecture_text'] = new_script
        slides[request.slide_number - 1]['speaker_notes'] = new_script
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        # Update database
        await db.execute(
            update(DBSlide).where(
                DBSlide.lesson_id == request.lesson_id,
                DBSlide.slide_number == request.slide_number
            ).values(
                speaker_notes=new_script
            )
        )
        await db.commit()
        
        return SlideScriptResponse(
            lesson_id=request.lesson_id,
            slide_number=request.slide_number,
            script=new_script,
            status="regenerated"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating segment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to regenerate: {str(e)}")


@router.post("/edit-script", response_model=SlideScriptResponse)
async def edit_script(
    request: EditScriptRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Edit slide script manually
    
    Args:
        request: Edit request with lesson_id, slide_number, new_script
        
    Returns:
        Updated slide script
        
    Example:
        POST /api/content/edit-script
        {
            "lesson_id": "abc-123",
            "slide_number": 1,
            "new_script": "This is the new script...",
            "regenerate_audio": true
        }
    """
    try:
        # Verify lesson exists and belongs to user
        result = await db.execute(
            select(Lesson).where(
                Lesson.id == request.lesson_id,
                Lesson.user_id == current_user["user_id"]
            )
        )
        lesson = result.scalar_one_or_none()
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Load manifest
        lesson_dir = Path(".data") / request.lesson_id
        manifest_path = lesson_dir / "manifest.json"
        
        if not manifest_path.exists():
            raise HTTPException(status_code=404, detail="Manifest not found")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        slides = manifest.get('slides', [])
        
        if request.slide_number < 1 or request.slide_number > len(slides):
            raise HTTPException(status_code=400, detail="Invalid slide number")
        
        # Update script in manifest
        slides[request.slide_number - 1]['lecture_text'] = request.new_script
        slides[request.slide_number - 1]['speaker_notes'] = request.new_script
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        # Update database
        await db.execute(
            update(DBSlide).where(
                DBSlide.lesson_id == request.lesson_id,
                DBSlide.slide_number == request.slide_number
            ).values(
                speaker_notes=request.new_script
            )
        )
        await db.commit()
        
        # Regenerate audio in background if requested
        if request.regenerate_audio:
            background_tasks.add_task(
                regenerate_audio_background,
                request.lesson_id,
                request.slide_number,
                request.new_script
            )
        
        return SlideScriptResponse(
            lesson_id=request.lesson_id,
            slide_number=request.slide_number,
            script=request.new_script,
            status="updated" if request.regenerate_audio else "updated_no_audio"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing script: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to edit: {str(e)}")


@router.post("/regenerate-audio", response_model=SlideScriptResponse)
async def regenerate_audio(
    request: RegenerateAudioRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate audio for a slide (keeping the same script)
    
    Args:
        request: Audio regeneration request
        
    Returns:
        Status of audio regeneration
    """
    try:
        # Verify lesson exists
        result = await db.execute(
            select(Lesson).where(
                Lesson.id == request.lesson_id,
                Lesson.user_id == current_user["user_id"]
            )
        )
        lesson = result.scalar_one_or_none()
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Load manifest
        lesson_dir = Path(".data") / request.lesson_id
        manifest_path = lesson_dir / "manifest.json"
        
        if not manifest_path.exists():
            raise HTTPException(status_code=404, detail="Manifest not found")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        slides = manifest.get('slides', [])
        
        if request.slide_number < 1 or request.slide_number > len(slides):
            raise HTTPException(status_code=400, detail="Invalid slide number")
        
        slide_data = slides[request.slide_number - 1]
        script = slide_data.get('lecture_text', '')
        
        # Regenerate audio in background
        background_tasks.add_task(
            regenerate_audio_background,
            request.lesson_id,
            request.slide_number,
            script,
            voice_speed=request.voice_speed,
            voice_pitch=request.voice_pitch
        )
        
        return SlideScriptResponse(
            lesson_id=request.lesson_id,
            slide_number=request.slide_number,
            script=script,
            status="audio_regenerating"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to regenerate audio: {str(e)}")


async def regenerate_audio_background(
    lesson_id: str,
    slide_number: int,
    script: str,
    voice_speed: Optional[float] = None,
    voice_pitch: Optional[float] = None
):
    """
    Background task to regenerate audio for a slide
    
    Args:
        lesson_id: Lesson ID
        slide_number: Slide number (1-based)
        script: Script text
        voice_speed: Optional voice speed
        voice_pitch: Optional voice pitch
    """
    try:
        logger.info(f"Regenerating audio for lesson {lesson_id}, slide {slide_number}")
        
        # Get TTS provider
        tts_provider = ProviderFactory.get_tts_provider()
        
        # Generate audio
        lesson_dir = Path(".data") / lesson_id
        audio_path = lesson_dir / f"slide_{slide_number}.mp3"
        
        # Generate SSML if provider supports it
        if hasattr(tts_provider, 'text_to_speech_ssml'):
            # Simple SSML wrapper
            ssml = f'<speak>{script}</speak>'
            duration = await tts_provider.text_to_speech_ssml(
                ssml,
                str(audio_path),
                voice_speed=voice_speed or 1.0
            )
        else:
            duration = await tts_provider.text_to_speech(
                script,
                str(audio_path)
            )
        
        # Update manifest with new duration
        manifest_path = lesson_dir / "manifest.json"
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        manifest['slides'][slide_number - 1]['duration'] = duration
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Audio regenerated successfully: {duration}s")
    
    except Exception as e:
        logger.error(f"Failed to regenerate audio: {e}", exc_info=True)


@router.get("/slide-script/{lesson_id}/{slide_number}", response_model=SlideScriptResponse)
async def get_slide_script(
    lesson_id: str,
    slide_number: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current script for a slide
    
    Args:
        lesson_id: Lesson ID
        slide_number: Slide number (1-based)
        
    Returns:
        Current slide script
    """
    try:
        # Verify lesson exists
        result = await db.execute(
            select(Lesson).where(
                Lesson.id == lesson_id,
                Lesson.user_id == current_user["user_id"]
            )
        )
        lesson = result.scalar_one_or_none()
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Load manifest
        lesson_dir = Path(".data") / lesson_id
        manifest_path = lesson_dir / "manifest.json"
        
        if not manifest_path.exists():
            raise HTTPException(status_code=404, detail="Manifest not found")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        slides = manifest.get('slides', [])
        
        if slide_number < 1 or slide_number > len(slides):
            raise HTTPException(status_code=400, detail="Invalid slide number")
        
        slide_data = slides[slide_number - 1]
        
        return SlideScriptResponse(
            lesson_id=lesson_id,
            slide_number=slide_number,
            script=slide_data.get('lecture_text', ''),
            audio_duration=slide_data.get('duration'),
            status="ok"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting slide script: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get script: {str(e)}")
