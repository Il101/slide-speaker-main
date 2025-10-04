# 🔒 Аудит безопасности и анализ проекта Slide Speaker

**Дата проверки:** 1 октября 2025  
**Версия:** 1.0.0  
**Статус:** ⚠️ Обнаружены критические и средние уязвимости

---

## 📊 Общая оценка

| Категория | Оценка | Критичность |
|-----------|--------|-------------|
| **Безопасность** | 5/10 | 🔴 HIGH |
| **Архитектура** | 7/10 | 🟡 MEDIUM |
| **Код качество** | 6/10 | 🟡 MEDIUM |
| **Производительность** | 6/10 | 🟡 MEDIUM |
| **Общая оценка** | 6/10 | 🟡 MEDIUM |

---

## 🔴 КРИТИЧЕСКИЕ УЯЗВИМОСТИ

### 1. **Hardcoded Credentials в Docker Compose**
**Критичность:** 🔴 CRITICAL  
**Файл:** `docker-compose.yml`

```yaml
environment:
  - MINIO_ROOT_USER=minioadmin
  - MINIO_ROOT_PASSWORD=minioadmin
```

**Проблема:**
- Дефолтные учётные данные MinIO доступны публично
- Любой может получить доступ к хранилищу данных
- Потенциально возможна утечка файлов пользователей

**Решение:**
```yaml
environment:
  - MINIO_ROOT_USER=${MINIO_ROOT_USER:-minioadmin}
  - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD:-minioadmin}
```

---

### 2. **Path Traversal уязвимость**
**Критичность:** 🔴 CRITICAL  
**Файл:** `backend/app/main.py:224`

```python
lesson_dir = settings.DATA_DIR / lesson_id
lesson_dir.mkdir(exist_ok=True)
file_path = lesson_dir / file.filename  # ⚠️ НЕТ ВАЛИДАЦИИ!
with open(file_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)
```

**Проблема:**
- `file.filename` не санитизируется
- Возможна атака типа `../../etc/passwd`
- Злоумышленник может перезаписать системные файлы

**Эксплойт:**
```python
# Атакующий может загрузить файл с именем:
filename = "../../../root/.ssh/authorized_keys"
# И получить root доступ к серверу
```

**Решение:**
```python
import os
from pathlib import Path

def sanitize_filename(filename: str) -> str:
    """Безопасное извлечение имени файла"""
    # Убираем путь, оставляем только имя файла
    safe_name = os.path.basename(filename)
    # Удаляем опасные символы
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._- ")
    # Ограничиваем длину
    return safe_name[:255]

# Использование:
safe_filename = sanitize_filename(file.filename)
file_path = lesson_dir / safe_filename
```

---

### 3. **Отсутствие аутентификации и авторизации**
**Критичность:** 🔴 CRITICAL  
**Файл:** `backend/app/main.py`

**Проблема:**
- НЕТ механизма аутентификации пользователей
- Любой может загружать файлы без ограничений
- Любой может получить доступ к урокам других пользователей через `lesson_id`
- Отсутствует контроль доступа к данным

**Атака:**
```python
# Злоумышленник может перебрать UUID и получить чужие уроки:
import requests
import uuid

for _ in range(1000):
    lesson_id = str(uuid.uuid4())
    response = requests.get(f"http://api/lessons/{lesson_id}/manifest")
    if response.status_code == 200:
        print(f"Found lesson: {lesson_id}")
```

**Решение:**
```python
from fastapi import Depends, HTTPException, Header
import jwt

async def get_current_user(authorization: str = Header(...)):
    """Проверка JWT токена"""
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/upload")
async def upload_file(
    file: UploadFile, 
    user_id: str = Depends(get_current_user)  # ✅ Добавить!
):
    # Сохранять с привязкой к user_id
    lesson_dir = settings.DATA_DIR / user_id / lesson_id
```

---

