"""
Smart Visual Cue Generator
Matches OCR text elements with TTS word timings to create precise highlights
"""
import logging
from typing import List, Dict, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SmartCueGenerator:
    """
    Generates visual cues by matching OCR text elements with TTS word timings.
    Uses fuzzy text matching to find when specific text elements are spoken.
    """
    
    def __init__(self, similarity_threshold: float = 0.6):
        """
        Args:
            similarity_threshold: Минимальное сходство текста для сопоставления (0-1)
        """
        self.similarity_threshold = similarity_threshold
    
    def generate_cues_from_timings(
        self,
        elements: List[Dict],
        speaker_notes: str,
        word_timings: List[Dict],
        audio_duration: float
    ) -> List[Dict]:
        """
        Генерирует визуальные cues на основе таймингов слов из TTS.
        
        Args:
            elements: OCR элементы с текстом и bbox координатами
            speaker_notes: Полный текст лекции
            word_timings: Список таймингов слов из Google TTS API
            audio_duration: Длительность аудио
            
        Returns:
            List[Dict]: Список cues с точными таймингами
        """
        if not elements:
            logger.warning("No OCR elements provided")
            return []
        
        if not word_timings:
            logger.warning("No word timings provided, falling back to simple distribution")
            return self._generate_simple_cues(elements, audio_duration)
        
        cues = []
        
        # Normalize speaker notes for matching
        normalized_notes = self._normalize_text(speaker_notes)
        
        for element in elements:
            element_text = element.get('text', '').strip()
            if not element_text or not element.get('bbox'):
                continue
            
            # Найти когда этот текст упоминается в лекции
            matches = self._find_text_mentions(
                element_text,
                normalized_notes,
                word_timings
            )
            
            if matches:
                # Создать cue для каждого упоминания
                for i, match in enumerate(matches):
                    cue = {
                        't0': match['start_time'],
                        't1': match['end_time'],
                        'action': 'highlight' if i % 2 == 0 else 'underline',
                        'bbox': element['bbox'],
                        'text': element_text,
                        'confidence': match.get('confidence', 1.0)
                    }
                    cues.append(cue)
                    logger.debug(f"Created cue for '{element_text[:30]}' at {match['start_time']:.1f}s")
            else:
                # Если не нашли точное совпадение, используем простую эвристику
                logger.debug(f"No timing match for '{element_text[:30]}', using fallback")
                fallback_cue = self._create_fallback_cue(element, audio_duration, len(elements))
                if fallback_cue:
                    cues.append(fallback_cue)
        
        # Сортируем по времени начала
        cues.sort(key=lambda c: c['t0'])
        
        logger.info(f"Generated {len(cues)} smart cues from {len(elements)} OCR elements and {len(word_timings)} word timings")
        return cues
    
    def _normalize_text(self, text: str) -> str:
        """Нормализует текст для сопоставления"""
        import re
        # Удаляем SSML теги
        text = re.sub(r'<[^>]+>', '', text)
        # Приводим к нижнему регистру
        text = text.lower()
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _normalize_for_matching(self, word: str) -> str:
        """
        Нормализует слово для сопоставления с mark_name:
        - убирает умлауты (ä->a, ö->o, ü->u, ß->ss)
        - убирает пунктуацию
        - приводит к нижнему регистру
        """
        import re
        word = word.lower()
        # Заменяем немецкие умлауты
        replacements = {
            'ä': 'a', 'ö': 'o', 'ü': 'u', 'ß': 'ss',
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'
        }
        for old, new in replacements.items():
            word = word.replace(old, new)
        # Убираем пунктуацию
        word = re.sub(r'[^\w\s]', '', word)
        return word.strip()
    
    def _find_text_mentions(
        self,
        element_text: str,
        full_text: str,
        word_timings: List[Dict]
    ) -> List[Dict]:
        """
        Находит все упоминания текста элемента сопоставляя с mark_name из word_timings.
        
        Returns:
            List[Dict]: Список словарей с start_time, end_time, confidence
        """
        if not word_timings:
            return []
        
        normalized_element = self._normalize_text(element_text)
        
        # Разбиваем текст элемента на слова
        element_words = normalized_element.split()
        if not element_words:
            return []
        
        matches = []
        
        # Google TTS возвращает marks с именами слов из SSML
        # Сопоставляем OCR текст с mark_name из word_timings
        if word_timings and 'mark_name' in word_timings[0]:
            # Создаем список mark names для поиска
            mark_names = [wt['mark_name'].lower() for wt in word_timings]
            
            logger.debug(f"Matching '{element_text}' against {len(mark_names)} marks")
            
            # Для каждого слова в элементе пытаемся найти соответствующий mark
            for element_word in element_words:
                # Нормализуем слово (удаляем пунктуацию, умлауты)
                normalized_word = self._normalize_for_matching(element_word)
                
                # Ищем наиболее похожий mark
                best_match_idx = -1
                best_similarity = 0.0
                
                for i, mark_name in enumerate(mark_names):
                    similarity = self._text_similarity(normalized_word, mark_name)
                    if similarity > best_similarity and similarity >= self.similarity_threshold:
                        best_similarity = similarity
                        best_match_idx = i
                
                if best_match_idx >= 0:
                    # Нашли совпадение!
                    start_time = word_timings[best_match_idx]['time_seconds']
                    # Конец - это следующий mark или +2 секунды
                    if best_match_idx + 1 < len(word_timings):
                        end_time = word_timings[best_match_idx + 1]['time_seconds']
                    else:
                        end_time = start_time + 2.0
                    
                    # Добавляем буфер для показа (минимум 1.5с)
                    duration = end_time - start_time
                    if duration < 1.5:
                        end_time = start_time + 1.5
                    
                    match = {
                        'start_time': start_time,
                        'end_time': end_time,
                        'confidence': best_similarity
                    }
                    matches.append(match)
                    logger.debug(f"  Matched '{element_word}' -> mark '{mark_names[best_match_idx]}' at {start_time:.1f}s (similarity: {best_similarity:.2f})")
                    break  # Нашли первое совпадение для этого элемента
            
            # Если нашли несколько слов из элемента, берем первое
            if matches:
                return matches[:1]  # Возвращаем только первое совпадение
        
        return []
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Вычисляет сходство двух текстов (0-1)"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _generate_simple_cues(self, elements: List[Dict], audio_duration: float) -> List[Dict]:
        """
        Простая генерация cues - равномерное распределение по времени
        (fallback когда нет word timings)
        """
        cues = []
        time_per_element = audio_duration / len(elements) if elements else 1.0
        
        for idx, element in enumerate(elements):
            if not element.get('bbox'):
                continue
            
            start_time = idx * time_per_element
            end_time = start_time + time_per_element * 0.8
            
            cue = {
                't0': round(start_time, 2),
                't1': round(end_time, 2),
                'action': 'highlight' if idx % 2 == 0 else 'underline',
                'bbox': element['bbox'],
                'text': element.get('text', '')
            }
            cues.append(cue)
        
        return cues
    
    def _create_fallback_cue(self, element: Dict, audio_duration: float, total_elements: int) -> Optional[Dict]:
        """Создает fallback cue для элемента"""
        if not element.get('bbox'):
            return None
        
        # Показываем в случайное время в первой половине аудио
        import random
        start_time = random.uniform(0, audio_duration * 0.5)
        end_time = start_time + min(2.0, audio_duration * 0.1)
        
        return {
            't0': round(start_time, 2),
            't1': round(end_time, 2),
            'action': 'highlight',
            'bbox': element['bbox'],
            'text': element.get('text', ''),
            'confidence': 0.3  # Низкая уверенность для fallback
        }
