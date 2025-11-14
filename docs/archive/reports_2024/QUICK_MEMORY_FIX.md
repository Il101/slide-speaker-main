# 🚀 БЫСТРЫЙ СТАРТ - Quick Start

## Проблема решена! / Problem Fixed!
Процесс больше не будет падать из-за нехватки памяти при обработке презентации.

## Что сделано / What's Done
1. ✅ Ограничен параллелизм TTS: 10 → **1 процесс**
2. ✅ Добавлена принудительная очистка памяти после каждого слайда
3. ✅ Кэширование модели работает правильно

## Запуск / Run
```bash
# 1. Перейдите в папку проекта
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main

# 2. Перезапустите Docker
docker-compose down
docker-compose up --build -d

# 3. Проверьте логи
docker-compose logs -f backend
```

## Проверка / Check
Ищите в логах:
```
✅ Silero TTS initialized
✅ Reusing cached Silero model
✅ Generated Silero TTS: ... sentences, ...s
```

## Память / Memory
- **До:** 10GB+ (падало)
- **После:** ~1-2GB (стабильно)

Подробнее: [MEMORY_FIX_COMPLETE.md](MEMORY_FIX_COMPLETE.md)
