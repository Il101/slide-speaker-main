"""
Bullet Point Synchronization Service
Синхронизирует визуальные эффекты с TTS для bullet points через Whisper
"""

import logging
import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available. Install: pip install openai-whisper")

logger = logging.getLogger(__name__)


def _check_whisper_availability() -> bool:
    """Check if Whisper is available"""
    return WHISPER_AVAILABLE


class BulletPointSyncService:
    """
    Сервис для точной синхронизации bullet points с аудио
    
    Workflow:
    1. TTS генерирует аудио с group markers в SSML
    2. Whisper распознаёт аудио и даёт word-level timing
    3. Сопоставляем group markers с Whisper timings через текстовое совпадение
    4. Генерируем точные визуальные эффекты для каждого bullet point
    """
    
    def __init__(self, whisper_model: str = "base"):
        """
        Args:
            whisper_model: Модель Whisper (tiny, base, small, medium, large)
                          base - оптимальный баланс скорость/качество
        
        ✅ OPTIMIZATION: Whisper загружается ТОЛЬКО если:
        1. TTS_PROVIDER=silero (не поддерживает word timing)
        2. Метод sync_bullet_points вызван (lazy loading)
        """
        self.whisper_model_name = whisper_model
        self.whisper_model = None  # Lazy loading
        
        # Check TTS provider to decide if Whisper is needed
        tts_provider = os.getenv("TTS_PROVIDER", "google").lower()
        self.needs_whisper = tts_provider in ("silero", "azure", "mock")
        
        if self.needs_whisper:
            logger.info(f"🎤 Whisper timing enabled for TTS provider: {tts_provider}")
        else:
            logger.info(f"✅ Native timing available for TTS provider: {tts_provider} (Whisper not needed)")
    
    def _load_whisper_model(self):
        """
        Lazy load Whisper model (ONLY when needed)
        
        ✅ OPTIMIZATION: Checks if Whisper is needed before loading
        - Google TTS: Skip Whisper (native word timing via <mark> tags)
        - Silero TTS: Load Whisper (need to extract timing from audio)
        """
        if not self.needs_whisper:
            logger.debug("Whisper not needed for current TTS provider")
            return
        
        if self.whisper_model is None and _check_whisper_availability():
            logger.info(f"📦 Loading Whisper model: {self.whisper_model_name}")
            import whisper  # Import only when needed
            self.whisper_model = whisper.load_model(self.whisper_model_name)
            logger.info("✅ Whisper model loaded")
    
    def sync_bullet_points(
        self,
        audio_path: str,
        talk_track_raw: List[Dict[str, Any]],
        semantic_map: Dict[str, Any],
        elements: List[Dict[str, Any]] = None,
        slide_language: str = "en",
        use_element_matching: bool = True,
        audio_duration: Optional[float] = None,
        tts_words: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Основной метод: синхронизирует bullet points с аудио

        Args:
            audio_path: Путь к аудио файлу (сгенерированному TTS)
            talk_track_raw: Talk track с group markers (из плана)
            semantic_map: Семантическая карта слайда (группы элементов)
            slide_language: Язык слайда (для определения несоответствия с TTS)
            audio_duration: Реальная длительность аудио в секундах (для fallback)
            tts_words: TTS data с word_timings и sentences (для Google TTS)

        Returns:
            List[Dict]: Обогащённые cues с точными таймингами для bullet points
            [
                {
                    "action": "highlight",
                    "bbox": [x, y, w, h],
                    "t0": 1.25,
                    "t1": 3.47,
                    "group_id": "group_bullets_001",
                    "text": "Faster performance",
                    "timing_source": "whisper"  # whisper|word_level|sentence|fallback
                }
            ]
        """

        # ✅ PRIORITY 1: Use word-level timing from Google TTS if available
        if tts_words and tts_words.get('word_timings'):
            logger.info("✅ Using word-level timing from Google TTS")
            cues = self._word_level_sync(tts_words, semantic_map, elements)
            if cues:
                return cues
            else:
                logger.warning("Word-level sync returned no cues, falling back to sentence-level")

        # ✅ PRIORITY 2: Skip Whisper if TTS provider has native timing
        if not self.needs_whisper:
            logger.info("✅ Using sentence-level TTS timing (Google/native provider) - Whisper not needed")
            return self._fallback_sync(talk_track_raw, semantic_map, elements, audio_duration)

        if not _check_whisper_availability() or not Path(audio_path).exists():
            logger.warning("Whisper unavailable or audio missing - using fallback")
            return self._fallback_sync(talk_track_raw, semantic_map, elements, audio_duration)
        
        try:
            # 1. Распознаём аудио через Whisper с word timestamps
            logger.info(f"🎙️ Running Whisper on {audio_path}...")
            self._load_whisper_model()
            
            result = self.whisper_model.transcribe(
                audio_path,
                word_timestamps=True,
                language=None  # Auto-detect (работает с любым языком)
            )
            
            # 2. Извлекаем word-level timings
            word_timings = self._extract_word_timings(result)
            logger.info(f"✅ Whisper: extracted {len(word_timings)} word timings")

            # 3. Сопоставляем group markers с Whisper словами
            if use_element_matching and elements:
                # ✅ NEW: Match groups by their element text (more reliable)
                group_timings = self._match_groups_by_elements(
                    semantic_map,
                    elements,
                    word_timings
                )
            else:
                # Fallback: match by talk_track text
                group_timings = self._match_groups_to_words(
                    talk_track_raw,
                    word_timings
                )
            
            # 4. Генерируем visual cues для каждой группы
            cues = self._generate_cues_from_timings(
                group_timings,
                semantic_map,
                elements or [],
                word_timings  # Pass word timings for element-level sync
            )
            
            logger.info(f"✅ Generated {len(cues)} synced bullet point cues")
            return cues

        except Exception as e:
            logger.error(f"Error in bullet sync: {e}", exc_info=True)
            return self._fallback_sync(talk_track_raw, semantic_map, elements, audio_duration)
    
    def _extract_word_timings(self, whisper_result: Dict) -> List[Dict[str, Any]]:
        """
        Извлекает word-level timings из результата Whisper
        
        Returns:
            [
                {"word": "hello", "start": 0.0, "end": 0.5},
                {"word": "world", "start": 0.6, "end": 1.2},
                ...
            ]
        """
        word_timings = []
        
        for segment in whisper_result.get('segments', []):
            for word_data in segment.get('words', []):
                word_timings.append({
                    'word': word_data['word'].strip().lower(),
                    'start': word_data['start'],
                    'end': word_data['end']
                })
        
        return word_timings
    
    def _normalize_text(self, text: str) -> str:
        """Нормализация текста для сравнения"""
        import unicodedata
        
        # Удаляем SSML markers
        text = re.sub(r'\[visual:[a-z]{2}\].*?\[/visual\]', '', text)
        text = re.sub(r'\[lang:[a-z]{2}\](.*?)\[/lang\]', r'\1', text)
        text = re.sub(r'\[phoneme:ipa:.*?\](.*?)\[/phoneme\]', r'\1', text)
        
        # ✅ FIX: Remove combining accents (ударения)
        # "микроско́п" → "микроскоп"
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        text = unicodedata.normalize('NFC', text)
        
        # Удаляем пунктуацию и приводим к нижнему регистру
        text = re.sub(r'[^\w\s]', '', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _match_groups_by_elements(
        self,
        semantic_map: Dict[str, Any],
        elements: List[Dict[str, Any]],
        word_timings: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Сопоставляет группы напрямую с Whisper через текст элементов

        Strategy:
        1. Для каждой группы берём текст её элементов
        2. Ищем эти слова в Whisper word timings
        3. Используем первое и последнее вхождение для определения границ

        Returns:
            {"group_id": {"t0": start, "t1": end}}
        """
        group_timings = {}

        # Create element lookup
        elements_by_id = {elem.get('id'): elem for elem in elements}

        # Process each group
        groups = semantic_map.get('groups', [])
        for group in groups:
            group_id = group.get('id')
            group_type = group.get('type', '')

            # Skip non-content groups
            if group_type in ['watermark', 'decoration', 'noise']:
                continue

            # Collect text from all elements in group
            element_ids = group.get('element_ids', [])
            group_texts = []
            for elem_id in element_ids:
                elem = elements_by_id.get(elem_id)
                if elem:
                    # Use translated text for matching with Whisper (if available)
                    text = elem.get('text_translated') or elem.get('text', '')
                    text = text.strip()
                    if text:
                        group_texts.append(text)

            if not group_texts:
                logger.warning(f"Group {group_id} has no text elements")
                continue

            # Normalize and extract words
            all_words = []
            for text in group_texts:
                normalized = self._normalize_text(text)
                words = [w for w in normalized.split() if len(w) > 2]  # Skip very short words
                all_words.extend(words)

            if not all_words:
                continue

            # Find these words in Whisper timings
            matched_indices = []
            for word in all_words[:10]:  # Check first 10 words to avoid too long search
                for i, wt in enumerate(word_timings):
                    whisper_word = wt['word'].lower()
                    if word in whisper_word or whisper_word in word:
                        matched_indices.append(i)
                        break

            if len(matched_indices) >= 1:
                # ✅ IMPROVED: Use clustering to find compact timing range
                # Instead of first-last (which can be too wide), find the most dense cluster
                first_idx = min(matched_indices)
                last_idx = max(matched_indices)

                # Check if timing is too wide (more than 20 seconds)
                t0_candidate = word_timings[first_idx]['start']
                t1_candidate = word_timings[last_idx]['end']
                duration = t1_candidate - t0_candidate

                if duration > 20:
                    # Too wide! Find a more compact cluster
                    # Strategy: use median indices instead of min/max
                    sorted_indices = sorted(matched_indices)

                    # Take middle 80% to exclude outliers
                    trim_count = max(1, len(sorted_indices) // 10)
                    trimmed_indices = sorted_indices[trim_count:-trim_count] if len(sorted_indices) > 4 else sorted_indices

                    first_idx = trimmed_indices[0]
                    last_idx = trimmed_indices[-1]

                    logger.info(f"   ⚠️ Wide timing detected ({duration:.1f}s), using compact cluster")

                # Expand range slightly to capture full phrase
                last_idx = min(last_idx + 3, len(word_timings) - 1)

                t0 = word_timings[first_idx]['start']
                t1 = word_timings[last_idx]['end']

                group_timings[group_id] = {
                    't0': round(t0, 2),
                    't1': round(t1, 2)
                }
                logger.info(f"✅ Matched '{group_id}' by elements: {t0:.2f}s - {t1:.2f}s ({len(matched_indices)} words, duration: {t1-t0:.1f}s)")
            else:
                logger.warning(f"⚠️ Could not match '{group_id}' (text: {' '.join(all_words[:3])}...)")

        return group_timings

    def _match_groups_to_words(
        self,
        talk_track_raw: List[Dict[str, Any]],
        word_timings: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Сопоставляет group markers с Whisper word timings
        
        Strategy:
        1. Для каждого segment с group_id ищем его текст в Whisper
        2. Находим первое и последнее слово этого сегмента
        3. Берём timing первого слова как t0, последнего как t1
        
        Returns:
            {
                "group_bullets_001": {"t0": 1.25, "t1": 3.47},
                "group_title_001": {"t0": 0.0, "t1": 1.20},
                ...
            }
        """
        group_timings = {}
        
        # Создаём непрерывную строку из всех Whisper слов для поиска
        whisper_text = " ".join([w['word'] for w in word_timings])
        
        for segment in talk_track_raw:
            group_id = segment.get('group_id')
            if not group_id:
                continue
            
            segment_text = self._normalize_text(segment.get('text', ''))
            if not segment_text:
                continue
            
            # Разбиваем текст сегмента на слова
            segment_words = segment_text.split()
            
            if not segment_words:
                continue
            
            # Ищем первое и последнее слово сегмента в Whisper timings
            first_word = segment_words[0]
            last_word = segment_words[-1]
            
            # Находим первое вхождение первого слова
            t0 = None
            for i, wt in enumerate(word_timings):
                if first_word in wt['word'] or wt['word'] in first_word:
                    # Проверяем, что это начало нашего сегмента
                    # (не середина другого сегмента)
                    context_words = [word_timings[j]['word'] for j in range(i, min(i+3, len(word_timings)))]
                    context = " ".join(context_words)
                    
                    if any(sw in context for sw in segment_words[:3]):
                        t0 = wt['start']
                        start_index = i
                        break
            
            # Находим последнее вхождение последнего слова (от найденного начала)
            t1 = None
            if t0 is not None:
                for i in range(start_index, len(word_timings)):
                    wt = word_timings[i]
                    if last_word in wt['word'] or wt['word'] in last_word:
                        t1 = wt['end']
                        # Не break - берём последнее вхождение
            
            # Если нашли оба тайминга
            if t0 is not None and t1 is not None:
                group_timings[group_id] = {
                    't0': round(t0, 2),
                    't1': round(t1, 2)
                }
                logger.info(f"✅ Matched '{group_id}': {t0:.2f}s - {t1:.2f}s")
            else:
                logger.warning(f"⚠️ Could not match '{group_id}' text: '{segment_text[:50]}'")
        
        return group_timings
    
    def _generate_cues_from_timings(
        self,
        group_timings: Dict[str, Dict[str, float]],
        semantic_map: Dict[str, Any],
        elements: List[Dict[str, Any]],
        word_timings: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Генерирует visual cues из group timings и semantic map

        Args:
            group_timings: {"group_id": {"t0": 1.2, "t1": 3.4}}
            semantic_map: Семантическая карта с bbox для групп
            elements: Список элементов слайда с bbox

        Returns:
            Список cues для визуальных эффектов
        """
        cues = []

        groups = semantic_map.get('groups', [])

        # ✅ FIX: elements come from slide, not semantic_map
        # Create element lookup by ID
        elements_by_id = {elem.get('id'): elem for elem in elements}

        for group in groups:
            # ✅ FIX: semantic_map uses 'id' field, not 'group_id'
            group_id = group.get('id')
            group_type = group.get('type', 'text')

            # Получаем timing для этой группы
            timing = group_timings.get(group_id)

            if not timing:
                logger.warning(f"No timing for group {group_id}")
                continue

            # Определяем визуальный эффект на основе типа группы
            if group_type == 'bullet_list':
                action = 'highlight'
            elif group_type == 'title':
                action = 'underline'
            elif group_type == 'image':
                action = 'zoom_in'
            else:
                action = 'highlight'

            # ✅ FIX: semantic_map has 'element_ids', not 'elements'
            # Get elements from element_ids list
            element_ids = group.get('element_ids', [])

            # ✅ NEW ALGORITHM: Sequential timing for all elements in group
            # Instead of finding individual timing for each element independently,
            # we find ALL mentions first, then assign sequential timing windows

            # Step 1: Collect all elements with their match info
            element_matches = []

            for element_id in element_ids:
                element = elements_by_id.get(element_id)
                if not element:
                    logger.warning(f"Element {element_id} not found in semantic_map")
                    continue

                bbox = element.get('bbox')
                if not bbox:
                    logger.warning(f"Element {element_id} has no bbox")
                    continue

                text_original = element.get('text_original') or element.get('text', '')
                text_translated = element.get('text_translated') or element.get('text', '')

                element_matches.append({
                    'element_id': element_id,
                    'element': element,
                    'bbox': bbox,
                    'text_original': text_original,
                    'text_translated': text_translated,
                    'first_mention_time': None
                })

            # Step 2: Find first mention time for each element in Whisper timings
            if word_timings:
                group_words = [wt for wt in word_timings if timing['t0'] <= wt['start'] <= timing['t1']]

                for match in element_matches:
                    text = match['text_translated'].strip()
                    first_time = self._find_first_mention_time(text, group_words)
                    match['first_mention_time'] = first_time

            # Step 3: Sort elements by first mention time (sequential order)
            # Elements with no match go to the end
            element_matches.sort(key=lambda m: m['first_mention_time'] if m['first_mention_time'] is not None else 999999)

            # Step 4: Assign sequential timing windows
            for i, match in enumerate(element_matches):
                # Calculate timing for this element
                if match['first_mention_time'] is not None:
                    # Use first mention as start
                    t0 = match['first_mention_time']

                    # Find end time: either next element's start, or group end
                    if i + 1 < len(element_matches) and element_matches[i + 1]['first_mention_time'] is not None:
                        t1 = element_matches[i + 1]['first_mention_time']
                    else:
                        t1 = timing['t1']

                    # Ensure minimum duration of 0.5s
                    if t1 - t0 < 0.5:
                        t1 = min(t0 + 0.5, timing['t1'])

                    element_timing = {'t0': round(t0, 2), 't1': round(t1, 2)}
                    timing_source = 'whisper_sequential'
                    logger.info(f"   🎯 Sequential timing for '{match['text_translated'][:40]}': {t0:.2f}s-{t1:.2f}s ({t1-t0:.1f}s)")
                else:
                    # No match found, use group timing
                    element_timing = timing
                    timing_source = 'whisper_group'
                    logger.debug(f"   ⚠️ No timing for '{match['text_translated'][:40]}', using group timing")

                # Create cue
                cue = {
                    'action': action,
                    'bbox': match['bbox'],
                    't0': element_timing['t0'],
                    't1': element_timing['t1'],
                    'group_id': group_id,
                    'element_id': match['element_id'],
                    'text': match['text_original'].strip(),
                    'text_original': match['text_original'].strip(),
                    'text_translated': match['text_translated'].strip(),
                    'timing_source': timing_source
                }

                cues.append(cue)
                logger.info(f"✅ Created cue for {group_id}/{match['element_id']}: {element_timing['t0']:.2f}s - {element_timing['t1']:.2f}s")

        return cues

    def _find_element_timing_in_words(
        self,
        element_text: str,
        word_timings: List[Dict[str, Any]],
        group_t0: float,
        group_t1: float
    ) -> Optional[Dict[str, float]]:
        """
        Находит точный timing для конкретного элемента (bullet point) внутри группы
        Использует fuzzy matching для лучшей работы с переведенным текстом

        Args:
            element_text: Текст элемента (переведенный на язык TTS)
            word_timings: Whisper word-level timings
            group_t0, group_t1: Временные границы группы

        Returns:
            {"t0": start_time, "t1": end_time} или None
        """
        # Normalize element text
        element_normalized = self._normalize_text(element_text)
        element_words = set(element_normalized.split())  # Use set for fuzzy matching

        if len(element_words) == 0:
            return None

        # Filter word timings to group time range
        group_words = [
            wt for wt in word_timings
            if group_t0 <= wt['start'] <= group_t1
        ]

        if not group_words:
            return None

        # NEW ALGORITHM: Find all words that match element words (fuzzy)
        # Then create a timing window that covers matched words
        matched_indices = []

        for i, wt in enumerate(group_words):
            word_normalized = self._normalize_text(wt['word'])

            # Check if this Whisper word matches any element word
            for elem_word in element_words:
                if len(elem_word) < 3:
                    # Short words: exact match
                    if word_normalized == elem_word:
                        matched_indices.append(i)
                        break
                else:
                    # Long words: fuzzy match (substring or vice versa)
                    if elem_word in word_normalized or word_normalized in elem_word:
                        matched_indices.append(i)
                        break
                    # Also check for common prefix (at least 4 chars)
                    min_len = min(len(elem_word), len(word_normalized))
                    if min_len >= 4:
                        # Check if words share 70% of characters
                        common_prefix_len = 0
                        for c1, c2 in zip(elem_word, word_normalized):
                            if c1 == c2:
                                common_prefix_len += 1
                            else:
                                break
                        if common_prefix_len >= min_len * 0.7:
                            matched_indices.append(i)
                            break

        if not matched_indices:
            return None

        # If we matched too few words relative to element size, it's unreliable
        match_ratio = len(matched_indices) / len(element_words)
        if match_ratio < 0.3:  # At least 30% of words should match
            return None

        # Sort indices to get continuous time range
        matched_indices.sort()

        # Use first and last matched word to create timing window
        start_idx = matched_indices[0]
        end_idx = matched_indices[-1]

        # Extract timing from group_words
        t0 = group_words[start_idx]['start']
        t1 = group_words[end_idx]['end']

        # Sanity check: timing should be within group and reasonable duration
        duration = t1 - t0
        if t0 >= group_t0 and t1 <= group_t1 and duration < 15:  # Max 15s per element
            return {'t0': round(t0, 2), 't1': round(t1, 2)}

        return None

    def _find_first_mention_time(
        self,
        element_text: str,
        group_words: List[Dict[str, Any]],
        min_word_length: int = 4  # ✅ Ignore very common short words
    ) -> Optional[float]:
        """
        Находит время первого упоминания элемента в Whisper timings
        
        ✅ IMPROVED: Better word matching with length filtering

        Args:
            element_text: Текст элемента (переведенный)
            group_words: Whisper word timings внутри группы
            min_word_length: Minimum word length to consider (default 4)

        Returns:
            Время первого слова элемента или None
        """
        element_normalized = self._normalize_text(element_text)
        # ✅ FIX: Filter out very short/common words that cause false matches
        element_words = [w for w in element_normalized.split() if len(w) >= min_word_length]

        if len(element_words) == 0:
            # Fallback: try with shorter words if no long words found
            element_words = [w for w in element_normalized.split() if len(w) >= 3]
        
        if len(element_words) == 0:
            return None
        
        # ✅ IMPROVED: Score-based matching instead of first-match
        # This prevents matching common words that appear everywhere
        best_match_time = None
        best_match_score = 0.0

        # Find first word from element that appears in Whisper
        for wt in group_words:
            word_normalized = self._normalize_text(wt['word'])
            
            # Skip very short Whisper words (articles, prepositions)
            if len(word_normalized) < 3:
                continue

            # Check if this Whisper word matches any element word
            for elem_word in element_words:
                match_score = 0.0
                
                if len(elem_word) < 4:
                    # Short words: exact match only (higher threshold)
                    if word_normalized == elem_word:
                        match_score = 1.0
                else:
                    # Long words: fuzzy match
                    if elem_word == word_normalized:
                        match_score = 1.0  # Perfect match
                    elif elem_word in word_normalized or word_normalized in elem_word:
                        match_score = 0.8  # Substring match
                    else:
                        # Check for common prefix (70% match)
                        min_len = min(len(elem_word), len(word_normalized))
                        if min_len >= 4:
                            common_prefix_len = 0
                            for c1, c2 in zip(elem_word, word_normalized):
                                if c1 == c2:
                                    common_prefix_len += 1
                                else:
                                    break
                            if common_prefix_len >= min_len * 0.7:
                                match_score = 0.6  # Prefix match
                
                # ✅ Prefer first occurrence of best matching word
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_match_time = wt['start']
                    
                    # If perfect match found, use it immediately
                    if match_score >= 0.9:
                        return best_match_time

        return best_match_time if best_match_score >= 0.6 else None

    def _word_level_sync(
        self,
        tts_words: Dict[str, Any],
        semantic_map: Dict[str, Any],
        elements: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Точная синхронизация используя word_timings из Google TTS

        Args:
            tts_words: TTS data с word_timings и sentences
            semantic_map: Семантическая карта слайда
            elements: Элементы слайда

        Returns:
            List of visual cues with precise word-level timing
        """
        logger.info("Using word-level sync from Google TTS word_timings")

        cues = []
        groups = semantic_map.get('groups', [])
        elements_by_id = {elem.get('id'): elem for elem in (elements or [])}

        # Get word timings and sentences
        word_timings = tts_words.get('word_timings', [])
        sentences = tts_words.get('sentences', [])

        if not word_timings or not sentences:
            logger.warning("No word_timings or sentences in tts_words, falling back")
            return []

        # ✅ NEW APPROACH: Find time ranges for each group using group_ markers
        # Then distribute elements within group time range
        group_time_ranges = {}

        for i, wt in enumerate(word_timings):
            mark_name = wt.get('mark_name', '')
            if mark_name.startswith('group_'):
                t0 = wt.get('time_seconds', 0)
                # Find next group marker or end
                t1 = None
                for j in range(i + 1, len(word_timings)):
                    next_mark = word_timings[j].get('mark_name', '')
                    if next_mark.startswith('group_'):
                        t1 = word_timings[j].get('time_seconds', 0)
                        break

                if t1 is None:
                    # Use last marker time or sentence end
                    if word_timings:
                        t1 = word_timings[-1].get('time_seconds', 0) + 1.0
                    else:
                        t1 = t0 + 10.0

                group_time_ranges[mark_name] = (t0, t1)

        logger.info(f"Found {len(group_time_ranges)} group time ranges from markers")

        # ✅ Create cues by distributing elements within their group time range
        for group in groups:
            group_type = group.get('type', 'text')
            if group_type in ['watermark', 'decoration', 'noise']:
                continue

            group_id = group.get('id')
            element_ids = group.get('element_ids', [])
            action = 'highlight' if group_type == 'bullet_list' else 'underline'

            # Find time range for this group
            group_t0, group_t1 = group_time_ranges.get(group_id, (None, None))
            if group_t0 is None or group_t1 is None:
                logger.debug(f"No time range found for group {group_id}, skipping")
                continue

            # Distribute elements evenly within group time range
            num_elements = len(element_ids)
            if num_elements == 0:
                continue

            group_duration = group_t1 - group_t0
            time_per_element = group_duration / num_elements
            min_duration = 0.5  # Minimum 0.5s per element

            logger.debug(f"Group {group_id}: {num_elements} elements in {group_duration:.1f}s ({time_per_element:.1f}s each)")

            for idx, elem_id in enumerate(element_ids):
                elem = elements_by_id.get(elem_id)
                if not elem:
                    continue

                bbox = elem.get('bbox')
                if not bbox:
                    continue

                # Calculate staggered timing within group range
                elem_t0 = group_t0 + (idx * time_per_element)
                elem_t1 = min(elem_t0 + time_per_element * 1.2, group_t1)  # 20% overlap

                # Ensure minimum duration
                if elem_t1 - elem_t0 < min_duration:
                    elem_t1 = elem_t0 + min_duration

                original_text = elem.get('text_original') or elem.get('text', '')
                cues.append({
                    'action': action,
                    'bbox': bbox,
                    't0': round(elem_t0, 2),
                    't1': round(elem_t1, 2),
                    'group_id': group_id,
                    'element_id': elem_id,
                    'text': original_text,
                    'timing_source': 'word_level_distributed'
                })
                logger.debug(f"Element {idx+1}/{num_elements}: '{original_text[:30]}' -> {elem_t0:.2f}s-{elem_t1:.2f}s")

        logger.info(f"Created {len(cues)} word-level cues")
        return cues

    def _fallback_sync(
        self,
        talk_track_raw: List[Dict[str, Any]],
        semantic_map: Dict[str, Any],
        elements: List[Dict[str, Any]] = None,
        audio_duration: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback: используем sentence-level timing без Whisper

        Args:
            talk_track_raw: Talk track с group markers
            semantic_map: Семантическая карта слайда
            elements: Элементы слайда
            audio_duration: Реальная длительность аудио в секундах

        Менее точно, но работает без дополнительных зависимостей
        """
        logger.warning("Using fallback sentence-level sync")

        cues = []
        groups = semantic_map.get('groups', [])

        # ✅ FIX: If no talk_track segments, create simple sequential cues
        if not talk_track_raw or not any(seg.get('group_id') for seg in talk_track_raw):
            logger.warning("No talk_track with group_id, creating simple time-based cues")
            # Create element lookup
            elements_by_id = {elem.get('id'): elem for elem in (elements or [])}

            # ✅ FIX: Use real audio duration if provided, otherwise estimate from talk_track
            total_duration = audio_duration
            if total_duration is None:
                total_duration = max((seg.get('end', 0) for seg in talk_track_raw), default=10.0)
            if total_duration == 0:
                total_duration = 10.0

            logger.info(f"📊 Distributing {len(groups)} groups across {total_duration:.1f}s audio")

            # Filter out non-content groups first
            content_groups = [g for g in groups
                            if g.get('type') not in ['watermark', 'decoration', 'noise']]

            if not content_groups:
                logger.warning("No content groups found")
                return []

            time_per_group = total_duration / len(content_groups)
            current_time = 0.0

            for i, group in enumerate(content_groups):
                # ✅ FIX: Use 'id' not 'group_id', and 'element_ids' not 'elements'
                group_id = group.get('id')
                element_ids = group.get('element_ids', [])

                # Calculate effect duration for this group
                # Make effects continuous without gaps
                group_start = current_time
                group_end = min(current_time + time_per_group, total_duration)

                # For the last group, extend to end of audio
                if i == len(content_groups) - 1:
                    group_end = total_duration

                for elem_id in element_ids:
                    elem = elements_by_id.get(elem_id)
                    if not elem:
                        continue

                    bbox = elem.get('bbox')
                    if not bbox:
                        continue

                    cue = {
                        'action': 'highlight',
                        'bbox': bbox,
                        't0': round(group_start, 2),
                        't1': round(group_end, 2),
                        'group_id': group_id,
                        'element_id': elem_id,
                        'timing_source': 'simple_fallback'
                    }
                    cues.append(cue)

                current_time += time_per_group
            
            logger.info(f"Created {len(cues)} simple cues")
            return cues
        
        # Deduplicate segments by (group_id, t0, t1) to avoid duplicate cues
        seen_segments = set()
        unique_segments = []
        for segment in talk_track_raw:
            group_id = segment.get('group_id')
            t0 = segment.get('start', 0.0)
            t1 = segment.get('end', 0.0)

            if not group_id or t0 == t1:
                continue

            # Use tuple as key for deduplication
            seg_key = (group_id, t0, t1)
            if seg_key not in seen_segments:
                seen_segments.add(seg_key)
                unique_segments.append(segment)

        # Original fallback logic for talk_track with group_id
        for segment in unique_segments:
            group_id = segment.get('group_id')
            t0 = segment.get('start', 0.0)
            t1 = segment.get('end', 0.0)

            # Находим соответствующую группу в semantic map
            for group in groups:
                # ✅ FIX: Use 'id' not 'group_id'
                if group.get('id') == group_id:
                    group_type = group.get('type', 'text')
                    
                    action = 'highlight' if group_type == 'bullet_list' else 'underline'
                    
                    # ✅ FIX: Use 'element_ids' and lookup in elements list
                    element_ids = group.get('element_ids', [])
                    elements_by_id = {elem.get('id'): elem for elem in (elements or [])}

                    # ✅ IMPROVED: Distribute elements evenly across segment time
                    # Instead of showing all elements at once, stagger them
                    num_elements = len(element_ids)
                    segment_duration = t1 - t0

                    # Calculate timing for each element
                    if num_elements > 1:
                        # Distribute elements across the segment
                        time_per_element = segment_duration / num_elements
                        min_duration = 0.5  # Minimum 0.5s per element

                        # If elements are too fast, overlap them
                        if time_per_element < min_duration:
                            time_per_element = min_duration
                    else:
                        time_per_element = segment_duration

                    for i, elem_id in enumerate(element_ids):
                        elem = elements_by_id.get(elem_id)
                        if not elem:
                            continue

                        bbox = elem.get('bbox')
                        if bbox:
                            # Calculate staggered timing for this element
                            elem_t0 = t0 + (i * time_per_element)
                            elem_t1 = min(elem_t0 + time_per_element * 1.2, t1)  # 20% overlap

                            # Ensure we don't exceed segment bounds
                            elem_t0 = max(t0, min(elem_t0, t1 - 0.3))
                            elem_t1 = max(elem_t0 + 0.3, min(elem_t1, t1))

                            # Use original text for display (slide shows original, not translated)
                            original_text = elem.get('text_original') or elem.get('text', '')
                            cues.append({
                                'action': action,
                                'bbox': bbox,
                                't0': round(elem_t0, 2),
                                't1': round(elem_t1, 2),
                                'group_id': group_id,
                                'element_id': elem_id,
                                'text': original_text,
                                'timing_source': 'sentence_distributed'
                            })
        
        return cues
