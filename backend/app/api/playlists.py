"""
Playlist API Router
Endpoints for playlist creation, management, sharing, and analytics
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.auth import get_current_user, get_current_user_optional
from ..models.playlist import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistListResponse,
    PlaylistAddVideosRequest,
    PlaylistReorderRequest,
    PlaylistShareResponse,
    PlaylistAnalytics,
    PlaylistViewCreate,
    PlaylistAccessRequest,
)
from ..services.playlist_service import PlaylistService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


@router.post("", response_model=PlaylistResponse)
async def create_playlist(
    data: PlaylistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create new playlist with videos
    
    **Requires authentication**
    """
    return await PlaylistService.create_playlist(db, current_user["sub"], data)


@router.get("", response_model=List[PlaylistListResponse])
async def get_user_playlists(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all playlists for current user
    
    **Requires authentication**
    """
    return await PlaylistService.get_user_playlists(db, current_user["sub"])


@router.get("/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: str,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get single playlist with items
    
    - Owner can always access
    - Non-owners can access if playlist is public
    - Password required for password-protected public playlists
    """
    user_id = current_user["sub"] if current_user else None
    return await PlaylistService.get_playlist(db, playlist_id, user_id, password)


@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: str,
    data: PlaylistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update playlist metadata
    
    **Requires authentication and ownership**
    """
    return await PlaylistService.update_playlist(db, playlist_id, current_user["sub"], data)


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete playlist (cascade deletes items and views)
    
    **Requires authentication and ownership**
    """
    await PlaylistService.delete_playlist(db, playlist_id, current_user["sub"])
    return {"message": "Playlist deleted successfully"}


@router.post("/{playlist_id}/videos", response_model=PlaylistResponse)
async def add_videos_to_playlist(
    playlist_id: str,
    data: PlaylistAddVideosRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add videos to existing playlist
    
    **Requires authentication and ownership**
    """
    return await PlaylistService.add_videos_to_playlist(
        db, playlist_id, current_user["sub"], data.lesson_ids
    )


@router.delete("/{playlist_id}/videos/{item_id}", response_model=PlaylistResponse)
async def remove_video_from_playlist(
    playlist_id: str,
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Remove video from playlist
    
    **Requires authentication and ownership**
    """
    return await PlaylistService.remove_video_from_playlist(
        db, playlist_id, item_id, current_user["sub"]
    )


@router.post("/{playlist_id}/reorder", response_model=PlaylistResponse)
async def reorder_playlist_items(
    playlist_id: str,
    data: PlaylistReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Reorder items in playlist
    
    **Requires authentication and ownership**
    """
    return await PlaylistService.reorder_playlist_items(
        db, playlist_id, data.item_id, data.new_order_index, current_user["sub"]
    )


@router.get("/{playlist_id}/share", response_model=PlaylistShareResponse)
async def get_share_info(
    playlist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get share info for playlist (generates token if needed)
    
    **Requires authentication and ownership**
    """
    return await PlaylistService.generate_share_token(db, playlist_id, current_user["sub"])


@router.post("/{playlist_id}/view")
async def track_playlist_view(
    playlist_id: str,
    data: PlaylistViewCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Track playlist view for analytics
    
    - Can be called by authenticated or anonymous users
    - Tracks viewing progress and completion
    """
    user_id = current_user["sub"] if current_user else None
    ip_address = request.client.host if request.client else None
    
    await PlaylistService.track_view(db, playlist_id, user_id, ip_address, data)
    return {"message": "View tracked successfully"}


@router.get("/{playlist_id}/analytics", response_model=PlaylistAnalytics)
async def get_playlist_analytics(
    playlist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get analytics for playlist
    
    **Requires authentication and ownership**
    
    Returns:
    - Total views and unique viewers
    - Completion rate
    - Average watch time
    - Video watch distribution
    """
    return await PlaylistService.get_analytics(db, playlist_id, current_user["sub"])


@router.get("/shared/{share_token}", response_model=PlaylistResponse)
async def get_playlist_by_token(
    share_token: str,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get playlist by share token (public access)
    
    - No authentication required
    - Password required for password-protected playlists
    """
    return await PlaylistService.get_playlist_by_token(db, share_token, password)


@router.post("/shared/{share_token}/access", response_model=PlaylistResponse)
async def access_protected_playlist(
    share_token: str,
    data: PlaylistAccessRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Access password-protected playlist with password
    
    - No authentication required
    - Returns playlist if password is correct
    """
    return await PlaylistService.get_playlist_by_token(db, share_token, data.password)
