"""Vision pipeline implementation - multimodal LLM processing"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import BasePipeline
from .vision_planner import vision_plan_for_slide
from ..core.config import settings
from ..services.provider_factory import synthesize_slide_text_google

logger = logging.getLogger(__name__)

class VisionPipeline(BasePipeline):
    """Vision pipeline using multimodal LLM for slide analysis"""
    
    def __init__(self):
        super().__init__()
        self.logger = logger
    
    def ingest(self, lesson_dir: str) -> None:
        """Process uploaded document and extract slides (reuse existing rasterization)"""
        self.logger.info(f"VisionPipeline: Starting ingest for {lesson_dir}")
        
        # This step is handled by the document parser in main.py
        # The manifest.json is already created with slides and PNG images
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
        # Load and validate manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        slides = manifest_data.get("slides", [])
        self.logger.info(f"VisionPipeline: Found {len(slides)} slides in manifest")
        
        # Ensure directories exist
        self.ensure_directories(lesson_dir)
        
        self.logger.info(f"VisionPipeline: Ingest completed for {lesson_dir}")
    
    def plan(self, lesson_dir: str) -> None:
        """Generate lecture plan using vision LLM"""
        self.logger.info(f"VisionPipeline: Starting plan for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        course_title = manifest_data.get("course_title", "Presentation")
        lecture_title = manifest_data.get("lecture_title", "Lecture")
        
        # Process each slide with vision LLM
        for i, slide in enumerate(manifest_data["slides"]):
            slide_id = slide["id"]
            
            self.logger.info(f"VisionPipeline: Processing slide {slide_id}")
            
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
            
            try:
                # Call vision planner
                vision_result = vision_plan_for_slide(
                    slide_png_path=str(slide_image_path),
                    orig_size=orig_size,
                    course_title=course_title,
                    lecture_title=lecture_title,
                    prev_summary=prev_summary,
                    provider=settings.LLM_PROVIDER,
                    model=getattr(settings, 'VISION_MODEL', 'x-ai/grok-4-fast:free')
                )
                
                # Update slide with vision results
                slide["lecture_text"] = vision_result.get("lecture_text", "")
                slide["rough_elements"] = vision_result.get("rough_elements", [])
                slide["rough_cues"] = vision_result.get("rough_cues", [])
                
                self.logger.info(f"✅ Generated vision plan for slide {slide_id}")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to generate vision plan for slide {slide_id}: {e}")
                slide["lecture_text"] = "Let's discuss the content of this slide."
                slide["rough_elements"] = []
                slide["rough_cues"] = []
        
        # Save updated manifest
        self.save_manifest(lesson_dir, manifest_data)
        
        self.logger.info(f"VisionPipeline: Plan completed for {lesson_dir}")
    
    def tts(self, lesson_dir: str) -> None:
        """Generate audio files and timing data using TTS"""
        self.logger.info(f"VisionPipeline: Starting TTS for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        # Process each slide with TTS
        for slide in manifest_data["slides"]:
            slide_id = slide["id"]
            
            self.logger.info(f"VisionPipeline: Generating audio for slide {slide_id}")
            
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
        
        self.logger.info(f"VisionPipeline: TTS completed for {lesson_dir}")
    
    def build_manifest(self, lesson_dir: str) -> None:
        """Build final manifest.json with vision data"""
        self.logger.info(f"VisionPipeline: Building final manifest for {lesson_dir}")
        
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
            
            # Use rough elements as elements (if available)
            rough_elements = slide.get("rough_elements", [])
            if rough_elements:
                slide["elements"] = rough_elements
            else:
                # Fallback: create placeholder element
                slide["elements"] = [{
                    "id": "slide_area",
                    "type": "placeholder",
                    "bbox": [0, 0, slide.get("orig_size", {}).get("w", 1600), slide.get("orig_size", {}).get("h", 900)],
                    "text": "Slide area",
                    "confidence": 0.5
                }]
            
            # Use rough cues as cues
            rough_cues = slide.get("rough_cues", [])
            if rough_cues:
                slide["cues"] = rough_cues
            else:
                # Fallback: create slide change cue
                slide["cues"] = [{
                    "t0": 0.0,
                    "t1": duration,
                    "action": "slide_change",
                    "slide_id": slide_id
                }]
            
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
        
        self.logger.info(f"VisionPipeline: Final manifest built for {lesson_dir}")