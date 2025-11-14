# 🤔 SharedState в Load Testing vs Production

## ❓ Вопрос: "А как в проде это работает? У каждого аккаунта свой список лекций!"

**Короткий ответ:** В production всё изолировано по пользователям, но в **load testing** мы специально эмулируем сценарии взаимодействия!

---

## 🏭 Production (реальность)

### В реальном приложении:

```
User Alice (ID: 1):
  ✅ Свои уроки: [lesson_1, lesson_2]
  ✅ Свои плейлисты: [playlist_A]
  ❌ НЕ ВИДИТ уроки Bob'a

User Bob (ID: 2):
  ✅ Свои уроки: [lesson_3, lesson_4]
  ✅ Свои плейлисты: [playlist_B]
  ❌ НЕ ВИДИТ уроки Alice

User Carol (ID: 3):
  ✅ Свои уроки: [lesson_5]
  ✅ Может добавить в плейлист:
      - lesson_5 (свой) ✅
      - lesson_1 (Alice) если есть права/share ⚠️
      - lesson_3 (Bob) если есть права/share ⚠️
```

**Да, в production данные изолированы, НО:**

---

## 🔄 Production: Сценарии взаимодействия

### Даже с изоляцией, пользователи ВЗАИМОДЕЙСТВУЮТ:

#### 1. **Shared/Public Content**
```
User Alice:
  → Создает урок "Python Basics"
  → Делает его PUBLIC или SHARED
  
User Bob:
  → Открывает "Browse Public Lessons"
  → Видит "Python Basics" от Alice ✅
  → Добавляет в свой плейлист ✅
  → Генерирует quiz для этого урока ✅
```

#### 2. **Team/Organization Workspace**
```
Company XYZ (Organization):
  
  User Alice (role: Content Creator):
    → Создает урок для компании
    → lesson_1 принадлежит Organization
  
  User Bob (role: Editor):
    → Редактирует lesson_1 (тот же урок!) ✅
  
  User Carol (role: Manager):
    → Создает плейлист из всех уроков компании ✅
    → Включая lesson_1 от Alice
```

#### 3. **Shared Playlists**
```
User Alice:
  → Создает плейлист "Best Python Courses"
  → Генерирует share link: /shared/abc123
  
User Bob:
  → Открывает /shared/abc123
  → Видит плейлист Alice ✅
  → Может создать свою копию ✅
```

#### 4. **Import/Fork Content**
```
User Alice:
  → Публикует урок в marketplace
  
User Bob:
  → Импортирует урок Alice в свой аккаунт
  → Теперь может его редактировать
  → Создавать квизы
  → Добавлять в плейлисты
```

---

## 🧪 Load Testing: Что мы тестируем

### Load testing ≠ копия production, это **симуляция сценариев**!

В load testing мы **эмулируем** эти взаимодействия:

```python
# Симуляция 1: Public/Shared Content
ContentCreatorUser (Alice):
  → Создает урок → добавляет в SharedState (как будто сделал public)

BrowsingUser (Bob):
  → Берет урок из SharedState (как будто нашел в browse public)
  → Добавляет в свой плейлист

# Симуляция 2: Team Workspace
ContentCreatorUser (Alice):
  → Создает урок → SharedState (урок компании)

ContentEditorUser (Bob):
  → Берет тот же урок → редактирует (как коллега в компании)

# Симуляция 3: Concurrent Access
User 1-50:
  → Все работают с одними и теми же уроками
  → Тестируем race conditions, locks, concurrency
```

---

## 📊 Реальные сценарии в production

### Сценарий 1: Публичная библиотека уроков

**Как это работает в проде:**
```sql
-- User Alice создает урок
INSERT INTO lessons (id, user_id, title, visibility)
VALUES ('lesson_1', 1, 'Python Basics', 'PUBLIC');

-- User Bob ищет публичные уроки
SELECT * FROM lessons 
WHERE visibility = 'PUBLIC';  -- Видит lesson_1! ✅

-- User Bob добавляет в плейлист
INSERT INTO playlist_items (playlist_id, lesson_id, user_id)
VALUES ('bob_playlist', 'lesson_1', 2);  -- Использует урок Alice! ✅
```

**Как мы тестируем:**
```python
# Alice создает урок
SharedState.add_lesson("lesson_1")

# Bob берет урок
lesson_id = SharedState.get_random_lesson()  # "lesson_1"
# Добавляет в плейлист
```

### Сценарий 2: Корпоративный workspace

