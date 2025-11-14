# 🔧 Исправление 401 Unauthorized

**Проблема:** Frontend получает 401 ошибку при запросе `/api/subscription/info`  
**Причина:** Несоответствие ключей токена в localStorage  
**Дата:** 2025-01-15

---

## ❌ Проблема

### Что Было:

**api.ts (правильно):**
```typescript
localStorage.getItem('slide-speaker-auth-token')  // ✅
```

**SubscriptionManager.tsx (неправильно):**
```typescript
localStorage.getItem('token')  // ❌ Неправильный ключ!
```

**Результат:**
- Пользователь залогинен
- Токен хранится как `'slide-speaker-auth-token'`
- Компонент ищет `'token'`
- Токен не найден → 401 Unauthorized

---

## ✅ Решение

### 1. Создан Публичный Метод

**api.ts:**
```typescript
class ApiClient {
  // Публичный метод для получения токена
  getAuthToken(): string | null {
    return localStorage.getItem('slide-speaker-auth-token');
  }

  // Публичный метод для получения заголовков
  getAuthHeaders(): HeadersInit {
    const token = this.getAuthToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }
}
```

### 2. Обновлены Компоненты

**SubscriptionManager.tsx:**
```typescript
// Было
headers: {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,  // ❌
}

// Стало
import { apiClient } from '@/lib/api';

headers: {
  ...apiClient.getAuthHeaders(),  // ✅
}
```

**ContentEditor.tsx:**
```typescript
// 3 места обновлено
headers: {
  ...apiClient.getAuthHeaders(),  // ✅
}
```

**EnhancedFileUploader.tsx:**
```typescript
// Было
token={localStorage.getItem('token') || undefined}  // ❌

// Стало
token={apiClient.getAuthToken() || undefined}  // ✅
```

---

## 📝 Список Изменений

### Обновленные Файлы:

1. ✅ `src/lib/api.ts`
   - Сделал `getAuthToken()` публичным
   - Добавил `getAuthHeaders()` метод

2. ✅ `src/components/SubscriptionManager.tsx`
   - Добавлен импорт `apiClient`
   - Заменен `localStorage.getItem('token')` на `apiClient.getAuthHeaders()`

3. ✅ `src/components/ContentEditor.tsx`
   - Добавлен импорт `apiClient`
   - 3 места с токеном обновлены

4. ✅ `src/components/EnhancedFileUploader.tsx`
   - Заменен `localStorage.getItem('token')` на `apiClient.getAuthToken()`

---

## 🧪 Как Проверить

### 1. Проверить Токен в DevTools:
```javascript
// Открыть Console в браузере
localStorage.getItem('slide-speaker-auth-token')
// Должен вернуть токен (если залогинен)
```

### 2. Проверить Запросы:
```javascript
// В Network tab смотреть запрос /api/subscription/info
// Должен быть заголовок:
// Authorization: Bearer eyJ...токен...
```

### 3. Проверить 401 Ошибки:
```bash
# Открыть страницу подписки
http://localhost:3000/subscription

# В Console не должно быть:
# ❌ 401 Unauthorized
# ✅ Должны загрузиться данные
```

---

## 🔍 Почему Это Случилось?

### Root Cause:

Компоненты создавались в разное время:
1. `api.ts` создан первым с ключом `'slide-speaker-auth-token'`
2. Новые компоненты создавались позже и использовали просто `'token'`
3. Не было единого централизованного метода для получения токена

### Правильный Подход:

✅ **Всегда использовать:**
```typescript
import { apiClient } from '@/lib/api';

// Для headers
headers: { ...apiClient.getAuthHeaders() }

// Для прямого доступа к токену
const token = apiClient.getAuthToken();
```

❌ **Никогда не использовать напрямую:**
```typescript
localStorage.getItem('token')  // ❌ Неправильный ключ
localStorage.getItem('slide-speaker-auth-token')  // ❌ Hardcoded
```

---

## ✅ Статус После Исправления

```
╔═══════════════════════════════════════════════════════╗
║           AUTH TOKEN FIX STATUS                       ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  api.ts:                  ✅ Public methods added    ║
║  SubscriptionManager:     ✅ Fixed                   ║
║  ContentEditor:           ✅ Fixed (3 places)        ║
║  EnhancedFileUploader:    ✅ Fixed                   ║
║                                                       ║
║  401 Error:               ✅ Should be fixed         ║
║                                                       ║
║  Action Required:         Test in browser            ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

---

## 🚀 Следующие Шаги

### После Применения Исправлений:

1. **Перезагрузить страницу** в браузере (Ctrl+R)
2. **Залогиниться** заново (если нужно)
3. **Открыть** `/subscription` страницу
4. **Проверить** что данные загружаются
5. **Проверить Console** - не должно быть 401 ошибок

### Если Всё Ещё Не Работает:

1. **Очистить localStorage:**
   ```javascript
   localStorage.clear()
   ```

2. **Залогиниться заново**

3. **Проверить что токен сохранился:**
   ```javascript
   localStorage.getItem('slide-speaker-auth-token')
   ```

4. **Проверить backend logs:**
   ```bash
   docker logs slide-speaker-main-backend-1 | grep 401
   ```

---

## 📚 Best Practices

### Для Будущих Компонентов:

**✅ DO:**
```typescript
import { apiClient } from '@/lib/api';

// В fetch запросах
fetch(url, {
  headers: { ...apiClient.getAuthHeaders() }
})

// Или использовать apiClient методы напрямую
await apiClient.getLesson(id);
```

**❌ DON'T:**
```typescript
// Не использовать localStorage напрямую
localStorage.getItem('token')
localStorage.getItem('slide-speaker-auth-token')

// Не hardcode токены
headers: { 'Authorization': 'Bearer ...' }
```

---

**Дата:** 2025-01-15  
**Статус:** ✅ Исправлено  
**Требуется:** Перезагрузка страницы в браузере