### 4. **Недостаточная валидация загружаемых файлов**
**Критичность:** 🔴 CRITICAL  
**Файл:** `backend/app/main.py:213-215`

```python
file_ext = Path(file.filename).suffix.lower()
if file_ext not in settings.ALLOWED_EXTENSIONS:
    raise HTTPException(status_code=400, detail="Only PPTX and PDF files are allowed")
```

**Проблема:**
- Проверка только по расширению, а не по MIME type
- Можно загрузить `malware.exe.pdf`
- Нет проверки содержимого файла (magic bytes)
- Нет антивирусной проверки

**Решение:**
```python
import magic

def validate_file(file: UploadFile) -> bool:
    """Проверка типа файла по содержимому"""
    # Читаем первые байты
    header = file.file.read(2048)
    file.file.seek(0)
    
    # Проверяем MIME type
    mime = magic.from_buffer(header, mime=True)
    
    allowed_mimes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    ]
    
    if mime not in allowed_mimes:
        raise HTTPException(400, f"Invalid file type: {mime}")
    
    return True
```

---

## 🟡 СРЕДНИЕ УЯЗВИМОСТИ

### 5. **Отсутствие Rate Limiting на критичных endpoints**
**Критичность:** 🟡 MEDIUM  
**Файл:** `backend/app/main.py`

**Проблема:**
```python
@app.get("/lessons/{lesson_id}/manifest")
async def get_manifest(lesson_id: str):
    # ⚠️ НЕТ RATE LIMITING!
```

- Rate limiting только на `/upload` (10/min)
- Остальные endpoints не защищены от DDoS
- Возможна перегрузка сервера

**Решение:**
```python
@app.get("/lessons/{lesson_id}/manifest")
@limiter.limit("100/minute")  # ✅ Добавить!
async def get_manifest(request: Request, lesson_id: str):
    ...
```

---

### 6. **Уязвимость к SSRF через URL в манифесте**
**Критичность:** 🟡 MEDIUM  
**Файл:** `src/components/Player.tsx:128`

```tsx
const imageUrl = currentSlideImageSrc 
    ? `${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}${currentSlideImageSrc}` 
    : '';
```

**Проблема:**
- Если злоумышленник контролирует `manifest.json`, может внедрить вредоносные URL
- Браузер будет запрашивать внутренние сервисы
- Возможна SSRF атака через img src

**Решение:**
```python
def validate_asset_url(url: str) -> bool:
    """Проверка, что URL ведёт на разрешённые ресурсы"""
    parsed = urlparse(url)
    
    # Только относительные пути
    if parsed.scheme or parsed.netloc:
        raise ValueError("Only relative URLs allowed")
    
    # Нет path traversal
    if ".." in url:
        raise ValueError("Path traversal not allowed")
    
    return True
```

---

### 7. **Небезопасное использование `shutil.rmtree` с `ignore_errors=True`**
**Критичность:** 🟡 MEDIUM  
**Файл:** `backend/app/main.py:285`

```python
shutil.rmtree(lesson_dir, ignore_errors=True)
```

**Проблема:**
- Скрывает ошибки удаления
- Может оставить незащищённые данные на диске
- Нарушает принцип fail-fast

**Решение:**
```python
try:
    shutil.rmtree(lesson_dir)
except Exception as e:
    logger.error(f"Failed to cleanup {lesson_dir}: {e}")
    # Добавить в очередь на повторное удаление
    cleanup_queue.add(lesson_dir)
```

---

### 8. **Хранение чувствительных данных в логах**
**Критичность:** 🟡 MEDIUM  
**Файл:** множество файлов

```python
logger.info(f"Generated speaker notes: {speaker_notes}")
logger.info(f"API Key: {api_key[:20]}...")  # ⚠️ Частично раскрыто
```

**Проблема:**
- Логи могут содержать персональные данные
- API ключи частично раскрыты
- Нарушение GDPR/privacy

