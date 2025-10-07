"""
SSML Generator - создание SSML разметки для TTS с word-level timing
"""
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SSMLGenerator:
    """Генератор SSML разметки для получения word-level timings от Google TTS"""
    
    def __init__(self, word_marking_strategy: str = "smart"):
        """
        Args:
            word_marking_strategy: Стратегия расстановки марок
                - "all": Все слова
                - "smart": Только значимые слова (умолчание)
                - "minimal": Только ключевые слова
        """
        self.mark_counter = 0
        self.word_marking_strategy = word_marking_strategy
        
        # Слова, которые не нужно маркировать в smart режиме
        self.skip_words = {
            # Русские
            'и', 'в', 'на', 'с', 'по', 'из', 'к', 'о', 'у', 'за', 'до', 'от', 'при',
            'это', 'то', 'а', 'но', 'как', 'же', 'ли', 'бы', 'не', 'ни', 'да', 'нет',
            # Английские
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            # Немецкие
            'der', 'die', 'das', 'des', 'dem', 'den', 'ein', 'eine', 'einem', 'einen',
            'und', 'oder', 'aber', 'in', 'an', 'auf', 'für', 'von', 'zu', 'mit', 'bei',
        }
    
    def generate_ssml_from_talk_track(self, talk_track: List[Dict[str, Any]], combine: bool = True) -> List[str]:
        """
        Создаёт SSML из talk_track segments
        
        Args:
            talk_track: List of segments with 'text' and optional 'group_id' fields
            combine: If True, combines all segments into one SSML (default). If False, returns separate SSML per segment.
            
        Returns:
            List of SSML strings
        """
        if combine:
            # Combine all segments into one SSML for better synthesis
            all_parts = []
            for segment in talk_track:
                text = segment.get('text', '')
                segment_type = segment.get('segment', 'text')
                group_id = segment.get('group_id')  # ✅ Get group_id for sync
                
                if not text.strip():
                    continue
                
                # ✅ Add group marker at the start of segment if group_id exists
                if group_id:
                    # Normalize marker name - don't double "group_" prefix
                    marker_name = group_id if group_id.startswith('group_') else f'group_{group_id}'
                    # ✅ IMPROVED: Better pause timing for natural speech
                    if len(all_parts) > 0:  # Add pause only between segments
                        pause_time = '500ms' if segment.get('segment') == 'hook' else '300ms'
                        all_parts.append(f'<break time="{pause_time}"/>')
                    all_parts.append(f'<mark name="{marker_name}"/>')
                    # Small pause after marker
                    all_parts.append('<break time="150ms"/>')
                    logger.debug(f"Added group marker: {marker_name}")
                
                # Create SSML part with prosody but without full <speak> wrapper
                prosody = self._get_prosody_for_segment(segment_type)
                words = self._tokenize_words(text)
                marked_words = []
                for word in words:
                    # Check if this is an SSML tag (like <sub>...</sub>)
                    if word.startswith('<') and word.endswith('>'):
                        # Keep SSML tags as-is without adding marks
                        marked_words.append(word)
                    elif self._should_mark_word(word):
                        # Regular word - add mark
                        mark_id = f"w{self.mark_counter}"
                        self.mark_counter += 1
                        marked_words.append(f'<mark name="{mark_id}"/>{word}')
                    else:
                        # Short words or punctuation - no mark
                        marked_words.append(word)
                
                marked_text = ' '.join(marked_words)
                part = f"{prosody['start']}{marked_text}{prosody['end']}"
                all_parts.append(part)
            
            # Wrap all parts in one SSML
            combined_ssml = f'<speak>{" ".join(all_parts)}</speak>'
            
            # ✅ IMPROVED: Better SSML size and marker management
            ssml_length = len(combined_ssml)
            mark_count = combined_ssml.count('<mark name=')
            
            # Reduce markers if too many
            MAX_SSML_SIZE = 4000  # Leave safety buffer
            MAX_MARKERS = 150  # Conservative limit for reliability
            GOOGLE_TTS_LIMIT = 5000  # Hard limit from Google TTS
            
            if ssml_length > MAX_SSML_SIZE or mark_count > MAX_MARKERS:
                logger.warning(
                    f"⚠️ SSML optimization needed: {ssml_length} chars, {mark_count} markers"
                )
                # Rebuild with fewer word markers (keep group markers)
                combined_ssml = self._optimize_ssml_markers(all_parts, MAX_MARKERS)
                ssml_length = len(combined_ssml)
                mark_count = combined_ssml.count('<mark name=')
                logger.info(f"✅ Optimized SSML: {ssml_length} chars, {mark_count} markers")
                
                # ✅ CRITICAL: Check if still too long after optimization
                if ssml_length > GOOGLE_TTS_LIMIT:
                    logger.error(f"❌ SSML still too long after optimization: {ssml_length} > {GOOGLE_TTS_LIMIT}")
                    logger.info(f"🔪 Splitting into multiple parts...")
                    # Split into multiple SSML parts
                    return self._split_ssml_into_parts(all_parts, GOOGLE_TTS_LIMIT)
            
            logger.info(f"✅ Generated SSML: {ssml_length} chars, {self.mark_counter} word marks")
            return [combined_ssml]
        else:
            # Original behavior - separate SSML per segment
            ssml_texts = []
            for segment in talk_track:
                text = segment.get('text', '')
                segment_type = segment.get('segment', 'text')
                group_id = segment.get('group_id')  # ✅ Get group_id
                
                if not text.strip():
                    continue
                
                # Create SSML with word marks and group marker
                ssml = self._create_ssml_with_marks(text, segment_type, group_id)
                ssml_texts.append(ssml)
            
            return ssml_texts
    
    def _create_ssml_with_marks(self, text: str, segment_type: str = 'text', group_id: str = None) -> str:
        """
        Создаёт SSML с <mark> тегами для каждого слова
        
        Args:
            text: Текст для преобразования
            segment_type: Тип сегмента (hook, context, explanation, etc)
            group_id: ID группы для синхронизации (опционально)
            
        Returns:
            SSML string
        """
        # ✅ Add group marker if provided
        if group_id:
            # Normalize marker name - don't double "group_" prefix
            marker_name = group_id if group_id.startswith('group_') else f'group_{group_id}'
            group_mark = f'<mark name="{marker_name}"/>\n'
        else:
            group_mark = ''
        
        # Split text into words
        words = self._tokenize_words(text)
        
        # Add marks before each significant word
        marked_words = []
        for word in words:
            # Skip very short words (articles, etc)
            if len(word.strip()) > 2 and not self._is_punctuation_only(word):
                mark_name = f"mark_{self.mark_counter}"
                self.mark_counter += 1
                marked_words.append(f'<mark name="{mark_name}"/>{word}')
            else:
                marked_words.append(word)
        
        # Join words back
        marked_text = ' '.join(marked_words)
        
        # Apply prosody based on segment type
        prosody = self._get_prosody_for_segment(segment_type)
        
        # Create SSML
        ssml = f'''<speak>
{group_mark}{prosody['start']}
{marked_text}
{prosody['end']}
</speak>'''
        
        return ssml
    
    def _process_foreign_terms(self, text: str) -> str:
        """
        Преобразует маркеры в SSML теги для управления речью:
        
        FOREIGN TERMS & VISUAL:
        - [visual:XX]term[/visual] → пауза (не озвучивается, только для visual effects)
        - [lang:XX]term[/lang] → <lang xml:lang="XX">term</lang>
        - [phoneme:ipa:трнскр]term[/phoneme] → <phoneme alphabet="ipa" ph="трнскр">term</phoneme>
        
        PROSODY & INTONATION:
        - [pause:XXXms] → <break time="XXXms"/>
        - [emphasis:level]text[/emphasis] → <emphasis level="level">text</emphasis>
        - [pitch:+/-X%]text[/pitch] → <prosody pitch="+/-X%">text</prosody>
        - [rate:X%]text[/rate] → <prosody rate="X%">text</prosody>
        
        Args:
            text: Текст с маркерами
            
        Returns:
            Текст с SSML тегами
        """
        # 1. Process [pause:XXXms] - standalone pauses
        pause_pattern = r'\[pause:(\d+)ms\]'
        text = re.sub(pause_pattern, r'<break time="\1ms"/>', text)
        
        # 2. Process [emphasis:level]text[/emphasis] - strong/moderate/reduced
        emphasis_pattern = r'\[emphasis:(strong|moderate|reduced)\](.*?)\[/emphasis\]'
        text = re.sub(emphasis_pattern, r'<emphasis level="\1">\2</emphasis>', text)
        
        # 3. Process [pitch:+/-X%]text[/pitch] - change pitch
        pitch_pattern = r'\[pitch:([\+\-]\d+%)\](.*?)\[/pitch\]'
        text = re.sub(pitch_pattern, r'<prosody pitch="\1">\2</prosody>', text)
        
        # 4. Process [rate:X%]text[/rate] - change speed
        rate_pattern = r'\[rate:(\d+%)\](.*?)\[/rate\]'
        text = re.sub(rate_pattern, r'<prosody rate="\1">\2</prosody>', text)
        
        # 5. Process [visual:XX]...[/visual] markers
        # These are NOT spoken by TTS, only used for visual effects
        # ✅ IMPROVED: Longer pause for visual-only content
        visual_pattern = r'\[visual:[a-z]{2}\](.*?)\[/visual\]'
        text = re.sub(visual_pattern, '<break time="400ms"/>', text)
        
        # 6. Process phoneme markers (they have priority over lang)
        # Pattern: [phoneme:ipa:транскрипция]term[/phoneme]
        phoneme_pattern = r'\[phoneme:ipa:(.*?)\](.*?)\[/phoneme\]'
        
        def replace_phoneme(match):
            ipa_transcription = match.group(1).strip()
            term = match.group(2).strip()
            return f'<phoneme alphabet="ipa" ph="{ipa_transcription}">{term}</phoneme>'
        
        text = re.sub(phoneme_pattern, replace_phoneme, text)
        
        # Process language markers
        # Pattern: [lang:XX]term[/lang]
        lang_pattern = r'\[lang:([a-z]{2})\](.*?)\[/lang\]'
        
        # Language code mapping (convert 2-letter to xml:lang format)
        lang_map = {
            'de': 'de-DE',
            'en': 'en-US',
            'fr': 'fr-FR',
            'es': 'es-ES',
            'it': 'it-IT',
            'pt': 'pt-PT',
            'nl': 'nl-NL',
            'pl': 'pl-PL',
            'ru': 'ru-RU',
            'ja': 'ja-JP',
            'zh': 'zh-CN',
            'ko': 'ko-KR',
            'la': 'la',  # Latin
        }
        
        def replace_lang(match):
            lang_code = match.group(1).strip()
            term = match.group(2).strip()
            xml_lang = lang_map.get(lang_code, f'{lang_code}-{lang_code.upper()}')
            return f'<lang xml:lang="{xml_lang}">{term}</lang>'
        
        text = re.sub(lang_pattern, replace_lang, text)
        
        # ✅ FINAL STEP: Remove parentheses with original foreign terms (non-spoken)
        # NOW all [lang:XX] markers are converted to <lang> tags, so we can safely remove parentheses
        # Pattern matches: (Epidermis), (<lang>Epidermis</lang>), (anything starting with capital/tag)
        # Examples that will be removed:
        # - "эпидермис (Epidermis)" → "эпидермис "
        # - "мезофилл (<lang>Mesophyll</lang>)" → "мезофилл "
        # - "палисадная паренхима (Palisadenparenchym)" → "палисадная паренхима "
        parentheses_pattern = r'\s*\([^)]+\)\s*'
        text = re.sub(parentheses_pattern, ' ', text)
        
        return text
    
    def _tokenize_words(self, text: str) -> List[str]:
        """
        Разбивает текст на слова, сохраняя пунктуацию и SSML теги
        
        Args:
            text: Исходный текст (может содержать SSML теги)
            
        Returns:
            List of words/tokens (including intact SSML tags)
        """
        # First process foreign term markers to <sub> tags
        text = self._process_foreign_terms(text)
        
        # Split by whitespace but keep SSML tags as single tokens
        import re
        
        # Find all SSML tags and mark their positions
        ssml_tags = []
        # Match SSML tags: <lang>, <sub>, <phoneme>, <emphasis>, <prosody>, <break>
        # Closing tags
        for match in re.finditer(r'<(?:lang|sub|phoneme|emphasis|prosody)[^>]*>.*?</(?:lang|sub|phoneme|emphasis|prosody)>', text):
            ssml_tags.append((match.start(), match.end(), match.group()))
        # Self-closing tags like <break/>
        for match in re.finditer(r'<break[^>]*/?>', text):
            ssml_tags.append((match.start(), match.end(), match.group()))
        
        # If no SSML tags, just split normally
        if not ssml_tags:
            return text.split()
        
        # Sort tags by position
        ssml_tags.sort(key=lambda x: x[0])
        
        # Build tokens list preserving SSML tags
        tokens = []
        last_pos = 0
        
        for start, end, tag_content in ssml_tags:
            # Add words before this tag
            before = text[last_pos:start].strip()
            if before:
                tokens.extend(before.split())
            # Add the complete tag as one token
            tokens.append(tag_content)
            last_pos = end
        
        # Add remaining text after last tag
        after = text[last_pos:].strip()
        if after:
            tokens.extend(after.split())
        
        return tokens
    
    def _is_punctuation_only(self, word: str) -> bool:
        """Проверяет, состоит ли слово только из пунктуации"""
        return all(not c.isalnum() for c in word)
    
    def _should_mark_word(self, word: str) -> bool:
        """
        Определяет, нужно ли добавлять маркер к этому слову
        
        Args:
            word: Слово для проверки
            
        Returns:
            True если нужно добавить маркер
        """
        # Очищаем от пунктуации
        clean_word = word.strip('.,!?;:"\'-()[]{}').lower()
        
        # Проверяем длину
        if len(clean_word) < 2:
            return False
        
        # Проверяем, является ли словом (не только пунктуация/цифры)
        if not any(c.isalpha() for c in clean_word):
            return False
        
        # Применяем стратегию
        if self.word_marking_strategy == "all":
            return True
        elif self.word_marking_strategy == "minimal":
            # Только длинные и важные слова
            return len(clean_word) > 5
        else:  # smart (по умолчанию)
            # Пропускаем служебные слова
            return clean_word not in self.skip_words
    
    def _is_important_word(self, word: str) -> bool:
        """
        Определяет, является ли слово важным (существительное, глагол, прилагательное)
        Используется для minimal стратегии
        """
        clean_word = word.strip('.,!?;:"\'-()[]{}').lower()
        
        # Простая эвристика: длинные слова обычно важнее
        if len(clean_word) > 6:
            return True
        
        # Слова с заглавной буквы (имена, названия)
        if word and word[0].isupper():
            return True
        
        # Технические термины и специфичные слова
        # (содержат числа, дефисы, специальные символы)
        if any(c.isdigit() for c in word) or '-' in word or '_' in word:
            return True
        
        return False
    
    def _get_prosody_for_segment(self, segment_type: str) -> Dict[str, str]:
        """
        Возвращает SSML prosody теги для разных типов сегментов
        
        Args:
            segment_type: Тип сегмента (hook, context, explanation, etc)
            
        Returns:
            Dict with 'start' and 'end' prosody tags
        """
        # ✅ IMPROVED: More natural prosody variations WITHOUT pitch changes
        # NOTE: pitch changes can be perceived as volume changes, so we only use rate and emphasis
        prosody_map = {
            'hook': {
                # ✅ FIXED: Only rate change, no pitch (pitch caused volume perception issues)
                'start': '<prosody rate="95%">',
                'end': '</prosody>'
            },
            'context': {
                # Normal speed and pitch
                'start': '',
                'end': ''
            },
            'explanation': {
                # Slightly slower for clarity
                'start': '<prosody rate="95%">',
                'end': '</prosody>'
            },
            'example': {
                # ✅ FIXED: Slightly faster but no pitch change
                'start': '<prosody rate="103%">',
                'end': '</prosody>'
            },
            'emphasis': {
                # ✅ FIXED: More natural emphasis (was too aggressive)
                'start': '<emphasis level="moderate">',
                'end': '</emphasis>'
            },
            'transition': {
                # Normal with pause before
                'start': '<break time="300ms"/>',
                'end': ''
            },
            'key_concept': {
                # ✅ IMPROVED: Moderate emphasis without extreme slowdown
                'start': '<prosody rate="95%"><emphasis level="moderate">',
                'end': '</emphasis></prosody>'
            },
            'summary': {
                # ✅ FIXED: Only rate change, no pitch
                'start': '<prosody rate="92%">',
                'end': '</prosody>'
            }
        }
        
        # Default: normal prosody (no changes)
        return prosody_map.get(segment_type, {
            'start': '',
            'end': ''
        })
    
    def _split_ssml_into_parts(self, parts: List[str], max_size: int) -> List[str]:
        """
        Split SSML into multiple parts if too long
        
        Args:
            parts: List of SSML parts (segments)
            max_size: Maximum size per SSML string (default 5000)
            
        Returns:
            List of SSML strings, each under max_size
        """
        # Target size with safety buffer
        target_size = int(max_size * 0.85)  # 4250 for 5000 limit
        
        result_parts = []
        current_parts = []
        current_size = len('<speak></speak>')
        
        for part in parts:
            part_size = len(part) + 1  # +1 for space
            
            # If single part is too large, we need to truncate it
            if part_size > target_size:
                logger.warning(f"⚠️ Single part too large ({part_size} chars), truncating...")
                # Keep group markers, remove some text
                if '<mark name="group_' in part:
                    # Extract group marker
                    import re
                    match = re.search(r'<mark name="(group_[^"]+)"/>', part)
                    if match:
                        group_marker = match.group(0)
                        # Keep first N chars after marker
                        truncated = part[:target_size - len(group_marker) - 50]
                        part = group_marker + ' ' + truncated + '...'
                        part_size = len(part)
                else:
                    part = part[:target_size - 50] + '...'
                    part_size = len(part)
            
            # Check if adding this part would exceed limit
            if current_size + part_size > target_size and current_parts:
                # Save current batch
                ssml = f'<speak>{" ".join(current_parts)}</speak>'
                result_parts.append(ssml)
                logger.info(f"  Created SSML part {len(result_parts)}: {len(ssml)} chars")
                
                # Start new batch
                current_parts = [part]
                current_size = len('<speak></speak>') + part_size
            else:
                # Add to current batch
                current_parts.append(part)
                current_size += part_size
        
        # Add remaining parts
        if current_parts:
            ssml = f'<speak>{" ".join(current_parts)}</speak>'
            result_parts.append(ssml)
            logger.info(f"  Created SSML part {len(result_parts)}: {len(ssml)} chars")
        
        logger.info(f"✅ Split SSML into {len(result_parts)} parts")
        return result_parts
    
    def _optimize_ssml_markers(self, parts: List[str], max_markers: int) -> str:
        """
        Optimize SSML by reducing word markers while keeping group markers
        
        Args:
            parts: List of SSML parts
            max_markers: Maximum allowed markers
            
        Returns:
            Optimized SSML string
        """
        # Rebuild parts with fewer word markers
        optimized_parts = []
        word_mark_counter = 0
        
        for part in parts:
            # Keep all group markers and breaks
            if '<mark name="group_' in part or '<break' in part:
                optimized_parts.append(part)
            else:
                # For text parts, reduce word markers
                # Remove every other word marker to reduce count
                import re
                def replace_word_mark(match):
                    nonlocal word_mark_counter
                    word_mark_counter += 1
                    # Keep every 3rd word marker only
                    if word_mark_counter % 3 == 0:
                        return match.group(0)
                    else:
                        # Remove the marker, keep the word
                        return match.group(1) if match.lastindex else ''
                
                # Pattern to match word markers: <mark name="wXXX"/>word
                pattern = r'<mark name="w\d+"/>(\w+)'
                optimized_part = re.sub(pattern, replace_word_mark, part)
                optimized_parts.append(optimized_part)
        
        return f'<speak>{" ".join(optimized_parts)}</speak>'
    
    def generate_simple_ssml(self, text: str) -> str:
        """
        Создаёт простой SSML с марками для текста (для fallback)
        
        Args:
            text: Текст для преобразования
            
        Returns:
            SSML string
        """
        return self._create_ssml_with_marks(text, 'text')


# Utility function for easy access
def generate_ssml_from_talk_track(talk_track: List[Dict[str, Any]]) -> List[str]:
    """Generate SSML from talk_track"""
    generator = SSMLGenerator()
    return generator.generate_ssml_from_talk_track(talk_track)


def generate_simple_ssml(text: str) -> str:
    """Generate simple SSML with marks"""
    generator = SSMLGenerator()
    return generator.generate_simple_ssml(text)
