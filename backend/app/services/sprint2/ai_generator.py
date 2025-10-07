"""Sprint 2: AI content generation service with anti-reading logic"""
import logging
from typing import Optional, Dict, Any, List, Tuple
import json
import subprocess
from pathlib import Path

from ...core.exceptions import AIGenerationError
from ...core.config import settings
from .concept_extractor import (
    extract_slide_concepts, 
    check_anti_reading, 
    generate_lecture_outline,
    SlideConcepts,
    AntiReadingDetector
)

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
    """AI content generation service with anti-reading logic"""
    
    def __init__(self):
        self.openai_key = settings.OPENAI_API_KEY
        self.anthropic_key = settings.ANTHROPIC_API_KEY
        self.anti_reading_threshold = 0.35
        self.min_inference_ratio = 0.5
        
    async def generate_lecture_outline(self, lecture_title: str, slide_concepts: List[SlideConcepts]) -> Dict[str, Any]:
        """Generate lecture outline for coherence"""
        try:
            logger.info(f"Generating lecture outline for: {lecture_title}")
            
            # Use the new outline generator
            outline = generate_lecture_outline(lecture_title, slide_concepts)
            
            logger.info(f"Generated outline with {len(outline['outline'])} goals")
            return outline
            
        except Exception as e:
            logger.error(f"Error generating lecture outline: {e}")
            raise AIGenerationError(f"Failed to generate lecture outline: {e}")
    
    async def generate_speaker_notes(self, 
                                   slide_content: List[Dict[str, Any]], 
                                   course_title: str = "",
                                   lecture_title: str = "",
                                   slide_index: int = 0,
                                   total_slides: int = 1,
                                   prev_summary: str = "",
                                   audience_level: str = "undergrad",
                                   style_preset: str = "explanatory",
                                   lecture_outline: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate speaker notes using new anti-reading approach"""
        try:
            logger.info(f"Generating speaker notes for slide {slide_index + 1}/{total_slides}")
            
            # Extract concepts instead of raw text
            concepts = extract_slide_concepts(slide_content)
            
            # Get slide text for overlap detection
            slide_text = self._extract_slide_text(slide_content)
            
            # Generate talk track with anti-reading logic
            talk_track = await self._generate_talk_track_with_anti_reading(
                concepts, course_title, lecture_title, slide_index, total_slides,
                prev_summary, audience_level, style_preset, lecture_outline, slide_text
            )
            
            # Generate visual cues
            visual_cues = self._generate_visual_cues(talk_track, slide_content)
            
            # Combine into final result
            result = {
                "talk_track": talk_track,
                "visual_cues": visual_cues,
                "terms_to_define": concepts.terms_to_define,
                "concepts": {
                    "title": concepts.title,
                    "key_theses": concepts.key_theses,
                    "visual_insight": concepts.visual_insight
                }
            }
            
            logger.info(f"Generated speaker notes with {len(talk_track)} talk segments")
            return result
            
        except Exception as e:
            logger.error(f"Error generating speaker notes: {e}")
            raise AIGenerationError(f"Failed to generate speaker notes: {e}")
    
    async def _generate_talk_track_with_anti_reading(self, 
                                                    concepts: SlideConcepts,
                                                    course_title: str,
                                                    lecture_title: str,
                                                    slide_index: int,
                                                    total_slides: int,
                                                    prev_summary: str,
                                                    audience_level: str,
                                                    style_preset: str,
                                                    lecture_outline: Optional[Dict[str, Any]],
                                                    slide_text: str,
                                                    max_attempts: int = 3) -> List[Dict[str, Any]]:
        """Generate talk track with anti-reading detection and regeneration"""
        
        for attempt in range(max_attempts):
            try:
                # Build the new prompt
                prompt = self._build_lecture_prompt(
                    concepts, course_title, lecture_title, slide_index, total_slides,
                    prev_summary, audience_level, style_preset, lecture_outline
                )
                
                # Add anti-reading instruction if this is a retry
                if attempt > 0:
                    prompt += AntiReadingDetector().get_regeneration_prompt_addition()
                
                # Generate using configured LLM provider
                talk_track = await self._call_llm_for_talk_track(prompt)
                
                # Check for anti-reading violations
                generated_text = " ".join([segment["text"] for segment in talk_track])
                should_regenerate, overlap = check_anti_reading(generated_text, slide_text, self.anti_reading_threshold)
                
                if not should_regenerate:
                    logger.info(f"Generated talk track passed anti-reading check (overlap: {overlap:.3f})")
                    return talk_track
                else:
                    logger.warning(f"Talk track failed anti-reading check (overlap: {overlap:.3f}), attempt {attempt + 1}/{max_attempts}")
                    
            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1}: {e}")
                if attempt == max_attempts - 1:
                    raise
        
        # If all attempts failed, return fallback
        logger.warning("All anti-reading attempts failed, using fallback")
        return self._create_fallback_talk_track(concepts)
    
    def _build_lecture_prompt(self, 
                             concepts: SlideConcepts,
                             course_title: str,
                             lecture_title: str,
                             slide_index: int,
                             total_slides: int,
                             prev_summary: str,
                             audience_level: str,
                             style_preset: str,
                             lecture_outline: Optional[Dict[str, Any]]) -> str:
        """Build the new lecture prompt"""
        
        # Build concept list
        concept_list = []
        if concepts.title:
            concept_list.append(f"Title: {concepts.title}")
        concept_list.extend([f"Thesis: {thesis}" for thesis in concepts.key_theses])
        if concepts.visual_insight:
            concept_list.append(f"Visual insight: {concepts.visual_insight}")
        
        concept_list_str = "\n- ".join(concept_list) if concept_list else "General slide content"
        
        # Get current slide goal from outline
        current_goal = ""
        if lecture_outline and slide_index < len(lecture_outline.get("outline", [])):
            current_goal = lecture_outline["outline"][slide_index].get("goal", "")
        
        # Build the full prompt
        prompt = f"""
SYSTEM:
You are an expert lecturer. Your goal is to EXPLAIN concepts, not to read slides.

USER:
Course: "{course_title}"
Lecture: "{lecture_title}"
Previous slide summary (1–2 sentences): {prev_summary}
Current slide meta:
- slideIndex: {slide_index + 1}/{total_slides}
- concepts (from elements): {concept_list_str}
- figure/table insight (if any): {concepts.visual_insight or "None"}

Audience: {audience_level} (e.g., undergrad CS / teachers / managers)
Style: clear, calm, didactic; 1 analogy; 1 concrete example.
Current goal: {current_goal}

Constraints (must follow):
- DO NOT read or enumerate slide bullets.
- Avoid quoting slide text (>10–15 consecutive words).
- Speak at ~130–160 wpm; 45–90 seconds total.
- Use plain language, no jargon unless defined.
- Include: Hook → Core explanation → Example/Analogy → Contrast/Warning → Takeaway.
- End with 1 rhetorical check question.

Output STRICT JSON (no prose outside JSON):
{{
  "talk_track": [
    {{"kind":"hook", "text":"..."}},
    {{"kind":"core", "text":"..."}},
    {{"kind":"example", "text":"..."}},
    {{"kind":"contrast", "text":"..."}},
    {{"kind":"takeaway", "text":"..."}},
    {{"kind":"question", "text":"..."}}
  ],
  "visual_cues": [
    # optional, reference element ids to highlight while speaking
    {{"at":"hook","targetId":"{{element_id_or_slide_area}}"}},
    {{"at":"core","targetId":"..."}}
  ],
  "terms_to_define": ["term1","term2"]   # optional
}}
If you repeat slide wording, paraphrase.
"""
        return prompt
    
    async def _call_llm_for_talk_track(self, prompt: str) -> List[Dict[str, Any]]:
        """Call LLM to generate talk track"""
        try:
            from ...services.provider_factory import plan_slide_with_gemini
            
            # For now, use the existing provider but with new prompt structure
            # In a real implementation, this would call the LLM directly
            response = await self._call_llm_direct(prompt)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                return result.get("talk_track", [])
            except json.JSONDecodeError:
                logger.warning("LLM returned invalid JSON, using fallback")
                return self._create_fallback_talk_track(SlideConcepts())
                
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise
    
    async def _call_llm_direct(self, prompt: str) -> str:
        """Direct LLM call using configured provider"""
        try:
            from ...services.provider_factory import ProviderFactory

            # Get LLM provider
            llm_provider = ProviderFactory.get_llm_provider()

            # Check if we're using OpenRouter
            if hasattr(llm_provider, 'generate_lecture_text'):
                # OpenRouter uses synchronous method - just text, no elements needed
                # For prompt-based generation, we need to adapt
                logger.info("Using OpenRouter LLM provider")

                # Create a simple element structure for compatibility
                fake_elements = [{"text": prompt, "type": "text"}]
                response = llm_provider.generate_lecture_text(fake_elements)

                # Try to extract JSON from response
                # OpenRouter might return plain text, so wrap it as needed
                try:
                    # Try to parse as JSON first
                    json.loads(response)
                    return response
                except json.JSONDecodeError:
                    # If not JSON, create fallback structure
                    logger.warning("LLM returned non-JSON response, creating fallback")
                    return json.dumps({
                        "talk_track": [
                            {"kind": "hook", "text": response[:200] if len(response) > 200 else response}
                        ],
                        "visual_cues": [],
                        "terms_to_define": []
                    })
            else:
                # Fallback for other providers
                logger.warning("LLM provider doesn't support generate_lecture_text, using mock")
                return json.dumps({
                    "talk_track": [
                        {"kind": "hook", "text": "Let's explore this important concept together."},
                        {"kind": "core", "text": "This topic is fundamental to understanding the broader subject."}
                    ],
                    "visual_cues": [],
                    "terms_to_define": []
                })

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            # Return fallback
            return json.dumps({
                "talk_track": [
                    {"kind": "hook", "text": "Let's explore this important concept together."},
                    {"kind": "core", "text": "This topic is fundamental to understanding the broader subject."}
                ],
                "visual_cues": [],
                "terms_to_define": []
            })
    
    def _extract_slide_text(self, slide_content: List[Dict[str, Any]]) -> str:
        """Extract all text from slide for overlap detection"""
        text_parts = []
        for element in slide_content:
            if element.get('type') == 'text' and element.get('text'):
                text_parts.append(element['text'])
        return " ".join(text_parts)
    
    def _generate_visual_cues(self, talk_track: List[Dict[str, Any]], slide_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate visual cues based on talk track"""
        cues = []
        
        # Map talk track segments to visual elements
        for i, segment in enumerate(talk_track):
            if i < len(slide_content):
                element = slide_content[i]
                cue = {
                    "at": segment["kind"],
                    "targetId": element.get("id", f"element_{i}")
                }
                cues.append(cue)
        
        return cues
    
    def _create_fallback_talk_track(self, concepts: SlideConcepts) -> List[Dict[str, Any]]:
        """Create fallback talk track when LLM fails"""
        return [
            {"kind": "hook", "text": f"Let's discuss {concepts.title or 'this important topic'}."},
            {"kind": "core", "text": "This concept is essential for understanding the material."},
            {"kind": "example", "text": "Here's a practical example to illustrate the point."},
            {"kind": "contrast", "text": "It's important not to confuse this with similar concepts."},
            {"kind": "takeaway", "text": "The key takeaway is understanding the fundamental principles."},
            {"kind": "question", "text": "Does this make sense so far?"}
        ]
    
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