"""WebSocket connection manager for real-time progress updates"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time progress updates.
    
    Features:
    - Multiple connections per lesson (multiple users watching same lesson)
    - Automatic cleanup on disconnect
    - Broadcast to all watchers of a lesson
    - JSON serialization of progress updates
    """
    
    def __init__(self):
        # lesson_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> lesson_id mapping for quick cleanup
        self.connection_to_lesson: Dict[WebSocket, str] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, lesson_id: str):
        """
        Accept and register a new WebSocket connection for a lesson
        
        Args:
            websocket: WebSocket connection
            lesson_id: Lesson ID to subscribe to
        """
        await websocket.accept()
        
        async with self._lock:
            if lesson_id not in self.active_connections:
                self.active_connections[lesson_id] = set()
            
            self.active_connections[lesson_id].add(websocket)
            self.connection_to_lesson[websocket] = lesson_id
        
        logger.info(f"WebSocket connected for lesson {lesson_id} (total: {len(self.active_connections[lesson_id])})")
    
    async def disconnect(self, websocket: WebSocket):
        """
        Unregister a WebSocket connection
        
        Args:
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if websocket in self.connection_to_lesson:
                lesson_id = self.connection_to_lesson[websocket]
                
                if lesson_id in self.active_connections:
                    self.active_connections[lesson_id].discard(websocket)
                    
                    # Clean up empty sets
                    if not self.active_connections[lesson_id]:
                        del self.active_connections[lesson_id]
                
                del self.connection_to_lesson[websocket]
                
                logger.info(f"WebSocket disconnected from lesson {lesson_id}")
    
    async def send_progress(
        self,
        lesson_id: str,
        stage: str,
        percent: float,
        message: str,
        current_slide: Optional[int] = None,
        total_slides: Optional[int] = None,
        eta_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Send progress update to all connections watching this lesson
        
        Args:
            lesson_id: Lesson ID
            stage: Current processing stage (e.g., "ocr", "ai_generation", "tts")
            percent: Overall progress percentage (0-100)
            message: Human-readable progress message
            current_slide: Current slide being processed (optional)
            total_slides: Total number of slides (optional)
            eta_seconds: Estimated time to completion in seconds (optional)
            metadata: Additional metadata (optional)
        """
        if lesson_id not in self.active_connections:
            # No active connections for this lesson
            return
        
        progress_data = {
            "type": "progress",
            "lesson_id": lesson_id,
            "stage": stage,
            "percent": min(100, max(0, percent)),  # Clamp to 0-100
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if current_slide is not None:
            progress_data["current_slide"] = current_slide
        
        if total_slides is not None:
            progress_data["total_slides"] = total_slides
        
        if eta_seconds is not None:
            progress_data["eta_seconds"] = eta_seconds
            progress_data["eta_formatted"] = self._format_eta(eta_seconds)
        
        if metadata:
            progress_data["metadata"] = metadata
        
        await self._broadcast(lesson_id, progress_data)
    
    async def send_completion(
        self,
        lesson_id: str,
        success: bool,
        message: str,
        result_data: Optional[Dict[str, Any]] = None
    ):
        """
        Send completion notification
        
        Args:
            lesson_id: Lesson ID
            success: Whether processing was successful
            message: Completion message
            result_data: Result data (e.g., manifest, duration)
        """
        if lesson_id not in self.active_connections:
            return
        
        completion_data = {
            "type": "completion",
            "lesson_id": lesson_id,
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if result_data:
            completion_data["result"] = result_data
        
        await self._broadcast(lesson_id, completion_data)
    
    async def send_error(
        self,
        lesson_id: str,
        error_type: str,
        error_message: str,
        stage: Optional[str] = None
    ):
        """
        Send error notification
        
        Args:
            lesson_id: Lesson ID
            error_type: Type of error (e.g., "api_error", "processing_error")
            error_message: Error message
            stage: Stage where error occurred (optional)
        """
        if lesson_id not in self.active_connections:
            return
        
        error_data = {
            "type": "error",
            "lesson_id": lesson_id,
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if stage:
            error_data["stage"] = stage
        
        await self._broadcast(lesson_id, error_data)
    
    async def send_slide_update(
        self,
        lesson_id: str,
        slide_number: int,
        status: str,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Send slide-specific update
        
        Args:
            lesson_id: Lesson ID
            slide_number: Slide number
            status: Status (e.g., "processing", "completed", "failed")
            message: Optional message
            data: Optional slide data
        """
        if lesson_id not in self.active_connections:
            return
        
        slide_update = {
            "type": "slide_update",
            "lesson_id": lesson_id,
            "slide_number": slide_number,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if message:
            slide_update["message"] = message
        
        if data:
            slide_update["data"] = data
        
        await self._broadcast(lesson_id, slide_update)
    
    async def _broadcast(self, lesson_id: str, data: Dict[str, Any]):
        """
        Broadcast message to all connections for a lesson
        
        Args:
            lesson_id: Lesson ID
            data: Data to broadcast
        """
        if lesson_id not in self.active_connections:
            return
        
        # Create a copy of connections to avoid modification during iteration
        connections = list(self.active_connections[lesson_id])
        
        # Send to all connections concurrently
        tasks = []
        for connection in connections:
            tasks.append(self._send_json(connection, data))
        
        # Wait for all sends, but don't fail if some connections are dead
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_json(self, websocket: WebSocket, data: Dict[str, Any]):
        """
        Send JSON data to a WebSocket, handling errors
        
        Args:
            websocket: WebSocket connection
            data: Data to send
        """
        try:
            await websocket.send_json(data)
        except WebSocketDisconnect:
            # Connection closed, clean it up
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            await self.disconnect(websocket)
    
    @staticmethod
    def _format_eta(seconds: float) -> str:
        """Format ETA seconds into human-readable string"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def get_connection_count(self, lesson_id: str) -> int:
        """Get number of active connections for a lesson"""
        return len(self.active_connections.get(lesson_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
ws_manager = ConnectionManager()


def get_ws_manager() -> ConnectionManager:
    """Get the global WebSocket manager instance"""
    return ws_manager
