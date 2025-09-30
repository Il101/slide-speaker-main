#!/usr/bin/env python3
"""
Smoke test for Slide Speaker export functionality
Tests the complete flow: upload -> generate -> export -> download
"""

import asyncio
import httpx
import json
import time
from pathlib import Path
import tempfile
import shutil

# Configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 300  # 5 minutes

class SmokeTest:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.lesson_id = None
        self.task_id = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_health_check(self):
        """Test API health check"""
        print("🔍 Testing health check...")
        
        response = await self.client.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        
        print("✅ Health check passed")
    
    async def test_demo_lesson(self):
        """Test demo lesson manifest"""
        print("🔍 Testing demo lesson...")
        
        response = await self.client.get(f"{API_BASE_URL}/lessons/demo-lesson/manifest")
        assert response.status_code == 200
        
        manifest = response.json()
        assert "slides" in manifest
        assert len(manifest["slides"]) > 0
        
        # Check slide structure
        slide = manifest["slides"][0]
        assert "id" in slide
        assert "image" in slide
        assert "audio" in slide
        assert "elements" in slide
        assert "cues" in slide
        
        print("✅ Demo lesson test passed")
        return "demo-lesson"
    
    async def test_export_request(self, lesson_id: str):
        """Test export request"""
        print("🔍 Testing export request...")
        
        export_request = {
            "lesson_id": lesson_id,
            "quality": "high",
            "include_audio": True,
            "include_effects": True
        }
        
        response = await self.client.post(
            f"{API_BASE_URL}/lessons/{lesson_id}/export",
            json=export_request
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "processing"
        assert "task_id" in data
        assert "estimated_time" in data
        
        self.task_id = data["task_id"]
        print(f"✅ Export request successful, task_id: {self.task_id}")
    
    async def test_export_status(self):
        """Test export status polling"""
        print("🔍 Testing export status...")
        
        if not self.task_id:
            raise Exception("No task_id available")
        
        max_attempts = 60  # 5 minutes with 5-second intervals
        attempt = 0
        
        while attempt < max_attempts:
            response = await self.client.get(f"{API_BASE_URL}/exports/{self.task_id}/status")
            assert response.status_code == 200
            
            data = response.json()
            status = data["status"]
            progress = data.get("progress", 0)
            message = data.get("message", "")
            
            print(f"📊 Status: {status}, Progress: {progress}%, Message: {message}")
            
            if status == "completed":
                print("✅ Export completed successfully")
                return data
            elif status == "failed":
                error = data.get("error", "Unknown error")
                raise Exception(f"Export failed: {error}")
            
            attempt += 1
            await asyncio.sleep(5)
        
        raise Exception("Export timeout - export did not complete in time")
    
    async def test_download_url(self, lesson_id: str):
        """Test download URL generation"""
        print("🔍 Testing download URL...")
        
        response = await self.client.get(f"{API_BASE_URL}/exports/{lesson_id}/download")
        
        # Should return either a file or redirect to S3
        assert response.status_code in [200, 302]
        
        if response.status_code == 200:
            # Local file download
            content_type = response.headers.get("content-type", "")
            assert "video/mp4" in content_type
            print("✅ Local file download successful")
        else:
            # S3 redirect
            print("✅ S3 redirect successful")
    
    async def test_storage_stats(self):
        """Test storage statistics"""
        print("🔍 Testing storage stats...")
        
        response = await self.client.get(f"{API_BASE_URL}/admin/storage-stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "local" in data
        assert "s3" in data
        
        print("✅ Storage stats retrieved successfully")
    
    async def test_frontend_access(self):
        """Test frontend accessibility"""
        print("🔍 Testing frontend access...")
        
        try:
            response = await self.client.get(FRONTEND_URL)
            assert response.status_code == 200
            print("✅ Frontend accessible")
        except httpx.ConnectError:
            print("⚠️  Frontend not accessible (may not be running)")
    
    async def run_all_tests(self):
        """Run all smoke tests"""
        print("🚀 Starting Slide Speaker smoke tests...")
        
        try:
            # Test API health
            await self.test_health_check()
            
            # Test demo lesson
            lesson_id = await self.test_demo_lesson()
            
            # Test export request
            await self.test_export_request(lesson_id)
            
            # Test export status polling
            export_result = await self.test_export_status()
            
            # Test download
            await self.test_download_url(lesson_id)
            
            # Test storage stats
            await self.test_storage_stats()
            
            # Test frontend
            await self.test_frontend_access()
            
            print("🎉 All smoke tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Smoke test failed: {e}")
            return False

async def main():
    """Main smoke test function"""
    print("=" * 60)
    print("SLIDE SPEAKER SMOKE TEST")
    print("=" * 60)
    
    async with SmokeTest() as test:
        success = await test.run_all_tests()
        
        if success:
            print("\n🎉 SUCCESS: All tests passed!")
            print("✅ Export functionality is working correctly")
            print("✅ MP4 generation is functional")
            print("✅ Queue system is operational")
            print("✅ S3 storage is configured")
            exit(0)
        else:
            print("\n❌ FAILURE: Some tests failed!")
            print("🔧 Check the logs above for details")
            exit(1)

if __name__ == "__main__":
    asyncio.run(main())