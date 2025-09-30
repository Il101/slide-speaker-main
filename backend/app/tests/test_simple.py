import pytest
from unittest.mock import patch, MagicMock

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
    from app.core.config import settings
    from app.models.schemas import Manifest, Slide, SlideElement, Cue

class TestBasicFunctionality:
    """Test basic functionality without external dependencies"""
    
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

class TestSchemaValidation:
    """Test schema validation"""
    
    def test_slide_element_validation(self):
        """Test slide element validation"""
        element_data = {
            "id": "elem_1",
            "type": "text",
            "bbox": [100, 100, 200, 50],
            "text": "Test Text",
            "confidence": 0.95
        }
        
        element = SlideElement(**element_data)
        assert element.id == "elem_1"
        assert element.type == "text"
        assert element.bbox == [100, 100, 200, 50]
        assert element.text == "Test Text"
        assert element.confidence == 0.95
    
    def test_cue_validation(self):
        """Test cue validation"""
        cue_data = {
            "cue_id": "cue_1",
            "t0": 0.5,
            "t1": 2.0,
            "action": "highlight",
            "bbox": [100, 100, 200, 50],
            "element_id": "elem_1"
        }
        
        cue = Cue(**cue_data)
        assert cue.cue_id == "cue_1"
        assert cue.t0 == 0.5
        assert cue.t1 == 2.0
        assert cue.action == "highlight"
        assert cue.bbox == [100, 100, 200, 50]
        assert cue.element_id == "elem_1"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])