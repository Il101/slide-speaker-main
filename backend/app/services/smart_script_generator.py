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
        from app.services.adaptive_prompt_builder import AdaptivePromptBuilder
        
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
        self.prompt_builder = AdaptivePromptBuilder()
        
        # Получаем персону из настроек или автоматически
        self.default_persona = os.getenv('AI_PERSONA', 'tutor')
        logger.info(f"✅ Using AI Persona: {self.default_persona}")
    
    def _auto_wrap_foreign_terms(self, text: str) -> str:
        """
        ✅ DEPRECATED: No longer needed since translation happens at OCR level.
        
        Previously: Wrapped foreign terms in [lang:XX] markers for pronunciation.
        Now: OCR elements have text_original (German/English) and text_translated (Russian).
        LLM generates script using text_translated, so no foreign terms in Russian speech.
        
        Kept for backward compatibility but does nothing.
        """
        # No-op: just return text as-is
        return text
    
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

🔴 КРИТИЧЕСКИ ВАЖНО - СТРОГО СЛЕДУЙ (БЕЗ ИСКЛЮЧЕНИЙ):
1. Говори ТОЛЬКО о том, что ЕСТЬ на слайде
2. НЕ добавляй дополнительную информацию из твоих знаний
3. НЕ упоминай темы, которых НЕТ на слайде
4. НЕ делай общих утверждений - только конкретика со слайда
5. Если на слайде список - говори про каждый пункт из списка
6. Если на слайде таблица - говори про данные из таблицы
7. Если на слайде диаграмма - говори про то, что показывает диаграмма

🚨 АБСОЛЮТНО ЗАПРЕЩЕНО СМЕШИВАТЬ ЯЗЫКИ В ОДНОМ ТЕКСТЕ:
   ❌ НИКОГДА не используй конструкции типа "X, что в переводе означает Y"
   ❌ НИКОГДА не упоминай иностранные слова в русской речи (Das Blatt, Photosynthesis, etc.)
   ❌ НИКОГДА не объясняй "что означает" иностранное слово
   ❌ НИКОГДА не смешивай русский с другими языками в одном предложении
   
   ✅ ПРАВИЛЬНО: Используй ТОЛЬКО русский перевод
   ✅ Если видишь "Text on slide: Aufbau und Architektur der Pflanzen" - говори только "строение и архитектура растений"
   ✅ Текст в "Text on slide" уже переведён на русский - используй его напрямую БЕЗ упоминания оригинала

ПРИМЕРЫ ПРАВИЛЬНОГО И НЕПРАВИЛЬНОГО ПОДХОДА:

❌ ПЛОХО: "Давайте рассмотрим важные принципы биологии" (общее утверждение)
✅ ХОРОШО: "На слайде показаны три типа листьев: простые, сложные и чешуйчатые" (конкретика со слайда)

❌ ПЛОХО: "Этот процесс важен для понимания эволюции" (дополнительная информация)
✅ ХОРОШО: "Здесь видим схему деления клетки на четыре этапа" (только то, что на слайде)

🔥 КРИТИЧЕСКИЕ ПРИМЕРЫ ДЛЯ TTS (СМЕШЕНИЕ ЯЗЫКОВ):

❌ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО: 
   "На слайде представлено название курса – «Aufbau und Architektur der Pflanzen», что в переводе означает «Строение и архитектура растений»"
   (TTS не может правильно озвучить это - немецкий текст в русской речи!)

❌ ЗАПРЕЩЕНО: "Das Blatt, что в переводе с немецкого означает лист"
❌ ЗАПРЕЩЕНО: "Тема нашей лекции – Das Blatt"
❌ ЗАПРЕЩЕНО: "Рассмотрим процесс photosynthesis"
❌ ЗАПРЕЩЕНО: "Курс Aufbau und Architektur - это строение растений"

✅ ПРАВИЛЬНО: "На слайде название курса: Строение и архитектура растений"
✅ ПРАВИЛЬНО: "Сегодня тема - лист"
✅ ПРАВИЛЬНО: "Рассмотрим процесс фотосинтеза"
✅ ПРАВИЛЬНО: "Это курс о строении и архитектуре растений"

