#!/usr/bin/env python3
"""
LLM Vision OCR Worker - тестирование определения координат
"""

import os
import base64
import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class LLMVisionOCRWorker:
    """OCR Worker использующий LLM Vision для анализа изображений"""
    
    def __init__(self):
        """Инициализация LLM Vision клиента"""
        try:
            # Загружаем переменные окружения
            load_dotenv('backend/.env')
            
            # Инициализируем OpenRouter клиент
            self.client = OpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            )
            
            self.model = os.getenv("OPENROUTER_MODEL", "x-ai/grok-4-fast:free")
            self.language = os.getenv("LLM_LANGUAGE", "ru")
            
            logger.info("✅ LLM Vision клиент инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации LLM Vision: {e}")
            raise
    
    def extract_elements_from_pages(self, image_paths: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Извлекает элементы из изображений слайдов используя LLM Vision
        
        Args:
            image_paths: Список путей к PNG изображениям слайдов
            
        Returns:
            Список элементов для каждого слайда
        """
        try:
            logger.info(f"🔍 LLM Vision: Обрабатываем {len(image_paths)} изображений")
            
            all_elements = []
            
            for i, image_path in enumerate(image_paths):
                logger.info(f"📄 Обрабатываем слайд {i+1}: {image_path}")
                
                # Анализируем изображение
                elements = self._analyze_slide_image(image_path, i+1)
                all_elements.append(elements)
                
                logger.info(f"✅ Слайд {i+1}: извлечено {len(elements)} элементов")
            
            logger.info(f"🎉 LLM Vision: Всего обработано {len(all_elements)} слайдов")
            return all_elements
            
        except Exception as e:
            logger.error(f"❌ Ошибка LLM Vision: {e}")
            raise
    
    def _analyze_slide_image(self, image_path: str, slide_number: int) -> List[Dict[str, Any]]:
        """
        Анализирует изображение слайда с помощью LLM Vision
        
        Args:
            image_path: Путь к изображению
            slide_number: Номер слайда
            
        Returns:
            Список элементов слайда
        """
        try:
            # Читаем изображение и кодируем в base64
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Создаем промпт для анализа
            prompt = self._create_analysis_prompt()
            
            # Отправляем запрос в LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Парсим ответ
            response_text = response.choices[0].message.content
            elements = self._parse_llm_response(response_text, slide_number)
            
            return elements
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения: {e}")
            return []
    
    def _create_analysis_prompt(self) -> str:
        """Создает промпт для анализа изображения"""
        
        language_instruction = "русском языке" if self.language == "ru" else "английском языке"
        
        return f"""
Проанализируй это изображение слайда презентации и найди все текстовые элементы.

ВАЖНО: Верни ТОЧНЫЕ координаты каждого элемента в формате JSON.

Требования:
1. Найди все текстовые элементы (заголовки, параграфы, списки)
2. Определи ТОЧНЫЕ координаты каждого элемента
3. Верни результат в формате JSON
4. Координаты должны быть в пикселях относительно левого верхнего угла изображения

Формат ответа:
{{
  "elements": [
    {{
      "id": "element_1",
      "type": "heading|paragraph|list_item",
      "text": "Текст элемента",
      "bbox": {{
        "x": 100,
        "y": 50,
        "width": 200,
        "height": 30
      }},
      "confidence": 0.95
    }}
  ]
}}

Отвечай только JSON, без дополнительного текста.
"""
    
    def _parse_llm_response(self, response_text: str, slide_number: int) -> List[Dict[str, Any]]:
        """
        Парсит ответ LLM в структурированные элементы
        
        Args:
            response_text: Ответ от LLM
            slide_number: Номер слайда
            
        Returns:
            Список элементов слайда
        """
        try:
            # Пытаемся найти JSON в ответе
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning(f"⚠️ Слайд {slide_number}: JSON не найден в ответе")
                return []
            
            json_text = response_text[json_start:json_end]
            data = json.loads(json_text)
            
            elements = []
            for i, element_data in enumerate(data.get('elements', [])):
                element = {
                    "id": element_data.get('id', f"slide_{slide_number}_element_{i}"),
                    "type": element_data.get('type', 'paragraph'),
                    "text": element_data.get('text', ''),
                    "confidence": element_data.get('confidence', 0.9),
                    "bbox": element_data.get('bbox', {"x": 0, "y": 0, "width": 100, "height": 30})
                }
                elements.append(element)
                
                logger.debug(f"📝 Элемент: {element['type']} - {element['text'][:50]}...")
            
            logger.info(f"📊 Слайд {slide_number}: {len(elements)} элементов извлечено")
            
            return elements
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON ответа: {e}")
            logger.error(f"Ответ: {response_text[:200]}...")
            return []
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга ответа: {e}")
            return []

# Для тестирования
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        
        try:
            worker = LLMVisionOCRWorker()
            elements = worker.extract_elements_from_pages([image_path])
            
            print(f"🎉 LLM Vision: Извлечено {len(elements[0])} элементов")
            for i, element in enumerate(elements[0]):
                bbox = element['bbox']
                print(f"  {i+1}. {element['type']}: {element['text'][:50]}...")
                print(f"      Координаты: x={bbox['x']}, y={bbox['y']}, w={bbox['width']}, h={bbox['height']}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    else:
        print("Использование: python ocr_llm_vision.py <путь_к_изображению>")
