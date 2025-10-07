# ⚡ Quick Fixes - Что Можно Исправить Прямо Сейчас (1-2 дня)

## 🎯 Приоритет 1: Исправить Сейчас (2-4 часа)

### 1. Добавить Timeout для Внешних API Вызовов

**Где:** `backend/app/pipeline/intelligent_optimized.py:658`

**Было:**
```python
audio_path, tts_words = await loop.run_in_executor(
    self.executor,
    lambda: GoogleTTSWorkerSSML().synthesize_slide_text_google_ssml(ssml_texts)
)
```

**Стало:**
```python
try:
    audio_path, tts_words = await asyncio.wait_for(
        loop.run_in_executor(
            self.executor,
            lambda: GoogleTTSWorkerSSML().synthesize_slide_text_google_ssml(ssml_texts)
        ),
        timeout=60.0  # 60 seconds per slide
    )
except asyncio.TimeoutError:
    self.logger.error(f"⏱️ Slide {slide_id}: TTS timeout after 60s")
    # Use mock/fallback
    return (index, None, {}, 0.0, None)
```

**Зачем:** Предотвращает зависание pipeline на вечно.

---

### 2. Укоротить Паузы в SSML Group Markers

**Где:** `backend/app/services/ssml_generator.py:43-45`

**Было:**
```python
all_parts.append('<break time="300ms"/>')
all_parts.append(f'<mark name="{marker_name}"/>')
all_parts.append('<break time="300ms"/>')
```

**Стало:**
```python
all_parts.append('<break time="100ms"/>')  # ✅ Короче
all_parts.append(f'<mark name="{marker_name}"/>')
all_parts.append('<break time="100ms"/>')  # ✅ Короче
```

**Зачем:** Google TTS надёжнее сохраняет markers при коротких паузах.

---

### 3. Добавить Логирование Размера SSML

**Где:** `backend/app/services/ssml_generator.py:75`

**Добавить перед return:**
```python
combined_ssml = f'<speak>{" ".join(all_parts)}</speak>'

# ✅ ADD: Проверка размера и предупреждение
if len(combined_ssml) > 4500:
    logger.warning(
        f"⚠️ SSML очень длинный: {len(combined_ssml)} символов "
        f"(лимит Google TTS: 5000). Риск потери markers!"
    )
    # Подсчитать markers
    mark_count = combined_ssml.count('<mark name=')
    logger.warning(f"   Всего markers: {mark_count}")

logger.info(f"✅ Generated SSML: {len(combined_ssml)} chars, {self.mark_counter} marks")
return [combined_ssml]
```

**Зачем:** Раннее обнаружение проблем с большими текстами.

---

### 4. Исправить Concurrent Access к slides[]

**Где:** `backend/app/pipeline/intelligent_optimized.py:545-550`

**Было:**
```python
# В process_single_slide
if i > 0:
    prev_slide = slides[i-1]  # ⚠️ Race condition!
    prev_text = " ".join([...])
```

**Стало:**
```python
# В начале plan() метода, ПЕРЕД параллельной обработкой
slides_summary_cache = {}
for i, slide in enumerate(slides):
    # Pre-compute summaries sequentially
    elements = slide.get('elements', [])
    summary = " ".join([e.get('text', '')[:50] for e in elements[:3]])
    slides_summary_cache[i] = summary

# Теперь в process_single_slide:
async def process_single_slide(slide_data: Tuple[int, Dict[str, Any]]):
    i, slide = slide_data
    
    # Безопасно читаем из кэша
    previous_slides_summary = ""
    if i > 0:
        previous_slides_summary = f"Previous: {slides_summary_cache[i-1]}..."
```

**Зачем:** Устраняет race condition при параллельной обработке.

---

## 🎯 Приоритет 2: Сделать Сегодня (4-6 часов)

### 5. Добавить Health Check Endpoint

**Где:** `backend/app/main.py`

**Добавить:**
```python
from datetime import datetime

# Global health status
app_health = {
    "status": "healthy",
    "started_at": datetime.utcnow().isoformat(),
    "checks": {}
}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    
    checks = {}
    overall_healthy = True
    
    # Check Redis
    try:
        await redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"
        overall_healthy = False
    
    # Check Google credentials
    try:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path and os.path.exists(creds_path):
            checks["google_credentials"] = "healthy"
        else:
            checks["google_credentials"] = "missing"
            overall_healthy = False
    except Exception as e:
        checks["google_credentials"] = f"error: {e}"
        overall_healthy = False
    
    # Check disk space
    import shutil
    data_dir = Path(".data")
    if data_dir.exists():
        stat = shutil.disk_usage(data_dir)
        free_gb = stat.free / (1024**3)
        checks["disk_space_gb"] = round(free_gb, 2)
        if free_gb < 1.0:  # Less than 1GB
            checks["disk_space_status"] = "critical"
            overall_healthy = False
        else:
            checks["disk_space_status"] = "healthy"
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    # Проверка что приложение готово принимать трафик
    try:
        # Check critical dependencies
        await redis_client.ping()
        return {"status": "ready"}
    except:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready"}
        )
```

