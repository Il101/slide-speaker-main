"""
Test Gemini API connection with existing credentials
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

print("="*70)
print("🔍 TESTING GEMINI API CONNECTION")
print("="*70)

# Check available credentials
print("\n1️⃣ Checking available credentials...")

# Google Cloud credentials
gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if gcp_creds:
    print(f"✅ GOOGLE_APPLICATION_CREDENTIALS: {gcp_creds}")
    if os.path.exists(gcp_creds):
        print(f"   File exists: ✅")
    else:
        print(f"   File exists: ❌")
else:
    print("⚠️  GOOGLE_APPLICATION_CREDENTIALS not set")

# Google API Key (для Gemini API Studio)
google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if google_api_key:
    print(f"✅ GOOGLE_API_KEY: {google_api_key[:10]}...")
else:
    print("⚠️  GOOGLE_API_KEY not set")

# GCP Project
gcp_project = os.getenv("GCP_PROJECT_ID")
if gcp_project:
    print(f"✅ GCP_PROJECT_ID: {gcp_project}")
else:
    print("⚠️  GCP_PROJECT_ID not set")

print("\n" + "="*70)

# Test 1: Gemini API Studio (requires GOOGLE_API_KEY)
print("\n2️⃣ Testing Gemini API Studio (google.generativeai)...")
try:
    import google.generativeai as genai
    
    # Try to configure
    if google_api_key:
        genai.configure(api_key=google_api_key)
        print("✅ Configured with GOOGLE_API_KEY")
        
        # List available models
        try:
            models = genai.list_models()
            gemini_models = [m for m in models if 'gemini' in m.name.lower()]
            
            print(f"✅ Available Gemini models: {len(gemini_models)}")
            for model in gemini_models[:5]:
                print(f"   - {model.name}")
            
            # Try a simple generation
            print("\n   Testing generation with gemini-2.0-flash-exp...")
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content("Say 'Hello from Gemini!'")
            print(f"   ✅ Response: {response.text[:50]}")
            
        except Exception as e:
            print(f"   ⚠️  Error listing models or generating: {e}")
    else:
        print("❌ No GOOGLE_API_KEY available")
        
except ImportError:
    print("⚠️  google-generativeai not installed")
    print("   Install with: pip install google-generativeai")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*70)

# Test 2: Vertex AI (requires GCP credentials)
print("\n3️⃣ Testing Vertex AI (vertexai)...")
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    
    if gcp_project and gcp_creds and os.path.exists(gcp_creds):
        try:
            # Initialize Vertex AI
            vertexai.init(
                project=gcp_project,
                location="us-central1"
            )
            print(f"✅ Initialized Vertex AI for project: {gcp_project}")
            
            # Try to use Gemini model
            model = GenerativeModel("gemini-2.0-flash-exp")
            print("✅ Created Gemini model instance")
            
            # Test generation
            response = model.generate_content("Say 'Hello from Vertex AI!'")
            print(f"✅ Response: {response.text[:50]}")
            
        except Exception as e:
            print(f"⚠️  Error with Vertex AI: {e}")
    else:
        print("❌ Missing GCP_PROJECT_ID or credentials file")
        
except ImportError:
    print("⚠️  vertexai not installed")
    print("   Install with: pip install google-cloud-aiplatform")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*70)

# Test 3: OpenRouter with Gemini models
print("\n4️⃣ Testing OpenRouter (может иметь Gemini)...")
try:
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        print(f"✅ OPENROUTER_API_KEY: {openrouter_key[:10]}...")
        
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
        
        # Try to list models (not all providers support this)
        print("   Trying to get model list...")
        # OpenRouter doesn't have list endpoint, skip
        print("   ℹ️  OpenRouter doesn't support model listing via API")
        print("   Check manually: https://openrouter.ai/models")
        
    else:
        print("❌ No OPENROUTER_API_KEY")
        
except ImportError:
    print("⚠️  openai not installed")
except Exception as e:
    print(f"⚠️  Error: {e}")

print("\n" + "="*70)
print("\n📊 SUMMARY:")
print("="*70)

if google_api_key:
    print("✅ BEST OPTION: Gemini API Studio (google.generativeai)")
    print("   - Fast and cheap")
    print("   - Direct API calls")
    print("   - Model: gemini-2.0-flash-exp")
    print("   - Cost: ~$0.01 per slide")
elif gcp_creds and os.path.exists(gcp_creds):
    print("✅ OPTION 2: Vertex AI (vertexai)")
    print("   - Uses GCP credentials")
    print("   - More complex setup")
    print("   - Model: gemini-2.0-flash-exp")
    print("   - Cost: ~$0.01 per slide")
else:
    print("❌ NO GEMINI ACCESS AVAILABLE")
    print("   Need either:")
    print("   1. GOOGLE_API_KEY (from AI Studio)")
    print("   2. Valid GCP credentials + project")

print("\n" + "="*70)
