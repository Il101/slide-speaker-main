#!/usr/bin/env python3
"""
Test script to check Visual Effects flow from DB -> API -> Frontend
"""

import json
import psycopg2
import requests

# Configuration
LESSON_ID = "c3bf4454-5711-4020-a767-6e4e6da29ca1"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "slide_speaker",
    "user": "postgres",
    "password": "kZYS-J3gRfo1CxRwbh-HqWY07ODVWIzIdVvb3STH_qc"
}
API_BASE = "http://localhost:8000"

def test_database():
    """Test 1: Check database has visual_effects_manifest"""
    print("=" * 80)
    print("TEST 1: Checking Database")
    print("=" * 80)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Check if visual_effects_manifest exists
    cur.execute("""
        SELECT 
            (manifest_data::jsonb -> 'slides' -> 0 -> 'visual_effects_manifest') IS NOT NULL as has_vfx,
            jsonb_array_length((manifest_data::jsonb -> 'slides' -> 0 -> 'visual_effects_manifest' -> 'effects')::jsonb) as effects_count
        FROM lessons 
        WHERE id = %s
    """, (LESSON_ID,))
    
    result = cur.fetchone()
    if result:
        has_vfx, effects_count = result
        print(f"✅ visual_effects_manifest exists: {has_vfx}")
        print(f"✅ Effects count: {effects_count}")
        
        # Get sample effect
        cur.execute("""
            SELECT 
                jsonb_pretty((manifest_data::jsonb -> 'slides' -> 0 -> 'visual_effects_manifest' -> 'effects' -> 0)::jsonb)
            FROM lessons 
            WHERE id = %s
        """, (LESSON_ID,))
        
        sample_effect = cur.fetchone()[0]
        print(f"\n📋 Sample effect:")
        print(sample_effect[:500] + "..." if len(sample_effect) > 500 else sample_effect)
    else:
        print("❌ Lesson not found in database")
    
    cur.close()
    conn.close()
    return has_vfx, effects_count

def test_api():
    """Test 2: Check API returns visual_effects_manifest"""
    print("\n" + "=" * 80)
    print("TEST 2: Checking API Response")
    print("=" * 80)
    
    # Try to get manifest (this will fail without auth, which is expected)
    response = requests.get(f"{API_BASE}/lessons/{LESSON_ID}/manifest")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 401:
        print("⚠️  Authentication required (expected)")
        print("💡 To test API properly, you need to:")
        print("   1. Login to the frontend")
        print("   2. Open browser DevTools -> Network tab")
        print("   3. Go to player page and check manifest response")
        return None
    elif response.status_code == 200:
        data = response.json()
        
        # Check slides
        slides = data.get('slides', [])
        print(f"✅ Slides count: {len(slides)}")
        
        if slides:
            first_slide = slides[0]
            has_vfx = 'visual_effects_manifest' in first_slide
            print(f"✅ First slide has visual_effects_manifest: {has_vfx}")
            
            if has_vfx:
                vfx = first_slide['visual_effects_manifest']
                print(f"✅ VFX version: {vfx.get('version')}")
                print(f"✅ VFX effects count: {len(vfx.get('effects', []))}")
                print(f"✅ VFX timeline events: {len(vfx.get('timeline', {}).get('events', []))}")
                
                # Show sample effect
                if vfx.get('effects'):
                    effect = vfx['effects'][0]
                    print(f"\n📋 Sample effect from API:")
                    print(json.dumps(effect, indent=2)[:500] + "...")
        
        return data
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
        print(response.text[:200])
        return None

def test_data_structure():
    """Test 3: Analyze data structure for frontend compatibility"""
    print("\n" + "=" * 80)
    print("TEST 3: Checking Data Structure Compatibility")
    print("=" * 80)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get full manifest data
    cur.execute("""
        SELECT manifest_data::jsonb
        FROM lessons 
        WHERE id = %s
    """, (LESSON_ID,))
    
    manifest_data = cur.fetchone()[0]
    
    # Check first slide structure
    if isinstance(manifest_data, str):
        manifest = json.loads(manifest_data)
    else:
        manifest = manifest_data
    
    first_slide = manifest['slides'][0]
    vfx = first_slide.get('visual_effects_manifest', {})
    
    print(f"📊 VFX Manifest Structure:")
    print(f"  - version: {vfx.get('version')}")
    print(f"  - id: {vfx.get('id')}")
    print(f"  - effects: {type(vfx.get('effects')).__name__} with {len(vfx.get('effects', []))} items")
    print(f"  - timeline: {type(vfx.get('timeline')).__name__}")
    
    if vfx.get('timeline'):
        timeline = vfx['timeline']
        print(f"    - total_duration: {timeline.get('total_duration')}")
        print(f"    - events: {len(timeline.get('events', []))} events")
    
    if vfx.get('effects'):
        effect = vfx['effects'][0]
        print(f"\n📋 First Effect Structure:")
        print(f"  - id: {effect.get('id')}")
        print(f"  - effect_id: {effect.get('effect_id')}")
        print(f"  - type: {effect.get('type')}")
        print(f"  - timing: {effect.get('timing')}")
        print(f"  - t0: {effect.get('t0')}")
        print(f"  - t1: {effect.get('t1')}")
        print(f"  - target: {effect.get('target')}")
        print(f"  - params: {list(effect.get('params', {}).keys())}")
    
    # Check for flattened timing fields (needed by VisualEffectsEngine)
    needs_flattening = False
    if vfx.get('effects'):
        for effect in vfx['effects']:
            if 'timing' in effect and ('t0' not in effect or 't1' not in effect):
                needs_flattening = True
                break
    
    if needs_flattening:
        print("\n⚠️  WARNING: Effects have nested 'timing' object but missing flattened fields!")
        print("   VisualEffectsEngine expects: effect.t0, effect.t1, effect.duration")
        print("   Currently have: effect.timing.t0, effect.timing.t1, effect.timing.duration")
        print("   Frontend will need to transform these!")
    else:
        print("\n✅ Effects have flattened timing fields (compatible with frontend)")
    
    cur.close()
    conn.close()

def main():
    print("🔍 Visual Effects Flow Test")
    print("Testing lesson:", LESSON_ID)
    print()
    
    try:
        # Test 1: Database
        has_vfx, effects_count = test_database()
        
        if not has_vfx:
            print("\n❌ FAIL: No visual_effects_manifest in database!")
            return
        
        # Test 2: API
        api_data = test_api()
        
        # Test 3: Data structure
        test_data_structure()
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("✅ Database: visual_effects_manifest exists")
        print(f"✅ Effects count: {effects_count}")
        if api_data is None:
            print("⚠️  API: Needs authentication (test manually in browser)")
        else:
            print("✅ API: Returns data successfully")
        
        print("\n💡 Next steps:")
        print("   1. Open browser and login")
        print("   2. Navigate to player page")
        print("   3. Open DevTools Console")
        print("   4. Check for debug logs from:")
        print("      - [SlideViewer] Current slide")
        print("      - [VisualEffectsEngine] Component render")
        print("      - [Canvas2DRenderer] Added effect")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
