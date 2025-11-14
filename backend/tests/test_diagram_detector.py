#!/usr/bin/env python3
"""
Unit tests for DiagramDetector
"""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from backend.app.services.diagram_detector import DiagramDetector


class TestDiagramDetector:
    """Test suite for DiagramDetector class"""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance (will use mock if no credentials)"""
        return DiagramDetector()
    
    @pytest.fixture
    def mock_text_elements(self):
        """Mock text elements from OCR"""
        return [
            {
                "id": "text_1",
                "type": "paragraph",
                "text": "Introduction to plant biology",
                "bbox": [100, 50, 400, 30]
            },
            {
                "id": "text_2",
                "type": "paragraph",
                "text": "This slide covers basic concepts",
                "bbox": [100, 100, 400, 25]
            }
        ]
    
    def test_detector_initialization(self, detector):
        """Test that detector initializes correctly"""
        assert detector is not None
        # Check if Vision API client is initialized (or None if no credentials)
        assert hasattr(detector, 'client')
    
    def test_calculate_text_coverage_empty(self, detector):
        """Test text coverage calculation with no elements"""
        coverage = detector._calculate_text_coverage([])
        assert coverage == 0.0
    
    def test_calculate_text_coverage_with_elements(self, detector, mock_text_elements):
        """Test text coverage calculation with elements"""
        coverage = detector._calculate_text_coverage(mock_text_elements)
        
        assert 0.0 <= coverage <= 1.0
        assert coverage > 0.0  # Should be non-zero with elements
    
    def test_calculate_bbox_overlap_no_overlap(self, detector):
        """Test bbox overlap calculation - no overlap"""
        # Two bboxes far apart
        overlap = detector._calculate_bbox_overlap(
            100, 100, 50, 50,   # bbox1
            500, 500, 50, 50    # bbox2 (far away)
        )
        assert overlap == 0.0
    
    def test_calculate_bbox_overlap_full_overlap(self, detector):
        """Test bbox overlap calculation - full overlap"""
        # Same bbox
        overlap = detector._calculate_bbox_overlap(
            100, 100, 50, 50,
            100, 100, 50, 50
        )
        assert overlap == 2500  # 50 * 50
    
    def test_calculate_bbox_overlap_partial(self, detector):
        """Test bbox overlap calculation - partial overlap"""
        overlap = detector._calculate_bbox_overlap(
            100, 100, 50, 50,
            125, 125, 50, 50  # Overlaps partially
        )
        assert overlap > 0
        assert overlap < 2500  # Less than full overlap
    
    def test_classify_diagram_chart(self, detector):
        """Test diagram classification - chart"""
        candidate = {'name': 'Bar Chart', 'bbox': [100, 100, 300, 200]}
        
        # Mock labels
        mock_labels = [
            Mock(description='chart', score=0.9),
            Mock(description='graph', score=0.85)
        ]
        
        diagram_type = detector._classify_diagram(candidate, [], mock_labels)
        assert diagram_type == 'chart'
    
    def test_classify_diagram_table(self, detector):
        """Test diagram classification - table"""
        candidate = {'name': 'spreadsheet', 'bbox': [100, 100, 300, 200]}
        
        mock_labels = [
            Mock(description='table', score=0.9),
            Mock(description='grid', score=0.85)
        ]
        
        diagram_type = detector._classify_diagram(candidate, [], mock_labels)
        assert diagram_type == 'table'
    
    def test_classify_diagram_flowchart(self, detector):
        """Test diagram classification - flowchart"""
        candidate = {'name': 'flow chart', 'bbox': [100, 100, 300, 200]}
        
        mock_labels = [
            Mock(description='flowchart', score=0.9),
            Mock(description='process', score=0.85)
        ]
        
        diagram_type = detector._classify_diagram(candidate, [], mock_labels)
        assert diagram_type == 'flowchart'
    
    def test_classify_diagram_image(self, detector):
        """Test diagram classification - image"""
        candidate = {'name': 'photo', 'bbox': [100, 100, 300, 200]}
        
        mock_labels = [
            Mock(description='photograph', score=0.9),
            Mock(description='image', score=0.85)
        ]
        
        diagram_type = detector._classify_diagram(candidate, [], mock_labels)
        assert diagram_type == 'image'
    
    def test_classify_diagram_icon_small_size(self, detector):
        """Test diagram classification - icon (small size)"""
        candidate = {'name': 'logo', 'bbox': [100, 100, 50, 50]}  # Small
        
        mock_labels = [
            Mock(description='icon', score=0.9),
            Mock(description='symbol', score=0.85)
        ]
        
        diagram_type = detector._classify_diagram(candidate, [], mock_labels)
        assert diagram_type == 'icon'
    
    def test_classify_diagram_generic(self, detector):
        """Test diagram classification - generic fallback"""
        candidate = {'name': 'unknown object', 'bbox': [100, 100, 300, 200]}
        
        mock_labels = [
            Mock(description='visual', score=0.7),
            Mock(description='content', score=0.6)
        ]
        
        diagram_type = detector._classify_diagram(candidate, [], mock_labels)
        assert diagram_type == 'generic_diagram'
    
    def test_estimate_complexity_low(self, detector):
        """Test complexity estimation - low"""
        candidate = {'bbox': [100, 100, 100, 100]}  # 10k pixels
        complexity = detector._estimate_complexity(candidate)
        assert complexity == 'low'
    
    def test_estimate_complexity_medium(self, detector):
        """Test complexity estimation - medium"""
        candidate = {'bbox': [100, 100, 500, 500]}  # 250k pixels
        complexity = detector._estimate_complexity(candidate)
        assert complexity == 'medium'
    
    def test_estimate_complexity_high(self, detector):
        """Test complexity estimation - high"""
        candidate = {'bbox': [100, 100, 800, 800]}  # 640k pixels
        complexity = detector._estimate_complexity(candidate)
        assert complexity == 'high'
    
    def test_generate_description_chart(self, detector):
        """Test description generation for chart"""
        mock_labels = [
            Mock(description='data', score=0.9),
            Mock(description='statistics', score=0.85)
        ]
        
        description = detector._generate_description(
            'chart', [], mock_labels, {'name': 'bar chart'}
        )
        
        assert 'График' in description or 'диаграмма' in description
        assert len(description) > 0
    
    def test_generate_description_table(self, detector):
        """Test description generation for table"""
        description = detector._generate_description(
            'table', [], [], {'name': 'data table'}
        )
        
        assert 'Таблица' in description
    
    def test_extract_key_elements(self, detector):
        """Test key elements extraction"""
        mock_labels = [
            Mock(description='data', score=0.95),
            Mock(description='chart', score=0.90),
            Mock(description='statistics', score=0.85),
            Mock(description='graph', score=0.80),
            Mock(description='axis', score=0.75),
            Mock(description='legend', score=0.70),  # Should be included
            Mock(description='low_score', score=0.50)  # Should be excluded
        ]
        
        mock_objects = [
            Mock(name='bar', score=0.85),
            Mock(name='line', score=0.75)
        ]
        
        key_elements = detector._extract_key_elements('chart', mock_objects, mock_labels)
        
        assert isinstance(key_elements, list)
        assert len(key_elements) > 0
        assert len(key_elements) <= 7  # Max 7 elements
        # Check that low confidence items are excluded
        assert 'low_score' not in key_elements
    
    def test_calculate_overlap_with_text_no_overlap(self, detector, mock_text_elements):
        """Test overlap calculation with text - no overlap"""
        # Bbox far from text elements
        bbox = [1000, 1000, 200, 200]
        
        overlap = detector._calculate_overlap_with_text(bbox, mock_text_elements)
        assert overlap == 0.0
    
    def test_calculate_overlap_with_text_high_overlap(self, detector, mock_text_elements):
        """Test overlap calculation with text - high overlap"""
        # Bbox overlapping with text element
        bbox = [100, 50, 400, 30]  # Same as text_1
        
        overlap = detector._calculate_overlap_with_text(bbox, mock_text_elements)
        assert overlap > 0.5  # Should be high overlap
    
    @patch('backend.app.services.diagram_detector.vision')
    def test_detect_diagrams_no_image(self, mock_vision, detector):
        """Test detect_diagrams with non-existent image"""
        diagrams = detector.detect_diagrams(
            "/nonexistent/image.png",
            [],
            slide_number=1
        )
        
        assert diagrams == []
    
    @patch('backend.app.services.diagram_detector.vision')
    def test_detect_diagrams_no_client(self, mock_vision):
        """Test detect_diagrams with no Vision API client"""
        detector = DiagramDetector()
        detector.client = None  # Simulate no client
        
        diagrams = detector.detect_diagrams(
            "/some/image.png",
            [],
            slide_number=1
        )
        
        assert diagrams == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
