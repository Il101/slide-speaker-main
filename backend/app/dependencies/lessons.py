"""
Dependencies for lesson-related endpoints
Provides reusable functions for lesson ownership checks
"""
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from ..core.database import get_db
from ..core.auth import get_current_user


def create_lesson_ownership_check(action: str = "access"):
    """
    Factory function to create a dependency that checks lesson ownership.
    
    Args:
        action: Action being performed (for error message): "access", "modify", "export", "view", "download"
    
    Returns:
        Dependency function that can be used with Depends()
    """
    async def check_ownership(
        lesson_id: str,
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> Dict[str, Any]:
        """
        Get lesson and check ownership, raise 403 if not authorized.
        
        Returns:
            Dict with lesson_id and user_id
        
        Raises:
            HTTPException 404: Lesson not found
            HTTPException 403: Not authorized
        """
        # Validate lesson_id format (prevent path traversal)
        from ..core.validators import validate_lesson_id
        lesson_id = validate_lesson_id(lesson_id)
        result = await db.execute(
            text("SELECT user_id FROM lessons WHERE id = :lesson_id"),
            {"lesson_id": lesson_id}
        )
        lesson_owner = result.scalar_one_or_none()
        
        if not lesson_owner:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        if lesson_owner != current_user["user_id"]:
            action_messages = {
                "access": "Not authorized to access this lesson",
                "modify": "Not authorized to modify this lesson",
                "export": "Not authorized to export this lesson",
                "view": "Not authorized to view this export status",
                "download": "Not authorized to download this video"
            }
            message = action_messages.get(action, "Not authorized to access this lesson")
            raise HTTPException(status_code=403, detail=message)
        
        return {"lesson_id": lesson_id, "user_id": lesson_owner}
    
    return check_ownership

