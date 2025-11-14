#!/usr/bin/env python3
"""
Diagram Detector - распознавание и классификация диаграмм, графиков, таблиц
Использует Google Cloud Vision API для обнаружения не-текстовых элементов
"""

import os
import logging
from typing import Dict, Any, List, Tuple, Optional
from google.cloud import vision
from pathlib import Path

logger = logging.getLogger(__name__)


class DiagramDetector:
    """
    Detects and classifies non-text elements (diagrams, images, charts, tables)
    
    Использует Google Vision API для:
    - Object Localization (определение объектов на изображении)
    - Label Detection (классификация содержимого)
    - Image Properties (анализ цветов и композиции)
    """
    
    # Пороги для классификации
    TEXT_AREA_THRESHOLD = 0.3  # Если >30% площади - текст, то не диаграмма
    MIN_DIAGRAM_SIZE = 100  # Минимальный размер bbox (пиксели)
    MIN_CONFIDENCE = 0.5  # Минимальная уверенность Vision API
    
    # Размеры слайда по умолчанию
    DEFAULT_SLIDE_WIDTH = 1440
    DEFAULT_SLIDE_HEIGHT = 1080
    
    def __init__(self):
        """Инициализация Vision API клиента"""
        try:
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not credentials_path or not os.path.exists(credentials_path):
                logger.warning(f"⚠️ Google credentials не найдены: {credentials_path}")
                self.client = None
            else:
                self.client = vision.ImageAnnotatorClient()
                logger.info("✅ DiagramDetector: Vision API клиент инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Vision API: {e}")
            self.client = None
    
    def detect_diagrams(
        self, 
        image_path: str, 
        text_elements: List[Dict],
        slide_number: int = 1
    ) -> List[Dict]:
        """
        Обнаружение не-текстовых элементов (диаграмм, изображений, графиков)
        
        Args:
            image_path: Путь к изображению слайда
            text_elements: Уже распознанные текстовые элементы (из OCR)
            slide_number: Номер слайда (для ID)
            
        Returns:
            Список диаграмм с полями:
            - id: уникальный ID
            - type: "diagram"
            - diagram_type: chart|flowchart|table|image|icon|generic_diagram
            - bbox: [x, y, w, h]
            - confidence: 0.0-1.0
            - description: текстовое описание
            - visual_complexity: low|medium|high
            - key_elements: список ключевых элементов
        """
        if not self.client:
            logger.warning("⚠️ Vision API недоступен, пропускаем распознавание диаграмм")
            return []
        
        if not os.path.exists(image_path):
            logger.error(f"❌ Изображение не найдено: {image_path}")
            return []
        
        try:
            logger.info(f"🔍 Распознаём диаграммы на слайде {slide_number}: {image_path}")
            
            # Читаем изображение
            with open(image_path, 'rb') as f:
                content = f.read()
            
            image = vision.Image(content=content)
            
            # Получаем данные от Vision API
            objects = self._detect_objects(image)
            labels = self._detect_labels(image)
            
            # Вычисляем покрытие текстом
            text_coverage = self._calculate_text_coverage(text_elements)
            logger.debug(f"📊 Покрытие текстом: {text_coverage:.1%}")
            
            # Находим регионы без текста (потенциальные диаграммы)
            diagram_candidates = self._find_non_text_regions(
                text_elements, objects, text_coverage
            )
            
            logger.info(f"🎯 Найдено кандидатов в диаграммы: {len(diagram_candidates)}")
            
            # Классифицируем диаграммы
            diagrams = []
            for idx, candidate in enumerate(diagram_candidates):
                diagram_type = self._classify_diagram(candidate, objects, labels)
                
                if diagram_type:
                    diagram_id = f"slide{slide_number:03d}_diagram_{idx}"
                    
                    diagrams.append({
                        "id": diagram_id,
                        "type": "diagram",
                        "diagram_type": diagram_type,
                        "bbox": candidate['bbox'],
                        "confidence": candidate['confidence'],
                        "description": self._generate_description(
                            diagram_type, objects, labels, candidate
                        ),
                        "visual_complexity": self._estimate_complexity(candidate),
                        "key_elements": self._extract_key_elements(
                            diagram_type, objects, labels
                        ),
                        "slide_number": slide_number
                    })
            
            logger.info(f"✅ Распознано диаграмм: {len(diagrams)}")
            for diag in diagrams:
                logger.debug(
                    f"  - {diag['diagram_type']}: {diag['description'][:50]}... "
                    f"(confidence: {diag['confidence']:.2f})"
                )
            
            return diagrams
            
        except Exception as e:
            logger.error(f"❌ Ошибка распознавания диаграмм: {e}", exc_info=True)
            return []
    
    def _detect_objects(self, image: vision.Image) -> List:
        """Обнаружение объектов на изображении"""
        try:
            response = self.client.object_localization(image=image)
            
            if response.error.message:
                logger.error(f"❌ Vision API ошибка (objects): {response.error.message}")
                return []
            
            objects = response.localized_object_annotations
            logger.debug(f"📦 Обнаружено объектов: {len(objects)}")
            
            return objects
            
        except Exception as e:
            logger.error(f"❌ Ошибка object detection: {e}")
            return []
    
    def _detect_labels(self, image: vision.Image) -> List:
        """Определение меток/классификация содержимого"""
        try:
            response = self.client.label_detection(image=image)
            
            if response.error.message:
                logger.error(f"❌ Vision API ошибка (labels): {response.error.message}")
                return []
            
            labels = response.label_annotations
            logger.debug(f"🏷️ Обнаружено меток: {len(labels)}")
            
            return labels
            
        except Exception as e:
            logger.error(f"❌ Ошибка label detection: {e}")
            return []
    
    def _calculate_text_coverage(self, text_elements: List[Dict]) -> float:
        """
        Вычисляет долю изображения, покрытую текстом
        
        Returns:
            Процент покрытия текстом (0.0 - 1.0)
        """
        if not text_elements:
            return 0.0
        
        image_area = self.DEFAULT_SLIDE_WIDTH * self.DEFAULT_SLIDE_HEIGHT
        
        text_area = 0
        for elem in text_elements:
            bbox = elem.get('bbox', [])
            if len(bbox) == 4:
                x, y, w, h = bbox
                text_area += w * h
        
        coverage = text_area / image_area
        return min(coverage, 1.0)  # Ограничиваем 100%
    
    def _find_non_text_regions(
        self,
        text_elements: List[Dict],
        objects: List,
        text_coverage: float
    ) -> List[Dict]:
        """
        Находит регионы изображения, не покрытые текстом (потенциальные диаграммы)
        
        Returns:
            Список кандидатов с bbox, confidence, name
        """
        candidates = []
        
        for obj in objects:
            # Проверяем уверенность
            if obj.score < self.MIN_CONFIDENCE:
                continue
            
            # Конвертируем normalized vertices в bbox
            vertices = obj.bounding_poly.normalized_vertices
            
            x_coords = [v.x for v in vertices]
            y_coords = [v.y for v in vertices]
            
            x = int(min(x_coords) * self.DEFAULT_SLIDE_WIDTH)
            y = int(min(y_coords) * self.DEFAULT_SLIDE_HEIGHT)
            w = int((max(x_coords) - min(x_coords)) * self.DEFAULT_SLIDE_WIDTH)
            h = int((max(y_coords) - min(y_coords)) * self.DEFAULT_SLIDE_HEIGHT)
            
            bbox = [x, y, w, h]
            
            # Проверяем минимальный размер
            if w < self.MIN_DIAGRAM_SIZE or h < self.MIN_DIAGRAM_SIZE:
                logger.debug(f"⏭️ Пропускаем маленький объект: {w}x{h}px")
                continue
            
            # Проверяем перекрытие с текстом
            overlap_ratio = self._calculate_overlap_with_text(bbox, text_elements)
            
            # Если объект сильно перекрывается с текстом - не диаграмма
            if overlap_ratio > 0.5:
                logger.debug(
                    f"⏭️ Пропускаем объект (перекрытие с текстом: {overlap_ratio:.1%}): "
                    f"{obj.name}"
                )
                continue
            
            candidates.append({
                'bbox': bbox,
                'confidence': obj.score,
                'name': obj.name,
                'overlap_with_text': overlap_ratio
            })
        
        return candidates
    
    def _calculate_overlap_with_text(
        self,
        bbox: List[int],
        text_elements: List[Dict]
    ) -> float:
        """
        Вычисляет долю bbox, перекрывающуюся с текстовыми элементами
        
        Returns:
            Процент перекрытия (0.0 - 1.0)
        """
        x1, y1, w1, h1 = bbox
        bbox_area = w1 * h1
        
        if bbox_area == 0:
            return 0.0
        
        total_overlap_area = 0
        
        for elem in text_elements:
            text_bbox = elem.get('bbox', [])
            if len(text_bbox) == 4:
                x2, y2, w2, h2 = text_bbox
                
                overlap_area = self._calculate_bbox_overlap(
                    x1, y1, w1, h1,
                    x2, y2, w2, h2
                )
                
                total_overlap_area += overlap_area
        
        overlap_ratio = total_overlap_area / bbox_area
        return min(overlap_ratio, 1.0)
    
    def _calculate_bbox_overlap(
        self,
        x1: int, y1: int, w1: int, h1: int,
        x2: int, y2: int, w2: int, h2: int
    ) -> float:
        """Вычисляет площадь перекрытия двух bbox"""
        # Находим пересечение
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        return (x_right - x_left) * (y_bottom - y_top)
    
    def _classify_diagram(
        self,
        candidate: Dict,
        objects: List,
        labels: List
    ) -> Optional[str]:
        """
        Классифицирует тип диаграммы на основе объектов и меток
        
        Returns:
            Тип диаграммы: chart|flowchart|table|image|icon|generic_diagram
            или None если не удалось классифицировать
        """
        name = candidate.get('name', '').lower()
        
        # Собираем метки
        label_names = [label.description.lower() for label in labels[:15]]
        label_text = ' '.join(label_names)
        
        # Классификация по ключевым словам
        # IMPORTANT: Check more specific patterns first!
        
        # Таблицы
        if any(word in name or word in label_text 
               for word in ['table', 'spreadsheet', 'grid', 'matrix']):
            return 'table'
        
        # Блок-схемы (BEFORE general 'chart')
        if any(word in name or word in label_text 
               for word in ['flowchart', 'flow chart', 'flow', 'process', 'workflow', 
                           'decision tree', 'algorithm']):
            return 'flowchart'
        
        # Фотографии и изображения (BEFORE general 'chart')
        if any(word in name or word in label_text 
               for word in ['photo', 'photograph', 'picture', 'image', 
                           'illustration', 'drawing']):
            return 'image'
        
        # Графики и диаграммы
        if any(word in name or word in label_text 
               for word in ['chart', 'graph', 'plot', 'bar chart', 'pie chart', 
                           'line graph', 'histogram', 'diagram']):
            return 'chart'
        
        # Иконки и символы
        if any(word in name or word in label_text 
               for word in ['icon', 'symbol', 'logo', 'emblem', 'badge']):
            # Проверяем размер - иконки обычно небольшие
            bbox = candidate['bbox']
            area = bbox[2] * bbox[3]
            if area < 100000:  # Менее 100k пикселей
                return 'icon'
        
        # Если ничего не подошло - generic_diagram
        # (любой визуальный элемент, который не текст)
        return 'generic_diagram'
    
    def _generate_description(
        self,
        diagram_type: str,
        objects: List,
        labels: List,
        candidate: Dict
    ) -> str:
        """
        Генерирует естественное описание диаграммы на русском
        
        Returns:
            Текстовое описание (для лектора)
        """
        label_names = [label.description for label in labels[:5]]
        obj_name = candidate.get('name', 'объект')
        
        # Шаблоны описаний на русском
        descriptions = {
            'chart': f"График или диаграмма, показывающая данные о {', '.join(label_names[:2]) if label_names else 'визуальной информации'}",
            'flowchart': f"Блок-схема, иллюстрирующая процесс или алгоритм",
            'table': f"Таблица с данными",
            'image': f"Изображение: {', '.join(label_names[:3]) if label_names else obj_name}",
            'icon': f"Иконка или символ: {obj_name}",
            'generic_diagram': f"Визуальный элемент, связанный с {', '.join(label_names[:2]) if label_names else 'содержимым слайда'}"
        }
        
        description = descriptions.get(diagram_type, "Визуальный элемент на слайде")
        
        return description
    
    def _estimate_complexity(self, candidate: Dict) -> str:
        """
        Оценивает визуальную сложность элемента
        
        Returns:
            low|medium|high
        """
        bbox = candidate['bbox']
        area = bbox[2] * bbox[3]
        
        # Классификация по площади
        if area > 500000:  # > 500k пикселей - большая диаграмма
            return 'high'
        elif area > 200000:  # 200k-500k - средняя
            return 'medium'
        else:  # < 200k - маленькая
            return 'low'
    
    def _extract_key_elements(
        self,
        diagram_type: str,
        objects: List,
        labels: List
    ) -> List[str]:
        """
        Извлекает ключевые элементы, видимые на диаграмме
        
        Returns:
            Список текстовых описаний ключевых элементов
        """
        # Используем метки как прокси для ключевых элементов
        key_elements = []
        
        # Топ-5 меток с наивысшей уверенностью
        for label in labels[:5]:
            if label.score > 0.7:  # Только уверенные метки
                key_elements.append(label.description)
        
        # Добавляем названия объектов
        for obj in objects[:3]:
            if obj.score > 0.7 and obj.name not in key_elements:
                key_elements.append(obj.name)
        
        return key_elements[:7]  # Максимум 7 элементов
