# 🚀 ЗАПУСК ПРОЕКТА С HYBRID PIPELINE ПО УМОЛЧАНИЮ

## ✅ Готово!

**Hybrid Pipeline теперь является пайплайном по умолчанию!**

При запуске проекта без дополнительных настроек будет использоваться:

- 🔍 **Google Document AI** для OCR
- 🤖 **OpenRouter Grok** для генерации контента  
- 🔊 **Google TTS** для синтеза речи
- ☁️ **Google Cloud Storage** для хранения файлов

## 🏃‍♂️ Быстрый запуск

### 1. Backend
```bash
cd backend
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 2. Frontend
```bash
npm install
npm run dev
```

### 3. Тестирование
```bash
curl -F "file=@test_presentation.pptx" "http://localhost:8001/upload"
```

## 🔧 Что изменилось

### В `backend/app/core/config.py`:
```python
# Старые значения по умолчанию
OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "easyocr")      # ❌
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")       # ❌  
TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "mock")         # ❌
STORAGE: str = os.getenv("STORAGE", "minio")                  # ❌

# Новые значения по умолчанию (Hybrid Pipeline)
OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "google")       # ✅
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openrouter")   # ✅
TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "google")       # ✅
STORAGE: str = os.getenv("STORAGE", "gcs")                    # ✅
```

## 📁 Файлы конфигурации

- `backend_env_hybrid_default.env` - полная конфигурация Hybrid pipeline
- `backend/app/core/config.py` - обновленные значения по умолчанию

## ⚠️ Важно

Для работы Hybrid pipeline нужны API ключи:

1. **Google Cloud** - файл `inspiring-keel-473421-j2-22cc51dfb336.json`
2. **OpenRouter** - API ключ для доступа к Grok

Если ключи не настроены, система автоматически переключится в mock режим.

## 🎯 Результат

Теперь при запуске проекта **сразу** будет использоваться мощный Hybrid pipeline с реальными сервисами Google и OpenRouter!

---

**Статус:** ✅ **ГОТОВО К ИСПОЛЬЗОВАНИЮ**  
**Дата:** 30 сентября 2025
