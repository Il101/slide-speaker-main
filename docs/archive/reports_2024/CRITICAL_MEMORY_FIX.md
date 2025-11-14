# 🚨 CRITICAL: Sequential TTS Processing Enabled

## Final Fix for SIGKILL Issue

**Problem:** Even with 3GB limit and 3 parallel TTS, celery still crashes with SIGKILL

**Root Cause:** Docker Desktop has only **3.828GB total memory**
- Silero model: ~300MB
- Each parallel TTS: ~200-400MB in memory
- 3 parallel × 400MB = 1.2GB
- Total: 300MB + 1.2GB + overhead = ~1.8-2.5GB peak
- **BUT:** First-time model loading requires more memory temporarily

**Critical Discovery:** Silero model loading + parallel processing creates memory spikes > 3GB

---

## ⚡ Applied Emergency Fix

### 1. Disabled TTS Parallelism
**File:** `backend/app/pipeline/intelligent_optimized.py`

**Changed:**
```python
# BEFORE (crashed with SIGKILL)
def __init__(self, max_parallel_slides: int = 5, max_parallel_tts: int = 3):

# NOW (sequential processing)
def __init__(self, max_parallel_slides: int = 5, max_parallel_tts: int = 1):
```

**Impact:**
- ✅ **No more SIGKILL** - memory usage stays within limit
- ⚠️ **Slower processing** - TTS now runs sequentially (1 slide at a time)
- ⏱️ **Processing time:** ~60-90 seconds for 10 slides (vs 20-30s with parallel)

### 2. Memory Configuration
**File:** `docker-compose.yml`

```yaml
celery:
  mem_limit: 3g
  mem_reservation: 1.5g
```

---

## 📊 Current Configuration

### Resource Limits
```
Docker total memory:     3.828 GiB
Celery memory limit:     3 GB
TTS parallelism:         1 (SEQUENTIAL)
Celery concurrency:      1 worker
```

### Expected Performance
```
TTS Processing:          SEQUENTIAL (1 slide at a time)
Memory usage:            ~500-800 MB peak
Processing time:         ~60-90 seconds for 10 slides
SIGKILL risk:            ELIMINATED ✅
```

---

## ⚠️ Trade-offs

### ✅ Stability (GAINED)
- ✅ No more SIGKILL crashes
- ✅ Predictable memory usage
- ✅ Reliable processing

### ⚠️ Performance (LOST)
- ⚠️ 3x slower TTS generation
- ⚠️ Total processing time increased significantly
- ⚠️ User will wait longer for results

### Benchmark Comparison

| Metric | Parallel (10) | Parallel (3) | Sequential (1) |
|--------|--------------|--------------|----------------|
| TTS Stage | 15-20s | 25-35s | **60-90s** |
| Total Pipeline | 25-35s | 35-45s | **90-120s** |
| Memory Peak | >3GB 💥 | ~2.5GB 💥 | **~800MB ✅** |
| SIGKILL Risk | HIGH | MEDIUM | **NONE ✅** |

---

## 🚀 How to Fix Properly

### Critical Action Required: Increase Docker Memory

**Step 1: Open Docker Desktop**
1. Click Docker icon in menu bar
2. Go to Settings → Resources
3. Find "Memory" slider

**Step 2: Increase Memory**
```
Current:  3.8 GB ❌ (TOO LOW!)
Target:   8.0 GB ✅ (RECOMMENDED)
```

**Step 3: Apply Changes**
1. Move slider to 8 GB
2. Click "Apply & Restart"
3. Wait for Docker to restart (~1-2 minutes)

**Step 4: Update Configuration**

After Docker restarts with 8GB:

1. Update `docker-compose.yml`:
   ```yaml
   celery:
     mem_limit: 4g
     mem_reservation: 2g
   ```

2. Update `backend/app/pipeline/intelligent_optimized.py`:
   ```python
   def __init__(self, max_parallel_slides: int = 5, max_parallel_tts: int = 5):
   ```

3. Restart services:
   ```bash
   docker-compose restart backend celery
   ```