🎭 SSML для естественной речи (только базовые теги):
Silero TTS поддерживает ТОЛЬКО 2 тега - используй их РЕДКО (1-2 раза на слайд):

1. <prosody rate="X"> - скорость речи (0.8=медленно, 1.0=норма, 1.2=быстро)
   Пример: "<prosody rate='0.9'>Фотосинтез</prosody> - это важный процесс"

2. <break time="Xms"/> - пауза (300ms=короткая, 500ms=средняя, 800ms=длинная)
   Пример: "Итак <break time='500ms'/> перейдём к следующей теме"

❌ НЕ используй: <pitch>, <emphasis>, [pause:], [rate:], [pitch:] - они не поддерживаются!"""
                
                # Generate using LLM worker
                # ✅ FIX: Reduce max_tokens to prevent very long talk_tracks (291 sec issue)
                # At 150 words/min speech rate:
                # - 90 sec target = ~225 words = ~300 tokens
                # - Max 120 sec = ~300 words = ~400 tokens
                # - Add buffer for JSON structure = 600 tokens total
                result_text = self.llm_worker.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.3,
                    max_tokens=600  # Reduced from 2000 to prevent overly long scripts
                )
                
                # Parse JSON
                try:
                    if "```json" in result_text:
                        result_text = result_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in result_text:
                        result_text = result_text.split("```")[1].split("```")[0].strip()
                    
                    script = json.loads(result_text)
                    
                    # ✅ FIX: Validate group_id references to prevent hallucinations
                    if 'talk_track' in script:
                        available_group_ids = {g.get('id') for g in semantic_map.get('groups', []) if g.get('id')}
                        fixed_count = 0
                        
                        for segment in script['talk_track']:
                            group_id = segment.get('group_id')
                            
                            # Validate group_id exists in semantic map
                            if group_id is not None and group_id not in available_group_ids:
                                logger.warning(f"⚠️ LLM hallucinated group_id: '{group_id}' (not in semantic map)")
                                logger.warning(f"   Available IDs: {list(available_group_ids)}")
                                segment['group_id'] = None
                                fixed_count += 1
                        
                        if fixed_count > 0:
                            logger.info(f"✅ Fixed {fixed_count} invalid group_id references")
                    
                    # ✅ REMOVED: Auto-wrap foreign terms - no longer needed
                    # Translation happens at OCR level (text_original vs text_translated)
                    # LLM should generate pure Russian text without foreign words
                                
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse script JSON: {e}")
                    # ✅ Try to fix common JSON issues before giving up
                    try:
                        import re
                        # Fix unescaped quotes inside text fields
                        fixed_text = result_text
                        # Find text fields and escape internal quotes
                        # Pattern: "text": "some text with "quotes" inside"
                        # This is a simple heuristic, not perfect but helps
                        fixed_text = re.sub(r'("text":\s*")([^"]*?"[^"]*?)(")', lambda m: m.group(1) + m.group(2).replace('"', "'") + m.group(3), fixed_text)
                        script = json.loads(fixed_text)
                        logger.info("✅ Fixed JSON by replacing internal quotes")
                    except:
                        if attempt == max_attempts - 1:
                            return self._generate_script_mock(semantic_map, ocr_elements, presentation_context)
                        continue
                
                # Check anti-reading
                generated_text = " ".join([item.get('text', '') for item in script.get('talk_track', [])])
                
                # ✅ FIX: Validate text length to prevent 291 sec slides
                word_count = len(generated_text.split())
                estimated_seconds = (word_count / 150) * 60  # 150 words per minute
                
                if word_count > 400:  # Max ~2.5 minutes at 150 wpm
                    logger.warning(
                        f"⚠️ Generated talk_track is too long: {word_count} words "
                        f"(~{estimated_seconds:.0f}s), max 400 words (~160s)"
                    )
                    logger.warning(f"   Text preview: {generated_text[:200]}...")
                    # Regenerate with stricter prompt
                    if attempt < max_attempts - 1:
                        logger.info("🔄 Regenerating with stricter length constraints...")
                        prompt += "\n\nCRITICAL: Your previous response was TOO LONG. Generate SHORTER text (max 300 words total)."
                        continue
                
                overlap = self._calculate_overlap(generated_text, slide_text)
                
                if overlap < self.anti_reading_threshold:
                    logger.info(f"✅ Script passed anti-reading check (overlap: {overlap:.3f})")
                    script['overlap_score'] = overlap
                    
                    # ✅ Добавляем метаданные о персоне и типе контента
                    script['persona_used'] = persona_config['name']
                    script['content_type'] = content_type.value
                    script['complexity'] = complexity
                    
                    # ✅ Используем уже рассчитанную оптимальную длительность из промпта
                    # (она учитывает visual_density, cognitive_load, и количество групп)
                    word_count = len(generated_text.split())
                    
                    # Для обратной совместимости также рассчитываем через persona
                    from app.services.ai_personas import PersonaType
                    persona_enum = PersonaType(persona_type)
                    persona_duration = self.personas.calculate_optimal_duration(
                        word_count, persona_enum, complexity
                    )
                    
                    # Используем среднее между adaptive и persona duration
                    # (adaptive учитывает слайд, persona учитывает стиль речи)
                    # Получаем optimal_duration из последнего вызова prompt_builder
                    # Для этого нужно сохранить его или пересчитать
                    visual_density = semantic_map.get('visual_density', 'medium')
                    cognitive_load = semantic_map.get('cognitive_load', 'medium')
                    groups = semantic_map.get('groups', [])
                    filtered_groups = self.prompt_builder._filter_and_rank_groups(
                        groups, visual_density, cognitive_load, None
                    )
                    slide_duration = self.prompt_builder._calculate_optimal_duration(
                        filtered_groups, visual_density, cognitive_load
                    )
                    
                    # Гибридная оценка: слайд + стиль речи
                    final_duration = int((slide_duration * 0.6) + (persona_duration * 0.4))
                    script['recommended_duration'] = final_duration
                    script['slide_based_duration'] = slide_duration
                    script['persona_based_duration'] = persona_duration
                    
                    logger.info(
                        f"📊 Duration: {final_duration}s (slide: {slide_duration}s, "
                        f"persona: {persona_duration:.1f}s, words: {word_count})"
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
        
        # ✅ NEW: Use AdaptivePromptBuilder for intelligent group filtering and formatting
        groups_text, filtered_groups, optimal_duration = self.prompt_builder.build_adaptive_groups_section(
            semantic_map,
            ocr_elements,
            max_groups=None  # Auto-determine based on slide density
        )
        
        # ✅ NEW: Generate adaptive instructions based on slide characteristics
        adaptive_instructions = self.prompt_builder.generate_adaptive_instructions(
            semantic_map,
            content_strategy or {},
            len(filtered_groups)
        )
        
        # ✅ NEW: Generate duration hint
        visual_density = semantic_map.get('visual_density', 'medium')
        duration_hint = self.prompt_builder.build_duration_hint(optimal_duration, visual_density)
        
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
        
        return f"""Generate an engaging lecture script for this slide.

