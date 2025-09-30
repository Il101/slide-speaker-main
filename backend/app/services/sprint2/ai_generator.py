"""Sprint 2: AI content generation service"""
import logging
from typing import Optional, Dict, Any, List
import json
import subprocess
from pathlib import Path

from ...core.exceptions import AIGenerationError
from ...core.config import settings

logger = logging.getLogger(__name__)

def _probe_audio_duration(audio_path: str) -> float:
    """Get audio duration using ffprobe"""
    try:
        # Handle both absolute and relative paths
        if audio_path.startswith("/"):
            full_path = audio_path
        else:
            full_path = str(settings.DATA_DIR / audio_path.lstrip("/"))
        
        result = subprocess.run([
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", full_path
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            logger.debug(f"Audio duration for {audio_path}: {duration}s")
            return duration
        else:
            logger.warning(f"ffprobe failed for {audio_path}: {result.stderr}")
            return 5.0  # Default duration
    except Exception as e:
        logger.warning(f"Could not probe audio duration for {audio_path}: {e}")
        return 5.0  # Default duration

def _normalize_cues(cues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize cues to ensure proper timing and remove overlaps"""
    if not cues:
        return []
    
    # Sort by start time
    sorted_cues = sorted(cues, key=lambda c: c.get("t0", 0))
    
    normalized = []
    for i, cue in enumerate(sorted_cues):
        # Ensure t1 > t0
        if cue.get("t1", 0) <= cue.get("t0", 0):
            cue["t1"] = cue["t0"] + 0.5
        
        # Avoid overlaps with previous cue
        if i > 0 and cue.get("t0", 0) < normalized[-1].get("t1", 0):
            cue["t0"] = normalized[-1]["t1"] + 0.1
        
        normalized.append(cue)
    
    return normalized

def build_cues_for_slide(notes: List[Dict], tts: Dict, elements_by_id: Dict[str, Dict]) -> List[Dict]:
    """Build cues from notes and TTS timing information"""
    sents = tts.get("sentences", [])
    cues = []
    
    for note, s in zip(notes, sents):
        target = note.get("targetId") or note.get("target")
        
        # Skip if target element not found
        if isinstance(target, str):
            if target not in elements_by_id:
                logger.warning(f"Target element {target} not found in elements_by_id")
                continue
            tgt = {"targetId": target}
        elif isinstance(target, dict):
            tgt = {"target": target}  # table_region etc.
        else:
            logger.warning(f"Invalid target in note: {target}")
            continue
        
        # Create highlight cue
        highlight_cue = {
            "t0": float(s["t0"]),
            "t1": float(s["t1"]),
            "action": "highlight",
            **tgt
        }
        cues.append(highlight_cue)
        
        # Create laser move cue after highlight
        laser_cue = {
            "t0": float(s["t1"]),
            "t1": float(s["t1"]) + 0.3,
            "action": "laser_move",
            **tgt
        }
        cues.append(laser_cue)
    
    return _normalize_cues(cues)

def inject_slide_changes(manifest: Dict[str, Any]) -> None:
    """Inject slide_change events into timeline"""
    timeline = []
    t = 0.0
    
    for i, slide in enumerate(manifest.get("slides", []), start=1):
        # Add slide change event
        timeline.append({
            "t0": round(t, 3),
            "action": "slide_change",
            "slide": i
        })
        
        # Calculate slide end time
        end = t
        
        # Check cues for end time
        if slide.get("cues"):
            cue_end = max(c.get("t1", 0) for c in slide["cues"] if "t1" in c)
            end = max(end, cue_end)
        
        # Check audio for end time
        if slide.get("audio"):
            audio_duration = _probe_audio_duration(slide["audio"])
            end = max(end, t + audio_duration)
        
        # Move to next slide
        t = end
    
    manifest["timeline"] = timeline
    logger.info(f"Injected {len(timeline)} slide_change events into timeline")

class AIGenerator:
    """AI content generation service"""
    
    def __init__(self):
        self.openai_key = settings.OPENAI_API_KEY
        self.anthropic_key = settings.ANTHROPIC_API_KEY
        
    async def generate_speaker_notes(self, slide_content: str, custom_prompt: Optional[str] = None) -> str:
        """Generate speaker notes for a slide using configured LLM provider"""
        try:
            logger.info("Generating speaker notes")
            
            # Try to use configured LLM provider
            try:
                from ...services.provider_factory import plan_slide_with_gemini
                
                # Convert slide content to elements format if it's a string
                if isinstance(slide_content, str):
                    # Create mock elements from slide content
                    elements = [{
                        "id": "slide_content",
                        "type": "paragraph", 
                        "text": slide_content,
                        "bbox": [100, 100, 800, 200],
                        "confidence": 1.0
                    }]
                else:
                    elements = slide_content
                
                # Generate speaker notes using configured LLM provider
                notes = plan_slide_with_gemini(elements)
                
                # Convert notes to text format
                speaker_notes = " ".join([note["text"] for note in notes])
                
                logger.info(f"Generated speaker notes using configured LLM provider: {len(speaker_notes)} characters")
                return speaker_notes
                
            except Exception as e:
                logger.warning(f"Failed to use configured LLM provider: {e}, using fallback")
            
            # Fallback to legacy implementation
            if not self.openai_key and not self.anthropic_key:
                logger.warning("No AI API keys configured, using placeholder")
                return "This slide covers the main topic with key points and examples."
            
            # Placeholder implementation
            prompt = custom_prompt or f"Generate speaker notes for this slide content: {slide_content}"
            
            # TODO: Call actual LLM API
            speaker_notes = f"Generated speaker notes for: {slide_content[:50]}..."
            
            return speaker_notes
            
        except Exception as e:
            logger.error(f"Error generating speaker notes: {e}")
            raise AIGenerationError(f"Failed to generate speaker notes: {e}")
    
    async def generate_slide_change_events(self, slides: list, audio_durations: list) -> list:
        """Generate slide change events based on audio durations"""
        try:
            logger.info("Generating slide change events")
            
            events = []
            current_time = 0.0
            
            for i, (slide, duration) in enumerate(zip(slides, audio_durations)):
                if i > 0:  # Skip first slide (starts at 0)
                    events.append({
                        "type": "slide_change",
                        "slide_id": slide.id,
                        "timestamp": current_time,
                        "transition_duration": 0.5
                    })
                
                current_time += duration
                
                # Add transition time
                if i < len(slides) - 1:  # Don't add transition after last slide
                    current_time += 0.5
            
            logger.info(f"Generated {len(events)} slide change events")
            return events
            
        except Exception as e:
            logger.error(f"Error generating slide change events: {e}")
            raise AIGenerationError(f"Failed to generate slide change events: {e}")
    
    async def generate_visual_cues(self, slide_content: str, speaker_notes: str) -> list:
        """Generate visual cues based on content and speaker notes"""
        try:
            logger.info("Generating visual cues")
            
            # TODO: Implement cue generation
            # - Analyze text timing
            # - Generate highlight/underline cues
            # - Create laser pointer movements
            
            # Placeholder implementation
            cues = [
                {
                    "t0": 0.5,
                    "t1": 2.0,
                    "action": "highlight",
                    "bbox": [100, 100, 800, 200]
                },
                {
                    "t0": 2.5,
                    "t1": 4.0,
                    "action": "underline",
                    "bbox": [100, 300, 600, 4]
                }
            ]
            
            return cues
            
        except Exception as e:
            logger.error(f"Error generating visual cues: {e}")
            raise AIGenerationError(f"Failed to generate visual cues: {e}")

class TTSService:
    """Text-to-Speech service"""
    
    def __init__(self):
        self.service = settings.TTS_SERVICE
        
    async def generate_audio_batch(self, texts: list, voice: str = "alloy", speed: float = 1.0) -> list:
        """Generate audio for multiple texts in batch to reduce API calls"""
        try:
            logger.info(f"Generating TTS audio batch for {len(texts)} texts")
            
            # Try to use configured TTS provider with batching
            try:
                from ...services.provider_factory import synthesize_slide_text_google
                
                # Generate audio using configured TTS provider with batching
                audio_path, tts_words = synthesize_slide_text_google(texts, voice, speed)
                
                # Read audio file
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                logger.info(f"Generated TTS audio batch using configured provider: {len(audio_data)} bytes")
                return [audio_data]
                
            except Exception as e:
                logger.warning(f"Failed to use configured TTS provider: {e}, using fallback")
            
            # Fallback to individual generation
            results = []
            for text in texts:
                audio_data = await self.generate_audio(text, voice, speed)
                results.append(audio_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating TTS audio batch: {e}")
            raise AIGenerationError(f"Failed to generate TTS audio batch: {e}")
    
    async def generate_audio(self, text: str, voice: str = "alloy", speed: float = 1.0) -> bytes:
        """Generate audio from text using configured TTS provider"""
        try:
            logger.info(f"Generating TTS audio with voice: {voice}")
            
            # Try to use configured TTS provider
            try:
                from ...services.provider_factory import synthesize_slide_text_google
                
                # Generate audio using configured TTS provider
                audio_path, tts_words = synthesize_slide_text_google([text], voice, speed)
                
                # Read audio file
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                logger.info(f"Generated TTS audio using configured provider: {len(audio_data)} bytes")
                return audio_data
                
            except Exception as e:
                logger.warning(f"Failed to use configured TTS provider: {e}, using fallback")
            
            # Fallback to legacy implementation
            # TODO: Implement TTS integration
            # - Connect to OpenAI TTS, ElevenLabs, or Azure
            # - Generate high-quality audio
            # - Handle different voices and speeds
            
            # Placeholder implementation
            # Return empty audio data
            return b""
            
        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}")
            raise AIGenerationError(f"Failed to generate TTS audio: {e}")
    
    async def get_available_voices(self) -> list:
        """Get list of available voices"""
        # TODO: Implement voice listing
        return [
            {"id": "alloy", "name": "Alloy", "language": "en"},
            {"id": "echo", "name": "Echo", "language": "en"},
            {"id": "fable", "name": "Fable", "language": "en"},
            {"id": "onyx", "name": "Onyx", "language": "en"},
            {"id": "nova", "name": "Nova", "language": "en"},
            {"id": "shimmer", "name": "Shimmer", "language": "en"}
        ]

class ContentEditor:
    """Content editing and synchronization service"""
    
    async def edit_speaker_notes(self, lesson_id: str, slide_id: int, new_notes: str) -> bool:
        """Edit speaker notes for a slide"""
        try:
            logger.info(f"Editing speaker notes for lesson {lesson_id}, slide {slide_id}")
            
            # TODO: Implement speaker notes editing
            # - Update manifest.json
            # - Regenerate audio if needed
            # - Update visual cues
            
            return True
            
        except Exception as e:
            logger.error(f"Error editing speaker notes: {e}")
            raise AIGenerationError(f"Failed to edit speaker notes: {e}")
    
    async def edit_audio_timing(self, lesson_id: str, slide_id: int, timing_data: Dict[str, Any]) -> bool:
        """Edit audio timing and synchronization"""
        try:
            logger.info(f"Editing audio timing for lesson {lesson_id}, slide {slide_id}")
            
            # TODO: Implement timing editing
            # - Update cue timestamps
            # - Resynchronize visual effects
            # - Validate timing consistency
            
            return True
            
        except Exception as e:
            logger.error(f"Error editing audio timing: {e}")
            raise AIGenerationError(f"Failed to edit audio timing: {e}")
    
    async def preview_changes(self, lesson_id: str, slide_id: int) -> Dict[str, Any]:
        """Preview changes before applying"""
        try:
            logger.info(f"Previewing changes for lesson {lesson_id}, slide {slide_id}")
            
            # TODO: Implement preview functionality
            # - Generate preview audio
            # - Show timing adjustments
            # - Allow rollback
            
            return {
                "preview_audio_url": f"/preview/{lesson_id}/{slide_id}/audio.mp3",
                "timing_changes": [],
                "visual_changes": []
            }
            
        except Exception as e:
            logger.error(f"Error previewing changes: {e}")
            raise AIGenerationError(f"Failed to preview changes: {e}")