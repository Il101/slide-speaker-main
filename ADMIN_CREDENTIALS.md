# 🔐 Учетные данные для доступа к системе

**Дата создания:** 2 ноября 2025

---

## 👨‍💼 Администратор

**Email:** `admin@example.com`  
**Password:** `admin123`  
**Role:** `admin`  
**User ID:** `D91BCD7F-9CCB-447C-8F2F-917A5C329A13`  
**Subscription Tier:** `premium`  
**Status:** ✅ Active

### Возможности админа:
- Полный доступ ко всем функциям системы
- Управление пользователями
- Просмотр всех уроков и плейлистов
- Доступ к аналитике
- Управление подписками

---

## 👤 Тестовый пользователь

**Email:** `test@example.com`  
**Password:** `TestPassword123!`  
**Role:** `user`  
**User ID:** `34eb0f28-77f6-4740-9f23-0f751ecb0e35`  
**Status:** ✅ Active

### Возможности пользователя:
- Создание и редактирование своих уроков
- Создание плейлистов
- Экспорт видео
- Доступ к базовым функциям

---

## 🔒 Примечания по безопасности

⚠️ **ВАЖНО:** Эти учетные данные предназначены только для разработки и тестирования!

**Для продакшена:**
1. Измените пароли на более надежные
2. Используйте переменные окружения для хранения секретов
3. Включите email-верификацию
4. Настройте 2FA (двухфакторную аутентификацию)
5. Регулярно ротируйте пароли

---

## 📝 Как создать нового админа

Если нужно создать дополнительного админа, используйте следующую команду:

```bash
docker exec slide-speaker-main-postgres-1 psql -U postgres -d slide_speaker -c "
INSERT INTO users (id, email, username, hashed_password, role, subscription_tier, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid()::text,
    'newemail@example.com',
    'newadmin',
    '\$pbkdf2-sha256\$29000\$...',  -- используйте хеш из скрипта
    'admin',
    'premium',
    true,
    NOW(),
    NOW()
);
"
```

Для генерации хеша пароля:
```bash
docker exec slide-speaker-main-backend-1 python3 -c "
import sys
sys.path.insert(0, '/app')
from app.core.auth import AuthManager
print(AuthManager.get_password_hash('your_password_here'))
"
```

---

## ✅ Проверено

- [x] Админ может войти в систему
- [x] Получение профиля работает
- [x] Роль `admin` установлена корректно
- [x] JWT токены генерируются правильно
- [x] HttpOnly cookies настроены
- [x] Тестовый пользователь работает

---

**Создано:** GitHub Copilot  
**Дата:** 2 ноября 2025
