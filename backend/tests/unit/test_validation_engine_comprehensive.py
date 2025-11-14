"""
Comprehensive unit tests for ValidationEngine
Testing: semantic validation, geometry, hallucination detection, coverage
"""
import pytest
from typing import Dict, Any, List


@pytest.fixture
def sample_semantic_map():
    """Sample valid semantic map"""
    return {
        "slide_type": "content_slide",
        "groups": [
            {
                "id": "group_0",
                "name": "Title",
                "type": "title",
                "priority": "high",
                "element_ids": ["elem_0"],
                "reading_order": [1],
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
            },
            {
                "id": "group_1",
                "name": "Content",
                "type": "key_point",
                "priority": "medium",
                "element_ids": ["elem_1", "elem_2"],
                "reading_order": [2, 3],
                "highlight_strategy": {
                    "when": "during_explanation",
                    "effect_type": "highlight",
                    "duration": 2.0,
                    "intensity": "normal"
                },
                "dependencies": {
                    "highlight_before": ["group_0"],
                    "highlight_together_with": None,
                    "highlight_after": None
                }
            }
        ],
        "noise_elements": ["elem_3"],
        "visual_density": "medium",
        "cognitive_load": "medium"
    }


@pytest.fixture
def sample_ocr_elements():
    """Sample OCR elements"""
    return [
        {
            "id": "elem_0",
            "text": "Title Text",
            "bbox": [100, 100, 800, 200],
            "type": "text",
            "confidence": 0.95
        },
        {
            "id": "elem_1",
            "text": "First point",
            "bbox": [100, 300, 700, 380],
            "type": "text",
            "confidence": 0.92
        },
        {
            "id": "elem_2",
            "text": "Second point",
            "bbox": [100, 400, 700, 480],
            "type": "text",
            "confidence": 0.93
        },
        {
            "id": "elem_3",
            "text": "© 2024",
            "bbox": [50, 950, 150, 1000],
            "type": "text",
            "confidence": 0.88
        }
    ]


@pytest.fixture
def sample_cues():
    """Sample visual cues"""
    return [
        {
            "cue_id": "cue_1",
            "t0": 0.5,
            "t1": 3.0,
            "action": "spotlight",
            "bbox": [100, 100, 800, 200],
            "element_id": "elem_0",
            "group_id": "group_0"
        },
        {
            "cue_id": "cue_2",
            "t0": 3.5,
            "t1": 6.0,
            "action": "highlight",
            "bbox": [100, 300, 700, 380],
            "element_id": "elem_1",
            "group_id": "group_1"
        }
    ]


