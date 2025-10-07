"""
AI Personas - разные стили презентации для разных аудиторий
Улучшение качества AI генерации контента
"""
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PersonaType(str, Enum):
    """Типы персон для AI лектора"""
    PROFESSOR = "professor"  # Академический стиль
    TUTOR = "tutor"  # Дружелюбный преподаватель
    BUSINESS_COACH = "business_coach"  # Бизнес-консультант
    STORYTELLER = "storyteller"  # Рассказчик историй
    TECHNICAL_EXPERT = "technical_expert"  # Технический эксперт
    MOTIVATIONAL_SPEAKER = "motivational_speaker"  # Мотивационный спикер


class AIPersonas:
    """
    Система персонажей для адаптации стиля AI лектора
    
    Каждая персона определяет:
    - Тон речи
    - Темп презентации
    - Тип примеров
    - Глубину объяснений
    - Модификаторы промптов
    """
    
    PERSONAS = {
        PersonaType.PROFESSOR: {
            "name": "Профессор",
            "description": "Академический стиль, глубокие объяснения, теоретические примеры",
            "tone": "academic",
            "pace": "measured",
            "speaking_rate": 0.9,  # Медленнее для сложных концепций
            "examples": "theoretical",
            "depth": "comprehensive",
            "formality": "high",
            "use_technical_terms": True,
            "prompt_modifier": """
You are a university professor giving a lecture.
Style:
- Use academic language and precise terminology
- Provide thorough, comprehensive explanations
- Reference theoretical foundations and research
- Build concepts logically and systematically
- Use scholarly examples and citations
- Maintain professional, formal tone
- Emphasize understanding over memorization
""",
            "intro_style": "Начнём с фундаментальных концепций...",
            "transition_style": "Следуя из предыдущего, рассмотрим...",
            "emphasis_markers": ["важно отметить", "ключевой момент", "существенно"],
        },
        
        PersonaType.TUTOR: {
            "name": "Репетитор",
            "description": "Дружелюбный, терпеливый, практические примеры",
            "tone": "friendly",
            "pace": "adaptive",
            "speaking_rate": 1.0,  # Нормальный темп
            "examples": "practical",
            "depth": "intuitive",
            "formality": "medium",
            "use_technical_terms": False,
            "prompt_modifier": """
You are a patient, friendly tutor helping students learn.
Style:
- Use simple, clear language
- Break down complex ideas into digestible parts
- Provide relatable, practical examples from everyday life
- Encourage learning with positive reinforcement
- Check for understanding frequently
- Use analogies and metaphors
- Make learning enjoyable and accessible
""",
            "intro_style": "Давайте разберёмся вместе...",
            "transition_style": "Теперь, когда мы поняли это, давайте...",
            "emphasis_markers": ["обратите внимание", "это важно", "запомните"],
        },
        
        PersonaType.BUSINESS_COACH: {
            "name": "Бизнес-коуч",
            "description": "Динамичный, фокус на действия, кейсы из практики",
            "tone": "dynamic",
            "pace": "fast",
            "speaking_rate": 1.1,  # Быстрее для бизнес-аудитории
            "examples": "case_studies",
            "depth": "actionable",
            "formality": "medium",
            "use_technical_terms": False,
            "prompt_modifier": """
You are a business consultant presenting to executives.
Style:
- Be concise and action-oriented
- Focus on practical business impact
- Use real-world case studies and examples
- Emphasize ROI and measurable results
- Provide clear next steps and takeaways
- Use business terminology naturally
- Be energetic and engaging
- Cut to the chase - no fluff
""",
            "intro_style": "Прямо к делу...",
            "transition_style": "Следующий важный момент...",
            "emphasis_markers": ["ключевой инсайт", "практический вывод", "action item"],
        },
        
        PersonaType.STORYTELLER: {
            "name": "Рассказчик",
            "description": "Увлекательные истории, эмоциональная связь, образные примеры",
            "tone": "narrative",
            "pace": "varied",
            "speaking_rate": 1.0,
            "examples": "stories",
            "depth": "engaging",
            "formality": "low",
            "use_technical_terms": False,
            "prompt_modifier": """
You are a storyteller captivating your audience.
Style:
- Weave concepts into engaging narratives
- Use vivid, descriptive language
- Create emotional connections
- Build suspense and curiosity
- Use metaphors and analogies
- Make abstract concepts concrete through stories
- Vary pacing for dramatic effect
- Paint mental pictures
""",
            "intro_style": "Представьте себе...",
            "transition_style": "А теперь давайте перенесёмся...",
            "emphasis_markers": ["вот в чём суть", "и здесь происходит магия", "ключевой момент истории"],
        },
        
        PersonaType.TECHNICAL_EXPERT: {
            "name": "Технический эксперт",
            "description": "Точный, детальный, технические подробности",
            "tone": "precise",
            "pace": "methodical",
            "speaking_rate": 0.95,
            "examples": "technical",
            "depth": "detailed",
            "formality": "high",
            "use_technical_terms": True,
            "prompt_modifier": """
You are a technical expert explaining implementation details.
Style:
- Be extremely precise and accurate
- Provide technical specifications and details
- Use correct technical terminology
- Explain step-by-step processes
- Reference standards and best practices
- Include edge cases and gotchas
- Assume technical competence
- Focus on "how" and "why" at technical level
""",
            "intro_style": "С технической точки зрения...",
            "transition_style": "Переходя к следующему компоненту...",
            "emphasis_markers": ["критически важно", "технически", "в частности"],
        },
        
        PersonaType.MOTIVATIONAL_SPEAKER: {
            "name": "Мотивационный спикер",
            "description": "Вдохновляющий, энергичный, акцент на возможности",
            "tone": "inspirational",
            "pace": "dynamic",
            "speaking_rate": 1.05,
            "examples": "success_stories",
            "depth": "motivating",
            "formality": "low",
            "use_technical_terms": False,
            "prompt_modifier": """
You are a motivational speaker inspiring your audience.
Style:
- Be energetic and passionate
- Inspire action and possibility
- Use empowering language
- Share success stories and transformations
- Challenge limiting beliefs
- Create vision of what's possible
- Be authentic and vulnerable
- End with clear call to action
""",
            "intro_style": "Сегодня вы откроете для себя...",
            "transition_style": "И вот где это становится по-настоящему захватывающим...",
            "emphasis_markers": ["представьте возможности", "это меняет всё", "вот ваша возможность"],
        },
    }
    
    @classmethod
    def get_persona(cls, persona_type: PersonaType) -> Dict[str, Any]:
        """Получить конфигурацию персоны"""
        return cls.PERSONAS.get(persona_type, cls.PERSONAS[PersonaType.TUTOR])
    
    @classmethod
    def get_all_personas(cls) -> Dict[str, Dict[str, Any]]:
        """Получить все доступные персоны"""
        return cls.PERSONAS
    
    @classmethod
    def get_persona_names(cls) -> Dict[str, str]:
        """Получить список имён персон для UI"""
        return {
            persona_type.value: config["name"]
            for persona_type, config in cls.PERSONAS.items()
        }
    
    @classmethod
    def adapt_prompt_for_persona(
        cls,
        base_prompt: str,
        persona_type: PersonaType,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Адаптировать промпт под выбранную персону
        
        Args:
            base_prompt: Базовый промпт для генерации
            persona_type: Тип персоны
            additional_context: Дополнительный контекст
            
        Returns:
            Модифицированный промпт
        """
        persona = cls.get_persona(persona_type)
        
        # Добавляем модификатор персоны
        adapted_prompt = f"{persona['prompt_modifier']}\n\n{base_prompt}"
        
        # Добавляем стилистические инструкции
        style_instructions = f"""

STYLE GUIDELINES:
- Tone: {persona['tone']}
- Pace: {persona['pace']}
- Example types: {persona['examples']}
- Explanation depth: {persona['depth']}
- Formality: {persona['formality']}
- Technical terms: {"Use freely" if persona['use_technical_terms'] else "Explain in simple language"}

Use these transition phrases:
- Intro: "{persona['intro_style']}"
- Transitions: "{persona['transition_style']}"
- Emphasis: {persona['emphasis_markers']}
"""
        
        adapted_prompt += style_instructions
        
        # Добавляем дополнительный контекст если есть
        if additional_context:
            if additional_context.get("audience_level"):
                adapted_prompt += f"\nAudience level: {additional_context['audience_level']}"
            if additional_context.get("time_constraint"):
                adapted_prompt += f"\nTime constraint: {additional_context['time_constraint']} seconds"
        
        return adapted_prompt
    
    @classmethod
    def get_speaking_rate(cls, persona_type: PersonaType) -> float:
        """Получить рекомендованную скорость речи для TTS"""
        persona = cls.get_persona(persona_type)
        return persona.get("speaking_rate", 1.0)
    
    @classmethod
    def calculate_optimal_duration(
        cls,
        word_count: int,
        persona_type: PersonaType,
        content_complexity: float = 0.5
    ) -> float:
        """
        Рассчитать оптимальную длительность слайда
        
        Args:
            word_count: Количество слов в скрипте
            persona_type: Тип персоны
            content_complexity: Сложность контента (0.0-1.0)
            
        Returns:
            Длительность в секундах
        """
        persona = cls.get_persona(persona_type)
        base_wpm = 150  # Базовая скорость слов в минуту
        
        # Корректируем на основе персоны
        speaking_rate = persona.get("speaking_rate", 1.0)
        adjusted_wpm = base_wpm * speaking_rate
        
        # Корректируем на основе сложности
        if content_complexity > 0.7:  # Сложный контент
            adjusted_wpm *= 0.8
        elif content_complexity < 0.3:  # Простой контент
            adjusted_wpm *= 1.2
        
        # Рассчитываем длительность
        duration_minutes = word_count / adjusted_wpm
        duration_seconds = duration_minutes * 60
        
        # Добавляем паузы
        pause_factor = 1.1  # 10% на паузы
        if persona.get("pace") == "measured":
            pause_factor = 1.2  # Больше пауз для академического стиля
        elif persona.get("pace") == "fast":
            pause_factor = 1.05  # Меньше пауз для бизнес-стиля
        
        final_duration = duration_seconds * pause_factor
        
        # Ограничиваем минимум и максимум
        final_duration = max(15.0, min(120.0, final_duration))
        
        logger.info(
            f"Calculated duration for {persona_type.value}: "
            f"{word_count} words, complexity {content_complexity:.2f} = {final_duration:.1f}s"
        )
        
        return final_duration
    
    @classmethod
    def select_persona_for_presentation(
        cls,
        presentation_context: Dict[str, Any]
    ) -> PersonaType:
        """
        Автоматически выбрать персону на основе контекста презентации
        
        Args:
            presentation_context: Контекст из PresentationIntelligence
            
        Returns:
            Рекомендованный тип персоны
        """
        subject_area = presentation_context.get("subject_area", "").lower()
        level = presentation_context.get("level", "").lower()
        style = presentation_context.get("presentation_style", "").lower()
        
        # Правила выбора персоны
        if "business" in subject_area or "corporate" in style:
            return PersonaType.BUSINESS_COACH
        
        if level in ["graduate", "phd"] or "academic" in style:
            return PersonaType.PROFESSOR
        
        if level in ["high_school", "undergraduate"]:
            return PersonaType.TUTOR
        
        if subject_area in ["computer_science", "engineering", "mathematics"]:
            return PersonaType.TECHNICAL_EXPERT
        
        if "storytelling" in style or "narrative" in style:
            return PersonaType.STORYTELLER
        
        if "motivation" in style or "inspirational" in style:
            return PersonaType.MOTIVATIONAL_SPEAKER
        
        # По умолчанию - дружелюбный репетитор
        return PersonaType.TUTOR
    
    @classmethod
    def get_persona_config_for_api(cls, persona_type: PersonaType) -> Dict[str, Any]:
        """Получить конфигурацию для API запроса"""
        persona = cls.get_persona(persona_type)
        return {
            "speaking_rate": persona["speaking_rate"],
            "pitch": 0.0,  # Можно добавить варьирование
            "volume_gain_db": 0.0,
        }


# Utility функции для быстрого доступа
def get_persona(persona_type: str = "tutor") -> Dict[str, Any]:
    """Удобная функция для получения персоны"""
    try:
        persona_enum = PersonaType(persona_type)
        return AIPersonas.get_persona(persona_enum)
    except ValueError:
        logger.warning(f"Unknown persona type: {persona_type}, using TUTOR")
        return AIPersonas.get_persona(PersonaType.TUTOR)


def adapt_prompt(prompt: str, persona_type: str = "tutor") -> str:
    """Удобная функция для адаптации промпта"""
    try:
        persona_enum = PersonaType(persona_type)
        return AIPersonas.adapt_prompt_for_persona(prompt, persona_enum)
    except ValueError:
        logger.warning(f"Unknown persona type: {persona_type}, using original prompt")
        return prompt