**Как это работает в проде:**
```sql
-- Все в одной организации
company_id = 123

-- Alice создает урок
INSERT INTO lessons (id, user_id, company_id, title)
VALUES ('lesson_1', 1, 123, 'Python Basics');

-- Bob (в той же компании) может редактировать
SELECT * FROM lessons 
WHERE company_id = 123;  -- Видит lesson_1! ✅

-- Carol может создать плейлист
SELECT * FROM lessons 
WHERE company_id = 123;  -- Все уроки компании! ✅
```

**Как мы тестируем:**
```python
# Эмулируем company workspace
# Все пользователи = сотрудники одной компании
SharedState.add_lesson("lesson_1")  # Урок компании

# Любой "сотрудник" может взять
lesson_id = SharedState.get_random_lesson()
```

### Сценарий 3: Shared Links

**Как это работает в проде:**
```sql
-- Alice создает shared playlist
INSERT INTO playlist_shares (playlist_id, token, permissions)
VALUES ('playlist_1', 'abc123', 'READ');

-- Bob использует share link
SELECT * FROM playlist_shares 
WHERE token = 'abc123';  -- Находит! ✅

-- Bob видит плейлист Alice
SELECT * FROM playlists 
WHERE id = 'playlist_1';  -- Доступ есть! ✅
```

**Как мы тестируем:**
```python
# Alice создает и шарит
SharedState.add_playlist("playlist_1")

# Bob получает доступ
playlist_id = SharedState.get_random_playlist()
```

---

## 🎯 Зачем SharedState: Реальные причины

### 1. **Тестируем Database Concurrency**

В production НЕ БЫВАЕТ полной изоляции. Даже если у каждого свои данные:

```sql
-- 50 пользователей одновременно:
SELECT * FROM lessons WHERE user_id IN (1,2,3...50);
SELECT * FROM playlists WHERE user_id IN (1,2,3...50);

-- Database видит параллельные запросы к РАЗНЫМ данным
-- Но нагрузка на:
-- ✅ Connection pool
-- ✅ Query cache
-- ✅ Index
-- ✅ Disk I/O
-- Всё это ОБЩЕЕ!
```

SharedState эмулирует эту **shared infrastructure load**.

### 2. **Тестируем Cross-User Features**

Реальные фичи, которые есть в вашем production:

```typescript
// Frontend: Browse Public Lessons
GET /api/lessons?visibility=public
// Возвращает уроки РАЗНЫХ пользователей! ✅

// Frontend: Shared Playlists
GET /api/playlists/shared/{token}
// Доступ к плейлисту ДРУГОГО пользователя! ✅

// Frontend: Organization Dashboard
GET /api/organization/123/lessons
// Все уроки ВСЕХ сотрудников! ✅

// Frontend: Import Lesson
POST /api/lessons/{lesson_id}/import
// Копирует урок ДРУГОГО пользователя! ✅
```

Без SharedState эти endpoints **НЕ ТЕСТИРУЮТСЯ**!

### 3. **Тестируем Race Conditions**

```python
# Production сценарий:
# User A и User B одновременно редактируют lesson_1

# Time: 00:00
User A: GET /lessons/lesson_1/manifest  # version=1
User B: GET /lessons/lesson_1/manifest  # version=1

# Time: 00:01
User A: PATCH /lessons/lesson_1  # Изменяет слайд 1
User B: PATCH /lessons/lesson_1  # Изменяет слайд 2

# Что произойдет?
# ✅ Conflict detection работает?
# ✅ Optimistic locking работает?
# ✅ Последние изменения сохраняются?
```

SharedState позволяет симулировать это!

### 4. **Тестируем Cache Invalidation**

```python
# Production:
User A: GET /lessons/lesson_1  # Кэшируется
User B: PATCH /lessons/lesson_1  # Изменяет
User A: GET /lessons/lesson_1  # Должен видеть изменения! ✅

# Работает ли инвалидация кэша?
# SharedState проверяет это!
```

---

## 🏗️ Архитектура: Production vs Load Testing

### Production Architecture:
```
User Alice → API → DB (alice_data)
User Bob   → API → DB (bob_data)
User Carol → API → DB (carol_data)

Shared Resources:
  ✅ Connection Pool (10-100 connections)
  ✅ Redis Cache (shared memory)
  ✅ Database Locks (shared)
  ✅ File Storage (shared disk)
  ✅ CPU/Memory (shared server)
```

### Load Testing With SharedState:
```
Virtual User 1 → API → DB (shared_data)
Virtual User 2 → API → DB (shared_data)
Virtual User 50 → API → DB (shared_data)

Simulates:
  ✅ Connection Pool Exhaustion
  ✅ Cache Contention
  ✅ Lock Contention
  ✅ Disk I/O Limits
  ✅ CPU/Memory Limits
```

