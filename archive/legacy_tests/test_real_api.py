"""
Test Intelligent Pipeline with REAL API keys
Проверяет качество semantic analysis и anti-reading
"""
import requests
import time
import json
import sys
from pathlib import Path

API_BASE = "http://localhost:8000"

def test_with_real_api(pdf_path):
    """Test pipeline with real API calls"""
    
    print("🚀 Testing Intelligent Pipeline with REAL API")
    print("="*70)
    print(f"PDF: {Path(pdf_path).name}")
    print("="*70)
    
    # 1. Upload PDF
    print("\n📤 Step 1: Uploading PDF...")
    with open(pdf_path, 'rb') as f:
        response = requests.post(
            f"{API_BASE}/upload",
            files={'file': (Path(pdf_path).name, f, 'application/pdf')},
            params={'pipeline': 'intelligent'}  # Explicitly use intelligent pipeline
        )
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return None
    
    data = response.json()
    lesson_id = data.get('lesson_id')
    print(f"✅ Uploaded! Lesson ID: {lesson_id}")
    
    # 2. Monitor processing with detailed progress
    print("\n⏳ Step 2: Monitoring pipeline processing...")
    max_wait = 600  # 10 minutes for real API calls
    start_time = time.time()
    last_progress = 0
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{API_BASE}/lessons/{lesson_id}/status")
        if response.status_code != 200:
            print(f"❌ Status check failed: {response.text}")
            time.sleep(5)
            continue
        
        status_data = response.json()
        status = status_data.get('status')
        progress = status_data.get('progress', 0)
        stage = status_data.get('stage', 'unknown')
        
        # Only print if progress changed
        if progress != last_progress:
            elapsed = time.time() - start_time
            print(f"   [{elapsed:.0f}s] Progress: {progress}% - Stage: {stage}")
            last_progress = progress
        
        if status == 'completed':
            print(f"\n✅ Processing completed in {elapsed:.0f}s!")
            break
        elif status == 'failed':
            print(f"\n❌ Processing failed: {status_data.get('message', 'Unknown error')}")
            return None
        
        time.sleep(5)
    else:
        print("\n❌ Timeout waiting for processing")
        return None
    
    # 3. Get manifest and analyze
    print("\n📋 Step 3: Analyzing results...")
    response = requests.get(f"{API_BASE}/lessons/{lesson_id}/manifest")
    if response.status_code != 200:
        print(f"❌ Manifest fetch failed: {response.text}")
        return None
    
    manifest = response.json()
    
    # Detailed analysis
    print("\n" + "="*70)
    print("📊 DETAILED ANALYSIS")
    print("="*70)
    
    slides = manifest.get('slides', [])
    print(f"\n📚 Total slides: {len(slides)}")
    
    # Check Presentation Context (Stage 0)
    presentation_context = manifest.get('presentation_context', {})
    if presentation_context:
        print("\n🧠 STAGE 0: Presentation Intelligence")
        print("-" * 70)
        print(f"  Theme: {presentation_context.get('theme', 'N/A')}")
        print(f"  Subject: {presentation_context.get('subject_area', 'N/A')}")
        print(f"  Level: {presentation_context.get('level', 'N/A')}")
        print(f"  Language: {presentation_context.get('language', 'N/A')}")
        print(f"  Style: {presentation_context.get('presentation_style', 'N/A')}")
        print(f"  Mock mode: {presentation_context.get('mock', False)}")
        
        if not presentation_context.get('mock', False):
            print("  ✅ REAL API was used!")
        else:
            print("  ⚠️  Mock mode was used (no API key?)")
    
    # Analyze first 3 slides in detail
    for slide_idx in range(min(3, len(slides))):
        slide = slides[slide_idx]
        slide_id = slide.get('id')
        
        print(f"\n{'='*70}")
        print(f"🔍 SLIDE {slide_id} ANALYSIS")
        print('='*70)
        
        print(f"\n📐 Basic Info:")
        print(f"  Elements: {len(slide.get('elements', []))}")
        print(f"  Duration: {slide.get('duration', 0):.1f}s")
        print(f"  Audio: {slide.get('audio', 'N/A')}")
        print(f"  Cues: {len(slide.get('cues', []))}")
        
        # STAGE 2: Semantic Map Analysis
        semantic_map = slide.get('semantic_map', {})
        if semantic_map:
            print(f"\n🎯 STAGE 2: Semantic Intelligence")
            print("-" * 70)
            print(f"  Slide type: {semantic_map.get('slide_type', 'N/A')}")
            print(f"  Total groups: {len(semantic_map.get('groups', []))}")
            print(f"  Noise elements: {len(semantic_map.get('noise_elements', []))}")
            print(f"  Visual density: {semantic_map.get('visual_density', 'N/A')}")
            print(f"  Cognitive load: {semantic_map.get('cognitive_load', 'N/A')}")
            print(f"  Mock mode: {semantic_map.get('mock', False)}")
            
            if not semantic_map.get('mock', False):
                print("  ✅ REAL Vision API was used!")
            else:
                print("  ⚠️  Mock mode was used")
            
            # Show groups in detail
            groups = semantic_map.get('groups', [])
            print(f"\n  📦 Groups breakdown:")
            for i, group in enumerate(groups[:5], 1):
                print(f"\n  Group {i}: {group.get('name', 'Unnamed')}")
                print(f"    Type: {group.get('type', 'N/A')}")
                print(f"    Priority: {group.get('priority', 'N/A')}")
                print(f"    Elements: {len(group.get('element_ids', []))}")
                print(f"    Intent: {group.get('educational_intent', 'N/A')[:60]}...")
                
                strategy = group.get('highlight_strategy', {})
                print(f"    Strategy:")
                print(f"      When: {strategy.get('when', 'N/A')}")
                print(f"      Effect: {strategy.get('effect_type', 'N/A')}")
                print(f"      Duration: {strategy.get('duration', 0):.1f}s")
                print(f"      Intensity: {strategy.get('intensity', 'N/A')}")
        
        # STAGE 3: Script Analysis
        talk_track = slide.get('talk_track', [])
        speaker_notes = slide.get('speaker_notes', '')
        
        if talk_track or speaker_notes:
            print(f"\n📝 STAGE 3: Smart Script")
            print("-" * 70)
            
            if talk_track:
                print(f"  Talk track segments: {len(talk_track)}")
                for segment in talk_track:
                    seg_type = segment.get('segment', 'N/A')
                    text = segment.get('text', '')
                    print(f"    [{seg_type:12}] {text[:70]}...")
            
            if speaker_notes:
                print(f"\n  Speaker notes ({len(speaker_notes)} chars):")
                print(f"    {speaker_notes[:200]}...")
            
            # Check for anti-reading
            if 'overlap_score' in slide:
                overlap = slide.get('overlap_score', 0)
                print(f"\n  🔍 Anti-Reading Check:")
                print(f"    Overlap score: {overlap:.3f}")
                if overlap < 0.35:
                    print(f"    ✅ PASSED (< 0.35 threshold)")
                else:
                    print(f"    ⚠️  HIGH OVERLAP (>= 0.35 threshold)")
        
        # STAGE 5: Visual Effects
        cues = slide.get('cues', [])
        if cues:
            print(f"\n✨ STAGE 5: Visual Effects")
            print("-" * 70)
            print(f"  Total cues: {len(cues)}")
            
            # Count effect types
            effect_types = {}
            for cue in cues:
                effect = cue.get('effect_type', cue.get('action', 'unknown'))
                effect_types[effect] = effect_types.get(effect, 0) + 1
            
            print(f"  Effect types:")
            for effect, count in sorted(effect_types.items(), key=lambda x: -x[1]):
                print(f"    {effect:20} x{count}")
            
            # Show first 5 cues
            print(f"\n  First 5 cues:")
            for i, cue in enumerate(cues[:5], 1):
                action = cue.get('action', 'N/A')
                effect = cue.get('effect_type', 'N/A')
                t0 = cue.get('t0', 0)
                t1 = cue.get('t1', 0)
                intensity = cue.get('intensity', 'N/A')
                print(f"    {i}. [{action}/{effect}] {t0:.1f}s-{t1:.1f}s (intensity: {intensity})")
    
    # Summary
    print("\n" + "="*70)
    print("📈 QUALITY SUMMARY")
    print("="*70)
    
    # Count slides with each feature
    slides_with_semantic = sum(1 for s in slides if s.get('semantic_map', {}).get('groups'))
    slides_with_talk_track = sum(1 for s in slides if s.get('talk_track'))
    slides_with_audio = sum(1 for s in slides if s.get('audio'))
    slides_with_cues = sum(1 for s in slides if s.get('cues'))
    
    total = len(slides)
    print(f"\nFeature coverage:")
    print(f"  Semantic maps: {slides_with_semantic}/{total} ({slides_with_semantic/total*100:.0f}%)")
    print(f"  Talk tracks:   {slides_with_talk_track}/{total} ({slides_with_talk_track/total*100:.0f}%)")
    print(f"  Audio:         {slides_with_audio}/{total} ({slides_with_audio/total*100:.0f}%)")
    print(f"  Visual cues:   {slides_with_cues}/{total} ({slides_with_cues/total*100:.0f}%)")
    
    # Check if real APIs were used
    used_real_context = presentation_context and not presentation_context.get('mock', True)
    used_real_semantic = any(not s.get('semantic_map', {}).get('mock', True) for s in slides)
    
    print(f"\nAPI usage:")
    print(f"  Presentation Context API: {'✅ YES' if used_real_context else '⚠️  NO (mock)'}")
    print(f"  Semantic Analysis API:    {'✅ YES' if used_real_semantic else '⚠️  NO (mock)'}")
    
    # Calculate total processing time
    total_duration = sum(s.get('duration', 0) for s in slides)
    print(f"\nTiming:")
    print(f"  Total audio duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"  Processing time:      {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"  Speed:                {elapsed/total_duration:.1f}x realtime")
    
    print("\n" + "="*70)
    print("🎉 Test completed successfully!")
    print(f"Lesson ID: {lesson_id}")
    print(f"View at: http://localhost:3000/?lesson={lesson_id}")
    print("="*70)
    
    return lesson_id

if __name__ == "__main__":
    # Use existing PDF
    test_pdf = "/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/.data/157dca84-de76-4ce2-b4c2-b462edfc1ae8/Physik-Vorlesung-1.pdf"
    
    if not Path(test_pdf).exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        sys.exit(1)
    
    print(f"📄 Testing with: {Path(test_pdf).name}")
    print(f"📍 Location: {test_pdf}")
    print()
    
    lesson_id = test_with_real_api(test_pdf)
    
    if lesson_id:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
