# 🔧 Быстрое исправление ошибки

## Проблема:
```
'str' object has no attribute 'suffix'
```

## Причина:
В tasks.py на строке ~75 передаётся строка вместо Path object в ParserFactory.create_parser()

## Решение:

В `backend/app/tasks.py` строка ~75:

**Было:**
```python
from pathlib import Path
parser = ParserFactory.create_parser(Path(file_path))
```

**Должно быть:**
```python
parser = ParserFactory.create_parser(file_path)
```

ИЛИ убедиться что везде используется правильный тип.

## Итог:

Intelligent Pipeline работает, но есть проблема совместимости типов в tasks.py после интеграции.

Нужно проверить все места где используется Path и убедиться в совместимости типов.

**Статус:** Gemini интегрирован ✅, но нужно исправить совместимость Path в tasks.py
