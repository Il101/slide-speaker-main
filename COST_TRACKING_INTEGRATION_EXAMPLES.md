# Cost Tracking Integration Examples

This document shows how to integrate cost tracking into your pipeline code.

## 1. Import Cost Tracker

Add to the top of your pipeline file:

```python
from app.services.cost_tracker import (
    track_ocr_cost,
    track_ai_generation_cost,
    track_tts_cost
)
```

## 2. Track OCR Costs

In `backend/app/pipeline/intelligent_optimized.py` or wherever OCR happens:

```python
async def process_presentation(self, pptx_path: str, user_id: str = None, lesson_id: str = None):
    """Process presentation with cost tracking"""
    
    # ... existing OCR code ...
    slide_count = len(slides)
    
    # Track OCR cost
    if self.db:  # If database session available
        await track_ocr_cost(
            db=self.db,
            slide_count=slide_count,
            user_id=user_id,
            lesson_id=lesson_id,
            file_name=Path(pptx_path).name
        )
```

## 3. Track AI Generation Costs

When generating scripts/content:

```python
async def generate_script(self, slide_data: dict, user_id: str = None, lesson_id: str = None):
    """Generate script with cost tracking"""
    
    # ... existing AI generation code ...
    response = await self.ai_client.generate(prompt, model="gemini-1.5-flash")
    
    # Track AI cost
    if self.db and hasattr(response, 'usage'):
        await track_ai_generation_cost(
            db=self.db,
            model="gemini-1.5-flash",
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            user_id=user_id,
            lesson_id=lesson_id,
            slide_number=slide_data.get('slide_number')
        )
    
    return script
```

## 4. Track TTS Costs

When generating audio:

```python
async def generate_audio(self, text: str, slide_id: int, user_id: str = None, lesson_id: str = None):
    """Generate TTS audio with cost tracking"""
    
    # ... existing TTS code ...
    audio_data = await synthesize_slide_text_google(
        text=text,
        voice="en-US-Neural2-F"
    )
    
    # Track TTS cost
    if self.db:
        await track_tts_cost(
            db=self.db,
            character_count=len(text),
            voice="neural2-en-US",  # or extract from config
            user_id=user_id,
            lesson_id=lesson_id,
            slide_number=slide_id
        )
    
    return audio_data
```

## 5. Complete Pipeline Integration Example

Here's how to integrate into `OptimizedIntelligentPipeline`:

```python
# In intelligent_optimized.py

class OptimizedIntelligentPipeline(BasePipeline):
    def __init__(self, db_session=None, **kwargs):
        super().__init__(**kwargs)
        self.db = db_session  # Store DB session for cost tracking
        # ... rest of init ...
    
    async def process(
        self,
        pptx_path: str,
        output_dir: str,
        user_id: str = None,
        lesson_id: str = None,
        progress_callback=None
    ):
        """Process with cost tracking"""
        
        # Stage 1: OCR
        self.logger.info("Stage 1: OCR Processing...")
        slides = await self._extract_slides(pptx_path)
        
        # Track OCR cost
        if self.db:
            from app.services.cost_tracker import track_ocr_cost
            await track_ocr_cost(
                db=self.db,
                slide_count=len(slides),
                user_id=user_id,
                lesson_id=lesson_id,
                file_name=Path(pptx_path).name
            )
        
        # Stage 2-3: AI Generation (per slide)
        for slide in slides:
            # Generate script
            script = await self._generate_script(slide)
            
            # Track AI cost (if response has token counts)
            if self.db and hasattr(script, '_token_usage'):
                from app.services.cost_tracker import track_ai_generation_cost
                await track_ai_generation_cost(
                    db=self.db,
                    model="gemini-1.5-flash",
                    input_tokens=script._token_usage['input'],
                    output_tokens=script._token_usage['output'],
                    user_id=user_id,
                    lesson_id=lesson_id,
                    slide_number=slide['id']
                )
        
        # Stage 4: TTS Generation
        for slide in slides:
            text = slide.get('lecture_text', '')
            audio = await self._generate_audio(text)
            
            # Track TTS cost
            if self.db:
                from app.services.cost_tracker import track_tts_cost
                await track_tts_cost(
                    db=self.db,
                    character_count=len(text),
                    voice="neural2",  # or from config
                    user_id=user_id,
                    lesson_id=lesson_id,
                    slide_number=slide['id']
                )
        
        return manifest
```

## 6. Integration in API Endpoint

