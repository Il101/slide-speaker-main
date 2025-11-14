"""Quiz Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
from datetime import datetime
from uuid import UUID

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    MULTIPLE_SELECT = "multiple_select"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"

class AnswerCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    is_correct: bool = False

class AnswerResponse(AnswerCreate):
    id: str
    order_index: int

class QuestionCreate(BaseModel):
    text: str = Field(..., min_length=5, max_length=1000)
    type: QuestionType
    difficulty: Difficulty = Difficulty.MEDIUM
    explanation: Optional[str] = Field(None, max_length=1000)
    points: int = Field(1, ge=1, le=10)
    answers: List[AnswerCreate] = Field(..., min_items=2, max_items=10)
    
    @field_validator('answers')
    @classmethod
    def validate_answers(cls, v, info):
        """Ensure at least one correct answer for MC/MS, exactly 2 answers for T/F"""
        if not v:
            raise ValueError("At least 2 answers required")
        
        # Check if we have question_type in the data
        data = info.data
        if 'type' not in data:
            return v
            
        q_type = data['type']
        
        if q_type == QuestionType.TRUE_FALSE and len(v) != 2:
            raise ValueError("True/False questions must have exactly 2 answers")
        
        if q_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.MULTIPLE_SELECT):
            correct_count = sum(1 for ans in v if ans.is_correct)
            if correct_count == 0:
                raise ValueError("At least one answer must be correct")
            if q_type == QuestionType.MULTIPLE_CHOICE and correct_count > 1:
                raise ValueError("Multiple choice must have exactly one correct answer")
        
        return v

class QuestionUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=5, max_length=1000)
    type: Optional[QuestionType] = None
    difficulty: Optional[Difficulty] = None
    explanation: Optional[str] = Field(None, max_length=1000)
    points: Optional[int] = Field(None, ge=1, le=10)
    answers: Optional[List[AnswerCreate]] = None

class QuestionResponse(BaseModel):
    id: str
    quiz_id: str
    text: str
    type: QuestionType
    difficulty: Difficulty
    explanation: Optional[str]
    points: int
    order_index: int
    answers: List[AnswerResponse]
    created_at: datetime

class QuizCreate(BaseModel):
    lesson_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    questions: List[QuestionCreate] = Field(..., min_items=1, max_items=100)

class QuizUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    questions: Optional[List[QuestionCreate]] = None

class QuizResponse(BaseModel):
    id: str
    lesson_id: str
    user_id: str
    title: str
    description: Optional[str]
    questions: List[QuestionResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class QuizGenerationSettings(BaseModel):
    num_questions: int = Field(10, ge=5, le=50)
    question_types: List[QuestionType] = [QuestionType.MULTIPLE_CHOICE]
    difficulty: Difficulty = Difficulty.MEDIUM
    language: str = Field("ru", pattern="^(ru|en|de)$")
    focus_slides: Optional[List[int]] = None

class QuizGenerateRequest(BaseModel):
    lesson_id: str
    settings: QuizGenerationSettings = Field(default_factory=QuizGenerationSettings)

class ExportFormat(str, Enum):
    JSON = "json"
    PDF = "pdf"
    GOOGLE_FORMS = "google_forms"
    MOODLE_XML = "moodle"
    HTML = "html"

class QuizExportRequest(BaseModel):
    format: ExportFormat

class QuizListResponse(BaseModel):
    id: str
    lesson_id: str
    title: str
    description: Optional[str]
    questions_count: int
    created_at: datetime
    updated_at: datetime