PRESENTATION CONTEXT:
- Theme: {theme}
- Level: {level}
- Language: {language}
- Style: {style}
- Slide {slide_index + 1} of {total_slides}

{persona_instructions}

{adaptive_instructions}

{duration_hint}

PREVIOUS SLIDES SUMMARY:
{previous_summary if previous_summary else "This is the first slide"}

{groups_text}

SLIDE TYPE: {semantic_map.get('slide_type', 'content_slide')}

🔴 КРИТИЧЕСКИ ВАЖНО - ГЛАВНОЕ ПРАВИЛО:
ГОВОРИ ТОЛЬКО О ТОМ, ЧТО ЕСТЬ НА СЛАЙДЕ!

1. ✅ РАЗРЕШЕНО: Упоминать конкретные элементы, которые видны на слайде
2. ❌ ЗАПРЕЩЕНО: Добавлять информацию, которой НЕТ на слайде
3. ❌ ЗАПРЕЩЕНО: Делать общие утверждения не связанные со слайдом
4. ❌ ЗАПРЕЩЕНО: Упоминать концепции, которых нет в "Text on slide"

🎯 КРИТИЧЕСКИ ВАЖНО ДЛЯ ВИЗУАЛЬНОЙ СИНХРОНИЗАЦИИ:
Когда упоминаешь несколько элементов из одной группы - РАЗДЕЛЯЙ ИХ НА ОТДЕЛЬНЫЕ ПРЕДЛОЖЕНИЯ!
Это необходимо для корректной синхронизации визуальных эффектов.

