"""WebSocket API endpoints for real-time progress updates"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import logging

from ..core.websocket_manager import get_ws_manager, ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_current_user_from_token(token: Optional[str] = Query(None)) -> Optional[dict]:
    """
    Get current user from WebSocket query parameter token
    
    Args:
        token: JWT token from query parameter
        
    Returns:
        User dict or None if no auth required for WebSocket
    """
    if not token:
        # Allow anonymous WebSocket connections for now
        # Can be restricted later based on requirements
        return None
    
    try:
        from ..core.auth import AuthManager
        payload = AuthManager.verify_token(token)
        return {"user_id": payload.get("sub")}
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        return None


@router.websocket("/ws/progress/{lesson_id}")
async def websocket_progress_endpoint(
    websocket: WebSocket,
    lesson_id: str,
    token: Optional[str] = Query(None),
    ws_manager: ConnectionManager = Depends(get_ws_manager)
):
    """
    WebSocket endpoint for receiving real-time progress updates
    
    Args:
        lesson_id: Lesson ID to subscribe to
        token: Optional JWT token for authentication
        
    Example usage from JavaScript:
        const ws = new WebSocket(`ws://localhost:8000/api/ws/progress/${lessonId}?token=${authToken}`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Progress:', data);
            
            switch(data.type) {
                case 'progress':
                    // Update progress bar: data.percent, data.message
                    break;
                case 'completion':
                    // Processing complete: data.success, data.result
                    break;
                case 'error':
                    // Error occurred: data.error_message
                    break;
                case 'slide_update':
                    // Individual slide update: data.slide_number, data.status
                    break;
            }
        };
    """
    # Authenticate user (optional)
    user = await get_current_user_from_token(token)
    
    # Connect WebSocket
    await ws_manager.connect(websocket, lesson_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "lesson_id": lesson_id,
            "message": "Connected to progress updates"
        })
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Receive messages from client (e.g., ping/pong for keepalive)
                data = await websocket.receive_text()
                
                # Handle client messages if needed
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for lesson {lesson_id}")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                break
    
    finally:
        # Clean up connection
        await ws_manager.disconnect(websocket)


@router.websocket("/ws/status")
async def websocket_status_endpoint(
    websocket: WebSocket,
    ws_manager: ConnectionManager = Depends(get_ws_manager)
):
    """
    WebSocket endpoint for server status and statistics
    
    Useful for monitoring and debugging
    """
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "type": "status",
            "total_connections": ws_manager.get_total_connections(),
            "active_lessons": len(ws_manager.active_connections)
        })
        
        # Wait for disconnect
        await websocket.receive_text()
        
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
