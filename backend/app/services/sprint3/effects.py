"""
Профессиональные визуальные эффекты для видео экспорта
Использует OpenCV и NumPy для высокопроизводительной обработки
"""
import numpy as np
import cv2
from typing import Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)


class VisualEffects:
    """Класс для применения профессиональных визуальных эффектов к кадрам видео"""
    
    # Цветовые схемы (BGR формат для OpenCV)
    PRIMARY_COLOR = (246, 130, 59)  # #3B82F6 в BGR
    HIGHLIGHT_COLOR = (0, 215, 255)  # Золотой цвет в BGR
    LASER_COLOR = (50, 50, 255)  # Красный для лазера
    UNDERLINE_COLOR = (246, 130, 59)  # Primary color
    
    # Настройки эффектов
    FADE_DURATION_PERCENT = 0.1  # Первые и последние 10% времени для fade in/out
    PULSE_FREQUENCY = 4  # Частота пульсации (циклов за время эффекта)
    GLOW_LAYERS = 3  # Количество слоев для glow эффекта
    TRAIL_LENGTH = 8  # Длина следа лазера
    
    @staticmethod
    def apply_highlight(frame: np.ndarray, bbox: List[float], t0: float, t1: float, current_time: float) -> np.ndarray:
        """
        Применяет профессиональный highlight эффект с:
        - Fade in/out в начале и конце
        - Пульсацией (pulsing)
        - Градиентом
        - Анимированной границей
        
        Args:
            frame: Кадр изображения (numpy array в RGB)
            bbox: Bounding box [x, y, width, height]
            t0: Время начала эффекта
            t1: Время окончания эффекта
            current_time: Текущее время
            
        Returns:
            Модифицированный кадр
        """
        try:
            if len(bbox) < 4:
                return frame
            
            x, y, w, h = map(int, bbox)
            
            # Проверка границ
            if x < 0 or y < 0 or x + w > frame.shape[1] or y + h > frame.shape[0]:
                logger.warning(f"Bbox выходит за границы кадра: {bbox}")
                return frame
            
            # Вычисляем прогресс (0.0 - 1.0)
            duration = t1 - t0
            if duration <= 0:
                return frame
            
            progress = (current_time - t0) / duration
            progress = max(0.0, min(1.0, progress))  # Clamp to [0, 1]
            
            # Fade in/out: первые и последние 10% времени
            alpha_multiplier = 1.0
            if progress < VisualEffects.FADE_DURATION_PERCENT:
                # Fade in
                alpha_multiplier = progress / VisualEffects.FADE_DURATION_PERCENT
            elif progress > (1.0 - VisualEffects.FADE_DURATION_PERCENT):
                # Fade out
                alpha_multiplier = (1.0 - progress) / VisualEffects.FADE_DURATION_PERCENT
            
            # Пульсация: изменяем прозрачность синусоидально
            pulse = 0.8 + 0.2 * np.sin(progress * VisualEffects.PULSE_FREQUENCY * np.pi)
            base_alpha = 0.3 * alpha_multiplier * pulse
            
            # Создаем overlay для highlight
            overlay = frame.copy()
            
            # Рисуем заполненный прямоугольник с градиентом
            # Создаем градиент от центра к краям
            for i in range(h):
                # Градиент по вертикали
                gradient_factor = 1.0 - abs(2 * (i / h) - 1) * 0.3  # Светлее в центре
                color = tuple(int(c * gradient_factor) for c in VisualEffects.HIGHLIGHT_COLOR)
                cv2.line(overlay, (x, y + i), (x + w, y + i), color, 1)
            
            # Blend с оригинальным кадром
            frame = cv2.addWeighted(frame, 1 - base_alpha, overlay, base_alpha, 0)
            
            # Анимированная граница
            border_width = 2 + int(2 * pulse)  # Толщина границы пульсирует
            border_alpha = 0.6 * alpha_multiplier
            
            # Рисуем границу
            border_overlay = frame.copy()
            cv2.rectangle(border_overlay, (x, y), (x + w, y + h), 
                         VisualEffects.HIGHLIGHT_COLOR, border_width)
            frame = cv2.addWeighted(frame, 1 - border_alpha, border_overlay, border_alpha, 0)
            
            # Glow эффект на границах
            glow_overlay = np.zeros_like(frame)
            for layer in range(VisualEffects.GLOW_LAYERS):
                offset = (layer + 1) * 2
                glow_alpha = base_alpha * 0.3 / (layer + 1)
                cv2.rectangle(glow_overlay, 
                            (x - offset, y - offset), 
                            (x + w + offset, y + h + offset),
                            VisualEffects.HIGHLIGHT_COLOR, 1)
            
            # Размываем glow
            glow_overlay = cv2.GaussianBlur(glow_overlay, (15, 15), 0)
            frame = cv2.addWeighted(frame, 1.0, glow_overlay, 0.5, 0)
            
            return frame
            
        except Exception as e:
            logger.error(f"Ошибка применения highlight эффекта: {e}")
            return frame
    
    @staticmethod
    def apply_laser_pointer(frame: np.ndarray, 
                           from_pos: Optional[Tuple[int, int]], 
                           to_pos: Tuple[int, int],
                           t0: float, 
                           t1: float, 
                           current_time: float,
                           prev_position: Optional[Tuple[int, int]] = None) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Применяет анимированную лазерную указку с:
        - Плавной интерполяцией с easing
        - Trail эффектом (следом)
        - Glow эффектом
        
        Args:
            frame: Кадр изображения (numpy array в RGB)
            from_pos: Начальная позиция (может быть None)
            to_pos: Целевая позиция [x, y]
            t0: Время начала движения
            t1: Время окончания движения
            current_time: Текущее время
            prev_position: Предыдущая позиция указки
            
        Returns:
            (Модифицированный кадр, текущая позиция указки)
        """
        try:
            # Вычисляем прогресс
            duration = t1 - t0
            if duration <= 0:
                current_pos = to_pos
            else:
                progress = (current_time - t0) / duration
                progress = max(0.0, min(1.0, progress))
                
                # Easing: ease-out-cubic для плавного замедления
                eased = 1 - pow(1 - progress, 3)
                
                # Интерполяция позиции
                start_pos = prev_position if prev_position else (from_pos if from_pos else to_pos)
                current_x = int(start_pos[0] + (to_pos[0] - start_pos[0]) * eased)
                current_y = int(start_pos[1] + (to_pos[1] - start_pos[1]) * eased)
                current_pos = (current_x, current_y)
            
            # Проверка границ
            h, w = frame.shape[:2]
            current_pos = (
                max(0, min(w - 1, current_pos[0])),
                max(0, min(h - 1, current_pos[1]))
            )
            
            # Trail эффект: рисуем несколько точек с уменьшающейся прозрачностью
            if prev_position:
                trail_steps = VisualEffects.TRAIL_LENGTH
                for i in range(trail_steps):
                    t = (i + 1) / trail_steps
                    trail_x = int(prev_position[0] + (current_pos[0] - prev_position[0]) * t)
                    trail_y = int(prev_position[1] + (current_pos[1] - prev_position[1]) * t)
                    
                    # Проверка границ для trail
                    if 0 <= trail_x < w and 0 <= trail_y < h:
                        alpha = 0.3 * (i / trail_steps)  # Прозрачность увеличивается к текущей позиции
                        radius = int(3 + 2 * (i / trail_steps))
                        
                        overlay = frame.copy()
                        cv2.circle(overlay, (trail_x, trail_y), radius, VisualEffects.LASER_COLOR, -1)
                        frame = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)
            
            # Glow эффект: несколько полупрозрачных кругов разного размера
            glow_radii = [12, 8, 5]
            glow_alphas = [0.2, 0.4, 0.6]
            
            for radius, alpha in zip(glow_radii, glow_alphas):
                overlay = frame.copy()
                cv2.circle(overlay, current_pos, radius, VisualEffects.LASER_COLOR, -1)
                # Размываем для glow эффекта
                overlay = cv2.GaussianBlur(overlay, (11, 11), 0)
                frame = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)
            
            # Центральная белая точка для контраста
            cv2.circle(frame, current_pos, 3, (255, 255, 255), -1)
            cv2.circle(frame, current_pos, 2, VisualEffects.LASER_COLOR, -1)
            
            return frame, current_pos
            
        except Exception as e:
            logger.error(f"Ошибка применения laser pointer эффекта: {e}")
            return frame, to_pos
    
    @staticmethod
    def apply_underline(frame: np.ndarray, bbox: List[float], t0: float, t1: float, current_time: float) -> np.ndarray:
        """
        Применяет анимированное подчеркивание с:
        - Анимацией рисования слева направо
        - Easing (ease-in-out)
        - Пульсирующей "волной" на конце линии
        
        Args:
            frame: Кадр изображения (numpy array в RGB)
            bbox: Bounding box [x, y, width, height] (для подчеркивания используется нижняя граница)
            t0: Время начала эффекта
            t1: Время окончания эффекта
            current_time: Текущее время
            
        Returns:
            Модифицированный кадр
        """
        try:
            if len(bbox) < 4:
                return frame
            
            x, y, w, h = map(int, bbox)
            
            # Линия подчеркивания внизу bbox
            line_y = y + h
            
            # Проверка границ
            if line_y >= frame.shape[0] or x < 0 or x + w > frame.shape[1]:
                return frame
            
            # Вычисляем прогресс
            duration = t1 - t0
            if duration <= 0:
                return frame
            
            progress = (current_time - t0) / duration
            progress = max(0.0, min(1.0, progress))
            
            # Easing: ease-in-out для плавного начала и конца
            eased = progress * progress * (3 - 2 * progress)
            
            # Текущая ширина линии
            current_width = int(w * eased)
            
            if current_width <= 0:
                return frame
            
            # Рисуем линию от x до x + current_width
            line_thickness = 3
            overlay = frame.copy()
            cv2.line(overlay, (x, line_y), (x + current_width, line_y), 
                    VisualEffects.UNDERLINE_COLOR, line_thickness)
            
            # Blend с оригиналом
            alpha = 0.8
            frame = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)
            
            # "Волна" на конце: пульсирующий круг
            if eased < 1.0:  # Только пока линия еще рисуется
                wave_x = x + current_width
                wave_radius = int(4 + 2 * np.sin(progress * 10 * np.pi))  # Быстрая пульсация
                wave_alpha = 0.6
                
                wave_overlay = frame.copy()
                cv2.circle(wave_overlay, (wave_x, line_y), wave_radius, 
                          VisualEffects.UNDERLINE_COLOR, -1)
                frame = cv2.addWeighted(frame, 1 - wave_alpha, wave_overlay, wave_alpha, 0)
            
            return frame
            
        except Exception as e:
            logger.error(f"Ошибка применения underline эффекта: {e}")
            return frame
    
    @staticmethod
    def apply_fade_in(frame: np.ndarray, bbox: List[float], t0: float, t1: float, current_time: float) -> np.ndarray:
        """
        Применяет fade-in эффект к области bbox
        
        Args:
            frame: Кадр изображения (numpy array в RGB)
            bbox: Bounding box [x, y, width, height]
            t0: Время начала эффекта
            t1: Время окончания эффекта
            current_time: Текущее время
            
        Returns:
            Модифицированный кадр
        """
        try:
            if len(bbox) < 4:
                return frame
            
            x, y, w, h = map(int, bbox)
            
            # Проверка границ
            if x < 0 or y < 0 or x + w > frame.shape[1] or y + h > frame.shape[0]:
                return frame
            
            # Вычисляем прогресс
            duration = t1 - t0
            if duration <= 0:
                return frame
            
            progress = (current_time - t0) / duration
            progress = max(0.0, min(1.0, progress))
            
            # Создаем белый overlay с изменяющейся прозрачностью
            alpha = 1.0 - progress  # От 1.0 до 0.0
            
            overlay = frame.copy()
            overlay[y:y+h, x:x+w] = [255, 255, 255]  # Белый цвет
            
            frame = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)
            
            return frame
            
        except Exception as e:
            logger.error(f"Ошибка применения fade_in эффекта: {e}")
            return frame
    
    @staticmethod
    def apply_fade_out(frame: np.ndarray, bbox: List[float], t0: float, t1: float, current_time: float) -> np.ndarray:
        """
        Применяет fade-out эффект к области bbox
        
        Args:
            frame: Кадр изображения (numpy array в RGB)
            bbox: Bounding box [x, y, width, height]
            t0: Время начала эффекта
            t1: Время окончания эффекта
            current_time: Текущее время
            
        Returns:
            Модифицированный кадр
        """
        try:
            if len(bbox) < 4:
                return frame
            
            x, y, w, h = map(int, bbox)
            
            # Проверка границ
            if x < 0 or y < 0 or x + w > frame.shape[1] or y + h > frame.shape[0]:
                return frame
            
            # Вычисляем прогресс
            duration = t1 - t0
            if duration <= 0:
                return frame
            
            progress = (current_time - t0) / duration
            progress = max(0.0, min(1.0, progress))
            
            # Создаем черный overlay с увеличивающейся прозрачностью
            alpha = progress  # От 0.0 до 1.0
            
            overlay = frame.copy()
            overlay[y:y+h, x:x+w] = [0, 0, 0]  # Черный цвет
            
            frame = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)
            
            return frame
            
        except Exception as e:
            logger.error(f"Ошибка применения fade_out эффекта: {e}")
            return frame


def create_text_overlay(frame: np.ndarray, text: str, position: Tuple[int, int], 
                       font_scale: float = 1.0, color: Tuple[int, int, int] = (255, 255, 255),
                       thickness: int = 2) -> np.ndarray:
    """
    Вспомогательная функция для добавления текста на кадр
    
    Args:
        frame: Кадр изображения
        text: Текст для отображения
        position: Позиция (x, y)
        font_scale: Размер шрифта
        color: Цвет текста (BGR)
        thickness: Толщина линий текста
        
    Returns:
        Кадр с текстом
    """
    try:
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Добавляем тень для лучшей читаемости
        shadow_offset = 2
        cv2.putText(frame, text, (position[0] + shadow_offset, position[1] + shadow_offset),
                   font, font_scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
        
        # Добавляем основной текст
        cv2.putText(frame, text, position, font, font_scale, color, thickness, cv2.LINE_AA)
        
        return frame
        
    except Exception as e:
        logger.error(f"Ошибка добавления текста на кадр: {e}")
        return frame
