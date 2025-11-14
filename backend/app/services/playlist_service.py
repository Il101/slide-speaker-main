"""Playlist service for managing playlists and items"""
import logging
import os
from typing import List, Optional, Dict
from uuid import uuid4
from datetime import datetime
import secrets
import hashlib
from sqlalchemy import select, func, delete, update, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ..core.database import Playlist, PlaylistItem, PlaylistView, Lesson
from ..models.playlist import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistListResponse,
    PlaylistItemResponse,
    PlaylistShareResponse,
    PlaylistAnalytics,
    PlaylistViewCreate,
)

logger = logging.getLogger(__name__)


class PlaylistService:
    """Service for playlist CRUD operations"""
    
    @staticmethod
    async def create_playlist(
        db: AsyncSession,
        user_id: str,
        data: PlaylistCreate
    ) -> PlaylistResponse:
        """Create new playlist with items"""
        logger.info(f"Creating playlist '{data.title}' for user {user_id}")
        
        # Verify user owns all lessons
        lesson_query = select(Lesson).where(
            Lesson.id.in_(data.lesson_ids),
            Lesson.user_id == user_id
        )
        result = await db.execute(lesson_query)
        lessons = result.scalars().all()
        
        if len(lessons) != len(data.lesson_ids):
            raise HTTPException(
                status_code=403,
                detail="You can only add your own lessons to a playlist"
            )
        
        # Hash password if provided
        password_hash = None
        if data.password:
            password_hash = hashlib.sha256(data.password.encode()).hexdigest()
        
        # Get thumbnail from first lesson if available
        thumbnail_url = None
        if lessons:
            first_lesson = lessons[0]
            if first_lesson.manifest_data and 'slides' in first_lesson.manifest_data:
                slides = first_lesson.manifest_data['slides']
                if slides and len(slides) > 0:
                    thumbnail_url = slides[0].get('image_path')
        
        # Create playlist
        playlist = Playlist(
            id=str(uuid4()),
            user_id=user_id,
            title=data.title,
            description=data.description,
            thumbnail_url=thumbnail_url,
            is_public=data.is_public,
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(playlist)
        
        # Create items in order
        for idx, lesson_id in enumerate(data.lesson_ids):
            item = PlaylistItem(
                id=str(uuid4()),
                playlist_id=playlist.id,
                lesson_id=lesson_id,
                order_index=idx,
                created_at=datetime.utcnow(),
            )
            db.add(item)
        
        await db.commit()
        await db.refresh(playlist)
        
        logger.info(f"✅ Playlist created: {playlist.id}")
        return await PlaylistService.get_playlist(db, playlist.id, user_id)
    
    @staticmethod
    async def get_user_playlists(
        db: AsyncSession,
        user_id: str
    ) -> List[PlaylistListResponse]:
        """Get all playlists for user"""
        query = select(Playlist).where(Playlist.user_id == user_id).order_by(Playlist.created_at.desc())
        result = await db.execute(query)
        playlists = result.scalars().all()
        
        response = []
        for playlist in playlists:
            # Count items and sum duration
            items_query = select(
                func.count(PlaylistItem.id),
                func.sum(Lesson.total_duration)
            ).join(
                Lesson, PlaylistItem.lesson_id == Lesson.id
            ).where(
                PlaylistItem.playlist_id == playlist.id
            )
            items_result = await db.execute(items_query)
            video_count, total_duration = items_result.first() or (0, None)
            
            response.append(PlaylistListResponse(
                id=playlist.id,
                user_id=playlist.user_id,
                title=playlist.title,
                description=playlist.description,
                thumbnail_url=playlist.thumbnail_url,
                is_public=playlist.is_public,
                has_password=bool(playlist.password_hash),
                video_count=video_count or 0,
                total_duration=total_duration,
                created_at=playlist.created_at,
                updated_at=playlist.updated_at,
            ))
        
        return response
    
    @staticmethod
    async def get_playlist(
        db: AsyncSession,
        playlist_id: str,
        user_id: Optional[str] = None,
        password: Optional[str] = None
    ) -> PlaylistResponse:
        """Get single playlist with items"""
        query = select(Playlist).where(Playlist.id == playlist_id)
        result = await db.execute(query)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Check access permissions
        if playlist.user_id != user_id:
            # Non-owner trying to access
            if not playlist.is_public:
                raise HTTPException(status_code=403, detail="This playlist is private")
            
            # Check password if required
            if playlist.password_hash:
                if not password:
                    raise HTTPException(status_code=401, detail="Password required")
                
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if password_hash != playlist.password_hash:
                    raise HTTPException(status_code=403, detail="Incorrect password")
        
        # Get items with lesson details
        items_query = select(
            PlaylistItem,
            Lesson.title,
            Lesson.manifest_data,
            Lesson.total_duration,
            Lesson.status
        ).join(
            Lesson, PlaylistItem.lesson_id == Lesson.id
        ).where(
            PlaylistItem.playlist_id == playlist_id
        ).order_by(PlaylistItem.order_index)
        
        items_result = await db.execute(items_query)
        items_data = items_result.all()
        
        items = []
        total_duration = 0.0
        for item, lesson_title, manifest_data, lesson_duration, lesson_status in items_data:
            # Extract thumbnail from manifest
            lesson_thumbnail = None
            if manifest_data and 'slides' in manifest_data:
                slides = manifest_data['slides']
                if slides and len(slides) > 0:
                    lesson_thumbnail = slides[0].get('image_path')
            
            items.append(PlaylistItemResponse(
                id=item.id,
                playlist_id=item.playlist_id,
                lesson_id=item.lesson_id,
                order_index=item.order_index,
                lesson_title=lesson_title,
                lesson_thumbnail=lesson_thumbnail,
                lesson_duration=lesson_duration,
                lesson_status=lesson_status,
                created_at=item.created_at,
            ))
            
            if lesson_duration:
                total_duration += lesson_duration
        
        return PlaylistResponse(
            id=playlist.id,
            user_id=playlist.user_id,
            title=playlist.title,
            description=playlist.description,
            thumbnail_url=playlist.thumbnail_url,
            is_public=playlist.is_public,
            has_password=bool(playlist.password_hash),
            share_token=playlist.share_token,
            video_count=len(items),
            total_duration=total_duration if total_duration > 0 else None,
            items=items,
            created_at=playlist.created_at,
            updated_at=playlist.updated_at,
        )
    
    @staticmethod
    async def get_playlist_by_token(
        db: AsyncSession,
        share_token: str,
        password: Optional[str] = None
    ) -> PlaylistResponse:
        """Get playlist by share token (public access)"""
        query = select(Playlist).where(Playlist.share_token == share_token)
        result = await db.execute(query)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        if not playlist.is_public:
            raise HTTPException(status_code=403, detail="This playlist is not public")
        
        return await PlaylistService.get_playlist(db, playlist.id, None, password)
    
    @staticmethod
    async def update_playlist(
        db: AsyncSession,
        playlist_id: str,
        user_id: str,
        data: PlaylistUpdate
    ) -> PlaylistResponse:
        """Update playlist metadata"""
        query = select(Playlist).where(Playlist.id == playlist_id)
        result = await db.execute(query)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        if playlist.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Update fields
        if data.title is not None:
            playlist.title = data.title
        if data.description is not None:
            playlist.description = data.description
        if data.is_public is not None:
            playlist.is_public = data.is_public
        if data.thumbnail_url is not None:
            playlist.thumbnail_url = data.thumbnail_url
        if data.password is not None:
            playlist.password_hash = hashlib.sha256(data.password.encode()).hexdigest()
        
        playlist.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(playlist)
        
        return await PlaylistService.get_playlist(db, playlist_id, user_id)
    
    @staticmethod
    async def delete_playlist(
        db: AsyncSession,
        playlist_id: str,
        user_id: str
    ) -> None:
        """Delete playlist (cascade deletes items)"""
        query = select(Playlist).where(Playlist.id == playlist_id)
        result = await db.execute(query)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        if playlist.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        await db.delete(playlist)
        await db.commit()
        logger.info(f"Deleted playlist {playlist_id}")
    
    @staticmethod
    async def add_videos_to_playlist(
        db: AsyncSession,
        playlist_id: str,
        user_id: str,
        lesson_ids: List[str]
    ) -> PlaylistResponse:
        """Add videos to existing playlist"""
        query = select(Playlist).where(Playlist.id == playlist_id)
        result = await db.execute(query)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        if playlist.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Verify user owns lessons
        lesson_query = select(Lesson).where(
            Lesson.id.in_(lesson_ids),
            Lesson.user_id == user_id
        )
        result = await db.execute(lesson_query)
        lessons = result.scalars().all()
        
        if len(lessons) != len(lesson_ids):
            raise HTTPException(status_code=403, detail="Can only add your own lessons")
        
        # Get current max order_index
        max_order_query = select(func.max(PlaylistItem.order_index)).where(
            PlaylistItem.playlist_id == playlist_id
        )
        result = await db.execute(max_order_query)
        max_order = result.scalar() or -1
        
        # Add new items
        for idx, lesson_id in enumerate(lesson_ids):
            # Check if already exists
            exists_query = select(PlaylistItem).where(
                PlaylistItem.playlist_id == playlist_id,
                PlaylistItem.lesson_id == lesson_id
            )
            exists_result = await db.execute(exists_query)
            if exists_result.scalar_one_or_none():
                logger.warning(f"Lesson {lesson_id} already in playlist {playlist_id}, skipping")
                continue
            
            item = PlaylistItem(
                id=str(uuid4()),
                playlist_id=playlist_id,
                lesson_id=lesson_id,
                order_index=max_order + idx + 1,
                created_at=datetime.utcnow(),
            )
            db.add(item)
        
        playlist.updated_at = datetime.utcnow()
        await db.commit()
        
        return await PlaylistService.get_playlist(db, playlist_id, user_id)
    
    @staticmethod
    async def remove_video_from_playlist(
        db: AsyncSession,
        playlist_id: str,
        item_id: str,
        user_id: str
    ) -> PlaylistResponse:
        """Remove video from playlist"""
        playlist_query = select(Playlist).where(Playlist.id == playlist_id)
        result = await db.execute(playlist_query)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        if playlist.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Delete item
        delete_stmt = delete(PlaylistItem).where(
            PlaylistItem.id == item_id,
            PlaylistItem.playlist_id == playlist_id
        )
        await db.execute(delete_stmt)
        
        # Reorder remaining items
        items_query = select(PlaylistItem).where(
            PlaylistItem.playlist_id == playlist_id
        ).order_by(PlaylistItem.order_index)
        result = await db.execute(items_query)
        items = result.scalars().all()
        
        for idx, item in enumerate(items):
            item.order_index = idx
        
        playlist.updated_at = datetime.utcnow()
        await db.commit()
        
        return await PlaylistService.get_playlist(db, playlist_id, user_id)
    
    @staticmethod
    async def reorder_playlist_items(
        db: AsyncSession,
        playlist_id: str,
        item_id: str,
        new_order_index: int,
        user_id: str
    ) -> PlaylistResponse:
        """Reorder items in playlist"""
        playlist_query = select(Playlist).where(Playlist.id == playlist_id)
        result = await db.execute(playlist_query)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        if playlist.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get all items
        items_query = select(PlaylistItem).where(
            PlaylistItem.playlist_id == playlist_id
        ).order_by(PlaylistItem.order_index)
        result = await db.execute(items_query)
        items = list(result.scalars().all())
        
        # Find item to move
        item_to_move = None
        old_index = None
        for idx, item in enumerate(items):
            if item.id == item_id:
                item_to_move = item
                old_index = idx
                break
        
        if not item_to_move:
            raise HTTPException(status_code=404, detail="Item not found in playlist")
        
        # Reorder
        items.pop(old_index)
        items.insert(new_order_index, item_to_move)
        
        # Update all order_index values
        for idx, item in enumerate(items):
            item.order_index = idx
        
        playlist.updated_at = datetime.utcnow()
        await db.commit()
        
        return await PlaylistService.get_playlist(db, playlist_id, user_id)
    
    @staticmethod
    async def generate_share_token(
        db: AsyncSession,
        playlist_id: str,
        user_id: str
    ) -> PlaylistShareResponse:
        """Generate share token for playlist"""
        query = select(Playlist).where(Playlist.id == playlist_id)
        result = await db.execute(query)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        if playlist.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Generate token if not exists
        if not playlist.share_token:
            playlist.share_token = secrets.token_urlsafe(16)
            await db.commit()
            await db.refresh(playlist)
        
        # Build share URL (you can customize this based on your frontend URL)
        # ✅ FIX: Get frontend URL from environment instead of hardcoding
        base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        share_url = f"{base_url}/playlists/shared/{playlist.share_token}"
        
        # Build embed code
        embed_code = f'<iframe src="{share_url}" width="800" height="600" frameborder="0" allowfullscreen></iframe>'
        
        return PlaylistShareResponse(
            share_url=share_url,
            embed_code=embed_code,
            share_token=playlist.share_token,
            is_public=playlist.is_public,
            has_password=bool(playlist.password_hash),
        )
    
    @staticmethod
    async def track_view(
        db: AsyncSession,
        playlist_id: str,
        viewer_id: Optional[str],
        ip_address: Optional[str],
        data: PlaylistViewCreate
    ) -> None:
        """Track playlist view for analytics"""
        view = PlaylistView(
            id=str(uuid4()),
            playlist_id=playlist_id,
            viewer_id=viewer_id,
            ip_address=ip_address,
            completed=data.completed,
            videos_watched=data.videos_watched,
            total_watch_time=data.total_watch_time,
            viewed_at=datetime.utcnow(),
        )
        db.add(view)
        await db.commit()
        logger.info(f"Tracked view for playlist {playlist_id}")
    
    @staticmethod
    async def get_analytics(
        db: AsyncSession,
        playlist_id: str,
        user_id: str
    ) -> PlaylistAnalytics:
        """Get analytics for playlist (owner only)"""
        playlist_query = select(Playlist).where(Playlist.id == playlist_id)
        result = await db.execute(playlist_query)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        if playlist.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get view statistics
        views_query = select(
            func.count(PlaylistView.id).label('total_views'),
            func.count(func.distinct(PlaylistView.viewer_id)).label('unique_viewers'),
            func.avg(PlaylistView.videos_watched).label('avg_videos_watched'),
            func.sum(PlaylistView.total_watch_time).label('total_watch_time'),
            func.sum(func.cast(PlaylistView.completed, Integer)).label('completed_count')
        ).where(PlaylistView.playlist_id == playlist_id)
        
        result = await db.execute(views_query)
        stats = result.first()
        
        total_views = stats.total_views or 0
        unique_viewers = stats.unique_viewers or 0
        avg_watch_time = stats.avg_videos_watched or 0
        total_watch_time = stats.total_watch_time or 0
        completed_count = stats.completed_count or 0
        
        completion_rate = completed_count / total_views if total_views > 0 else 0
        
        # Get video watch distribution
        distribution_query = select(
            PlaylistView.videos_watched,
            func.count(PlaylistView.id)
        ).where(
            PlaylistView.playlist_id == playlist_id
        ).group_by(PlaylistView.videos_watched)
        
        result = await db.execute(distribution_query)
        distribution = {str(videos): count for videos, count in result.all()}
        
        return PlaylistAnalytics(
            playlist_id=playlist_id,
            total_views=total_views,
            unique_viewers=unique_viewers,
            completion_rate=completion_rate,
            average_watch_time=float(avg_watch_time) if avg_watch_time else None,
            total_watch_time=float(total_watch_time) if total_watch_time else None,
            videos_watched_distribution=distribution,
        )