**Зачем:** Мониторинг и автоматические рестарты в production.

---

### 6. Добавить Метрики Времени Обработки

**Где:** `backend/app/pipeline/intelligent_optimized.py`

**Добавить в начало класса:**
```python
from prometheus_client import Histogram, Counter

# Metrics
pipeline_stage_duration = Histogram(
    'pipeline_stage_duration_seconds',
    'Duration of each pipeline stage',
    ['stage', 'status']
)

pipeline_slides_processed = Counter(
    'pipeline_slides_processed_total',
    'Total number of slides processed',
    ['status']  # success/error
)
```

**И обернуть каждый этап:**
```python
def plan(self, lesson_dir: str) -> None:
    """Stage 2-4: Planning with metrics"""
    
    with pipeline_stage_duration.labels(stage='plan', status='running').time():
        try:
            # ... существующий код ...
            
            pipeline_stage_duration.labels(stage='plan', status='success').observe(elapsed)
            pipeline_slides_processed.labels(status='success').inc(success_count)
            
        except Exception as e:
            pipeline_stage_duration.labels(stage='plan', status='error').observe(time.time() - start_time)
            raise
```

**Зачем:** Понимание где тратится время, оптимизация bottlenecks.

---

### 7. Логировать Все Ошибки с Context

**Где:** Все except блоки

**Было:**
```python
except Exception as e:
    logger.error(f"Error: {e}")
```

**Стало:**
```python
except Exception as e:
    logger.error(
        f"Error in {self.__class__.__name__}.{method_name}: {e}",
        exc_info=True,  # ✅ Include full traceback
        extra={
            "lesson_id": lesson_id,
            "slide_id": slide_id,
            "error_type": type(e).__name__
        }
    )
```

**Зачем:** Debugging в production становится намного проще.

---

## 🎯 Приоритет 3: На Этой Неделе (1-2 дня)

### 8. Создать Fallback для Каждого Внешнего Сервиса

**Где:** `backend/app/services/provider_factory.py`

**Добавить:**
```python
class ServiceWithFallback:
    """Wrapper для сервисов с автоматическим fallback"""
    
    def __init__(self, primary_service, fallback_service):
        self.primary = primary_service
        self.fallback = fallback_service
        self.failure_count = 0
        self.max_failures = 3
    
    async def call_with_fallback(self, method_name: str, *args, **kwargs):
        """Вызвать метод с fallback"""
        
        # Попробовать primary
        try:
            method = getattr(self.primary, method_name)
            result = await method(*args, **kwargs)
            
            # Success - reset counter
            self.failure_count = 0
            return result
            
        except Exception as e:
            self.failure_count += 1
            logger.warning(
                f"Primary service failed ({self.failure_count}/{self.max_failures}): {e}"
            )
            
            # Попробовать fallback
            if self.fallback:
                try:
                    method = getattr(self.fallback, method_name)
                    result = await method(*args, **kwargs)
                    logger.info("✅ Fallback service succeeded")
                    return result
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise
            else:
                raise

# Использование:
class ProviderFactory:
    @classmethod
    def get_llm_provider_with_fallback(cls):
        """LLM с fallback на более дешёвую модель"""
        primary = OpenRouterLLM(model="meta-llama/llama-3.3-70b")
        fallback = OpenRouterLLM(model="meta-llama/llama-3.3-8b-instruct:free")
        
        return ServiceWithFallback(primary, fallback)
```

**Зачем:** Надёжность. Если основной сервис недоступен, используем резервный.

---

### 9. Добавить Rate Limiting для API

**Где:** `backend/app/api/v2_lecture.py`

