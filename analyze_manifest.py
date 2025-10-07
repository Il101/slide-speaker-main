#!/usr/bin/env python3
"""Analyze manifest from completed lesson"""
import requests
import json

LESSON_ID = "ffea6465-6e18-441c-be01-cb0853c3d41a"
API_BASE = "http://localhost:8000"

print("=" * 70)
print("📊 INTELLIGENT PIPELINE RESULTS")
print("=" * 70)

# Get manifest
resp = requests.get(f"{API_BASE}/lessons/{LESSON_ID}/manifest")
if resp.status_code != 200:
    print(f"❌ Failed to get manifest: {resp.status_code}")
    exit(1)

data = resp.json()

# Presentation context
pc = data.get('presentation_context', {})
print(f"\n🧠 Presentation Context (Stage 0):")
print(f"   Theme: {pc.get('theme', 'N/A')}")
print(f"   Level: {pc.get('level', 'N/A')}")
print(f"   Language: {pc.get('language', 'N/A')}")
print(f"   Mock: {pc.get('mock', False)}")

# First slide analysis
slides = data.get('slides', [])
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
            print(f"      {i}. {group.get('type')} (priority: {group.get('priority')})")
            print(f"         Elements: {len(group.get('elements', []))}")
    
    # Talk track
    tt = slide.get('talk_track', [])
    if tt:
        print(f"\n   ✅ Talk Track (Stage 3):")
        print(f"      Segments: {len(tt)}")
        for seg in tt[:2]:
            print(f"      [{seg.get('segment')}] {seg.get('text', '')[:60]}...")

# Summary
print(f"\n📈 PIPELINE STATUS:")
print("=" * 70)

has_pc = bool(pc and not pc.get('mock', True))
has_sm = bool(slides and slides[0].get('semantic_map') and not slides[0].get('semantic_map', {}).get('mock', True))
has_tt = bool(slides and slides[0].get('talk_track'))

if has_pc and has_sm and has_tt:
    print("✅✅✅ INTELLIGENT PIPELINE ACTIVE WITH GEMINI!")
    print("   - Presentation Context: ✅")
    print("   - Semantic Maps (Gemini): ✅")
    print("   - Talk Tracks: ✅")
    print("\n💰 Using Gemini 2.0 Flash (99.3% cheaper than GPT-4o-mini)")
else:
    print("⚠️ PARTIAL PIPELINE")
    print(f"   - Presentation Context: {'✅' if has_pc else '❌'}")
    print(f"   - Semantic Maps: {'✅' if has_sm else '❌'}")
    print(f"   - Talk Tracks: {'✅' if has_tt else '❌'}")

print(f"\n🌐 View: http://localhost:3000/?lesson={LESSON_ID}")
print("=" * 70)
