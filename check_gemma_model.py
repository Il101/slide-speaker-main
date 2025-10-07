#!/usr/bin/env python3
import requests
import json

API_KEY = "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"
MODEL = "google/gemma-3-12b-it:free"

# Get all models
response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {API_KEY}"}
)

if response.status_code == 200:
    data = response.json()
    models = data.get("data", [])
    
    # Find our model
    model = None
    for m in models:
        if m.get("id") == MODEL:
            model = m
            break
    
    if model:
        print("="*70)
        print(f"Model: {MODEL}")
        print("="*70)
        print(f"Name: {model.get('name', 'N/A')}")
        print(f"Context: {model.get('context_length', 0)} tokens")
        
        arch = model.get("architecture", {})
        modality = arch.get("modality", "N/A")
        print(f"Modality: {modality}")
        
        has_vision = "image" in str(modality).lower()
        print(f"Vision Support: {'✅ YES' if has_vision else '❌ NO'}")
        
        pricing = model.get("pricing", {})
        prompt_price = float(pricing.get("prompt", 0)) * 1000000
        completion_price = float(pricing.get("completion", 0)) * 1000000
        
        print(f"\nPricing:")
        print(f"  Input:  ${prompt_price:.2f} per 1M tokens")
        print(f"  Output: ${completion_price:.2f} per 1M tokens")
        
        if prompt_price == 0 and completion_price == 0:
            print(f"  Status: FREE! 🎉")
        else:
            print(f"  Status: Paid")
        
        print("="*70)
    else:
        print(f"❌ Model {MODEL} not found!")
        print("\nAvailable Gemma models:")
        gemma_models = [m for m in models if "gemma" in m.get("id", "").lower()]
        for m in gemma_models[:10]:
            print(f"  - {m.get('id')}")
else:
    print(f"❌ API Error: {response.status_code}")
    print(response.text)
