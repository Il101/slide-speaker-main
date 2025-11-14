"""
Test script to verify visual effects fix
Runs build_manifest on existing lesson to regenerate cues
"""
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app.pipeline.intelligent_optimized import OptimizedIntelligentPipeline

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_visual_effects():
    """Test visual effects generation on existing lesson"""
    
    # Use existing lesson with audio
    lesson_dir = "backend/.data/2d496931-6167-4c61-9793-6ad7c1ad857c"
    
    logger.info(f"Testing visual effects fix on {lesson_dir}")
    logger.info("=" * 60)
    
    # Create pipeline
    pipeline = OptimizedIntelligentPipeline()
    
    # Run build_manifest to regenerate cues
    try:
        logger.info("Running build_manifest to generate visual cues...")
        pipeline.build_manifest(lesson_dir)
        
        # Check results
        import json
        manifest_path = Path(lesson_dir) / "manifest.json"
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Verify first slide
        slide = manifest['slides'][0]
        
        logger.info("=" * 60)
        logger.info("RESULTS:")
        logger.info(f"  Duration: {slide.get('duration')} seconds")
        logger.info(f"  Semantic map: {'Yes' if slide.get('semantic_map') else 'No'}")
        logger.info(f"  Groups: {len(slide.get('semantic_map', {}).get('groups', []))}")
        logger.info(f"  Cues: {len(slide.get('cues', []))}")
        logger.info(f"  Visual cues: {len(slide.get('visual_cues', []))}")
        
        if slide.get('cues'):
            logger.info("\n  First 3 cues:")
            for i, cue in enumerate(slide['cues'][:3]):
                logger.info(f"    {i+1}. t0={cue.get('t0'):.2f}s, t1={cue.get('t1'):.2f}s, " 
                          f"action={cue.get('action')}, bbox={cue.get('bbox')[:2] if cue.get('bbox') else None}...")
        
        # Check if it worked
        if slide.get('duration') and len(slide.get('cues', [])) > 0:
            logger.info("\n✅ SUCCESS: Visual effects are now generated!")
        else:
            logger.warning("\n⚠️ WARNING: Visual effects still not generated properly")
            
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    success = test_visual_effects()
    sys.exit(0 if success else 1)
