# 📊 Pipeline Flow Diagram

## 🎬 От PPTX к Интерактивной Лекции

```
┌─────────────────────────────────────────────────────────────────┐
│                     UPLOAD PRESENTATION                         │
│                    presentation.pptx                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  MAIN.PY: PRE-PROCESSING                        │
│  • Convert PPTX → PNG images                                    │
│  • Extract OCR (text + coordinates)                             │
│  • Create initial manifest.json                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 1: INGEST (0.1s)                            │
│  • Validate manifest.json exists                                │
│  • Count slides                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│         STAGE 0: PRESENTATION CONTEXT (2-3s)                    │
│  📊 PresentationIntelligence.analyze_presentation()             │
│                                                                 │
│  Input: All slides                                              │
│  Output: {                                                      │
│    "theme": "Биология растений",                               │
│    "level": "undergraduate",                                    │
│    "style": "academic"                                          │
│  }                                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│     STAGE 2-3: PLAN - Parallel Processing (12s for 15 slides)  │
│                                                                 │
│  ⚡ Up to 5 slides processed in parallel                        │
│                                                                 │
│  For each slide:                                                │
│  ┌────────────────────────────────────────────────────┐        │
│  │  STAGE 2: SEMANTIC ANALYSIS (3-4s)                 │        │
│  │  🔍 SemanticAnalyzer.analyze_slide()               │        │
│  │                                                     │        │
│  │  Input:                                             │        │
│  │  • Slide image (PNG)                                │        │
│  │  • OCR elements                                     │        │
│  │  • Presentation context                             │        │
│  │  • Previous slides                                  │        │
│  │                                                     │        │
│  │  LLM: Gemini Vision API                             │        │
│  │                                                     │        │
│  │  Output: semantic_map {                             │        │
│  │    "groups": [                                      │        │
│  │      {                                              │        │
│  │        "id": "group_0",                             │        │
│  │        "name": "Title",                             │        │
│  │        "type": "title",                             │        │
│  │        "priority": "high",                          │        │
│  │        "element_ids": ["slide_1_block_0"],          │        │
│  │        "highlight_strategy": {                      │        │
│  │          "when": "start",                           │        │
│  │          "effect_type": "spotlight"                 │        │
│  │        }                                            │        │
│  │      }                                              │        │
│  │    ]                                                │        │
│  │  }                                                  │        │
│  └────────────────────────────────────────────────────┘        │
│                         │                                        │
│                         ↓                                        │
│  ┌────────────────────────────────────────────────────┐        │
│  │  STAGE 3: SCRIPT GENERATION (2-3s)                 │        │
│  │  📝 SmartScriptGenerator.generate_script()         │        │
│  │                                                     │        │
│  │  Input:                                             │        │
│  │  • semantic_map                                     │        │
│  │  • elements                                         │        │
│  │  • presentation_context                             │        │
│  │  • previous_slides_summary                          │        │
│  │                                                     │        │
│  │  LLM: Gemini Text API                               │        │
│  │                                                     │        │
│  │  Output: {                                          │        │
│  │    "talk_track": [                                  │        │
│  │      {"segment": "hook", "text": "..."},            │        │
│  │      {"segment": "context", "text": "..."},         │        │
│  │      {"segment": "explanation", "text": "..."},     │        │
│  │      {"segment": "example", "text": "..."},         │        │
│  │      {"segment": "emphasis", "text": "..."},        │        │
│  │      {"segment": "transition", "text": "..."}       │        │
│  │    ],                                               │        │
│  │    "speaker_notes": "Full text...",                 │        │
│  │    "estimated_duration": 45                         │        │
│  │  }                                                  │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│     STAGE 4: TTS - Parallel Generation (10s for 15 slides)     │
│                                                                 │
│  ⚡ Up to 10 slides processed in parallel                       │
│                                                                 │
│  For each slide:                                                │
│  ┌────────────────────────────────────────────────────┐        │
│  │  SSML GENERATION (0.1s)                            │        │
│  │  🎨 SSMLGenerator.generate_ssml()                  │        │
│  │                                                     │        │
│  │  Input: talk_track segments                         │        │
│  │                                                     │        │
│  │  Output: SSML with <mark> tags                      │        │
│  │  <speak>                                            │        │
│  │    <prosody rate="medium" pitch="+2st">             │        │
│  │      <mark name="mark_0"/>Willkommen                │        │
│  │      <mark name="mark_1"/>zum                       │        │
│  │      <mark name="mark_2"/>ersten                    │        │
│  │    </prosody>                                       │        │
│  │  </speak>                                           │        │
│  └────────────────────────────────────────────────────┘        │
│                         │                                        │
│                         ↓                                        │
│  ┌────────────────────────────────────────────────────┐        │
│  │  TTS SYNTHESIS (4-6s)                              │        │
│  │  🎙️ GoogleTTSWorkerSSML                            │        │
│  │                                                     │        │
│  │  API: Google Cloud TTS v1beta1                      │        │
│  │  Voice: ru-RU-Wavenet-D (configurable)             │        │
│  │                                                     │        │
│  │  Output: {                                          │        │
│  │    "audio": "path/to/001.wav",                      │        │
│  │    "sentences": [                                   │        │
│  │      {"text": "...", "t0": 0.0, "t1": 2.5}          │        │
│  │    ],                                               │        │
│  │    "word_timings": [                                │        │
│  │      {"mark_name": "mark_0", "time_seconds": 0.34}, │        │
│  │      {"mark_name": "mark_1", "time_seconds": 0.82}, │        │
│  │      {"mark_name": "mark_2", "time_seconds": 1.15}  │        │
│  │    ]                                                │        │
│  │  }                                                  │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│        STAGE 5-8: BUILD MANIFEST (3s for 15 slides)            │
│                                                                 │
│  For each slide:                                                │
│  ┌────────────────────────────────────────────────────┐        │
│  │  STAGE 5: VISUAL EFFECTS (0.2s)                    │        │
│  │  ✨ VisualEffectsEngine.generate_cues()            │        │
│  │                                                     │        │
│  │  Input:                                             │        │
│  │  • semantic_map (groups + strategies)               │        │
│  │  • elements (OCR data)                              │        │
│  │  • duration (audio length)                          │        │
│  │  • word_timings (from TTS)                          │        │
│  │                                                     │        │
│  │  Algorithm:                                         │        │
│  │  1. Extract word_timings                            │        │
│  │  2. For each group:                                 │        │
│  │     - Get group text                                │        │
│  │     - Find when text is spoken (TTS sync)           │        │
│  │     - Generate cue with exact timing                │        │
│  │                                                     │        │
│  │  Output: [                                          │        │
│  │    {                                                │        │
│  │      "cue_id": "cue_abc123",                        │        │
│  │      "t0": 0.34,  ← Synced with TTS!                │        │
│  │      "t1": 1.67,                                    │        │
│  │      "action": "spotlight",                         │        │
│  │      "element_id": "slide_1_block_0",               │        │
│  │      "bbox": [588, 97, 265, 47]                     │        │
│  │    }                                                │        │
│  │  ]                                                  │        │
│  └────────────────────────────────────────────────────┘        │
│                         │                                        │
│                         ↓                                        │
│  ┌────────────────────────────────────────────────────┐        │
│  │  STAGE 6: VALIDATION (0.1s)                        │        │
│  │  ✅ ValidationEngine.validate_cues()               │        │
│  │                                                     │        │
│  │  Checks:                                            │        │
│  │  • t1 > t0                                          │        │
│  │  • No overlaps                                      │        │
│  │  • element_id exists                                │        │
│  │  • bbox is valid                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                         │                                        │
│                         ↓                                        │
│  ┌────────────────────────────────────────────────────┐        │
│  │  STAGE 8: TIMELINE (0.1s)                          │        │
│  │  📅 Build presentation timeline                     │        │
│  │                                                     │        │
│  │  Output: [                                          │        │
│  │    {                                                │        │
│  │      "t0": 0.0,                                     │        │
│  │      "t1": 29.376,                                  │        │
│  │      "action": "slide_change",                      │        │
│  │      "slide_id": 1                                  │        │
│  │    },                                               │        │
│  │    ...                                              │        │
│  │  ]                                                  │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                   FINAL MANIFEST.JSON                           │
│                                                                 │
│  {                                                              │
│    "presentation_context": {...},                              │
│    "slides": [                                                 │
│      {                                                         │
│        "id": 1,                                                │
│        "image": "/assets/.../001.png",                         │
│        "audio": "/assets/.../001.wav",                         │
│        "duration": 29.376,                                     │
│        "elements": [...],                                      │
│        "semantic_map": {...},                                  │
│        "talk_track": [...],                                    │
│        "cues": [...]                                           │
│      }                                                         │
│    ],                                                          │
│    "timeline": [...]                                           │
│  }                                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND PLAYER                              │
│  🎬 Interactive Lecture Playback                                │
│                                                                 │
│  • Shows slides with synchronized audio                         │
│  • Visual effects appear when words are spoken                  │
│  • Smooth transitions between slides                            │
│  • Total duration: ~7 minutes (for 15 slides)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⏱️ Performance Summary (15 slides)

| Stage | Sequential | Parallel | Speedup |
|-------|-----------|----------|---------|
| **Ingest** | 0.1s | 0.1s | 1x |
| **Plan** (Stage 2-3) | 45s | 12s | **3.75x** |
| **TTS** (Stage 4) | 75s | 10s | **7.5x** |
| **Build** (Stage 5-8) | 3s | 3s | 1x |
| **TOTAL** | **123s** | **25s** | **4.9x** |

---

## 🎯 Key Features

### 🧠 Semantic-Driven
- Analyzes **meaning**, not just text
- Groups logically related elements
- Determines what's important

### 🎓 Pedagogically Structured
- 6-segment talk_track (hook → transition)
- Maintains context between slides
- Natural lecture flow

### 🎙️ Word-Level Timing
- SSML with `<mark>` tags
- Accuracy: ±0.1-0.3 seconds
- Synchronization: 90-95%

### ⚡ High Performance
- Parallel slide processing (5x)
- Parallel TTS generation (10x)
- OCR caching in Redis

---

## 📦 Output Files

```
.data/{uuid}/
├── manifest.json        (Complete metadata)
├── slides/
│   ├── 001.png         (Slide images)
│   ├── 002.png
│   └── ...
└── audio/
    ├── 001.wav         (Audio with word timing)
    ├── 002.wav
    └── ...
```

**Total size:** ~5-10 MB for 15 slides
**Processing time:** ~25 seconds
