# Silero TTS Integration Guide

## Overview

Silero TTS - это **бесплатная, локальная и быстрая** альтернатива Google Cloud TTS и Azure TTS.

### Преимущества

✅ **Полностью бесплатно** - нет API ключей, нет лимитов  
✅ **Работает офлайн** - не требует интернет-соединения  
✅ **Быстрая генерация** - использует PyTorch для оптимизации  
✅ **Множество языков** - русский, английский, немецкий, и др.  
✅ **Разные голоса** - мужские и женские голоса на выбор  

### Недостатки

❌ Требует PyTorch (~800MB дополнительно)  
❌ Качество немного ниже, чем у облачных решений  
❌ Нет word-level timing (только sentence-level)  

---

## Installation

### 1. Установить зависимости

```bash
cd backend
pip install torch>=2.0.0 torchaudio>=2.0.0 omegaconf>=2.3.0
```

Или использовать уже обновленный `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Настроить окружение

Добавьте в `.env` или `docker.env`:

```env
# TTS Provider
TTS_PROVIDER=silero

# Silero TTS Configuration
SILERO_TTS_LANGUAGE=ru          # ru|en|de|es|fr|ua|uz|xal|indic|ba|kk|tt
SILERO_TTS_SPEAKER=aidar        # ru: aidar|baya|kseniya|xenia|eugene
SILERO_TTS_SAMPLE_RATE=48000    # 8000|24000|48000
```

---

## Supported Languages & Speakers

### Russian (ru)
- **aidar** - мужской голос (рекомендуется)
- **baya** - женский голос
- **kseniya** - женский голос
- **xenia** - женский голос
- **eugene** - мужской голос

### English (en)
- **en_0** - Speaker 0
- **en_1** - Speaker 1
- **en_2** - Speaker 2
- **en_3** - Speaker 3

### Other Languages
- **de** - German
- **es** - Spanish
- **fr** - French
- **ua** - Ukrainian
- **uz** - Uzbek
- **ba** - Bashkir
- **kk** - Kazakh
- **tt** - Tatar
- **xal** - Kalmyk
- **indic** - Indian languages

---

## Testing

### Quick Test

```bash
python test_silero_tts.py
```

Этот скрипт протестирует:
- Русский TTS с голосом "aidar"
- Английский TTS с голосом "en_0"
- Разные русские голоса

### Manual Test

```python
from workers.tts_silero import SileroTTSWorker

# Create worker
worker = SileroTTSWorker(
    language="ru",
    speaker="aidar",
    sample_rate=48000
)

# Synthesize text
texts = [
    "Привет, мир!",
    "Это тест Silero TTS."
]

audio_path, timings = worker.synthesize_slide_text_google(texts)
print(f"Audio: {audio_path}")
print(f"Sentences: {timings['sentences']}")
```

---

## Usage in Production

### With ProviderFactory

Silero TTS автоматически интегрирован через `ProviderFactory`:

```python
from app.services.provider_factory import ProviderFactory

# Get TTS provider (reads TTS_PROVIDER from env)
tts = ProviderFactory.get_tts_provider()

# Synthesize
audio_path, timings = tts.synthesize_slide_text_google([
    "Первое предложение.",
    "Второе предложение."
])
```

### Direct Usage

```python
from workers.tts_silero import SileroTTSWorker

worker = SileroTTSWorker(language="ru", speaker="aidar")
audio_path, timings = worker.synthesize_slide_text_google(texts)
```

---

## Architecture

```
backend/workers/tts_silero.py
    ├── SileroTTSWorker
    │   ├── _load_model()          # Lazy load Silero model from torch hub
    │   ├── _synthesize_text()     # Generate audio for single text
    │   ├── _split_into_sentences() # Split texts into sentences
    │   ├── _estimate_duration()   # Calculate audio duration
    │   ├── _combine_audio_segments() # Merge WAV files
    │   └── synthesize_slide_text_google() # Main API (compatible with other TTS)
```

### Compatibility

`SileroTTSWorker` реализует тот же интерфейс, что и `GoogleTTSWorker`:

```python
def synthesize_slide_text_google(
    texts: List[str], 
    **kwargs
) -> Tuple[str, Dict]:
    """
    Returns:
        (audio_path, {
            "audio": "/path/to/audio.wav",
            "sentences": [
                {"text": "...", "t0": 0.0, "t1": 1.5},
                ...
            ],
            "words": []
        })
    """
```

---

## Performance Comparison

| Provider | Cost | Speed | Quality | Offline | API Key |
|----------|------|-------|---------|---------|---------|
| **Silero TTS** | Free | Fast | Good | ✅ Yes | ❌ No |
| Google Cloud TTS | Paid | Medium | Excellent | ❌ No | ✅ Required |
| Azure TTS | Paid | Medium | Excellent | ❌ No | ✅ Required |

---

## Troubleshooting

### PyTorch Import Error

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Model Download Fails

Убедитесь, что есть интернет при первом запуске. Модель скачивается через `torch.hub`.

### Mock Mode Activates

Если PyTorch не установлен, `SileroTTSWorker` автоматически переключается в mock mode (генерирует тишину).

Проверьте логи:
```
WARNING: PyTorch not available, will use mock mode
```

---

## Configuration Examples

### Development (Local)

```env
TTS_PROVIDER=silero
SILERO_TTS_LANGUAGE=ru
SILERO_TTS_SPEAKER=aidar
SILERO_TTS_SAMPLE_RATE=48000
```

### Production (High Quality)

```env
TTS_PROVIDER=google
GOOGLE_TTS_VOICE=ru-RU-Wavenet-D
```

### Testing (Fast)

```env
TTS_PROVIDER=silero
SILERO_TTS_LANGUAGE=ru
SILERO_TTS_SPEAKER=aidar
SILERO_TTS_SAMPLE_RATE=24000  # Faster, lower quality
```

---

## Next Steps

1. ✅ Silero TTS worker created
2. ✅ ProviderFactory integration
3. ✅ Configuration added
4. ✅ Documentation created

**To use:**
```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Configure
export TTS_PROVIDER=silero

# 3. Test
python test_silero_tts.py

# 4. Use in production
# TTS will be automatically used by the pipeline
```

---

## Credits

Silero TTS by Silero Team: https://github.com/snakers4/silero-models