In `backend/app/api/v2_lecture.py` or similar:

```python
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.post("/process")
async def process_presentation(
    file: UploadFile = File(...),
    user_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Process presentation with cost tracking"""
    
    # Save file
    temp_path = await save_upload(file)
    
    # Create lesson record
    lesson_id = str(uuid.uuid4())
    
    # Initialize pipeline with DB session
    pipeline = OptimizedIntelligentPipeline(db_session=db)
    
    # Process (cost tracking happens automatically inside)
    result = await pipeline.process(
        pptx_path=temp_path,
        output_dir=output_dir,
        user_id=user_id,
        lesson_id=lesson_id
    )
    
    return {"lesson_id": lesson_id, "status": "processing"}
```

## 7. Alternative: Use Context Manager

For automatic cost tracking:

```python
from app.services.cost_tracker import CostTracker

async def process_slide(self, slide_data, user_id, lesson_id):
    """Process slide with automatic cost tracking"""
    
    # AI Generation with auto-tracking
    async with CostTracker(self.db, "ai_generation", user_id, lesson_id) as tracker:
        response = await generate_script(slide_data)
        
        # Add metadata for cost calculation
        tracker.add_metadata(
            model="gemini-1.5-flash",
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            slide_number=slide_data['id']
        )
        # Cost is automatically tracked on exit
    
    return response
```

## 8. Key Integration Points

### Where to Track OCR Costs
- `backend/app/services/sprint1/document_parser.py`
- After calling Google Vision API or any OCR service
- Track once per presentation (total slides)

### Where to Track AI Costs
- `backend/app/services/smart_script_generator.py`
- `backend/app/services/semantic_analyzer.py`
- After each AI model call (Gemini, OpenAI, etc.)
- Track per slide or per API call

### Where to Track TTS Costs
- `backend/app/services/provider_factory.py` (in `synthesize_slide_text_google`)
- After each TTS API call
- Track per slide

### Where to Track Storage Costs
- When uploading final video to GCS
- After saving presentation files
- Monthly aggregation possible

## 9. Testing Cost Tracking

Test your integration:

```python
# Test OCR tracking
async def test_ocr_tracking():
    from app.core.database import AsyncSessionLocal
    from app.services.cost_tracker import track_ocr_cost
    
    async with AsyncSessionLocal() as db:
        await track_ocr_cost(
            db=db,
            slide_count=20,
            user_id="test-user-123",
            lesson_id="test-lesson-456",
            file_name="presentation.pptx"
        )
        await db.commit()
    
    # Check database
    # SELECT * FROM cost_logs ORDER BY timestamp DESC LIMIT 1;
    print("✅ Cost tracking test passed")
```

## 10. Monitoring Costs

Query costs from the database:

```sql
-- Total costs today
SELECT 
    operation,
    SUM(cost) as total_cost,
    COUNT(*) as operations_count
FROM cost_logs
WHERE DATE(timestamp) = CURRENT_DATE
GROUP BY operation;

-- Cost per user
SELECT 
    user_id,
    SUM(cost) as total_cost
FROM cost_logs
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY user_id
ORDER BY total_cost DESC
LIMIT 10;

-- Average cost per lecture
SELECT 
    AVG(total_cost) as avg_cost_per_lecture
FROM (
    SELECT 
        lesson_id,
        SUM(cost) as total_cost
    FROM cost_logs
    WHERE lesson_id IS NOT NULL
    GROUP BY lesson_id
) subquery;
```

## 11. Best Practices

1. **Always pass user_id and lesson_id** when available
2. **Track costs immediately after API calls** (don't wait)
3. **Don't let tracking failures break the pipeline** (use try-except)
4. **Add metadata for debugging** (model names, token counts, etc.)
5. **Test in staging first** before production
6. **Monitor costs daily** to catch anomalies early
7. **Set up alerts** for unusual cost spikes

## 12. Troubleshooting

### Costs not appearing in database
- Check if DB session is passed to pipeline
- Verify migration ran successfully
- Check backend logs for errors
- Ensure `await db.commit()` is called

### Token counts not available
- Some APIs don't return usage data
- Fall back to estimating: `tokens ≈ len(text) / 4`
- Log warning when estimation is used

### Performance impact
- Cost tracking adds ~10ms per call (negligible)
- Use async functions to avoid blocking
- Batch multiple cost logs if needed

---

**Ready to integrate?** Start with OCR tracking (easiest), then add AI and TTS tracking gradually.
