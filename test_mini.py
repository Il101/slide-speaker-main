"""
Quick test with first 3 slides only
"""
import requests
import time
import json

API_BASE = "http://localhost:8000"

# Upload PDF
print("📤 Uploading PDF...")
pdf_path = "/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/.data/157dca84-de76-4ce2-b4c2-b462edfc1ae8/Physik-Vorlesung-1.pdf"
with open(pdf_path, 'rb') as f:
    response = requests.post(
        f"{API_BASE}/upload",
        files={'file': ('test.pdf', f, 'application/pdf')},
        params={'pipeline': 'intelligent'}
    )

lesson_id = response.json()['lesson_id']
print(f"✅ Lesson ID: {lesson_id}")

# Wait for processing
print("\n⏳ Waiting for processing...")
for i in range(120):  # 10 minutes max
    resp = requests.get(f"{API_BASE}/lessons/{lesson_id}/status")
    if resp.status_code != 200:
        print(f"Error: {resp.text[:200]}")
        time.sleep(5)
        continue
    
    status = resp.json()
    if status.get('status') == 'completed':
        print(f"\n✅ Processing completed!")
        break
    elif status.get('status') == 'failed':
        print(f"\n❌ Failed: {status}")
        break
    
    print(f"  {status.get('progress')}% - {status.get('stage')}", end='\r')
    time.sleep(5)

# Get manifest
print("\n📋 Fetching manifest...")
manifest = requests.get(f"{API_BASE}/lessons/{lesson_id}/manifest").json()

# Analyze
slides = manifest.get('slides', [])
print(f"\n📊 ANALYSIS (first 3 slides)")
print("="*70)

# Check Presentation Context
pc = manifest.get('presentation_context', {})
if pc:
    print(f"\n🧠 Presentation Context:")
    print(f"  Theme: {pc.get('theme')}")
    print(f"  Mock: {pc.get('mock', False)}")

# Check first slide in detail
if slides:
    slide = slides[0]
    print(f"\n🔍 Slide 1:")
    print(f"  Elements: {len(slide.get('elements', []))}")
    
    sm = slide.get('semantic_map', {})
    if sm:
        print(f"  Semantic groups: {len(sm.get('groups', []))}")
        print(f"  Mock: {sm.get('mock', False)}")
        for i, group in enumerate(sm.get('groups', [])[:3], 1):
            print(f"    Group {i}: {group.get('type')} (priority: {group.get('priority')})")
    
    tt = slide.get('talk_track', [])
    if tt:
        print(f"  Talk track: {len(tt)} segments")
        for seg in tt[:2]:
            print(f"    [{seg.get('segment')}] {seg.get('text')[:50]}...")
    
    print(f"  Audio: {slide.get('audio', 'N/A')}")
    print(f"  Cues: {len(slide.get('cues', []))}")

print(f"\n✅ View at: http://localhost:3000/?lesson={lesson_id}")
