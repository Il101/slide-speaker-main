"""
Quiz API Router
Endpoints for quiz generation, management, and export
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
import logging
from datetime import datetime

from ..core.database import get_db, Lesson, Quiz, QuizQuestion, QuizAnswer
from ..core.auth import get_current_user
from ..models.quiz import (
    QuizGenerateRequest, QuizResponse, QuizCreate, QuizUpdate,
    QuizListResponse, QuizExportRequest, QuestionResponse, AnswerResponse
)
from ..services.quiz_generator import QuizGeneratorService, QuizCostTracker
from ..services.quiz_exporter import QuizExporter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])

# Initialize quiz generator
quiz_generator = QuizGeneratorService()


async def get_lecture_content(db: AsyncSession, lesson_id: str) -> str:
    """
    Extract lecture content from lesson manifest
    
    Args:
        db: Database session
        lesson_id: Lesson ID
        
    Returns:
        Combined text content from speaker notes and talk tracks
    """
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    
    manifest = lesson.manifest_data
    if not manifest or 'slides' not in manifest:
        raise HTTPException(400, "Lesson has no content to generate quiz from")
    
    # Extract content from slides
    content_parts = []
    
    for slide in manifest.get('slides', []):
        # Add speaker notes
        if slide.get('speaker_notes'):
            if isinstance(slide['speaker_notes'], list):
                # Structured format
                for note in slide['speaker_notes']:
                    if isinstance(note, dict) and 'text' in note:
                        content_parts.append(note['text'])
                    elif isinstance(note, str):
                        content_parts.append(note)
            elif isinstance(slide['speaker_notes'], str):
                content_parts.append(slide['speaker_notes'])
        
        # Add talk track
        if slide.get('talk_track'):
            for segment in slide['talk_track']:
                if isinstance(segment, dict) and 'text' in segment:
                    content_parts.append(segment['text'])
        
        # Add lecture text if available
        if slide.get('lecture_text'):
            content_parts.append(slide['lecture_text'])
    
    content = '\n\n'.join(content_parts)
    
    if not content.strip():
        raise HTTPException(400, "No text content found in lesson to generate quiz")
    
    logger.info(f"Extracted {len(content)} characters from lesson {lesson_id}")
    return content


async def save_quiz_to_db(db: AsyncSession, quiz_data: dict) -> Quiz:
    """
    Save quiz with questions and answers to database
    
    Args:
        db: Database session
        quiz_data: Quiz data dict from generator
        
    Returns:
        Saved Quiz object
    """
    # Create quiz
    quiz = Quiz(
        id=quiz_data['id'],
        lesson_id=quiz_data['lesson_id'],
        user_id=quiz_data['user_id'],
        title=quiz_data['title'],
        description=quiz_data.get('description'),
        created_at=quiz_data['created_at'],
        updated_at=quiz_data['updated_at']
    )
    
    db.add(quiz)
    await db.flush()
    
    # Create questions and answers
    for q_data in quiz_data['questions']:
        question = QuizQuestion(
            id=q_data['id'],
            quiz_id=quiz.id,
            question_text=q_data['text'],
            question_type=q_data['type'],
            difficulty=q_data.get('difficulty'),
            explanation=q_data.get('explanation'),
            points=q_data.get('points', 1),
            order_index=q_data['order_index'],
            created_at=q_data['created_at']
        )
        
        db.add(question)
        await db.flush()
        
        # Create answers
        for a_data in q_data['answers']:
            answer = QuizAnswer(
                id=a_data['id'],
                question_id=question.id,
                answer_text=a_data['text'],
                is_correct=a_data['is_correct'],
                order_index=a_data['order_index']
            )
            db.add(answer)
    
    await db.commit()
    await db.refresh(quiz)
    
    return quiz


async def load_quiz_with_questions(db: AsyncSession, quiz_id: str) -> QuizResponse:
    """Load quiz with all questions and answers"""
    
    # Get quiz
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    
    # Get questions
    result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == quiz_id)
        .order_by(QuizQuestion.order_index)
    )
    questions = result.scalars().all()
    
    # Build response
    questions_response = []
    for question in questions:
        # Get answers
        result = await db.execute(
            select(QuizAnswer)
            .where(QuizAnswer.question_id == question.id)
            .order_by(QuizAnswer.order_index)
        )
        answers = result.scalars().all()
        
        answers_response = [
            AnswerResponse(
                id=a.id,
                text=a.answer_text,
                is_correct=a.is_correct,
                order_index=a.order_index
            )
            for a in answers
        ]
        
        questions_response.append(
            QuestionResponse(
                id=question.id,
                quiz_id=question.quiz_id,
                text=question.question_text,
                type=question.question_type,
                difficulty=question.difficulty or 'medium',
                explanation=question.explanation,
                points=question.points,
                order_index=question.order_index,
                answers=answers_response,
                created_at=question.created_at
            )
        )
    
    return QuizResponse(
        id=quiz.id,
        lesson_id=quiz.lesson_id,
        user_id=quiz.user_id,
        title=quiz.title,
        description=quiz.description,
        questions=questions_response,
        created_at=quiz.created_at,
        updated_at=quiz.updated_at
    )


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a quiz from lecture content using AI
    
    Args:
        request: Quiz generation request with lesson_id and settings
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Generated quiz with questions
    """
    logger.info(f"🎯 Quiz generation requested by user {current_user.id} for lesson {request.lesson_id}")
    
    # Check if lesson exists and belongs to user
    result = await db.execute(
        select(Lesson).where(
            Lesson.id == request.lesson_id,
            Lesson.user_id == current_user.id
        )
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(404, "Lesson not found or access denied")
    
    # Get lecture content
    lecture_content = await get_lecture_content(db, request.lesson_id)
    
    # Estimate cost
    estimated_cost = QuizCostTracker.estimate_cost(
        len(lecture_content),
        request.settings.num_questions,
        use_free_tier=True  # Gemini 2.0 Flash is free under limits
    )
    
    logger.info(f"Estimated cost: ${estimated_cost:.4f}")
    
    # Generate quiz
    quiz_data = await quiz_generator.generate_quiz(
        lesson_id=request.lesson_id,
        user_id=current_user.id,
        lecture_content=lecture_content,
        settings=request.settings.dict()
    )
    
    # Save to database
    quiz = await save_quiz_to_db(db, quiz_data)
    
    # Track cost in background
    if estimated_cost > 0:
        background_tasks.add_task(
            QuizCostTracker.track_generation,
            db, current_user.id, lesson.id, estimated_cost
        )
    
    # Load and return full quiz
    return await load_quiz_with_questions(db, quiz.id)


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a quiz by ID"""
    
    # Check ownership
    result = await db.execute(
        select(Quiz).where(
            Quiz.id == quiz_id,
            Quiz.user_id == current_user.id
        )
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(404, "Quiz not found or access denied")
    
    return await load_quiz_with_questions(db, quiz_id)


@router.put("/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: str,
    update_data: QuizUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a quiz (title, description, questions)"""
    
    # Check ownership
    result = await db.execute(
        select(Quiz).where(
            Quiz.id == quiz_id,
            Quiz.user_id == current_user.id
        )
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(404, "Quiz not found or access denied")
    
    # Update quiz fields
    if update_data.title is not None:
        quiz.title = update_data.title
    if update_data.description is not None:
        quiz.description = update_data.description
    
    # Update questions if provided
    if update_data.questions is not None:
        # Delete existing questions (cascade will delete answers)
        await db.execute(
            delete(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
        )
        await db.flush()
        
        # Create new questions
        from uuid import uuid4
        for i, q_data in enumerate(update_data.questions):
            question = QuizQuestion(
                id=str(uuid4()),
                quiz_id=quiz.id,
                question_text=q_data.text,
                question_type=q_data.type.value,
                difficulty=q_data.difficulty.value if q_data.difficulty else 'medium',
                explanation=q_data.explanation,
                points=q_data.points,
                order_index=i,
                created_at=datetime.utcnow()
            )
            
            db.add(question)
            await db.flush()
            
            # Create answers
            for j, a_data in enumerate(q_data.answers):
                answer = QuizAnswer(
                    id=str(uuid4()),
                    question_id=question.id,
                    answer_text=a_data.text,
                    is_correct=a_data.is_correct,
                    order_index=j
                )
                db.add(answer)
    
    quiz.updated_at = datetime.utcnow()
    await db.commit()
    
    return await load_quiz_with_questions(db, quiz_id)


@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a quiz"""
    
    # Check ownership
    result = await db.execute(
        select(Quiz).where(
            Quiz.id == quiz_id,
            Quiz.user_id == current_user.id
        )
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(404, "Quiz not found or access denied")
    
    await db.delete(quiz)
    await db.commit()
    
    return {"message": "Quiz deleted successfully", "quiz_id": quiz_id}


@router.get("/lesson/{lesson_id}", response_model=List[QuizListResponse])
async def get_lesson_quizzes(
    lesson_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all quizzes for a lesson"""
    
    # Check lesson ownership
    result = await db.execute(
        select(Lesson).where(
            Lesson.id == lesson_id,
            Lesson.user_id == current_user.id
        )
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(404, "Lesson not found or access denied")
    
    # Get quizzes
    result = await db.execute(
        select(Quiz)
        .where(Quiz.lesson_id == lesson_id)
        .order_by(Quiz.created_at.desc())
    )
    quizzes = result.scalars().all()
    
    # Build response with question counts
    response = []
    for quiz in quizzes:
        result = await db.execute(
            select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id)
        )
        questions_count = len(result.scalars().all())
        
        response.append(
            QuizListResponse(
                id=quiz.id,
                lesson_id=quiz.lesson_id,
                title=quiz.title,
                description=quiz.description,
                questions_count=questions_count,
                created_at=quiz.created_at,
                updated_at=quiz.updated_at
            )
        )
    
    return response


@router.post("/{quiz_id}/export")
async def export_quiz(
    quiz_id: str,
    export_request: QuizExportRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export quiz to various formats (JSON, Moodle XML, HTML)"""
    
    # Check ownership
    result = await db.execute(
        select(Quiz).where(
            Quiz.id == quiz_id,
            Quiz.user_id == current_user.id
        )
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(404, "Quiz not found or access denied")
    
    # Load full quiz data
    quiz_data = await load_quiz_with_questions(db, quiz_id)
    
    # Convert to dict for exporter
    quiz_dict = {
        "id": quiz_data.id,
        "title": quiz_data.title,
        "description": quiz_data.description,
        "questions": [
            {
                "text": q.text,
                "type": q.type,
                "difficulty": q.difficulty,
                "explanation": q.explanation,
                "answers": [
                    {
                        "text": a.text,
                        "is_correct": a.is_correct
                    }
                    for a in q.answers
                ]
            }
            for q in quiz_data.questions
        ]
    }
    
    # Export
    try:
        exported_content = QuizExporter.export(quiz_dict, export_request.format.value)
        
        # Determine content type
        content_types = {
            "json": "application/json",
            "moodle": "application/xml",
            "moodle_xml": "application/xml",
            "html": "text/html",
        }
        
        return {
            "format": export_request.format.value,
            "content": exported_content,
            "content_type": content_types.get(export_request.format.value, "text/plain"),
            "filename": f"{quiz.title}_{quiz.id}.{export_request.format.value}"
        }
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(500, f"Export failed: {str(e)}")
