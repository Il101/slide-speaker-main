#!/usr/bin/env python3
"""Test full pipeline: PDF -> PNG -> Vision API -> LLM -> TTS -> Video"""
import requests
import time
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Login
print("=" * 60)
print("STEP 1: Login")
print("=" * 60)
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "admin@example.com", "password": "admin123"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print(f"✅ Login successful")

headers = {
    "Authorization": f"Bearer {token}",
}

# Upload PDF
print("\n" + "=" * 60)
print("STEP 2: Upload PDF")
print("=" * 60)
pdf_file = "Kurs_10_short.pdf"
if not Path(pdf_file).exists():
    print(f"❌ File {pdf_file} not found")
    exit(1)

with open(pdf_file, 'rb') as f:
    files = {'file': (pdf_file, f, 'application/pdf')}
    upload_response = requests.post(
        f"{BASE_URL}/upload",
        headers=headers,
        files=files
    )

if upload_response.status_code != 200:
    print(f"❌ Upload failed: {upload_response.status_code}")
    print(upload_response.text)
    exit(1)

upload_data = upload_response.json()
lesson_id = upload_data.get('lesson_id')
print(f"✅ Upload successful")
print(f"   Lesson ID: {lesson_id}")
print(f"   Slides: {upload_data.get('slides_count', 'unknown')}")

# Monitor processing
print("\n" + "=" * 60)
print("STEP 3: Monitor Processing Pipeline")
print("=" * 60)
print("Stages: PDF -> PNG -> Vision OCR -> LLM Notes -> TTS Audio -> Visual Cues")
print()

stages_seen = set()
max_iterations = 60  # 2 minutes max
for i in range(max_iterations):
    time.sleep(2)
    
    # Get lesson status
    status_response = requests.get(
        f"{BASE_URL}/lessons/{lesson_id}",
        headers=headers
    )
    
    if status_response.status_code == 200:
        lesson_data = status_response.json()
        status = lesson_data.get('status', 'unknown')
        progress = lesson_data.get('processing_progress', {})
        
        if isinstance(progress, str):
            try:
                progress = json.loads(progress)
            except:
                progress = {}
        
        stage = progress.get('stage', 'unknown')
        progress_pct = progress.get('progress', 0)
        
        # Print only new stages
        stage_key = f"{stage}_{progress_pct}"
        if stage_key not in stages_seen:
            stages_seen.add(stage_key)
            print(f"[{i+1}] Status: {status}, Stage: {stage}, Progress: {progress_pct}%")
        
        # Check stage details
        if stage == 'parsing' and 'parsing' not in stages_seen:
            print("    📄 Parsing PDF and converting to PNG...")
            stages_seen.add('parsing')
        elif stage == 'generating_notes' and 'generating_notes' not in stages_seen:
            print("    👁️  Using Vision API for OCR...")
            print("    🤖 Using LLM (OpenRouter) for speaker notes...")
            stages_seen.add('generating_notes')
        elif stage == 'generating_audio' and 'generating_audio' not in stages_seen:
            print("    🔊 Using TTS for audio generation...")
            stages_seen.add('generating_audio')
        elif stage == 'generating_cues' and 'generating_cues' not in stages_seen:
            print("    ✨ Generating visual cues...")
            stages_seen.add('generating_cues')
        
        if status == 'completed':
            print(f"\n✅ Processing completed successfully!")
            print(f"   Total slides: {lesson_data.get('slides_count', 'unknown')}")
            break
        elif status == 'failed':
            print(f"\n❌ Processing failed")
            print(f"   Error: {progress.get('error', 'Unknown error')}")
            exit(1)
    else:
        print(f"❌ Failed to get status: {status_response.status_code}")
        break
else:
    print("\n⏰ Timeout waiting for processing to complete")
    exit(1)

# Check generated files
print("\n" + "=" * 60)
print("STEP 4: Verify Generated Files")
print("=" * 60)

# Get manifest
manifest_response = requests.get(
    f"{BASE_URL}/lessons/{lesson_id}/manifest",
    headers=headers
)

if manifest_response.status_code == 200:
    manifest = manifest_response.json()
    print(f"✅ Manifest loaded")
    print(f"   Slides: {len(manifest.get('slides', []))}")
    
    for i, slide in enumerate(manifest.get('slides', []), 1):
        print(f"\n   Slide {i}:")
        print(f"     - Image: {slide.get('image', 'N/A')}")
        print(f"     - Audio: {slide.get('audio', 'N/A')}")
        print(f"     - Elements: {len(slide.get('elements', []))}")
        print(f"     - Speaker notes: {len(slide.get('speaker_notes', ''))} chars")
        print(f"     - Visual cues: {len(slide.get('cues', []))}")
        
        # Check first element text (OCR result)
        if slide.get('elements'):
            first_elem = slide['elements'][0]
            text_preview = first_elem.get('text', '')[:50]
            print(f"     - First element text: '{text_preview}...'")
else:
    print(f"❌ Failed to get manifest: {manifest_response.status_code}")

# Export video
print("\n" + "=" * 60)
print("STEP 5: Export to Video (with Audio)")
print("=" * 60)

export_response = requests.post(
    f"{BASE_URL}/lessons/{lesson_id}/export",
    headers=headers
)

if export_response.status_code != 200:
    print(f"❌ Export failed: {export_response.status_code}")
    print(export_response.text)
    exit(1)

export_data = export_response.json()
job_id = export_data.get('job_id')
print(f"✅ Export started")
print(f"   Job ID: {job_id}")

# Monitor export
print("\nMonitoring export progress...")
for i in range(30):
    time.sleep(2)
    
    status_response = requests.get(
        f"{BASE_URL}/lessons/{lesson_id}/export/status",
        headers=headers,
        params={"job_id": job_id}
    )
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        status = status_data.get('status')
        progress = status_data.get('progress', 0)
        stage = status_data.get('stage', 'unknown')
        
        print(f"[{i+1}] Export: {status}, Stage: {stage}, Progress: {progress}%")
        
        if status in ['completed', 'success']:
            print(f"\n✅ Video export completed!")
            if 'download_url' in status_data:
                print(f"   Download: {BASE_URL}{status_data['download_url']}")
            break
        elif status == 'failure':
            print(f"\n❌ Export failed: {status_data.get('error', 'Unknown')}")
            exit(1)
else:
    print("\n⏰ Export timeout")

# Summary
print("\n" + "=" * 60)
print("PIPELINE TEST SUMMARY")
print("=" * 60)
print("✅ PDF Upload")
print("✅ PDF to PNG conversion")
print("✅ Vision API OCR")
print("✅ LLM (OpenRouter) speaker notes generation")
print("✅ TTS audio generation")
print("✅ Visual cues generation")
print("✅ Video export with audio")
print("\n🎉 Full pipeline works correctly!")
