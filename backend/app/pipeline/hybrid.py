"""Hybrid pipeline implementation - Vision + OCR alignment"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from .base import BasePipeline
from .vision_planner import vision_plan_for_slide
from .alignment import align_slide_elements, align_cues
from ..core.config import settings
from ..services.provider_factory import synthesize_slide_text_google

logger = logging.getLogger(__name__)

class HybridPipeline(BasePipeline):
    """Hybrid pipeline combining Vision LLM with OCR alignment"""
    
    def __init__(self):
        super().__init__()
        self.logger = logger
    
    def ingest(self, lesson_dir: str) -> None:
        """Process uploaded document and extract slides (OCR/Document AI)"""
        self.logger.info(f"HybridPipeline: Starting ingest for {lesson_dir}")
        
        # This step is handled by the document parser in main.py
        # The manifest.json is already created with slides and elements from OCR
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
        # Load and validate manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        slides = manifest_data.get("slides", [])
        self.logger.info(f"HybridPipeline: Found {len(slides)} slides in manifest")
        
        # Ensure directories exist
        self.ensure_directories(lesson_dir)
        
        self.logger.info(f"HybridPipeline: Ingest completed for {lesson_dir}")
    
    def plan(self, lesson_dir: str) -> None:
        """Generate lecture plan using vision LLM and align with OCR elements"""
        self.logger.info(f"HybridPipeline: Starting plan for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        course_title = manifest_data.get("course_title", "Presentation")
        lecture_title = manifest_data.get("lecture_title", "Lecture")
        
        # Process each slide with vision LLM and alignment
        for i, slide in enumerate(manifest_data["slides"]):
            slide_id = slide["id"]
            
            self.logger.info(f"HybridPipeline: Processing slide {slide_id}")
            
            # Get slide image path
            slide_image_path = lesson_path / "slides" / f"{slide_id:03d}.png"
            if not slide_image_path.exists():
                self.logger.warning(f"⚠️ Slide image not found: {slide_image_path}")
                continue
            
            # Get original slide size
            orig_size = slide.get("orig_size", {"w": 1600, "h": 900})
            
            # Get previous slide summary for context
            prev_summary = None
            if i > 0:
                prev_slide = manifest_data["slides"][i-1]
                prev_summary = prev_slide.get("lecture_text", "")
            
            # Get precise elements from OCR
            precise_elements = slide.get("elements", [])
            
            try:
                # Call vision planner
                vision_result = vision_plan_for_slide(
                    slide_png_path=str(slide_image_path),
                    orig_size=orig_size,
                    course_title=course_title,
                    lecture_title=lecture_title,
                    prev_summary=prev_summary,
                    provider=settings.LLM_PROVIDER,
                    model=getattr(settings, 'VISION_MODEL', 'gpt-4o-mini')
                )
                
                # Update slide with vision results
                slide["lecture_text"] = vision_result.get("lecture_text", "")
                slide["rough_elements"] = vision_result.get("rough_elements", [])
                slide["rough_cues"] = vision_result.get("rough_cues", [])
                
                # Align rough elements with precise OCR elements
                if precise_elements and slide["rough_elements"]:
                    aligned_elements, mapping = align_slide_elements(
                        slide["rough_elements"],
                        precise_elements
                    )
                    
                    # Update slide with aligned elements
                    slide["elements"] = aligned_elements
                    slide["element_mapping"] = mapping
                    
                    # Align cues to precise elements
                    if slide["rough_cues"]:
                        slide["cues"] = align_cues(slide["rough_cues"], mapping)
                    else:
                        slide["cues"] = []
                    
                    self.logger.info(f"✅ Aligned {len(aligned_elements)} elements for slide {slide_id}")
                else:
                    # Fallback: use precise elements if available, otherwise rough elements
                    if precise_elements:
                        slide["elements"] = precise_elements
                        slide["cues"] = []
                    else:
                        slide["elements"] = slide["rough_elements"]
                        slide["cues"] = slide["rough_cues"]
                    
                    self.logger.info(f"✅ Used fallback elements for slide {slide_id}")
                
                self.logger.info(f"✅ Generated hybrid plan for slide {slide_id}")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to generate hybrid plan for slide {slide_id}: {e}")
                slide["lecture_text"] = "Let's discuss the content of this slide."
                slide["elements"] = precise_elements  # Use OCR elements as fallback
                slide["cues"] = []
        
        # Save updated manifest
        self.save_manifest(lesson_dir, manifest_data)
        
        self.logger.info(f"HybridPipeline: Plan completed for {lesson_dir}")
    
    def tts(self, lesson_dir: str) -> None:
        """Generate audio files and timing data using TTS"""
        self.logger.info(f"HybridPipeline: Starting TTS for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        # Process each slide with TTS
        for slide in manifest_data["slides"]:
            slide_id = slide["id"]
            
            self.logger.info(f"HybridPipeline: Generating audio for slide {slide_id}")
            
            try:
                # Use lecture_text for TTS
                lecture_text = slide.get("lecture_text", "")
                if not lecture_text:
                    self.logger.warning(f"⚠️ No lecture text found for slide {slide_id}")
                    slide["audio"] = None
                    slide["duration"] = 0.0
                    continue
                
                # Generate audio using TTS
                audio_path, tts_words = synthesize_slide_text_google([lecture_text])
                
                # Verify audio file was created
                if not audio_path or not Path(audio_path).exists():
                    self.logger.error(f"❌ TTS failed to create audio file for slide {slide_id}")
                    slide["audio"] = None
                    slide["duration"] = 0.0
                    continue
                
                # Copy audio to lesson directory
                audio_dest = lesson_path / "audio" / f"{slide_id:03d}.wav"
                audio_dest.parent.mkdir(exist_ok=True)
                
                import shutil
                shutil.copy2(audio_path, audio_dest)
                
                # Verify file was copied successfully
                if not audio_dest.exists():
                    self.logger.error(f"❌ Failed to copy audio file for slide {slide_id}")
                    slide["audio"] = None
                    slide["duration"] = 0.0
                    continue
                
                # Update slide with audio info
                slide["audio"] = f"/assets/{Path(lesson_dir).name}/audio/{slide_id:03d}.wav"
                duration = tts_words.get("sentences", [{}])[-1].get("t1", 0.0) if tts_words.get("sentences") else 0.0
                slide["duration"] = duration
                
                # Save TTS words for timing
                tts_words_path = lesson_path / "audio" / f"{slide_id:03d}_words.json"
                with open(tts_words_path, "w", encoding="utf-8") as f:
                    json.dump(tts_words, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"✅ Generated audio for slide {slide_id}: {duration:.2f}s")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to generate audio for slide {slide_id}: {e}")
                slide["audio"] = None
                slide["duration"] = 0.0
        
        # Save updated manifest
        self.save_manifest(lesson_dir, manifest_data)
        
        self.logger.info(f"HybridPipeline: TTS completed for {lesson_dir}")
    
    def build_manifest(self, lesson_dir: str) -> None:
        """Build final manifest.json with hybrid data"""
        self.logger.info(f"HybridPipeline: Building final manifest for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        # Process each slide
        timeline = []
        current_time = 0.0
        
        for slide in manifest_data["slides"]:
            slide_id = slide["id"]
            duration = slide.get("duration", 0.0)
            
            # Ensure cues reference existing elements
            cues = slide.get("cues", [])
            elements = slide.get("elements", [])
            element_ids = {elem["id"] for elem in elements}
            
            # Filter cues to only reference existing elements
            valid_cues = []
            for cue in cues:
                if "targetId" in cue and cue["targetId"] in element_ids:
                    valid_cues.append(cue)
                elif "element_id" in cue and cue["element_id"] in element_ids:
                    valid_cues.append(cue)
                else:
                    # Skip cues that don't reference existing elements
                    self.logger.debug(f"Skipping cue with invalid target: {cue}")
            
            slide["cues"] = valid_cues
            
            # Add to timeline
            if duration > 0:
                timeline.append({
                    "t0": current_time,
                    "t1": current_time + duration,
                    "action": "slide_change",
                    "slide_id": slide_id
                })
                
                current_time += duration
        
        manifest_data["timeline"] = timeline
        
        # Save final manifest
        self.save_manifest(lesson_dir, manifest_data)
        
        self.logger.info(f"HybridPipeline: Final manifest built for {lesson_dir}")