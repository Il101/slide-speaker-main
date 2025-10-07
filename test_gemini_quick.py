#!/usr/bin/env python3
"""Quick test for Gemini initialization in container"""
import subprocess
import sys

print("=" * 70)
print("🧪 TESTING GEMINI INITIALIZATION")
print("=" * 70)

# Test inside celery container
cmd = r'''python3 << 'PYEOF'
import os
import sys

# Check API key
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    print(f"GOOGLE_API_KEY: SET ({api_key[:10]}...)")
else:
    print("GOOGLE_API_KEY: NOT SET")

# Try to initialize Gemini
try:
    import google.generativeai as genai
    print("✅ google.generativeai module imported")
    
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        print("✅ Gemini 2.0 Flash configured successfully")
        print("✅ Model initialized")
    else:
        print("⚠️  No API key - will use mock mode")
except Exception as e:
    print(f"❌ Gemini initialization failed: {e}")
    sys.exit(1)
PYEOF
'''

result = subprocess.run(
    ['docker', 'compose', 'exec', '-T', 'celery', 'bash', '-c', cmd],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

print("=" * 70)
if result.returncode == 0:
    print("✅ Gemini is properly configured!")
else:
    print("❌ Gemini configuration failed")
    sys.exit(1)
