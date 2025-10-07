#!/usr/bin/env bash
set -e

# Smoke test script for pipeline testing
# Usage: ./scripts/smoke.sh [api_url]

API=${API:-http://localhost:8000}
MODE=classic
DEMO_FILE=${DEMO_FILE:-test.pdf}

echo "🧪 Running smoke test for pipeline: $MODE"
echo "📡 API: $API"
echo "📄 Demo file: $DEMO_FILE"

# Check if demo file exists
if [ ! -f "$DEMO_FILE" ]; then
    echo "❌ Demo file not found: $DEMO_FILE"
    echo "Please provide a PDF file via DEMO_FILE environment variable"
    exit 1
fi

# Check if API is running
echo "🔍 Checking API health..."
if ! curl -s "$API/health" > /dev/null; then
    echo "❌ API is not running at $API"
    echo "Please start the backend server first"
    exit 1
fi
echo "✅ API is running"

# Upload file
echo "📤 Uploading file..."
UPLOAD_RESPONSE=$(curl -s -F "file=@$DEMO_FILE" "$API/upload?pipeline=$MODE")
LESSON_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.lesson_id')

if [ "$LESSON_ID" = "null" ] || [ -z "$LESSON_ID" ]; then
    echo "❌ Upload failed"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo "✅ Upload successful, lesson ID: $LESSON_ID"

# Wait a moment for processing
echo "⏳ Waiting for document processing..."
sleep 2

# Generate audio
echo "🎵 Generating audio..."
AUDIO_RESPONSE=$(curl -s -X POST "$API/lessons/$LESSON_ID/generate-audio")
AUDIO_STATUS=$(echo "$AUDIO_RESPONSE" | jq -r '.status')

if [ "$AUDIO_STATUS" != "success" ]; then
    echo "❌ Audio generation failed"
    echo "Response: $AUDIO_RESPONSE"
    exit 1
fi

echo "✅ Audio generation successful"

# Wait for processing
echo "⏳ Waiting for audio processing..."
sleep 5

# Get manifest and check results
echo "📋 Checking manifest..."
MANIFEST_RESPONSE=$(curl -s "$API/lessons/$LESSON_ID/manifest")
MANIFEST_DATA=$(echo "$MANIFEST_RESPONSE" | jq '.')

# Extract key metrics
SLIDES_COUNT=$(echo "$MANIFEST_DATA" | jq '.slides | length')
FIRST_SLIDE_ELEMENTS=$(echo "$MANIFEST_DATA" | jq '.slides[0].elements | length')
FIRST_SLIDE_CUES=$(echo "$MANIFEST_DATA" | jq '.slides[0].cues | length')
FIRST_SLIDE_AUDIO=$(echo "$MANIFEST_DATA" | jq '.slides[0].audio')
FIRST_SLIDE_LECTURE_TEXT=$(echo "$MANIFEST_DATA" | jq '.slides[0].lecture_text | length')
TIMELINE_LENGTH=$(echo "$MANIFEST_DATA" | jq '.timeline | length')

echo "📊 Results for pipeline '$MODE':"
echo "  📄 Slides: $SLIDES_COUNT"
echo "  🎯 Elements (slide 0): $FIRST_SLIDE_ELEMENTS"
echo "  ⏰ Cues (slide 0): $FIRST_SLIDE_CUES"
echo "  🎵 Audio: $FIRST_SLIDE_AUDIO"
echo "  📝 Lecture text length: $FIRST_SLIDE_LECTURE_TEXT"
echo "  📅 Timeline events: $TIMELINE_LENGTH"

# Validate results based on pipeline type
echo "🔍 Validating results..."

VALIDATION_PASSED=true

# Check basic requirements
if [ "$SLIDES_COUNT" -eq 0 ]; then
    echo "❌ No slides found"
    VALIDATION_PASSED=false
fi

if [ "$FIRST_SLIDE_LECTURE_TEXT" -eq 0 ]; then
    echo "❌ No lecture text generated"
    VALIDATION_PASSED=false
fi

if [ "$TIMELINE_LENGTH" -eq 0 ]; then
    echo "❌ No timeline events"
    VALIDATION_PASSED=false
fi

# Pipeline-specific validations
if [ "$FIRST_SLIDE_ELEMENTS" -eq 0 ]; then
    echo "❌ Classic pipeline should have OCR elements"
    VALIDATION_PASSED=false
fi

# Final result
if [ "$VALIDATION_PASSED" = true ]; then
    echo "✅ Smoke test PASSED"
    echo "🎉 All validations successful!"
    exit 0
else
    echo "❌ Smoke test FAILED"
    echo "🔍 Check the validation errors above"
    exit 1
fi