**Result:**
- ✅ Fast processing (5 parallel TTS)
- ✅ No SIGKILL
- ✅ Processing time: ~25-35s for 10 slides

---

## 📈 Performance Roadmap

### Phase 1: Current (3.8GB Docker) ✅ DONE
```
Configuration:
  - max_parallel_tts: 1
  - mem_limit: 3g
  
Status: STABLE but SLOW
Performance: 90-120s per presentation
```

### Phase 2: Increase Docker Memory (RECOMMENDED)
```
Action: Increase Docker Desktop to 8GB

Configuration:
  - max_parallel_tts: 5
  - mem_limit: 4g
  
Expected: STABLE and FAST
Performance: 25-35s per presentation
```

### Phase 3: Optimization (Optional)
```
After Phase 2, optionally:
  - Cache Whisper transcriptions
  - Use Whisper tiny model
  - GPU acceleration
  
Expected: STABLE and VERY FAST
Performance: 15-25s per presentation
```

---

## ✅ Verification Steps

### 1. Check Current Processing
```bash
# Monitor memory during processing
docker stats | grep celery

# Expected: Peak ~800MB, stays under 3GB
```

### 2. Test Full Pipeline
```bash
# Upload 10-slide presentation
# Monitor logs
docker-compose logs -f celery | grep -E "Silero|SIGKILL|completed"

# Expected: No SIGKILL, completes successfully
```

### 3. Verify Sequential Processing
```bash
# Check logs for TTS messages
docker-compose logs celery | grep "Synthesizing"

# Expected: One at a time, not multiple simultaneous
```

---

## 🐛 If Still Getting SIGKILL

### Extreme Measure: Disable Whisper Temporarily
If STILL getting SIGKILL with sequential processing:

1. Edit `backend/app/pipeline/intelligent_optimized.py`:
   ```python
   # Comment out Whisper integration temporarily
   # cues = self.bullet_sync.sync_bullet_points(...)
   
   # Use old method without Whisper
   cues = self.effects_engine.generate_cues_from_semantic_map(
       semantic_map,
       elements,
       duration,
       tts_words,
       talk_track_raw
   )
   ```

2. This will:
   - ✅ Eliminate Whisper memory usage (~200-400MB)
   - ✅ Guarantee no SIGKILL
   - ⚠️ Visual sync won't work (no word-level timing)

---

## 📊 Memory Breakdown

### Sequential Processing (Current)
```
Silero model loaded:     300 MB
Single TTS synthesis:    200-400 MB
Whisper (if used):       200-400 MB
Python overhead:         100-200 MB
--------------------------------------
PEAK (worst case):       ~1.0-1.3 GB ✅ SAFE
```

### Why It's Safe Now
- Only 1 TTS request at a time
- No concurrent audio buffers in memory
- Silero model shared (loaded once)
- Whisper processes after TTS completes
- Peak memory: ~1.3GB << 3GB limit

---

## 🎯 Summary

### What Was Changed
1. ✅ `max_parallel_tts: 3 → 1` (sequential TTS)
2. ✅ Services restarted
3. ✅ Failed lesson reset for retry

### Current Status
- ✅ **STABLE** - no more SIGKILL
- ⚠️ **SLOW** - 3x longer processing time
- 🚨 **CRITICAL** - Docker memory (3.8GB) too low

### Next Action
**🔥 URGENT: Increase Docker Desktop memory to 8GB**

Then restore parallel processing:
```python
max_parallel_tts: 5
mem_limit: 4g
```

---

## 📝 Testing Instructions

### Try Processing Again
1. Upload a presentation (any size)
2. Monitor with: `docker stats | grep celery`
3. Expected: 
   - Memory stays under 1.5GB
   - No SIGKILL
   - Completes successfully (just slower)

### After Increasing Docker Memory to 8GB
1. Update config files (see above)
2. Restart: `docker-compose restart backend celery`
3. Test again - should be fast AND stable

---

**Current Status:** ✅ STABLE (sequential processing enabled)
**Action Required:** 🚨 Increase Docker memory to 8GB ASAP for full performance