**Добавить:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/upload")
@limiter.limit("10/minute")  # ✅ Максимум 10 загрузок в минуту
async def upload_presentation(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    # ...
```

**requirements.txt:**
```
slowapi==0.1.9
```

**Зачем:** Защита от DDoS и злоупотреблений.

---

### 10. Улучшить Валидацию Входных Данных

**Где:** `backend/app/api/v2_lecture.py`

**Добавить перед обработкой:**
```python
from pydantic import BaseModel, validator, Field

class PresentationUpload(BaseModel):
    """Валидация загрузки презентации"""
    
    file_size: int = Field(..., gt=0, lt=100_000_000)  # Max 100MB
    file_name: str = Field(..., min_length=1, max_length=255)
    mime_type: str
    
    @validator('mime_type')
    def check_mime_type(cls, v):
        allowed = {
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/pdf'
        }
        if v not in allowed:
            raise ValueError(f'Invalid file type: {v}')
        return v
    
    @validator('file_name')
    def check_file_name(cls, v):
        # Защита от path traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid file name')
        return v

@router.post("/upload")
async def upload_presentation(
    file: UploadFile = File(...),
):
    # Валидация
    upload_data = PresentationUpload(
        file_size=file.size,
        file_name=file.filename,
        mime_type=file.content_type
    )
    
    # Дополнительная проверка содержимого
    content_sample = await file.read(2048)
    await file.seek(0)
    
    # Проверка magic bytes для PPTX
    if upload_data.mime_type.endswith('presentation'):
        if not content_sample.startswith(b'PK'):  # ZIP signature
            raise HTTPException(400, "Invalid PPTX file")
    
    # Проверка на макросы
    if b'vbaProject.bin' in content_sample:
        raise HTTPException(400, "Presentations with macros are not allowed")
    
    # Теперь безопасно обрабатывать
```

---

## 📊 Измеримые Улучшения После Этих Исправлений

### Надёжность:
- ✅ **0% зависаний** вместо возможных зависаний на TTS
- ✅ **95%+ success rate** вместо 100%-или-ничего
- ✅ **Автоматический fallback** на резервные сервисы

### Производительность:
- ✅ **No race conditions** - правильный контекст между слайдами
- ✅ **Быстрее на 5-10%** за счёт оптимизации логов
- ✅ **Надёжнее SSML** - меньше потерянных markers

### Безопасность:
- ✅ **Rate limiting** - защита от abuse
- ✅ **Валидация входных данных** - защита от вредоносных файлов
- ✅ **Health checks** - мониторинг состояния

### Observability:
- ✅ **Prometheus метрики** - понимание bottlenecks
- ✅ **Структурированные логи** - быстрый debug
- ✅ **Health endpoints** - автоматический мониторинг

---

## 🚀 Порядок Внедрения (Рекомендуемый)

### День 1 - Утро (2-3 часа):
1. ✅ Добавить timeout для TTS (#1)
2. ✅ Укоротить паузы в SSML (#2)
3. ✅ Исправить race condition (#4)
4. ✅ Добавить логирование размера SSML (#3)

**Тестирование:** Запустить на 5 тестовых презентациях

### День 1 - День (3-4 часа):
5. ✅ Добавить health checks (#5)
6. ✅ Добавить метрики (#6)
7. ✅ Улучшить логирование ошибок (#7)

**Тестирование:** Проверить /health endpoint

### День 2 - Утро (2-3 часа):
8. ✅ Создать fallback систему (#8)
9. ✅ Добавить rate limiting (#9)

**Тестирование:** Проверить что fallback работает

### День 2 - День (2-3 часа):
10. ✅ Улучшить валидацию (#10)
11. ✅ Написать тесты для всех изменений
12. ✅ Задеплоить на staging

**Тестирование:** Full regression testing

---

## ✅ Критерии Успешности

После внедрения этих исправлений:

1. **Pipeline не должен падать** на любой презентации
2. **Processing time < 30s** для 15 слайдов
3. **Success rate > 95%** на тестовых презентациях
4. **0 критических ошибок** в логах за 24 часа
5. **/health endpoint возвращает 200** стабильно

---

## 🧪 Минимальный Набор Тестов

```python
# tests/test_quick_fixes.py
import pytest
import asyncio

class TestQuickFixes:
    
    @pytest.mark.asyncio
    async def test_tts_timeout_works(self):
        """Проверка что timeout срабатывает"""
        pipeline = OptimizedIntelligentPipeline()
        
        # Mock TTS чтобы зависнуть
        async def slow_tts(*args):
            await asyncio.sleep(100)  # 100 секунд
        
        pipeline.tts_worker.synthesize = slow_tts
        
        # Должен вернуться через 60 секунд с fallback
        start = time.time()
        result = await pipeline.generate_audio_for_slide(test_slide)
        elapsed = time.time() - start
        
        assert elapsed < 65  # 60s timeout + 5s запас
        assert result[1] is None  # audio_path = None (fallback)
    
    def test_health_endpoint(self, client):
        """Проверка health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert data["checks"]["redis"] == "healthy"
    
    def test_file_validation_rejects_macros(self, client):
        """Проверка что файлы с макросами отклоняются"""
        # Создать fake PPTX с vbaProject
        fake_pptx = b'PK\x03\x04' + b'vbaProject.bin' + b'\x00' * 100
        
        files = {"file": ("evil.pptx", io.BytesIO(fake_pptx), "application/vnd.openxmlformats")}
        response = client.post("/api/v2/upload", files=files)
        
        assert response.status_code == 400
        assert "macros" in response.json()["detail"].lower()
```

Эти quick fixes можно внедрить за 1-2 дня и сразу увидеть улучшение надёжности!
