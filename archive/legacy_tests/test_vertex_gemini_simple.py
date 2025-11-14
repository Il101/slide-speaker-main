"""
Test Vertex AI Gemini with different models and regions
"""
import os
import sys

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'keys/gcp-sa.json'

print("="*70)
print("🧪 TESTING VERTEX AI GEMINI - MULTIPLE OPTIONS")
print("="*70)

import vertexai
from vertexai.generative_models import GenerativeModel

project = 'inspiring-keel-473421-j2'

# Try different model names and locations
test_configs = [
    # (location, model_name)
    ('us-central1', 'gemini-1.5-flash'),
    ('us-central1', 'gemini-1.5-flash-001'),
    ('us-central1', 'gemini-pro'),
    ('europe-west1', 'gemini-1.5-flash'),
    ('us-east1', 'gemini-1.5-flash'),
]

for location, model_name in test_configs:
    print(f"\n{'='*70}")
    print(f"Testing: {model_name} in {location}")
    print(f"{'='*70}")
    
    try:
        # Initialize for this location
        vertexai.init(project=project, location=location)
        print(f"✅ Initialized: {location}")
        
        # Create model
        model = GenerativeModel(model_name)
        print(f"✅ Model created: {model_name}")
        
        # Test generation
        prompt = "Say 'Hello!' in one word."
        print(f"   Prompt: {prompt}")
        print("   Generating...")
        
        response = model.generate_content(prompt)
        
        print(f"\n   ✅✅✅ SUCCESS!")
        print(f"   Response: {response.text}")
        print(f"\n   🎉 WORKING CONFIG:")
        print(f"   Location: {location}")
        print(f"   Model: {model_name}")
        
        # If we got here, it works!
        print("\n" + "="*70)
        print("✅ VERTEX AI GEMINI WORKS!")
        print(f"Use: location='{location}', model='{model_name}'")
        print("="*70)
        sys.exit(0)
        
    except Exception as e:
        error_msg = str(e)
        if '404' in error_msg:
            print(f"   ❌ Model not found")
        elif '403' in error_msg:
            print(f"   ❌ Permission denied")
        elif '400' in error_msg:
            print(f"   ❌ Bad request")
        else:
            print(f"   ❌ Error: {error_msg[:100]}")

print("\n" + "="*70)
print("❌ NONE OF THE CONFIGS WORKED")
print("="*70)
print("\nPossible issues:")
print("1. Vertex AI API not fully activated")
print("2. Project doesn't have access to Gemini models")
print("3. Need to enable Generative AI features")
print("\nNext steps:")
print("1. Check: https://console.cloud.google.com/vertex-ai/generative")
print("2. Enable Generative AI API")
print("3. Or use Google AI Studio instead")
