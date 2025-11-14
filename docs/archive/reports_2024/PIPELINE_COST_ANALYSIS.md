# Pipeline Cost Analysis - Slide Processing

## Pricing Data (2025)

### Google Cloud Services
- **Vision API (OCR)**: 
  - First 1,000 pages/month: **FREE**
  - 1K - 5M pages: **$1.50 per 1,000 pages**
  - Over 5M pages: **$0.60 per 1,000 pages**

- **Text-to-Speech (Wavenet)**:
  - Standard voices: **$16 per 1M characters**
  - WaveNet/Neural2: **$16 per 1M characters**
  - ~150 words per slide = ~750 chars = **$0.012 per slide**

### LLM Providers

#### OpenRouter (via OpenAI/Anthropic)
- **gpt-4o-mini**:
  - Input: **$0.15 per 1M tokens**
  - Output: **$0.60 per 1M tokens**
  - Vision support: ✅

- **claude-3.5-sonnet**:
  - Input: **$3.00 per 1M tokens**
  - Output: **$15.00 per 1M tokens**
  - Vision support: ✅

#### Google Gemini (Free Tier)
- **gemini-2.0-flash-exp**:
  - First 50 requests/day: **FREE**
  - Then: quota exceeded
  - Vision support: ✅

---

## Pipeline Comparison

### **Classic Pipeline** (Simple)
```
OCR → LLM (text only) → TTS → Visual Effects
```

**Per Slide Costs:**
1. **OCR (Vision API)**: $0.0015 per slide
2. **LLM Call** (1x per slide):
   - Input: ~500 tokens (OCR elements)
   - Output: ~200 tokens (speaker notes)
   - **gpt-4o-mini**: $0.00019
   - **claude-3.5**: $0.00450
3. **TTS**: $0.012 per slide
4. **Total per slide**:
   - With gpt-4o-mini: **$0.01369** (~**$0.014**)
   - With claude-3.5: **$0.01819** (~**$0.018**)

**For 100 slides:**
- gpt-4o-mini: **$1.37**
- claude-3.5: **$1.82**

---

### **Intelligent Pipeline** (Advanced with Vision)
```
Stage 0: Presentation Analysis (1x per presentation)
Stage 2: Semantic Analysis with Vision (1x per slide)  ← VISION
Stage 3: Script Generation (1x per slide, with retries)
TTS + Visual Effects
```

**Per Presentation (one-time):**
1. **Stage 0: Presentation Intelligence**
   - Input: ~1000 tokens (all slides summary)
   - Output: ~500 tokens (context JSON)
   - **gpt-4o-mini**: $0.00045
   - **claude-3.5**: $0.01050

**Per Slide:**
2. **Stage 2: Semantic Analysis (with Vision)**
   - Input: ~800 tokens (OCR + prompt) + **IMAGE** (base64)
   - Image tokens: ~1500 tokens equivalent
   - Output: ~800 tokens (semantic map JSON)
   - Total input: ~2300 tokens
   - **gpt-4o-mini**: $0.00083
   - **claude-3.5**: $0.01890

3. **Stage 3: Script Generation**
   - Input: ~1200 tokens (semantic map + context)
   - Output: ~600 tokens (script JSON)
   - Retries: up to 3x for anti-reading check
   - Average: 1.5x calls
   - **gpt-4o-mini**: $0.00072 × 1.5 = $0.00108
   - **claude-3.5**: $0.01650 × 1.5 = $0.02475

4. **OCR**: $0.0015 per slide

5. **TTS**: $0.012 per slide

**Total per slide (Intelligent):**
- **gpt-4o-mini**: $0.01541 (~**$0.015**)
- **claude-3.5**: $0.04515 (~**$0.045**)

**For 100 slides:**
- **gpt-4o-mini**: 
  - Stage 0: $0.00045
  - 100 slides: $1.54
  - **Total: $1.54**

- **claude-3.5**: 
  - Stage 0: $0.01
  - 100 slides: $4.51
  - **Total: $4.52**

---

## Cost Comparison Table

