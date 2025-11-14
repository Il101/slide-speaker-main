# Излишнее в промпте smart_script_generator.py

## ❌ **Что нужно убрать:**

### 1. **Инструкции про [visual:XX] и [lang:XX] markers** (строка ~200-205, 477-550)

**Было:**
```
🚨 CRITICAL RULE:
When you encounter ANY foreign language word:
1. Wrap with [visual:XX]term[/visual] or [lang:XX]term[/lang]
2. Language codes: de=German, en=English, etc.

Examples:
✅ CORRECT: "Рассмотрим [lang:de]Das Blatt[/lang]"
❌ WRONG: "Рассмотрим Das Blatt"
```

**Почему не нужно:**
- Translation теперь на уровне OCR (text_original, text_translated)
- LLM генерирует **только русский текст** из text_translated
- Иностранных слов в генерируемом тексте **не будет**
- Whisper работает с русским текстом напрямую

**Убрать:**
- Весь раздел "FOREIGN TERMS MARKUP (3 OPTIONS)" (~200 строк!)
- Примеры с [visual:de], [lang:en]
- Объяснения про коды языков

---

### 2. **Инструкции про "(Original Foreign Term)" в скобках** (строка ~552-580)

**Было:**
```
🎯 CRITICAL FOR VISUAL SYNC - Original Terms in Parentheses:
When you mention a term in FOREIGN language, add original in parentheses:
- Format: "Russian translation (Original Foreign Term)"
- Example: "эпидермис (Epidermis)"
```

**Почему не нужно:**
- Whisper matching работает через text_translated
- Не нужны оригинальные термины для синхронизации
- Усложняет текст без пользы

**Убрать:**
- Весь раздел "Original Terms in Parentheses"
- Все примеры с (Epidermis), (Mesophyll)

---

### 3. **Russian stress marks инструкции** (строка ~207-230)

**Было:**
```
📍 RUSSIAN STRESS MARKS (for correct pronunciation):
For ambiguous Russian words, add stress mark ́ (U+0301):
- за́мок (castle) vs замо́к (lock)
- о́рган (organ-body) vs орга́н (organ-music)
```

**Почему не нужно:**
- Silero TTS использует `put_accent=True` - автоматически ставит ударения!
- Не нужно вручную добавлять combining accents
- LLM всё равно часто ошибается с ударениями

**Убрать:**
- Весь раздел "RUSSIAN STRESS MARKS"
- Список примеров с ударениями
- Инструкции как печатать U+0301

---

### 4. **Избыточные SSML prosody инструкции** (строка ~220-275)

**Было (~100 строк про SSML):**
```
🎭 PROSODY & INTONATION (SSML for natural speech):

1. <prosody rate="..."> - Speech rate for emphasis
2. <prosody pitch="..."> - Pitch for emotional coloring  
3. <break time="...ms"/> - Pauses for rhythm
4. <emphasis level="..."> - Stress important words
5. [pause:XXXms] - Custom pause marker
6. [pitch:+/-X%] - Custom pitch change
7. [rate:X%] - Custom rate change

Examples: (показывает 10+ примеров)
...
```

**Почему сократить:**
Silero TTS поддерживает **только базовые теги:**
- ✅ `<prosody rate="X">` - скорость речи  
- ✅ `<break time="Xms"/>` - паузы
- ❌ `<prosody pitch="X">` - **не поддерживается!**
- ❌ `<emphasis level="X">` - **не поддерживается!**
- ❌ `[pause:XXXms]`, `[pitch:X%]`, `[rate:X%]` - **custom markers не нужны!**

**Упростить до:**
```
🎭 SSML для естественной речи (только для Silero TTS):

Silero поддерживает ТОЛЬКО 2 тега:
1. <prosody rate="X"> - скорость (0.8=медленно, 1.0=норма, 1.2=быстро)
2. <break time="Xms"/> - пауза (300ms, 500ms, 800ms)

Используй РЕДКО (2-3 раза на слайд):
✅ "<prosody rate='0.9'>Фотосинтез</prosody> - это процесс..."
✅ "Итак <break time='500ms'/> перейдём к выводам"

❌ НЕ используй: <pitch>, <emphasis>, [pause:], [rate:]
```

Сократить с ~100 строк до ~15 строк.

---

### 5. **Дублирование anti-reading инструкций**

В промпте 3 раза повторяется одно и то же:

**Строка 186-192:**
```
1. Говори ТОЛЬКО о том, что ЕСТЬ на слайде
2. НЕ добавляй информацию из твоих знаний
3. НЕ делай общих утверждений
```

**Строка 461-467 (в промпте):**
```
EXPLANATION STRATEGY:
1. Cover ONLY what is on the slide
2. Be specific, not generic
3. Don't add extra information
```

**Строка 489-495 (ещё раз):**
```
🚨 STRICT RULE:
- ONLY speak about slide content
- NO external knowledge
- NO generalizations
```

**Упростить:**
Оставить **один раз** в начале system_prompt, убрать повторы из user prompt.

---

## ✅ **Что оставить (актуально):**

1. ✅ Основные правила: "Говори только о слайде, не добавляй информацию"
2. ✅ Базовые SSML теги: `<prosody rate>` и `<break time>`
3. ✅ Инструкции про списки: "Упомяни КАЖДЫЙ элемент"
4. ✅ Length limits: max 300 words
5. ✅ JSON формат ответа
6. ✅ group_id привязка к semantic_map

---

## 📊 **Экономия токенов:**

**Текущий system_prompt:** ~1000 строк, ~6000 токенов  
**После очистки:** ~300 строк, ~1800 токенов  
**Экономия:** ~4200 токенов на каждый слайд!

На презентацию из 18 слайдов: **~75,000 токенов экономии** 💰

---

## 🎯 **Приоритеты очистки:**

1. **HIGH**: Убрать [visual:XX], [lang:XX] инструкции (~200 строк)
2. **HIGH**: Убрать "(Original Term)" инструкции (~30 строк)
3. **MEDIUM**: Сократить SSML инструкции (~80 строк)
4. **MEDIUM**: Убрать stress marks инструкции (~25 строк)
5. **LOW**: Убрать дублирование anti-reading (~20 строк)

**Итого:** ~355 строк можно убрать/сократить!
