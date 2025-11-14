#!/bin/bash
# Простой тест Gemini TTS через curl (без Python зависимостей)

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-inspiring-keel-473421-j2}"
OUTPUT_DIR=".test_results/gemini_tts_test"
mkdir -p "$OUTPUT_DIR"

# Установить GOOGLE_APPLICATION_CREDENTIALS если не установлен
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="./inspiring-keel-473421-j2-22cc51dfb336.json"
    echo "ℹ️  Установлен GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"
fi

echo "======================================================================"
echo "🧪 ТЕСТ: Gemini TTS Flash 2.5 через REST API"
echo "======================================================================"
echo ""

# Получить access token
echo "🔑 Получаем access token..."
ACCESS_TOKEN=$(gcloud auth application-default print-access-token 2>/dev/null || gcloud auth print-access-token)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Не удалось получить access token"
    echo "   Запустите: gcloud auth application-default login"
    exit 1
fi

echo "✅ Access token получен"
echo ""

# Тест 1: Базовый синтез
echo "======================================================================"
echo "🧪 ТЕСТ 1: Базовый синтез с Gemini TTS Flash"
echo "======================================================================"

curl -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "x-goog-user-project: $PROJECT_ID" \
  -d '{
    "input": {
      "text": "Hello world! This is a test of Gemini TTS Flash."
    },
    "voice": {
      "languageCode": "en-US",
      "name": "Kore",
      "model": "gemini-2.5-flash-tts"
    },
    "audioConfig": {
      "audioEncoding": "MP3"
    }
  }' \
  "https://texttospeech.googleapis.com/v1/text:synthesize" \
  > "$OUTPUT_DIR/test1_response.json"

if [ $? -eq 0 ]; then
    echo "✅ Базовый синтез: SUCCESS"
    
    # Извлечь аудио из response
    cat "$OUTPUT_DIR/test1_response.json" | jq -r '.audioContent' | base64 -d > "$OUTPUT_DIR/test1_basic.mp3"
    
    SIZE=$(wc -c < "$OUTPUT_DIR/test1_basic.mp3")
    echo "   Файл: $OUTPUT_DIR/test1_basic.mp3"
    echo "   Размер: $SIZE bytes"
    
    # Проверить наличие timepoints в response
    TIMEPOINTS=$(cat "$OUTPUT_DIR/test1_response.json" | jq -r '.timepoints // empty')
    if [ -z "$TIMEPOINTS" ]; then
        echo "   ❌ Timepoints: НЕТ в response"
    else
        echo "   ✅ Timepoints: ЕСТЬ в response"
        echo "$TIMEPOINTS" | jq '.'
    fi
else
    echo "❌ Базовый синтез: FAILED"
fi

echo ""

# Тест 2: Русский язык
echo "======================================================================"
echo "🧪 ТЕСТ 2: Поддержка русского языка"
echo "======================================================================"

curl -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "x-goog-user-project: $PROJECT_ID" \
  -d '{
    "input": {
      "text": "Привет мир! Это тест голосовой модели Gemini."
    },
    "voice": {
      "languageCode": "ru-RU",
      "name": "Kore",
      "model": "gemini-2.5-flash-tts"
    },
    "audioConfig": {
      "audioEncoding": "MP3"
    }
  }' \
  "https://texttospeech.googleapis.com/v1/text:synthesize" \
  > "$OUTPUT_DIR/test2_response.json"

if [ $? -eq 0 ]; then
    echo "✅ Русский язык: SUCCESS"
    
    cat "$OUTPUT_DIR/test2_response.json" | jq -r '.audioContent' | base64 -d > "$OUTPUT_DIR/test2_russian.mp3"
    
    SIZE=$(wc -c < "$OUTPUT_DIR/test2_russian.mp3")
    echo "   Файл: $OUTPUT_DIR/test2_russian.mp3"
    echo "   Размер: $SIZE bytes"
else
    echo "❌ Русский язык: FAILED"
fi

echo ""

# Тест 3: КРИТИЧЕСКИЙ - SSML с mark тегами
echo "======================================================================"
echo "🧪 ТЕСТ 3: ⚠️  КРИТИЧЕСКИЙ - SSML <mark> теги + timepoints"
echo "======================================================================"

curl -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "x-goog-user-project: $PROJECT_ID" \
  -d '{
    "input": {
      "ssml": "<speak>Hello <mark name=\"mark1\"/> world. This <mark name=\"mark2\"/> is a test.</speak>"
    },
    "voice": {
      "languageCode": "en-US",
      "name": "Kore",
      "model": "gemini-2.5-flash-tts"
    },
    "audioConfig": {
      "audioEncoding": "LINEAR16",
      "sampleRateHertz": 24000
    },
    "enableTimePointing": ["SSML_MARK"]
  }' \
  "https://texttospeech.googleapis.com/v1/text:synthesize" \
  > "$OUTPUT_DIR/test3_response.json"

