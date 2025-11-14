"""
AI-powered Quiz Generator using Google Gemini
Generates quizzes from lecture content with customizable settings
"""
import logging
from typing import Dict, List, Optional
import json
import re
import os
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)

class QuizGeneratorService:
    """AI-powered quiz generation service using Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.use_mock = not self.api_key
        
        if not self.use_mock:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.genai = genai
                # Use fast and cheap model for quiz generation
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("✅ QuizGenerator: Gemini 2.0 Flash configured")
            except Exception as e:
                logger.warning(f"Gemini setup failed: {e}, using mock mode")
                self.use_mock = True
    
    async def generate_quiz(
        self,
        lesson_id: str,
        user_id: str,
        lecture_content: str,
        settings: Dict
    ) -> Dict:
        """
        Generate quiz from lecture content
        
        Args:
            lesson_id: Lesson ID
            user_id: User ID
            lecture_content: Text content from lecture (speaker notes, transcripts)
            settings: Quiz generation settings (num_questions, types, difficulty, etc.)
            
        Returns:
            Quiz data ready for database insertion
        """
        logger.info(f"🎯 Generating quiz: {settings.get('num_questions', 10)} questions")
        
        if self.use_mock:
            logger.warning("Using mock quiz generation (no API key)")
            return self._generate_mock_quiz(lesson_id, user_id, settings)
        
        try:
            # Build prompt
            prompt = self._build_prompt(lecture_content, settings)
            
            # Generate with Gemini
            response = await self._generate_with_retry(prompt)
            
            # Parse and validate response
            quiz_data = self._parse_response(response.text)
            
            # Format for database insertion
            formatted = self._format_quiz_data(quiz_data, lesson_id, user_id, settings)
            
            logger.info(f"✅ Quiz generated: {len(formatted['questions'])} questions")
            return formatted
            
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            # Fallback to mock
            logger.warning("Falling back to mock quiz generation")
            return self._generate_mock_quiz(lesson_id, user_id, settings)
    
    async def _generate_with_retry(self, prompt: str, max_retries: int = 2):
        """Generate content with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.3,
                        'max_output_tokens': 4096,
                    }
                )
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Generation attempt {attempt + 1} failed: {e}, retrying...")
                    continue
                raise
    
    def _build_prompt(self, content: str, settings: Dict) -> str:
        """Build comprehensive prompt for Gemini"""
        
        # Limit content to avoid token limits (keep ~8000 chars = ~2000 tokens)
        content_preview = content[:8000] if len(content) > 8000 else content
        
        # Get question types as string
        types_list = settings.get('question_types', ['multiple_choice'])
        types_str = ", ".join(types_list)
        
        num_questions = settings.get('num_questions', 10)
        difficulty = settings.get('difficulty', 'medium')
        language = settings.get('language', 'ru')
        
        # Build difficulty instructions
        difficulty_guide = {
            "easy": "Базовые вопросы на понимание ключевых фактов",
            "medium": "Вопросы на применение и анализ концепций",
            "hard": "Вопросы на синтез и оценку информации",
            "mixed": "Микс: 30% простых, 50% средних, 20% сложных"
        }
        
        # Language instructions
        lang_instructions = {
            'ru': 'Все вопросы и ответы на русском языке',
            'en': 'All questions and answers in English',
            'de': 'Alle Fragen und Antworten auf Deutsch'
        }
        
        prompt = f"""Ты эксперт-преподаватель, создающий тест по материалам лекции.

СОДЕРЖАНИЕ ЛЕКЦИИ:
{content_preview}

ТРЕБОВАНИЯ К ТЕСТУ:
- Создай РОВНО {num_questions} вопросов
- Типы вопросов: {types_str}
- Сложность: {difficulty} - {difficulty_guide.get(difficulty, '')}
- Язык: {lang_instructions.get(language, lang_instructions['ru'])}

ПРАВИЛА СОЗДАНИЯ ВОПРОСОВ:
1. Проверяй ПОНИМАНИЕ, а не механическое запоминание
2. Вопросы должны быть чёткими и однозначными
3. Избегай «подковырок» и излишне мелких деталей
4. Фокусируйся на ключевых концепциях из лекции

ДЛЯ МНОЖЕСТВЕННОГО ВЫБОРА (multiple_choice):
- Предоставь 4 варианта ответа (A, B, C, D)
- РОВНО 1 правильный ответ
- 3 правдоподобных, но неверных дистрактора
- Дистракторы должны быть убедительными, не очевидно неправильными

ДЛЯ ВЫБОРА НЕСКОЛЬКИХ (multiple_select):
- Предоставь 4-5 вариантов
- 2-3 правильных ответа
- Укажи явно, что нужно выбрать несколько

ДЛЯ ВЕРНО/НЕВЕРНО (true_false):
- Утверждение должно требовать размышления
- Избегай очевидно верных/неверных утверждений
- Формулируй утверждения чётко и конкретно

ДЛЯ КРАТКИХ ОТВЕТОВ (short_answer):
- Вопрос должен иметь чёткий, определённый ответ
- Не слишком открытый вопрос

ОБЪЯСНЕНИЯ:
- Объясни, ПОЧЕМУ правильный ответ правильный
- Сошлись на конкретные концепции из лекции
- Держи объяснения краткими (1-2 предложения)

ФОРМАТ ВЫВОДА (СТРОГО JSON):
{{
  "title": "Тест по [Тема]",
  "description": "Краткое описание содержания теста",
  "questions": [
    {{
      "text": "Текст вопроса?",
      "type": "multiple_choice",
      "difficulty": "medium",
      "explanation": "Объяснение правильного ответа",
      "answers": [
        {{"text": "Вариант A", "is_correct": false}},
        {{"text": "Вариант B", "is_correct": true}},
        {{"text": "Вариант C", "is_correct": false}},
        {{"text": "Вариант D", "is_correct": false}}
      ]
    }}
  ]
}}

КРИТИЧЕСКИ ВАЖНО:
- Возвращай ТОЛЬКО валидный JSON
- БЕЗ markdown блоков кода
- БЕЗ пояснительного текста до или после JSON
- Все спецсимволы в JSON должны быть экранированы
- Ровно {num_questions} вопросов
"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse Gemini response and extract JSON"""
        
        # Clean markdown formatting
        cleaned = response_text.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Fallback: try to extract JSON from text
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            logger.error(f"Failed to parse quiz JSON: {e}")
            logger.error(f"Response preview: {cleaned[:500]}")
            raise ValueError(f"Failed to parse quiz JSON: {e}")
    
    def _format_quiz_data(
        self,
        quiz_data: Dict,
        lesson_id: str,
        user_id: str,
        settings: Dict
    ) -> Dict:
        """Format quiz data for database insertion"""
        
        # Validate we have the right number of questions
        questions = quiz_data.get("questions", [])
        num_questions = settings.get('num_questions', 10)
        
        if len(questions) != num_questions:
            # Trim or pad to match settings
            questions = questions[:num_questions]
            logger.warning(f"Question count mismatch: got {len(quiz_data.get('questions', []))}, expected {num_questions}")
        
        allowed_types = settings.get('question_types', ['multiple_choice'])
        formatted_questions = []
        
        for i, q_data in enumerate(questions):
            # Validate question type
            q_type = q_data.get("type", "multiple_choice")
            if q_type not in allowed_types:
                # Default to first allowed type
                q_type = allowed_types[0]
            
            # Format answers
            answers = []
            for j, ans_data in enumerate(q_data.get("answers", [])):
                answers.append({
                    "id": str(uuid4()),
                    "text": ans_data.get("text", ""),
                    "is_correct": ans_data.get("is_correct", False),
                    "order_index": j
                })
            
            # Ensure at least one correct answer
            if not any(a["is_correct"] for a in answers):
                if answers:
                    answers[0]["is_correct"] = True
            
            formatted_questions.append({
                "id": str(uuid4()),
                "text": q_data.get("text", ""),
                "type": q_type,
                "difficulty": q_data.get("difficulty", settings.get('difficulty', 'medium')),
                "explanation": q_data.get("explanation"),
                "points": 1,
                "order_index": i,
                "answers": answers,
                "created_at": datetime.utcnow()
            })
        
        return {
            "id": str(uuid4()),
            "lesson_id": lesson_id,
            "user_id": user_id,
            "title": quiz_data.get("title", "Generated Quiz"),
            "description": quiz_data.get("description"),
            "questions": formatted_questions,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    def _generate_mock_quiz(self, lesson_id: str, user_id: str, settings: Dict) -> Dict:
        """Generate a mock quiz for testing/fallback"""
        num_questions = settings.get('num_questions', 5)
        
        questions = []
        for i in range(num_questions):
            questions.append({
                "id": str(uuid4()),
                "text": f"Пример вопроса {i + 1} (MOCK MODE)",
                "type": "multiple_choice",
                "difficulty": "medium",
                "explanation": "Это тестовый вопрос в mock режиме",
                "points": 1,
                "order_index": i,
                "answers": [
                    {"id": str(uuid4()), "text": "Ответ A", "is_correct": True, "order_index": 0},
                    {"id": str(uuid4()), "text": "Ответ B", "is_correct": False, "order_index": 1},
                    {"id": str(uuid4()), "text": "Ответ C", "is_correct": False, "order_index": 2},
                    {"id": str(uuid4()), "text": "Ответ D", "is_correct": False, "order_index": 3},
                ],
                "created_at": datetime.utcnow()
            })
        
        return {
            "id": str(uuid4()),
            "lesson_id": lesson_id,
            "user_id": user_id,
            "title": "Mock Quiz (тестовый режим)",
            "description": "Это тестовый квиз в mock режиме. Настройте GOOGLE_API_KEY для реальной генерации.",
            "questions": questions,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }


# Cost estimation utility
class QuizCostTracker:
    """Track quiz generation costs"""
    
    # Gemini 2.0 Flash pricing (per 1M tokens)
    GEMINI_FLASH_INPUT = 0.0  # FREE under 128K tokens/minute
    GEMINI_FLASH_OUTPUT = 0.0  # FREE under 128K tokens/minute
    
    # Fallback to paid tier if needed
    GEMINI_FLASH_INPUT_PAID = 0.075 / 1_000_000  # $0.075 per 1M tokens
    GEMINI_FLASH_OUTPUT_PAID = 0.30 / 1_000_000  # $0.30 per 1M tokens
    
    @staticmethod
    def estimate_cost(lecture_chars: int, num_questions: int, use_free_tier: bool = True) -> float:
        """
        Estimate quiz generation cost
        
        Args:
            lecture_chars: Number of characters in lecture content
            num_questions: Number of questions to generate
            use_free_tier: Whether using free tier (under limits)
            
        Returns:
            Estimated cost in USD
        """
        if use_free_tier:
            return 0.0  # Free tier
        
        # Rough: 4 chars per token
        input_tokens = (lecture_chars / 4) + 500  # +500 for prompt
        output_tokens = num_questions * 150  # ~150 tokens per question with answers
        
        cost = (
            input_tokens * QuizCostTracker.GEMINI_FLASH_INPUT_PAID +
            output_tokens * QuizCostTracker.GEMINI_FLASH_OUTPUT_PAID
        )
        
        return cost
    
    @staticmethod
    async def track_generation(
        db,
        user_id: str,
        lesson_id: str,
        cost: float
    ):
        """Track cost in database"""
        from uuid import uuid4
        from datetime import datetime
        from sqlalchemy import text
        
        try:
            await db.execute(
                text("""
                    INSERT INTO cost_logs (id, operation, cost, user_id, lesson_id, timestamp, meta_data)
                    VALUES (:id, :operation, :cost, :user_id, :lesson_id, :timestamp, :meta_data)
                """),
                {
                    "id": str(uuid4()),
                    "operation": "quiz_generation",
                    "cost": cost,
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "timestamp": datetime.utcnow(),
                    "meta_data": json.dumps({"model": "gemini-2.0-flash-exp"})
                }
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to track quiz generation cost: {e}")
