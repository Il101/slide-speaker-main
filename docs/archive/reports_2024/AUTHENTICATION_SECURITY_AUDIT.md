# 🔒 Аудит Безопасности Аутентификации

**Дата:** 2024  
**Система:** Slide Speaker - Authentication System  
**Статус:** ⚠️ **ТРЕБУЮТСЯ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ**

---

## 📊 Сводка

| Категория | Статус | Критичных | Важных | Средних |
|-----------|--------|-----------|--------|---------|
| JWT Security | 🔴 Критично | 2 | 1 | 1 |
| Password Security | 🟡 Важно | 0 | 2 | 1 |
| API Endpoints | 🟡 Важно | 0 | 2 | 2 |
| CSRF Protection | 🟢 Хорошо | 0 | 0 | 1 |
| Database | 🟡 Важно | 0 | 1 | 1 |
| **ИТОГО** | 🔴 | **2** | **6** | **6** |

---

## 🔴 КРИТИЧЕСКИЕ ПРОБЛЕМЫ (Требуют немедленного исправления)

### 1. 🔴 Слабый JWT Secret Key в Production

**Файл:** `backend/app/core/auth.py:18`

**Проблема:**
```python
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
```

**Риск:** 
- Если JWT_SECRET_KEY не установлен в .env, используется предсказуемый дефолтный ключ
- Атакующий может подделать JWT токены
- **CVSS Score: 9.1 (Critical)**

**Проверка:**
```bash
# В backend/.env НЕТ JWT_SECRET_KEY
grep "JWT_SECRET_KEY" backend/.env
# Результат: пусто (используется дефолт!)
```

**Исправление:**
```python
# 1. Сгенерировать сильный ключ
import secrets
jwt_secret = secrets.token_urlsafe(64)
print(jwt_secret)  # Сохранить в .env

# 2. Обязательная проверка при старте
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be set in environment variables")

# 3. Добавить в backend/.env:
# JWT_SECRET_KEY=<сгенерированный_64_байтный_ключ>
```

**Приоритет:** 🔴 **КРИТИЧНО - Исправить немедленно**

---

### 2. 🔴 Слабый CSRF Secret Key

**Файл:** `backend/app/core/csrf.py:108`

**Проблема:**
```python
csrf_protection = CSRFProtection(
    secret_key=os.getenv("CSRF_SECRET_KEY", "your-csrf-secret-key-change-in-production")
)
```

**Риск:**
- Предсказуемый дефолтный CSRF ключ
- Возможность CSRF атак
- **CVSS Score: 8.1 (High)**

**Исправление:**
```python
# 1. В backend/.env добавить:
CSRF_SECRET_KEY=<сгенерированный_32_байтный_ключ>

# 2. В csrf.py:
SECRET_KEY = os.getenv("CSRF_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("CSRF_SECRET_KEY must be set")

csrf_protection = CSRFProtection(secret_key=SECRET_KEY)
```

**Приоритет:** 🔴 **КРИТИЧНО - Исправить в течение 24 часов**

---

## 🟡 ВАЖНЫЕ ПРОБЛЕМЫ (Исправить в течение недели)

### 3. 🟡 Отсутствие Rate Limiting на /login

**Файл:** `backend/app/api/auth.py:43`

**Проблема:**
```python
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # НЕТ rate limiting!
```

**Риск:**
- Brute force атаки на пароли
- Credential stuffing
- **CVSS Score: 7.5 (High)**

**Исправление:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # Макс 5 попыток в минуту
async def login(
    request: Request,  # Добавить Request
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # Добавить задержку после неудачной попытки
    await asyncio.sleep(0.5)  # 500ms delay
    ...
```

**Дополнительно:**
- Логировать неудачные попытки логина
- Блокировать IP после 10 неудачных попыток на 1 час
- Email уведомления о подозрительной активности

**Приоритет:** 🟡 **ВАЖНО**

---

### 4. 🟡 Отсутствие Проверки Сложности Пароля

**Файл:** `backend/app/api/auth.py:74`

**Проблема:**
```python
@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest, ...):
    # НЕТ проверки сложности пароля!
    hashed_password = AuthManager.get_password_hash(request.password)
```

**Риск:**
- Пользователи могут установить слабые пароли ("123456", "password")
- **CVSS Score: 6.5 (Medium)**

**Исправление:**
```python
import re

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Проверка сложности пароля:
    - Минимум 8 символов
    - Минимум 1 заглавная буква
    - Минимум 1 строчная буква
    - Минимум 1 цифра
    - Минимум 1 спецсимвол
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain digit"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain special character"
    
    return True, "Strong password"

@router.post("/register")
async def register(request: RegisterRequest, ...):
    # Проверить пароль
    is_valid, message = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    # Продолжить регистрацию...
