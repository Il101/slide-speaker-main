"""Pydantic schemas for API requests and responses"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum

class ActionType(str, Enum):
    """Types of visual effects"""
    HIGHLIGHT = "highlight"
    UNDERLINE = "underline"
    LASER_MOVE = "laser_move"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_CHANGE = "slide_change"

class SlideElement(BaseModel):
    """Detected element on slide"""
    id: str = Field(..., description="Unique element identifier")
    type: str = Field(..., description="Element type (text, image, shape)")
    bbox: List[int] = Field(..., description="Bounding box [x, y, width, height]")
    text: Optional[str] = Field(None, description="Text content if applicable")
    confidence: float = Field(default=1.0, description="Detection confidence")
    
    @field_validator('bbox')
    @classmethod
    def validate_bbox(cls, v):
        if len(v) != 4:
            raise ValueError('bbox must have exactly 4 elements [x, y, width, height]')
        if any(x < 0 for x in v):
            raise ValueError('bbox coordinates must be non-negative')
        if v[2] <= 0 or v[3] <= 0:  # width and height must be positive
            raise ValueError('bbox width and height must be positive')
        return v

class Cue(BaseModel):
    """Visual effect cue"""
    cue_id: str = Field(..., description="Unique cue identifier")
    t0: float = Field(..., description="Start time in seconds")
    t1: float = Field(..., description="End time in seconds")
    action: ActionType = Field(..., description="Type of visual effect")
    bbox: Optional[List[int]] = Field(None, description="Bounding box [x, y, width, height]")
    to: Optional[List[int]] = Field(None, description="Target position [x, y] for laser_move")
    element_id: Optional[str] = Field(None, description="Reference to slide element")
    
    @field_validator('bbox')
    @classmethod
    def validate_bbox(cls, v):
        if v is None:
            return v
        if len(v) != 4:
            raise ValueError('bbox must have exactly 4 elements [x, y, width, height]')
        if any(x < 0 for x in v):
            raise ValueError('bbox coordinates must be non-negative')
        if v[2] <= 0 or v[3] <= 0:  # width and height must be positive
            raise ValueError('bbox width and height must be positive')
        return v
    
    @field_validator('to')
    @classmethod
    def validate_to(cls, v):
        if v is None:
            return v
        if len(v) != 2:
            raise ValueError('to must have exactly 2 elements [x, y]')
        if any(x < 0 for x in v):
            raise ValueError('to coordinates must be non-negative')
        return v

class Slide(BaseModel):
    """Slide data structure with new concept-based approach"""
    id: int = Field(..., description="Slide number")
    image: str = Field(..., description="Path to slide image")
    audio: str = Field(..., description="Path to audio file")
    elements: List[SlideElement] = Field(default_factory=list, description="Detected elements")
    cues: List[Cue] = Field(default_factory=list, description="Visual effects")
    speaker_notes: Optional[List[Dict[str, Any]]] = Field(None, description="Generated speaker notes")
    lecture_text: Optional[str] = Field(None, description="Generated lecture text from talk_track")
    talk_track: Optional[List[Dict[str, Any]]] = Field(None, description="Structured talk track")
    visual_cues: Optional[List[Dict[str, Any]]] = Field(None, description="Visual cues for talk track")
    concepts: Optional[Dict[str, Any]] = Field(None, description="Extracted slide concepts")
    terms_to_define: Optional[List[str]] = Field(None, description="Terms that need definition")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")

class TimelineRule(BaseModel):
    """Individual timeline rule for visual effects"""
    action_type: str = Field(..., description="Type of action (highlight, underline, laser_move)")
    min_duration: float = Field(default=0.8, description="Minimum duration in seconds")
    max_duration: float = Field(default=5.0, description="Maximum duration in seconds")
    priority: int = Field(default=1, description="Priority level (1=highest)")
    gap_before: float = Field(default=0.2, description="Minimum gap before this action")
    gap_after: float = Field(default=0.2, description="Minimum gap after this action")

class Timeline(BaseModel):
    """Timeline configuration for visual effects with smoothness rules"""
    rules: List[TimelineRule] = Field(default_factory=list, description="Timeline rules")
    default_duration: float = Field(default=2.0, description="Default effect duration")
    transition_duration: float = Field(default=0.5, description="Transition duration between effects")
    min_highlight_duration: float = Field(default=0.8, description="Minimum highlight duration")
    min_gap: float = Field(default=0.2, description="Minimum gap between effects")
    max_total_duration: float = Field(default=90.0, description="Maximum total slide duration")
    smoothness_enabled: bool = Field(default=True, description="Enable smoothness rules")
    slide_change_events: List[Dict[str, Any]] = Field(default_factory=list, description="Slide change events")
    
    def get_default_rules(self) -> List[TimelineRule]:
        """Get default timeline rules if none provided"""
        if not self.rules:
            return [
                TimelineRule(
                    action_type="highlight",
                    min_duration=self.min_highlight_duration,
                    max_duration=5.0,
                    priority=1,
                    gap_before=self.min_gap,
                    gap_after=self.min_gap
                ),
                TimelineRule(
                    action_type="underline",
                    min_duration=0.5,
                    max_duration=3.0,
                    priority=2,
                    gap_before=self.min_gap,
                    gap_after=self.min_gap
                ),
                TimelineRule(
                    action_type="laser_move",
                    min_duration=0.3,
                    max_duration=2.0,
                    priority=3,
                    gap_before=self.min_gap,
                    gap_after=self.min_gap
                )
            ]
        return self.rules

class Manifest(BaseModel):
    """Lesson manifest structure with lecture outline"""
    slides: List[Slide] = Field(..., description="List of slides")
    timeline: Optional[Timeline] = Field(None, description="Timeline configuration")
    lecture_outline: Optional[Dict[str, Any]] = Field(None, description="Lecture outline for coherence")
    course_title: Optional[str] = Field(None, description="Course title")
    lecture_title: Optional[str] = Field(None, description="Lecture title")
    audience_level: Optional[str] = Field(None, description="Target audience level")
    style_preset: Optional[str] = Field(None, description="Presentation style preset")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class UploadResponse(BaseModel):
    """Response for file upload"""
    lesson_id: str = Field(..., description="Unique lesson identifier")
    status: str = Field(default="processing", description="Processing status")

class ExportResponse(BaseModel):
    """Response for export request"""
    status: str = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    estimated_time: Optional[str] = Field(None, description="Estimated completion time")
    task_id: Optional[str] = Field(None, description="Task ID for tracking")

class ProcessingStatus(BaseModel):
    """Processing status response"""
    lesson_id: str = Field(..., description="Lesson identifier")
    status: str = Field(..., description="Current status")
    progress: int = Field(default=0, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")

# Sprint 2: AI Generation schemas with new approach
class SpeakerNotesRequest(BaseModel):
    """Request for generating speaker notes with new approach"""
    lesson_id: str = Field(..., description="Lesson identifier")
    slide_id: int = Field(..., description="Slide number")
    course_title: Optional[str] = Field(None, description="Course title")
    lecture_title: Optional[str] = Field(None, description="Lecture title")
    audience_level: Optional[str] = Field("undergrad", description="Target audience level")
    style_preset: Optional[str] = Field("explanatory", description="Presentation style")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for generation")

class LectureOutlineRequest(BaseModel):
    """Request for generating lecture outline"""
    lesson_id: str = Field(..., description="Lesson identifier")
    lecture_title: str = Field(..., description="Lecture title")
    course_title: Optional[str] = Field(None, description="Course title")
    audience_level: Optional[str] = Field("undergrad", description="Target audience level")

class TalkTrackResponse(BaseModel):
    """Response with structured talk track"""
    talk_track: List[Dict[str, Any]] = Field(..., description="Structured talk track")
    visual_cues: List[Dict[str, Any]] = Field(default_factory=list, description="Visual cues")
    terms_to_define: List[str] = Field(default_factory=list, description="Terms to define")
    concepts: Dict[str, Any] = Field(default_factory=dict, description="Extracted concepts")
    overlap_score: Optional[float] = Field(None, description="Overlap with slide text")
    regeneration_attempts: Optional[int] = Field(None, description="Number of regeneration attempts")

class TTSRequest(BaseModel):
    """Request for text-to-speech generation"""
    lesson_id: str = Field(..., description="Lesson identifier")
    slide_id: int = Field(..., description="Slide number")
    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field(default="alloy", description="Voice to use")
    speed: float = Field(default=1.0, description="Speech speed multiplier")

class EditRequest(BaseModel):
    """Request for editing generated content"""
    lesson_id: str = Field(..., description="Lesson identifier")
    slide_id: int = Field(..., description="Slide number")
    field: str = Field(..., description="Field to edit (speaker_notes, audio, cues)")
    value: Any = Field(..., description="New value")

# Sprint 3: Export schemas
class ExportRequest(BaseModel):
    """Request for video export"""
    lesson_id: str = Field(..., description="Lesson identifier")
    quality: str = Field(default="high", description="Export quality")
    include_audio: bool = Field(default=True, description="Include audio in export")
    include_effects: bool = Field(default=True, description="Include visual effects")

# Sprint 2: Patch schemas
class CuePatch(BaseModel):
    """Patch for a single cue"""
    cue_id: Optional[str] = Field(None, description="Cue identifier (for updates)")
    t0: Optional[float] = Field(None, description="Start time")
    t1: Optional[float] = Field(None, description="End time")
    action: Optional[str] = Field(None, description="Action type")
    bbox: Optional[List[int]] = Field(None, description="Bounding box")
    to: Optional[List[int]] = Field(None, description="Target position")
    element_id: Optional[str] = Field(None, description="Element reference")

class ElementPatch(BaseModel):
    """Patch for a slide element"""
    element_id: str = Field(..., description="Element identifier")
    bbox: Optional[List[int]] = Field(None, description="New bounding box")
    text: Optional[str] = Field(None, description="New text content")
    confidence: Optional[float] = Field(None, description="New confidence score")

class SlidePatch(BaseModel):
    """Patch for a slide"""
    slide_id: int = Field(..., description="Slide number")
    speaker_notes: Optional[str] = Field(None, description="New speaker notes")
    duration: Optional[float] = Field(None, description="New duration")
    cues: Optional[List[CuePatch]] = Field(None, description="Cue modifications")
    elements: Optional[List[ElementPatch]] = Field(None, description="Element modifications")

class LessonPatchRequest(BaseModel):
    """Request for patching lesson content"""
    lesson_id: str = Field(..., description="Lesson identifier")
    slides: List[SlidePatch] = Field(..., description="Slide modifications")
    timeline: Optional[Dict[str, Any]] = Field(None, description="Timeline modifications")

class PatchResponse(BaseModel):
    """Response for patch request"""
    success: bool = Field(..., description="Whether patch was successful")
    message: str = Field(..., description="Response message")
    updated_slides: List[int] = Field(default_factory=list, description="Updated slide IDs")
    validation_issues: List[str] = Field(default_factory=list, description="Validation issues")