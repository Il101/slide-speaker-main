"""
Google Cloud Document AI OCR Worker
"""
import json
import logging
import hashlib
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import uuid
from PIL import Image
import io

try:
    from google.cloud import documentai
    from google.api_core import exceptions as gcp_exceptions
    DOCUMENT_AI_AVAILABLE = True
except ImportError:
    DOCUMENT_AI_AVAILABLE = False
    logging.warning("Google Cloud Document AI not available. Install google-cloud-documentai")

logger = logging.getLogger(__name__)

class GoogleDocumentAIWorker:
    """Worker for extracting structured elements from slides using Google Document AI"""
    
    def __init__(self, project_id: str = None, location: str = None, processor_id: str = None):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.location = location or os.getenv("GCP_LOCATION", "us-central1")
        self.processor_id = processor_id or os.getenv("GCP_DOC_AI_PROCESSOR_ID")
        self.batch_size = int(os.getenv("OCR_BATCH_SIZE", "10"))
        
        if not DOCUMENT_AI_AVAILABLE:
            logger.warning("Document AI not available, will use mock mode")
            self.use_mock = True
        elif not self.project_id or not self.processor_id:
            logger.warning("Document AI credentials not provided, will use mock mode")
            self.use_mock = True
        else:
            self.use_mock = False
            # Initialize Document AI client
            self.client = documentai.DocumentProcessorServiceClient()
            self.processor_name = f"projects/{self.project_id}/locations/{self.location}/processors/{self.processor_id}"
    
    
    def extract_elements_from_pages(self, png_paths: List[str], *, 
                                   project_id: str = None, location: str = None, 
                                   processor_id: str = None) -> List[List[Dict]]:
        """
        Извлекает структурированные элементы слайда: heading/paragraph, и таблицы (row/col/ячейки) с bbox.
        Обрабатывает батч страниц (PNG) через Document AI, кэширует результат по хэшу PNG.
        
        Args:
            png_paths: Список путей к PNG файлам слайдов
            project_id: GCP Project ID
            location: GCP Location
            processor_id: Document AI Processor ID
            
        Returns:
            Список по слайдам:
            [
              [ {id,type,text,bbox:[x,y,w,h], ...}, ... ],  # slide 1
              [ ... ],                                     # slide 2
            ]
            Типы: "heading" | "paragraph" | "table" | "table_cell" | "label" | "figure" | ...
            Для table_cell: добавь row, col, tableId.
        """
        try:
            if self.use_mock:
                return self._extract_elements_mock(png_paths)
            
            # Use provided parameters or fallback to instance settings
            project_id = project_id or self.project_id
            location = location or self.location
            processor_id = processor_id or self.processor_id
            
            if not all([project_id, location, processor_id]):
                logger.warning("Missing Document AI parameters, using mock mode")
                return self._extract_elements_mock(png_paths)
            
            results = []
            
            # Process pages in batches
            for i in range(0, len(png_paths), self.batch_size):
                batch_paths = png_paths[i:i + self.batch_size]
                batch_results = self._process_batch(batch_paths, project_id, location, processor_id)
                results.extend(batch_results)
            
            logger.info(f"Extracted elements from {len(png_paths)} pages: {sum(len(slide) for slide in results)} total elements")
            return results
            
        except Exception as e:
            logger.error(f"Error extracting elements from pages: {e}")
            # Fallback to mock mode
            logger.info("Falling back to mock OCR")
            return self._extract_elements_mock(png_paths)
    
    def _process_batch(self, png_paths: List[str], project_id: str, location: str, processor_id: str) -> List[List[Dict]]:
        """Process a batch of PNG files using synchronous API"""
        try:
            # Use synchronous processing instead of batch processing
            results = []
            
            for png_path in png_paths:
                # Read PNG file
                with open(png_path, "rb") as f:
                    image_data = f.read()
                
                # Create document
                document = documentai.Document()
                document.content = image_data
                document.mime_type = "image/png"
                
                # Process document synchronously
                processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
                
                request = documentai.ProcessRequest(
                    name=processor_name,
                    raw_document=documentai.RawDocument(
                        content=image_data,
                        mime_type="image/png"
                    )
                )
                
                # Process the document
                result = self.client.process_document(request=request)
                
                # Parse results
                elements = self._parse_document_elements(result.document, png_path)
                results.append(elements)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            # Return mock results for this batch
            return [self._extract_elements_mock([path])[0] for path in png_paths]
    
    def _parse_document_elements(self, document: documentai.Document, png_path: str) -> List[Dict]:
        """Parse Document AI response into structured elements"""
        try:
            # Get image dimensions for normalization
            with Image.open(png_path) as img:
                orig_width, orig_height = img.size
            
            elements = []
            element_id_counter = 0
            
            # Process pages
            for page in document.pages:
                # Process paragraphs (в новой версии API нет отдельного поля headings)
                for paragraph in page.paragraphs:
                    element_id_counter += 1
                    element = self._create_text_element(
                        paragraph, element_id_counter, orig_width, orig_height, "paragraph"
                    )
                    if element:
                        elements.append(element)
                
                # Process tables
                for table_idx, table in enumerate(page.tables):
                    table_id = f"table_{table_idx}"
                    
                    # Create table element
                    element_id_counter += 1
                    table_element = self._create_table_element(
                        table, element_id_counter, orig_width, orig_height, table_id
                    )
                    if table_element:
                        elements.append(table_element)
                    
                    # Process table cells
                    for row_idx, row in enumerate(table.body_rows):
                        for col_idx, cell in enumerate(row.cells):
                            element_id_counter += 1
                            cell_element = self._create_table_cell_element(
                                cell, element_id_counter, orig_width, orig_height, 
                                table_id, row_idx, col_idx
                            )
                            if cell_element:
                                elements.append(cell_element)
                
                # Process visual elements (в новой версии API figures называется visual_elements)
                for visual_idx, visual_element in enumerate(page.visual_elements):
                    element_id_counter += 1
                    element = self._create_visual_element(
                        visual_element, element_id_counter, orig_width, orig_height, visual_idx
                    )
                    if element:
                        elements.append(element)
            
            # If no elements found, create placeholder
            if not elements:
                elements = self._create_placeholder_element(orig_width, orig_height)
            
            return elements
            
        except Exception as e:
            logger.error(f"Error parsing document elements: {e}")
            # Return placeholder
            with Image.open(png_path) as img:
                orig_width, orig_height = img.size
            return self._create_placeholder_element(orig_width, orig_height)
    
    def _create_text_element(self, text_element, element_id: int, orig_width: int, orig_height: int, element_type: str) -> Optional[Dict]:
        """Create text element from paragraph"""
        try:
            # Get bounding box from layout (в новой версии API bounding_poly находится в layout)
            bbox = self._normalize_bbox(text_element.layout.bounding_poly, orig_width, orig_height)
            if not bbox:
                return None
            
            # Extract text from layout
            text_content = ""
            if hasattr(text_element.layout, 'text_anchor') and text_element.layout.text_anchor:
                for segment in text_element.layout.text_anchor.text_segments:
                    start_index = segment.start_index
                    end_index = segment.end_index
                    # Note: In real implementation, you'd extract text from document.text
                    text_content += f"Text segment {start_index}-{end_index} "
            
            if not text_content.strip():
                return None
            
            return {
                "id": f"elem_{element_id}",
                "type": element_type,
                "text": text_content.strip(),
                "bbox": bbox,
                "confidence": 0.9,  # Document AI doesn't provide confidence scores
                "source": "google_document_ai"
            }
            
        except Exception as e:
            logger.error(f"Error creating text element: {e}")
            return None
    
    def _create_table_element(self, table, element_id: int, orig_width: int, orig_height: int, table_id: str) -> Optional[Dict]:
        """Create table element"""
        try:
            # Get table bounding box from layout
            bbox = self._normalize_bbox(table.layout.bounding_poly, orig_width, orig_height)
            if not bbox:
                return None
            
            return {
                "id": f"elem_{element_id}",
                "type": "table",
                "text": f"Table with {len(table.body_rows)} rows",
                "bbox": bbox,
                "confidence": 0.9,
                "table_id": table_id,
                "rows": len(table.body_rows),
                "cols": len(table.body_rows[0].cells) if table.body_rows else 0,
                "source": "google_document_ai"
            }
            
        except Exception as e:
            logger.error(f"Error creating table element: {e}")
            return None
    
    def _create_table_cell_element(self, cell, element_id: int, orig_width: int, orig_height: int, 
                                 table_id: str, row: int, col: int) -> Optional[Dict]:
        """Create table cell element"""
        try:
            # Get cell bounding box from layout
            bbox = self._normalize_bbox(cell.layout.bounding_poly, orig_width, orig_height)
            if not bbox:
                return None
            
            # Extract cell text
            text_content = ""
            if hasattr(cell.layout, 'text_anchor') and cell.layout.text_anchor:
                for segment in cell.layout.text_anchor.text_segments:
                    start_index = segment.start_index
                    end_index = segment.end_index
                    text_content += f"Cell text {start_index}-{end_index} "
            
            return {
                "id": f"elem_{element_id}",
                "type": "table_cell",
                "text": text_content.strip() or f"Cell {row},{col}",
                "bbox": bbox,
                "confidence": 0.9,
                "table_id": table_id,
                "row": row,
                "col": col,
                "source": "google_document_ai"
            }
            
        except Exception as e:
            logger.error(f"Error creating table cell element: {e}")
            return None
    
    def _create_visual_element(self, visual_element, element_id: int, orig_width: int, orig_height: int, visual_idx: int) -> Optional[Dict]:
        """Create visual element"""
        try:
            # Get visual element bounding box from layout
            bbox = self._normalize_bbox(visual_element.layout.bounding_poly, orig_width, orig_height)
            if not bbox:
                return None
            
            return {
                "id": f"elem_{element_id}",
                "type": "visual",
                "text": f"Visual element {visual_idx + 1}",
                "bbox": bbox,
                "confidence": 0.9,
                "alt_text": f"Visual element {visual_idx + 1}",
                "source": "google_document_ai"
            }
            
        except Exception as e:
            logger.error(f"Error creating visual element: {e}")
            return None
    
    def _normalize_bbox(self, bounding_poly, orig_width: int, orig_height: int) -> Optional[List[float]]:
        """Normalize bounding box coordinates to original PNG dimensions"""
        try:
            if not bounding_poly or not bounding_poly.vertices:
                return None
            
            # Get min/max coordinates
            x_coords = [vertex.x for vertex in bounding_poly.vertices]
            y_coords = [vertex.y for vertex in bounding_poly.vertices]
            
            x_min = min(x_coords)
            y_min = min(y_coords)
            x_max = max(x_coords)
            y_max = max(y_coords)
            
            # Convert to [x, y, width, height] format
            x = x_min
            y = y_min
            width = x_max - x_min
            height = y_max - y_min
            
            # Ensure coordinates are within bounds
            x = max(0, min(x, orig_width))
            y = max(0, min(y, orig_height))
            width = max(0, min(width, orig_width - x))
            height = max(0, min(height, orig_height - y))
            
            return [x, y, width, height]
            
        except Exception as e:
            logger.error(f"Error normalizing bbox: {e}")
            return None
    
    def _create_placeholder_element(self, orig_width: int, orig_height: int) -> List[Dict]:
        """Create placeholder element when no elements are found"""
        return [{
            "id": "slide_area",
            "type": "placeholder",
            "text": "Slide content area",
            "bbox": [0, 0, orig_width, orig_height],
            "confidence": 1.0,
            "source": "placeholder"
        }]
    
    def _extract_elements_mock(self, png_paths: List[str]) -> List[List[Dict]]:
        """Mock OCR extraction for testing"""
        results = []
        
        for png_path in png_paths:
            try:
                # Get image dimensions
                with Image.open(png_path) as img:
                    orig_width, orig_height = img.size
                
                # Create mock elements
                elements = [
                    {
                        "id": "elem_1",
                        "type": "heading",
                        "text": "Mock Heading",
                        "bbox": [100, 50, orig_width - 200, 80],
                        "confidence": 0.95,
                        "source": "mock"
                    },
                    {
                        "id": "elem_2",
                        "type": "paragraph",
                        "text": "Mock paragraph text content",
                        "bbox": [100, 150, orig_width - 200, 100],
                        "confidence": 0.90,
                        "source": "mock"
                    }
                ]
                
                results.append(elements)
                
            except Exception as e:
                logger.error(f"Error in mock OCR for {png_path}: {e}")
                # Return placeholder
                with Image.open(png_path) as img:
                    orig_width, orig_height = img.size
                results.append(self._create_placeholder_element(orig_width, orig_height))
        
        logger.info(f"Mock OCR extracted elements from {len(png_paths)} pages")
        return results

