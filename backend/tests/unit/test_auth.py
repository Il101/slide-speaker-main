"""
Unit tests for Authentication Module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException
import jwt
import uuid

from app.core.auth import AuthManager, authenticate_user, require_admin, get_current_user, get_current_user_optional
from app.core.database import User


class TestAuthManager:
    """Test AuthManager class"""
    
    def test_get_password_hash(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = AuthManager.get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$pbkdf2-sha256$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = AuthManager.get_password_hash(password)
        
        assert AuthManager.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = AuthManager.get_password_hash(password)
        
        assert AuthManager.verify_password(wrong_password, hashed) is False
    
    def test_create_access_token_default_expiry(self):
        """Test JWT token creation with default expiry"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = AuthManager.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify payload
        from app.core.auth import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload
    
    def test_create_access_token_custom_expiry(self):
        """Test JWT token creation with custom expiry"""
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)  # 1 hour
        token = AuthManager.create_access_token(data, expires_delta)
        
        assert token is not None
        
        # Verify token has expiry and can be decoded
        from app.core.auth import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload
        assert payload["sub"] == "user123"
        
        # Verify expiry is in the future
        now_timestamp = datetime.utcnow().timestamp()
        assert payload["exp"] > now_timestamp
    
    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = AuthManager.create_access_token(data)
        
        payload = AuthManager.verify_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
    
    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        data = {"sub": "user123"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = AuthManager.create_access_token(data, expires_delta)
        
        with pytest.raises(HTTPException) as exc_info:
            AuthManager.verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(HTTPException) as exc_info:
            AuthManager.verify_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "credentials" in exc_info.value.detail.lower()
    
    def test_verify_token_tampered(self):
        """Test token verification with tampered token"""
        data = {"sub": "user123"}
        token = AuthManager.create_access_token(data)
        
        # Tamper with token
        tampered_token = token[:-10] + "tampered12"
        
        with pytest.raises(HTTPException) as exc_info:
            AuthManager.verify_token(tampered_token)
        
        assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    """Test get_current_user dependency"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_cookie(self, mock_db_session):
        """Test getting user from cookie token"""
        user_id = str(uuid.uuid4())
        
        # Create valid token
        token = AuthManager.create_access_token({"sub": user_id, "email": "test@example.com"})
        
        # Mock request with cookie
        mock_request = Mock()
        mock_request.cookies.get.return_value = token
        
        # Mock user in database
        mock_user = User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role="user",
            is_active=True
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Call get_current_user
        user_data = await get_current_user(mock_request, mock_db_session, None)
        
        assert user_data["user_id"] == user_id
        assert user_data["email"] == "test@example.com"
        assert user_data["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_header(self, mock_db_session):
        """Test getting user from Authorization header"""
        user_id = str(uuid.uuid4())
        
        # Create valid token
        token = AuthManager.create_access_token({"sub": user_id, "email": "test@example.com"})
        
        # Mock request without cookie
        mock_request = Mock()
        mock_request.cookies.get.return_value = None
        
        # Mock credentials from header
        mock_credentials = Mock()
        mock_credentials.credentials = token
        
        # Mock user in database
        mock_user = User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role="user",
            is_active=True
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Call get_current_user
        user_data = await get_current_user(mock_request, mock_db_session, mock_credentials)
        
        assert user_data["user_id"] == user_id
        assert user_data["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, mock_db_session):
        """Test getting user without token"""
        mock_request = Mock()
        mock_request.cookies.get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_db_session, None)
        
        assert exc_info.value.status_code == 401
        assert "authenticated" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self, mock_db_session):
        """Test getting inactive user"""
        user_id = str(uuid.uuid4())
        token = AuthManager.create_access_token({"sub": user_id})
        
        mock_request = Mock()
        mock_request.cookies.get.return_value = token
        
        # Mock inactive user
        mock_user = User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role="user",
            is_active=False  # Inactive!
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_db_session, None)
        
        assert exc_info.value.status_code == 401
        assert "inactive" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_db_session):
        """Test getting non-existent user"""
        user_id = str(uuid.uuid4())
        token = AuthManager.create_access_token({"sub": user_id})
        
        mock_request = Mock()
        mock_request.cookies.get.return_value = token
        
        # Mock user not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_db_session, None)
        
        assert exc_info.value.status_code == 401
        assert "not found" in exc_info.value.detail.lower()


class TestGetCurrentUserOptional:
    """Test get_current_user_optional dependency"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_token(self, mock_db_session):
        """Test optional user with valid token"""
        user_id = str(uuid.uuid4())
        token = AuthManager.create_access_token({"sub": user_id, "email": "test@example.com"})
        
        mock_request = Mock()
        mock_request.cookies.get.return_value = token
        
        mock_user = User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role="user",
            is_active=True
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        user_data = await get_current_user_optional(mock_request, mock_db_session, None)
        
        assert user_data is not None
        assert user_data["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_get_current_user_optional_without_token(self, mock_db_session):
        """Test optional user without token"""
        mock_request = Mock()
        mock_request.cookies.get.return_value = None
        
        user_data = await get_current_user_optional(mock_request, mock_db_session, None)
        
        assert user_data is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_optional_invalid_token(self, mock_db_session):
        """Test optional user with invalid token"""
        mock_request = Mock()
        mock_request.cookies.get.return_value = "invalid.token"
        
        # Should return None instead of raising exception
        user_data = await get_current_user_optional(mock_request, mock_db_session, None)
        
        assert user_data is None


class TestAuthenticateUser:
    """Test authenticate_user function"""
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mock_db_session):
        """Test successful user authentication"""
        email = "test@example.com"
        password = "test_password_123"
        hashed = AuthManager.get_password_hash(password)
        
        mock_user = User(
            id=str(uuid.uuid4()),
            email=email,
            username="testuser",
            hashed_password=hashed,
            role="user",
            is_active=True
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        user_data = await authenticate_user(email, password, mock_db_session)
        
        assert user_data is not None
        assert user_data["email"] == email
        assert user_data["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, mock_db_session):
        """Test authentication with wrong password"""
        email = "test@example.com"
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed = AuthManager.get_password_hash(correct_password)
        
        mock_user = User(
            id=str(uuid.uuid4()),
            email=email,
            username="testuser",
            hashed_password=hashed,
            role="user",
            is_active=True
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        user_data = await authenticate_user(email, wrong_password, mock_db_session)
        
        assert user_data is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, mock_db_session):
        """Test authentication with non-existent user"""
        email = "nonexistent@example.com"
        password = "any_password"
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        user_data = await authenticate_user(email, password, mock_db_session)
        
        assert user_data is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, mock_db_session):
        """Test authentication with inactive user"""
        email = "test@example.com"
        password = "test_password"
        hashed = AuthManager.get_password_hash(password)
        
        mock_user = User(
            id=str(uuid.uuid4()),
            email=email,
            username="testuser",
            hashed_password=hashed,
            role="user",
            is_active=False  # Inactive!
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        user_data = await authenticate_user(email, password, mock_db_session)
        
        assert user_data is None


class TestRequireAdmin:
    """Test require_admin dependency"""
    
    @pytest.mark.asyncio
    async def test_require_admin_success(self):
        """Test require_admin with admin user"""
        admin_user = {
            "user_id": str(uuid.uuid4()),
            "email": "admin@example.com",
            "role": "admin"
        }
        
        result = await require_admin(admin_user)
        
        assert result == admin_user
    
    @pytest.mark.asyncio
    async def test_require_admin_forbidden(self):
        """Test require_admin with non-admin user"""
        regular_user = {
            "user_id": str(uuid.uuid4()),
            "email": "user@example.com",
            "role": "user"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(regular_user)
        
        assert exc_info.value.status_code == 403
        assert "admin" in exc_info.value.detail.lower()
