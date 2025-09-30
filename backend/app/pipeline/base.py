"""Base pipeline interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class BasePipeline(ABC):
    """Base class for all processing pipelines"""
    
    def __init__(self):
        self.logger = logger
    
    @abstractmethod
    def ingest(self, lesson_dir: str) -> None:
        """Process uploaded document and extract slides"""
        pass
    
    @abstractmethod
    def plan(self, lesson_dir: str) -> None:
        """Generate lecture plan and speaker notes"""
        pass
    
    @abstractmethod
    def tts(self, lesson_dir: str) -> None:
        """Generate audio files and timing data"""
        pass
    
    @abstractmethod
    def build_manifest(self, lesson_dir: str) -> None:
        """Build final manifest.json with all data"""
        pass
    
    def process_full_pipeline(self, lesson_dir: str) -> Dict[str, Any]:
        """Run complete pipeline processing"""
        try:
            self.logger.info(f"Starting {self.__class__.__name__} pipeline for {lesson_dir}")
            
            # Run pipeline steps
            self.ingest(lesson_dir)
            self.plan(lesson_dir)
            self.tts(lesson_dir)
            self.build_manifest(lesson_dir)
            
            self.logger.info(f"Completed {self.__class__.__name__} pipeline for {lesson_dir}")
            
            return {
                "status": "success",
                "pipeline": self.__class__.__name__,
                "lesson_dir": lesson_dir
            }
            
        except Exception as e:
            self.logger.error(f"Pipeline error in {self.__class__.__name__}: {e}")
            raise
    
    def load_manifest(self, lesson_dir: str) -> Dict[str, Any]:
        """Load existing manifest.json"""
        manifest_path = Path(lesson_dir) / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_manifest(self, lesson_dir: str, manifest: Dict[str, Any]) -> None:
        """Save manifest.json"""
        manifest_path = Path(lesson_dir) / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved manifest: {manifest_path}")
    
    def ensure_directories(self, lesson_dir: str) -> None:
        """Ensure required directories exist"""
        lesson_path = Path(lesson_dir)
        lesson_path.mkdir(exist_ok=True)
        (lesson_path / "slides").mkdir(exist_ok=True)
        (lesson_path / "audio").mkdir(exist_ok=True)