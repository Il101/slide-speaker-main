#!/usr/bin/env python3
"""
Test script to verify visual effects transformation in API
"""

import json
import psycopg2

# Configuration
LESSON_ID = "c3bf4454-5711-4020-a767-6e4e6da29ca1"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "slide_speaker",
    "user": "postgres",
    "password": "kZYS-J3gRfo1CxRwbh-HqWY07ODVWIzIdVvb3STH_qc"
}

def test_transformation():
    """Test if data needs transformation"""
    print("🔍 Checking visual_effects_manifest structure in database")
    print("=" * 80)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get manifest data
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
    
    if not vfx:
        print("❌ No visual_effects_manifest found!")
        return False
    
    print(f"✅ VFX Manifest found")
    print(f"   Version: {vfx.get('version')}")
    print(f"   ID: {vfx.get('id')}")
    print(f"   Effects count: {len(vfx.get('effects', []))}")
    
    if not vfx.get('effects'):
        print("❌ No effects found!")
        return False
    
    # Check first effect
    first_effect = vfx['effects'][0]
    print(f"\n📋 First Effect (BEFORE transformation):")
    print(f"   id: {first_effect.get('id')}")
    print(f"   effect_id: {first_effect.get('effect_id')}")
    print(f"   type: {first_effect.get('type')}")
    print(f"   Has 'timing' object: {'timing' in first_effect}")
    print(f"   Has flat 't0': {'t0' in first_effect}")
    print(f"   Has flat 't1': {'t1' in first_effect}")
    print(f"   Has flat 'duration': {'duration' in first_effect}")
    
    if 'timing' in first_effect:
        print(f"   timing.t0: {first_effect['timing'].get('t0')}")
        print(f"   timing.t1: {first_effect['timing'].get('t1')}")
        print(f"   timing.duration: {first_effect['timing'].get('duration')}")
    
    # Simulate transformation
    print(f"\n🔧 Simulating API transformation...")
    transformed_effect = first_effect.copy()
    
    # Add effect_id alias
    if "id" in transformed_effect and "effect_id" not in transformed_effect:
        transformed_effect["effect_id"] = transformed_effect["id"]
    
    # Flatten timing fields
    if "timing" in transformed_effect and transformed_effect["timing"]:
        timing = transformed_effect["timing"]
        if "t0" not in transformed_effect:
            transformed_effect["t0"] = timing.get("t0", 0)
        if "t1" not in transformed_effect:
            transformed_effect["t1"] = timing.get("t1", 0)
        if "duration" not in transformed_effect:
            transformed_effect["duration"] = timing.get("duration", 0)
        if "confidence" not in transformed_effect:
            transformed_effect["confidence"] = timing.get("confidence", 1.0)
        if "source" not in transformed_effect:
            transformed_effect["source"] = timing.get("source", "fallback")
        if "precision" not in transformed_effect:
            transformed_effect["precision"] = timing.get("precision", "segment")
    
    print(f"\n📋 First Effect (AFTER transformation):")
    print(f"   id: {transformed_effect.get('id')}")
    print(f"   effect_id: {transformed_effect.get('effect_id')}")
    print(f"   type: {transformed_effect.get('type')}")
    print(f"   t0: {transformed_effect.get('t0')}")
    print(f"   t1: {transformed_effect.get('t1')}")
    print(f"   duration: {transformed_effect.get('duration')}")
    print(f"   confidence: {transformed_effect.get('confidence')}")
    print(f"   source: {transformed_effect.get('source')}")
    print(f"   precision: {transformed_effect.get('precision')}")
    
    # Check if transformation is correct
    has_all_fields = all([
        transformed_effect.get('effect_id'),
        transformed_effect.get('t0') is not None,
        transformed_effect.get('t1') is not None,
        transformed_effect.get('duration') is not None,
    ])
    
    if has_all_fields:
        print(f"\n✅ Transformation successful!")
        print(f"   Frontend will now receive all required fields")
    else:
        print(f"\n❌ Transformation incomplete!")
        missing = []
        if not transformed_effect.get('effect_id'):
            missing.append('effect_id')
        if transformed_effect.get('t0') is None:
            missing.append('t0')
        if transformed_effect.get('t1') is None:
            missing.append('t1')
        if transformed_effect.get('duration') is None:
            missing.append('duration')
        print(f"   Missing fields: {', '.join(missing)}")
    
    cur.close()
    conn.close()
    
    return has_all_fields

def main():
    print("🧪 Visual Effects Transformation Test\n")
    
    try:
        success = test_transformation()
        
        print("\n" + "=" * 80)
        print("RESULT")
        print("=" * 80)
        
        if success:
            print("✅ Backend transformation will work correctly")
            print("\n💡 Next steps:")
            print("   1. Test in browser with authenticated session")
            print("   2. Check browser console for VFX logs")
            print("   3. Verify effects are rendering on canvas")
        else:
            print("❌ Transformation logic needs adjustment")
            print("\n💡 Check:")
            print("   1. backend/app/main.py transformation code")
            print("   2. Database structure of visual_effects_manifest")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
