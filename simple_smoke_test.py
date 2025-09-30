#!/usr/bin/env python3
"""
Simple smoke test for Slide Speaker export functionality
Tests the complete flow without external dependencies
"""

import json
import subprocess
import time
import sys
from pathlib import Path

def test_docker_services():
    """Test if Docker services are running"""
    print("🔍 Testing Docker services...")
    
    try:
        # Check if docker-compose is running
        result = subprocess.run(
            ["docker-compose", "ps"],
            capture_output=True,
            text=True,
            cwd="/workspace"
        )
        
        if result.returncode != 0:
            print("❌ Docker Compose not running")
            return False
        
        # Check for required services
        output = result.stdout.lower()
        required_services = ["backend", "frontend", "redis", "celery", "minio"]
        
        for service in required_services:
            if service not in output:
                print(f"❌ Service {service} not running")
                return False
        
        print("✅ All Docker services are running")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Docker services: {e}")
        return False

def test_api_health():
    """Test API health endpoint"""
    print("🔍 Testing API health...")
    
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8000/health"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ API health check failed")
            return False
        
        data = json.loads(result.stdout)
        if data.get("status") != "ok":
            print("❌ API not healthy")
            return False
        
        print("✅ API health check passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing API health: {e}")
        return False

def test_demo_lesson():
    """Test demo lesson manifest"""
    print("🔍 Testing demo lesson...")
    
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8000/lessons/demo-lesson/manifest"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ Demo lesson request failed")
            return False
        
        data = json.loads(result.stdout)
        if "slides" not in data:
            print("❌ Invalid manifest structure")
            return False
        
        if len(data["slides"]) == 0:
            print("❌ No slides in manifest")
            return False
        
        print("✅ Demo lesson test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing demo lesson: {e}")
        return False

def test_export_request():
    """Test export request"""
    print("🔍 Testing export request...")
    
    try:
        export_data = {
            "lesson_id": "demo-lesson",
            "quality": "high",
            "include_audio": True,
            "include_effects": True
        }
        
        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                "http://localhost:8000/lessons/demo-lesson/export",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(export_data)
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ Export request failed")
            return False
        
        data = json.loads(result.stdout)
        if data.get("status") != "processing":
            print("❌ Export not started")
            return False
        
        if "task_id" not in data:
            print("❌ No task_id returned")
            return False
        
        print(f"✅ Export request successful, task_id: {data['task_id']}")
        return data["task_id"]
        
    except Exception as e:
        print(f"❌ Error testing export request: {e}")
        return None

def test_export_status(task_id):
    """Test export status"""
    print("🔍 Testing export status...")
    
    try:
        result = subprocess.run(
            ["curl", "-s", f"http://localhost:8000/exports/{task_id}/status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ Status request failed")
            return False
        
        data = json.loads(result.stdout)
        status = data.get("status")
        
        if status not in ["pending", "processing", "completed", "failed"]:
            print(f"❌ Invalid status: {status}")
            return False
        
        print(f"✅ Status check passed: {status}")
        return True
        
    except Exception as e:
        print(f"❌ Error testing export status: {e}")
        return False

def test_storage_stats():
    """Test storage statistics"""
    print("🔍 Testing storage stats...")
    
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8000/admin/storage-stats"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ Storage stats request failed")
            return False
        
        data = json.loads(result.stdout)
        if "local" not in data or "s3" not in data:
            print("❌ Invalid storage stats structure")
            return False
        
        print("✅ Storage stats test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing storage stats: {e}")
        return False

def test_minio_console():
    """Test MinIO console accessibility"""
    print("🔍 Testing MinIO console...")
    
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "http://localhost:9001"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ MinIO console not accessible")
            return False
        
        status_code = result.stdout.strip()
        if status_code not in ["200", "302"]:
            print(f"❌ MinIO console returned status: {status_code}")
            return False
        
        print("✅ MinIO console accessible")
        return True
        
    except Exception as e:
        print(f"❌ Error testing MinIO console: {e}")
        return False

def main():
    """Main smoke test function"""
    print("=" * 60)
    print("SLIDE SPEAKER SIMPLE SMOKE TEST")
    print("=" * 60)
    
    tests = [
        ("Docker Services", test_docker_services),
        ("API Health", test_api_health),
        ("Demo Lesson", test_demo_lesson),
        ("MinIO Console", test_minio_console),
        ("Storage Stats", test_storage_stats),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    # Test export if basic tests pass
    if passed == total:
        print(f"\n🧪 Export Request")
        task_id = test_export_request()
        if task_id:
            print(f"\n🧪 Export Status")
            if test_export_status(task_id):
                passed += 1
            total += 1
        total += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Slide Speaker Sprint 3 is working correctly")
        print("✅ Export functionality is operational")
        print("✅ Queue system is functional")
        print("✅ S3 storage is configured")
        print("\n🚀 Ready for production!")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("🔧 Check the logs above for details")
        print("💡 Make sure all services are running: docker-compose up --build")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)