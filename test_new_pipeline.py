#!/usr/bin/env python3
"""
Test script for new pipeline methods (ingest_v2 and extract_elements_ocr)
"""
import sys
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.pipeline.intelligent_optimized import OptimizedIntelligentPipeline
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_new_pipeline():
    """Test new pipeline methods with test_presentation.pptx"""
    
    # 1. Setup test directory
    test_dir = Path("/tmp/test_lesson_new_pipeline")
    
    # Clean up if exists
    if test_dir.exists():
        logger.info(f"Cleaning up existing test directory: {test_dir}")
        shutil.rmtree(test_dir)
    
    test_dir.mkdir(exist_ok=True)
    logger.info(f"✅ Created test directory: {test_dir}")
    
    # 2. Copy test PPTX
    test_pptx = Path("test_presentation.pptx")
    
    if not test_pptx.exists():
        logger.error(f"❌ Test PPTX not found: {test_pptx}")
        logger.info("Please create a test_presentation.pptx file in the project root")
        return False
    
    shutil.copy(test_pptx, test_dir / "test.pptx")
    logger.info(f"✅ Copied test PPTX to {test_dir}")
    
    # 3. Initialize pipeline
    pipeline = OptimizedIntelligentPipeline()
    logger.info("✅ Initialized OptimizedIntelligentPipeline")
    
    try:
        # 4. Test Stage 1: PPTX → PNG (ingest_v2)
        logger.info("\n" + "="*60)
        logger.info("Testing Stage 1: ingest_v2() - PPTX → PNG")
        logger.info("="*60)
        
        pipeline.ingest_v2(str(test_dir))
        
        # Verify PNG files created
        slides_dir = test_dir / "slides"
        if not slides_dir.exists():
            raise AssertionError("Slides directory not created!")
        
        png_files = list(slides_dir.glob("*.png"))
        if not png_files:
            raise AssertionError("No PNG files created!")
        
        logger.info(f"✅ ingest_v2() SUCCESS: Created {len(png_files)} PNG files")
        
        # Verify manifest created
        manifest_path = test_dir / "manifest.json"
        if not manifest_path.exists():
            raise AssertionError("Manifest not created!")
        
        import json
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        assert "slides" in manifest, "Manifest missing 'slides' key"
        assert len(manifest["slides"]) == len(png_files), "Slide count mismatch"
        
        logger.info(f"✅ Manifest created with {len(manifest['slides'])} slides")
        
        # 5. Test Stage 2: OCR (extract_elements_ocr)
        logger.info("\n" + "="*60)
        logger.info("Testing Stage 2: extract_elements_ocr() - OCR extraction")
        logger.info("="*60)
        
        pipeline.extract_elements_ocr(str(test_dir))
        
        # Verify elements added to manifest
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        for slide in manifest["slides"]:
            if "elements" not in slide:
                raise AssertionError(f"Slide {slide['id']} missing 'elements' key")
            
            elements_count = len(slide.get("elements", []))
            logger.info(f"  Slide {slide['id']}: {elements_count} elements")
        
        total_elements = sum(len(s.get("elements", [])) for s in manifest["slides"])
        logger.info(f"✅ extract_elements_ocr() SUCCESS: Extracted {total_elements} total elements")
        
        # 6. Test rest of pipeline (optional - may take time)
        run_full_test = input("\n🤔 Run full pipeline test (plan + tts + build_manifest)? [y/N]: ").lower() == 'y'
        
        if run_full_test:
            logger.info("\n" + "="*60)
            logger.info("Testing Stage 3-8: Full pipeline")
            logger.info("="*60)
            
            pipeline.plan(str(test_dir))
            logger.info("✅ plan() completed")
            
            pipeline.tts(str(test_dir))
            logger.info("✅ tts() completed")
            
            pipeline.build_manifest(str(test_dir))
            logger.info("✅ build_manifest() completed")
            
            # Verify final manifest
            with open(manifest_path, "r") as f:
                final_manifest = json.load(f)
            
            # Check for speaker_notes, audio, cues
            for slide in final_manifest["slides"]:
                assert "speaker_notes" in slide, f"Slide {slide['id']} missing speaker_notes"
                assert "audio" in slide, f"Slide {slide['id']} missing audio"
                assert "cues" in slide, f"Slide {slide['id']} missing cues"
            
            logger.info("✅ Full pipeline test PASSED!")
        
        # 7. Summary
        logger.info("\n" + "="*60)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("="*60)
        logger.info(f"\nTest directory: {test_dir}")
        logger.info(f"PNG slides: {len(png_files)}")
        logger.info(f"Total OCR elements: {total_elements}")
        logger.info(f"\nYou can inspect the results at: {test_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting NEW pipeline methods test")
    logger.info("Testing: ingest_v2() and extract_elements_ocr()")
    logger.info("")
    
    success = test_new_pipeline()
    
    if success:
        logger.info("\n🎉 New pipeline methods are working!")
        sys.exit(0)
    else:
        logger.error("\n💥 Tests failed - check logs above")
        sys.exit(1)
