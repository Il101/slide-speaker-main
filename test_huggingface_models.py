#!/usr/bin/env python3
"""
Test Hugging Face Inference API for vision models
"""
import os
import sys
import requests
import json
import base64

# Popular vision models on HF
VISION_MODELS = [
    # Open source vision-language models
    "llava-hf/llava-1.5-7b-hf",
    "llava-hf/llava-v1.6-mistral-7b-hf",
    "microsoft/Phi-3-vision-128k-instruct",
    "microsoft/Phi-4",
    "Qwen/Qwen2-VL-7B-Instruct",
    "openbmb/MiniCPM-V-2_6",
    "THUDM/glm-4v-9b",
    "meta-llama/Llama-3.2-11B-Vision-Instruct",
    # Smaller/faster models
    "vikhyatk/moondream2",
    "HuggingFaceM4/idefics2-8b",
]

def test_hf_api(model_id, hf_token=None):
    """Test a Hugging Face model via Inference API"""
    
    API_URL = f"https://api-inference.huggingface.co/models/{model_id}"
    
    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
    
    # Simple test payload (text only first)
    payload = {
        "inputs": "What is in this image?",
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            return {"status": "✅ Available", "response": response.json()}
        elif response.status_code == 401:
            return {"status": "🔐 Requires token", "error": "Authentication required"}
        elif response.status_code == 403:
            return {"status": "❌ Access denied", "error": "Forbidden"}
        elif response.status_code == 404:
            return {"status": "❌ Not found", "error": "Model not found"}
        elif response.status_code == 503:
            return {"status": "⏳ Loading", "error": "Model is loading"}
        else:
            return {"status": f"❌ Error {response.status_code}", "error": response.text[:100]}
    except requests.exceptions.Timeout:
        return {"status": "⏱️ Timeout", "error": "Request timed out"}
    except Exception as e:
        return {"status": "❌ Error", "error": str(e)[:100]}

def main():
    print("="*80)
    print("Hugging Face Vision Models - Availability Test")
    print("="*80)
    
    # Check for HF token in environment
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_TOKEN")
    
    if hf_token:
        print(f"\n✅ Using HF Token: {hf_token[:10]}...")
    else:
        print("\n⚠️  No HF token found (some models may require authentication)")
        print("   Set HF_TOKEN environment variable to test gated models")
    
    print(f"\nTesting {len(VISION_MODELS)} vision models...\n")
    
    results = []
    for i, model in enumerate(VISION_MODELS, 1):
        print(f"{i:2}. Testing {model}...", end=" ", flush=True)
        result = test_hf_api(model, hf_token)
        print(result["status"])
        results.append((model, result))
    
    # Summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    
    available = [m for m, r in results if "✅" in r["status"] or "⏳" in r["status"]]
    requires_auth = [m for m, r in results if "🔐" in r["status"]]
    unavailable = [m for m, r in results if "❌" in r["status"]]
    
    print(f"\n✅ Available models: {len(available)}")
    for model in available:
        print(f"   - {model}")
    
    if requires_auth:
        print(f"\n🔐 Requires authentication: {len(requires_auth)}")
        for model in requires_auth:
            print(f"   - {model}")
    
    if unavailable:
        print(f"\n❌ Unavailable: {len(unavailable)}")
        for model in unavailable:
            print(f"   - {model}")
    
    # Recommendations
    print("\n" + "="*80)
    print("Recommended Models")
    print("="*80)
    
    recommendations = {
        "Best Free Option": "vikhyatk/moondream2",
        "Best Quality": "llava-hf/llava-v1.6-mistral-7b-hf",
        "Microsoft": "microsoft/Phi-3-vision-128k-instruct",
        "Fast & Light": "HuggingFaceM4/idefics2-8b",
    }
    
    for category, model in recommendations.items():
        status = next((r["status"] for m, r in results if m == model), "Unknown")
        print(f"{category:20} → {model}")
        print(f"{'':20}   Status: {status}")

if __name__ == "__main__":
    main()
