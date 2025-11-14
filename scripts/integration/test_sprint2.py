#!/usr/bin/env python3
"""
Smoke test for Sprint 2 functionality
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.workers.plan_llm import LLMWorker, generate_notes_for_slide
from backend.workers.tts_edge import TTSEdgeWorker, generate_slide_audio
from backend.align import TimelineAligner, align_lesson_slide

async def test_llm_worker():
    """Test LLM worker functionality"""
    print("Testing LLM Worker...")
    
    test_content = {
        "elements": [
            {"id": "elem_1", "type": "text", "text": "Welcome to our presentation", "bbox": [100, 100, 400, 50]},
            {"id": "elem_2", "type": "text", "text": "Today we will discuss AI technology", "bbox": [100, 200, 400, 50]}
        ]
    }
    
    try:
        # Test without actual LLM endpoint (will use fallback)
        async with LLMWorker() as worker:
            notes = await worker.generate_speaker_notes(test_content)
            print(f"✓ Generated speaker notes: {len(notes)} characters")
            
            analysis = await worker.analyze_slide_content(test_content)
            print(f"✓ Analyzed slide content: {len(analysis.get('key_concepts', []))} concepts")
            
            cues = await worker.generate_timing_cues(notes, analysis)
            print(f"✓ Generated timing cues: {len(cues)} cues")
            
        return True
    except Exception as e:
        print(f"✗ LLM Worker test failed: {e}")
        return False

async def test_tts_worker():
    """Test TTS worker functionality"""
    print("\nTesting TTS Worker...")
    
    test_notes = "Welcome to our presentation about artificial intelligence."
    test_elements = [
        {"id": "elem_1", "type": "text", "text": "Artificial Intelligence", "bbox": [100, 100, 400, 50]},
        {"id": "elem_2", "type": "text", "text": "Machine Learning", "bbox": [100, 200, 400, 50]}
    ]
    
    try:
        # Test without actual TTS endpoint (will use fallback)
        async with TTSEdgeWorker() as worker:
            audio_data, timings, mapping = await worker.generate_audio_for_slide(
                test_notes, test_elements
            )
            print(f"✓ Generated audio: {len(audio_data)} bytes")
            print(f"✓ Sentence timings: {len(timings)} segments")
            print(f"✓ Element mapping: {len(mapping)} mappings")
            
        return True
    except Exception as e:
        print(f"✗ TTS Worker test failed: {e}")
        return False

def test_aligner():
    """Test timeline aligner functionality"""
    print("\nTesting Timeline Aligner...")
    
    test_notes = "Welcome to our presentation. Today we will discuss AI technology."
    test_timings = [
        {"sentence": "Welcome to our presentation.", "t0": 0.0, "t1": 2.5, "duration": 2.5, "index": 0},
        {"sentence": "Today we will discuss AI technology.", "t0": 2.8, "t1": 6.0, "duration": 3.2, "index": 1}
    ]
    test_elements = [
        {"id": "elem_1", "type": "text", "text": "Welcome to our presentation", "bbox": [100, 100, 400, 50]},
        {"id": "elem_2", "type": "text", "text": "AI technology", "bbox": [100, 200, 300, 50]}
    ]
    
    try:
        aligner = TimelineAligner()
        result = aligner.align_slide_content(test_notes, test_timings, test_elements)
        
        print(f"✓ Aligned cues: {len(result['cues'])}")
        print(f"✓ Total duration: {result['total_duration']:.2f}s")
        print(f"✓ Coverage ratio: {result['metadata']['coverage_ratio']:.2f}")
        
        # Test validation
        validation = aligner.validate_alignment(result)
        print(f"✓ Validation: {'Valid' if validation['valid'] else 'Issues found'}")
        
        return True
    except Exception as e:
        print(f"✗ Timeline Aligner test failed: {e}")
        return False

def test_timeline_rules():
    """Test timeline rules validation"""
    print("\nTesting Timeline Rules...")
    
    # Test manifest with timeline rules
    test_manifest = {
        "slides": [
            {
                "id": 1,
                "cues": [
                    {"t0": 0.0, "t1": 0.5, "action": "highlight", "bbox": [100, 100, 200, 50]},  # Too short
                    {"t0": 0.6, "t1": 2.0, "action": "highlight", "bbox": [100, 200, 200, 50]}   # Valid
                ]
            }
        ],
        "timeline": {
            "min_highlight_duration": 0.8,
            "min_gap": 0.2,
            "smoothness_enabled": True
        }
    }
    
    try:
        # Import validation function from app.main
        sys.path.append(str(Path(__file__).parent / "backend"))
        from app.main import _validate_timeline_smoothness
        
        issues = _validate_timeline_smoothness(test_manifest)
        print(f"✓ Found {len(issues)} timeline issues")
        for issue in issues:
            print(f"  - {issue}")
        
        return True
    except Exception as e:
        print(f"✗ Timeline Rules test failed: {e}")
        return False

async def test_integration():
    """Test integration of all components"""
    print("\nTesting Integration...")
    
    try:
        # Simulate complete workflow
        lesson_id = "test-lesson"
        slide_id = 1
        
        slide_content = {
            "elements": [
                {"id": "elem_1", "type": "text", "text": "Introduction to AI", "bbox": [100, 100, 400, 50]},
                {"id": "elem_2", "type": "text", "text": "Machine Learning Basics", "bbox": [100, 200, 400, 50]}
            ]
        }
        
        # Step 1: Generate notes
        notes_result = await generate_notes_for_slide(lesson_id, slide_id, slide_content)
        print(f"✓ Generated notes: {len(notes_result['speaker_notes'])} chars")
        
        # Step 2: Generate audio
        audio_result = await generate_slide_audio(
            lesson_id, slide_id, 
            notes_result['speaker_notes'], 
            slide_content['elements']
        )
        print(f"✓ Generated audio: {audio_result['total_duration']:.2f}s")
        
        # Step 3: Align content
        alignment_result = align_lesson_slide(
            lesson_id, slide_id,
            notes_result['speaker_notes'],
            audio_result['sentence_timings'],
            slide_content['elements']
        )
        print(f"✓ Aligned content: {len(alignment_result['cues'])} cues")
        
        return True
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Sprint 2 Smoke Test\n")
    
    tests = [
        ("LLM Worker", test_llm_worker()),
        ("TTS Worker", test_tts_worker()),
        ("Timeline Aligner", test_aligner()),
        ("Timeline Rules", test_timeline_rules()),
        ("Integration", test_integration())
    ]
    
    results = []
    for name, test in tests:
        if asyncio.iscoroutine(test):
            result = await test
        else:
            result = test
        results.append((name, result))
    
    print("\n" + "="*50)
    print("📊 Test Results:")
    print("="*50)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Sprint 2 implementation is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)