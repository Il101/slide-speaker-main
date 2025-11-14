"""
Test script для нового Intelligent Pipeline
"""
import requests
import time
import json
import sys

API_BASE = "http://localhost:8000"

def test_upload_and_process(pdf_path):
    """Upload PDF and test intelligent pipeline"""
    
    print("🚀 Testing Intelligent Pipeline")
    print("="*60)
    
    # 1. Upload PDF
    print("\n📤 Step 1: Uploading PDF...")
    with open(pdf_path, 'rb') as f:
        response = requests.post(
            f"{API_BASE}/upload",
            files={'file': ('test.pdf', f, 'application/pdf')}
        )
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return None
    
    data = response.json()
    lesson_id = data.get('lesson_id')
    print(f"✅ Uploaded! Lesson ID: {lesson_id}")
    
    # 2. Wait for processing
    print("\n⏳ Step 2: Waiting for pipeline processing...")
    max_wait = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{API_BASE}/lessons/{lesson_id}/status")
        if response.status_code != 200:
            print(f"❌ Status check failed: {response.text}")
            return None
        
        status_data = response.json()
        status = status_data.get('status')
        progress = status_data.get('progress', 0)
        stage = status_data.get('stage', 'unknown')
        
        print(f"   Progress: {progress}% - Stage: {stage}")
        
        if status == 'completed':
            print(f"✅ Processing completed!")
            break
        elif status == 'failed':
            print(f"❌ Processing failed: {status_data.get('message', 'Unknown error')}")
            return None
        
        time.sleep(5)
    else:
        print("❌ Timeout waiting for processing")
        return None
    
    # 3. Get manifest
    print("\n📋 Step 3: Fetching manifest...")
    response = requests.get(f"{API_BASE}/lessons/{lesson_id}/manifest")
    if response.status_code != 200:
        print(f"❌ Manifest fetch failed: {response.text}")
        return None
    
    manifest = response.json()
    print(f"✅ Manifest fetched!")
    
    # 4. Analyze results
    print("\n📊 Step 4: Analyzing results...")
    print("="*60)
    
    slides = manifest.get('slides', [])
    print(f"Total slides: {len(slides)}")
    
    # Check presentation context
    presentation_context = manifest.get('presentation_context', {})
    if presentation_context:
        print("\n🧠 Presentation Context:")
        print(f"  Theme: {presentation_context.get('theme', 'N/A')}")
        print(f"  Level: {presentation_context.get('level', 'N/A')}")
        print(f"  Language: {presentation_context.get('language', 'N/A')}")
        print(f"  Style: {presentation_context.get('presentation_style', 'N/A')}")
        print(f"  Mock: {presentation_context.get('mock', False)}")
    
    # Analyze first slide in detail
    if slides:
        slide = slides[0]
        print(f"\n🔍 Slide 1 Analysis:")
        print(f"  Elements: {len(slide.get('elements', []))}")
        print(f"  Duration: {slide.get('duration', 0):.1f}s")
        print(f"  Audio: {slide.get('audio', 'N/A')}")
        print(f"  Cues: {len(slide.get('cues', []))}")
        
        # Check semantic map
        semantic_map = slide.get('semantic_map', {})
        if semantic_map:
            print(f"\n  📍 Semantic Map:")
            print(f"    Slide type: {semantic_map.get('slide_type', 'N/A')}")
            print(f"    Groups: {len(semantic_map.get('groups', []))}")
            print(f"    Noise elements: {len(semantic_map.get('noise_elements', []))}")
            print(f"    Cognitive load: {semantic_map.get('cognitive_load', 'N/A')}")
            print(f"    Mock: {semantic_map.get('mock', False)}")
            
            # Show groups
            for i, group in enumerate(semantic_map.get('groups', [])[:3]):
                print(f"\n    Group {i+1}:")
                print(f"      Type: {group.get('type', 'N/A')}")
                print(f"      Priority: {group.get('priority', 'N/A')}")
                print(f"      Elements: {len(group.get('element_ids', []))}")
                strategy = group.get('highlight_strategy', {})
                print(f"      Effect: {strategy.get('effect_type', 'N/A')}")
                print(f"      Intensity: {strategy.get('intensity', 'N/A')}")
        
        # Check talk track
        talk_track = slide.get('talk_track', [])
        if talk_track:
            print(f"\n  💬 Talk Track ({len(talk_track)} segments):")
            for segment in talk_track[:3]:
                seg_type = segment.get('segment', 'N/A')
                text = segment.get('text', '')[:80]
                print(f"    [{seg_type}] {text}...")
        
        # Check speaker notes
        speaker_notes = slide.get('speaker_notes', '')
        if speaker_notes:
            print(f"\n  📝 Speaker Notes:")
            print(f"    {speaker_notes[:150]}...")
        
        # Show cues
        cues = slide.get('cues', [])
        if cues:
            print(f"\n  ✨ Visual Cues ({len(cues)} total):")
            for i, cue in enumerate(cues[:5]):
                action = cue.get('action', 'N/A')
                t0 = cue.get('t0', 0)
                t1 = cue.get('t1', 0)
                effect_type = cue.get('effect_type', 'N/A')
                print(f"    {i+1}. {action} ({effect_type}) @ {t0:.1f}s - {t1:.1f}s")
    
    print("\n" + "="*60)
    print("🎉 Test completed successfully!")
    print(f"Lesson ID: {lesson_id}")
    print(f"View at: http://localhost:3000/?lesson={lesson_id}")
    
    return lesson_id

if __name__ == "__main__":
    # Use existing PDF
    test_pdf = "/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/.data/157dca84-de76-4ce2-b4c2-b462edfc1ae8/Physik-Vorlesung-1.pdf"
    
    print(f"Testing with: {test_pdf}")
    
    lesson_id = test_upload_and_process(test_pdf)
    
    if lesson_id:
        sys.exit(0)
    else:
        sys.exit(1)
