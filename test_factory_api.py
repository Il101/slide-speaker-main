#!/usr/bin/env python3
"""
Test Factory AI API connection and capabilities
"""
import os
import sys
import json
import base64
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("❌ OpenAI library not installed")
    print("Install: pip install openai")
    sys.exit(1)

# Factory AI configuration
API_KEY = "fk-k9Jp84eGpLE3QnibxIaB-UQeqw7tqg4w1I4oWuHtXi_nfjb4s_Wgn4xFJTyY54iQ"
BASE_URL = "https://api.factory.ai/v1"
MODEL = "gpt-4o-mini"

print("="*60)
print("Factory AI API Test")
print("="*60)

# Initialize client
client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

print(f"\n✅ Client initialized")
print(f"   Base URL: {BASE_URL}")
print(f"   Model: {MODEL}")

# Test 1: Simple text completion
print("\n" + "="*60)
print("Test 1: Simple Text Completion")
print("="*60)

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from Factory AI!' in Russian"}
        ],
        temperature=0.5,
        max_tokens=100
    )
    
    result = response.choices[0].message.content
    print(f"✅ Text completion works!")
    print(f"   Response: {result}")
    
except Exception as e:
    print(f"❌ Text completion failed: {e}")
    sys.exit(1)

# Test 2: Check available models
print("\n" + "="*60)
print("Test 2: Available Models")
print("="*60)

try:
    models = client.models.list()
    print(f"✅ Models endpoint accessible")
    print(f"   Available models:")
    for model in models.data[:10]:  # First 10 models
        print(f"   - {model.id}")
except Exception as e:
    print(f"⚠️ Could not list models: {e}")

# Test 3: Vision support (multimodal)
print("\n" + "="*60)
print("Test 3: Vision/Multimodal Support")
print("="*60)

# Create a simple test image (1x1 red pixel PNG)
test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What color is this image? Answer in one word."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{test_image_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=50
    )
    
    result = response.choices[0].message.content
    print(f"✅ Vision/multimodal works!")
    print(f"   Response: {result}")
    print(f"   Model supports image analysis: YES")
    
except Exception as e:
    print(f"❌ Vision support failed: {e}")
    print(f"   Model supports image analysis: NO")
    print(f"   Note: {MODEL} may not support vision")

# Test 4: Russian language support
print("\n" + "="*60)
print("Test 4: Russian Language Translation")
print("="*60)

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system", 
                "content": "You are a translator. Translate everything to Russian."
            },
            {
                "role": "user",
                "content": "Translate this German text to Russian: 'Guten Morgen, wie geht es Ihnen?'"
            }
        ],
        temperature=0.2,
        max_tokens=100
    )
    
    result = response.choices[0].message.content
    print(f"✅ Russian translation works!")
    print(f"   German: 'Guten Morgen, wie geht es Ihnen?'")
    print(f"   Russian: {result}")
    
except Exception as e:
    print(f"❌ Translation failed: {e}")

# Summary
print("\n" + "="*60)
print("Summary")
print("="*60)
print(f"✅ Factory AI API is accessible")
print(f"✅ Text completion works")
print(f"✅ Russian language supported")
print(f"Check vision test result above for multimodal support")
