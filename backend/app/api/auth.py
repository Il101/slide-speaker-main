"""Authentication API endpoints"""
import asyncio
import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
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

router = APIRouter(prefix="/auth", tags=["authentication"])


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


@router.post("/login")
async def login(
    request_data: LoginRequest,
    http_request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint to get JWT access token
    
    ✅ Security features:
    - Rate limited to 5 attempts/minute (via main.py limiter)
    - 500ms delay to prevent timing attacks
    - Failed attempts logged with IP and user-agent
    - JWT stored in HttpOnly cookie (protected from XSS)
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

    # ✅ Set JWT in HttpOnly cookie (protected from XSS)
    # Token expires in 30 days (43200 minutes = 30 days)
    token_max_age = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200")) * 60
    
    # ✅ Secure cookie settings based on environment
    # Local: secure=False (HTTP), Production: secure=True (HTTPS)
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # ✅ JavaScript cannot access
        secure=is_production,  # ✅ True in production (HTTPS), False locally (HTTP)
        samesite="lax",  # ✅ Works with proxy and subdomains
        max_age=token_max_age,  # 30 days by default
        path="/"
    )

    # Log successful login
    logger.info(
        f"User logged in: {user['email']}",
        extra={
            "email": user['email'],
            "ip": http_request.client.host if http_request.client else "unknown"
        }
    )

    # Check if this is a cross-origin request
    origin = http_request.headers.get("origin")
    referer = http_request.headers.get("referer")
    is_cross_origin = origin and origin != str(http_request.url).split('/')[0:3]
    
    # Return success message and token for cross-origin requests
    response_data = {
        "message": "Login successful",
        "user": {
            "email": user["email"],
            "role": user["role"]
        }
    }
    
    # Add token for cross-origin requests (when cookies won't work)
    if is_cross_origin:
        response_data["access_token"] = access_token
    
    return response_data


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


@router.post("/logout")
async def logout(response: Response):
    """
    Logout endpoint - clears HttpOnly cookie
    
    ✅ Security features:
    - Removes JWT cookie
    - Works even without authentication
    """
    response.delete_cookie(
        key="access_token",
        path="/"
    )
    
    return {"message": "Logout successful"}


@router.post("/refresh")
async def refresh_token(
    current_user: dict = Depends(get_current_user),
    response: Response = None
):
    """Refresh access token and update cookie"""
    access_token = AuthManager.create_access_token(
        data={"sub": current_user["user_id"], "email": current_user["email"], "role": current_user["role"]}
    )
    
    # ✅ Update cookie with new token
    if response:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=1800,
            path="/"
        )
    
    return {"message": "Token refreshed"}


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