❌ ПЛОХО: "Снаружи находится эпидермис, гиподерма, палисадная паренхима и ксилема"
   (все элементы в одном предложении - невозможно синхронизировать визуал!)

✅ ХОРОШО: "Снаружи находится эпидермис. Под ним располагается гиподерма. Далее идёт палисадная паренхима. И наконец, ксилема."
   (каждый элемент в отдельном предложении - визуал будет выделяться последовательно!)

❌ ПЛОХО: "На слайде три типа листьев: простые, сложные и чешуйчатые"
   (список в одном предложении)

✅ ХОРОШО: "На слайде три типа листьев. Первый тип - простые листья. Второй тип - сложные листья. Третий тип - чешуйчатые листья."
   (каждый элемент отдельно)

💡 ПРАВИЛО: Один элемент = одно или несколько предложений. НЕ перечисляй элементы через запятую!

Примеры контекста:
❌ ПЛОХО: "Фотосинтез — важный процесс для всех растений" (если на слайде нет про фотосинтез)
✅ ХОРОШО: "На слайде три типа листьев. Рассмотрим каждый подробнее." (берём из "Text on slide")

CRITICAL RULES:
1. SPEAK ONLY about what IS on the slide (check "Text on slide" sections)
2. DO NOT add information from your knowledge if it's not on the slide
3. MENTION specific terms/keywords from "Text on slide" when explaining each group
4. DO NOT make general statements unrelated to slide content
5. Use conversational tone - imagine explaining to a student
6. Reference previous slides when relevant
7. **STRICT LENGTH LIMIT: 30-90 seconds MAXIMUM (200-300 words TOTAL for ALL 6 segments)**
8. Each segment should be SHORT (30-50 words each, NOT MORE)
9. **MANDATORY: Generate ALL text in "{language}" language**

⚠️ LENGTH VALIDATION:
- Total word count for ALL 6 segments MUST be under 300 words
- If you exceed this, the response will be REJECTED
- Be concise, clear, and to the point

🚨 SPECIAL RULE FOR TITLES/COURSE NAMES:
❌ DO NOT analyze or explain titles/course names in detail!
✅ Simply MENTION the title briefly (1 sentence max):
   "Сегодня тема: [название]" OR "Это курс номер X о [тема]"
❌ WRONG: "Итак, группа номер один – это название курса... Это означает, что мы будем изучать..."
✅ CORRECT: "Сегодня курс номер 3 о клеточной стенке и осмосе"
→ Then IMMEDIATELY move to actual content groups!

EXPLANATION STRATEGY:
- When talking about a group, naturally MENTION its key terms from "Text on slide"
- Don't just read the text - explain WHY it matters, give examples, add context

🚨 КРИТИЧЕСКИ ВАЖНО ДЛЯ СПИСКОВ И BULLET POINTS:
Если группа содержит НЕСКОЛЬКО элементов (например, список тканей, список пунктов, перечисление):
1. ✅ ОБЯЗАТЕЛЬНО упомяни КАЖДЫЙ элемент
2. ✅ КАЖДЫЙ элемент в ОТДЕЛЬНОМ предложении
3. ❌ НЕ пропускай элементы для краткости!
4. ❌ НЕ объединяй все элементы в одно перечисление через запятую!

Пример группы с 5 элементами:
❌ ПЛОХО: "На слайде три ткани: эпидермис, колленхима и хлоренхима" (упомянуты только 3 из 5!)
✅ ХОРОШО: "Первая ткань - эпидермис. Вторая ткань - колленхима. Третья - хлоренхима. Четвертая - склеренхима. И пятая - паренхима."

