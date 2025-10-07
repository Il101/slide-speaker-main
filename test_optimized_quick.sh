#!/bin/bash
# Быстрый тест оптимизированного пайплайна

echo "🧪 Тестирование OptimizedIntelligentPipeline"
echo "============================================"
echo ""

# Проверяем настройки
echo "1. Проверка конфигурации:"
docker exec slide-speaker-main-celery-1 printenv | grep PIPELINE
echo ""

# Проверяем что OptimizedIntelligentPipeline доступен
echo "2. Проверка OptimizedIntelligentPipeline:"
docker exec slide-speaker-main-celery-1 python -c "from app.pipeline import get_pipeline; p = get_pipeline('intelligent_optimized'); print(f'✅ {p.__name__} loaded')"
echo ""

# Загружаем презентацию
echo "3. Загружаем презентацию через API..."
RESPONSE=$(curl -s -X POST http://localhost:8000/upload \
  -F "file=@test_real.pptx" \
  -H "Accept: application/json")

LESSON_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('lesson_id', ''))")

if [ -z "$LESSON_ID" ]; then
    echo "❌ Ошибка загрузки презентации"
    echo "Response: $RESPONSE"
    exit 1
fi

echo "✅ Презентация загружена: $LESSON_ID"
echo ""

# Ждём обработки и мониторим логи
echo "4. Мониторинг обработки (жду 60 секунд)..."
echo "   Следите за логами Celery для OptimizedIntelligentPipeline..."
echo ""

# Показываем логи в реальном времени
timeout 60s docker logs -f slide-speaker-main-celery-1 2>&1 | grep -E "intelligent_optimized|OptimizedPipeline|⚡|Processing.*parallel" &
LOG_PID=$!

# Ждём завершения
sleep 60
kill $LOG_PID 2>/dev/null

echo ""
echo "5. Проверка результатов..."

# Проверяем manifest
if [ -f ".data/$LESSON_ID/manifest.json" ]; then
    SLIDES=$(cat .data/$LESSON_ID/manifest.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('slides', [])))")
    echo "✅ Manifest создан: $SLIDES слайдов"
    
    # Проверяем аудио
    AUDIO_COUNT=$(ls -1 .data/$LESSON_ID/audio/*.wav 2>/dev/null | wc -l)
    echo "✅ Аудио файлов: $AUDIO_COUNT"
    
    # Проверяем первый слайд
    DURATION=$(cat .data/$LESSON_ID/manifest.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['slides'][0].get('duration', 0))")
    echo "✅ Длительность слайда 1: ${DURATION}s"
else
    echo "❌ Manifest не найден"
fi

echo ""
echo "============================================"
echo "✅ Тест завершён!"
