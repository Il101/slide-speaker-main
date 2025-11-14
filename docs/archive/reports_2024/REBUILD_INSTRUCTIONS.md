# 🔧 Инструкции по пересборке после изменений

## Когда нужна пересборка?

### ✅ Изменения требующие пересборки:
- **Python код** (`.py` файлы в `backend/`) - нужна пересборка backend
- **Frontend код** (`.tsx`, `.ts` файлы в `src/`) - нужна пересборка frontend
- **Requirements** (`requirements.txt`) - нужна пересборка backend
- **Package.json** (`package.json`) - нужна пересборка frontend

### ❌ Изменения НЕ требующие пересборки:
- **Environment файлы** (`.env`, `docker.env`) - достаточно `docker-compose restart`
- **Docker compose** (`docker-compose.yml`) - достаточно `docker-compose up -d`

## Команды пересборки

### 1. Полная пересборка (все сервисы)
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 2. Пересборка только backend
```bash
docker-compose build --no-cache backend celery
docker-compose up -d backend celery
```

### 3. Пересборка только frontend
```bash
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### 4. Быстрая пересборка (с кешем)
```bash
docker-compose build backend frontend
docker-compose up -d
```

## Проверка сборки

### Проверить когда были созданы образы:
```bash
docker images | grep slide-speaker
```

### Проверить логи сборки:
```bash
docker-compose logs backend --tail=50
docker-compose logs frontend --tail=50
```

### Проверить работающие контейнеры:
```bash
docker-compose ps
```

## Исправленные файлы (требуют пересборки backend)

1. **backend/app/services/sprint2/ai_generator.py** (lines 107-145)
   - `generate_visual_cues()` теперь использует реальные OCR bbox координаты
   - Вместо hardcoded `[100, 100, 800, 200]`

2. **src/components/Player.tsx** (lines 415-436)
   - `togglePlayPause()` теперь правильно обрабатывает Promise от `audio.play()`
   - Добавлена обработка ошибок autoplay

## После пересборки

1. **Загрузите презентацию заново** - старая использует старые координаты cues
2. **Откройте DevTools** (F12) → Console для проверки логов audio
3. **Проверьте**:
   - ✅ Аудио воспроизводится без остановки
   - ✅ Визуальные эффекты подсвечивают реальный текст
   - ✅ Субтитры без SSML тегов (уже работает)

## Troubleshooting

### Сборка застряла
```bash
# Прервите (Ctrl+C) и перезапустите
docker-compose build --no-cache --progress=plain backend 2>&1 | tee build.log
```

### Образы не обновились
```bash
# Проверьте время создания
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}"

# Удалите старые образы
docker rmi slide-speaker-main-backend slide-speaker-main-celery
docker-compose build --no-cache backend celery
```

### Контейнеры не запускаются
```bash
# Проверьте логи
docker-compose logs --tail=100

# Пересоздайте контейнеры
docker-compose down
docker-compose up -d
```
