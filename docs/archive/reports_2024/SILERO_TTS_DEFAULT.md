# Silero TTS - Default Configuration

## Изменения

✅ **Silero TTS теперь установлен по умолчанию**

### Что изменилось:

1. **backend/app/core/config.py**
   - `TTS_PROVIDER` default изменен: `"google"` → `"silero"`

2. **docker.env**
   - `TTS_PROVIDER=silero`
   - Добавлены настройки Silero TTS

3. **docker.env.template**
   - `TTS_PROVIDER=silero`
   - Добавлены настройки Silero TTS

4. **railway.env**
   - `TTS_PROVIDER=silero`
   - Добавлены настройки Silero TTS

5. **railway.env.template**
   - `TTS_PROVIDER=silero`
   - Добавлены настройки Silero TTS

6. **README.md**
   - Обновлена документация с новым default

---

## Почему Silero TTS по умолчанию?

### Преимущества:

✅ **Полностью бесплатно** - нет затрат на API  
✅ **Работает офлайн** - не требует интернет  
✅ **Нет API ключей** - проще настройка  
✅ **Быстрая генерация** - использует PyTorch  
✅ **Множество языков** - 12+ языков из коробки  
✅ **Разные голоса** - несколько спикеров на каждый язык  

### Ограничения:

❌ Требует PyTorch (~800MB)  
❌ Качество чуть ниже, чем у Google Cloud TTS  
❌ Нет word-level timing (только sentence-level)  

---

## Google TTS остается доступен

**Google Cloud TTS НЕ УДАЛЕН из кода!** Он остается доступным как альтернатива.

### Как переключиться на Google TTS:

#### В docker.env:
```env
TTS_PROVIDER=google
```

#### В railway.env:
```env
TTS_PROVIDER=google
```

#### Через переменную окружения:
```bash
export TTS_PROVIDER=google
```

---

## Конфигурация по умолчанию

### Silero TTS (Default):
```env
TTS_PROVIDER=silero
SILERO_TTS_LANGUAGE=ru
SILERO_TTS_SPEAKER=aidar
SILERO_TTS_SAMPLE_RATE=48000
```

### Google Cloud TTS (Alternative):
```env
TTS_PROVIDER=google
GOOGLE_TTS_VOICE=ru-RU-Wavenet-D
GOOGLE_TTS_SPEAKING_RATE=1.0
GOOGLE_TTS_PITCH=0.0
```

---

## Установка зависимостей

### Для Silero TTS:
```bash
pip install torch>=2.0.0 torchaudio>=2.0.0 omegaconf>=2.3.0
```

### Для Google Cloud TTS:
```bash
pip install google-cloud-texttospeech>=2.16.3
```

Обе библиотеки уже включены в `requirements.txt`.

---

## Тестирование

### Быстрый тест Silero TTS:
```bash
python test_silero_tts.py
```

### Проверка текущего провайдера:
```python
from app.services.provider_factory import ProviderFactory

tts = ProviderFactory.get_tts_provider()
print(f"Current TTS: {tts.__class__.__name__}")
```

---

## Визуальные эффекты

✅ **Silero TTS полностью совместим** с системой визуальных эффектов.

Использует **sentence-level timing** для синхронизации:
```python
{
    "audio": "/path/to/audio.wav",
    "sentences": [
        {"text": "Первое предложение.", "t0": 0.0, "t1": 2.0},
        {"text": "Второе предложение.", "t0": 2.2, "t1": 4.5}
    ],
    "words": []
}
```

---

## Production Ready

Для production можно использовать:

### Вариант 1: Silero (рекомендуется для начала)
- ✅ Бесплатно
- ✅ Нет зависимостей от внешних API
- ✅ Стабильная работа

### Вариант 2: Google Cloud TTS (для высокого качества)
- Лучшее качество голоса
- Word-level timing
- Требует настройки GCP и оплаты

---

## Миграция с Google на Silero

Если вы использовали Google TTS и хотите перейти на Silero:

1. **Обновите переменную окружения:**
   ```bash
   TTS_PROVIDER=silero
   ```

2. **Установите зависимости:**
   ```bash
   pip install torch torchaudio omegaconf
   ```

3. **Перезапустите сервисы:**
   ```bash
   docker-compose restart
   ```

4. **Проверьте работу:**
   ```bash
   python test_silero_tts.py
   ```

---

## Rollback на Google TTS

Если нужно вернуться на Google TTS:

```bash
# В .env файле
TTS_PROVIDER=google

# Перезапустить
docker-compose restart
```

Все настройки Google TTS сохранены в конфигурации.

---

## Документация

- **Полная документация Silero TTS:** `SILERO_TTS_GUIDE.md`
- **Интеграция провайдеров:** `backend/app/services/provider_factory.py`
- **Визуальные эффекты:** `backend/app/services/visual_effects_engine.py`

---

## Поддержка

Если возникли проблемы с Silero TTS:

1. Проверьте установку PyTorch:
   ```bash
   python -c "import torch; print(torch.__version__)"
   ```

2. Запустите тест:
   ```bash
   python test_silero_tts.py
   ```

3. Проверьте логи:
   ```bash
   docker-compose logs backend | grep -i "tts\|silero"
   ```

4. При необходимости переключитесь на Google TTS временно.
