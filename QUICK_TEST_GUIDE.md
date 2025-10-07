# 🚀 Quick Test Guide - New Pipeline Methods

## Этап 1: Добавлены новые методы ✅

Новые методы в pipeline:
- `ingest_v2()` - PPTX → PNG конвертация
- `extract_elements_ocr()` - OCR извлечение

**Старый код НЕ изменён** - можно безопасно тестировать!

---

## 🧪 Как Протестировать

### Вариант 1: Быстрый тест (рекомендуется)

```bash
# 1. Запустить тестовый скрипт
python test_new_pipeline.py

# 2. Проверить результаты
ls -la /tmp/test_lesson_new_pipeline/
```

**Ожидаемый результат:**
```
✅ ingest_v2() SUCCESS: Created N PNG files
✅ Manifest created with N slides
✅ extract_elements_ocr() SUCCESS: Extracted M total elements
✅ ALL TESTS PASSED!
```

---

### Вариант 2: Полный тест с реальной презентацией

```bash
# Использовать test_real.pptx (более реалистичный)
cp test_real.pptx /tmp/test_lesson/test.pptx
python test_new_pipeline.py
```

---

## 📁 Что Создаётся

```
/tmp/test_lesson_new_pipeline/
├── test.pptx                    ← Оригинальный файл
├── manifest.json                ← Метаданные + OCR элементы
└── slides/
    ├── 001.png                 ← Конвертированные слайды
    ├── 002.png
    └── ...
```

---

## ✅ Критерии Успеха

1. ✅ PNG файлы созданы в `slides/`
2. ✅ `manifest.json` содержит слайды
3. ✅ Каждый слайд имеет `elements` (OCR результаты)
4. ✅ Нет ошибок в логах

---

## 🐛 Если Что-то Не Работает

### Проблема: "No PPTX file found"
```bash
# Убедитесь что test_presentation.pptx существует
ls -lh test_presentation.pptx

# Или используйте test_real.pptx
cp test_real.pptx test_presentation.pptx
```

### Проблема: "PyMuPDF not found"
```bash
# Установить PyMuPDF (должен быть в requirements.txt)
pip install PyMuPDF
```

### Проблема: "OCR extraction failed"
```bash
# Проверить OCR_PROVIDER
echo $OCR_PROVIDER

# Проверить Google credentials
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -lh $GOOGLE_APPLICATION_CREDENTIALS

# Fallback сработает автоматически - тест должен пройти
```

---

## 🎯 После Успешного Теста

Если тест прошёл успешно:

1. ✅ **Этап 1 завершён** - новые методы работают
2. ⏭️ **Переходим к Этапу 2** - интеграция в main.py с feature flag
3. 🔧 **Feature flag:** `USE_NEW_PIPELINE=true` для тестирования в production

---

## 📊 Производительность

**Тестовая презентация (3 слайда):**
- Stage 1 (PPTX→PNG): ~1-2 секунды
- Stage 2 (OCR): ~1-3 секунды (зависит от кэша)
- **Общее:** ~2-5 секунд

**Реальная презентация (15 слайдов):**
- Stage 1: ~5-10 секунд
- Stage 2: ~5-15 секунд (с кэшем быстрее)
- **Общее:** ~10-25 секунд

---

## 💡 Важно

- ❌ **Не удалять старый код** - он пока работает в production
- ✅ **Тестировать в изоляции** - `/tmp/test_lesson_new_pipeline/`
- ✅ **Проверять логи** - все этапы должны быть в консоли
- ✅ **Feature flag выключен** - `USE_NEW_PIPELINE=false` (default)

---

**Готовы продолжить?** После успешного теста переходим к Этапу 2! 🚀
