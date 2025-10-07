"""
Test upload and monitor pipeline with Gemini
"""
import requests
import time
import json

API_BASE = "http://localhost:8000"

print("="*70)
print("🧪 TESTING INTELLIGENT PIPELINE WITH GEMINI")
print("="*70)

# Find existing PDF
import os
pdf_files = [
    ".data/157dca84-de76-4ce2-b4c2-b462edfc1ae8/Physik-Vorlesung-1.pdf",
    "test_presentation.pptx",
    "test_real.pptx"
]

pdf_path = None
for path in pdf_files:
    if os.path.exists(path):
        pdf_path = path
        break

if not pdf_path:
    print("❌ No test file found!")
    print("   Searched for:")
    for p in pdf_files:
        print(f"   - {p}")
    exit(1)

print(f"\n📄 Using file: {pdf_path}")

# Upload
print("\n1️⃣ Uploading presentation...")
try:
    with open(pdf_path, 'rb') as f:
        response = requests.post(
            f"{API_BASE}/upload",
            files={'file': (os.path.basename(pdf_path), f, 'application/pdf')},
            params={'pipeline': 'intelligent'},
            timeout=30
        )
    
    if response.status_code != 200:
        print(f"   ❌ Upload failed: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        exit(1)
    
    data = response.json()
    lesson_id = data.get('lesson_id')
    print(f"   ✅ Uploaded! Lesson ID: {lesson_id}")
    
except Exception as e:
    print(f"   ❌ Upload error: {e}")
    exit(1)

# Monitor processing
print("\n2️⃣ Monitoring processing...")
print("   (This may take 2-5 minutes with Gemini FREE tier)")

start_time = time.time()
last_stage = ""

for i in range(180):  # 15 minutes max
    try:
        resp = requests.get(f"{API_BASE}/lessons/{lesson_id}/status", timeout=10)
        
        if resp.status_code != 200:
            print(f"\r   ⚠️  Status check failed: {resp.status_code}", end='')
            time.sleep(5)
            continue
        
        status = resp.json()
        stage = status.get('stage', 'unknown')
        progress = status.get('progress', 0)
        
        # Show stage changes
        if stage != last_stage:
            elapsed = int(time.time() - start_time)
            print(f"\r   [{elapsed}s] {stage}: {progress}%")
            last_stage = stage
        else:
            print(f"\r   [{int(time.time() - start_time)}s] {stage}: {progress}%", end='', flush=True)
        
        # Check completion
        if status.get('status') == 'completed':
            elapsed = int(time.time() - start_time)
            print(f"\n   ✅ Completed in {elapsed} seconds!")
            break
        
        if status.get('status') == 'failed':
            print(f"\n   ❌ Failed: {status}")
            break
        
        time.sleep(5)
    
    except Exception as e:
        print(f"\r   ⚠️  Error: {str(e)[:50]}", end='')
        time.sleep(5)

# Get manifest
print("\n3️⃣ Analyzing results...")
try:
    manifest = requests.get(f"{API_BASE}/lessons/{lesson_id}/manifest", timeout=10).json()
    
    # Check presentation context
    pc = manifest.get('presentation_context', {})
    slides = manifest.get('slides', [])
    
    print(f"\n📊 RESULTS:")
    print("="*70)
    
    # Presentation context
    if pc:
        print(f"\n🧠 Presentation Context (Stage 0):")
        print(f"   Theme: {pc.get('theme', 'N/A')}")
        print(f"   Level: {pc.get('level', 'N/A')}")
        print(f"   Language: {pc.get('language', 'N/A')}")
        print(f"   Mock: {pc.get('mock', False)}")
    else:
        print(f"\n⚠️  No presentation_context (fallback used)")
    
    # Analyze first slide
    if slides:
        slide = slides[0]
        print(f"\n🔍 First Slide Analysis:")
        print(f"   Elements: {len(slide.get('elements', []))}")
        
        # Semantic map
        sm = slide.get('semantic_map', {})
        if sm:
            print(f"\n   ✅ Semantic Map (Stage 2 - Gemini):")
            print(f"      Groups: {len(sm.get('groups', []))}")
            print(f"      Mock: {sm.get('mock', False)}")
            
            for i, group in enumerate(sm.get('groups', [])[:3], 1):
                elements = group.get('elements', [])
                print(f"      {i}. {group.get('type')} (priority: {group.get('priority')}, elements: {len(elements)})")
                print(f"         Strategy: {group.get('highlight_strategy', 'N/A')}")
        else:
            print(f"\n   ⚠️  No semantic_map (fallback used)")
        
        # Talk track
        tt = slide.get('talk_track', [])
        if tt:
            print(f"\n   ✅ Talk Track (Stage 3):")
            print(f"      Segments: {len(tt)}")
            for seg in tt[:2]:
                print(f"      [{seg.get('segment')}] {seg.get('text', '')[:60]}...")
        else:
            print(f"\n   ⚠️  No talk_track")
        
        # Visual effects
        cues = slide.get('cues', [])
        if cues:
            print(f"\n   ✅ Visual Effects (Stage 5):")
            print(f"      Cues: {len(cues)}")
            effect_types = set(c.get('effect_type', 'unknown') for c in cues)
            print(f"      Types: {', '.join(list(effect_types)[:5])}")
        else:
            print(f"\n   ⚠️  No cues")
        
        # Audio
        audio = slide.get('audio')
        duration = slide.get('duration')
        print(f"\n   Audio: {audio if audio else 'N/A'}")
        print(f"   Duration: {duration:.1f}s" if duration else "   Duration: N/A")
    
    # Summary
    print(f"\n📈 PIPELINE STATUS:")
    print("="*70)
    
    has_pc = bool(pc and not pc.get('mock', True))
    has_sm = bool(slides and slides[0].get('semantic_map') and not slides[0].get('semantic_map', {}).get('mock', True))
    has_tt = bool(slides and slides[0].get('talk_track'))
    
    if has_pc and has_sm and has_tt:
        print("✅✅✅ INTELLIGENT PIPELINE ACTIVE!")
        print("   - Presentation Context: ✅")
        print("   - Semantic Maps (Gemini): ✅")
        print("   - Talk Tracks: ✅")
        print("\n💰 Using Gemini 2.0 Flash ($0.01 vs $1.50)")
    else:
        print("⚠️⚠️⚠️  FALLBACK MODE")
        print(f"   - Presentation Context: {'✅' if has_pc else '❌'}")
        print(f"   - Semantic Maps: {'✅' if has_sm else '❌'}")
        print(f"   - Talk Tracks: {'✅' if has_tt else '❌'}")
        print("\n   Check logs for errors")
    
    print(f"\n🌐 View: http://localhost:3000/?lesson={lesson_id}")
    print("="*70)

except Exception as e:
    print(f"❌ Error analyzing results: {e}")
    import traceback
    traceback.print_exc()