**SharedState = симуляция shared infrastructure load!**

---

## 💡 Конкретный пример

### Production Scenario: EdTech Platform

**Реальная архитектура:**
```
Company "TechCorp" (Organization ID: 123):
  ├── Alice (Content Creator)
  ├── Bob (Editor)
  ├── Carol (Manager)
  └── 100 Students

Lessons:
  ✅ lesson_1 (created by Alice, company_id=123)
  ✅ lesson_2 (created by Bob, company_id=123)
  ✅ lesson_3 (public, anyone can access)
```

**Реальные взаимодействия:**
```
09:00 - Alice создает lesson_4
09:05 - Bob редактирует lesson_4 (collaboration!)
09:10 - Carol добавляет lesson_4 в company playlist
09:15 - 100 students одновременно смотрят lesson_4
        (100 concurrent GET requests!)
09:20 - Bob генерирует quiz для lesson_4
09:25 - Alice генерирует speaker notes для lesson_4
```

**Load Test С SharedState:**
```python
# Эмулируем TechCorp organization
ContentCreatorUser (Alice):
  → Creates lesson_4
  → SharedState.add_lesson("lesson_4")

ContentEditorUser (Bob):
  → lesson_id = SharedState.get_random_lesson()  # lesson_4
  → Edits lesson_4 ✅ (реалистично!)

PlaylistManagerUser (Carol):
  → lesson_id = SharedState.get_random_lesson()  # lesson_4
  → Adds to playlist ✅ (реалистично!)

BrowsingUser (100 students):
  → lesson_id = SharedState.get_random_lesson()  # lesson_4
  → 100x GET /lessons/lesson_4 ✅ (реалистично!)

AIGenerationUser (Bob):
  → lesson_id = SharedState.get_random_lesson()  # lesson_4
  → Generates quiz ✅ (реалистично!)

AIGenerationUser (Alice):
  → lesson_id = SharedState.get_random_lesson()  # lesson_4
  → Generates notes ✅ (реалистично!)
```

**Результат:** Тестируется **ТОЧНО ТА ЖЕ НАГРУЗКА**, что будет в production!

---

## 🎯 Итоговое сравнение

| Аспект | Production | Load Test БЕЗ SharedState | Load Test С SharedState |
|--------|-----------|---------------------------|------------------------|
| **Изоляция данных** | ✅ У каждого свои данные | ✅ У каждого свои данные | ⚠️ Эмуляция shared access |
| **Public/Shared content** | ✅ Работает | ❌ НЕ тестируется | ✅ Тестируется |
| **Team collaboration** | ✅ Работает | ❌ НЕ тестируется | ✅ Тестируется |
| **Concurrent access** | ✅ 100+ users → 1 lesson | ❌ Каждый в вакууме | ✅ Эмулируется |
| **Database load** | ✅ Shared pool/cache/locks | ❌ Искусственно разделено | ✅ Realistic load |
| **Race conditions** | ✅ Возможны | ❌ Невозможны | ✅ Тестируются |
| **Cache invalidation** | ✅ Критично | ❌ Не проверяется | ✅ Проверяется |

---

## 🎉 Заключение

### SharedState НЕ означает "все видят все данные в production"!

**SharedState = инструмент для эмуляции:**

1. ✅ **Public/Shared контента** (который реально есть)
2. ✅ **Team collaboration** (который реально есть)
3. ✅ **Concurrent access** (который реально есть)
4. ✅ **Shared infrastructure** (connection pool, cache, locks)
5. ✅ **Cross-user features** (browse, import, share)

### Вопрос был про production:

> "У каждого аккаунта свой список лекций"

**Ответ:**
- ✅ Да, свой список
- ✅ НО есть public/shared контент
- ✅ НО есть team workspaces
- ✅ НО вся инфраструктура shared (DB, cache, servers)
- ✅ НО concurrent access к популярным урокам

**SharedState тестирует ВСЁ это, не нарушая концепцию изоляции данных в production!**

---

## 📚 Дополнительно

### Если в вашем production НЕТ shared/public контента:

Тогда SharedState всё равно полезен для:
1. **Database connection pool testing** (shared!)
2. **Redis cache testing** (shared!)
3. **Server resource testing** (CPU/memory shared!)
4. **API rate limiting testing** (shared!)

Даже если данные изолированы, **инфраструктура всегда shared**! 🚀
