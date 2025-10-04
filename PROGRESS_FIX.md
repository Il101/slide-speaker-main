# Fix: Progress Updates Not Working

## Проблема
Прогресс обработки застревал на первом шаге (initializing) и не обновлялся дальше.

## Причина
В `backend/app/tasks.py` функция `process_lesson_full_pipeline` обновляла поле `processing_progress` в базе данных только в начале (initializing) и в конце (completed). Промежуточные этапы (parsing, generating_notes, generating_audio, generating_cues) обновлялись только в Celery state, но не в БД.

Поскольку frontend poll'ит `/lessons/{id}/status` который читает из БД, он не видел обновлений промежуточных этапов.

## Решение
Добавили `db.execute()` + `db.commit()` после каждого вызова `self.update_state()`:

### Изменения в backend/app/tasks.py

1. **После parsing (20%)**
```python
# Update DB with parsing stage
db.execute(text("""
    UPDATE lessons 
    SET processing_progress = :progress
    WHERE id = :lesson_id
"""), {
    'progress': json.dumps({'stage': 'parsing', 'progress': 20}),
    'lesson_id': lesson_id
})
db.commit()
```

2. **После generating_notes (50%)**
```python
# Update DB with generating_notes stage
db.execute(text("""
    UPDATE lessons 
    SET processing_progress = :progress
    WHERE id = :lesson_id
"""), {
    'progress': json.dumps({'stage': 'generating_notes', 'progress': 50}),
    'lesson_id': lesson_id
})
db.commit()
```

3. **После generating_audio (70%)**
```python
# Update DB with generating_audio stage
db.execute(text("""
    UPDATE lessons 
    SET processing_progress = :progress
    WHERE id = :lesson_id
"""), {
    'progress': json.dumps({'stage': 'generating_audio', 'progress': 70}),
    'lesson_id': lesson_id
})
db.commit()
```

4. **После generating_cues (90%)**
```python
# Update DB with generating_cues stage
db.execute(text("""
    UPDATE lessons 
    SET processing_progress = :progress
    WHERE id = :lesson_id
"""), {
    'progress': json.dumps({'stage': 'generating_cues', 'progress': 90}),
    'lesson_id': lesson_id
})
db.commit()
```

### Добавлено логирование в frontend

**src/components/FileUploader.tsx:**
- Добавлены console.log для отслеживания polling
- Логируются все поля статуса: lesson_id, status, stage, progress, message

**src/lib/api.ts:**
- Добавлено логирование запросов и ответов getLessonStatus

## Как проверить
1. Перезапустить backend и celery:
   ```bash
   docker-compose restart backend celery
   ```

2. Загрузить презентацию

3. Открыть DevTools консоль (F12)

4. Наблюдать логи:
   - `[FileUploader] Starting polling for lesson: ...`
   - `[API] Fetching lesson status for: ...`
   - `[API] Lesson status response: {status, stage, progress}`
   - `[FileUploader] Status poll result: {...}`

5. Прогресс должен обновляться: initializing → parsing → generating_notes → generating_audio → generating_cues → completed

## Дата исправления
3 октября 2025
