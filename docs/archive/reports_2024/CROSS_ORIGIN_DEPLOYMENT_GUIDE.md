# Cross-Origin Deployment Guide (Netlify + Railway)

**Дата:** 2025-01-08  
**Проблема:** HttpOnly cookies не работают между разными доменами

---

## 🚨 Проблема

### Текущая ситуация:
```
Frontend: localhost:3000
Backend:  localhost:8000
Cookie:   Same-Origin ✅ Работает
```

### После деплоя:
```
Frontend: your-app.netlify.app
Backend:  your-app.railway.app
Cookie:   Cross-Origin ❌ НЕ РАБОТАЕТ!
```

---

## ⚠️ Почему не работает?

### 1. **Same-Site Policy**
Браузеры блокируют cookies от разных доменов:
```javascript
// Backend на railway.app устанавливает cookie
Set-Cookie: access_token=...; HttpOnly; SameSite=lax

// Frontend на netlify.app НЕ получит этот cookie!
// Браузер заблокирует из-за different origin
```

### 2. **Browser Security**
- Chrome/Firefox: Блокируют по умолчанию
- Safari: Особенно строгий (Intelligent Tracking Prevention)
- Mobile browsers: Ещё строже

### 3. **SameSite Attribute**
```
SameSite=strict → Только same domain
SameSite=lax   → Работает для GET, НЕ работает для POST (частично)
SameSite=none  → Требует Secure=true (HTTPS)
```

---

## ✅ Решения (3 варианта)

### **Вариант 1: Custom Domain + Поддомены** ⭐ РЕКОМЕНДУЕТСЯ

Используйте один домен с поддоменами:

```
Frontend: app.yourdomain.com    (Netlify)
Backend:  api.yourdomain.com    (Railway)
Cookie:   domain=.yourdomain.com ✅ Работает!
```

#### Преимущества:
- ✅ HttpOnly cookies работают
- ✅ Максимальная безопасность
- ✅ Нет проблем с CORS
- ✅ Работает во всех браузерах

#### Настройка:

**1. Купите домен (например на Namecheap, GoDaddy)**

**2. Настройте DNS:**
```
app.yourdomain.com → CNAME → your-app.netlify.app
api.yourdomain.com → CNAME → your-app.railway.app
```

**3. Настройте Netlify:**
```
Netlify Dashboard → Domain settings → Add custom domain
→ app.yourdomain.com
→ Enable HTTPS (automatic)
```

**4. Настройте Railway:**
```
Railway Dashboard → Settings → Domains
→ Add custom domain: api.yourdomain.com
→ Enable HTTPS (automatic)
```

**5. Обновите Backend (`backend/app/api/auth.py`):**

```python
# Установка cookie с правильным domain
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=True,  # ✅ Обязательно для production
    samesite="none",  # ✅ Позволяет cross-subdomain
    max_age=token_max_age,
    domain=".yourdomain.com",  # ✅ Работает для всех поддоменов
    path="/"
)
```

**6. Обновите CORS (`docker.env` или Railway env vars):**
```bash
CORS_ORIGINS=https://app.yourdomain.com
```

**7. Обновите Frontend (`.env` для Netlify):**
```bash
VITE_API_BASE=https://api.yourdomain.com
```

#### Стоимость:
- Домен: ~$10-15/год
- Netlify: Free
- Railway: $5+/месяц

---

### **Вариант 2: Proxy через Netlify** ⭐ АЛЬТЕРНАТИВА

Проксируйте API запросы через Netlify, чтобы избежать cross-origin.

```
Frontend: app.netlify.app
API:      app.netlify.app/api → proxy → railway.app
Cookie:   Same-Origin ✅ Работает!
```

#### Настройка:

**1. Создайте `netlify.toml`:**
```toml
[[redirects]]
  from = "/api/*"
  to = "https://your-app.railway.app/api/:splat"
  status = 200
  force = true
  headers = {X-From = "Netlify"}
  
[[headers]]
  for = "/api/*"
  [headers.values]
    Access-Control-Allow-Credentials = "true"
```

**2. Frontend видит API как same-origin:**
```typescript
// src/lib/api.ts
const API_BASE = import.meta.env.VITE_API_BASE || '';  // ✅ Пустая строка = same origin
```

**3. Backend cookies работают:**
```python
# Cookie установлен от app.netlify.app (same origin)
response.set_cookie(
    key="access_token",
    httponly=True,
    secure=True,
    samesite="lax",  # ✅ Работает для same-origin
    max_age=token_max_age,
    path="/"
)
```

#### Преимущества:
- ✅ Не нужен custom domain
- ✅ HttpOnly cookies работают
- ✅ Проще настроить