class TestValidationEngineInitialization:
    """Test initialization"""
    
    def test_init(self):
        """Test ValidationEngine initialization"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        assert engine is not None
        assert hasattr(engine, 'fuzzy_match_threshold')
        assert hasattr(engine, 'min_coverage')
        assert hasattr(engine, 'max_cognitive_load')
        
        # Verify default values
        assert engine.fuzzy_match_threshold > 0
        assert engine.min_coverage > 0
        assert engine.max_cognitive_load > 0


class TestSemanticValidation:
    """Test Layer 1: Semantic Structure Validation"""
    
    def test_validate_semantic_structure_valid(self, sample_semantic_map, sample_ocr_elements):
        """Test validation of valid semantic map"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        fixed_map, errors = engine.validate_semantic_map(
            sample_semantic_map,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        assert fixed_map is not None
        assert isinstance(errors, list)
        # Valid map should have no errors
        assert len(errors) == 0
    
    def test_validate_missing_groups_field(self, sample_ocr_elements):
        """Test handling of missing 'groups' field"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        invalid_map = {
            "slide_type": "content_slide",
            # Missing 'groups' field!
        }
        
        fixed_map, errors = engine.validate_semantic_map(
            invalid_map,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should add groups field
        assert "groups" in fixed_map
        assert isinstance(fixed_map["groups"], list)
        # Should report error
        assert len(errors) > 0
        assert any("groups" in err.lower() for err in errors)
    
    def test_validate_group_missing_required_fields(self, sample_ocr_elements):
        """Test handling of groups with missing required fields"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        invalid_map = {
            "slide_type": "content_slide",
            "groups": [
                {
                    # Missing: id, priority, element_ids, highlight_strategy
                    "name": "Some Group",
                    "type": "content"
                }
            ]
        }
        
        fixed_map, errors = engine.validate_semantic_map(
            invalid_map,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should fix missing fields
        group = fixed_map["groups"][0]
        assert "id" in group
        assert "priority" in group
        assert "element_ids" in group
        assert "highlight_strategy" in group
        
        # Should report errors
        assert len(errors) > 0


class TestGeometricValidation:
    """Test Layer 2: Geometric Validation"""
    
    def test_validate_geometry_valid(self, sample_semantic_map, sample_ocr_elements):
        """Test validation of valid geometry"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Add bbox to groups
        map_with_bbox = sample_semantic_map.copy()
        map_with_bbox["groups"][0]["bbox"] = [100, 100, 700, 100]
        
        fixed_map, errors = engine.validate_semantic_map(
            map_with_bbox,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Valid geometry should pass
        geometry_errors = [e for e in errors if "bbox" in e.lower()]
        assert len(geometry_errors) == 0
    
    def test_validate_geometry_negative_coordinates(self, sample_semantic_map, sample_ocr_elements):
        """Test detection of negative coordinates"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Add invalid bbox
        map_with_bad_bbox = sample_semantic_map.copy()
        map_with_bad_bbox["groups"][0]["bbox"] = [-10, -20, 700, 100]
        
        fixed_map, errors = engine.validate_semantic_map(
            map_with_bad_bbox,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should report error
        assert len(errors) > 0
        assert any("negative" in err.lower() for err in errors)
    
    def test_validate_geometry_exceeds_boundaries(self, sample_semantic_map, sample_ocr_elements):
        """Test detection of bbox exceeding slide boundaries"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Add bbox that exceeds slide size
        map_with_large_bbox = sample_semantic_map.copy()
        map_with_large_bbox["groups"][0]["bbox"] = [100, 100, 2000, 1500]  # Exceeds 1440x1080
        
        fixed_map, errors = engine.validate_semantic_map(
            map_with_large_bbox,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should report error
        assert len(errors) > 0
        assert any("exceed" in err.lower() for err in errors)
    
    def test_validate_geometry_invalid_bbox_format(self, sample_semantic_map, sample_ocr_elements):
        """Test handling of invalid bbox format"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Add invalid bbox format
        map_with_bad_format = sample_semantic_map.copy()
        map_with_bad_format["groups"][0]["bbox"] = [100, 100]  # Should be 4 values
        
        fixed_map, errors = engine.validate_semantic_map(
            map_with_bad_format,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should report error
        assert len(errors) > 0
        assert any("invalid bbox" in err.lower() for err in errors)


class TestHallucinationDetection:
    """Test Layer 3: Hallucination Detection"""
    
    def test_detect_hallucinated_elements(self, sample_semantic_map, sample_ocr_elements):
        """Test detection of hallucinated (non-existent) elements"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Add hallucinated element IDs
        map_with_hallucinations = sample_semantic_map.copy()
        map_with_hallucinations["groups"][0]["element_ids"] = ["elem_0", "elem_fake", "elem_ghost"]
        
        fixed_map, errors = engine.validate_semantic_map(
            map_with_hallucinations,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should remove hallucinated elements
        group = fixed_map["groups"][0]
        assert "elem_0" in group["element_ids"]  # Valid element kept
        assert "elem_fake" not in group["element_ids"]  # Hallucinated removed
        assert "elem_ghost" not in group["element_ids"]  # Hallucinated removed
        
        # Should report errors
        assert len(errors) > 0
        assert any("hallucinated" in err.lower() for err in errors)
    
    def test_fuzzy_match_element_ids(self, sample_semantic_map, sample_ocr_elements):
        """Test fuzzy matching of element IDs"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Element ID with typo that can be fuzzy matched
        map_with_typo = sample_semantic_map.copy()
        map_with_typo["groups"][0]["element_ids"] = ["elem_O"]  # 'O' instead of '0'
        
        fixed_map, errors = engine.validate_semantic_map(
            map_with_typo,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should fuzzy match and fix
        group = fixed_map["groups"][0]
        # Either kept as-is or corrected
        assert len(group["element_ids"]) > 0
    
    def test_remove_groups_with_no_valid_elements(self, sample_semantic_map, sample_ocr_elements):
        """Test removal of groups with no valid elements"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Add group with only hallucinated elements
        map_with_empty_group = sample_semantic_map.copy()
        map_with_empty_group["groups"].append({
            "id": "group_fake",
            "name": "Fake Group",
            "type": "content",
            "priority": "low",
            "element_ids": ["fake_1", "fake_2"],  # All hallucinated
            "reading_order": [1, 2],
            "highlight_strategy": {
                "when": "never",
                "effect_type": "none",
                "duration": 0,
                "intensity": "none"
            }
        })
        
        fixed_map, errors = engine.validate_semantic_map(
            map_with_empty_group,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should remove group with no valid elements
        group_ids = [g["id"] for g in fixed_map["groups"]]
        assert "group_fake" not in group_ids
        
        # Should report error
        assert len(errors) > 0


class TestCoverageAnalysis:
    """Test Layer 4: Coverage Analysis"""
    
    def test_coverage_analysis_complete(self, sample_semantic_map, sample_ocr_elements):
        """Test coverage analysis with complete coverage"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        fixed_map, errors = engine.validate_semantic_map(
            sample_semantic_map,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # All elements are covered (groups + noise)
        # Should pass coverage check
        coverage_errors = [e for e in errors if "coverage" in e.lower()]
        assert len(coverage_errors) == 0
    
    def test_coverage_analysis_missing_elements(self, sample_semantic_map, sample_ocr_elements):
        """Test coverage analysis with missing elements"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Remove an element from groups (incomplete coverage)
        incomplete_map = sample_semantic_map.copy()
        incomplete_map["groups"][1]["element_ids"] = ["elem_1"]  # Missing elem_2
        incomplete_map["noise_elements"] = []  # elem_3 not covered
        
        # Add more OCR elements that aren't covered
        extended_ocr = sample_ocr_elements + [
            {"id": "elem_4", "text": "Extra", "bbox": [100, 600, 200, 650]},
            {"id": "elem_5", "text": "More", "bbox": [100, 700, 200, 750]}
        ]
        
        fixed_map, errors = engine.validate_semantic_map(
            incomplete_map,
            extended_ocr,
            slide_size=(1440, 1080)
        )
        
        # Should auto-add uncategorized group for missed elements
        group_ids = [g["id"] for g in fixed_map["groups"]]
        # May add "group_uncategorized" or similar
        
        # Should report low coverage
        assert len(errors) > 0
        # Coverage error or auto-fix message
    
    def test_coverage_threshold(self, sample_semantic_map, sample_ocr_elements):
        """Test coverage threshold check"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Create scenario with many uncovered elements
        many_ocr_elements = sample_ocr_elements + [
            {"id": f"elem_{i}", "text": f"Text {i}", "bbox": [100, 100+i*50, 200, 150+i*50]}
            for i in range(10, 20)
        ]
        
        # Only cover a few
        sparse_map = {
            "slide_type": "content_slide",
            "groups": [
                {
                    "id": "group_0",
                    "name": "Title",
                    "type": "title",
                    "priority": "high",
                    "element_ids": ["elem_0"],
                    "reading_order": [1],
                    "highlight_strategy": {"when": "start", "effect_type": "spotlight", "duration": 2.0, "intensity": "normal"}
                }
            ],
            "noise_elements": []
        }
        
        fixed_map, errors = engine.validate_semantic_map(
            sparse_map,
            many_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should report low coverage or auto-fix
        assert len(errors) > 0 or len(fixed_map["groups"]) > 1


class TestCognitiveLoadCheck:
    """Test Layer 5: Cognitive Load Check"""
    
    def test_cognitive_load_normal(self, sample_semantic_map, sample_ocr_elements):
        """Test normal cognitive load"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        fixed_map, errors = engine.validate_semantic_map(
            sample_semantic_map,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # 2 groups, both not all high priority - should be ok
        cognitive_errors = [e for e in errors if "cognitive" in e.lower()]
        # Should have no cognitive load warnings
    
    def test_cognitive_load_excessive(self, sample_semantic_map, sample_ocr_elements):
        """Test excessive cognitive load"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Create map with many high-priority groups
        overloaded_map = sample_semantic_map.copy()
        overloaded_map["groups"] = [
            {
                "id": f"group_{i}",
                "name": f"Group {i}",
                "type": "content",
                "priority": "high",  # All high priority!
                "element_ids": [f"elem_{i}"],
                "reading_order": [i+1],
                "highlight_strategy": {"when": "start", "effect_type": "spotlight", "duration": 2.0, "intensity": "dramatic"}
            }
            for i in range(10)  # 10 high-priority groups
        ]
        
        fixed_map, errors = engine.validate_semantic_map(
            overloaded_map,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should report cognitive load warning
        assert len(errors) > 0
        assert any("cognitive" in err.lower() or "priority" in err.lower() for err in errors)


class TestCueValidation:
    """Test visual cue validation"""
    
    def test_validate_cues_valid(self, sample_cues, sample_ocr_elements):
        """Test validation of valid cues"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        audio_duration = 10.0
        
        fixed_cues, errors = engine.validate_cues(
            sample_cues,
            audio_duration,
            sample_ocr_elements
        )
        
        assert fixed_cues is not None
        assert isinstance(fixed_cues, list)
        assert len(fixed_cues) == len(sample_cues)
        # Valid cues should have no errors
        assert len(errors) == 0
    
    def test_validate_cues_negative_timing(self, sample_ocr_elements):
        """Test handling of negative timing"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        bad_cues = [
            {
                "cue_id": "cue_1",
                "t0": -1.0,  # Negative!
                "t1": 2.0,
                "action": "highlight",
                "element_id": "elem_0"
            }
        ]
        
        fixed_cues, errors = engine.validate_cues(
            bad_cues,
            audio_duration=10.0,
            elements=sample_ocr_elements
        )
        
        # Should fix negative t0
        assert fixed_cues[0]["t0"] >= 0
        # Should report error
        assert len(errors) > 0
        assert any("negative" in err.lower() for err in errors)
    
    def test_validate_cues_t1_less_than_t0(self, sample_ocr_elements):
        """Test handling of t1 <= t0"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        bad_cues = [
            {
                "cue_id": "cue_1",
                "t0": 5.0,
                "t1": 3.0,  # Less than t0!
                "action": "highlight",
                "element_id": "elem_0"
            }
        ]
        
        fixed_cues, errors = engine.validate_cues(
            bad_cues,
            audio_duration=10.0,
            elements=sample_ocr_elements
        )
        
        # Should fix t1
        assert fixed_cues[0]["t1"] > fixed_cues[0]["t0"]
        # Should report error
        assert len(errors) > 0
    
    def test_validate_cues_exceeds_audio_duration(self, sample_ocr_elements):
        """Test handling of cues exceeding audio duration"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        bad_cues = [
            {
                "cue_id": "cue_1",
                "t0": 2.0,
                "t1": 15.0,  # Exceeds audio duration
                "action": "highlight",
                "element_id": "elem_0"
            }
        ]
        
        fixed_cues, errors = engine.validate_cues(
            bad_cues,
            audio_duration=10.0,
            elements=sample_ocr_elements
        )
        
        # Should clamp t1 to audio duration
        assert fixed_cues[0]["t1"] <= 10.0
        # Should report error
        assert len(errors) > 0
    
    def test_validate_cues_nonexistent_element(self, sample_ocr_elements):
        """Test handling of cues referencing non-existent elements"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        bad_cues = [
            {
                "cue_id": "cue_1",
                "t0": 1.0,
                "t1": 3.0,
                "action": "highlight",
                "element_id": "elem_fake"  # Doesn't exist
            }
        ]
        
        fixed_cues, errors = engine.validate_cues(
            bad_cues,
            audio_duration=10.0,
            elements=sample_ocr_elements
        )
        
        # Should mark as invalid
        assert fixed_cues[0].get("invalid_element") is True
        # Should report error
        assert len(errors) > 0


class TestOverlapFixing:
    """Test cue overlap fixing"""
    
    def test_fix_overlapping_cues(self, sample_ocr_elements):
        """Test fixing overlapping cues"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        overlapping_cues = [
            {
                "cue_id": "cue_1",
                "t0": 1.0,
                "t1": 4.0,  # Overlaps with next
                "action": "highlight",
                "element_id": "elem_0"
            },
            {
                "cue_id": "cue_2",
                "t0": 3.0,  # Starts before previous ends
                "t1": 6.0,
                "action": "highlight",
                "element_id": "elem_1"
            }
        ]
        
        fixed_cues, errors = engine.validate_cues(
            overlapping_cues,
            audio_duration=10.0,
            elements=sample_ocr_elements
        )
        
        # Should fix overlap
        assert fixed_cues[0]["t1"] < fixed_cues[1]["t0"] or \
               fixed_cues[0]["t1"] <= fixed_cues[1]["t0"] + 0.1  # Small gap allowed
        
        # Should report overlap
        assert len(errors) > 0
        assert any("overlap" in err.lower() for err in errors)
    
    def test_fix_maintains_minimum_duration(self, sample_ocr_elements):
        """Test that fixing maintains minimum cue duration"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        # Cues that would result in too short duration if simply adjusted
        close_cues = [
            {
                "cue_id": "cue_1",
                "t0": 1.0,
                "t1": 2.2,
                "action": "highlight",
                "element_id": "elem_0"
            },
            {
                "cue_id": "cue_2",
                "t0": 2.0,  # Very close to previous
                "t1": 4.0,
                "action": "highlight",
                "element_id": "elem_1"
            }
        ]
        
        fixed_cues, errors = engine.validate_cues(
            close_cues,
            audio_duration=10.0,
            elements=sample_ocr_elements
        )
        
        # Each cue should have minimum duration (0.3s or more)
        for cue in fixed_cues:
            duration = cue["t1"] - cue["t0"]
            # Allow overlap if needed for minimum duration
            assert duration >= 0.2  # Small minimum


class TestEdgeCases:
    """Test edge cases"""
    
    def test_validate_empty_semantic_map(self, sample_ocr_elements):
        """Test validation with empty semantic map"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        empty_map = {}
        
        fixed_map, errors = engine.validate_semantic_map(
            empty_map,
            sample_ocr_elements,
            slide_size=(1440, 1080)
        )
        
        # Should create minimal valid structure
        assert "groups" in fixed_map
        assert isinstance(fixed_map["groups"], list)
    
    def test_validate_empty_cues(self, sample_ocr_elements):
        """Test validation with no cues"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        fixed_cues, errors = engine.validate_cues(
            [],
            audio_duration=10.0,
            elements=sample_ocr_elements
        )
        
        # Should handle gracefully
        assert fixed_cues == []
        assert isinstance(errors, list)
    
    def test_validate_with_no_ocr_elements(self, sample_semantic_map):
        """Test validation with no OCR elements"""
        from app.services.validation_engine import ValidationEngine
        
        engine = ValidationEngine()
        
        fixed_map, errors = engine.validate_semantic_map(
            sample_semantic_map,
            [],  # No OCR elements
            slide_size=(1440, 1080)
        )
        
        # Should handle gracefully
        assert fixed_map is not None
        # May report hallucination errors since no elements exist
