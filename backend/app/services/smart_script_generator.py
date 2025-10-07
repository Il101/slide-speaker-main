"""
Stage 3: Smart Script Generator
Context-aware генерация скриптов с anti-reading логикой + AI Personas + Content Intelligence
"""
import logging
from typing import List, Dict, Any, Optional
import os
import json

logger = logging.getLogger(__name__)

class SmartScriptGenerator:
    """Умная генерация скриптов с учётом контекста, semantic map, personas и типов контента"""
    
    def __init__(self):
        # Use configured LLM provider (Gemini/OpenRouter/etc)
        from app.services.provider_factory import ProviderFactory
        from app.services.ai_personas import AIPersonas, PersonaType
        from app.services.content_intelligence import ContentIntelligence
        
        try:
            self.llm_worker = ProviderFactory.get_llm_provider()
            self.use_mock = False
            logger.info(f"✅ SmartScriptGenerator: Using {os.getenv('LLM_PROVIDER', 'unknown')} provider")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM provider: {e}, using mock mode")
            self.llm_worker = None
            self.use_mock = True
        
        self.anti_reading_threshold = 0.35
        self.personas = AIPersonas
        self.content_intelligence = ContentIntelligence()
        
        # Получаем персону из настроек или автоматически
        self.default_persona = os.getenv('AI_PERSONA', 'tutor')
        logger.info(f"✅ Using AI Persona: {self.default_persona}")
    
    def _auto_wrap_foreign_terms(self, text: str) -> str:
        """
        Automatically detect and wrap foreign (Latin) terms in Cyrillic text with [lang:XX] markers.
        This ensures proper pronunciation AND visual sync even if LLM doesn't follow instructions.
        
        Args:
            text: Russian text that may contain unwrapped foreign terms
            
        Returns:
            Text with foreign terms wrapped in [lang:XX] markers for pronunciation
        """
        import re
        
        # Pattern: Latin word(s) possibly with hyphens, not already wrapped
        # Must be surrounded by Cyrillic/spaces/punctuation
        # Captures: word or phrase like "Blatt", "Anatomische Blatt-Typen", "DNA", etc.
        # Negative lookbehind: not after [ or Latin letter
        # Negative lookahead: not before ] or Latin letter
        latin_pattern = r'(?<![a-zA-Z\[])\b([A-Z][a-z]{1,}(?:[-\s][A-Z][a-z]{1,})*)\b(?![a-zA-Z\]])'
        
        def determine_language(term: str) -> str:
            """Simple heuristic to guess language"""
            term_lower = term.lower()
            # German indicators
            if any(word in term_lower for word in ['blatt', 'pflanzen', 'arten', 'typen', 'metamorphosen']):
                return 'de'
            # Latin indicators (binomial nomenclature)
            if ' ' in term and term[0].isupper() and len(term.split()) == 2:
                return 'la'
            # Default to German for this scientific context
            return 'de'
        
        def wrap_term(match):
            term = match.group(1)
            match_pos = match.start()
            
            # Check if this term is already inside a marker
            # Find all marker regions [xxx:yy]...[/xxx]
            marker_regions = []
            for marker_match in re.finditer(r'\[(visual|lang|phoneme):[^\]]+\].*?\[/\1\]', text):
                marker_regions.append((marker_match.start(), marker_match.end()))
            
            # Check if current match is inside any marker region
            for region_start, region_end in marker_regions:
                if region_start <= match_pos < region_end:
                    return term  # Already wrapped, skip
            
            # Skip very short terms (likely abbreviations)
            if len(term) < 3:
                return term
            # Skip common English abbreviations
            if term.upper() in ['DNA', 'RNA', 'ATP', 'PCR', 'HIV', 'AIDS']:
                return term
            
            lang = determine_language(term)
            # Wrap with [lang:] for proper pronunciation AND visual sync
            return f'[lang:{lang}]{term}[/lang]'
        
        result = re.sub(latin_pattern, wrap_term, text)
        
        # Log if we wrapped anything
        if result != text:
            wrapped_count = result.count('[lang:') - text.count('[lang:')
            if wrapped_count > 0:
                logger.info(f"🔧 Auto-wrapped {wrapped_count} foreign term(s) that LLM didn't mark")
        
        return result
    
    async def generate_script(
        self,
        semantic_map: Dict[str, Any],
        ocr_elements: List[Dict[str, Any]],
        presentation_context: Dict[str, Any],
        previous_slides_summary: str = "",
        slide_index: int = 0,
        persona_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Генерирует скрипт лекции на основе semantic map с учётом personas и типа контента
        
        Args:
            semantic_map: Semantic map из SemanticAnalyzer
            ocr_elements: OCR элементы (для anti-reading check)
            presentation_context: Контекст презентации
            previous_slides_summary: Краткое содержание предыдущих слайдов
            slide_index: Индекс текущего слайда
            persona_override: Переопределить персону для этого слайда
            
        Returns:
            Script с talk_track, speaker_notes, и SSML
        """
        try:
            logger.info(f"Generating script for slide {slide_index + 1}")
            
            if self.use_mock:
                return self._generate_script_mock(semantic_map, ocr_elements, presentation_context)
            
            # ✅ Детектируем тип контента
            content_type, content_strategy = self.content_intelligence.detect_content_type(ocr_elements)
            complexity = self.content_intelligence.analyze_complexity(ocr_elements, content_type)
            logger.info(f"📊 Content type: {content_type.value}, complexity: {complexity:.2f}")
            
            # ✅ Выбираем персону
            persona_type = persona_override or self.default_persona
            if not persona_override:
                # Автоматический выбор персоны на основе презентации
                from app.services.ai_personas import PersonaType
                persona_enum = self.personas.select_persona_for_presentation(presentation_context)
                persona_type = persona_enum.value
            
            persona_config = self.personas.get_persona(persona_type)
            logger.info(f"🎭 Using persona: {persona_config['name']}")
            
            # Prepare slide text for anti-reading check
            slide_text = self._extract_slide_text(ocr_elements)
            
            # ✅ Create prompt с учётом персоны и типа контента
            prompt = self._create_script_generation_prompt(
                semantic_map,
                ocr_elements,
                presentation_context,
                previous_slides_summary,
                slide_index,
                persona_config,
                content_strategy
            )
            
            # Generate with Gemini
            max_attempts = 3
            for attempt in range(max_attempts):
                # Get language from environment or presentation context
                target_language = os.getenv('LLM_LANGUAGE', 'ru')
                
                language_instructions = {
                    'ru': 'ВАЖНО: Весь текст должен быть ТОЛЬКО на русском языке!',
                    'en': 'IMPORTANT: All text must be in English only!',
                    'de': 'WICHTIG: Der gesamte Text muss auf Deutsch sein!'
                }
                
                lang_instruction = language_instructions.get(target_language, language_instructions['ru'])
                
                system_prompt = f"""You are an expert lecturer who creates engaging explanations without simply reading slides.

{lang_instruction}

🚨 CRITICAL RULE - ALWAYS FOLLOW (NO EXCEPTIONS):
When you encounter ANY foreign language word or phrase (German, Latin, English, French, etc.) in your narration:
1. You MUST wrap it with ONE of these markers:
   - [visual:XX]term[/visual] - if term is on slide but NOT spoken (pause instead)
   - [lang:XX]term[/lang] - if term SHOULD be pronounced in its native language
2. Language codes: de=German, en=English, fr=French, es=Spanish, it=Italian, la=Latin
3. This is MANDATORY for EVERY foreign word - check your output before returning!

Examples you MUST follow:
❌ WRONG: "Рассмотрим Das Blatt"
✅ CORRECT: "Рассмотрим [visual:de]Das Blatt[/visual]" or "Рассмотрим [lang:de]Das Blatt[/lang]"

❌ WRONG: "Термин photosynthesis важен"  
✅ CORRECT: "Термин [lang:en]photosynthesis[/lang] важен"

DO NOT write foreign words without markers! This breaks the system.

📍 RUSSIAN STRESS MARKS (for correct pronunciation):
For ambiguous Russian words where stress affects meaning, add stress mark ́ (U+0301) after the stressed vowel:
- за́мок (castle) vs замо́к (lock)
- о́рган (organ-body) vs орга́н (organ-music)
- му́ка (flour) vs мука́ (torture)
- до́ма (houses) vs дома́ (at home)
- пла́чу (I cry) vs плачу́ (I pay)

How to use:
1. Type the vowel, then immediately type the combining acute accent: а́ е́ и́ о́ у́ ы́ э́ ю́ я́
2. Only use for words where wrong stress would confuse listeners
3. Common words don't need stress marks - TTS handles them correctly

Example: "В этом за́мке был установлен надёжный замо́к"
(In this castle was installed a reliable lock)"""
                
                # Generate using LLM worker
                result_text = self.llm_worker.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.3,
                    max_tokens=2000
                )
                
                # Parse JSON
                try:
                    if "```json" in result_text:
                        result_text = result_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in result_text:
                        result_text = result_text.split("```")[1].split("```")[0].strip()
                    
                    script = json.loads(result_text)
                    
                    # Auto-wrap foreign terms (Latin text in Russian speech)
                    if 'talk_track' in script:
                        for segment in script['talk_track']:
                            if 'text' in segment:
                                segment['text'] = self._auto_wrap_foreign_terms(segment['text'])
                                
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse script JSON: {e}")
                    if attempt == max_attempts - 1:
                        return self._generate_script_mock(semantic_map, ocr_elements, presentation_context)
                    continue
                
                # Check anti-reading
                generated_text = " ".join([item.get('text', '') for item in script.get('talk_track', [])])
                overlap = self._calculate_overlap(generated_text, slide_text)
                
                if overlap < self.anti_reading_threshold:
                    logger.info(f"✅ Script passed anti-reading check (overlap: {overlap:.3f})")
                    script['overlap_score'] = overlap
                    
                    # ✅ Добавляем метаданные о персоне и типе контента
                    script['persona_used'] = persona_config['name']
                    script['content_type'] = content_type.value
                    script['complexity'] = complexity
                    
                    # ✅ Рассчитываем оптимальную длительность
                    word_count = len(generated_text.split())
                    from app.services.ai_personas import PersonaType
                    persona_enum = PersonaType(persona_type)
                    optimal_duration = self.personas.calculate_optimal_duration(
                        word_count, persona_enum, complexity
                    )
                    script['recommended_duration'] = optimal_duration
                    logger.info(
                        f"📊 Recommended duration: {optimal_duration:.1f}s "
                        f"(words: {word_count}, complexity: {complexity:.2f})"
                    )
                    
                    return script
                else:
                    logger.warning(f"Script failed anti-reading check (overlap: {overlap:.3f}), attempt {attempt + 1}/{max_attempts}")
                    # Add stronger anti-reading instructions for next attempt
                    prompt += "\n\nIMPORTANT: You are READING the slide directly. EXPLAIN the concepts in your own words with examples and analogies. DO NOT quote the slide text."
            
            # If all attempts failed, return last attempt
            logger.warning("All anti-reading attempts failed, using last generated script")
            script['overlap_score'] = overlap
            return script
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return self._generate_script_mock(semantic_map, ocr_elements, presentation_context)
    
    def _create_script_generation_prompt(
        self,
        semantic_map: Dict[str, Any],
        ocr_elements: List[Dict[str, Any]],
        presentation_context: Dict[str, Any],
        previous_summary: str,
        slide_index: int,
        persona_config: Optional[Dict[str, Any]] = None,
        content_strategy: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create prompt for script generation with persona and content intelligence"""
        
        # Extract key information from semantic map
        groups_summary = []
        groups = semantic_map.get('groups', [])
        
        # Build elements lookup by ID
        elements_by_id = {elem.get('id'): elem for elem in ocr_elements}
        
        for group in groups[:8]:  # Top 8 groups
            if group.get('priority') != 'none':
                group_id = group.get('id', 'unknown')
                group_type = group.get('type', 'content')
                intent = group.get('educational_intent', 'N/A')
                
                # ✅ ADDED: Get text from elements in this group
                element_ids = group.get('element_ids', [])
                element_texts = []
                for elem_id in element_ids[:5]:  # Max 5 elements per group
                    if elem_id in elements_by_id:
                        text = elements_by_id[elem_id].get('text', '').strip()
                        if text:
                            element_texts.append(text)
                
                text_summary = ' | '.join(element_texts) if element_texts else 'No text'
                groups_summary.append(f"- ID: {group_id}, Type: {group_type}, Intent: {intent}\n  Text on slide: \"{text_summary}\"")
        
        groups_text = "\n".join(groups_summary) if groups_summary else "No groups available"
        
        # Get presentation context
        theme = presentation_context.get('theme', 'Unknown')
        level = presentation_context.get('level', 'undergraduate')
        # Always use target language from environment, not from presentation
        language = os.getenv('LLM_LANGUAGE', 'ru')
        style = presentation_context.get('presentation_style', 'academic')
        total_slides = presentation_context.get('total_slides', '?')
        
        # ✅ Добавляем инструкции из persona
        persona_instructions = ""
        if persona_config:
            persona_instructions = f"""
AI PERSONA: {persona_config['name']}
{persona_config.get('prompt_modifier', '')}

Use these style elements:
- Intro style: "{persona_config.get('intro_style', '')}"
- Transitions: "{persona_config.get('transition_style', '')}"
- Emphasis markers: {persona_config.get('emphasis_markers', [])}
"""
        
        # ✅ Добавляем инструкции по типу контента
        content_instructions = ""
        if content_strategy:
            content_type = content_strategy.get('content_type', 'text')
            content_instructions = f"""
CONTENT TYPE DETECTED: {content_type}
{content_strategy.get('prompt_additions', '')}

Recommended speaking pace: {content_strategy.get('pace', 'natural')}
Explanation style: {content_strategy.get('explanation_style', 'narrative')}
"""
        
        return f"""Generate an engaging lecture script for this slide.

PRESENTATION CONTEXT:
- Theme: {theme}
- Level: {level}
- Language: {language}
- Style: {style}
- Slide {slide_index + 1} of {total_slides}

{persona_instructions}

{content_instructions}

PREVIOUS SLIDES SUMMARY:
{previous_summary if previous_summary else "This is the first slide"}

CURRENT SLIDE SEMANTIC GROUPS:
{groups_text}

SLIDE TYPE: {semantic_map.get('slide_type', 'content_slide')}

CRITICAL RULES:
1. DO NOT read the slide text directly - EXPLAIN instead
2. MENTION specific terms/keywords from "Text on slide" when explaining each group
3. Add examples, analogies, and context around the slide terms
4. Use conversational tone - imagine explaining to a student
5. Reference previous slides when relevant
6. Keep it 30-60 seconds (130-160 words per minute)
7. **MANDATORY: Generate ALL text in "{language}" language**

EXPLANATION STRATEGY:
- When talking about a group, naturally MENTION its key terms from "Text on slide"
- Don't just read the text - explain WHY it matters, give examples, add context

FOREIGN TERMS MARKUP (3 OPTIONS):

**Option 1: [visual:XX]term[/visual] - Visual effects ONLY (NOT spoken)**
- Use when term should sync visuals but NOT be pronounced (pause instead)
- TTS makes 200ms pause instead of speaking the term
- Visual effects find and highlight the term on slide
- Term is HIDDEN in subtitles
- Example: "Сегодня изучаем [visual:de]Das Blatt[/visual] — строение листа"
  → TTS: "Сегодня изучаем [pause] строение листа"
  → Visual: highlights "Das Blatt" on slide
  → Subtitles: "Сегодня изучаем — строение листа"

**Option 2: [lang:XX]term[/lang] - Spoken with native pronunciation**
- Use when term SHOULD be pronounced in its native language
- TTS pronounces with correct accent
- Visual effects also sync to this term
- Term SHOWN in subtitles
- Language codes: de=German, en=English, fr=French, es=Spanish, it=Italian, la=Latin
- Example: "Сегодня изучаем [lang:de]Das Blatt[/lang] — лист растения"
  → TTS: "Сегодня изучаем [German accent] Das Blatt [Russian] — лист растения"
  → Visual: highlights "Das Blatt"
  → Subtitles: "Сегодня изучаем Das Blatt — лист растения"

**Option 3: [phoneme:ipa:...]term[/phoneme] - Precise IPA pronunciation**
- Use for complex scientific terms requiring exact phonetics
- TTS uses IPA transcription for pronunciation
- Example: "[phoneme:ipa:ˈkwɛrkʊs]Quercus[/phoneme]"
- If IPA unknown, fall back to [lang:XX]

CHOOSE WISELY:
- [visual:XX] → term on slide but narrator describes in Russian
- [lang:XX] → narrator says term in foreign language
- [phoneme:ipa:] → precise scientific pronunciation needed

🎯 CRITICAL FOR VISUAL SYNC - Original Terms in Parentheses:
When you mention a term that appears on the slide in a FOREIGN language, ALWAYS add the original term in parentheses (non-spoken):
- These parentheses help sync visual highlights to spoken content
- TTS will NOT read the parentheses (they are filtered out)
- Format: "Russian translation (Original Foreign Term)"

Examples:
✅ CORRECT: "Сначала мы видим эпидермис (Epidermis) верхней стороны листа"
✅ CORRECT: "Далее идёт мезофилл (Mesophyll), который отвечает за фотосинтез"
✅ CORRECT: "Здесь располагается палисадная паренхима (Palisadenparenchym)"
✅ CORRECT: "Губчатая паренхима (Schwammparenchym) находится ниже"

❌ WRONG: "Далее мы видим мезофилл" (missing original term from slide)
❌ WRONG: "Далее мы видим Mesophyll" (foreign term without translation)

WHY THIS IS CRITICAL:
- Slide elements have text in foreign language (e.g. "Epidermis der Blattoberseite")
- Visual effects need to find when you mention this element
- Your narration is in Russian, but element text is foreign
- Parentheses provide the bridge: "эпидермис (Epidermis)" links Russian speech to foreign slide text

WHEN TO ADD PARENTHESES:
✅ Technical terms that appear on slide (botanical names, chemical formulas, etc.)
✅ Foreign language labels, titles, headings from the slide
✅ Scientific nomenclature, species names, anatomical terms
❌ Common words already in Russian (город, дом, человек)
❌ Terms that don't appear visually on the slide

PROSODY & INTONATION MARKUP (makes speech more engaging):

**1. Pauses [pause:XXXms]** - add dramatic effect, emphasis, breathing room
- After key statements: "Это очень важно. [pause:500ms] Запомните это!"
- Before reveals: "И результат... [pause:800ms] превзошёл все ожидания"
- Natural breathing: "Рассмотрим три аспекта. [pause:300ms] Первый..."
- Recommended: 300-800ms (avoid over 1000ms)

**2. Emphasis [emphasis:level]text[/emphasis]** - stress important words
- strong: KEY concepts, warnings, critical info
  "Это [emphasis:strong]крайне важно[/emphasis] для понимания"
- moderate: notable points, interesting facts
  "[emphasis:moderate]Обратите внимание[/emphasis] на детали"
- reduced: de-emphasize secondary info
  "[emphasis:reduced]как мы видели ранее[/emphasis]"

**3. Pitch [pitch:+/-X%]text[/pitch]** - change tone for effect
- Raise (+5% to +20%): excitement, questions, highlights
  "[pitch:+10%]Удивительно![/pitch]"
- Lower (-5% to -20%): seriousness, conclusions
  "[pitch:-10%]Это ключевой вывод[/pitch]"
- Use sparingly! Too much sounds unnatural

**4. Rate [rate:X%]text[/rate]** - change speaking speed
- Slow (80-90%): complex concepts, definitions
  "[rate:85%]Рассмотрим сложную формулу[/rate]"
- Fast (110-120%): lists, known facts, transitions
  "[rate:115%]как мы уже знаем[/rate]"
- Normal is 100%, avoid extremes (<70% or >130%)

**BEST PRACTICES FOR ENGAGING NARRATION:**
- Use pauses after questions or before important reveals
- Emphasize 2-3 KEY words per segment (not everything!)
- Add pitch variation to avoid monotone delivery
- Slow down for NEW concepts, speed up for KNOWN info
- Combine techniques: "[pause:400ms][emphasis:strong]Запомните:[/emphasis] [rate:90%]это основа всей теории[/rate]"

**DON'T OVERUSE!** Too many markers make speech robotic. Use naturally and sparingly.

RETURN JSON (with text in {language}):
{{
  "talk_track": [
    {{"segment": "hook", "text": "Engaging opening in {language}", "group_id": "group_id_from_semantic_map_or_null"}},
    {{"segment": "context", "text": "Context in {language}", "group_id": "group_id_when_talking_about_specific_group"}},
    {{"segment": "explanation", "text": "Explanation in {language}", "group_id": "group_id_of_explained_element"}},
    {{"segment": "example", "text": "Example in {language}", "group_id": null}},
    {{"segment": "emphasis", "text": "Key point in {language}", "group_id": "group_id_of_emphasized_element"}},
    {{"segment": "transition", "text": "Transition in {language}", "group_id": null}}
  ],
  "speaker_notes": "Notes in {language}",
  "estimated_duration": 45
}}

IMPORTANT ABOUT group_id (MANDATORY):
- **ALWAYS** include "group_id" field in EVERY talk_track segment
- When talking about a specific group, use its exact "id" from the semantic map above
- **REUSE the same group_id** for multiple consecutive segments if you're explaining/detailing the same concept
- Use null ONLY for general introductions that don't relate to any specific visual element
- This field enables precise visual synchronization between speech and highlights
- Available group IDs: {', '.join([g.get('id', 'unknown') for g in groups if g.get('priority') != 'none'])}

Examples with CORRECT group_id usage:
✅ CORRECT (reusing group_id for continued explanation):
{{
  "talk_track": [
    {{"segment": "hook", "text": "Let's explore the main concept", "group_id": "group_title"}},
    {{"segment": "explanation", "text": "The key formula shows...", "group_id": "group_formula"}},
    {{"segment": "example", "text": "For instance, if we apply it...", "group_id": "group_formula"}},
    {{"segment": "emphasis", "text": "This demonstrates the principle", "group_id": "group_formula"}}
  ]
}}

❌ WRONG (missing group_id field):
{{"segment": "hook", "text": "Let's explore..."}}  <!-- Field is missing! -->

❌ WRONG (null when talking about slide content):
{{"segment": "example", "text": "Monocots have parallel veins...", "group_id": null}}  <!-- Should reference the monocot group! -->

Respond ONLY with valid JSON."""
        
        return prompt
    
    def _extract_slide_text(self, elements: List[Dict[str, Any]]) -> str:
        """Extract all text from elements for anti-reading check"""
        texts = []
        for elem in elements:
            if elem.get('text'):
                texts.append(elem['text'].lower())
        return " ".join(texts)
    
    def _calculate_overlap(self, generated_text: str, slide_text: str) -> float:
        """Calculate Jaccard similarity for anti-reading check"""
        if not generated_text or not slide_text:
            return 0.0
        
        gen_words = set(generated_text.lower().split())
        slide_words = set(slide_text.lower().split())
        
        intersection = gen_words.intersection(slide_words)
        union = gen_words.union(slide_words)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _generate_script_mock(
        self,
        semantic_map: Dict[str, Any],
        ocr_elements: List[Dict[str, Any]],
        presentation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock script generation"""
        logger.info("Using mock script generation")
        
        # Extract some text from elements
        element_texts = [elem.get('text', '')[:100] for elem in ocr_elements[:3]]
        slide_text = " ".join(element_texts)
        
        # Get group IDs for synchronization
        groups = semantic_map.get('groups', [])
        group_ids = [g.get('id') for g in groups if g.get('priority') != 'none']
        
        # Always use target language from environment
        language = os.getenv('LLM_LANGUAGE', 'ru')
        
        if language == 'ru':
            talk_track = [
                {"segment": "hook", "text": "Давайте рассмотрим важный концепт.", "group_id": group_ids[0] if len(group_ids) > 0 else None},
                {"segment": "context", "text": "Это связано с тем, что мы обсуждали ранее.", "group_id": None},
                {"segment": "explanation", "text": f"Ключевая идея здесь в том, что {slide_text[:50]}...", "group_id": group_ids[1] if len(group_ids) > 1 else None},
                {"segment": "example", "text": "Представьте себе ситуацию, когда...", "group_id": None},
                {"segment": "emphasis", "text": "Важно запомнить основной принцип.", "group_id": group_ids[2] if len(group_ids) > 2 else None},
                {"segment": "transition", "text": "Теперь перейдём к следующему вопросу.", "group_id": None}
            ]
            speaker_notes = "Объяснение основных концептов слайда с примерами."
        else:
            talk_track = [
                {"segment": "hook", "text": "Let's explore an important concept.", "group_id": group_ids[0] if len(group_ids) > 0 else None},
                {"segment": "context", "text": "This relates to what we discussed earlier.", "group_id": None},
                {"segment": "explanation", "text": f"The key idea here is {slide_text[:50]}...", "group_id": group_ids[1] if len(group_ids) > 1 else None},
                {"segment": "example", "text": "Imagine a situation where...", "group_id": None},
                {"segment": "emphasis", "text": "Remember the main principle.", "group_id": group_ids[2] if len(group_ids) > 2 else None},
                {"segment": "transition", "text": "Now let's move to the next topic.", "group_id": None}
            ]
            speaker_notes = "Explanation of main slide concepts with examples."
        
        return {
            "talk_track": talk_track,
            "speaker_notes": speaker_notes,
            "estimated_duration": 35,
            "overlap_score": 0.15,
            "mock": True
        }
