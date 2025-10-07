"""
Quick integration test for Intelligent Pipeline
"""
import requests
import time
import json

API_BASE = "http://localhost:8000"

# Find existing lesson to test on
print("📋 Fetching existing lessons...")
response = requests.get(f"{API_BASE}/lessons")
lessons = response.json()

if not lessons:
    print("❌ No lessons found. Please upload a presentation first.")
    exit(1)

# Use first lesson
lesson_id = lessons[0]['id']
print(f"✅ Testing with lesson: {lesson_id}")

# Get manifest
print("\n📊 Fetching manifest...")
resp = requests.get(f"{API_BASE}/lessons/{lesson_id}/manifest")
if resp.status_code != 200:
    print(f"❌ Failed to fetch manifest: {resp.text}")
    exit(1)

manifest = resp.json()
slides = manifest.get('slides', [])

print(f"\n✨ INTELLIGENT PIPELINE RESULTS")
print("="*70)

# Check for intelligent pipeline markers
pc = manifest.get('presentation_context')
if pc:
    print("\n🧠 Presentation Context (Stage 0):")
    print(f"  ✅ Found! Theme: {pc.get('theme', 'N/A')}")
    print(f"  Mock mode: {pc.get('mock', False)}")
else:
    print("\n⚠️  No presentation_context - using fallback logic")

# Check first slide
if slides:
    slide = slides[0]
    print(f"\n🔍 Slide 1 Analysis:")
    print(f"  Elements: {len(slide.get('elements', []))}")
    print(f"  Speaker notes: {len(slide.get('speaker_notes', ''))} chars")
    
    # Check semantic map
    sm = slide.get('semantic_map')
    if sm:
        print(f"\n  ✅ Semantic Map (Stage 2):")
        print(f"    Groups: {len(sm.get('groups', []))}")
        print(f"    Mock: {sm.get('mock', False)}")
        for i, group in enumerate(sm.get('groups', [])[:3], 1):
            print(f"      {i}. {group.get('type')} (priority: {group.get('priority')})")
    else:
        print(f"\n  ⚠️  No semantic_map - using fallback")
    
    # Check talk track
    tt = slide.get('talk_track')
    if tt:
        print(f"\n  ✅ Talk Track (Stage 3):")
        print(f"    Segments: {len(tt)}")
        for seg in tt[:2]:
            print(f"      [{seg.get('segment')}] {seg.get('text', '')[:50]}...")
    else:
        print(f"\n  ⚠️  No talk_track - using fallback")
    
    # Check visual effects
    cues = slide.get('cues', [])
    if cues:
        print(f"\n  ✅ Visual Effects (Stage 5):")
        print(f"    Cues: {len(cues)}")
        effect_types = set(c.get('effect_type') for c in cues)
        print(f"    Effect types: {', '.join(effect_types)}")
    else:
        print(f"\n  ⚠️  No cues")
    
    # Check validation markers
    validation = slide.get('validation')
    if validation:
        print(f"\n  ✅ Validation (Stage 6):")
        for layer, result in validation.items():
            print(f"    {layer}: {result}")
    else:
        print(f"\n  ⚠️  No validation data")

print(f"\n\n{'='*70}")
print(f"📈 Pipeline Status:")
if pc and slides[0].get('semantic_map') and slides[0].get('talk_track'):
    print("  ✅✅✅ INTELLIGENT PIPELINE ACTIVE!")
else:
    print("  ⚠️⚠️⚠️  Using fallback (classic) pipeline")

print(f"\n🌐 View at: http://localhost:3000/?lesson={lesson_id}")