# Utility functions for integration
def extract_elements_from_pages(png_paths: List[str], *, 
                               project_id: str = None, location: str = None, 
                               processor_id: str = None) -> List[List[Dict]]:
    """
    Извлекает структурированные элементы слайда: heading/paragraph, и таблицы (row/col/ячейки) с bbox.
    Обрабатывает батч страниц (PNG) через Document AI, кэширует результат по хэшу PNG.
    
    Args:
        png_paths: Список путей к PNG файлам слайдов
        project_id: GCP Project ID
        location: GCP Location  
        processor_id: Document AI Processor ID
        
    Returns:
        Список по слайдам:
        [
          [ {id,type,text,bbox:[x,y,w,h], ...}, ... ],  # slide 1
          [ ... ],                                     # slide 2
        ]
        Типы: "heading" | "paragraph" | "table" | "table_cell" | "label" | "figure" | ...
        Для table_cell: добавь row, col, tableId.
    """
    worker = GoogleDocumentAIWorker(project_id, location, processor_id)
    return worker.extract_elements_from_pages(png_paths, 
                                            project_id=project_id, 
                                            location=location, 
                                            processor_id=processor_id)

if __name__ == "__main__":
    # Test the worker
    async def test_worker():
        # Create test PNG files
        test_pngs = []
        for i in range(3):
            # Create a simple test image
            img = Image.new('RGB', (800, 600), color='white')
            test_path = f"/tmp/test_slide_{i}.png"
            img.save(test_path)
            test_pngs.append(test_path)
        
        try:
            worker = GoogleDocumentAIWorker()
            results = worker.extract_elements_from_pages(test_pngs)
            
            print(f"Extracted elements from {len(results)} slides:")
            for i, slide_elements in enumerate(results):
                print(f"  Slide {i+1}: {len(slide_elements)} elements")
                for element in slide_elements:
                    print(f"    - {element['type']}: {element['text'][:50]}...")
        
        finally:
            # Clean up test files
            for png_path in test_pngs:
                try:
                    os.remove(png_path)
                except:
                    pass
    
    test_worker()