💡 ВАЖНО: Если инструкция говорит "This group has X items - mention EACH ONE" - это ОБЯЗАТЕЛЬНОЕ требование!

EXPLANATION STRATEGY:
- Naturally explain what you see on the slide
- Use clear Russian without foreign words
- Be specific and concrete, not generic

RETURN JSON (with text in {language}):

🚨 JSON FORMATTING RULES (CRITICAL):
- НЕ используй двойные кавычки " внутри текста (используй одинарные ' если нужно)
- НЕ используй переносы строк внутри text полей
- Пример ПРАВИЛЬНО: "text": "Это 'важный' процесс"
- Пример НЕПРАВИЛЬНО: "text": "Это "важный" процесс" ❌

{{
  "talk_track": [
    {{"segment": "hook", "text": "Short engaging opening (30-40 words max)", "group_id": "group_id_from_semantic_map_or_null"}},
    {{"segment": "context", "text": "Brief context (30-40 words max)", "group_id": "group_id_when_talking_about_specific_group"}},
    {{"segment": "explanation", "text": "Concise explanation (40-50 words max)", "group_id": "group_id_of_explained_element"}},
    {{"segment": "example", "text": "Quick example (30-40 words max)", "group_id": null}},
    {{"segment": "emphasis", "text": "Key point briefly (20-30 words max)", "group_id": "group_id_of_emphasized_element"}},
    {{"segment": "transition", "text": "Short transition (20-30 words max)", "group_id": null}}
  ],
  "speaker_notes": "Brief notes",
  "estimated_duration": 60
}}

⚠️ CRITICAL: Keep EACH segment under 50 words, TOTAL under 300 words for all 6 segments!

