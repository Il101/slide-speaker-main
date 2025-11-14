#!/usr/bin/env python3
"""Test both Gemini and Factory AI keys"""
import sys

print("="*60)
print("API Keys Test")
print("="*60)

# Test 1: Google Gemini
print("\n1. Testing Google Gemini...")
try:
    import google.generativeai as genai
    
    gemini_key = "AIzaSyDNEtewj8q9qGWELrR-KS0mwcMTr4TGjA0"
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    response = model.generate_content("Say hello in Russian. One sentence only.")
    print(f"✅ Gemini works!")
    print(f"   Response: {response.text}")
    
except Exception as e:
    print(f"❌ Gemini failed: {e}")
    if "quota" in str(e).lower():
        print("   ⚠️ QUOTA EXCEEDED!")
    elif "api key not valid" in str(e).lower():
        print("   ⚠️ INVALID API KEY!")

# Test 2: Factory AI key (check if it's actually OpenRouter)
print("\n2. Testing Factory AI key...")
factory_key = "fk-k9Jp84eGpLE3QnibxIaB-UQeqw7tqg4w1I4oWuHtXi_nfjb4s_Wgn4xFJTyY54iQ"

print(f"   Key format: {factory_key[:10]}...")
print(f"   Key starts with 'fk-': {factory_key.startswith('fk-')}")

# Try as OpenAI-compatible (maybe it works?)
try:
    from openai import OpenAI
    
    # Try different base URLs
    base_urls = [
        "https://api.factory.ai/v1",
        "https://api.factory.ai/api/v1", 
        "https://factory.ai/api/v1"
    ]
    
    for base_url in base_urls:
        try:
            print(f"\n   Trying {base_url}...")
            client = OpenAI(
                base_url=base_url,
                api_key=factory_key,
                timeout=10.0
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=20
            )
            
            print(f"   ✅ Factory AI works with {base_url}!")
            print(f"   Response: {response.choices[0].message.content}")
            break
            
        except Exception as e:
            error_msg = str(e)
            if "Could not resolve host" in error_msg:
                print(f"   ❌ Host not reachable: {base_url}")
            elif "401" in error_msg or "authentication" in error_msg.lower():
                print(f"   ❌ Authentication failed")
            elif "404" in error_msg:
                print(f"   ❌ Endpoint not found")
            else:
                print(f"   ❌ Error: {error_msg[:100]}")
    
except ImportError:
    print("   ⚠️ OpenAI library not installed")
except Exception as e:
    print(f"   ❌ Factory AI test failed: {e}")

# Test 3: OpenRouter key (from backend/.env)
print("\n3. Testing OpenRouter key...")
openrouter_key = "your_openrouter_api_key_here"

try:
    from openai import OpenAI
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_key,
        timeout=10.0
    )
    
    response = client.chat.completions.create(
        model="google/gemini-2.0-flash-thinking-exp:free",
        messages=[{"role": "user", "content": "Say hello in Russian"}],
        max_tokens=50
    )
    
    print(f"✅ OpenRouter works!")
    print(f"   Response: {response.choices[0].message.content}")
    
except Exception as e:
    error_msg = str(e)
    if "429" in error_msg or "rate limit" in error_msg.lower():
        print(f"❌ OpenRouter: Rate limit exceeded")
        print(f"   Need to add credits or wait")
    elif "404" in error_msg:
        print(f"❌ OpenRouter: Model not found")
    else:
        print(f"❌ OpenRouter failed: {error_msg[:200]}")

print("\n" + "="*60)
print("Summary")
print("="*60)
