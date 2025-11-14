"""
Comprehensive unit tests for SemanticAnalyzer
Testing: semantic analysis, multimodal vision, hallucination detection
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from typing import Dict, Any, List


@pytest.fixture
def mock_llm_worker():
    """Mock LLM worker for testing"""
    worker = Mock()
    worker.generate = Mock(return_value=json.dumps({
        "slide_type": "content_slide",
        "groups": [
            {
                "id": "group_0",
                "name": "Title",
                "type": "title",
                "priority": "high",
                "element_ids": ["elem_0"],
                "reading_order": [1],
                "educational_intent": "Introduce topic",
                "highlight_strategy": {
                    "when": "start",
                    "effect_type": "spotlight",
                    "duration": 2.5,
                    "intensity": "dramatic"
                },
                "dependencies": {
                    "highlight_before": None,
                    "highlight_together_with": None,
                    "highlight_after": None
                }
            }
        ],
        "noise_elements": [],
        "visual_density": "medium",
        "cognitive_load": "medium"
    }))
    return worker


@pytest.fixture
def sample_ocr_elements():
    """Sample OCR elements for testing"""
    return [
        {
            "id": "elem_0",
            "type": "text",
            "text": "Introduction to Machine Learning",
            "bbox": [100, 100, 800, 200],
            "confidence": 0.95
        },
        {
            "id": "elem_1",
            "type": "text",
            "text": "Key concepts and applications",
            "bbox": [100, 300, 700, 400],
            "confidence": 0.92
        },
        {
            "id": "elem_2",
            "type": "text",
            "text": "© 2024 Company",
            "bbox": [50, 900, 200, 950],
            "confidence": 0.88
        }
    ]


@pytest.fixture
def sample_presentation_context():
    """Sample presentation context"""
    return {
        "theme": "Technical Education",
        "level": "undergraduate",
        "presentation_style": "academic",
        "total_slides": 10,
        "detected_language": "en"
    }


class TestSemanticAnalyzerInitialization:
    """Test SemanticAnalyzer initialization"""
    
    def test_init_with_valid_llm_provider(self):
        """Test initialization with valid LLM provider"""
        with patch('app.services.semantic_analyzer.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = Mock()
            
            from app.services.semantic_analyzer import SemanticAnalyzer
            
            analyzer = SemanticAnalyzer()
            
            assert analyzer is not None
            assert analyzer.use_mock is False
            assert analyzer.llm_worker is not None
    
    def test_init_with_failed_llm_provider(self):
        """Test initialization when LLM provider fails"""
        with patch('app.services.semantic_analyzer.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.side_effect = Exception("Provider unavailable")
            
            from app.services.semantic_analyzer import SemanticAnalyzer
            
            analyzer = SemanticAnalyzer()
            
            assert analyzer is not None
            assert analyzer.use_mock is True
            assert analyzer.llm_worker is None


class TestSemanticAnalyzerAnalyzeSlide:
    """Test analyze_slide method"""
    
    @pytest.mark.asyncio
    async def test_analyze_slide_success(
        self,
        mock_llm_worker,
        sample_ocr_elements,
        sample_presentation_context,
        tmp_path
    ):
        """Test successful slide analysis"""
        # Create test image
        test_image = tmp_path / "test_slide.png"
        test_image.write_bytes(b"fake_image_data")
        
        with patch('app.services.semantic_analyzer.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = mock_llm_worker
            
            from app.services.semantic_analyzer import SemanticAnalyzer
            
            analyzer = SemanticAnalyzer()
            analyzer.llm_worker = mock_llm_worker
            analyzer.use_mock = False
            
            result = await analyzer.analyze_slide(
                str(test_image),
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Verify result structure
            assert result is not None
            assert "groups" in result
            assert "slide_type" in result
            assert len(result["groups"]) > 0
            
            # Verify group structure
            group = result["groups"][0]
            assert "id" in group
            assert "priority" in group
            assert "element_ids" in group
            assert "highlight_strategy" in group
            
            # Verify LLM was called
            mock_llm_worker.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_slide_with_previous_context(
        self,
        mock_llm_worker,
        sample_ocr_elements,
        sample_presentation_context,
        tmp_path
    ):
        """Test analysis with previous slides context"""
        test_image = tmp_path / "test_slide.png"
        test_image.write_bytes(b"fake_image_data")
        
        previous_slides = [
            {
                "id": 1,
                "elements": [{"text": "Previous slide content"}],
                "semantic_map": {"groups": []}
            }
        ]
        
        with patch('app.services.semantic_analyzer.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = mock_llm_worker
            
            from app.services.semantic_analyzer import SemanticAnalyzer
            
            analyzer = SemanticAnalyzer()
            analyzer.llm_worker = mock_llm_worker
            analyzer.use_mock = False
            
            result = await analyzer.analyze_slide(
                str(test_image),
                sample_ocr_elements,
                sample_presentation_context,
                previous_slides=previous_slides,
                slide_index=1
            )
            
            assert result is not None
            assert "groups" in result
    
    @pytest.mark.asyncio
    async def test_analyze_slide_with_invalid_json_response(
        self,
        sample_ocr_elements,
        sample_presentation_context,
        tmp_path
    ):
        """Test handling of invalid JSON from LLM"""
        test_image = tmp_path / "test_slide.png"
        test_image.write_bytes(b"fake_image_data")
        
        # Mock LLM that returns invalid JSON
        bad_llm_worker = Mock()
        bad_llm_worker.generate = Mock(return_value="This is not valid JSON")
        
        with patch('app.services.semantic_analyzer.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = bad_llm_worker
            
            from app.services.semantic_analyzer import SemanticAnalyzer
            
            analyzer = SemanticAnalyzer()
            analyzer.llm_worker = bad_llm_worker
            analyzer.use_mock = False
            
            result = await analyzer.analyze_slide(
                str(test_image),
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Should fall back to mock mode
            assert result is not None
            assert result.get("mock") is True
            assert "groups" in result
    
    @pytest.mark.asyncio
    async def test_analyze_slide_with_exception(
        self,
        sample_ocr_elements,
        sample_presentation_context,
        tmp_path
    ):
        """Test handling of exceptions during analysis"""
        test_image = tmp_path / "test_slide.png"
        test_image.write_bytes(b"fake_image_data")
        
        # Mock LLM that raises exception
        bad_llm_worker = Mock()
        bad_llm_worker.generate = Mock(side_effect=Exception("API Error"))
        
        with patch('app.services.semantic_analyzer.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = bad_llm_worker
            
            from app.services.semantic_analyzer import SemanticAnalyzer
            
            analyzer = SemanticAnalyzer()
            analyzer.llm_worker = bad_llm_worker
            analyzer.use_mock = False
            
            result = await analyzer.analyze_slide(
                str(test_image),
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Should fall back to mock mode
            assert result is not None
            assert result.get("mock") is True
    
    @pytest.mark.asyncio
    async def test_analyze_slide_mock_mode(
        self,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test analysis in mock mode (no LLM)"""
        with patch('app.services.semantic_analyzer.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.side_effect = Exception("No provider")
            
            from app.services.semantic_analyzer import SemanticAnalyzer
            
            analyzer = SemanticAnalyzer()
            
            result = await analyzer.analyze_slide(
                "/fake/path.png",
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Should return mock result
            assert result is not None
            assert result.get("mock") is True
            assert "groups" in result
            assert len(result["groups"]) > 0


class TestSemanticAnalyzerHelperMethods:
    """Test helper methods"""
    
    def test_encode_image(self, tmp_path):
        """Test image encoding to base64"""
        from app.services.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        # Create test image
        test_image = tmp_path / "test.png"
        test_content = b"fake_png_data"
        test_image.write_bytes(test_content)
        
        result = analyzer._encode_image(str(test_image))
        
        assert result is not None
        assert isinstance(result, str)
        # Verify it's base64 encoded
        import base64
        decoded = base64.b64decode(result)
        assert decoded == test_content
    
    def test_prepare_ocr_summary(self, sample_ocr_elements):
        """Test OCR summary preparation"""
        from app.services.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        summary = analyzer._prepare_ocr_summary(sample_ocr_elements)
        
        assert summary is not None
        assert isinstance(summary, str)
        assert "elem_0" in summary
        assert "Introduction" in summary
    
    def test_prepare_ocr_summary_with_many_elements(self):
        """Test OCR summary with >20 elements (should truncate)"""
        from app.services.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        # Create 30 elements
        many_elements = [
            {
                "id": f"elem_{i}",
                "text": f"Text {i}",
                "bbox": [0, 0, 100, 100],
                "type": "text"
            }
            for i in range(30)
        ]
        
        summary = analyzer._prepare_ocr_summary(many_elements)
        
        assert summary is not None
        # Should only include first 20
        assert "elem_19" in summary
        assert "elem_20" not in summary


class TestSemanticAnalyzerPromptGeneration:
    """Test prompt generation"""
    
    def test_create_semantic_analysis_prompt(
        self,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test semantic analysis prompt creation"""
        from app.services.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        ocr_summary = analyzer._prepare_ocr_summary(sample_ocr_elements)
        
        prompt = analyzer._create_semantic_analysis_prompt(
            ocr_summary,
            sample_presentation_context,
            previous_slides=None,
            slide_index=0
        )
        
        assert prompt is not None
        assert isinstance(prompt, str)
        
        # Verify key elements in prompt
        assert "semantic map" in prompt.lower()
        assert "groups" in prompt.lower()
        assert sample_presentation_context["theme"] in prompt
        assert "JSON" in prompt
    
    def test_prompt_includes_few_shot_examples(
        self,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test that prompt includes few-shot examples"""
        from app.services.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        ocr_summary = analyzer._prepare_ocr_summary(sample_ocr_elements)
        
        prompt = analyzer._create_semantic_analysis_prompt(
            ocr_summary,
            sample_presentation_context,
            previous_slides=None,
            slide_index=0
        )
        
        # Check for few-shot examples
        assert "Example" in prompt or "example" in prompt
        assert "Title Slide" in prompt or "Content with List" in prompt


class TestSemanticAnalyzerMockMode:
    """Test mock mode functionality"""
    
    def test_analyze_slide_mock_with_large_elements(
        self,
        sample_presentation_context
    ):
        """Test mock analysis with large elements"""
        from app.services.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        # Large element (title)
        large_element = {
            "id": "elem_0",
            "text": "Big Title",
            "bbox": [100, 100, 800, 300],  # Large bbox
            "type": "text"
        }
        
        result = analyzer._analyze_slide_mock(
            [large_element],
            sample_presentation_context,
            slide_index=0
        )
        
        assert result is not None
        assert result["mock"] is True
        assert len(result["groups"]) > 0
        
        # Large element should be classified as title
        group = result["groups"][0]
        assert group["type"] == "title"
        assert group["priority"] == "high"
    
    def test_analyze_slide_mock_detects_noise(
        self,
        sample_presentation_context
    ):
        """Test mock analysis detects noise elements"""
        from app.services.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        # Watermark element
        watermark = {
            "id": "elem_watermark",
            "text": "© 2024",
            "bbox": [50, 950, 150, 1000],  # Bottom of slide, small
            "type": "text"
        }
        
        content_elem = {
            "id": "elem_content",
            "text": "Main content here",
            "bbox": [100, 400, 800, 500],
            "type": "text"
        }
        
        result = analyzer._analyze_slide_mock(
            [content_elem, watermark],
            sample_presentation_context,
            slide_index=0
        )
        
        assert result is not None
        # Watermark should be in noise_elements
        assert "elem_watermark" in result["noise_elements"]
        # Content should be in groups
        group_ids = [g["element_ids"][0] for g in result["groups"]]
        assert "elem_content" in group_ids


class TestSemanticAnalyzerEdgeCases:
    """Test edge cases"""
    
    @pytest.mark.asyncio
    async def test_analyze_with_empty_elements(
        self,
        mock_llm_worker,
        sample_presentation_context,
        tmp_path
    ):
        """Test analysis with no OCR elements"""
        test_image = tmp_path / "test_slide.png"
        test_image.write_bytes(b"fake_image_data")
        
        with patch('app.services.semantic_analyzer.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = mock_llm_worker
            
            from app.services.semantic_analyzer import SemanticAnalyzer
            
            analyzer = SemanticAnalyzer()
            analyzer.llm_worker = mock_llm_worker
            analyzer.use_mock = False
            
            result = await analyzer.analyze_slide(
                str(test_image),
                [],  # Empty elements
                sample_presentation_context,
                slide_index=0
            )
            
            assert result is not None
            assert "groups" in result
    
    @pytest.mark.asyncio
    async def test_analyze_with_missing_image(
        self,
        mock_llm_worker,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test analysis with missing image file"""
        with patch('app.services.semantic_analyzer.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = mock_llm_worker
            
            from app.services.semantic_analyzer import SemanticAnalyzer
            
            analyzer = SemanticAnalyzer()
            analyzer.llm_worker = mock_llm_worker
            analyzer.use_mock = False
            
            # Should handle missing file gracefully
            result = await analyzer.analyze_slide(
                "/nonexistent/image.png",
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Should fall back or handle error
            assert result is not None


class TestSemanticAnalyzerIntegration:
    """Integration-style tests (mocked external deps)"""
    
    @pytest.mark.asyncio
    async def test_full_slide_analysis_workflow(
        self,
        sample_ocr_elements,
        sample_presentation_context,
        tmp_path
    ):
        """Test complete slide analysis workflow"""
        test_image = tmp_path / "slide.png"
        test_image.write_bytes(b"fake_image")
        
        # Mock LLM with realistic response
        realistic_response = {
            "slide_type": "content_slide",
            "groups": [
                {
                    "id": "group_title",
                    "name": "Main Title",
                    "type": "title",
                    "priority": "high",
                    "element_ids": ["elem_0"],
                    "reading_order": [1],
                    "educational_intent": "Introduce ML concepts",
                    "highlight_strategy": {
                        "when": "start",
                        "effect_type": "spotlight",
                        "duration": 3.0,
                        "intensity": "dramatic"
                    },
                    "dependencies": {
                        "highlight_before": None,
                        "highlight_together_with": None,
                        "highlight_after": None
                    }
                },
                {
                    "id": "group_content",
                    "name": "Key Concepts",
                    "type": "key_point",
                    "priority": "medium",
                    "element_ids": ["elem_1"],
                    "reading_order": [2],
                    "educational_intent": "Explain applications",
                    "highlight_strategy": {
                        "when": "during_explanation",
                        "effect_type": "highlight",
                        "duration": 2.5,
                        "intensity": "normal"
                    },
                    "dependencies": {
                        "highlight_before": ["group_title"],
                        "highlight_together_with": None,
                        "highlight_after": None
                    }
                }
            ],
            "noise_elements": ["elem_2"],
            "visual_density": "medium",
            "cognitive_load": "medium"
        }
        
        mock_worker = Mock()
        mock_worker.generate = Mock(return_value=json.dumps(realistic_response))
        
        with patch('app.services.semantic_analyzer.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = mock_worker
            
            from app.services.semantic_analyzer import SemanticAnalyzer
            
            analyzer = SemanticAnalyzer()
            analyzer.llm_worker = mock_worker
            analyzer.use_mock = False
            
            result = await analyzer.analyze_slide(
                str(test_image),
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Verify complete structure
            assert result["slide_type"] == "content_slide"
            assert len(result["groups"]) == 2
            assert len(result["noise_elements"]) == 1
            
            # Verify first group (title)
            title_group = result["groups"][0]
            assert title_group["type"] == "title"
            assert title_group["priority"] == "high"
            assert title_group["highlight_strategy"]["effect_type"] == "spotlight"
            
            # Verify second group (content)
            content_group = result["groups"][1]
            assert content_group["type"] == "key_point"
            assert "group_title" in content_group["dependencies"]["highlight_before"]
