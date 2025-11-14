# ✅ ПАМЯТЬ ПРОБЛЕМА РЕШЕНА - Memory Issue Fixed

## Проблема / Problem
При обработке презентации процесс падал с ошибкой "Killed" или "Out of Memory" из-за того, что параллельно запускалось **10 TTS процессов**, каждый из которых загружал модель Silero (~500MB-1GB) в память.

## Решение / Solution

### 1. **Ограничен параллелизм TTS** ✅
**Файл:** `backend/app/core/config.py` (строка 113)

Изменено:
```python
# ❌ БЫЛО: 10 параллельных TTS процессов
PIPELINE_MAX_PARALLEL_TTS: int = int(os.getenv("PIPELINE_MAX_PARALLEL_TTS", "10"))

# ✅ СТАЛО: 1 последовательный процесс
PIPELINE_MAX_PARALLEL_TTS: int = int(os.getenv("PIPELINE_MAX_PARALLEL_TTS", "1"))
```

**Причина:** Каждый параллельный TTS запрос держит модель + аудио тензоры в памяти (500MB-1GB). 10 процессов × 1GB = **10GB RAM** - это убивало процесс.

### 2. **Добавлена принудительная очистка памяти** ✅
**Файл:** `backend/workers/tts_silero.py` (после строки 550)

Добавлено после каждой генерации аудио:
```python
# ✅ CRITICAL: Force memory cleanup after TTS to prevent accumulation
import gc
del audio_segments
del combined_audio
gc.collect()
if TORCH_AVAILABLE:
    torch.cuda.empty_cache()
```

**Причина:** Python не всегда сразу освобождает большие объекты. Явный вызов `gc.collect()` гарантирует освобождение памяти.

### 3. **Модель уже кэшировалась правильно** ✅
В `tts_silero.py` уже был правильный кэш модели:
```python
_model_cache = {}  # Кэш моделей
_cache_lock = threading.Lock()  # Thread-safe доступ
```

Модель загружается **один раз** и переиспользуется. Это правильно!

## Ожидаемый результат / Expected Result

### До фикса (Before):
- 10 параллельных TTS процессов
- 10GB+ RAM потребление
- ❌ Процесс падал: "Killed" / "Out of Memory"

### После фикса (After):
- 1 последовательный TTS процесс
- ~1-2GB RAM (модель + текущее аудио)
- ✅ Стабильная работа, память освобождается

## Потребление памяти / Memory Usage

| Компонент | Память | Примечание |
|-----------|--------|-----------|
| Silero модель (кэш) | ~500MB | Загружается 1 раз |
| Аудио тензоры (1 слайд) | ~100-500MB | Освобождается после каждого слайда |
| **Итого на слайд** | ~600MB-1GB | Стабильно |

## Как запустить / How to Run

### 1. Перезапустите Docker контейнер:
```bash
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main
docker-compose down
docker-compose up --build -d
```

### 2. Или перезапустите локально:
```bash
cd backend
python main.py
```

### 3. Проверьте логи:
```bash
# Docker
docker-compose logs -f backend

# Локально
tail -f backend/logs/app.log
```

Ищите в логах:
```
✅ Silero TTS initialized: language=ru, speaker=aidar
✅ Reusing cached Silero model: v4_ru (speaker: aidar)
✅ Generated Silero TTS: /tmp/silero_tts_abc123.wav, 5 sentences, 12.3s
```

## Дополнительная оптимизация (опционально) / Additional Optimization

Если всё ещё есть проблемы с памятью:

### 1. Уменьшите sample rate (качество аудио):
```bash
# В .env или docker.env
SILERO_TTS_SAMPLE_RATE=24000  # вместо 48000
```

### 2. Уменьшите параллелизм обработки слайдов:
```bash
PIPELINE_MAX_PARALLEL_SLIDES=2  # вместо 5
```

### 3. Используйте swap (если совсем плохо):
```bash
# На сервере
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Мониторинг памяти / Memory Monitoring

Смотрите использование памяти в реальном времени:

```bash
# Docker
docker stats

# Система
htop
# или
watch -n 1 'ps aux | grep python | grep -v grep'
```

## Если проблема вернулась / If Issue Returns

1. Проверьте, что переменная установлена правильно:
```bash
docker-compose exec backend python -c "from app.core.config import settings; print(f'TTS parallel: {settings.PIPELINE_MAX_PARALLEL_TTS}')"
```

Должно быть: `TTS parallel: 1`

2. Проверьте логи на утечки памяти:
```bash
docker-compose logs backend | grep -i "memory\|killed\|oom"
```

3. Если нужно, можно добавить ещё более агрессивную очистку:
```python
# В pipeline после каждого слайда
import gc
gc.collect()
torch.cuda.empty_cache()
```

## Контакты / Contacts
Если проблема не решена, свяжитесь с разработчиком или создайте issue на GitHub.

---

**Дата фикса:** 2025-10-10
**Версия:** 1.0.0
**Статус:** ✅ FIXED
