"""CSRF Protection middleware for FastAPI"""
import os
import secrets
import hashlib
from typing import Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class CSRFProtection:
    """CSRF Protection using Double Submit Cookie pattern"""
    
    def __init__(self, secret_key: str, cookie_name: str = "csrf_token", header_name: str = "X-CSRF-Token"):
        self.secret_key = secret_key
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.token_length = 32
    
    def generate_token(self) -> str:
        """Generate a random CSRF token"""
        return secrets.token_urlsafe(self.token_length)
    
    def verify_token(self, cookie_token: str, header_token: str) -> bool:
        """Verify that cookie and header tokens match"""
        if not cookie_token or not header_token:
            return False
        return secrets.compare_digest(cookie_token, header_token)
    
    def set_csrf_cookie(self, response: Response, token: str) -> None:
        """Set CSRF token in cookie"""
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            httponly=False,  # Must be accessible to JavaScript
            secure=True,      # Only over HTTPS in production
            samesite="strict", # Prevent CSRF attacks
            max_age=3600     # 1 hour
        )
    
    async def __call__(self, request: Request, call_next):
        """CSRF middleware implementation"""
        
        # Skip CSRF check for safe methods and certain endpoints
        if self._should_skip_csrf_check(request):
            response = await call_next(request)
            return response
        
        # Get CSRF token from cookie
        cookie_token = request.cookies.get(self.cookie_name)
        
        # Get CSRF token from header
        header_token = request.headers.get(self.header_name)
        
        # For GET requests, just set the token if it doesn't exist
        if request.method == "GET":
            response = await call_next(request)
            if not cookie_token:
                new_token = self.generate_token()
                self.set_csrf_cookie(response, new_token)
            return response
        
        # For state-changing methods, verify CSRF token
        if not self.verify_token(cookie_token, header_token):
            logger.warning(f"CSRF token verification failed for {request.method} {request.url}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token verification failed"}
            )
        
        # Token is valid, proceed with request
        response = await call_next(request)
        
        # Set new token for subsequent requests
        new_token = self.generate_token()
        self.set_csrf_cookie(response, new_token)
        
        return response
    
    def _should_skip_csrf_check(self, request: Request) -> bool:
        """Determine if CSRF check should be skipped"""
        
        # Skip for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        
        # Skip for health check endpoints
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return True
        
        # Skip for authentication endpoints (they have their own protection)
        if request.url.path.startswith("/auth/"):
            return True
        
        # Skip for static files
        if request.url.path.startswith("/static/"):
            return True
        
        return False

# Global CSRF instance
CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY")
if not CSRF_SECRET_KEY or CSRF_SECRET_KEY == "your-csrf-secret-key-change-in-production":
    raise ValueError(
        "CSRF_SECRET_KEY must be set in .env and cannot be default value. "
        "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )

csrf_protection = CSRFProtection(
    secret_key=CSRF_SECRET_KEY,
    cookie_name="csrf_token",
    header_name="X-CSRF-Token"
)
