import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import json

# Mock all external dependencies before importing
with patch.dict('sys.modules', {
    'pymupdf': MagicMock(),
    'pptx': MagicMock(),
    'easyocr': MagicMock(),
    'cv2': MagicMock(),
    'PIL': MagicMock(),
    'moviepy': MagicMock(),
    'celery': MagicMock(),
    'redis': MagicMock(),
    'boto3': MagicMock(),
    'google.cloud': MagicMock(),
    'openai': MagicMock(),
    'anthropic': MagicMock(),
}):
    from app.main import app
    from app.core.config import settings
    from app.models.schemas import Manifest, Slide, SlideElement, Cue

class TestBasicFunctionality:
    """Test basic functionality without external dependencies"""
    
    def test_app_creation(self):
        """Test that FastAPI app is created successfully"""
        assert app is not None
        assert app.title == "Slide Speaker API"
    
    def test_settings_initialization(self):
        """Test settings initialization"""
        assert settings.API_TITLE == "Slide Speaker API"
        assert settings.API_VERSION == "1.0.0"
        assert settings.MAX_FILE_SIZE > 0
        assert ".pptx" in settings.ALLOWED_EXTENSIONS
        assert ".pdf" in settings.ALLOWED_EXTENSIONS
    
    def test_data_directories_creation(self):
        """Test that data directories are created"""
        assert settings.DATA_DIR.exists()
        assert settings.UPLOAD_DIR.exists()
        assert settings.ASSETS_DIR.exists()
        assert settings.EXPORTS_DIR.exists()

class TestManifestValidation:
    """Test manifest validation"""
    
    def test_valid_manifest_structure(self):
        """Test valid manifest structure"""
        manifest_data = {
            "slides": [
                {
                    "id": 1,
                    "image": "/assets/test/slides/001.png",
                    "audio": "/assets/test/audio/001.mp3",
                    "elements": [
                        {
                            "id": "elem_1",
                            "type": "text",
                            "bbox": [100, 100, 200, 50],
                            "text": "Test Text",
                            "confidence": 0.95
                        }
                    ],
                    "cues": [
                        {
                            "cue_id": "cue_1",
                            "t0": 0.5,
                            "t1": 2.0,
                            "action": "highlight",
                            "bbox": [100, 100, 200, 50],
                            "element_id": "elem_1"
                        }
                    ]
                }
            ],
            "timeline": {
                "rules": [],
                "default_duration": 2.0,
                "transition_duration": 0.5,
                "min_highlight_duration": 0.8,
                "min_gap": 0.2,
                "max_total_duration": 90.0,
                "smoothness_enabled": True
            }
        }
        
        manifest = Manifest(**manifest_data)
        assert manifest is not None
        assert len(manifest.slides) == 1
        assert manifest.timeline is not None
        assert manifest.timeline.smoothness_enabled is True

class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "slide-speaker-api"}
    
    def test_demo_manifest_endpoint(self):
        """Test demo manifest endpoint"""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/lessons/demo-lesson/manifest")
        
        assert response.status_code == 200
        data = response.json()
        assert "slides" in data
        assert len(data["slides"]) > 0
        assert "timeline" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])