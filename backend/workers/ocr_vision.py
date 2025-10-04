#!/usr/bin/env python3
"""
Google Cloud Vision API OCR Worker
Специально для презентаций с изображениями, таблицами и графиками
"""

import os
import logging
from typing import List, Dict, Any
from google.cloud import vision
from google.cloud.vision_v1 import types
import json

logger = logging.getLogger(__name__)

class VisionOCRWorker:
    """OCR Worker использующий Google Cloud Vision API"""
    
    def __init__(self):
        """Инициализация Vision API клиента"""
        try:
            # Проверяем credentials
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not credentials_path or not os.path.exists(credentials_path):
                raise ValueError(f"Google credentials не найдены: {credentials_path}")
            
            # Инициализируем Vision API клиент
            self.client = vision.ImageAnnotatorClient()
            logger.info("✅ Google Cloud Vision API клиент инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Vision API: {e}")
            raise
    
    def extract_elements_from_pages(self, image_paths: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Извлекает элементы из изображений слайдов используя Vision API
        
        Args:
            image_paths: Список путей к PNG изображениям слайдов
            
        Returns:
            Список элементов для каждого слайда
        """
        try:
            logger.info(f"🔍 Vision API: Обрабатываем {len(image_paths)} изображений")
            
            all_elements = []
            
            for i, image_path in enumerate(image_paths):
                logger.info(f"📄 Обрабатываем слайд {i+1}: {image_path}")
                
                # Читаем изображение
                with open(image_path, 'rb') as image_file:
                    content = image_file.read()
                
                # Создаем Vision API запрос
                image = types.Image(content=content)
                
                # Выполняем OCR с дополнительными возможностями
                response = self.client.document_text_detection(image=image)
                
                if response.error.message:
                    logger.error(f"❌ Vision API ошибка: {response.error.message}")
                    continue
                
                # Парсим результат
                elements = self._parse_vision_response(response, i+1)
                all_elements.append(elements)
                
                logger.info(f"✅ Слайд {i+1}: извлечено {len(elements)} элементов")
            
            logger.info(f"🎉 Vision API: Всего обработано {len(all_elements)} слайдов")
            return all_elements
            
        except Exception as e:
            logger.error(f"❌ Ошибка Vision API: {e}")
            raise
    
    def _parse_vision_response(self, response, slide_number: int) -> List[Dict[str, Any]]:
        """
        Парсит ответ Vision API в структурированные элементы
        
        Args:
            response: Ответ от Vision API
            slide_number: Номер слайда
            
        Returns:
            Список элементов слайда
        """
        elements = []
        
        try:
            # Получаем полный текст
            full_text = response.full_text_annotation.text if response.full_text_annotation else ""
            
            if not full_text.strip():
                logger.warning(f"⚠️ Слайд {slide_number}: Текст не найден")
                return elements
            
            # Разбиваем текст на блоки и параграфы
            if response.full_text_annotation.pages:
                page = response.full_text_annotation.pages[0]
                
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
                        # Определяем тип элемента
                        element_type = self._determine_element_type(block_text, block_idx)
                        
                        element = {
                            "id": f"slide_{slide_number}_block_{block_idx}",
                            "type": element_type,
                            "text": block_text,
                            "confidence": 0.9,  # Vision API не предоставляет confidence для блоков
                            "bbox": self._get_block_bbox(block)
                        }
                        
                        elements.append(element)
                        logger.debug(f"📝 Элемент: {element_type} - {block_text[:50]}...")
            
            # Если нет блоков, создаем простой элемент из полного текста
            if not elements and full_text.strip():
                element = {
                    "id": f"slide_{slide_number}_text",
                    "type": "paragraph",
                    "text": full_text.strip(),
                    "confidence": 0.9,
                    "bbox": [0, 0, 100, 100]
                }
                elements.append(element)
            
            logger.info(f"📊 Слайд {slide_number}: {len(elements)} элементов извлечено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга Vision API ответа: {e}")
        
        return elements
    
    def _determine_element_type(self, text: str, block_idx: int) -> str:
        """
        Определяет тип элемента на основе текста
        
        Args:
            text: Текст элемента
            block_idx: Индекс блока
            
        Returns:
            Тип элемента (heading, paragraph, list_item, table, etc.)
        """
        text_lower = text.lower().strip()
        
        # Заголовки обычно короткие и в начале
        if block_idx == 0 and len(text) < 100:
            return "heading"
        
        # Списки содержат маркеры
        if any(marker in text_lower for marker in ['•', '-', '*', '1.', '2.', '3.']):
            return "list_item"
        
        # Таблицы содержат разделители
        if any(sep in text for sep in ['|', '\t', '  ']) and len(text.split('\n')) > 2:
            return "table"
        
        # По умолчанию параграф
        return "paragraph"
    
    def _get_block_bbox(self, block) -> List[float]:
        """
        Получает координаты блока
        
        Args:
            block: Блок из Vision API ответа
            
        Returns:
            Список с координатами [x, y, width, height]
        """
        try:
            if block.bounding_box and block.bounding_box.vertices:
                vertices = block.bounding_box.vertices
                if len(vertices) >= 4:
                    x_coords = [v.x for v in vertices]
                    y_coords = [v.y for v in vertices]
                    
                    x = min(x_coords)
                    y = min(y_coords)
                    width = max(x_coords) - min(x_coords)
                    height = max(y_coords) - min(y_coords)
                    
                    return [x, y, width, height]
        except Exception as e:
            logger.debug(f"⚠️ Не удалось получить координаты блока: {e}")
        
        # Возвращаем дефолтные координаты
        return [0, 0, 100, 100]
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Извлекает только текст из изображения
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Извлеченный текст
        """
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = types.Image(content=content)
            response = self.client.document_text_detection(image=image)
            
            if response.error.message:
                logger.error(f"❌ Vision API ошибка: {response.error.message}")
                return ""
            
            return response.full_text_annotation.text if response.full_text_annotation else ""
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения текста: {e}")
            return ""

# Для тестирования
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    # Загружаем переменные окружения
    load_dotenv("../backend_env_hybrid_default.env")
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        
        try:
            worker = VisionOCRWorker()
            elements = worker.extract_elements_from_pages([image_path])
            
            print(f"🎉 Vision API: Извлечено {len(elements[0])} элементов")
            for i, element in enumerate(elements[0]):
                print(f"  {i+1}. {element['type']}: {element['text'][:100]}...")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    else:
        print("Использование: python ocr_vision.py <путь_к_изображению>")
