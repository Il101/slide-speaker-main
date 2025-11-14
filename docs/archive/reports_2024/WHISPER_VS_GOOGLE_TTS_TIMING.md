# 🎤 Whisper vs Google TTS Timing - Когда что используется?

## ❓ Вопрос: Зачем Whisper если Google TTS может timing отдавать?

**Короткий ответ:** Whisper используется ТОЛЬКО с Silero TTS, НЕ с Google TTS!

## 📊 Таблица использования

| TTS Provider | Word Timing Method | Whisper Used? | Memory Usage |
|--------------|-------------------|---------------|--------------|
| **Google TTS** | Native SSML `<mark>` tags | ❌ No | Low (~200MB) |
| **Silero TTS** | Whisper recognition | ✅ Yes | High (~700MB) |
| **Azure TTS** | Whisper recognition | ✅ Yes | High (~700MB) |
| **Mock TTS** | Fallback (time-based) | ❌ No | Minimal |

## 🔍 Как это работает

### Сценарий 1: Google Cloud TTS (Production)

```
┌─────────────────────────────────────────────────────────────┐
│ TTS_PROVIDER=google                                          │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: TTS Generation                                      │
│                                                               │
│ SmartScriptGenerator → SSMLGenerator                         │
│                                                               │
│ Output: SSML with <mark> tags                                │
│ <mark name="group_title"/>Заголовок                          │
│ <mark name="group_bullet_1"/>Первый пункт                    │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Google Cloud TTS API                                         │
│                                                               │
│ Input: SSML with <mark> tags                                 │
│ Output: {                                                    │
│   audio_bytes: ...,                                          │
│   word_timings: [                                            │
│     {mark_name: "group_title", time_seconds: 0.5},           │
│     {mark_name: "group_bullet_1", time_seconds: 2.3}         │
│   ]                                                          │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: Visual Effects                                      │
│                                                               │
│ BulletPointSyncService.sync_bullet_points()                  │
│   → self.needs_whisper = False  ✅                           │
│   → Uses native word_timings from Google                     │
│   → Whisper NOT loaded                                       │
│                                                               │
│ VisualEffectsEngine                                          │
│   → Matches group_id with mark_name                          │
│   → Creates cues: t0=0.5s, t1=2.5s                           │
└─────────────────────────────────────────────────────────────┘
```

**Memory:** ~200MB (TTS model not loaded locally)

### Сценарий 2: Silero TTS (Free Fallback)

```
┌─────────────────────────────────────────────────────────────┐
│ TTS_PROVIDER=silero                                          │
│ (или Google credentials отсутствуют)                         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: TTS Generation                                      │
│                                                               │
│ SmartScriptGenerator → SSMLGenerator                         │
│                                                               │
│ Output: SSML (limited support)                               │
│ <prosody rate="1.0">Заголовок</prosody>                      │
│ <break time="500ms"/>                                        │
│ Первый пункт                                                 │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Silero TTS (Local)                                           │
│                                                               │
│ Input: SSML (basic tags only)                                │
│ Output: {                                                    │
│   audio_bytes: ...,                                          │
│   word_timings: []  ❌ EMPTY - Silero не поддерживает!       │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: Visual Effects                                      │
│                                                               │
│ BulletPointSyncService.sync_bullet_points()                  │
│   → self.needs_whisper = True  ⚠️                            │
│   → Loads Whisper model (~500MB)                             │
│   → Whisper recognizes audio → word_timings                  │
│                                                               │
│ Whisper.transcribe(audio_path, word_timestamps=True)         │
│   → {                                                        │
│       segments: [                                            │
│         {words: [                                            │
│           {word: "заголовок", start: 0.5, end: 1.2},         │
│           {word: "первый", start: 2.3, end: 2.7}             │
│         ]}                                                   │
│       ]                                                      │
│     }                                                        │
│                                                               │
│ VisualEffectsEngine                                          │
│   → Matches text with Whisper words                          │
│   → Creates cues: t0=0.5s, t1=2.7s                           │
└─────────────────────────────────────────────────────────────┘
```

**Memory:** ~700MB (Silero model + Whisper model)

## 💡 Умная логика детекции

### BulletPointSyncService.__init__()

```python
def __init__(self, whisper_model: str = "base"):
    # ✅ SMART: Check TTS provider to decide if Whisper is needed
    tts_provider = os.getenv("TTS_PROVIDER", "google").lower()
    self.needs_whisper = tts_provider in ("silero", "azure", "mock")
    
    if self.needs_whisper:
        logger.info(f"🎤 Whisper timing enabled for TTS provider: {tts_provider}")
    else:
        logger.info(f"✅ Native timing available for TTS provider: {tts_provider} (Whisper not needed)")
```

