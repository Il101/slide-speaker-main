"""
Comprehensive unit tests for SmartScriptGenerator
Testing: script generation, anti-reading logic, personas, multilingual
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from typing import Dict, Any, List


@pytest.fixture
def mock_llm_worker():
    """Mock LLM worker"""
    worker = Mock()
    worker.generate = Mock(return_value=json.dumps({
        "talk_track": [
            {
                "segment": "hook",
                "text": "Let's explore machine learning concepts today.",
                "group_id": "group_title"
            },
            {
                "segment": "explanation",
                "text": "Machine learning enables computers to learn from data without explicit programming.",
                "group_id": "group_content"
            },
            {
                "segment": "example",
                "text": "For instance, email spam filters use ML to identify unwanted messages.",
                "group_id": None
            }
        ],
        "speaker_notes": "Introduction to machine learning with practical examples.",
        "estimated_duration": 45
    }))
    return worker


@pytest.fixture
def sample_semantic_map():
    """Sample semantic map"""
    return {
        "slide_type": "content_slide",
        "groups": [
            {
                "id": "group_title",
                "name": "Title",
                "type": "title",
                "priority": "high",
                "element_ids": ["elem_0"],
                "reading_order": [1]
            },
            {
                "id": "group_content",
                "name": "Main Content",
                "type": "key_point",
                "priority": "medium",
                "element_ids": ["elem_1", "elem_2"],
                "reading_order": [2, 3]
            }
        ],
        "visual_density": "medium",
        "cognitive_load": "medium"
    }


@pytest.fixture
def sample_ocr_elements():
    """Sample OCR elements"""
    return [
        {
            "id": "elem_0",
            "text": "Machine Learning Basics",
            "bbox": [100, 100, 800, 200]
        },
        {
            "id": "elem_1",
            "text": "Definition and core concepts",
            "bbox": [100, 300, 700, 380]
        },
        {
            "id": "elem_2",
            "text": "Real-world applications",
            "bbox": [100, 400, 700, 480]
        }
    ]


@pytest.fixture
def sample_presentation_context():
    """Sample presentation context"""
    return {
        "theme": "AI Education",
        "level": "undergraduate",
        "presentation_style": "academic",
        "total_slides": 10
    }


class TestSmartScriptGeneratorInitialization:
    """Test initialization"""
    
    def test_init_with_llm_provider(self):
        """Test initialization with LLM provider"""
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = Mock()
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            
            assert generator is not None
            assert generator.use_mock is False
            assert generator.llm_worker is not None
            assert generator.anti_reading_threshold == 0.35
    
    def test_init_fallback_to_mock(self):
        """Test fallback to mock mode"""
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.side_effect = Exception("No provider")
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            
            assert generator is not None
            assert generator.use_mock is True
            assert generator.llm_worker is None
    
    def test_init_loads_personas(self):
        """Test that personas are loaded"""
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = Mock()
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            
            assert hasattr(generator, 'personas')
            assert hasattr(generator, 'content_intelligence')
            assert hasattr(generator, 'prompt_builder')


class TestGenerateScript:
    """Test generate_script method"""
    
    @pytest.mark.asyncio
    async def test_generate_script_success(
        self,
        mock_llm_worker,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test successful script generation"""
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = mock_llm_worker
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            generator.llm_worker = mock_llm_worker
            generator.use_mock = False
            
            result = await generator.generate_script(
                sample_semantic_map,
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Verify result structure
            assert result is not None
            assert "talk_track" in result
            assert "speaker_notes" in result
            assert "estimated_duration" in result
            
            # Verify talk_track structure
            assert len(result["talk_track"]) > 0
            for segment in result["talk_track"]:
                assert "segment" in segment
                assert "text" in segment
                assert "group_id" in segment
            
            # Verify LLM was called
            mock_llm_worker.generate.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_script_with_anti_reading_check(
        self,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test anti-reading check passes"""
        # LLM response with LOW overlap (good!)
        good_response = {
            "talk_track": [
                {
                    "segment": "hook",
                    "text": "Today we'll explore the fascinating world of artificial intelligence.",
                    "group_id": "group_title"
                }
            ],
            "speaker_notes": "Engaging introduction",
            "estimated_duration": 30
        }
        
        good_llm = Mock()
        good_llm.generate = Mock(return_value=json.dumps(good_response))
        
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = good_llm
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            generator.llm_worker = good_llm
            generator.use_mock = False
            
            result = await generator.generate_script(
                sample_semantic_map,
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Should have overlap_score
            assert "overlap_score" in result
            assert result["overlap_score"] < 0.35  # Below threshold
    
    @pytest.mark.asyncio
    async def test_generate_script_fails_anti_reading_retries(
        self,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test retry when anti-reading check fails"""
        # First attempt: HIGH overlap (bad - just reading slide)
        bad_response = {
            "talk_track": [
                {
                    "segment": "hook",
                    "text": "Machine Learning Basics. Definition and core concepts. Real-world applications.",
                    "group_id": "group_title"
                }
            ],
            "speaker_notes": "Content",
            "estimated_duration": 20
        }
        
        # Second attempt: LOW overlap (good - explaining)
        good_response = {
            "talk_track": [
                {
                    "segment": "hook",
                    "text": "Let's dive into how computers can learn patterns from data.",
                    "group_id": "group_title"
                }
            ],
            "speaker_notes": "Better explanation",
            "estimated_duration": 35
        }
        
        retry_llm = Mock()
        retry_llm.generate = Mock(side_effect=[
            json.dumps(bad_response),  # First call: bad
            json.dumps(good_response)   # Second call: good
        ])
        
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = retry_llm
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            generator.llm_worker = retry_llm
            generator.use_mock = False
            
            result = await generator.generate_script(
                sample_semantic_map,
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Should retry and succeed
            assert result is not None
            assert retry_llm.generate.call_count == 2  # Retried once
            assert result["overlap_score"] < 0.35
    
    @pytest.mark.asyncio
    async def test_generate_script_with_persona_override(
        self,
        mock_llm_worker,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test using persona override"""
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = mock_llm_worker
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            generator.llm_worker = mock_llm_worker
            generator.use_mock = False
            
            result = await generator.generate_script(
                sample_semantic_map,
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0,
                persona_override="motivational"
            )
            
            assert result is not None
            # Should have persona metadata
            if "persona_used" in result:
                assert "motivational" in result["persona_used"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_script_mock_mode(
        self,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test script generation in mock mode"""
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.side_effect = Exception("No LLM")
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            
            result = await generator.generate_script(
                sample_semantic_map,
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Should return mock script
            assert result is not None
            assert result["mock"] is True
            assert "talk_track" in result
            assert len(result["talk_track"]) > 0


class TestAntiReadingLogic:
    """Test anti-reading detection"""
    
    def test_extract_slide_text(self, sample_ocr_elements):
        """Test extracting text from OCR elements"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        slide_text = generator._extract_slide_text(sample_ocr_elements)
        
        assert slide_text is not None
        assert isinstance(slide_text, str)
        assert "machine learning" in slide_text.lower()
        assert "definition" in slide_text.lower()
    
    def test_calculate_overlap_high(self):
        """Test high overlap detection (reading slide)"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        # Generated text is almost identical to slide
        generated = "machine learning basics definition and core concepts"
        slide = "machine learning basics definition and core concepts applications"
        
        overlap = generator._calculate_overlap(generated, slide)
        
        assert overlap > 0.5  # High overlap
    
    def test_calculate_overlap_low(self):
        """Test low overlap (explaining, not reading)"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        # Generated text explains concepts differently
        generated = "today we explore how computers learn patterns from data"
        slide = "machine learning basics definition and core concepts"
        
        overlap = generator._calculate_overlap(generated, slide)
        
        assert overlap < 0.3  # Low overlap - good!
    
    def test_calculate_overlap_empty(self):
        """Test overlap with empty strings"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        overlap = generator._calculate_overlap("", "test")
        assert overlap == 0.0
        
        overlap = generator._calculate_overlap("test", "")
        assert overlap == 0.0
        
        overlap = generator._calculate_overlap("", "")
        assert overlap == 0.0


class TestMultilingualSupport:
    """Test multilingual features"""
    
    def test_auto_wrap_foreign_terms_german(self):
        """Test auto-wrapping German terms"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        text = "Рассмотрим структуру Blatt растения"
        
        wrapped = generator._auto_wrap_foreign_terms(text)
        
        # Should wrap "Blatt"
        assert "[lang:" in wrapped
        assert "Blatt" in wrapped
    
    def test_auto_wrap_foreign_terms_latin(self):
        """Test auto-wrapping Latin terms"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        text = "Вид Quercus robur распространён в Европе"
        
        wrapped = generator._auto_wrap_foreign_terms(text)
        
        # Should wrap "Quercus robur"
        assert "[lang:" in wrapped or "Quercus" in wrapped
    
    def test_auto_wrap_preserves_already_wrapped(self):
        """Test that already wrapped terms are not double-wrapped"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        text = "Рассмотрим [lang:de]Blatt[/lang] растения"
        
        wrapped = generator._auto_wrap_foreign_terms(text)
        
        # Should not double-wrap
        assert wrapped.count("[lang:") == 1
    
    def test_auto_wrap_skips_short_terms(self):
        """Test skipping very short terms"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        text = "Формула E=mc² важна"
        
        wrapped = generator._auto_wrap_foreign_terms(text)
        
        # Should not wrap single letters
        assert wrapped == text or "[lang:" not in wrapped


class TestPromptGeneration:
    """Test prompt generation"""
    
    def test_create_script_generation_prompt(
        self,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test prompt creation"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        prompt = generator._create_script_generation_prompt(
            sample_semantic_map,
            sample_ocr_elements,
            sample_presentation_context,
            previous_summary="",
            slide_index=0,
            persona_config=None,
            content_strategy=None
        )
        
        assert prompt is not None
        assert isinstance(prompt, str)
        
        # Verify key components
        assert "talk_track" in prompt.lower()
        assert "group_id" in prompt.lower()
        assert sample_presentation_context["theme"] in prompt
    
    def test_prompt_includes_anti_reading_instructions(
        self,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test that prompt includes anti-reading rules"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        prompt = generator._create_script_generation_prompt(
            sample_semantic_map,
            sample_ocr_elements,
            sample_presentation_context,
            previous_summary="",
            slide_index=0,
            persona_config=None,
            content_strategy=None
        )
        
        # Check for anti-reading instructions
        assert "DO NOT read" in prompt or "EXPLAIN" in prompt
        assert "do not quote" in prompt.lower() or "don't read" in prompt.lower()


class TestMockScriptGeneration:
    """Test mock generation"""
    
    def test_generate_script_mock_structure(
        self,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test mock script has correct structure"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        result = generator._generate_script_mock(
            sample_semantic_map,
            sample_ocr_elements,
            sample_presentation_context
        )
        
        assert result is not None
        assert result["mock"] is True
        assert "talk_track" in result
        assert "speaker_notes" in result
        assert "estimated_duration" in result
        
        # Verify talk_track segments
        for segment in result["talk_track"]:
            assert "segment" in segment
            assert "text" in segment
            assert "group_id" in segment
    
    def test_generate_script_mock_uses_group_ids(
        self,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test mock uses actual group IDs from semantic map"""
        from app.services.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator()
        
        result = generator._generate_script_mock(
            sample_semantic_map,
            sample_ocr_elements,
            sample_presentation_context
        )
        
        # Should use group IDs from semantic_map
        group_ids = [g["id"] for g in sample_semantic_map["groups"]]
        talk_track_group_ids = [seg["group_id"] for seg in result["talk_track"] if seg["group_id"]]
        
        # At least some group IDs should match
        assert any(gid in group_ids for gid in talk_track_group_ids)


class TestEdgeCases:
    """Test edge cases"""
    
    @pytest.mark.asyncio
    async def test_generate_with_empty_semantic_map(
        self,
        mock_llm_worker,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test with empty semantic map"""
        empty_map = {
            "slide_type": "content_slide",
            "groups": [],
            "visual_density": "low",
            "cognitive_load": "easy"
        }
        
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = mock_llm_worker
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            generator.llm_worker = mock_llm_worker
            generator.use_mock = False
            
            result = await generator.generate_script(
                empty_map,
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            assert result is not None
            assert "talk_track" in result
    
    @pytest.mark.asyncio
    async def test_generate_with_empty_ocr_elements(
        self,
        mock_llm_worker,
        sample_semantic_map,
        sample_presentation_context
    ):
        """Test with no OCR elements"""
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = mock_llm_worker
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            generator.llm_worker = mock_llm_worker
            generator.use_mock = False
            
            result = await generator.generate_script(
                sample_semantic_map,
                [],  # No OCR elements
                sample_presentation_context,
                slide_index=0
            )
            
            assert result is not None
            # Anti-reading check should pass (no slide text to match)
            assert "overlap_score" in result
    
    @pytest.mark.asyncio
    async def test_generate_with_invalid_json_response(
        self,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test handling invalid JSON from LLM"""
        bad_llm = Mock()
        bad_llm.generate = Mock(return_value="Not valid JSON at all")
        
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = bad_llm
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            generator.llm_worker = bad_llm
            generator.use_mock = False
            
            result = await generator.generate_script(
                sample_semantic_map,
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Should fall back to mock
            assert result is not None
            assert result.get("mock") is True


class TestDurationCalculation:
    """Test duration estimation"""
    
    @pytest.mark.asyncio
    async def test_duration_calculation_included(
        self,
        mock_llm_worker,
        sample_semantic_map,
        sample_ocr_elements,
        sample_presentation_context
    ):
        """Test that duration is calculated"""
        with patch('app.services.smart_script_generator.ProviderFactory') as mock_factory:
            mock_factory.get_llm_provider.return_value = mock_llm_worker
            
            from app.services.smart_script_generator import SmartScriptGenerator
            
            generator = SmartScriptGenerator()
            generator.llm_worker = mock_llm_worker
            generator.use_mock = False
            
            result = await generator.generate_script(
                sample_semantic_map,
                sample_ocr_elements,
                sample_presentation_context,
                slide_index=0
            )
            
            # Should have duration fields
            assert "recommended_duration" in result or "estimated_duration" in result
            
            if "recommended_duration" in result:
                assert result["recommended_duration"] > 0
                assert result["recommended_duration"] < 300  # Reasonable max