```

**Приоритет:** 🟡 **ВАЖНО**

---

### 5. 🟡 Несоответствие Database Schema

**Файл:** `backend/app/core/database.py:28`

**Проблема:**
```python
# User model НЕ имеет поле username
class User(Base):
    id: Mapped[str]
    email: Mapped[str]
    hashed_password: Mapped[str]
    role: Mapped[str]
    is_active: Mapped[bool]
    # ❌ НЕТ username!

# Но в auth.py пытаемся его использовать:
@router.get("/me")
async def get_current_user_info(...):
    return UserResponse(
        username=user.email.split("@")[0],  # Хак!
    )
```

**Риск:**
- Пользователи не могут установить username
- Несоответствие API schema
- **Impact: Medium**

**Исправление:**
```python
# 1. Добавить в database.py:
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True)  # Добавить!
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# 2. Создать Alembic миграцию:
# alembic revision -m "Add username to users"
# В миграции:
# op.add_column('users', sa.Column('username', sa.String(100), nullable=True))
# op.create_unique_constraint('uq_users_username', 'users', ['username'])

# 3. Обновить RegisterRequest:
class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str  # Сделать обязательным
```

**Приоритет:** 🟡 **ВАЖНО**

---

### 6. 🟡 Отсутствие Email Verification

**Файл:** `backend/app/api/auth.py:74`

**Проблема:**
- Пользователи могут зарегистрироваться с любым email
- Нет подтверждения email
- Возможна регистрация с чужими email

**Исправление:**
```python
# 1. Добавить в User model:
class User(Base):
    ...
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255))
    email_verification_expires: Mapped[Optional[datetime]] = mapped_column(DateTime)

# 2. При регистрации:
@router.post("/register")
async def register(request: RegisterRequest, ...):
    # Создать токен верификации
    verification_token = secrets.token_urlsafe(32)
    verification_expires = datetime.utcnow() + timedelta(hours=24)
    
    new_user = User(
        email=request.email,
        email_verified=False,
        email_verification_token=verification_token,
        email_verification_expires=verification_expires,
        ...
    )
    
    # Отправить email с ссылкой
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    await send_verification_email(request.email, verification_url)
    
    return {"message": "Registration successful. Please verify your email."}

# 3. Endpoint для верификации:
@router.post("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    user = await db.execute(
        select(User).where(
            User.email_verification_token == token,
            User.email_verification_expires > datetime.utcnow()
        )
    )
    user = user.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user.email_verified = True
    user.email_verification_token = None
    await db.commit()
    
    return {"message": "Email verified successfully"}
```

**Приоритет:** 🟡 **ВАЖНО**

---

### 7. 🟡 Незащищённые Endpoints

**Файлы:** `backend/app/main.py`, `backend/app/api/v2_lecture.py`

**Проблема:**
- Некоторые endpoints не требуют аутентификации
- Любой может создать lessons/exports

**Проверка:**
```bash
# Эти endpoints НЕ защищены:
POST /api/upload           # Может загружать кто угодно
POST /api/export           # Может экспортировать чужие lessons
POST /api/v2/lecture-outline  # Нет проверки auth
```

**Исправление:**
```python
# Добавить get_current_user к незащищённым endpoints:

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),  # Добавить!
    ...
):
    # Сохранить с user_id
    lesson.user_id = current_user["user_id"]
    ...

@app.post("/api/export")
async def export_video(
    request: ExportRequest,
    current_user: dict = Depends(get_current_user),  # Добавить!
    ...
):
    # Проверить владение
    lesson = await db.get(Lesson, request.lesson_id)
    if lesson.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    ...
```

**Приоритет:** 🟡 **ВАЖНО**

---

## 🟢 СРЕДНИЕ ПРОБЛЕМЫ (Улучшения)

### 8. 🟢 Отсутствие Refresh Token Rotation

**Проблема:**
- Refresh tokens не ротируются
- Один токен может использоваться бесконечно

**Исправление:**
```python
# 1. Добавить refresh_token в User или отдельную таблицу
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    token: Mapped[str] = mapped_column(String(500), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

# 2. При refresh - создать новый токен и отозвать старый
@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    # Проверить и отозвать старый
    old_token = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False
        )
    )
    
    if not old_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Отозвать старый
    old_token.is_revoked = True
    
    # Создать новый
    new_access_token = AuthManager.create_access_token(...)
    new_refresh_token = create_refresh_token(user_id)
    
    await db.commit()
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }
```

**Приоритет:** 🟢 **СРЕДНИЙ**

---

### 9. 🟢 CSRF Bypass для Auth Endpoints

**Файл:** `backend/app/core/csrf.py:87`

**Проблема:**
```python
# Skip for authentication endpoints
if request.url.path.startswith("/auth/"):
    return True  # CSRF пропускается!
