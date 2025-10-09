"""Playlist Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class PlaylistItemResponse(BaseModel):
    """Single item in playlist with lesson details"""
    id: str
    playlist_id: str
    lesson_id: str
    order_index: int
    # Lesson details (joined from lessons table)
    lesson_title: str
    lesson_thumbnail: Optional[str] = None
    lesson_duration: Optional[float] = None
    lesson_status: str
    created_at: datetime


class PlaylistCreate(BaseModel):
    """Create new playlist"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: bool = False
    password: Optional[str] = Field(None, min_length=4, max_length=50)
    lesson_ids: List[str] = Field(..., min_items=1)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v, info):
        """Password required only if is_public is True"""
        data = info.data
        if v and not data.get('is_public', False):
            raise ValueError("Password can only be set for public playlists")
        return v


class PlaylistUpdate(BaseModel):
    """Update playlist metadata"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=4, max_length=50)
    thumbnail_url: Optional[str] = None


class PlaylistResponse(BaseModel):
    """Full playlist with items"""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    is_public: bool
    has_password: bool  # Don't expose actual password
    share_token: Optional[str]
    video_count: int
    total_duration: Optional[float]
    items: List[PlaylistItemResponse]
    created_at: datetime
    updated_at: datetime


class PlaylistListResponse(BaseModel):
    """Playlist in list view (without items)"""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    is_public: bool
    has_password: bool
    video_count: int
    total_duration: Optional[float]
    created_at: datetime
    updated_at: datetime


class PlaylistAddVideosRequest(BaseModel):
    """Add videos to existing playlist"""
    lesson_ids: List[str] = Field(..., min_items=1)


class PlaylistReorderRequest(BaseModel):
    """Reorder items in playlist"""
    item_id: str
    new_order_index: int = Field(..., ge=0)


class PlaylistShareResponse(BaseModel):
    """Share info with URL and embed code"""
    share_url: str
    embed_code: str
    share_token: str
    is_public: bool
    has_password: bool


class PlaylistAnalytics(BaseModel):
    """Analytics data for playlist"""
    playlist_id: str
    total_views: int
    unique_viewers: int
    completion_rate: float  # 0.0 to 1.0
    average_watch_time: Optional[float]
    total_watch_time: Optional[float]
    videos_watched_distribution: dict  # {video_index: watch_count}


class PlaylistViewCreate(BaseModel):
    """Track playlist view"""
    videos_watched: int = Field(0, ge=0)
    completed: bool = False
    total_watch_time: Optional[int] = None


class PlaylistAccessRequest(BaseModel):
    """Request access to password-protected playlist"""
    password: Optional[str] = None