IMPORTANT ABOUT group_id (MANDATORY):
- **ALWAYS** include "group_id" field in EVERY talk_track segment
- When talking about a specific group, use its exact "id" from the semantic map above
- **REUSE the same group_id** for multiple consecutive segments if you're explaining/detailing the same concept
- Use null ONLY for general introductions that don't relate to any specific visual element
- This field enables precise visual synchronization between speech and highlights
- Available group IDs: {', '.join([g.get('id', 'unknown') for g in filtered_groups])}

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
        """
        Extract all text from elements for anti-reading check
        ✅ CRITICAL: Use translated text to avoid language mixing in TTS
        """
        texts = []
        for elem in elements:
            # Prefer translated text if available, fallback to original
            # This ensures anti-reading check works on the same text LLM will use
            text = elem.get('text_translated') or elem.get('text')
            if text:
                texts.append(text.lower())
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
    
    async def _generate_diagram_explanation(
        self,
        diagram_element: Dict[str, Any],
        presentation_context: Dict[str, Any],
        persona_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Генерирует специальное объяснение для диаграммы
        
        Returns:
            Dict с полями:
            - overview: краткий обзор диаграммы (5-10 сек)
            - walkthrough: подробное объяснение (15-30 сек)
            - conclusion: вывод (5-10 сек)
        """
        diagram_type = diagram_element.get('diagram_type', 'unknown')
        description = diagram_element.get('description', 'визуальный элемент')
        key_elements = diagram_element.get('key_elements', [])
        complexity = diagram_element.get('visual_complexity', 'medium')
        
        level = presentation_context.get('level', 'undergraduate')
        language = os.getenv('LLM_LANGUAGE', 'ru')
        
        # Адаптируем длину под сложность
        complexity_durations = {
            'low': (5, 10, 5),      # (overview, walkthrough, conclusion)
            'medium': (8, 20, 7),
            'high': (10, 30, 10)
        }
        target_overview, target_walkthrough, target_conclusion = complexity_durations.get(
            complexity, (8, 20, 7)
        )
        
        # Формируем промпт с учётом персоны
        persona_style = ""
        if persona_config:
            persona_style = f"""
Use {persona_config['name']} style:
- Tone: {persona_config.get('intro_style', '')}
- Use these markers: {persona_config.get('emphasis_markers', [])}
"""
        
        prompt = f"""Ты объясняешь {diagram_type} студентам уровня {level}.

**Диаграмма:** {description}
**Ключевые элементы:** {', '.join(key_elements) if key_elements else 'не указаны'}
**Сложность:** {complexity}
**Язык:** {language}

{persona_style}

**Задание:** Создай объяснение диаграммы в 3 сегмента:

1. **OVERVIEW** ({target_overview} сек): 
   - Что показывает эта диаграмма в целом?
   - Какую информацию она передаёт?
   - Для чего она здесь?

2. **WALKTHROUGH** ({target_walkthrough} сек):
   - Пройдись по ключевым элементам диаграммы
   - Объясни что означает каждый элемент
   - Покажи связи между элементами
   - Используй направление: слева направо / сверху вниз (в зависимости от типа)

3. **CONCLUSION** ({target_conclusion} сек):
   - Какой главный вывод из этой диаграммы?
   - Почему это важно для понимания темы?

**ВАЖНО:**
- Используй простой, разговорный язык
- НЕ читай подписи дословно - объясняй своими словами
- Избегай фраз "на этой диаграмме мы видим" - говори прямо
- Используй активные глаголы и примеры
- Длительность каждого сегмента должна быть примерно {target_overview}/{target_walkthrough}/{target_conclusion} секунд

**Формат ответа (JSON):**
{{
  "overview": "текст обзора...",
  "walkthrough": "текст подробного объяснения...",
  "conclusion": "текст вывода..."
}}

Верни ТОЛЬКО JSON, без лишнего текста."""

        try:
            if self.use_mock:
                # Mock response
                logger.info(f"⚠️ Using mock diagram explanation for {diagram_type}")
                
                if language == 'ru':
                    return {
                        "overview": f"Перед нами {diagram_type}, который показывает {description.lower()}.",
                        "walkthrough": f"Давайте рассмотрим основные элементы. {' Также видим '.join(key_elements[:3]) if key_elements else 'Элементы иллюстрируют ключевые концепты'}.",
                        "conclusion": f"Таким образом, эта диаграмма помогает нам понять важные взаимосвязи."
                    }
                else:
                    return {
                        "overview": f"Here we have a {diagram_type} showing {description.lower()}.",
                        "walkthrough": f"Let's examine the main elements. {' We also see '.join(key_elements[:3]) if key_elements else 'The elements illustrate key concepts'}.",
                        "conclusion": f"Thus, this diagram helps us understand important relationships."
                    }
            
            # Real LLM generation
            logger.info(f"🖼️ Generating explanation for {diagram_type} diagram...")
            
            # Generate with Gemini
            response = await self.llm_worker.generate_async(
                prompt=prompt,
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group(0))
                
                logger.info(f"✅ Generated diagram explanation: "
                          f"overview={len(result.get('overview', ''))} chars, "
                          f"walkthrough={len(result.get('walkthrough', ''))} chars, "
                          f"conclusion={len(result.get('conclusion', ''))} chars")
                
                return result
            else:
                raise ValueError("No JSON found in LLM response")
                
        except Exception as e:
            logger.error(f"❌ Failed to generate diagram explanation: {e}")
            
            # Fallback to simple template
            if language == 'ru':
                return {
                    "overview": f"Эта диаграмма типа {diagram_type} показывает нам важную информацию.",
                    "walkthrough": f"Рассмотрим основные элементы: {', '.join(key_elements[:3]) if key_elements else 'представлены ключевые данные'}.",
                    "conclusion": "Эта визуализация помогает лучше понять концепцию."
                }
            else:
                return {
                    "overview": f"This {diagram_type} diagram shows us important information.",
                    "walkthrough": f"Let's look at the main elements: {', '.join(key_elements[:3]) if key_elements else 'key data is presented'}.",
                    "conclusion": "This visualization helps us better understand the concept."
                }
    
    def _generate_script_mock(
        self,
        semantic_map: Dict[str, Any],
        ocr_elements: List[Dict[str, Any]],
        presentation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock script generation"""
        logger.info("Using mock script generation")
        
        # Extract some text from elements (use translated text if available)
        element_texts = [(elem.get('text_translated') or elem.get('text', ''))[:100] for elem in ocr_elements[:3]]
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
