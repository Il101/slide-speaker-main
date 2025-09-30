"""Classic pipeline implementation - current production logic"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from .base import BasePipeline
from ..core.config import settings
from ..services.provider_factory import plan_slide_with_gemini, synthesize_slide_text_google

logger = logging.getLogger(__name__)

class ClassicPipeline(BasePipeline):
    """Classic pipeline using OCR + LLM + TTS (current production logic)"""
    
    def __init__(self):
        super().__init__()
        self.logger = logger
    
    def ingest(self, lesson_dir: str) -> None:
        """Process uploaded document and extract slides (OCR/Document AI)"""
        self.logger.info(f"ClassicPipeline: Starting ingest for {lesson_dir}")
        
        # This step is handled by the document parser in main.py
        # The manifest.json is already created with slides and elements
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
        # Load and validate manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        slides = manifest_data.get("slides", [])
        self.logger.info(f"ClassicPipeline: Found {len(slides)} slides in manifest")
        
        # Ensure directories exist
        self.ensure_directories(lesson_dir)
        
        self.logger.info(f"ClassicPipeline: Ingest completed for {lesson_dir}")
    
    def plan(self, lesson_dir: str) -> None:
        """Generate lecture plan and speaker notes using LLM"""
        self.logger.info(f"ClassicPipeline: Starting plan for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        # Process each slide with AI
        for slide in manifest_data["slides"]:
            slide_id = slide["id"]
            elements = slide.get("elements", [])
            
            self.logger.info(f"ClassicPipeline: Processing slide {slide_id}")
            
            # Generate speaker notes using LLM
            try:
                speaker_notes = plan_slide_with_gemini(elements)
                slide["speaker_notes"] = speaker_notes
                self.logger.info(f"✅ Generated {len(speaker_notes)} speaker notes for slide {slide_id}")
            except Exception as e:
                self.logger.error(f"❌ Failed to generate speaker notes for slide {slide_id}: {e}")
                slide["speaker_notes"] = []
            
            # Generate lecture text (fallback to speaker notes)
            try:
                if slide.get("speaker_notes"):
                    lecture_text = " ".join([note.get("text", "") for note in slide["speaker_notes"]])
                    slide["lecture_text"] = lecture_text
                    self.logger.info(f"✅ Generated lecture text for slide {slide_id}")
                else:
                    slide["lecture_text"] = "Let's discuss the content of this slide."
                    self.logger.info(f"✅ Used fallback lecture text for slide {slide_id}")
            except Exception as e:
                self.logger.error(f"❌ Failed to generate lecture text for slide {slide_id}: {e}")
                slide["lecture_text"] = "Let's discuss the content of this slide."
        
        # Save updated manifest
        self.save_manifest(lesson_dir, manifest_data)
        
        self.logger.info(f"ClassicPipeline: Plan completed for {lesson_dir}")
    
    def tts(self, lesson_dir: str) -> None:
        """Generate audio files and timing data using TTS"""
        self.logger.info(f"ClassicPipeline: Starting TTS for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        # Process each slide with TTS
        for slide in manifest_data["slides"]:
            slide_id = slide["id"]
            
            self.logger.info(f"ClassicPipeline: Generating audio for slide {slide_id}")
            
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
        
        self.logger.info(f"ClassicPipeline: TTS completed for {lesson_dir}")
    
    def build_manifest(self, lesson_dir: str) -> None:
        """Build final manifest.json with all data"""
        self.logger.info(f"ClassicPipeline: Building final manifest for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        # Add timeline with slide changes
        timeline = []
        current_time = 0.0
        
        for slide in manifest_data["slides"]:
            slide_id = slide["id"]
            duration = slide.get("duration", 0.0)
            
            if duration > 0:
                # Add slide change cue
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
        
        self.logger.info(f"ClassicPipeline: Final manifest built for {lesson_dir}")