**Решение:**
```python
def redact_sensitive_data(data: str) -> str:
    """Редактирование чувствительных данных"""
    patterns = [
        (r'(api[_-]?key)["\s:=]+([a-zA-Z0-9]+)', r'\1: ***'),
        (r'(password)["\s:=]+([^\s]+)', r'\1: ***'),
        (r'(token)["\s:=]+([a-zA-Z0-9]+)', r'\1: ***'),
    ]
    for pattern, replacement in patterns:
        data = re.sub(pattern, replacement, data, flags=re.IGNORECASE)
    return data

logger.info(redact_sensitive_data(log_message))
```

---

### 9. **Отсутствие CSRF protection**
**Критичность:** 🟡 MEDIUM  
**Файл:** `backend/app/main.py`

**Проблема:**
- FastAPI по умолчанию не защищает от CSRF
- Frontend использует cookie-based auth (потенциально)
- Возможна CSRF атака через формы

**Решение:**
```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/upload")
async def upload_file(
    file: UploadFile,
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf_in_cookies(request)
    ...
```

---

### 10. **Небезопасное использование `dangerouslySetInnerHTML`**
**Критичность:** 🟡 MEDIUM  
**Файл:** `src/components/ui/chart.tsx:70`

```tsx
dangerouslySetInnerHTML={{
    __html: `...`
}}
```

**Проблема:**
- Потенциальная XSS уязвимость
- Если данные не санитизированы, возможно внедрение JS кода

**Решение:**
```tsx
import DOMPurify from 'dompurify';

dangerouslySetInnerHTML={{
    __html: DOMPurify.sanitize(htmlContent)
}}
```

---

## 🟢 НИЗКИЕ УЯЗВИМОСТИ И ПРЕДУПРЕЖДЕНИЯ

### 11. **Отсутствие версионирования API**
**Критичность:** 🟢 LOW

```python
# Сейчас:
@app.post("/upload")

# Лучше:
@app.post("/api/v1/upload")
```

---

### 12. **Недостаточное логирование событий безопасности**
**Критичность:** 🟢 LOW

Нет логирования:
- Неудачных попыток доступа
- Подозрительных действий пользователей
- Изменений в критичных данных

---

### 13. **Отсутствие HTTP Security Headers**
**Критичность:** 🟢 LOW

```python
# Добавить в middleware:
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

### 14. **Слабая конфигурация CORS**
**Критичность:** 🟢 LOW  
**Файл:** `backend/app/core/config.py:15-28`

```python
CORS_ORIGINS: list = [
    "http://localhost:3000",
    "http://localhost:5173",
    # ... множество origins
]
```

**Проблема:**
- Разрешено слишком много origins
- В production должен быть только один домен

**Решение:**
```python
CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "https://app.example.com").split(",")
```

---

### 15. **Нет backup стратегии для данных**
**Критичность:** 🟢 LOW

- Данные в `.data/` могут быть потеряны
- Нет автоматических бэкапов
- Нет disaster recovery плана

---

## 🏗️ АРХИТЕКТУРНЫЕ ПРОБЛЕМЫ

### 16. **Отсутствие базы данных**
**Проблема:**
- Метаданные хранятся в JSON файлах
- Сложно делать запросы и фильтрацию
- Нет транзакционности
- Проблемы с масштабированием

**Решение:**
```python
# Добавить PostgreSQL или MongoDB:
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Lesson(Base):
    __tablename__ = 'lessons'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    created_at = Column(DateTime)
    status = Column(String)
```

---

### 17. **Синхронная обработка в асинхронном контексте**
**Файл:** `backend/app/main.py:273-276`

```python
pipeline_result = process_lesson_full_pipeline(lesson_id)  # ⚠️ Синхронный!
```

**Проблема:**
- Блокирует event loop
- Тормозит другие запросы
- Не использует преимущества async/await

**Решение:**
```python
from celery import Celery