if [ $? -eq 0 ]; then
    echo "✅ SSML синтез: SUCCESS"
    
    # Проверить response
    cat "$OUTPUT_DIR/test3_response.json" | jq -r '.audioContent' | base64 -d > "$OUTPUT_DIR/test3_marks.wav"
    
    SIZE=$(wc -c < "$OUTPUT_DIR/test3_marks.wav")
    echo "   Файл: $OUTPUT_DIR/test3_marks.wav"
    echo "   Размер: $SIZE bytes"
    
    # КРИТИЧЕСКАЯ ПРОВЕРКА: есть ли timepoints?
    TIMEPOINTS=$(cat "$OUTPUT_DIR/test3_response.json" | jq -r '.timepoints // empty')
    if [ -z "$TIMEPOINTS" ]; then
        echo ""
        echo "   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        echo "   ❌ КРИТИЧНО: Timepoints НЕТ в response"
        echo "   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        echo ""
        echo "   Это значит, что Gemini TTS НЕ поддерживает timepoints,"
        echo "   что делает миграцию НЕВОЗМОЖНОЙ без деградации продукта."
        echo ""
        CAN_MIGRATE="NO"
    else
        echo "   ✅ Timepoints: ЕСТЬ в response"
        echo "   Детали:"
        echo "$TIMEPOINTS" | jq '.'
        CAN_MIGRATE="YES"
    fi
else
    echo "❌ SSML синтез: FAILED"
    CAN_MIGRATE="UNKNOWN"
fi

echo ""

# Тест 4: Промпты для стилистики
echo "======================================================================"
echo "🧪 ТЕСТ 4: Промпты для контроля стиля"
echo "======================================================================"

curl -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "x-goog-user-project: $PROJECT_ID" \
  -d '{
    "input": {
      "text": "This is a test of emotional expression.",
      "prompt": "Speak like a friendly tutor explaining a topic to a student"
    },
    "voice": {
      "languageCode": "en-US",
      "name": "Kore",
      "model": "gemini-2.5-flash-tts"
    },
    "audioConfig": {
      "audioEncoding": "MP3"
    }
  }' \
  "https://texttospeech.googleapis.com/v1/text:synthesize" \
  > "$OUTPUT_DIR/test4_response.json"

if [ $? -eq 0 ]; then
    echo "✅ Промпты: SUCCESS"
    
    cat "$OUTPUT_DIR/test4_response.json" | jq -r '.audioContent' | base64 -d > "$OUTPUT_DIR/test4_prompt.mp3"
    
    SIZE=$(wc -c < "$OUTPUT_DIR/test4_prompt.mp3")
    echo "   Файл: $OUTPUT_DIR/test4_prompt.mp3"
    echo "   Размер: $SIZE bytes"
    
    # Проверить, есть ли ошибка
    ERROR=$(cat "$OUTPUT_DIR/test4_response.json" | jq -r '.error // empty')
    if [ -n "$ERROR" ]; then
        echo "   ❌ Ошибка в response:"
        echo "$ERROR" | jq '.'
    fi
else
    echo "❌ Промпты: FAILED"
fi

echo ""

# Тест 5: Markup tags
echo "======================================================================"
echo "🧪 ТЕСТ 5: Markup tags ([pause], [whispering], etc)"
echo "======================================================================"

curl -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "x-goog-user-project: $PROJECT_ID" \
  -d '{
    "input": {
      "text": "Hello. [medium pause] This is a test. [whispering] Can you hear this whisper? [extremely fast] This part should be very fast.",
      "prompt": "Read this text naturally with the markup instructions"
    },
    "voice": {
      "languageCode": "en-US",
      "name": "Kore",
      "model": "gemini-2.5-flash-tts"
    },
    "audioConfig": {
      "audioEncoding": "MP3"
    }
  }' \
  "https://texttospeech.googleapis.com/v1/text:synthesize" \
  > "$OUTPUT_DIR/test5_response.json"

if [ $? -eq 0 ]; then
    echo "✅ Markup tags: SUCCESS"
    
    cat "$OUTPUT_DIR/test5_response.json" | jq -r '.audioContent' | base64 -d > "$OUTPUT_DIR/test5_markup.mp3"
    
    SIZE=$(wc -c < "$OUTPUT_DIR/test5_markup.mp3")
    echo "   Файл: $OUTPUT_DIR/test5_markup.mp3"
    echo "   Размер: $SIZE bytes"
    
    # Проверить, есть ли ошибка
    ERROR=$(cat "$OUTPUT_DIR/test5_response.json" | jq -r '.error // empty')
    if [ -n "$ERROR" ]; then
        echo "   ❌ Ошибка в response:"
        echo "$ERROR" | jq '.'
    fi
else
    echo "❌ Markup tags: FAILED"
fi

echo ""

# Итоговая сводка
echo "======================================================================"
echo "🏁 ФИНАЛЬНЫЙ ВЕРДИКТ"
echo "======================================================================"
echo ""

if [ "$CAN_MIGRATE" = "YES" ]; then
    echo "✅ МОЖНО мигрировать на Gemini TTS Flash 2.5"
    echo ""
    echo "Причины:"
    echo "  ✅ Timepoints поддерживаются"
    echo "  ✅ Синхронизация визуальных эффектов сохранится"
else
    echo "❌ НЕ РЕКОМЕНДУЕТСЯ мигрировать на Gemini TTS Flash 2.5"
    echo ""
    echo "Причины:"
    echo "  ❌ КРИТИЧНО: Timepoints НЕ поддерживаются"
    echo "  ❌ Синхронизация визуальных эффектов СЛОМАЕТСЯ"
    echo "  ⚠️  Нужна деградация функциональности"
fi

echo ""
echo "======================================================================"
echo "📁 Все результаты сохранены в: $OUTPUT_DIR"
echo "======================================================================"
