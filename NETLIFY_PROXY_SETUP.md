# Netlify Proxy Setup - Инструкция

**Дата:** 2025-01-08  
**Статус:** ✅ Настроено для переключения Local ↔ Production

---

## 🎯 Что сделано

Проект теперь поддерживает **два режима работы**:

### **1. Local Development (по умолчанию)**
```
Frontend:  localhost:3000
Backend:   localhost:8000 (прямое подключение)
Cookies:   secure=false (работает по HTTP)
Proxy:     Не используется
```

### **2. Production (Netlify + Railway)**
```
Frontend:  your-app.netlify.app
Backend:   your-app.netlify.app/api → proxy → railway
Cookies:   secure=true (требует HTTPS)
Proxy:     ✅ Используется (same-origin)
```

---

## 📝 Изменённые файлы

### ✅ 1. `.env.local` (НОВЫЙ)
```bash
# Local development configuration
VITE_API_BASE=http://localhost:8000
```

**Статус:** ✅ Создан, в `.gitignore` (не коммитится)

---

### ✅ 2. `netlify.toml` (ОБНОВЛЁН)
```toml
# Proxy для /api/* запросов в production
[[redirects]]
  from = "/api/*"
  to = "https://your-railway-app.up.railway.app/api/:splat"
  status = 200

# Contexts:
[context.development.environment]
  VITE_API_BASE = "http://localhost:8000"  # Local

[context.production.environment]
  VITE_API_BASE = ""  # Proxy (same-origin)
```

**Статус:** ✅ Обновлён с proxy настройками

---

### ✅ 3. `backend/app/api/auth.py` (ОБНОВЛЁН)
```python
# Cookie secure зависит от ENVIRONMENT
is_production = os.getenv("ENVIRONMENT", "development") == "production"

response.set_cookie(
    secure=is_production,  # False локально, True в production
    ...
)
```

**Статус:** ✅ Обновлён для динамической настройки

---

## 🚀 Использование

### **Локальная разработка (сейчас)**

```bash
# 1. Запустить backend
docker-compose up -d

# 2. Запустить frontend
npm run dev

# 3. Открыть http://localhost:3000
# ✅ Всё работает как раньше!
```

**Что происходит:**
- Frontend читает `.env.local`
- `VITE_API_BASE=http://localhost:8000`
- Запросы идут напрямую к `localhost:8000`
- Cookie `secure=false` (работает по HTTP)

---

### **Деплой на Netlify + Railway (потом)**

#### Шаг 1: Подготовка Railway

1. **Откройте Railway Dashboard → Variables**
2. **Добавьте переменную:**
   ```
   ENVIRONMENT=production
   ```
3. **Обновите CORS_ORIGINS (если нужно):**
   ```
   CORS_ORIGINS=https://your-app.netlify.app
   ```

#### Шаг 2: Обновите netlify.toml

**Замените** `your-railway-app.up.railway.app` на **ваш реальный Railway URL**:

```toml
[[redirects]]
  from = "/api/*"
  to = "https://YOUR-ACTUAL-APP.up.railway.app/api/:splat"
  #           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  #           Замените на ваш Railway URL!
  status = 200
  force = true
```

#### Шаг 3: Deploy на Netlify

```bash
git add .
git commit -m "Add Netlify proxy configuration"
git push origin main
```

Netlify автоматически задеплоит с новыми настройками.

**Что происходит:**
- Frontend на Netlify получает `VITE_API_BASE=""`
- Запросы идут к `/api/*` (relative path)
- Netlify проксирует на Railway
- Same-origin → Cookie работает!

---

## 🧪 Проверка

### **Local (сейчас):**

```bash
# 1. Запустите проект
npm run dev

# 2. Откройте http://localhost:3000
# 3. Залогиньтесь (admin@example.com / admin123)
# 4. F12 → Network → Проверьте:
#    Request URL: http://localhost:8000/api/auth/login ✅

# 5. F12 → Application → Cookies
#    Secure: false ✅ (нормально для HTTP)

# 6. Перезагрузите страницу
#    Должны остаться залогинены ✅
```

