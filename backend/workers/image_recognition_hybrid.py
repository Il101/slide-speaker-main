import logging
from typing import List, Dict, Any
import os
from PIL import Image
import base64
import json
from openai import OpenAI
from google.cloud import vision
from google.oauth2 import service_account
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

logger = logging.getLogger(__name__)

class HybridImageRecognitionWorker:
    """
    Гибридный worker для распознавания изображений:
    Vision API для быстрого обнаружения + LLM Vision для детального анализа
    """
    def __init__(self):
        # Инициализируем Vision API
        self.vision_client = self._initialize_vision_client()
        
        # Инициализируем LLM Vision
        self.llm_client = OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
        )
        self.model = settings.OPENROUTER_MODEL
        self.language = settings.LLM_LANGUAGE
        
        logger.info(f"✅ Hybrid Image Recognition Worker инициализирован")

    def _initialize_vision_client(self):
        """Инициализирует Vision API клиент"""
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path or not os.path.exists(credentials_path):
            logger.error("❌ Google credentials не найдены")
            return None
        
        try:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            return vision.ImageAnnotatorClient(credentials=credentials)
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Vision API: {e}")
            return None

    def analyze_slide_images(self, png_path: str, slide_number: int) -> List[Dict]:
        """
        Анализирует изображения на слайде с помощью гибридного подхода
        """
        if not self.vision_client:
            logger.error("❌ Vision API клиент не инициализирован")
            return []

        logger.info(f"🔍 Анализируем изображения на слайде {slide_number}: {png_path}")
        
        try:
            # Этап 1: Vision API - быстрое обнаружение изображений
            vision_results = self._detect_images_with_vision_api(png_path, slide_number)
            
            # Этап 2: LLM Vision - детальный анализ важных изображений
            detailed_results = self._analyze_images_with_llm_vision(png_path, slide_number, vision_results)
            
            # Объединяем результаты
            all_results = vision_results + detailed_results
            
            logger.info(f"✅ Слайд {slide_number}: найдено {len(all_results)} изображений")
            return all_results
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображений слайда {slide_number}: {e}")
            return []

    def _detect_images_with_vision_api(self, png_path: str, slide_number: int) -> List[Dict]:
        """Этап 1: Vision API для быстрого обнаружения"""
        results = []
        
        try:
            with open(png_path, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)

            # Используем label_detection и object_localization
            features = [
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION),
                vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION),
            ]

            response = self.vision_client.annotate_image({'image': image, 'features': features})
            
            # Обрабатываем метки
            if response.label_annotations:
                for i, label in enumerate(response.label_annotations):
                    if label.score > 0.5:  # Только уверенные метки
                        results.append({
                            "id": f"slide_{slide_number}_vision_label_{i}",
                            "type": "image",
                            "subtype": "vision_detection",
                            "description": label.description,
                            "confidence": label.score,
                            "bbox": {"x": 0, "y": 0, "width": 100, "height": 100},
                            "source": "vision_api",
                            "detailed_analysis": False
                        })
            
            # Обрабатываем объекты
            if response.localized_object_annotations:
                for i, obj in enumerate(response.localized_object_annotations):
                    if obj.score > 0.5:
                        bbox = self._convert_normalized_bbox(obj.bounding_poly)
                        results.append({
                            "id": f"slide_{slide_number}_vision_object_{i}",
                            "type": "image",
                            "subtype": "vision_object",
                            "description": obj.name,
                            "confidence": obj.score,
                            "bbox": bbox,
                            "source": "vision_api",
                            "detailed_analysis": False
                        })
            
        except Exception as e:
            logger.error(f"❌ Ошибка Vision API для слайда {slide_number}: {e}")
        
        return results

    def _analyze_images_with_llm_vision(self, png_path: str, slide_number: int, vision_results: List[Dict]) -> List[Dict]:
        """Этап 2: LLM Vision для детального анализа"""
        results = []
        
        # Анализируем только если Vision API нашел изображения
        if not vision_results:
            return results
        
        try:
            # Кодируем изображение
            with open(png_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Создаем промпт для детального анализа
            prompt = f"""
            Проанализируй это изображение слайда презентации по анатомии растений.
            
            Найди и опиши все изображения, диаграммы, микроскопические снимки и другие визуальные элементы.
            Для каждого изображения укажи:
            1. Тип изображения (микроскопический снимок, диаграмма, фотография растения, таблица, график)
            2. Что именно изображено
            3. Научное значение
            4. Координаты (приблизительные)
            
            Отвечай на русском языке в формате JSON:
            {{
                "images": [
                    {{
                        "type": "микроскопический_снимок",
                        "description": "Поперечный срез листа растения",
                        "details": "Видна структура эпидермиса, мезофилла и проводящих пучков",
                        "bbox": {{"x": 100, "y": 200, "width": 300, "height": 400}},
                        "scientific_significance": "Демонстрирует анатомическое строение листа"
                    }}
                ]
            }}
            """
            
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Парсим ответ
            response_content = response.choices[0].message.content
            analysis_data = json.loads(response_content)
            
            # Преобразуем в наш формат
            for i, img_data in enumerate(analysis_data.get("images", [])):
                results.append({
                    "id": f"slide_{slide_number}_llm_image_{i}",
                    "type": "image",
                    "subtype": img_data.get("type", "unknown"),
                    "description": img_data.get("description", ""),
                    "details": img_data.get("details", ""),
                    "scientific_significance": img_data.get("scientific_significance", ""),
                    "bbox": img_data.get("bbox", {"x": 0, "y": 0, "width": 100, "height": 100}),
                    "source": "llm_vision",
                    "detailed_analysis": True
                })
            
        except Exception as e:
            logger.error(f"❌ Ошибка LLM Vision для слайда {slide_number}: {e}")
        
        return results

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