# Правильно через Celery:
task = process_lesson_full_pipeline.delay(lesson_id)
return {"lesson_id": lesson_id, "task_id": task.id}
```

---

### 18. **Отсутствие graceful shutdown**
**Критичность:** 🟢 LOW

```python
# Добавить обработку сигналов:
import signal

def shutdown_handler(signum, frame):
    logger.info("Shutting down gracefully...")
    # Завершить активные задачи
    # Закрыть соединения с БД
    # Сохранить состояние
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
```

---

## 🐛 КАЧЕСТВО КОДА И БАГИ

### 19. **Нет обработки ошибок в critical paths**
**Файл:** множество

```python
# Часто встречается:
try:
    result = some_operation()
except Exception as e:
    logger.error(f"Error: {e}")
    # ⚠️ А дальше что? Программа продолжает работу с ошибочным состоянием
```

**Решение:**
- Конкретные типы исключений
- Proper error recovery
- Circuit breaker pattern для внешних сервисов

---

### 20. **Memory leaks в генераторе визуальных эффектов**
**Файл:** `backend/workers/visual_cues_generator.py:17-186`

```python
# Кеш никогда не очищается:
@lru_cache(maxsize=100)
def _get_image_hash(image_path: str) -> str:
    ...

@lru_cache(maxsize=50)
def _cached_ocr_detection(image_hash: str, image_path: str):
    ...
```

**Проблема:**
- При большом количестве уроков кеш переполнится
- Память будет расти без ограничений

**Решение:**
```python
from cachetools import TTLCache

# Кеш с TTL (time-to-live):
cache = TTLCache(maxsize=100, ttl=3600)  # 1 час

@functools.lru_cache(maxsize=None)
def get_cache():
    return cache
```

---

### 21. **Race conditions в Celery tasks**
**Файл:** `backend/app/tasks.py`

```python
# Несколько воркеров могут одновременно обрабатывать один урок:
@celery_app.task(bind=True)
def process_lesson_full_pipeline(self, lesson_id: str):
    manifest_path = lesson_dir / "manifest.json"
    with open(manifest_path, "r") as f:  # ⚠️ Read
        manifest_data = json.load(f)
    
    # ... модификация ...
    
    with open(manifest_path, "w") as f:  # ⚠️ Write (race condition!)
        json.dump(manifest_data, f)
```

**Решение:**
```python
# Использовать distributed lock:
from redis import Redis
from redis.lock import Lock

redis_client = Redis.from_url(settings.REDIS_URL)

@celery_app.task(bind=True)
def process_lesson_full_pipeline(self, lesson_id: str):
    lock = Lock(redis_client, f"lesson:{lesson_id}", timeout=300)
    
    if not lock.acquire(blocking=False):
        raise Exception("Lesson is being processed by another worker")
    
    try:
        # ... обработка ...
    finally:
        lock.release()
```

---

### 22. **Нет мониторинга и алертинга**

**Проблема:**
- Нет метрик о состоянии системы
- Нет оповещений об ошибках
- Сложно диагностировать проблемы в production

**Решение:**
```python
# Интеграция с Prometheus:
from prometheus_client import Counter, Histogram, Gauge

upload_counter = Counter('uploads_total', 'Total uploads')
processing_time = Histogram('processing_seconds', 'Processing time')
active_lessons = Gauge('active_lessons', 'Active lessons')

@app.post("/upload")
async def upload_file(...):
    upload_counter.inc()
    with processing_time.time():
        # ... обработка ...
```

---

## 📦 DEPENDENCY ISSUES

### 23. **Устаревшие зависимости**
**Файл:** `backend/requirements.txt`

```
fastapi==0.104.1        # ⚠️ Текущая: 0.115.0 (security fixes)
uvicorn==0.24.0         # ⚠️ Текущая: 0.34.0
openai==1.3.7           # ⚠️ Текущая: 1.54.0
numpy<2.0.0             # ⚠️ Ограничение мешает обновлениям
```

**Решение:**
```bash
pip install --upgrade fastapi uvicorn openai
pip-audit  # Проверка на known vulnerabilities
```

---

### 24. **Отсутствие pinned versions для production**

```
# requirements.txt использует ==, но нет hash verification:
fastapi==0.104.1  # ✅ Хорошо, но...

