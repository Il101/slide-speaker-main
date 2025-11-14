# 🎤 Миграция на Gemini TTS Flash 2.5

**Дата:** 12 ноября 2025  
**Статус:** ✅ READY TO TEST

---

## 📋 Что изменилось

### ✅ Добавлено:

1. **Новый worker:** `backend/workers/tts_gemini.py`
   - Поддержка Gemini TTS Flash 2.5
   - Natural Language Prompts
   - Markup Tags (15+ тегов)
   - Sentence-level timing

2. **Provider Factory:**
   - Добавлен `synthesize_slide_text_gemini()` 
   - Обновлен `get_tts_provider()` для поддержки `TTS_PROVIDER=gemini`

3. **Pipeline Integration:**
   - `intelligent_optimized.py` теперь проверяет `TTS_PROVIDER`
   - Автоматически выбирает между Gemini TTS и Chirp 3 HD
   - Извлекает plain text из talk_track для Gemini TTS (no SSML)

4. **Environment Variables:**
   - `TTS_PROVIDER=gemini` - включает Gemini TTS
   - `GEMINI_TTS_MODEL=gemini-2.5-flash-tts` - модель
   - `GEMINI_TTS_VOICE=Charon` - голос (language-independent)
   - `GEMINI_TTS_LANGUAGE=ru-RU` - язык
   - `GEMINI_TTS_PROMPT` - стилистический промпт

---

## 🚀 Как использовать

### Вариант 1: Gemini TTS (рекомендуется для тестирования)

```bash
# Обновить docker.env
TTS_PROVIDER=gemini
GEMINI_TTS_MODEL=gemini-2.5-flash-tts
GEMINI_TTS_VOICE=Charon
GEMINI_TTS_LANGUAGE=ru-RU
GEMINI_TTS_PROMPT=Speak naturally and clearly, with good pacing and intonation.
```

**Особенности:**
- ✅ Отличное качество голоса (10/10)
- ✅ 78% дешевле ($0.025 vs $0.115 на 10 минут)
- ⚠️ Sentence-level timing (не word-level)
- ⚠️ Visual effects будут менее точными

### Вариант 2: Chirp 3 HD (текущая система)

```bash
# Обновить docker.env
TTS_PROVIDER=google
GOOGLE_TTS_VOICE=ru-RU-Chirp3-HD-Puck
```

**Особенности:**
- ✅ Word-level timing для VFX
- ✅ SSML support
- ⚠️ Качество голоса хуже (8/10)
- ⚠️ Дороже ($0.115 на 10 минут)

---

## 🧪 Тестирование

### 1. Тест Gemini TTS worker

```bash
cd backend
python workers/tts_gemini.py
```

**Ожидаемый результат:**
```
✅ Gemini TTS client initialized: model=gemini-2.5-flash-tts, voice=Charon
🎤 Synthesizing with Gemini TTS: 50 chars, model=gemini-2.5-flash-tts, voice=Charon
✅ Gemini TTS synthesis complete: 26112 bytes
✅ Audio saved to: /tmp/gemini_tts_xxxx.wav
✅ Total duration: 3.25s
✅ Sentences: 3
⚠️ Word timings: 0 (expected 0 for Gemini TTS)
✅ Precision: sentence
```

### 2. Тест в pipeline

```bash
# Загрузить тестовую презентацию через API
curl -X POST http://localhost:8000/upload \
  -F "file=@test_presentation.pdf" \
  -H "Authorization: Bearer <token>"
```

**Проверить логи:**
```bash
docker logs slide-speaker-backend -f | grep "Gemini TTS"
```

**Ожидаемый вывод:**
```
✅ Using Gemini TTS Flash 2.5 (superior voice, sentence-level timing)
🎤 Slide slide_1: Using Gemini TTS Flash 2.5 with 8 text segments
✅ Slide slide_1: Gemini TTS complete (sentence-level timing)
⚠️ Word-level timing not available - visual effects will use sentence-level estimation
```

### 3. Проверка аудио

```bash
# Найти сгенерированные аудио файлы
find .data -name "*.wav" -type f -mmin -5

# Проиграть аудио (macOS)
afplay .data/<lesson_id>/slides/001.wav

# Или скачать через API
curl http://localhost:8000/api/lessons/<lesson_id>/audio/001.wav --output test_audio.wav
```

---

## 📊 Сравнение результатов

### Метрики для проверки:

| Метрика | Chirp 3 HD | Gemini TTS Flash 2.5 | Как проверить |
|---------|-----------|---------------------|---------------|
| **Качество голоса** | 8/10 | 10/10 | Прослушать аудио |
| **Стоимость (10 мин)** | $0.115 | $0.025 | Логи API calls |
| **Word-level timing** | ✅ 60+ timings | ❌ 0 timings | `manifest.json` → `tts_words.word_timings` |
| **Sentence-level timing** | ✅ | ✅ | `manifest.json` → `tts_words.sentences` |
| **VFX precision** | ±50ms | ±500ms | Визуальная проверка |
| **Generation speed** | ~7s | ~5s | Логи `Stage 4` |

---

## 🔧 Откат на Chirp 3 HD

Если что-то пошло не так:

