#!/usr/bin/env python3
"""
Comprehensive test of all Google AI APIs
"""
import os
import sys
import json
import requests
from pathlib import Path

# Configuration
GOOGLE_API_KEY = "AIzaSyDNEtewj8q9qGWELrR-KS0mwcMTr4TGjA0"
GCP_PROJECT_ID = "inspiring-keel-473421-j2"
SERVICE_ACCOUNT_PATH = "inspiring-keel-473421-j2-22cc51dfb336.json"

print("="*80)
print("Google AI APIs - Comprehensive Test")
print("="*80)

# Test 1: Gemini API (Direct with API Key)
print("\n" + "="*80)
print("TEST 1: Gemini API (generativelanguage.googleapis.com)")
print("="*80)

try:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GOOGLE_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": "Say hello in Russian"}]
        }]
    }
    
    print(f"Endpoint: {url[:80]}...")
    print("Making request...")
    
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if 'candidates' in data:
            text = data['candidates'][0]['content']['parts'][0]['text']
            print(f"✅ SUCCESS! Response: {text[:100]}")
        else:
            print(f"✅ Response received: {json.dumps(data, indent=2)[:200]}")
    elif response.status_code == 429:
        error_data = response.json()
        print(f"❌ QUOTA EXCEEDED: {error_data.get('error', {}).get('message', 'Rate limit')}")
        
        # Check quota details
        if 'error' in error_data:
            error = error_data['error']
            print(f"\nError Details:")
            print(f"  Status: {error.get('status', 'N/A')}")
            print(f"  Message: {error.get('message', 'N/A')}")
            
            if 'details' in error:
                for detail in error['details']:
                    print(f"  Reason: {detail.get('reason', 'N/A')}")
                    print(f"  Domain: {detail.get('domain', 'N/A')}")
    elif response.status_code == 403:
        print(f"❌ FORBIDDEN: API key may be invalid or restricted")
        print(f"   Response: {response.text[:200]}")
    else:
        print(f"❌ ERROR {response.status_code}: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: Try different Gemini models
print("\n" + "="*80)
print("TEST 2: Try Different Gemini Models")
print("="*80)

models_to_try = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-pro",
    "gemini-2.0-flash-exp",
]

for model in models_to_try:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GOOGLE_API_KEY}"
        payload = {"contents": [{"parts": [{"text": "Hi"}]}]}
        
        print(f"\nTrying {model}...", end=" ")
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Available")
        elif response.status_code == 429:
            print("⚠️ Quota exceeded")
        elif response.status_code == 404:
            print("❌ Not found")
        else:
            print(f"❌ Error {response.status_code}")
            
    except Exception as e:
        print(f"❌ {str(e)[:50]}")

# Test 3: Check API Key quota status
print("\n" + "="*80)
print("TEST 3: Check API Key Details")
print("="*80)

try:
    # List available models
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GOOGLE_API_KEY}"
    
    print("Fetching available models...")
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])
        print(f"✅ API Key valid! Found {len(models)} models:")
        
        # Show vision-capable models
        vision_models = [m for m in models if 'vision' in m.get('displayName', '').lower() or 
                        'generateContent' in m.get('supportedGenerationMethods', [])]
        
        if vision_models:
            print(f"\n🔎 Vision-capable models:")
            for model in vision_models[:5]:
                print(f"  - {model.get('displayName', model.get('name', 'N/A'))}")
        
        # Show flash models  
        flash_models = [m for m in models if 'flash' in m.get('name', '').lower()]
        if flash_models:
            print(f"\n⚡ Flash models:")
            for model in flash_models[:5]:
                print(f"  - {model.get('name', 'N/A').split('/')[-1]}")
                
    elif response.status_code == 429:
        print(f"⚠️ Rate limited even for listing models")
    else:
        print(f"❌ Error {response.status_code}")
        
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 4: Vertex AI with Service Account
print("\n" + "="*80)
print("TEST 4: Vertex AI (with Service Account)")
print("="*80)

try:
    # Check if service account file exists
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print(f"❌ Service account file not found: {SERVICE_ACCOUNT_PATH}")
    else:
        print(f"✅ Service account file found")
        
        # Try to import google-auth
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
            
            print("✅ google-auth library available")
            
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            print("✅ Credentials loaded")
            
            # Get access token
            credentials.refresh(Request())
            access_token = credentials.token
            
            print(f"✅ Access token obtained: {access_token[:20]}...")
            
            # Try Vertex AI endpoint
            location = "us-central1"
            endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{GCP_PROJECT_ID}/locations/{location}/publishers/google/models/gemini-2.0-flash-exp:generateContent"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": "Say hello in Russian"}]
                }]
            }
            
            print(f"\nTrying Vertex AI endpoint...")
            print(f"Location: {location}")
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data:
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    print(f"✅ VERTEX AI SUCCESS! Response: {text[:100]}")
                else:
                    print(f"✅ Response: {json.dumps(data, indent=2)[:200]}")
            else:
                print(f"❌ Error: {response.text[:300]}")
                
        except ImportError:
            print("❌ google-auth library not installed")
            print("   Install: pip install google-auth")
            
except Exception as e:
    print(f"❌ Exception: {e}")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print("\nAvailable Options:")
print("1. Gemini API Key: Check if quota renewed")
print("2. Vertex AI: Requires google-auth library")
print("3. OpenRouter (current): Free Gemma-3-12b model")

print("\nRecommendations:")
print("- If Gemini quota OK → Use Gemini (best quality, free)")
print("- If Vertex AI works → Use Vertex (enterprise, reliable)")
print("- Otherwise → Keep OpenRouter Gemma-3 (free, good quality)")

print("\n" + "="*80)