| Configuration | 10 slides | 100 slides | 1,000 slides |
|--------------|-----------|------------|--------------|
| **Classic + gpt-4o-mini** | $0.14 | $1.37 | $13.69 |
| **Classic + claude-3.5** | $0.18 | $1.82 | $18.19 |
| **Intelligent + gpt-4o-mini** | $0.15 | $1.54 | $15.41 |
| **Intelligent + claude-3.5** | $0.45 | $4.52 | $45.15 |
| **Gemini Free (50/day)** | FREE | FREE | quota limit |

---

## Optimization Strategies

### 1. **Hybrid Approach** (Best Value)
```
- Use Gemini for Stages 0-3 (50 slides/day free)
- After quota: switch to gpt-4o-mini
- Cost: ~$0.77 per 100 slides (50 free + 50 paid)
```

### 2. **No-Vision Mode** (Cheapest)
```
- Disable Semantic Analyzer vision
- Use only text-based analysis
- Same as Classic Pipeline
- Cost: $1.37 per 100 slides (gpt-4o-mini)
```

### 3. **Premium Quality** 
```
- Use claude-3.5-sonnet for all stages
- Best quality semantic analysis
- Cost: $4.52 per 100 slides
```

### 4. **Batch Processing**
```
- Process <50 slides/day with Gemini
- Wait for quota refresh
- Cost: FREE (unlimited over time)
```

---

## Key Insights

### Vision Cost Impact
- **Classic Pipeline**: No vision = cheaper
- **Intelligent + Vision**: +$0.17 per slide (~12% more expensive)
- Vision adds: Better semantic grouping, understands layout

### Model Selection
- **gpt-4o-mini**: Best value ($0.015/slide)
- **claude-3.5**: 3x more expensive but better quality
- **Gemini free**: Best for <50 slides/day

### Scale Economics
- 10 slides: Differences negligible ($0.01-0.30)
- 100 slides: **gpt-4o-mini recommended** ($1.54)
- 1000 slides: **Batch with Gemini** or gpt-4o-mini ($15)

---

## Recommendations by Use Case

### **Testing/Development** (< 50 slides/day)
✅ **Use Gemini Free Tier**
- Cost: **$0.00**
- Quality: Excellent
- Limit: 50 requests/day

### **Production (Low Volume)** (< 500 slides/month)
✅ **Intelligent Pipeline + gpt-4o-mini**
- Cost: **~$7.70/month**
- Quality: Very good
- Vision: ✅

### **Production (High Volume)** (> 1000 slides/month)
✅ **Classic Pipeline + gpt-4o-mini**
- Cost: **~$13.69/month** (1000 slides)
- Quality: Good
- Vision: ❌ (saves 12%)

### **Premium Quality** (Any volume)
✅ **Intelligent Pipeline + claude-3.5**
- Cost: **~$4.52 per 100 slides**
- Quality: Best
- Vision: ✅

---

## Current Situation

### Your Setup:
- Gemini: ❌ Quota exceeded (50/day limit)
- OpenRouter: ⚠️ Free tier exhausted
- Factory AI: ❌ Not an LLM provider

### Immediate Options:

#### Option 1: Add Credits to OpenRouter ($10 minimum)
- Unlocks: 1000+ free requests/day
- Enables: gpt-4o-mini at $0.015/slide
- **Cost for 1000 slides: $15.41**

#### Option 2: New Gemini Key (Free)
- Create new Google Cloud project
- Get new API key
- Limit: 50 slides/day
- **Cost: $0.00** (but slow for bulk)

#### Option 3: Switch to Classic Pipeline (No Vision)
- Saves 12% cost
- Reduces: 3 LLM calls → 1 call per slide
- **Cost: $1.37 per 100 slides** (with gpt-4o-mini)

---

## Conclusion

**Best Overall Value: Intelligent Pipeline + gpt-4o-mini**
- Vision support: ✅
- Quality: High
- Cost: **$1.54 per 100 slides**
- Recommended for: Production use

**For Budget: Classic Pipeline + gpt-4o-mini**
- Vision support: ❌
- Quality: Good
- Cost: **$1.37 per 100 slides** (-11%)
- Recommended for: High volume

**For Free: Batch with Gemini**
- Process 50 slides/day
- Cost: **$0.00**
- Recommended for: Testing, low urgency
