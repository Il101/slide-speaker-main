# TTS Smart Fallback System 🎙️

## Что изменилось

Теперь система TTS использует **умную стратегию с автоматическим fallback**:

### 📊 Приоритет TTS Провайдеров

1. **Google Cloud TTS** (Primary)
   - Высокое качество голоса
   - Word-level timing через `<mark>` теги (точная синхронизация)
   - Whisper НЕ требуется
   - Требует Google Cloud credentials

2. **Silero TTS** (Auto-Fallback)
   - Бесплатный, локальный
   - Быстрый синтез
   - Word-level timing через Whisper (автоматически загружается)
   - Не требует API ключей

3. **Mock TTS** (Development Only)
   - Для тестирования без настоящего TTS

---

## 🔧 Технические детали

### Логика переключения

```python
# 1. Попытка использовать Google TTS
if TTS_PROVIDER == "google" and GOOGLE_APPLICATION_CREDENTIALS exists:
    use GoogleTTSWorker
    # Word timing из Google TTS напрямую, Whisper не нужен
else:
    # 2. Automatic fallback to Silero
    use SileroTTSWorker
    # Whisper загрузится автоматически для получения word timing
```

### Оптимизация загрузки Whisper

**До:**
```python
import whisper  # Всегда загружался, даже если не нужен
```

**После:**
```python
# Lazy import - только когда реально используется Silero
def _load_whisper_model(self):
    if not self.needs_whisper:  # Google TTS не нуждается в Whisper
        return
    import whisper  # Загружается ТОЛЬКО для Silero
```

**Преимущества:**
- ✅ С Google TTS: Whisper не загружается → экономия памяти (~500MB)
- ✅ С Silero TTS: Whisper загружается автоматически только когда нужен
- ✅ Быстрый старт приложения

---

## 📝 Конфигурация

### Environment Variables

```env
# Primary TTS (Google)
TTS_PROVIDER=google
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-sa.json
GOOGLE_TTS_VOICE=ru-RU-Wavenet-D
GOOGLE_TTS_SPEAKING_RATE=1.0
GOOGLE_TTS_PITCH=0.0

# Fallback TTS (Silero)
SILERO_TTS_LANGUAGE=ru
SILERO_TTS_SPEAKER=aidar
SILERO_TTS_SAMPLE_RATE=48000
```

### Файлы конфигурации

#### `docker.env.template`
```env
TTS_PROVIDER=google  # google (primary, word-level timing) with auto-fallback to silero
```

#### `railway.env.template`
```env
TTS_PROVIDER=google  # google (primary) with auto-fallback to silero (if no Google credentials)
```

#### `backend/app/core/config.py`
```python
TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "google")  # Default changed: silero → google
```

---

## 🎯 Сценарии использования

### Сценарий 1: Production с Google Cloud

```bash
# .env
TTS_PROVIDER=google
GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-sa.json

# Результат:
# ✅ Google Cloud TTS (высокое качество + word timing)
# ❌ Whisper не загружается (экономия памяти)
```

### Сценарий 2: Development без Google Cloud

```bash
# .env
TTS_PROVIDER=google
# GOOGLE_APPLICATION_CREDENTIALS не указан

# Результат:
# ⚠️ Google credentials not found
# ✅ Automatic fallback to Silero TTS
# ✅ Whisper загружается автоматически для timing
```

### Сценарий 3: Явное использование Silero

```bash
# .env
TTS_PROVIDER=silero

# Результат:
# ✅ Silero TTS (быстрый, локальный)
# ✅ Whisper загружается автоматически
```

---

## 🚀 Преимущества новой системы

### 1. Автоматический Fallback
- Не нужно вручную менять конфигурацию
- Система сама определяет доступность Google credentials
- Плавное переключение без ошибок

### 2. Оптимизация памяти
- Whisper (~500MB) загружается ТОЛЬКО когда нужен
- С Google TTS: экономия памяти
- Lazy loading для всех зависимостей

### 3. Лучшее качество по умолчанию
- Google TTS - primary (высокое качество)
- Silero - fallback (быстро и бесплатно)
- Mock - development only

