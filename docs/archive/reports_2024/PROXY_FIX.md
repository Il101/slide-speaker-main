# 🔧 Исправление Proxy Ошибки

**Проблема:** Frontend не может подключиться к Backend API  
**Ошибка:** `Failed to load resource` / `ECONNREFUSED`  
**Причина:** Docker networking issue

---

## ❌ Проблема

### Что Было:
```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // ❌ НЕ РАБОТАЕТ в Docker!
      changeOrigin: true,
    }
  }
}
```

**Почему не работает:**
- Frontend контейнер пытается обратиться к `localhost:8000`
- Но `localhost` внутри контейнера = сам контейнер
- Backend находится в другом контейнере
- Нужно использовать имя сервиса из docker-compose

---

## ✅ Решение

### Что Стало:
```typescript
// vite.config.ts
server: {
  host: '0.0.0.0',
  port: 5173,
  proxy: {
    '/api': {
      target: process.env.VITE_API_URL || 'http://backend:8000',  // ✅ Имя сервиса
      changeOrigin: true,
      secure: false,
    }
  }
}
```

**Изменения:**
1. ✅ `target: 'http://backend:8000'` - используем имя сервиса из docker-compose.yml
2. ✅ `host: '0.0.0.0'` - слушаем все интерфейсы
3. ✅ `port: 5173` - явно указываем порт
4. ✅ `secure: false` - отключаем SSL проверку
5. ✅ `process.env.VITE_API_URL` - можно переопределить через env var

---

## 🔍 Как Это Работает

### Docker Networking:

```yaml
# docker-compose.yml
services:
  backend:      # ← Это имя сервиса
    ports:
      - "8000:8000"
  
  frontend:     # ← Это имя сервиса
    ports:
      - "3000:5173"
    depends_on:
      - backend
```

**В Docker Compose:**
- Каждый сервис доступен по своему имени
- `backend` = `backend:8000` внутри сети
- `frontend` = `frontend:5173` внутри сети
- `localhost` = только текущий контейнер

**Снаружи (с хоста):**
- `localhost:8000` → backend
- `localhost:3000` → frontend

**Внутри (между контейнерами):**
- `backend:8000` → backend
- `frontend:5173` → frontend

---

## 🧪 Проверка

### 1. Проверить что frontend запущен:
```bash
curl http://localhost:3000
# Должен вернуть HTML
```

### 2. Проверить что backend доступен:
```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"slide-speaker-api"}
```

### 3. Проверить proxy:
```bash
# Открыть в браузере:
http://localhost:3000

# Открыть DevTools → Network
# Запросы к /api/* должны проксироваться на backend
```

### 4. Проверить логи:
```bash
docker logs slide-speaker-main-frontend-1 2>&1 | grep -i "proxy\|error"
```

---

## 📝 Альтернативные Решения

### Вариант 1: Environment Variable (рекомендуется)
```yaml
# docker-compose.yml
frontend:
  environment:
    - VITE_API_URL=http://backend:8000
```

### Вариант 2: Host Network Mode
```yaml
# docker-compose.yml
frontend:
  network_mode: "host"
  # Не рекомендуется - нарушает изоляцию
```

### Вариант 3: Direct API Calls (без proxy)
```typescript
// src/lib/api.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

fetch(`${API_BASE}/api/subscription/plans`)
```

---

## ✅ Статус После Исправления

```
╔═══════════════════════════════════════════════════════╗
║           PROXY FIX STATUS                            ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  Configuration:       ✅ Fixed                       ║
║  Docker Networking:   ✅ Correct                     ║
║  Frontend → Backend:  ✅ Should work now             ║
║                                                       ║
║  Action Required:     Test in browser                ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

---

## 🔄 Если Всё Ещё Не Работает

### Шаг 1: Пересобрать
```bash
docker-compose down
docker-compose up -d --build frontend
```

### Шаг 2: Проверить сеть
```bash
docker network inspect slide-speaker-main_default
# Должны быть оба контейнера (backend и frontend)
```

### Шаг 3: Проверить из контейнера
```bash
docker exec slide-speaker-main-frontend-1 wget -O- http://backend:8000/health
# Должен вернуть {"status":"healthy"}
```

### Шаг 4: Проверить переменные окружения
```bash
docker exec slide-speaker-main-frontend-1 env | grep VITE
```

---

**Дата:** 2025-01-15  
**Статус:** ✅ Исправлено  
**Требуется:** Перезапуск frontend (выполнено)
