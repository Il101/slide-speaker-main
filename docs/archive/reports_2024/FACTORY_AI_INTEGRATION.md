# Factory AI Integration - Complete Migration

## ✅ Completed Changes

### Overview
Successfully migrated **Intelligent Pipeline** from Google Gemini to **Factory AI** for all LLM operations.

---

## 🔄 Components Updated

### 1. **PresentationIntelligence** (`backend/app/services/presentation_intelligence.py`)

**Before:**
```python
import google.generativeai as genai
self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
response = self.model.generate_content(prompt)
```

**After:**
```python
from openai import OpenAI
self.client = OpenAI(
    base_url="https://api.factory.ai/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
response = self.client.chat.completions.create(
    model=os.getenv("OPENROUTER_MODEL", "gpt-4o-mini"),
    messages=[...]
)
```

**Purpose:** Global presentation context analysis (theme, level, language, structure)

---

### 2. **SemanticAnalyzer** (`backend/app/services/semantic_analyzer.py`)

**Before:**
```python
import google.generativeai as genai
self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = self.model.generate_content([prompt, img])
```

**After:**
```python
from openai import OpenAI
self.client = OpenAI(
    base_url="https://api.factory.ai/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
response = self.client.chat.completions.create(
    model=self.model,
    messages=[
        {"role": "system", "content": "..."},
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
        ]}
    ]
)
```

**Purpose:** Semantic grouping and visual analysis with multimodal support (text + image)

---

### 3. **SmartScriptGenerator** (`backend/app/services/smart_script_generator.py`)

**Before:**
```python
import google.generativeai as genai
self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
response = self.model.generate_content(prompt)
```

**After:**
```python
from openai import OpenAI
self.client = OpenAI(
    base_url="https://api.factory.ai/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
response = self.client.chat.completions.create(
    model=self.model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
)
```

**Purpose:** Context-aware script generation with anti-reading logic

---

## 🎯 Current Configuration

### Environment Variables (`docker.env`)
```env
# LLM Provider
LLM_PROVIDER=openrouter

# Factory AI Configuration
OPENROUTER_API_KEY=fk-k9Jp84eGpLE3QnibxIaB-UQeqw7tqg4w1I4oWuHtXi_nfjb4s_Wgn4xFJTyY54iQ
OPENROUTER_MODEL=gpt-4o-mini
OPENROUTER_BASE_URL=https://api.factory.ai/v1

# Language
LLM_LANGUAGE=ru
LLM_TEMPERATURE=0.2

# OCR (unchanged)
OCR_PROVIDER=vision  # Google Cloud Vision API

# TTS (unchanged)
TTS_PROVIDER=google  # Google Cloud TTS
```

---

## 📊 Architecture After Migration

```
Intelligent Pipeline:
├─ Stage 0: Presentation Intelligence
│  └─ Factory AI (gpt-4o-mini) ✅
│
├─ Stage 1: OCR
│  └─ Google Cloud Vision API ✅ (unchanged)
│
├─ Stage 2: Semantic Analysis  
│  └─ Factory AI (gpt-4o-mini) with vision ✅
│
├─ Stage 3: Script Generation
│  └─ Factory AI (gpt-4o-mini) ✅
│
├─ Stage 4: TTS
│  └─ Google Cloud TTS (Wavenet) ✅ (unchanged)
│
└─ Stage 5: Visual Effects + Validation
   └─ Logic-based (no LLM) ✅
```

---

## 🔧 Available Factory AI Models

### Recommended Models:

| Model | Cost | Quality | Speed | Best For |
|-------|------|---------|-------|----------|
| **gpt-4o-mini** ⭐ | $ | ⭐⭐⭐ | ⚡⚡⚡ | **Current, optimal balance** |
| gpt-4o | $$$ | ⭐⭐⭐⭐⭐ | ⚡⚡ | Maximum quality |
| claude-3.5-sonnet | $$ | ⭐⭐⭐⭐⭐ | ⚡⚡ | Best alternative |
| claude-3-haiku | $ | ⭐⭐⭐ | ⚡⚡⚡ | Fast & cheap |

To change model:
```env
OPENROUTER_MODEL=claude-3.5-sonnet
```

---

## ✅ Benefits of Migration

### 1. **Unified API Provider**
- All LLM operations through single Factory AI endpoint
- Consistent error handling and retry logic
- Simplified configuration

### 2. **Model Flexibility**
- Easy switching between models (GPT-4, Claude, Llama, etc.)
- No code changes needed, just config update
- Test different models for optimal cost/quality

### 3. **Cost Control**
- Centralized billing through Factory AI
- Usage tracking and limits
- Model-specific pricing optimization

### 4. **Better Language Support**
- Explicit language instructions in all prompts
- Forces translation from source language to target (`LLM_LANGUAGE=ru`)
- More reliable multilingual handling

---

## 🚀 Next Steps

### 1. Test the Pipeline
```bash
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main
docker-compose down
docker-compose up -d --build
```

### 2. Upload Test Presentation
- Upload a German presentation
- Verify text is generated in Russian
- Check all stages complete successfully

### 3. Monitor Performance
- Check Factory AI usage dashboard
- Compare quality vs Gemini (if needed)
- Adjust model if needed (gpt-4o for better quality)

### 4. (Optional) Fine-tune Prompts
- All prompts now in OpenAI format
- Can adjust system prompts for better results
- Test different temperature settings

---

## 📝 Notes

### Vision API Still Used
- **Google Cloud Vision API** remains for OCR
- Factory AI vision used for semantic analysis (different purpose)
- Both complement each other:
  - Vision API: Extract text from images
  - Factory AI vision: Understand slide structure

### Mock Mode Fallback
All components have mock mode if Factory AI key is missing:
```python
if not self.api_key:
    self.use_mock = True
    # Returns placeholder data for testing
```

### Backward Compatibility
- Classic Pipeline unchanged (already used Factory AI)
- Can still switch between pipelines via config
- `PIPELINE=classic` or `PIPELINE=intelligent`

---

## 🔍 Verification Checklist

- [x] PresentationIntelligence uses Factory AI
- [x] SemanticAnalyzer uses Factory AI with vision
- [x] SmartScriptGenerator uses Factory AI
- [x] Language prompts updated (translate to target language)
- [x] All error handling preserved
- [x] Mock mode fallback works
- [x] Configuration documented
- [ ] **TODO: Test with real presentation**
- [ ] **TODO: Verify multilingual support**

---

## 📞 Support

If issues occur:
1. Check Factory AI API key is valid
2. Verify `OPENROUTER_BASE_URL=https://api.factory.ai/v1`
3. Check model availability: `OPENROUTER_MODEL=gpt-4o-mini`
4. Review logs: `docker-compose logs backend`
5. Try mock mode for testing: remove `OPENROUTER_API_KEY` temporarily

---

**Migration completed on:** 2025-01-XX  
**Status:** ✅ Ready for testing