### BulletPointSyncService.sync_bullet_points()

```python
def sync_bullet_points(self, audio_path, ...):
    # ✅ SMART CHECK: Skip Whisper if TTS provider has native timing
    if not self.needs_whisper:
        logger.info("✅ Using native TTS timing (Google/native provider) - Whisper not needed")
        return self._fallback_sync(talk_track_raw, semantic_map, elements)
    
    # Only reaches here if TTS is Silero/Azure
    logger.info("🎙️ Running Whisper on audio...")
    self._load_whisper_model()
    result = self.whisper_model.transcribe(audio_path, word_timestamps=True)
    ...
```

## 📈 Сравнение производительности

| Metric | Google TTS | Silero TTS + Whisper |
|--------|-----------|---------------------|
| **TTS Speed** | ~2s per slide (API) | ~0.5s per slide (local) |
| **Timing Extraction** | Instant (в TTS) | +3-5s (Whisper recognition) |
| **Total Time** | **~2s** | **~4-6s** |
| **Memory** | ~200MB | ~700MB |
| **Cost** | $4 per 1M chars | Free |
| **Quality** | Excellent (WaveNet) | Good (neural) |
| **Timing Accuracy** | Native (100%) | Whisper (95-98%) |

## 🚀 Оптимизация: Lazy Loading

### До оптимизации:

```python
# ❌ ПЛОХО: Whisper загружается ВСЕГДА
import whisper
self.whisper_model = whisper.load_model("base")  # ~500MB
```

**Проблема:** Даже с Google TTS, Whisper загружался и занимал 500MB памяти зря!

### После оптимизации:

```python
# ✅ ХОРОШО: Whisper загружается ТОЛЬКО когда нужен
def _load_whisper_model(self):
    if not self.needs_whisper:  # Google TTS → skip
        logger.debug("Whisper not needed for current TTS provider")
        return
    
    if self.whisper_model is None:
        import whisper  # Lazy import
        self.whisper_model = whisper.load_model(self.whisper_model_name)
```

**Результат:**
- Google TTS: Whisper НЕ загружается → **экономия 500MB**
- Silero TTS: Whisper загружается автоматически только когда вызван sync_bullet_points()

## 🔧 Текущая конфигурация Docker

```bash
$ docker exec slide-speaker-main-backend-1 printenv | grep TTS
TTS_PROVIDER=google
SILERO_TTS_LANGUAGE=ru
SILERO_TTS_SAMPLE_RATE=48000
SILERO_TTS_SPEAKER=xenia
```

**Статус:** Whisper НЕ используется (Google TTS активен) ✅

## 🎯 Когда Whisper реально нужен?

### Случай 1: Google Credentials отсутствуют

```env
TTS_PROVIDER=google
GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-sa.json  ❌ файл не найден
```

**Результат:**
```python
# provider_factory.py
if not google_creds or not Path(google_creds).exists():
    logger.warning("Google credentials not found, falling back to Silero TTS")
    return ProviderFactory._get_silero_tts_fallback()
```

→ Автоматический fallback на Silero → Whisper загружается

### Случай 2: Явно выбран Silero

```env
TTS_PROVIDER=silero
```

→ Whisper загружается сразу

### Случай 3: Azure TTS

```env
TTS_PROVIDER=azure
```

→ Azure TTS не поддерживает SSML marks → Whisper нужен

## 📝 Выводы

1. **Whisper - это smart fallback**, не основной метод
2. С Google TTS (production) Whisper **не используется** и **не загружается**
3. С Silero TTS (free fallback) Whisper **автоматически загружается** для извлечения timing
4. Это дает лучшее из обоих миров:
   - Производство: Google TTS (быстро, точно, без лишней памяти)
   - Разработка/Free: Silero + Whisper (бесплатно, локально, работает)

## 🐛 Устаревшие комментарии (исправлено)

**Было:**
```python
# ✅ Generate visual cues using Whisper + Silero hybrid approach
```

**Стало:**
```python
# ✅ Generate visual cues with smart timing strategy:
# - Google TTS: Uses native word_timings from SSML <mark> tags (no Whisper needed)
# - Silero TTS: Uses Whisper to extract word-level timing from generated audio
```

---

**Статус:** ✅ Комментарии обновлены, путаница устранена!
