"""API endpoints for user's video library"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime, timezone
import logging

from ..core.auth import get_current_user
from ..core.database import get_db, Lesson, Export
from pydantic import BaseModel, Field, field_serializer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lessons", tags=["lessons"])


# Response models
class VideoPreview(BaseModel):
    """Video preview information"""
    lesson_id: str = Field(..., description="Lesson ID")
    title: str = Field(..., description="Video title")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL (first slide)")
    duration: Optional[float] = Field(None, description="Total duration in seconds")
    slides_count: Optional[int] = Field(None, description="Number of slides")
    status: str = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    video_url: Optional[str] = Field(None, description="URL to exported MP4 (if exists)")
    video_size: Optional[int] = Field(None, description="Video file size in bytes")
    can_play: bool = Field(..., description="Whether video can be played in player")

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info):
        """Serialize datetime with explicit UTC timezone for proper client-side conversion"""
        if dt.tzinfo is None:
            # Assume UTC if no timezone (PostgreSQL stores in UTC)
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class UserVideosResponse(BaseModel):
    """List of user's videos"""
    videos: List[VideoPreview] = Field(..., description="List of videos")
    total: int = Field(..., description="Total number of videos")


@router.get("/my-videos", response_model=UserVideosResponse)
async def get_user_videos(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """
    Get list of user's generated videos
    
    Returns:
    - Videos sorted by creation date (newest first)
    - Includes thumbnail, title, duration, status
    - Shows both completed lessons and exported MP4s
    """
    try:
        user_id = current_user["user_id"]
        
        # Get user's lessons
        query = (
            select(Lesson)
            .where(Lesson.user_id == user_id)
            .order_by(desc(Lesson.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        lessons = result.scalars().all()
        
        # Get count
        count_query = select(Lesson).where(Lesson.user_id == user_id)
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        # Build video previews
        videos = []
        for lesson in lessons:
            # Get export info if exists
            # Get thumbnail (first slide image)
            thumbnail_url = None
            if lesson.manifest_data and lesson.manifest_data.get("slides"):
                first_slide = lesson.manifest_data["slides"][0]
                thumbnail_url = first_slide.get("image")
            
            # Use total_duration from DB (calculated during processing)
            duration = lesson.total_duration
            
            # For now, no video URL (no export functionality yet)
            video_url = None
            video_size = None
            
            # Can play if lesson is completed (has manifest)
            can_play = lesson.status == "completed" and lesson.manifest_data is not None
            
            video = VideoPreview(
                lesson_id=lesson.id,
                title=lesson.title or f"Lesson {lesson.id[:8]}",
                thumbnail_url=thumbnail_url,
                duration=lesson.total_duration,
                slides_count=lesson.slides_count,
                status=lesson.status,
                created_at=lesson.created_at,
                updated_at=lesson.updated_at,
                video_url=video_url,
                video_size=video_size,
                can_play=can_play
            )
            
            videos.append(video)
        
        logger.info(f"Retrieved {len(videos)} videos for user {user_id}")
        
        return UserVideosResponse(
            videos=videos,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error retrieving user videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve videos: {str(e)}")


@router.get("/{lesson_id}", response_model=VideoPreview)
async def get_video_details(
    lesson_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific video
    """
    try:
        user_id = current_user["user_id"]
        
        # Get lesson
        query = select(Lesson).where(Lesson.id == lesson_id)
        result = await db.execute(query)
        lesson = result.scalar_one_or_none()
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Check ownership
        if lesson.user_id != user_id and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get export info
        export_query = (
            select(Export)
            .where(Export.lesson_id == lesson_id)
            .where(Export.status == "completed")
            .order_by(desc(Export.created_at))
            .limit(1)
        )
        export_result = await db.execute(export_query)
        export = export_result.scalar_one_or_none()
        
        # Get thumbnail
        thumbnail_url = None
        if lesson.manifest_data and lesson.manifest_data.get("slides"):
            first_slide = lesson.manifest_data["slides"][0]
            thumbnail_url = first_slide.get("image")
        
        # Video URL
        video_url = None
        video_size = None
        if export and export.file_path:
            video_url = f"/exports/{lesson.id}/download"
            video_size = export.file_size
        
        can_play = lesson.status == "completed" and lesson.manifest_data is not None
        
        return VideoPreview(
            lesson_id=lesson.id,
            title=lesson.title or f"Lesson {lesson.id[:8]}",
            thumbnail_url=thumbnail_url,
            duration=lesson.total_duration,
            slides_count=lesson.slides_count,
            status=lesson.status,
            created_at=lesson.created_at,
            updated_at=lesson.updated_at,
            video_url=video_url,
            video_size=video_size,
            can_play=can_play
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving video details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve video: {str(e)}")


@router.post("/{lesson_id}/cancel")
async def cancel_processing(
    lesson_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel processing of a video that is currently being processed
    
    This will:
    - Revoke the Celery task
    - Update lesson status to 'cancelled'
    - Clean up processing resources
    """
    try:
        user_id = current_user["user_id"]
        
        # Get lesson
        query = select(Lesson).where(Lesson.id == lesson_id)
        result = await db.execute(query)
        lesson = result.scalar_one_or_none()
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Check ownership
        if lesson.user_id != user_id and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if lesson is currently processing
        if lesson.status not in ["processing", "queued"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel video with status '{lesson.status}'. Only 'processing' or 'queued' videos can be cancelled."
            )
        
        # Revoke Celery task if task_id exists
        task_revoked = False
        if hasattr(lesson, 'task_id') and lesson.task_id:
            try:
                from ..celery_app import celery_app
                # Terminate=True will kill the worker process if task is running
                celery_app.control.revoke(lesson.task_id, terminate=True, signal='SIGTERM')
                task_revoked = True
                logger.info(f"Revoked Celery task {lesson.task_id} for lesson {lesson_id}")
            except Exception as e:
                logger.error(f"Error revoking Celery task: {e}")
        
        # Update lesson status to cancelled
        lesson.status = "cancelled"
        lesson.updated_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Cancelled processing for video {lesson_id} (user: {user_id}, task_revoked: {task_revoked})")
        
        return {
            "success": True, 
            "message": "Processing cancelled successfully",
            "task_revoked": task_revoked
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling video processing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel processing: {str(e)}")


@router.delete("/{lesson_id}")
async def delete_video(
    lesson_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user's video
    """
    try:
        user_id = current_user["user_id"]
        
        # Get lesson
        query = select(Lesson).where(Lesson.id == lesson_id)
        result = await db.execute(query)
        lesson = result.scalar_one_or_none()
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Check ownership
        if lesson.user_id != user_id and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete lesson and associated data
        await db.delete(lesson)
        await db.commit()
        
        logger.info(f"Deleted video {lesson_id} for user {user_id}")
        
        return {"success": True, "message": "Video deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")