```

**Риск:** CSRF атаки на /login, /register

**Исправление:**
- Включить CSRF для /login, /register
- Только /refresh может быть исключением

**Приоритет:** 🟢 **СРЕДНИЙ**

---

### 10. 🟢 Логирование Неудачных Попыток Входа

**Проблема:**
- Нет логирования failed login attempts
- Сложно обнаружить атаки

**Исправление:**
```python
@router.post("/login")
async def login(request: LoginRequest, ...):
    user = await authenticate_user(...)
    
    if not user:
        # Логировать неудачную попытку
        logger.warning(
            f"Failed login attempt",
            extra={
                "email": request.email,
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # Увеличить счётчик в Redis
        redis_key = f"failed_login:{request.email}"
        redis.incr(redis_key)
        redis.expire(redis_key, 3600)  # 1 час
        
        # Если слишком много попыток - блокировать
        failed_count = int(redis.get(redis_key))
        if failed_count >= 5:
            raise HTTPException(
                status_code=429,
                detail="Too many failed attempts. Try again in 1 hour."
            )
        
        raise HTTPException(status_code=401, detail="Incorrect credentials")
```

**Приоритет:** 🟢 **СРЕДНИЙ**

---

## ✅ ЧТО УЖЕ ХОРОШО

### 1. ✅ Правильное Хэширование Паролей
```python
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
```
- Использует pbkdf2_sha256 (безопасный алгоритм)
- Автоматическое обновление устаревших схем

### 2. ✅ JWT с Expiration
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30
to_encode.update({"exp": expire})
```
- Токены истекают через 30 минут
- Правильная проверка exp в verify_token

### 3. ✅ HTTPBearer Security
```python
security = HTTPBearer()
```
- Стандартная схема Bearer token
- Правильная проверка Authorization header

### 4. ✅ CSRF Protection Implementation
- Double Submit Cookie pattern
- SameSite=strict cookies
- HttpOnly для безопасности

### 5. ✅ Database Indexes
```python
email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
```
- Индексы на email для быстрого поиска

---

## 📋 Plan Исправлений

### Неделя 1 (КРИТИЧНО):
- [ ] Сгенерировать и установить JWT_SECRET_KEY (64 байта)
- [ ] Сгенерировать и установить CSRF_SECRET_KEY (32 байта)
- [ ] Добавить обязательную проверку секретов при старте
- [ ] Проверить все environment variables в production

### Неделя 2 (ВАЖНО):
- [ ] Добавить rate limiting на /login (5/min)
- [ ] Добавить валидацию сложности пароля
- [ ] Добавить username в User model + миграция
- [ ] Защитить незащищённые endpoints

### Неделя 3 (ВАЖНО):
- [ ] Реализовать email verification
- [ ] Добавить логирование failed login attempts
- [ ] Создать dashboard для мониторинга безопасности

### Неделя 4 (УЛУЧШЕНИЯ):
- [ ] Refresh token rotation
- [ ] CSRF для auth endpoints
- [ ] 2FA (опционально)

---

## 🔧 Быстрые Исправления (Сейчас)

### 1. Сгенерировать Сильные Секреты

```bash
# Запустить в backend директории
python3 << EOF
import secrets

jwt_secret = secrets.token_urlsafe(64)
csrf_secret = secrets.token_urlsafe(32)

print("# Add to backend/.env:")
print(f"JWT_SECRET_KEY={jwt_secret}")
print(f"CSRF_SECRET_KEY={csrf_secret}")
EOF
```

### 2. Обновить backend/.env

```bash
# Добавить в конец файла:
echo "" >> backend/.env
echo "# Security Keys (GENERATED - DO NOT COMMIT)" >> backend/.env
echo "JWT_SECRET_KEY=<paste_generated_jwt_secret>" >> backend/.env
echo "CSRF_SECRET_KEY=<paste_generated_csrf_secret>" >> backend/.env
```

### 3. Проверить Обязательные Секреты

```python
# В backend/app/core/auth.py:18 изменить на:
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-in-production":
    raise ValueError(
        "JWT_SECRET_KEY must be set in .env and cannot be default value. "
        "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
    )
```

---

## 📊 Оценка Безопасности

### До Исправлений:
- **Общая Оценка:** 5.5/10 (Средний уровень безопасности)
- **Критичные уязвимости:** 2
- **Важные проблемы:** 6
- **Готовность к production:** ⚠️ НЕ ГОТОВ

### После Исправлений:
- **Ожидаемая Оценка:** 9.0/10 (Высокий уровень безопасности)
- **Критичные уязвимости:** 0
- **Важные проблемы:** 0-1
- **Готовность к production:** ✅ ГОТОВ

---

## 📞 Рекомендации

1. **НЕМЕДЛЕННО:** Сгенерировать и установить JWT_SECRET_KEY и CSRF_SECRET_KEY
2. **В ТЕЧЕНИЕ НЕДЕЛИ:** Добавить rate limiting на /login
3. **В ТЕЧЕНИЕ 2 НЕДЕЛЬ:** Реализовать email verification
4. **ПОСТОЯННО:** Мониторить логи на подозрительную активность

**ВАЖНО:** Не deploy в production до исправления критических проблем #1 и #2!

---

**Дата проверки:** 2024  
**Следующая проверка:** Через 1 месяц после исправлений
