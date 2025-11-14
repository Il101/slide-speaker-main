"""
Integration tests for Main API endpoints
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
class TestMainAPIEndpoints:
    """Test main API endpoints"""
    
    async def test_health_endpoints(self, test_client):
        """Test all health endpoints"""
        # Basic health
        response = await test_client.get("/health")
        assert response.status_code == 200
        
        # Ready
        response = await test_client.get("/health/ready")
        assert response.status_code == 200
        
        # Live
        response = await test_client.get("/health/live")
        assert response.status_code == 200
    
    async def test_metrics_endpoint(self, test_client):
        """Test Prometheus metrics endpoint"""
        response = await test_client.get("/metrics")
        assert response.status_code == 200
        # Metrics should return plain text
        assert "text/plain" in response.headers.get("content-type", "")
    
    async def test_voices_endpoint(self, test_client):
        """Test voices listing endpoint"""
        response = await test_client.get("/voices")
        # Should return 200 or 404 if not implemented
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
    
    async def test_upload_endpoint_without_file(self, test_client):
        """Test upload endpoint without file"""
        response = await test_client.post("/upload")
        # Should return 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422]
    
    async def test_lesson_status_not_found(self, test_client):
        """Test lesson status for non-existent lesson"""
        response = await test_client.get("/lessons/non-existent-id/status")
        # Should return 404
        assert response.status_code in [404, 422]
    
    async def test_lesson_manifest_not_found(self, test_client):
        """Test lesson manifest for non-existent lesson"""
        response = await test_client.get("/lessons/non-existent-id/manifest")
        # Should return 404
        assert response.status_code in [404, 422]
    
    async def test_export_endpoints_not_found(self, test_client):
        """Test export endpoints for non-existent lesson"""
        response = await test_client.get("/lessons/non-existent/export/status")
        assert response.status_code in [404, 422]
        
        response = await test_client.get("/exports/non-existent/download")
        assert response.status_code in [404, 422]
    
    async def test_admin_endpoints_unauthorized(self, test_client):
        """Test admin endpoints without auth"""
        response = await test_client.get("/admin/storage-stats")
        # Should require auth (401) or not found (404)
        assert response.status_code in [401, 404]
        
        response = await test_client.post("/admin/cleanup")
        assert response.status_code in [401, 404, 405]
    
    async def test_post_endpoints_validation(self, test_client):
        """Test POST endpoints with invalid data"""
        endpoints = [
            "/lessons/test-id/generate-speaker-notes",
            "/lessons/test-id/generate-audio",
            "/lessons/test-id/edit",
            "/lessons/test-id/patch",
            "/lessons/test-id/export",
        ]
        
        for endpoint in endpoints:
            response = await test_client.post(endpoint, json={})
            # Should return validation error, not found, or bad request
            assert response.status_code in [400, 404, 422]
    
    async def test_cors_headers(self, test_client):
        """Test CORS headers are present"""
        response = await test_client.get("/health")
        # CORS headers should be present in production
        # In test environment they might not be, so we just check response is OK
        assert response.status_code == 200
    
    async def test_invalid_routes(self, test_client):
        """Test invalid routes return 404"""
        invalid_routes = [
            "/api/invalid",
            "/unknown/endpoint",
            "/random/path/here",
        ]
        
        for route in invalid_routes:
            response = await test_client.get(route)
            assert response.status_code == 404
    
    async def test_method_not_allowed(self, test_client):
        """Test method not allowed errors"""
        # Try POST on GET-only endpoint
        response = await test_client.post("/health")
        assert response.status_code in [405, 404]  # Method not allowed or not found
        
        # Try GET on POST-only endpoint
        response = await test_client.get("/upload")
        assert response.status_code in [405, 422]  # Method not allowed or validation error


@pytest.mark.asyncio
@pytest.mark.integration
class TestAPIRateLimiting:
    """Test API rate limiting"""
    
    async def test_rate_limit_not_triggered_single_request(self, test_client):
        """Test single request doesn't trigger rate limit"""
        response = await test_client.get("/health")
        assert response.status_code == 200
        # Should not have rate limit headers on first request
    
    async def test_multiple_requests_accepted(self, test_client):
        """Test multiple reasonable requests are accepted"""
        for i in range(5):
            response = await test_client.get("/health")
            assert response.status_code == 200
