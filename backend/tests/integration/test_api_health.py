"""
Integration tests for Health API endpoints
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    async def test_health_check_basic(self, test_client):
        """Test basic health check endpoint"""
        response = await test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "slide-speaker-api"
    
    async def test_health_ready(self, test_client):
        """Test readiness health check"""
        response = await test_client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ready", "healthy"]
    
    async def test_health_detailed(self, test_client):
        """Test detailed health check with database"""
        response = await test_client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["service"] == "slide-speaker-api"
        assert "checks" in data
        assert "timestamp" in data
    
    async def test_root_endpoint(self, test_client):
        """Test root endpoint returns API info"""
        response = await test_client.get("/")
        
        # Root may redirect or return API info
        assert response.status_code in [200, 307, 404]
        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "name" in data or "status" in data
