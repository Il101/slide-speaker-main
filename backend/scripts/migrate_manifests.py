#!/usr/bin/env python3
"""
Migration script for slide-speaker manifests
Migrates existing manifests to ensure they have required fields for playback
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _placeholder_element():
    """Create a placeholder element for slides with no detected content"""
    return {
        "id": "slide_area",
        "type": "placeholder", 
        "text": "",
        "bbox": [0, 0, 1600, 900],
        "confidence": 1.0,
        "source": "fallback"
    }

def _probe_audio_duration(audio_path: str) -> float:
    """Get audio duration using ffprobe"""
    try:
        import subprocess
        result = subprocess.run([
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", audio_path
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return float(result.stdout.strip())
        else:
            logger.warning(f"ffprobe failed for {audio_path}: {result.stderr}")
            return 5.0  # Default duration
    except Exception as e:
        logger.warning(f"Could not get audio duration for {audio_path}: {e}")
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

def _build_simple_cues_for_slide(slide: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build simple cues for slide if none exist"""
    cues = []
    
    # If slide has audio, create simple highlight cues
    if slide.get("audio"):
        # Create a simple highlight for the entire slide area
        cue = {
            "t0": 0.0,
            "t1": 3.0,  # Default 3 seconds
            "action": "highlight",
            "targetId": "slide_area"
        }
        cues.append(cue)
    
    return _normalize_cues(cues)

def _inject_slide_changes(manifest: Dict[str, Any]) -> None:
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

def migrate_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate a single manifest to ensure playback compatibility"""
    logger.info("Starting manifest migration...")
    
    # Ensure slides exist
    if "slides" not in manifest:
        manifest["slides"] = []
        logger.warning("Added missing slides array")
    
    # Migrate each slide
    for i, slide in enumerate(manifest["slides"]):
        logger.info(f"Migrating slide {i+1}...")
        
        # Ensure elements exist and are not empty
        if "elements" not in slide or not slide["elements"]:
            slide["elements"] = [_placeholder_element()]
            logger.info(f"Added placeholder element to slide {i+1}")
        
        # Ensure cues exist
        if "cues" not in slide or not slide["cues"]:
            slide["cues"] = _build_simple_cues_for_slide(slide)
            logger.info(f"Added simple cues to slide {i+1}")
        
        # Ensure lecture_text exists
        if "lecture_text" not in slide:
            # Try to build from speaker_notes
            if slide.get("speaker_notes"):
                lecture_text = " ".join(note.get("text", "") for note in slide["speaker_notes"] if note.get("text"))
                slide["lecture_text"] = lecture_text
                logger.info(f"Added lecture_text to slide {i+1}")
            else:
                slide["lecture_text"] = f"Slide {i+1} content"
                logger.info(f"Added default lecture_text to slide {i+1}")
        
        # Ensure audio path is MP3
        if slide.get("audio") and not slide["audio"].endswith(".mp3"):
            # Convert .wav to .mp3 path
            if slide["audio"].endswith(".wav"):
                slide["audio"] = slide["audio"].replace(".wav", ".mp3")
                logger.info(f"Updated audio path to MP3 for slide {i+1}")
    
    # Inject slide changes into timeline
    if "timeline" not in manifest or not manifest["timeline"]:
        _inject_slide_changes(manifest)
        logger.info("Added timeline with slide_change events")
    
    logger.info("Manifest migration completed successfully")
    return manifest

def migrate_manifest_file(file_path: Path, backup: bool = True) -> bool:
    """Migrate a single manifest file"""
    try:
        # Read manifest
        with open(file_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Create backup if requested
        if backup:
            backup_path = file_path.with_suffix('.json.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            logger.info(f"Created backup: {backup_path}")
        
        # Migrate manifest
        migrated_manifest = migrate_manifest(manifest)
        
        # Write migrated manifest
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(migrated_manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully migrated: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to migrate {file_path}: {e}")
        return False

def find_manifest_files(data_dir: Path) -> List[Path]:
    """Find all manifest files in data directory"""
    manifest_files = []
    
    # Look for manifest.json files in lesson directories
    for lesson_dir in data_dir.iterdir():
        if lesson_dir.is_dir():
            manifest_file = lesson_dir / "manifest.json"
            if manifest_file.exists():
                manifest_files.append(manifest_file)
    
    return manifest_files

def main():
    parser = argparse.ArgumentParser(description='Migrate slide-speaker manifests for playback compatibility')
    parser.add_argument('--data-dir', type=str, default='.data', help='Data directory path')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without making changes')
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        sys.exit(1)
    
    # Find manifest files
    manifest_files = find_manifest_files(data_dir)
    
    if not manifest_files:
        logger.warning("No manifest files found")
        sys.exit(0)
    
    logger.info(f"Found {len(manifest_files)} manifest files")
    
    # Migrate each file
    success_count = 0
    for manifest_file in manifest_files:
        if args.dry_run:
            logger.info(f"Would migrate: {manifest_file}")
            success_count += 1
        else:
            if migrate_manifest_file(manifest_file, backup=not args.no_backup):
                success_count += 1
    
    logger.info(f"Migration completed: {success_count}/{len(manifest_files)} files processed successfully")
    
    if success_count == len(manifest_files):
        logger.info("All manifests migrated successfully!")
        sys.exit(0)
    else:
        logger.error("Some manifests failed to migrate")
        sys.exit(1)

if __name__ == "__main__":
    main()