"""
Unit tests for Pipeline Base Class
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import json


class TestBasePipeline:
    """Test BasePipeline abstract class"""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        from app.pipeline.base import BasePipeline
        
        # Create concrete implementation
        class ConcretePipeline(BasePipeline):
            def ingest(self, lesson_dir: str): pass
            def plan(self, lesson_dir: str): pass
            def tts(self, lesson_dir: str): pass
            def build_manifest(self, lesson_dir: str): pass
        
        pipeline = ConcretePipeline()
        assert pipeline.logger is not None
    
    def test_load_manifest(self, temp_dir):
        """Test loading manifest"""
        from app.pipeline.base import BasePipeline
        
        class ConcretePipeline(BasePipeline):
            def ingest(self, lesson_dir: str): pass
            def plan(self, lesson_dir: str): pass
            def tts(self, lesson_dir: str): pass
            def build_manifest(self, lesson_dir: str): pass
        
        pipeline = ConcretePipeline()
        
        # Create test manifest
        manifest_data = {
            "slides": [{"id": 1, "image": "test.png"}],
            "metadata": {"stage": "test"}
        }
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        # Load manifest
        loaded = pipeline.load_manifest(str(temp_dir))
        
        assert loaded == manifest_data
        assert loaded["slides"][0]["id"] == 1
    
    def test_load_manifest_not_found(self, temp_dir):
        """Test loading non-existent manifest"""
        from app.pipeline.base import BasePipeline
        
        class ConcretePipeline(BasePipeline):
            def ingest(self, lesson_dir: str): pass
            def plan(self, lesson_dir: str): pass
            def tts(self, lesson_dir: str): pass
            def build_manifest(self, lesson_dir: str): pass
        
        pipeline = ConcretePipeline()
        
        with pytest.raises(FileNotFoundError):
            pipeline.load_manifest(str(temp_dir))
    
    def test_save_manifest(self, temp_dir):
        """Test saving manifest"""
        from app.pipeline.base import BasePipeline
        
        class ConcretePipeline(BasePipeline):
            def ingest(self, lesson_dir: str): pass
            def plan(self, lesson_dir: str): pass
            def tts(self, lesson_dir: str): pass
            def build_manifest(self, lesson_dir: str): pass
        
        pipeline = ConcretePipeline()
        
        # Save manifest
        manifest_data = {
            "slides": [{"id": 1, "image": "test.png"}],
            "metadata": {"stage": "saved"}
        }
        pipeline.save_manifest(str(temp_dir), manifest_data)
        
        # Check file exists
        manifest_path = temp_dir / "manifest.json"
        assert manifest_path.exists()
        
        # Load and verify
        loaded = json.loads(manifest_path.read_text())
        assert loaded == manifest_data
    
    def test_ensure_directories(self, temp_dir):
        """Test ensuring required directories exist"""
        from app.pipeline.base import BasePipeline
        
        class ConcretePipeline(BasePipeline):
            def ingest(self, lesson_dir: str): pass
            def plan(self, lesson_dir: str): pass
            def tts(self, lesson_dir: str): pass
            def build_manifest(self, lesson_dir: str): pass
        
        pipeline = ConcretePipeline()
        
        lesson_dir = temp_dir / "test_lesson"
        pipeline.ensure_directories(str(lesson_dir))
        
        assert lesson_dir.exists()
        assert (lesson_dir / "slides").exists()
        assert (lesson_dir / "audio").exists()
    
    def test_process_full_pipeline_with_callback(self, temp_dir):
        """Test full pipeline processing with progress callback"""
        from app.pipeline.base import BasePipeline
        
        # Track progress calls
        progress_calls = []
        
        def progress_callback(stage: str, progress: int, message: str):
            progress_calls.append({"stage": stage, "progress": progress, "message": message})
        
        class ConcretePipeline(BasePipeline):
            def ingest(self, lesson_dir: str):
                # Create minimal manifest
                manifest = {"slides": [{"id": 1}], "metadata": {}}
                self.save_manifest(lesson_dir, manifest)
            
            def plan(self, lesson_dir: str):
                manifest = self.load_manifest(lesson_dir)
                manifest["slides"][0]["speaker_notes"] = "Test notes"
                self.save_manifest(lesson_dir, manifest)
            
            def tts(self, lesson_dir: str):
                manifest = self.load_manifest(lesson_dir)
                manifest["slides"][0]["audio"] = "/test/audio.wav"
                self.save_manifest(lesson_dir, manifest)
            
            def build_manifest(self, lesson_dir: str):
                manifest = self.load_manifest(lesson_dir)
                manifest["slides"][0]["cues"] = []
                self.save_manifest(lesson_dir, manifest)
        
        pipeline = ConcretePipeline()
        result = pipeline.process_full_pipeline(str(temp_dir), progress_callback)
        
        assert result["status"] == "success"
        assert result["lesson_dir"] == str(temp_dir)
        
        # Check progress callbacks were called
        assert len(progress_calls) >= 4
        assert progress_calls[0]["stage"] == "parsing"
        assert progress_calls[-1]["stage"] == "generating_cues"


class TestPipelineErrorHandling:
    """Test pipeline error handling"""
    
    def test_pipeline_error_propagation(self, temp_dir):
        """Test that errors are properly propagated"""
        from app.pipeline.base import BasePipeline
        
        class FailingPipeline(BasePipeline):
            def ingest(self, lesson_dir: str):
                raise ValueError("Ingest failed")
            
            def plan(self, lesson_dir: str): pass
            def tts(self, lesson_dir: str): pass
            def build_manifest(self, lesson_dir: str): pass
        
        pipeline = FailingPipeline()
        
        with pytest.raises(ValueError, match="Ingest failed"):
            pipeline.process_full_pipeline(str(temp_dir))
    
    def test_pipeline_partial_failure_handling(self, temp_dir):
        """Test handling of partial pipeline failures"""
        from app.pipeline.base import BasePipeline
        
        class PartialFailurePipeline(BasePipeline):
            def ingest(self, lesson_dir: str):
                manifest = {"slides": [{"id": 1}], "metadata": {}}
                self.save_manifest(lesson_dir, manifest)
            
            def plan(self, lesson_dir: str):
                raise RuntimeError("Planning failed")
            
            def tts(self, lesson_dir: str): pass
            def build_manifest(self, lesson_dir: str): pass
        
        pipeline = PartialFailurePipeline()
        
        with pytest.raises(RuntimeError, match="Planning failed"):
            pipeline.process_full_pipeline(str(temp_dir))
        
        # Check that ingest completed
        manifest_path = temp_dir / "manifest.json"
        assert manifest_path.exists()


class TestPipelineIntegration:
    """Test pipeline integration with services"""
    
    @pytest.mark.asyncio
    async def test_pipeline_with_mock_services(self, temp_dir, sample_png):
        """Test pipeline with mocked services"""
        from app.pipeline.base import BasePipeline
        
        class MockServicePipeline(BasePipeline):
            def __init__(self):
                super().__init__()
                self.ocr_called = False
                self.llm_called = False
                self.tts_called = False
            
            def ingest(self, lesson_dir: str):
                self.ocr_called = True
                manifest = {
                    "slides": [{"id": 1, "image": "test.png", "elements": []}],
                    "metadata": {}
                }
                self.save_manifest(lesson_dir, manifest)
            
            def plan(self, lesson_dir: str):
                self.llm_called = True
                manifest = self.load_manifest(lesson_dir)
                manifest["slides"][0]["speaker_notes"] = "Generated notes"
                self.save_manifest(lesson_dir, manifest)
            
            def tts(self, lesson_dir: str):
                self.tts_called = True
                manifest = self.load_manifest(lesson_dir)
                manifest["slides"][0]["audio"] = "/test/audio.wav"
                manifest["slides"][0]["duration"] = 10.0
                self.save_manifest(lesson_dir, manifest)
            
            def build_manifest(self, lesson_dir: str):
                manifest = self.load_manifest(lesson_dir)
                manifest["slides"][0]["cues"] = []
                self.save_manifest(lesson_dir, manifest)
        
        pipeline = MockServicePipeline()
        result = pipeline.process_full_pipeline(str(temp_dir))
        
        assert result["status"] == "success"
        assert pipeline.ocr_called
        assert pipeline.llm_called
        assert pipeline.tts_called
        
        # Verify final manifest
        manifest = pipeline.load_manifest(str(temp_dir))
        assert len(manifest["slides"]) == 1
        assert manifest["slides"][0]["speaker_notes"] == "Generated notes"
        assert manifest["slides"][0]["audio"] == "/test/audio.wav"
