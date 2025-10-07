# 🚀 Quick Fix Guide - Pipeline Issues

## Что было исправлено

### Проблема 1: Визуальные эффекты рассинхронизированы ✅
**Решение:**
- Улучшен fuzzy matching для поиска timing в TTS
- Добавлен адаптивный padding для эффектов
- Добавлен confidence scoring для better matches

### Проблема 2: TTS паузы и интонация неправильные ✅
**Решение:**
- Увеличены паузы между сегментами (300-500ms)
- Добавлена динамическая prosody для разных типов контента
- Оптимизировано количество markers (<150)

### Проблема 3: Некоторые слайды без аудио ✅
**Решение:**
- Добавлен OCR fallback при отсутствии скрипта
- Реализован retry механизм для timeouts
- Детальное логирование причин отсутствия аудио

## Как проверить исправления

### 1. Перезапустить Docker контейнеры
```bash
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main
docker-compose down
docker-compose up --build -d
```

### 2. Проверить логи
```bash
# Следить за логами в реальном времени
docker-compose logs -f backend celery

# Проверить конкретные ошибки
docker-compose logs celery | grep "TTS FAILURES"
docker-compose logs celery | grep "using OCR fallback"
```

### 3. Загрузить тестовую презентацию
1. Откройте интерфейс: http://localhost:5173
2. Загрузите презентацию
3. Дождитесь обработки
4. Проверьте:
   - Все ли слайды имеют аудио
   - Синхронизированы ли визуальные эффекты
   - Естественны ли паузы в речи

### 4. Проверить результаты в логах
Ищите эти сообщения:
```
✅ Generated SSML: XXX chars, YYY markers
✅ Optimized SSML: XXX chars, YYY markers  # Если было >150 markers
✅ Found N/M words [...] at X.XXs (confidence: XX%)
⚡ TTS completed (X/Y slides)
```

Если есть проблемы:
```
⚠️ TTS FAILURES: N slides without audio:
   - Slide X: <причина>
⚠️ Slide X: using OCR fallback for TTS
🔄 Retrying TTS for slide X...
```

## Что проверять в результатах

### ✅ Аудио качество
- [ ] Паузы между предложениями естественные (не слишком короткие)
- [ ] Интонация варьируется для разных типов контента
- [ ] Иностранные термины произносятся корректно
- [ ] Нет обрывов или артефактов

### ✅ Визуальные эффекты
- [ ] Эффекты появляются синхронно с речью
- [ ] Нет слишком ранних или поздних эффектов
- [ ] Эффекты не перекрываются некорректно
- [ ] Длительность эффектов соответствует контенту

### ✅ Надёжность
- [ ] Все слайды обработаны
- [ ] Нет критических ошибок в логах
- [ ] При сбоях используется fallback
- [ ] Retry работает при timeouts

## Если проблемы остались

### Проблема: Всё ещё есть слайды без аудио
**Проверить:**
1. Логи celery: `docker-compose logs celery | tail -100`
2. Причина в TTS FAILURES отчёте
3. OCR fallback сработал?

**Решение:**
- Если "no script AND no OCR text" → проблема с OCR extraction
- Если "TTS timeout" → увеличить timeout или проверить сеть
- Если "Retry failed" → проверить Google TTS credentials

### Проблема: Визуальные эффекты всё ещё не синхронизированы
**Проверить:**
1. Confidence score в логах: должно быть >50%
2. Количество найденных слов в "Found N/M words"
3. Есть ли group markers в TTS response

**Решение:**
- Если confidence низкий → проблема с text matching
- Если нет group markers → проблема с SSML generation
- Если markers есть, но эффекты не синхронизированы → проверить visual_effects_engine

### Проблема: TTS звучит неестественно
**Проверить:**
1. Количество markers: должно быть <150
2. Длина SSML: должна быть <4000 chars
3. Prosody применяется корректно

**Решение:**
- Если >150 markers → проверить optimizer работу
- Если >4000 chars → разбить на несколько частей
- Если prosody не применяется → проверить segment types

## Следующие шаги

### Краткосрочные (сейчас)
1. Перезапустить Docker
2. Протестировать на 2-3 презентациях
3. Проверить логи на ошибки

### Среднесрочные (на неделе)
1. Добавить quota check перед TTS batch
2. Реализовать exponential backoff для retry
3. Добавить alternative TTS provider fallback

### Долгосрочные (в будущем)
1. Мониторинг и алерты для TTS success rate
2. A/B тестирование prosody настроек
3. ML-based timing prediction для визуальных эффектов

## Диагностические команды

```bash
# Проверить статус контейнеров
docker-compose ps

# Полные логи за последние 10 минут
docker-compose logs --since 10m

# Только ошибки
docker-compose logs celery 2>&1 | grep -E "(ERROR|❌|⚠️)"

# Статистика по TTS
docker-compose logs celery | grep "TTS completed"

# Проверить manifest файл последней презентации
cat .data/*/manifest.json | jq '.slides[] | select(.audio == null) | .id'
```

---

**Готово к тестированию!** 🎉

Если возникнут проблемы, проверяйте логи и используйте эти документы:
- `PIPELINE_DEEP_DIAGNOSTIC.md` - полная диагностика
- `PIPELINE_FIXES_APPLIED.md` - детали исправлений  
- `TTS_FAILURE_FIX.md` - исправление проблем с аудио
