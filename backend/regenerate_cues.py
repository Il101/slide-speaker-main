#!/usr/bin/env python3
"""
Quick script to regenerate visual cues for existing lesson
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, '.')

from app.services.bullet_point_sync import BulletPointSyncService
from app.services.validation_engine import ValidationEngine

lesson_id = '2e57368c-d4c1-47e6-90ca-22c66665f724'
manifest_path = Path(f'../.data/{lesson_id}/manifest.json')

with open(manifest_path) as f:
    data = json.load(f)

print(f"🔧 Regenerating {len(data['slides'])} slides...")

sync = BulletPointSyncService()
validator = ValidationEngine()

updated = 0

for i, slide in enumerate(data['slides'], 1):
    try:
        slide_id = slide.get('id')
        duration = slide.get('duration', 0)
        elements = slide.get('elements', [])
        talk_track = slide.get('talk_track', [])
        semantic_map = slide.get('semantic_map', {})
        tts_words = slide.get('tts_words')  # ✅ Get word timings

        audio_full_path = Path(f'../.data/{lesson_id}/audio/{slide_id:03d}.wav')

        cues = sync.sync_bullet_points(
            audio_path=str(audio_full_path),
            talk_track_raw=talk_track,
            semantic_map=semantic_map,
            elements=elements,
            audio_duration=duration,
            tts_words=tts_words  # ✅ Pass word-level timing
        )

        if cues:
            cues, errors = validator.validate_cues(cues, duration, elements)

        slide['cues'] = cues
        slide['visual_cues'] = cues

        print(f"Slide {i}: {len(cues)} cues")
        updated += 1

    except Exception as e:
        print(f"Slide {i}: ❌ {e}")

with open(manifest_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Done: {updated} slides updated")
print(f"📁 Saved to: {manifest_path}")
