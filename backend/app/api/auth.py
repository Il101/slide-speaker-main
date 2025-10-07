"""Authentication API endpoints"""
import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..core.auth import AuthManager, authenticate_user, get_current_user
from ..core.database import get_db, User
from ..core.logging import get_logger
from ..core.validators import validate_password_strength

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# Request/Response models
class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    username: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    username: Optional[str]
    role: str
    is_active: bool


@router.post("/login", response_model=TokenResponse)
async def login(
    request_data: LoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint to get JWT access token
    
    ✅ Security features:
    - Rate limited to 5 attempts/minute (via main.py limiter)
    - 500ms delay to prevent timing attacks
    - Failed attempts logged with IP and user-agent
    """
    
    # Add delay to prevent timing attacks
    await asyncio.sleep(0.5)  # 500ms delay
    
    user = await authenticate_user(request_data.email, request_data.password, db)

    if not user:
        # Log failed login attempt
        logger.warning(
            f"Failed login attempt for {request_data.email}",
            extra={
                "email": request_data.email,
                "ip": http_request.client.host if http_request.client else "unknown",
                "user_agent": http_request.headers.get("user-agent", "unknown")
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = AuthManager.create_access_token(
        data={"sub": user["user_id"], "email": user["email"], "role": user["role"]}
    )

    # Log successful login
    logger.info(
        f"User logged in: {user['email']}",
        extra={
            "email": user['email'],
            "ip": http_request.client.host if http_request.client else "unknown"
        }
    )

    return TokenResponse(access_token=access_token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    
    ✅ Security features:
    - Rate limited to 3 registrations/minute (via main.py limiter)
    - Password strength validation (8+ chars, uppercase, lowercase, digit, special char)
    - Username must be unique
    """
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = AuthManager.get_password_hash(request.password)
    new_user = User(
        id=str(uuid.uuid4()),  # Generate UUID for new user
        email=request.email,
        username=request.username or request.email.split("@")[0],
        hashed_password=hashed_password,
        role="user",
        is_active=True
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info(f"New user registered: {new_user.email}")

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        role=new_user.role,
        is_active=new_user.is_active
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: dict = Depends(get_current_user)
):
    """Refresh access token"""
    access_token = AuthManager.create_access_token(
        data={"sub": current_user["user_id"], "email": current_user["email"], "role": current_user["role"]}
    )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information"""
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username or user.email.split("@")[0],  # Use username or email prefix
        role=user.role,
        is_active=user.is_active
    )
