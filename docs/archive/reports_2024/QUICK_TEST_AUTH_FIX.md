# Быстрый тест исправления 403 Forbidden

## ✅ Что было исправлено

1. **Загрузка файлов** - добавлен Authorization header для cross-origin запросов
2. **Проверка владения** - улучшена безопасность доступа к лекциям
3. **Backend перезапущен** - изменения применены

---

## 🧪 Как протестировать

### Локальное тестирование

1. **Запустите frontend:**
```bash
npm run dev
```

2. **Откройте браузер:**
```
http://localhost:3000
```

3. **Войдите в систему:**
- Email: admin@example.com
- Password: admin123

4. **Загрузите презентацию:**
- Нажмите "Выбрать файл" или перетащите PPTX/PDF
- **Ожидаемый результат:** ✅ Загрузка проходит успешно без ошибки 403

5. **Проверьте статус обработки:**
- Должен появиться прогресс-бар
- **Ожидаемый результат:** ✅ Статус обновляется без ошибок

6. **Проверьте плеер:**
- После обработки откроется плеер
- **Ожидаемый результат:** ✅ Видео воспроизводится

---

## 🔍 Проверка в DevTools

### 1. Откройте DevTools (F12)

### 2. Вкладка Network

**При загрузке файла:**
```
POST http://localhost:8000/upload
Status: 200 OK (не 403!)
Headers:
  - Cookie: access_token=...
  - X-CSRF-Token: ...
```

**При проверке статуса:**
```
GET http://localhost:8000/lessons/{lesson_id}/status
Status: 200 OK (не 403!)
Headers:
  - Cookie: access_token=...
```

**При загрузке манифеста:**
```
GET http://localhost:8000/lessons/{lesson_id}/manifest
Status: 200 OK (не 403!)
Headers:
  - Cookie: access_token=...
```

### 3. Вкладка Console

**Не должно быть ошибок:**
- ❌ "403 Forbidden"
- ❌ "Not authenticated"
- ✅ Только обычные логи

---

## 🚀 Production (Netlify + Railway)

### Перед деплоем убедитесь:

1. **Railway Environment Variables:**
```bash
ENVIRONMENT=production
CORS_ORIGINS=https://your-app.netlify.app
```

2. **netlify.toml правильно настроен:**
```toml
[[redirects]]
  from = "/api/*"
  to = "https://your-railway-app.up.railway.app/api/:splat"
  status = 200
  force = true
```

3. **Деплой:**
```bash
git push origin production-deploy
```

### После деплоя проверьте:

1. **Login/Logout** - работает
2. **Upload** - файлы загружаются без 403
3. **Player** - видео воспроизводится
4. **F12 → Network** - все запросы возвращают 200/201

---

## 🐛 Troubleshooting

### Проблема: Все еще получаю 403

**Решение 1: Очистите кеш**
```
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

**Решение 2: Проверьте авторизацию**
```
1. Разлогиньтесь
2. Очистите cookies (F12 → Application → Cookies → Clear)
3. Залогиньтесь заново
```

**Решение 3: Перезапустите backend**
```bash
docker-compose restart backend
```

### Проблема: Cross-origin не работает

**Проверьте в Railway:**
```bash
# Должно быть установлено
ENVIRONMENT=production
```

**Проверьте в браузере (F12 → Network):**
```
Request URL: https://your-app.netlify.app/api/upload
(НЕ railway.app - это через proxy!)
```

---

## 📋 Что изменилось в коде

### Frontend (src/lib/api.ts)
```typescript
// Метод uploadFile теперь добавляет Authorization header
if (this.isCrossOrigin()) {
  const authHeaders = this.getAuthHeaders();
  Object.assign(headers, authHeaders);
}
```

### Backend (backend/app/main.py)
```python
# Эндпоинт /lessons/{lesson_id}/manifest теперь правильно проверяет владение
if lesson_owner:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if lesson_owner != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
```

---

## ✅ Checklist

- [x] Backend перезапущен
- [x] Код собирается без ошибок (npm run build)
- [x] Backend компилируется без ошибок
- [x] Изменения закоммичены
- [ ] Протестирована загрузка файла локально
- [ ] Протестирован плеер локально
- [ ] Протестирован деплой в production (опционально)

---

## 📚 Дополнительно

- `AUTHENTICATION_FIX_403.md` - Подробное описание исправлений
- `NETLIFY_PROXY_SETUP.md` - Настройка proxy
- `CROSS_ORIGIN_DEPLOYMENT_GUIDE.md` - Гайд по деплою
