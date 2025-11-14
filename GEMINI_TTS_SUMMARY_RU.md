# 📋 Gemini TTS Flash 2.5: Краткая сводка

**Дата:** 12 ноября 2025

---

## ✅ Что РАБОТАЕТ и НОВОЕ

### 🎭 1. Natural Language Prompts (Новое!)
```python
prompt="Speak like a friendly tutor explaining a complex topic"
prompt="Narrate in a calm, professional tone for a documentary"
prompt="React with an amused laugh"
```
**Применение:** Контроль тона, эмоций, акцента через естественный язык

### 🏷️ 2. Markup Tags - 15+ тегов (Новое!)

**Non-speech sounds:**
- `[sigh]` `[laughing]` `[uhm]`

**Style modifiers:**
- `[whispering]` `[extremely fast]` `[shouting]` `[sarcasm]` `[robotic]`

**Pauses:**
- `[short pause]` `[medium pause]` `[long pause]`

**Пример:**
```python
text = "[whispering] Don't tell anyone [medium pause] about this."
```

### 🎤 3. Multi-speaker synthesis
- Freeform text: `"Sam: Hi!\nBob: Hello!"`
- Structured turns для natural pronunciation
- 30 голосов (те же что в Chirp 3 HD)

### 📡 4. Streaming synthesis
- Low latency для real-time
- Half-Close signal
- Async chunks отправка

### 🌍 5. Языки
- **Русский (ru-RU)** ✅ GA
- 24 языка GA + 60+ Preview
- Голоса язык-независимые

---

## ❌ Что НЕ работает

### 🚫 1. SSML (нет поддержки)
- Нет `<speak>`, `<break>`, `<emphasis>`, `<prosody>`
- Замена: markup tags `[pause]`

### �� 2. **TIMEPOINTS (КРИТИЧНО!)**

**Тест:**
```bash
curl -d '{"enableTimePointing": ["SSML_MARK"]}' ...
```

**Ответ:**
```json
{
  "error": {
    "code": 400,
    "message": "Unknown name \"enableTimePointing\": Cannot find field"
  }
}
```

**Воздействие:**
- ❌ Stage 5 (Visual Effects) не работает
- ❌ Невозможна синхронизация spotlight/cascade/highlight
- ❌ Потеря 60-96 word timings на слайд

---

## 🎯 Вердикт

### ❌ Миграция НЕ рекомендуется

**Причина:** Отсутствие timepoints = невозможность визуальных эффектов

---

## 💡 Альтернатива: Гибридный подход

### Используйте **Gemini TTS** для:
✅ Простые превью без VFX  
✅ Демо-режим  
✅ Чат-боты  
✅ Multi-speaker диалоги  

### Используйте **Chirp 3 HD** для:
✅ Презентации с визуальными эффектами (production)  
✅ Основной продукт  
✅ Всё, где нужны timepoints  

---

## 📊 Сравнительная таблица

| Возможность | Chirp 3 HD | Gemini TTS | Вывод |
|-------------|-----------|-----------|-------|
| Timepoints | ✅ | ❌ | **БЛОКЕР** |
| SSML | ✅ | ❌ | Деградация |
| Prompts | ❌ | ✅ | Новое |
| Markup tags | ❌ | ✅ | Новое |
| Русский язык | ✅ | ✅ | OK |
| Streaming | ✅ | ✅ | OK |
| Multi-speaker | ✅ | ✅ | OK |

---

## 🔗 Детали

Полная документация: `GEMINI_TTS_CAPABILITIES_FULL.md`  
Результаты тестов: `.test_results/gemini_final/`

---

**Итог:** Gemini TTS - мощная технология, но **не подходит** для нашего use case из-за отсутствия timepoints.