### 4. Word-level timing всегда работает
- Google TTS: нативно через `<mark>` теги
- Silero TTS: через Whisper (автоматически)
- Точная синхронизация визуальных эффектов

---

## 🔍 Логирование

### Google TTS (Primary)
```
✅ Using Google Cloud TTS (primary)
✅ Native timing available for TTS provider: google (Whisper not needed)
```

### Silero TTS (Fallback)
```
⚠️ Google credentials not found, falling back to Silero TTS
✅ Using Silero TTS (fallback - local & free)
🎤 Whisper timing enabled for TTS provider: silero
📦 Loading Whisper model: base
✅ Whisper model loaded
```

### Mock TTS (Development)
```
⚠️ Falling back to mock TTS
```

---

## 📦 Зависимости

### Google TTS
```txt
google-cloud-texttospeech>=2.21.0
```

### Silero TTS
```txt
torch>=2.0.0
torchaudio>=2.0.0
```

### Whisper (только для Silero)
```txt
openai-whisper>=20230314
```

---

## 🧪 Тестирование

### Проверка текущего TTS провайдера

```python
from app.services.provider_factory import ProviderFactory

tts = ProviderFactory.get_tts_provider()
print(f"Current TTS: {tts.__class__.__name__}")
# Output: GoogleTTSWorker или SileroTTSWorker
```

### Проверка Whisper availability

```python
from app.services.bullet_point_sync import BulletPointSyncService

sync = BulletPointSyncService()
print(f"Needs Whisper: {sync.needs_whisper}")
# Google TTS: False
# Silero TTS: True
```

---

## 📊 Сравнение

| Параметр | Google TTS | Silero TTS |
|----------|------------|------------|
| Качество голоса | ⭐⭐⭐⭐⭐ (отлично) | ⭐⭐⭐⭐ (хорошо) |
| Word timing | ✅ Нативно (через `<mark>`) | ✅ Через Whisper |
| API ключ | ❌ Требуется | ✅ Не требуется |
| Стоимость | 💰 Платно | 🆓 Бесплатно |
| Скорость | 🔵 Средняя (API call) | 🟢 Быстро (локально) |
| Память | 🟢 Низкая | 🔵 Средняя (+ Whisper) |
| Whisper | ✅ Не нужен | ❌ Требуется |

---

## 🔄 Миграция

### Если раньше использовали Silero по умолчанию

**Было:**
```env
TTS_PROVIDER=silero  # Default
```

**Стало:**
```env
TTS_PROVIDER=google  # Default with auto-fallback
```

**Что делать:**
1. Ничего не делать - fallback сработает автоматически
2. Или добавьте Google credentials для лучшего качества
3. Или явно укажите `TTS_PROVIDER=silero` если хотите оставить Silero

---

## 🛠️ Troubleshooting

### Google TTS не работает

**Проблема:**
```
⚠️ Google credentials not found, falling back to Silero TTS
```

**Решение:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-sa.json
# или в .env:
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-sa.json
```

### Whisper не загружается для Silero

**Проблема:**
```
⚠️ Whisper not available. Install: pip install openai-whisper
```

**Решение:**
```bash
pip install openai-whisper
```

### Медленная загрузка Whisper

**Решение:**
Используйте меньшую модель в `intelligent_optimized.py`:
```python
self.bullet_sync = BulletPointSyncService(whisper_model="tiny")  # вместо "base"
```

Модели:
- `tiny` - самая быстрая, минимальное качество
- `base` - ✅ рекомендуемая (баланс)
- `small` - лучше качество, медленнее
- `medium` - высокое качество, медленно
- `large` - максимальное качество, очень медленно

---

## ✅ Итог

Теперь система TTS работает **умно**:
1. **Пробует Google TTS** (высокое качество, без Whisper)
2. **Fallback на Silero** (бесплатно, локально, с Whisper)
3. **Whisper загружается только когда нужен** (экономия памяти)
4. **Все работает из коробки** (не требует ручной настройки)

🎉 **Лучшее качество по умолчанию, надёжный fallback, оптимизация памяти!**
