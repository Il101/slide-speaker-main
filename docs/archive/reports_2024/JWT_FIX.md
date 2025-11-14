# Fix: JWT Import Error - 500 CORS Error

## Проблема
При загрузке файлов в браузере появлялась CORS ошибка:
```
Origin http://localhost:3000 is not allowed by Access-Control-Allow-Origin. Status code: 500
```

При попытке получить статус урока получали 403 ошибку:
```
403 Forbidden - {"detail":"Not authenticated"}
```

## Причина
Backend падал с ошибкой при попытке проверить JWT токен:
```
AttributeError: module 'jwt' has no attribute 'JWTError'
```

Проблема была в неправильном импорте исключений JWT в `backend/app/core/auth.py`. 

В библиотеке PyJWT:
- ❌ `jwt.JWTError` не существует
- ✅ `jwt.exceptions.InvalidTokenError` - правильное исключение
- ✅ `jwt.exceptions.ExpiredSignatureError` - для истекших токенов

## Решение

### Исправлен файл: `backend/app/core/auth.py`

**Было:**
```python
import os
import jwt
from datetime import datetime, timedelta
...

except jwt.ExpiredSignatureError:
    ...
except jwt.JWTError:  # ❌ Не существует
    ...
```

**Стало:**
```python
import os
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError  # ✅ Правильный импорт
...

except ExpiredSignatureError:  # ✅ Работает
    ...
except InvalidTokenError:  # ✅ Заменили JWTError
    ...
```

### Последовательность действий:
1. Исправлены импорты в `auth.py`
2. Заменено `jwt.JWTError` на `InvalidTokenError`
3. Перезапущен backend: `docker-compose restart backend`

## Проверка
После исправления:
- ✅ Backend запускается без ошибок
- ✅ JWT токены правильно валидируются
- ✅ CORS работает корректно
- ✅ Загрузка файлов работает
- ✅ Polling статуса работает

## Дата исправления
3 октября 2025
