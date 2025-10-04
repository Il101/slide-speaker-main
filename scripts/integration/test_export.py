#!/usr/bin/env python3
"""Test video export functionality"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

# First login to get token
print("Logging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "admin@example.com", "password": "admin123"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print(f"Got token: {token[:20]}...")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Use a known completed lesson ID
lesson_id = "a9695704-9aa9-4809-a9bd-c2cb47abb963"
print(f"\nUsing lesson: {lesson_id}")

# Start export
print(f"\nStarting video export for lesson {lesson_id}...")
export_response = requests.post(
    f"{BASE_URL}/lessons/{lesson_id}/export",
    headers=headers
)

if export_response.status_code != 200:
    print(f"Export failed: {export_response.status_code}")
    print(export_response.text)
    exit(1)

export_data = export_response.json()
print(f"Export started!")
print(f"Job ID: {export_data.get('job_id')}")
print(f"Status: {export_data.get('status')}")

# Poll for status
job_id = export_data.get('job_id')
if job_id:
    print(f"\nPolling export status...")
    for i in range(30):  # Poll for up to 30 iterations
        time.sleep(2)
        status_response = requests.get(
            f"{BASE_URL}/lessons/{lesson_id}/export/status",
            headers=headers,
            params={"job_id": job_id}
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"[{i+1}] Status: {status_data.get('status')}, Progress: {status_data.get('progress', 0)}%, Stage: {status_data.get('stage', 'unknown')}")
            
            if status_data.get('status') in ['completed', 'success']:
                print(f"\n✅ Export completed!")
                if 'download_url' in status_data:
                    print(f"Download URL: {status_data['download_url']}")
                break
            elif status_data.get('status') == 'failure':
                print(f"\n❌ Export failed: {status_data.get('error', 'Unknown error')}")
                break
        else:
            print(f"Failed to get status: {status_response.status_code}")
            break
    else:
        print("\nTimeout waiting for export to complete")