# Лучше с хешами для production:
# pip install --require-hashes -r requirements.txt
fastapi==0.104.1 \
    --hash=sha256:abc123...
```

---

## 🔐 SECRETS MANAGEMENT

### 25. **API ключи в переменных окружения**
**Критичность:** 🟡 MEDIUM

```python
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
```

**Проблема:**
- Ключи в plain text в .env файлах
- .env файлы могут попасть в git
- Нет ротации ключей

**Решение:**
```python
# Использовать secrets manager:
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://myvault.vault.azure.net/", credential=credential)

OPENAI_API_KEY = client.get_secret("openai-api-key").value
```

---

## 🎯 РЕКОМЕНДАЦИИ ПО ПРИОРИТЕТАМ

### 🔴 КРИТИЧНО (исправить немедленно):

1. ✅ **Path Traversal** - добавить sanitize_filename
2. ✅ **Аутентификация** - внедрить JWT auth
3. ✅ **Hardcoded credentials** - использовать secrets
4. ✅ **Валидация файлов** - проверять MIME types

### 🟡 ВЫСОКИЙ ПРИОРИТЕТ (в течение недели):

5. ✅ Rate limiting на все endpoints
6. ✅ CSRF protection
7. ✅ Добавить PostgreSQL для метаданных
8. ✅ Distributed locks для Celery

### 🟢 СРЕДНИЙ ПРИОРИТЕТ (в течение месяца):

9. HTTP Security Headers
10. Улучшить логирование
11. Добавить мониторинг
12. Обновить зависимости

---

## 📋 CHECKLIST ДЛЯ PRODUCTION

- [ ] Аутентификация и авторизация
- [ ] Валидация всех входных данных
- [ ] Rate limiting на все endpoints
- [ ] HTTPS обязательно (TLS 1.3)
- [ ] Security headers
- [ ] CSRF protection
- [ ] XSS protection
- [ ] SQL/NoSQL injection protection (если добавите БД)
- [ ] Secrets в vault (не в .env)
- [ ] Логирование security events
- [ ] Мониторинг и алертинг
- [ ] Backup стратегия
- [ ] Disaster recovery план
- [ ] Penetration testing
- [ ] Code audit (SAST/DAST)
- [ ] Dependency scanning
- [ ] Container scanning (Docker images)
- [ ] WAF (Web Application Firewall)
- [ ] DDoS protection

---

## 🛠️ ИНСТРУМЕНТЫ ДЛЯ АУДИТА

### Автоматические сканеры:

```bash
# Python security
pip install bandit safety
bandit -r backend/
safety check

# Dependency vulnerabilities
pip install pip-audit
pip-audit

# Docker security
docker scan slide-speaker:latest

# SAST
semgrep --config=auto backend/

# Secrets scanning
gitleaks detect --source=.
```

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Guide](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)

---

## ✅ ЗАКЛЮЧЕНИЕ

**Проект имеет хорошую архитектурную основу**, но **требует серьёзной работы над безопасностью** перед развёртыванием в production.

**Основные риски:**
1. Отсутствие аутентификации (кто угодно может загружать и читать файлы)
2. Path Traversal (можно перезаписать системные файлы)
3. Hardcoded credentials (MinIO доступен всем)
4. Недостаточная валидация входных данных

**Рекомендуется:**
- Немедленно исправить критические уязвимости
- Провести penetration testing
- Внедрить CI/CD с автоматическими security checks
- Регулярно обновлять зависимости
- Добавить WAF и DDoS protection для production

**Оценка готовности к production:** ⚠️ **НЕ ГОТОВ** (требуется security hardening)

---

**Подготовлено:** AI Security Audit Tool  
**Контакт:** security@example.com
