"""Database configuration and models"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, JSON, Integer, Float, Boolean
from datetime import datetime
from typing import Optional, Dict, Any, List
import os

from .config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=False  # Set to True for SQL debugging
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """Base class for all database models"""
    pass

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="user")
    subscription_tier: Mapped[str] = mapped_column(String(50), default="free")  # free, starter, pro, business
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Lesson(Base):
    """Lesson model for storing lesson metadata"""
    __tablename__ = "lessons"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="processing")  # processing, completed, failed, cancelled
    task_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)  # Celery task ID for cancellation
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    file_type: Mapped[Optional[str]] = mapped_column(String(50))
    slides_count: Mapped[Optional[int]] = mapped_column(Integer)
    total_duration: Mapped[Optional[float]] = mapped_column(Float)
    manifest_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    processing_progress: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

class Slide(Base):
    """Slide model for storing slide metadata"""
    __tablename__ = "slides"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    lesson_id: Mapped[str] = mapped_column(String(36), index=True)
    slide_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    speaker_notes: Mapped[Optional[str]] = mapped_column(Text)
    audio_duration: Mapped[Optional[float]] = mapped_column(Float)
    audio_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    image_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    elements_data: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    cues_data: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Export(Base):
    """Export model for tracking video exports"""
    __tablename__ = "exports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    lesson_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(50), default="queued")  # queued, processing, completed, failed
    quality: Mapped[str] = mapped_column(String(20), default="high")
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    duration: Mapped[Optional[float]] = mapped_column(Float)
    progress: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

# Analytics Models
class AnalyticsEvent(Base):
    """Analytics event tracking"""
    __tablename__ = "analytics_events"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    event_name: Mapped[str] = mapped_column(String(255), index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    properties: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Metadata
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    device: Mapped[Optional[str]] = mapped_column(String(50))  # mobile, desktop, tablet
    browser: Mapped[Optional[str]] = mapped_column(String(100))
    os: Mapped[Optional[str]] = mapped_column(String(100))

class UserSession(Base):
    """User session tracking"""
    __tablename__ = "user_sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    page_views: Mapped[int] = mapped_column(Integer, default=0)
    
    # Session data
    landing_page: Mapped[Optional[str]] = mapped_column(String(500))
    referrer: Mapped[Optional[str]] = mapped_column(String(500))
    utm_source: Mapped[Optional[str]] = mapped_column(String(100))
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100))
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Device info
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    country: Mapped[Optional[str]] = mapped_column(String(100))

class DailyMetrics(Base):
    """Daily aggregated metrics"""
    __tablename__ = "daily_metrics"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    date: Mapped[datetime] = mapped_column(DateTime, unique=True, index=True)
    
    # User metrics
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    new_users: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    
    # Usage metrics
    lectures_created: Mapped[int] = mapped_column(Integer, default=0)
    presentations_uploaded: Mapped[int] = mapped_column(Integer, default=0)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Revenue metrics
    new_subscriptions: Mapped[int] = mapped_column(Integer, default=0)
    cancelled_subscriptions: Mapped[int] = mapped_column(Integer, default=0)
    mrr: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Costs
    total_costs: Mapped[float] = mapped_column(Float, default=0.0)
    ocr_costs: Mapped[float] = mapped_column(Float, default=0.0)
    ai_costs: Mapped[float] = mapped_column(Float, default=0.0)
    tts_costs: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Conversion
    signup_to_lecture_rate: Mapped[Optional[float]] = mapped_column(Float)
    free_to_paid_rate: Mapped[Optional[float]] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CostLog(Base):
    """Individual cost tracking"""
    __tablename__ = "cost_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    operation: Mapped[str] = mapped_column(String(50), index=True)  # ocr, ai_generation, tts, storage
    cost: Mapped[float] = mapped_column(Float)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

class Subscription(Base):
    """Subscription model for tracking user subscriptions"""
    __tablename__ = "subscriptions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    tier: Mapped[str] = mapped_column(String(50))  # free, starter, pro, business
    price: Mapped[float] = mapped_column(Float, default=0.0)  # Monthly price in USD
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, cancelled, expired, trial
    billing_cycle: Mapped[str] = mapped_column(String(20), default="monthly")  # monthly, yearly
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trial_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Quiz Models
class Quiz(Base):
    """Quiz model for storing quiz metadata"""
    __tablename__ = "quizzes"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    lesson_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class QuizQuestion(Base):
    """Quiz question model"""
    __tablename__ = "quiz_questions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    quiz_id: Mapped[str] = mapped_column(String(36), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(50))  # multiple_choice, multiple_select, true_false, short_answer
    difficulty: Mapped[Optional[str]] = mapped_column(String(20))  # easy, medium, hard
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    points: Mapped[int] = mapped_column(Integer, default=1)
    order_index: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class QuizAnswer(Base):
    """Quiz answer model"""
    __tablename__ = "quiz_answers"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    question_id: Mapped[str] = mapped_column(String(36), index=True)
    answer_text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    order_index: Mapped[int] = mapped_column(Integer)

class QuizAttempt(Base):
    """Quiz attempt model for analytics"""
    __tablename__ = "quiz_attempts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    quiz_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    score: Mapped[Optional[float]] = mapped_column(Float)
    max_score: Mapped[Optional[float]] = mapped_column(Float)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

# Playlist Models
class Playlist(Base):
    """Playlist model for grouping lessons"""
    __tablename__ = "playlists"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    share_token: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PlaylistItem(Base):
    """Playlist item model - junction table between playlists and lessons"""
    __tablename__ = "playlist_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    playlist_id: Mapped[str] = mapped_column(String(36), index=True)
    lesson_id: Mapped[str] = mapped_column(String(36), index=True)
    order_index: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PlaylistView(Base):
    """Playlist view model for analytics"""
    __tablename__ = "playlist_views"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    playlist_id: Mapped[str] = mapped_column(String(36), index=True)
    viewer_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    videos_watched: Mapped[int] = mapped_column(Integer, default=0)
    total_watch_time: Mapped[Optional[int]] = mapped_column(Integer)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

# Database dependency
async def get_db() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Database initialization
async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close database connections"""
    await engine.dispose()