#### Недостатки:
- ⚠️ Дополнительная задержка (proxy hop)
- ⚠️ Netlify bandwidth limits

---

### **Вариант 3: Токен в LocalStorage** ⚠️ МЕНЬШЕ БЕЗОПАСНОСТИ

Отказаться от HttpOnly cookies, хранить токен в localStorage.

```javascript
// После логина
const response = await api.login(credentials);
localStorage.setItem('token', response.access_token);

// При запросах
headers: {
  'Authorization': `Bearer ${localStorage.getItem('token')}`
}
```

#### Преимущества:
- ✅ Работает на любых доменах
- ✅ Простая реализация

#### Недостатки:
- ❌ Уязвимо к XSS атакам
- ❌ JavaScript может украсть токен
- ❌ Меньше безопасности

#### Когда использовать:
- Если нет custom domain
- Если не хотите proxy
- Если понимаете риски XSS

#### Изменения:

**Backend (`backend/app/api/auth.py`):**
```python
@router.post("/login")
async def login(...):
    # ...
    access_token = create_token(...)
    
    # ❌ НЕ устанавливаем cookie
    # response.set_cookie(...)
    
    # ✅ Возвращаем токен в JSON
    return {
        "message": "Login successful",
        "access_token": access_token,  # ✅ Frontend сохранит в localStorage
        "user": {...}
    }
```

**Frontend (`src/contexts/AuthContext.tsx`):**
```typescript
const login = async (credentials) => {
  const response = await apiClient.login(credentials);
  
  // ✅ Сохраняем токен в localStorage
  localStorage.setItem('access_token', response.access_token);
  localStorage.setItem('user', JSON.stringify(response.user));
  
  setUser(response.user);
};

const initializeAuth = async () => {
  const token = localStorage.getItem('access_token');
  
  if (token) {
    try {
      // Проверяем токен
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch {
      // Токен недействителен
      localStorage.clear();
    }
  }
};
```

**API Client (`src/lib/api.ts`):**
```typescript
async getCurrentUser(): Promise<UserResponse> {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`${API_BASE}/api/auth/me`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`  // ✅ Отправляем токен в header
    }
  });
  
  return response.json();
}
```

---

## 📊 Сравнение вариантов

| Критерий | Custom Domain | Netlify Proxy | LocalStorage |
|----------|---------------|---------------|--------------|
| **Безопасность** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Сложность** | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Стоимость** | $10-15/год | Free | Free |
| **Скорость** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **XSS защита** | ✅ Да | ✅ Да | ❌ Нет |
| **CSRF защита** | ✅ Да | ✅ Да | ✅ Да |
| **Браузеры** | ✅ Все | ✅ Все | ✅ Все |

---

## 🎯 Рекомендация

### **Для Production: Вариант 1 (Custom Domain)**

**Почему:**
- Максимальная безопасность
- Профессиональный вид
- Работает везде
- Стоит копейки ($10/год)

**Setup:**
1. Купите домен на Namecheap (~$10/год)
2. Настройте DNS (5 минут)
3. Добавьте домен в Netlify и Railway (5 минут)
4. Обновите cookie domain и CORS (5 минут)
5. ✅ Готово!

### **Для MVP/тестирования: Вариант 2 (Proxy)**

**Почему:**
- Не нужен домен
- Быстро настроить
- Хорошая безопасность

**Setup:**
1. Создайте netlify.toml (2 минуты)
2. Deploy на Netlify (1 минута)
3. ✅ Готово!

---

## 🔧 Текущие настройки проекта

### Что нужно изменить для деплоя:

**1. Backend cookie settings (`backend/app/api/auth.py`):**

```python
# ✅ ДЛЯ PRODUCTION с custom domain
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=True,  # ✅ Обязательно HTTPS
    samesite="none",  # ✅ Для cross-subdomain
    max_age=token_max_age,
    domain=os.getenv("COOKIE_DOMAIN", None),  # .yourdomain.com
    path="/"
)
```

**2. CORS settings (`backend/app/main.py`):**

```python
# Читаем из environment variables
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # ✅ Точный домен Netlify
    allow_credentials=True,  # ✅ Обязательно для cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**3. Environment variables:**

**Railway:**
```bash
CORS_ORIGINS=https://app.yourdomain.com
COOKIE_DOMAIN=.yourdomain.com
JWT_SECRET_KEY=<your-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

**Netlify:**
```bash
VITE_API_BASE=https://api.yourdomain.com
```

---

## 🧪 Тестирование после деплоя

### Checklist:

```bash
# 1. Проверить CORS
curl -H "Origin: https://app.yourdomain.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS https://api.yourdomain.com/api/auth/login

