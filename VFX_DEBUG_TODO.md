# 🔧 Действия по отладке VFX

## Что сделано:

1. ✅ **Пересборка контейнеров** - `docker-compose down -v && docker-compose build --no-cache`
   - Удалены старые контейнеры и volumes
   - Запущена полная пересборка без кеша

2. ✅ **Добавлена расширенная отладка** в frontend:
   - `SlideViewer.tsx` - подробное логирование manifest
   - `VisualEffectsEngine.tsx` - валидация структуры manifest
   - Проверка наличия timeline и effects

3. ✅ **Создана тестовая страница** `/vfx-test`:
   - Изолированное тестирование VFX
   - Hardcoded manifest для проверки
   - Debug панель с метриками
   - Ручное управление timeline

4. ✅ **Создан гайд по отладке** - `VFX_DEBUGGING_GUIDE.md`

## Следующие шаги после завершения сборки:

### 1. Запустить контейнеры:
```bash
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main
docker-compose up -d
```

### 2. Проверить тестовую страницу:
```
http://localhost:3000/vfx-test
```
**Что проверить:**
- [ ] Страница загружается
- [ ] Debug панель видна
- [ ] Canvas element существует
- [ ] При нажатии Play появляется эффект (spotlight)
- [ ] В Console есть логи от VisualEffectsEngine

### 3. Проверить реальный плеер:
```
http://localhost:3000/player/75dc761d-f4f7-4ecc-8c53-d92a076ffc3c
```
**Что проверить:**
- [ ] В Console логи `[SlideViewer] 🎨 VFX Details`
- [ ] manifest передаётся корректно
- [ ] VisualEffectsEngine инициализируется
- [ ] Canvas рендерится
- [ ] Events срабатывают при воспроизведении

### 4. Ручной тест Canvas:
```javascript
// В Browser Console (F12)
const canvas = document.querySelector('canvas');
const ctx = canvas.getContext('2d');
ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
ctx.fillRect(100, 100, 200, 200);
```
**Ожидаемый результат:** Красный полупрозрачный квадрат на слайде

## Возможные причины проблемы:

1. **Manifest не передаётся:**
   - API не возвращает `visual_effects_manifest`
   - Frontend не читает поле

2. **Canvas не виден:**
   - z-index проблемы
   - Canvas имеет размеры 0x0
   - display: none

3. **Renderer не работает:**
   - Не инициализируется
   - Не запускается (.start() не вызывается)
   - Ошибки в render loop

4. **Timeline не синхронизируется:**
   - audioElement не передан
   - Events не привязаны
   - Callbacks не вызываются

## Debug команды:

```bash
# Проверить логи backend
docker logs slide-speaker-main-backend-1 2>&1 | grep -i vfx | tail -50

# Проверить manifest в файле
docker exec slide-speaker-main-backend-1 cat /app/.data/75dc761d-f4f7-4ecc-8c53-d92a076ffc3c/manifest.json | python3 -m json.tool | grep -A 20 "visual_effects_manifest"

# Проверить что frontend получил изменения
docker logs slide-speaker-main-frontend-1 2>&1 | tail -20
```

---

**Статус:** ⏳ Ожидание завершения сборки контейнеров