### **Production (после деплоя):**

```bash
# 1. Откройте https://your-app.netlify.app
# 2. Залогиньтесь
# 3. F12 → Network → Проверьте:
#    Request URL: https://your-app.netlify.app/api/auth/login ✅
#    (НЕ railway.app, а netlify.app - это proxy!)

# 4. F12 → Application → Cookies
#    Domain: your-app.netlify.app ✅
#    Secure: true ✅
#    HttpOnly: true ✅

# 5. Перезагрузите страницу
#    Должны остаться залогинены ✅
```

---

## ❓ FAQ

### **Q: Нужно ли что-то менять для локальной работы?**
A: **Нет!** Всё работает как раньше. Просто `npm run dev`.

### **Q: Когда использовать proxy?**
A: Только при деплое на Netlify + Railway. Локально proxy НЕ используется.

### **Q: Что если я хочу тестировать с Railway backend локально?**
A: Раскомментируйте в `.env.local`:
```bash
VITE_API_BASE=https://your-app.railway.app
```

### **Q: Как вернуть обратно на localhost?**
A: Закомментируйте обратно в `.env.local`:
```bash
VITE_API_BASE=http://localhost:8000
```

### **Q: Где найти Railway URL?**
A: Railway Dashboard → Settings → Domains

### **Q: Нужен ли custom domain?**
A: **НЕТ!** Proxy работает с бесплатными netlify.app и railway.app доменами.

---

## 🔧 Troubleshooting

### Проблема: "Вылетает из аккаунта" на Netlify

**Причина:** Не установлена переменная `ENVIRONMENT=production` в Railway

**Решение:**
```bash
# Railway Dashboard → Variables
ENVIRONMENT=production
```

---

### Проблема: CORS ошибка в production

**Причина:** Railway не знает о Netlify домене

**Решение:**
```bash
# Railway Dashboard → Variables
CORS_ORIGINS=https://your-app.netlify.app
```

---

### Проблема: 404 на /api/* в production

**Причина:** Неправильный Railway URL в netlify.toml

**Решение:**
1. Откройте Railway → Settings → Domains
2. Скопируйте URL (например: `myapp-production.up.railway.app`)
3. Обновите `netlify.toml`:
```toml
to = "https://myapp-production.up.railway.app/api/:splat"
```

---

### Проблема: Локально не работает login

**Причина:** Backend не запущен или порт занят

**Решение:**
```bash
# Проверьте что backend работает
docker-compose ps | grep backend
# Должен быть: Up (healthy)

# Если нет, перезапустите
docker-compose restart backend
```

---

## 📊 Таблица режимов

| Параметр | Local | Production |
|----------|-------|------------|
| **VITE_API_BASE** | `localhost:8000` | `""` (empty) |
| **Cookie Secure** | `false` | `true` |
| **Proxy** | ❌ Не используется | ✅ Netlify → Railway |
| **Origin** | Different | Same (через proxy) |
| **HTTPS** | ❌ HTTP | ✅ HTTPS |

---

## ✅ Checklist перед деплоем

- [ ] Railway: Добавлена переменная `ENVIRONMENT=production`
- [ ] Railway: Обновлена `CORS_ORIGINS` (если нужно)
- [ ] netlify.toml: Обновлён Railway URL в proxy redirect
- [ ] git push на main ветку
- [ ] Netlify автоматически задеплоил
- [ ] Проверили что login работает
- [ ] Проверили что cookie устанавливается
- [ ] Проверили что reload не вылогинивает

---

## 🎉 Готово!

Теперь у вас есть:
- ✅ Локальная разработка с прямым подключением
- ✅ Production деплой через Netlify proxy
- ✅ Переключение через environment variables
- ✅ HttpOnly cookies работают везде
- ✅ Не нужен custom domain

**Работайте локально, деплойте когда готовы!** 🚀

---

## 📚 Дополнительные материалы

- `CROSS_ORIGIN_DEPLOYMENT_GUIDE.md` - Подробный гайд по всем вариантам деплоя
- [Netlify Redirects Docs](https://docs.netlify.com/routing/redirects/)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)