```bash
# 1. Изменить docker.env
TTS_PROVIDER=google

# 2. Перезапустить сервисы
docker-compose down
docker-compose up -d backend celery-worker

# 3. Проверить логи
docker logs slide-speaker-backend -f
```

**Ожидаемый вывод после отката:**
```
✅ Using Google Cloud TTS Chirp 3 HD (word-level timing)
🎤 Slide slide_1: Using Chirp 3 HD TTS with SSML (word-level timing)
✅ Slide slide_1: audio generated (92.7s)
   TTS returned: 60 marks total, 8 sentences
   Group markers in TTS: 8
```

---

## ⚠️ Известные ограничения Gemini TTS

### 1. Нет word-level timing
**Проблема:** Visual effects менее точные  
**Решение (будущее):** 
- Speech-to-Text для обратной синхронизации
- Forced Alignment (Gentle/Aeneas)
- ML модель для предсказания timing

### 2. Нет SSML support
**Проблема:** Невозможно использовать SSML теги  
**Решение:** Используем plain text + Markup Tags (15+ тегов):
```python
text = "Добро пожаловать [short pause] в нашу презентацию."
# Вместо SSML: <prosody rate="slow">text</prosody>
# Используем: [extremely slow]text[/extremely slow]
```

### 3. Text limit: 4000 bytes
**Проблема:** Длинные слайды могут превысить лимит  
**Решение:** Автоматическое усечение в worker (уже реализовано)

---

## 📈 Мониторинг

### Grafana Dashboard

**Метрики для отслеживания:**
```
- tts_gemini_requests_total
- tts_gemini_duration_seconds
- tts_gemini_errors_total
- tts_cost_per_presentation
```

### Логи

**Ключевые логи для мониторинга:**
```bash
# TTS provider selection
grep "Using Gemini TTS" backend.log

# TTS errors
grep "Gemini TTS error" backend.log

# Cost tracking
grep "TTS cost" backend.log
```

---

## 💡 Рекомендации

### Для production:

1. **A/B тестирование:**
   - 50% презентаций → Gemini TTS
   - 50% презентаций → Chirp 3 HD
   - Сравнить user feedback

2. **Hybrid стратегия:**
   ```python
   if user.premium_tier:
       TTS_PROVIDER=google  # Word-level VFX
   else:
       TTS_PROVIDER=gemini  # Better voice, cheaper
   ```

3. **Cost tracking:**
   - Логировать каждый TTS call
   - Считать ежедневные расходы
   - Алерты при превышении бюджета

### Для development:

1. **Тестировать оба варианта:**
   - Gemini TTS для новых фичей
   - Chirp 3 HD для регрессии

2. **Mock mode:**
   ```bash
   # Если нет Google credentials
   TTS_PROVIDER=mock
   ```

---

## 🎯 Следующие шаги

### Фаза 1: Testing (сейчас)
- ✅ Gemini TTS worker создан
- ✅ Pipeline интеграция готова
- 🔄 Тестирование на реальных презентациях
- 🔄 Сравнение качества голоса
- 🔄 Проверка sentence-level VFX

### Фаза 2: STT Integration (если нужны word-level timings)
- 🔄 Создать `tts_gemini_with_stt.py`
- 🔄 Интегрировать Google Speech-to-Text
- 🔄 Кэширование STT результатов
- 🔄 Тестирование точности VFX

### Фаза 3: Production Rollout
- 🔄 A/B тестирование
- 🔄 User feedback сбор
- 🔄 Cost monitoring
- 🔄 Gradual rollout (10% → 50% → 100%)

---

## 🐛 Troubleshooting

### Проблема 1: "Gemini TTS not available"

**Симптом:**
```
⚠️ Using mock audio (Gemini TTS not available)
```

**Решение:**
```bash
# Проверить credentials
echo $GOOGLE_APPLICATION_CREDENTIALS
cat $GOOGLE_APPLICATION_CREDENTIALS | jq .

# Проверить IAM роли
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"
```

### Проблема 2: "Text too long (4100 bytes)"

**Симптом:**
```
⚠️ Text too long (4100 bytes), truncating to 4000 bytes
```

**Решение:**
- Проверить длину talk_track segments
- Разбить длинные сегменты на части
- Или переключиться на Chirp 3 HD (нет лимита)

### Проблема 3: Visual effects не синхронизированы

**Симптом:**
- Эффекты появляются рано/поздно
- ±500ms рассинхрон

**Решение:**
- Ожидаемо для sentence-level timing
- Для точных VFX → переключиться на Chirp 3 HD
- Или подождать STT integration (Фаза 2)

---

## 📚 Документация

- **Gemini TTS возможности:** `GEMINI_TTS_CAPABILITIES_FULL.md`
- **Тесты и результаты:** `GEMINI_TTS_TEST_RESULTS.md`
- **Решения для VFX:** `GEMINI_TTS_VFX_SOLUTIONS.md`
- **Sentence-level VFX:** `SENTENCE_VFX_EXPLANATION.md`
- **Стоимость pipeline:** `PIPELINE_COST_ANALYSIS.md`

---

**Статус миграции:** ✅ ГОТОВО К ТЕСТИРОВАНИЮ

**Контакты для вопросов:** [ваш контакт]

**Последнее обновление:** 12 ноября 2025
