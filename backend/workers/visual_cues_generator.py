"""
Генератор визуальных cues для синхронизации с аудио
"""
import logging
import uuid
from typing import List, Dict, Any, Optional

# Попытка импорта с относительными путями (для Celery)
try:
    from app.models.schemas import Cue, ActionType
except (ImportError, ValueError):
    # Fallback для прямого запуска
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.models.schemas import Cue, ActionType

logger = logging.getLogger(__name__)

class VisualCuesGenerator:
    """Генератор визуальных cues на основе элементов слайда и аудио"""
    
    def __init__(self):
        self.logger = logger
    
    def generate_cues_for_slide(self, 
                               elements: List[Dict[str, Any]], 
                               audio_duration: float,
                               tts_words: Optional[Dict[str, Any]] = None) -> List[Cue]:
        """
        Генерирует визуальные cues для слайда на основе элементов и аудио
        
        Args:
            elements: Список элементов слайда
            audio_duration: Длительность аудио в секундах
            tts_words: Данные о времени произнесения слов (если доступны)
            
        Returns:
            Список визуальных cues
        """
        try:
            self.logger.info(f"Генерируем визуальные cues для {len(elements)} элементов, длительность аудио: {audio_duration:.2f}s")
            
            cues = []
            
            if not elements:
                self.logger.warning("Нет элементов для генерации cues")
                return cues
            
            # Если есть данные о времени произнесения слов с метками, используем их для точной синхронизации
            if tts_words and tts_words.get("word_timings"):
                self.logger.info(f"Используем {len(tts_words['word_timings'])} меток слов для синхронизации")
                cues = self._generate_word_synchronized_cues(elements, tts_words["word_timings"])
            elif tts_words and tts_words.get("sentences"):
                # Fallback: синхронизация по предложениям
                cues = self._generate_synchronized_cues(elements, tts_words["sentences"])
            else:
                # Генерируем базовые cues с равномерным распределением времени
                cues = self._generate_basic_cues(elements, audio_duration)
            
            self.logger.info(f"✅ Сгенерировано {len(cues)} визуальных cues")
            return cues
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка генерации визуальных cues: {e}")
            return []
    
    def _normalize_bbox(self, bbox: Any) -> List[float]:
        """Нормализует bbox к формату [x, y, width, height]"""
        if isinstance(bbox, dict):
            # Формат словаря: {"x": ..., "y": ..., "width": ..., "height": ...}
            return [
                bbox.get("x", 0),
                bbox.get("y", 0),
                bbox.get("width", 100),
                bbox.get("height", 50)
            ]
        elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
            # Формат списка: [x, y, width, height]
            return list(bbox[:4])
        else:
            # Fallback
            return [0, 0, 100, 50]
    
    def _generate_word_synchronized_cues(self,
                                        elements: List[Dict[str, Any]],
                                        word_timings: List[Dict[str, Any]]) -> List[Cue]:
        """Генерирует cues синхронизированные с метками слов из TTS"""
        cues = []

        # Фильтруем текстовые элементы
        text_types = ["text", "heading", "paragraph", "list_item"]
        text_elements = [elem for elem in elements if elem.get("type") in text_types and elem.get("text")]

        if not text_elements:
            self.logger.warning("Нет текстовых элементов для синхронизации")
            return cues

        # Получаем временные метки из word_timings
        if not word_timings:
            self.logger.warning("Нет меток слов для синхронизации")
            return cues

        # Извлекаем уникальные временные отметки (каждая метка соответствует слову)
        time_marks = sorted([wt.get('time_seconds', 0.0) for wt in word_timings])

        if not time_marks:
            self.logger.warning("Не удалось извлечь временные метки")
            return cues

        self.logger.info(f"Используем {len(time_marks)} временных меток для {len(text_elements)} элементов")

        # Распределяем временные метки между элементами слайда
        # Каждый элемент получает пропорциональную часть меток
        marks_per_element = max(1, len(time_marks) // len(text_elements))

        current_mark_idx = 0
        for i, element in enumerate(text_elements):
            # Определяем диапазон меток для этого элемента
            start_idx = current_mark_idx
            end_idx = min(current_mark_idx + marks_per_element, len(time_marks))

            if start_idx >= len(time_marks):
                break

            # Время начала - первая метка элемента
            t0 = time_marks[start_idx]
            # Время конца - последняя метка элемента + небольшая задержка
            t1 = time_marks[end_idx - 1] + 1.0 if end_idx > start_idx else t0 + 1.0

            normalized_bbox = self._normalize_bbox(element.get("bbox", [0, 0, 100, 50]))

            # Highlight cue для элемента
            highlight_cue = Cue(
                cue_id=f"cue_{uuid.uuid4().hex[:8]}",
                t0=t0,
                t1=t1,
                action=ActionType.HIGHLIGHT,
                bbox=normalized_bbox,
                element_id=element.get("id")
            )
            cues.append(highlight_cue)

            # Underline cue (начинается немного позже)
            underline_cue = Cue(
                cue_id=f"cue_{uuid.uuid4().hex[:8]}",
                t0=t0 + 0.1,
                t1=t1,
                action=ActionType.UNDERLINE,
                bbox=self._get_underline_bbox(normalized_bbox),
                element_id=element.get("id")
            )
            cues.append(underline_cue)

            # Laser move к следующему элементу
            if i < len(text_elements) - 1:
                next_element = text_elements[i + 1]
                next_bbox = self._normalize_bbox(next_element.get("bbox", [0, 0, 100, 50]))
                laser_cue = Cue(
                    cue_id=f"cue_{uuid.uuid4().hex[:8]}",
                    t0=t1 - 0.3,
                    t1=t1,
                    action=ActionType.LASER_MOVE,
                    to=self._get_element_center(next_bbox)
                )
                cues.append(laser_cue)

            current_mark_idx = end_idx

        self.logger.info(f"Создано {len(cues)} cues на основе меток слов")
        return cues
    
    def _generate_synchronized_cues(self,
                                   elements: List[Dict[str, Any]],
                                   sentences: List[Dict[str, Any]]) -> List[Cue]:
        """Генерирует cues синхронизированные с предложениями аудио"""
        cues = []

        # Фильтруем текстовые элементы (любой тип с текстом)
        text_types = ["text", "heading", "paragraph", "list_item"]
        text_elements = [elem for elem in elements if elem.get("type") in text_types and elem.get("text")]

        if not text_elements:
            self.logger.warning("Нет текстовых элементов для синхронизации")
            return cues
        
        # Простое сопоставление: каждое предложение с элементом
        for i, sentence in enumerate(sentences):
            if i < len(text_elements):
                element = text_elements[i]
                normalized_bbox = self._normalize_bbox(element.get("bbox", [0, 0, 100, 50]))
                
                # Highlight cue
                highlight_cue = Cue(
                    cue_id=f"cue_{uuid.uuid4().hex[:8]}",
                    t0=sentence.get("t0", 0.0),
                    t1=sentence.get("t1", sentence.get("t0", 0.0) + 2.0),
                    action=ActionType.HIGHLIGHT,
                    bbox=normalized_bbox,
                    element_id=element.get("id")
                )
                cues.append(highlight_cue)
                
                # Underline cue (начинается немного позже highlight)
                underline_start = sentence.get("t0", 0.0) + 0.5
                underline_cue = Cue(
                    cue_id=f"cue_{uuid.uuid4().hex[:8]}",
                    t0=underline_start,
                    t1=sentence.get("t1", underline_start + 1.5),
                    action=ActionType.UNDERLINE,
                    bbox=self._get_underline_bbox(normalized_bbox),
                    element_id=element.get("id")
                )
                cues.append(underline_cue)
        
        return cues
    
    def _generate_basic_cues(self,
                           elements: List[Dict[str, Any]],
                           audio_duration: float) -> List[Cue]:
        """Генерирует базовые cues с равномерным распределением времени"""
        cues = []

        # Фильтруем текстовые элементы (любой тип с текстом)
        text_types = ["text", "heading", "paragraph", "list_item"]
        text_elements = [elem for elem in elements if elem.get("type") in text_types and elem.get("text")]

        if not text_elements:
            self.logger.warning("Нет текстовых элементов для генерации базовых cues")
            return cues
        
        # Равномерно распределяем время между элементами
        time_per_element = audio_duration / len(text_elements)
        current_time = 0.5  # Начинаем через 0.5 секунды
        
        for i, element in enumerate(text_elements):
            normalized_bbox = self._normalize_bbox(element.get("bbox", [0, 0, 100, 50]))
            
            # Highlight cue
            highlight_cue = Cue(
                cue_id=f"cue_{uuid.uuid4().hex[:8]}",
                t0=current_time,
                t1=current_time + time_per_element * 0.8,  # 80% времени на highlight
                action=ActionType.HIGHLIGHT,
                bbox=normalized_bbox,
                element_id=element.get("id")
            )
            cues.append(highlight_cue)
            
            # Underline cue (начинается немного позже highlight)
            underline_start = current_time + time_per_element * 0.2
            underline_cue = Cue(
                cue_id=f"cue_{uuid.uuid4().hex[:8]}",
                t0=underline_start,
                t1=current_time + time_per_element * 0.9,  # Заканчивается почти одновременно с highlight
                action=ActionType.UNDERLINE,
                bbox=self._get_underline_bbox(normalized_bbox),
                element_id=element.get("id")
            )
            cues.append(underline_cue)
            
            # Laser move to next element (если есть следующий элемент)
            if i < len(text_elements) - 1:
                next_element = text_elements[i + 1]
                next_bbox = self._normalize_bbox(next_element.get("bbox", [0, 0, 100, 50]))
                laser_cue = Cue(
                    cue_id=f"cue_{uuid.uuid4().hex[:8]}",
                    t0=current_time + time_per_element * 0.8,
                    t1=current_time + time_per_element,
                    action=ActionType.LASER_MOVE,
                    to=self._get_element_center(next_bbox)
                )
                cues.append(laser_cue)
            
            current_time += time_per_element
        
        return cues
    
    def _get_underline_bbox(self, element_bbox: List[float]) -> List[float]:
        """Получает координаты для подчеркивания элемента"""
        if len(element_bbox) >= 4:
            x, y, width, height = element_bbox
            # Подчеркивание внизу элемента
            return [x, y + height - 4, width, 4]
        return [0, 0, 100, 4]
    
    def _get_element_center(self, element_bbox: List[float]) -> List[float]:
        """Получает центр элемента для лазерной указки"""
        if len(element_bbox) >= 4:
            x, y, width, height = element_bbox
            return [x + width // 2, y + height // 2]
        return [50, 50]

# Функция для интеграции в пайплайн
def generate_visual_cues_for_slide(elements: List[Dict[str, Any]], 
                                  audio_duration: float,
                                  tts_words: Optional[Dict[str, Any]] = None) -> List[Cue]:
    """
    Генерирует визуальные cues для слайда
    
    Args:
        elements: Список элементов слайда
        audio_duration: Длительность аудио в секундах
        tts_words: Данные о времени произнесения слов (если доступны)
        
    Returns:
        Список визуальных cues
    """
    generator = VisualCuesGenerator()
    return generator.generate_cues_for_slide(elements, audio_duration, tts_words)
