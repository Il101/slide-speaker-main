#!/usr/bin/env python3

import requests
import json

def test_api():
    base_url = "http://localhost:8001"
    
    # Тест health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Тест демо manifest
    try:
        response = requests.get(f"{base_url}/lessons/demo-lesson/manifest", timeout=5)
        print(f"Demo manifest: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Slides count: {len(data['slides'])}")
            print(f"First slide: {data['slides'][0]['id']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Demo manifest failed: {e}")

if __name__ == "__main__":
    test_api()