# Ожидаемый результат:
# Access-Control-Allow-Origin: https://app.yourdomain.com
# Access-Control-Allow-Credentials: true

# 2. Проверить cookie
curl -X POST https://api.yourdomain.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"test"}' \
     -v 2>&1 | grep Set-Cookie

# Ожидаемый результат:
# Set-Cookie: access_token=...; Domain=.yourdomain.com; Secure; HttpOnly; SameSite=None

# 3. Проверить в браузере
# - Откройте https://app.yourdomain.com
# - Залогиньтесь
# - F12 → Application → Cookies
# - Должен быть cookie access_token от .yourdomain.com
# - Перезагрузите страницу - должны остаться залогинены
```

---

## 📝 Пошаговая инструкция (Custom Domain)

### День 1: Купить домен

1. Зайдите на Namecheap.com
2. Найдите доступный домен (~$10/год)
3. Купите домен
4. ✅ Готово

### День 2: Настроить DNS

1. **Namecheap → Domain List → Manage**
2. **Advanced DNS → Add New Record:**
   ```
   Type: CNAME
   Host: app
   Value: your-app.netlify.app
   TTL: Automatic
   
   Type: CNAME
   Host: api  
   Value: your-app.railway.app
   TTL: Automatic
   ```
3. ✅ Подождите 5-30 минут (DNS propagation)

### День 3: Настроить Netlify

1. **Netlify Dashboard → Domain settings**
2. **Add custom domain:** app.yourdomain.com
3. **Enable HTTPS:** Автоматически
4. ✅ Готово

### День 4: Настроить Railway

1. **Railway Dashboard → Settings → Domains**
2. **Custom Domain:** api.yourdomain.com
3. **Verify:** Следуйте инструкциям
4. ✅ Готово

### День 5: Обновить код

1. **Обновите backend/app/api/auth.py** (cookie domain)
2. **Обновите docker.env** (CORS_ORIGINS, COOKIE_DOMAIN)
3. **Deploy на Railway**
4. **Обновите .env для Netlify** (VITE_API_BASE)
5. **Deploy на Netlify**
6. ✅ Готово!

### День 6: Тестирование

1. Откройте https://app.yourdomain.com
2. Залогиньтесь
3. Проверьте cookie в DevTools
4. Перезагрузите страницу
5. ✅ Должны остаться залогинены!

---

## 🆘 Troubleshooting

### Проблема: Cookie не устанавливается

**Причины:**
- Secure=False в production
- SameSite=strict для cross-origin
- CORS не настроен

**Решение:**
```python
# ✅ Убедитесь:
secure=True  # HTTPS обязательно
samesite="none"  # Для cross-subdomain
domain=".yourdomain.com"  # С точкой в начале
```

### Проблема: CORS ошибка

**Причины:**
- allow_credentials=False
- Wildcard в allow_origins с credentials
- Неправильный домен

**Решение:**
```python
allow_origins=["https://app.yourdomain.com"],  # ✅ Точный домен
allow_credentials=True,  # ✅ Обязательно
```

### Проблема: Safari блокирует

**Причины:**
- Intelligent Tracking Prevention (ITP)
- Third-party cookies блокируются

**Решение:**
- ✅ Используйте поддомены (app. и api.)
- ✅ SameSite=none
- ✅ Или используйте proxy

---

## ✅ Checklist для Production

- [ ] Купили custom domain
- [ ] Настроили DNS (app. и api.)
- [ ] Добавили домен в Netlify
- [ ] Добавили домен в Railway
- [ ] Обновили cookie domain в коде
- [ ] Обновили CORS_ORIGINS
- [ ] Установили secure=True
- [ ] Установили samesite="none"
- [ ] Протестировали login
- [ ] Протестировали reload страницы
- [ ] Протестировали в разных браузерах
- [ ] Проверили cookie в DevTools
- [ ] Проверили HTTPS работает
- [ ] Проверили Analytics Dashboard

---

## 📚 Дополнительные ресурсы

- [MDN: HTTP Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies)
- [SameSite Cookie Explained](https://web.dev/samesite-cookies-explained/)
- [Netlify Redirects and Rewrites](https://docs.netlify.com/routing/redirects/)
- [Railway Custom Domains](https://docs.railway.app/deploy/exposing-your-app#custom-domains)

---

**Вывод:** Для production с Netlify + Railway **обязательно нужен custom domain** или **proxy**, иначе HttpOnly cookies не будут работать между разными доменами.

**Рекомендация:** Потратьте $10 на домен - это того стоит для безопасности и профессионального вида! 🚀
