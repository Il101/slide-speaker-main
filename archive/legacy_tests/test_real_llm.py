#!/usr/bin/env python3
"""
Test script to verify real LLM is working (not mock mode)
Tests semantic analysis with actual Gemini API call
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

# Set environment to use Docker config
os.environ['LLM_PROVIDER'] = 'gemini'
os.environ['GCP_PROJECT_ID'] = 'inspiring-keel-473421-j2'
os.environ['GEMINI_LOCATION'] = 'europe-west1'
os.environ['GEMINI_MODEL'] = 'gemini-2.0-flash'

async def test_semantic_analyzer():
    """Test SemanticAnalyzer with real LLM"""
    from app.services.semantic_analyzer import SemanticAnalyzer
    
    print("=" * 60)
    print("Testing Semantic Analyzer with Real LLM")
    print("=" * 60)
    
    analyzer = SemanticAnalyzer()
    
    print(f"\n1. Configuration:")
    print(f"   Mock mode: {analyzer.use_mock}")
    print(f"   Backend: {analyzer.backend}")
    print(f"   Has LLM worker: {analyzer.llm_worker is not None}")
    
    if analyzer.use_mock:
        print("\n❌ ERROR: Still in mock mode!")
        return False
    
    print("\n✅ Real LLM configured!")
    
    # Test with real analysis
    print("\n2. Testing semantic analysis...")
    
    test_elements = [
        {
            'id': 'elem_1',
            'text': 'Machine Learning Basics',
            'type': 'heading',
            'bbox': [100, 50, 800, 100],
            'confidence': 0.95
        },
        {
            'id': 'elem_2',
            'text': '• Neural Networks',
            'type': 'list_item',
            'bbox': [150, 200, 600, 50],
            'confidence': 0.9
        },
        {
            'id': 'elem_3',
            'text': '• Deep Learning',
            'type': 'list_item',
            'bbox': [150, 270, 600, 50],
            'confidence': 0.9
        }
    ]
    
    presentation_context = {
        'topic': 'Machine Learning',
        'language': 'en',
        'total_slides': 1
    }
    
    try:
        # Find a real slide image (or use None for text-only test)
        test_image = None
        lesson_dir = Path('backend/.data/2d496931-6167-4c61-9793-6ad7c1ad857c')
        if lesson_dir.exists():
            test_image = str(lesson_dir / 'slides/001.png')
            if not Path(test_image).exists():
                test_image = None
        
        print(f"   Using image: {test_image if test_image else 'text-only mode'}")
        
        result = await analyzer.analyze_slide(
            slide_image_path=test_image or '/tmp/test.png',
            ocr_elements=test_elements,
            presentation_context=presentation_context,
            slide_index=0
        )
        
        print(f"\n3. Results:")
        print(f"   Groups found: {len(result.get('groups', []))}")
        print(f"   Has mock flag: {result.get('mock', False)}")
        
        if result.get('mock'):
            print("\n❌ Result has 'mock' flag - still using mock mode!")
            return False
        
        if result.get('groups'):
            first_group = result['groups'][0]
            print(f"\n   First group:")
            print(f"     ID: {first_group.get('id')}")
            print(f"     Type: {first_group.get('type')}")
            print(f"     Name: {first_group.get('name')}")
            print(f"     Priority: {first_group.get('priority')}")
            
            # Check for LLM-specific fields
            has_llm_fields = (
                'educational_intent' in first_group or
                'cognitive_load' in result or
                'name' in first_group  # Mock mode doesn't set name
            )
            
            if has_llm_fields:
                print("\n✅ SUCCESS: Real LLM analysis detected!")
                print("   (Contains LLM-specific fields)")
                return True
            else:
                print("\n⚠️ WARNING: Looks like mock results")
                print("   (Missing LLM-specific fields)")
                return False
        else:
            print("\n❌ No groups found!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_semantic_analyzer())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ REAL LLM IS WORKING!")
    else:
        print("❌ STILL IN MOCK MODE OR ERROR")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
