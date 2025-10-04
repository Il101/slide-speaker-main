import logging
from typing import List, Dict, Any
from google.cloud import vision
from google.oauth2 import service_account
import os
from PIL import Image

logger = logging.getLogger(__name__)

class EnhancedVisionOCRWorker:
    """
    Улучшенный Vision API worker для извлечения текста, изображений и объектов
    """
    def __init__(self):
        self.client = self._initialize_vision_client()
        if self.client:
            logger.info("✅ Enhanced Google Cloud Vision API клиент инициализирован")
        else:
            logger.error("❌ Ошибка инициализации Vision API: Google credentials не найдены")

    def _initialize_vision_client(self):
        """Initializes the Google Cloud Vision client."""
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            logger.error("❌ Ошибка: Google credentials не найдены: GOOGLE_APPLICATION_CREDENTIALS не установлен.")
            return None
        
        if not os.path.exists(credentials_path):
            logger.error(f"❌ Ошибка: Файл Google credentials не найден по пути: {credentials_path}")
            return None

        try:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            return vision.ImageAnnotatorClient(credentials=credentials)
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки Google credentials: {e}")
            return None

    def extract_elements_from_pages(self, png_paths: List[str], **kwargs) -> List[List[Dict]]:
        """
        Извлекает элементы (текст, изображения, объекты) из списка PNG изображений
        """
        if not self.client:
            logger.error("❌ Vision API клиент не инициализирован. Возвращаем пустые элементы.")
            return [[] for _ in png_paths]

        results = []
        logger.info(f"🔍 Enhanced Vision API: Обрабатываем {len(png_paths)} изображений")

        for i, png_path in enumerate(png_paths):
            logger.info(f"📄 Обрабатываем слайд {i+1}: {png_path}")
            try:
                with open(png_path, 'rb') as image_file:
                    content = image_file.read()
                image = vision.Image(content=content)

                # Получаем все типы аннотаций
                features = [
                    vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION),
                    vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION),
                    vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION),
                ]

                response = self.client.annotate_image({'image': image, 'features': features})
                elements = self._parse_enhanced_response(response, png_path, i+1)
                results.append(elements)
                logger.info(f"✅ Слайд {i+1}: извлечено {len(elements)} элементов")

            except Exception as e:
                logger.error(f"❌ Ошибка обработки слайда {i+1} с Enhanced Vision API: {e}")
                results.append([]) # Return empty for failed slides
        
        logger.info(f"🎉 Enhanced Vision API: Всего обработано {len(png_paths)} слайдов")
        return results

    def _parse_enhanced_response(self, response, png_path: str, slide_number: int) -> List[Dict]:
        """
        Парсит расширенный ответ Vision API в структурированные элементы
        """
        elements = []
        
        try:
            # 1. Обрабатываем текст (как раньше)
            if response.full_text_annotation and response.full_text_annotation.text:
                text_elements = self._parse_text_elements(response.full_text_annotation, slide_number)
                elements.extend(text_elements)
            
            # 2. Обрабатываем метки изображений
            if response.label_annotations:
                label_elements = self._parse_label_elements(response.label_annotations, slide_number)
                elements.extend(label_elements)
            
            # 3. Обрабатываем локализованные объекты
            if response.localized_object_annotations:
                object_elements = self._parse_object_elements(response.localized_object_annotations, slide_number)
                elements.extend(object_elements)
            
            logger.info(f"📊 Слайд {slide_number}: {len([e for e in elements if e['type'] == 'text'])} текстовых, "
                       f"{len([e for e in elements if e['type'] == 'image'])} изображений, "
                       f"{len([e for e in elements if e['type'] == 'object'])} объектов")
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга ответа Vision API для слайда {slide_number}: {e}")
        
        return elements

    def _parse_text_elements(self, full_text_annotation, slide_number: int) -> List[Dict]:
        """Парсит текстовые элементы"""
        elements = []
        
        if full_text_annotation.pages:
            page = full_text_annotation.pages[0]
            
            for block_idx, block in enumerate(page.blocks):
                block_text = ""
                
                # Собираем текст блока
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ""
                        for symbol in word.symbols:
                            word_text += symbol.text
                        block_text += word_text + " "
                
                block_text = block_text.strip()
                
                if block_text:
                    element_type = self._determine_element_type(block_text, block_idx)
                    
                    bbox_dict = self._get_block_bbox(block)
                    element = {
                        "id": f"slide_{slide_number}_text_{block_idx}",
                        "type": "text",
                        "subtype": element_type,
                        "text": block_text,
                        "confidence": 0.9,
                        "bbox": [bbox_dict["x"], bbox_dict["y"], bbox_dict["width"], bbox_dict["height"]],
                        "source": "vision_api_text"
                    }
                    elements.append(element)
        
        return elements

    def _parse_label_elements(self, label_annotations, slide_number: int) -> List[Dict]:
        """Парсит метки изображений"""
        elements = []
        
        for i, label in enumerate(label_annotations):
            if label.score > 0.5:  # Только уверенные метки
                element = {
                    "id": f"slide_{slide_number}_image_{i}",
                    "type": "image",
                    "subtype": "detected_content",
                    "text": f"Изображение: {label.description}",
                    "description": label.description,
                    "confidence": label.score,
                    "bbox": [0, 0, 100, 100],  # Общие координаты в формате списка
                    "source": "vision_api_labels"
                }
                elements.append(element)
        
        return elements

    def _parse_object_elements(self, object_annotations, slide_number: int) -> List[Dict]:
        """Парсит локализованные объекты"""
        elements = []
        
        for i, obj in enumerate(object_annotations):
            if obj.score > 0.5:  # Только уверенные объекты
                # Конвертируем нормализованные координаты в пиксели
                bbox = self._convert_normalized_bbox(obj.bounding_poly)
                
                element = {
                    "id": f"slide_{slide_number}_object_{i}",
                    "type": "object",
                    "subtype": "detected_object",
                    "text": f"Объект: {obj.name}",
                    "description": obj.name,
                    "confidence": obj.score,
                    "bbox": [bbox["x"], bbox["y"], bbox["width"], bbox["height"]],
                    "source": "vision_api_objects"
                }
                elements.append(element)
        
        return elements

    def _convert_normalized_bbox(self, bounding_poly) -> Dict[str, float]:
        """Конвертирует нормализованные координаты в пиксели"""
        if not bounding_poly or not bounding_poly.normalized_vertices:
            return {"x": 0, "y": 0, "width": 100, "height": 100}
        
        vertices = bounding_poly.normalized_vertices
        if len(vertices) >= 4:
            x_coords = [v.x for v in vertices]
            y_coords = [v.y for v in vertices]
            
            # Предполагаем стандартный размер слайда 1440x1080
            width, height = 1440, 1080
            
            return {
                "x": min(x_coords) * width,
                "y": min(y_coords) * height,
                "width": (max(x_coords) - min(x_coords)) * width,
                "height": (max(y_coords) - min(y_coords)) * height
            }
        
        return {"x": 0, "y": 0, "width": 100, "height": 100}

    def _determine_element_type(self, text: str, block_idx: int) -> str:
        """Определяет тип текстового элемента"""
        text_lower = text.lower()
        
        if block_idx == 0 or any(keyword in text_lower for keyword in ['universität', 'university', 'курс', 'лекция']):
            return "heading"
        elif any(keyword in text_lower for keyword in ['•', '-', '1.', '2.', '3.']):
            return "list_item"
        elif len(text) > 100:
            return "paragraph"
        else:
            return "text"

    def _get_block_bbox(self, block) -> Dict[str, float]:
        """Получает координаты блока"""
        try:
            if block.bounding_box and block.bounding_box.vertices:
                vertices = block.bounding_box.vertices
                if len(vertices) >= 4:
                    x_coords = [v.x for v in vertices]
                    y_coords = [v.y for v in vertices]
                    
                    return {
                        "x": min(x_coords),
                        "y": min(y_coords),
                        "width": max(x_coords) - min(x_coords),
                        "height": max(y_coords) - min(y_coords)
                    }
        except Exception as e:
            logger.debug(f"⚠️ Не удалось получить координаты блока: {e}")
        
        # Возвращаем дефолтные координаты
        return {"x": 0, "y": 0, "width": 100, "height": 100}
