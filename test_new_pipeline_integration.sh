#!/bin/bash
# Integration test for NEW pipeline through API

echo "🧪 Testing NEW Pipeline Integration"
echo "=================================="
echo ""

# Check if test file exists
if [ ! -f "test_real.pptx" ]; then
    echo "❌ test_real.pptx not found!"
    exit 1
fi

echo "✅ Test file found: test_real.pptx"
echo ""

# Set environment variable for new pipeline
export USE_NEW_PIPELINE=true
echo "✅ USE_NEW_PIPELINE=true"
echo ""

# Start services (if not running)
echo "Starting services..."
docker-compose up -d redis postgres 2>&1 | grep -E "(Starting|Started|Creating|Created)" || echo "Services already running"
sleep 2
echo ""

# Run backend server in background
echo "Starting backend server..."
cd backend && python3 -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 5
echo ""

# Test upload endpoint
echo "🚀 Uploading test file..."
curl -X POST "http://localhost:8000/upload" \
  -F "file=@../test_real.pptx" \
  -v 2>&1 | tee /tmp/upload_response.txt

echo ""
echo ""

# Extract lesson_id from response
LESSON_ID=$(grep -o '"lesson_id":"[^"]*"' /tmp/upload_response.txt | cut -d'"' -f4)

if [ -z "$LESSON_ID" ]; then
    echo "❌ Failed to get lesson_id from response"
    kill $BACKEND_PID
    exit 1
fi

echo "✅ Lesson ID: $LESSON_ID"
echo ""

# Wait for processing
echo "⏳ Waiting for processing to start..."
sleep 5

# Check manifest
MANIFEST_PATH=".data/$LESSON_ID/manifest.json"
echo "📁 Checking manifest: $MANIFEST_PATH"

if [ -f "$MANIFEST_PATH" ]; then
    echo "✅ Manifest exists!"
    echo ""
    echo "Manifest content:"
    cat "$MANIFEST_PATH" | python3 -m json.tool | head -40
else
    echo "❌ Manifest not found (this is expected - created by Celery task)"
fi

echo ""
echo "📊 Checking slides directory..."
SLIDES_DIR=".data/$LESSON_ID/slides"
if [ -d "$SLIDES_DIR" ]; then
    echo "✅ Slides directory exists!"
    ls -lh "$SLIDES_DIR"
else
    echo "❌ Slides directory not found yet"
fi

echo ""
echo "=================================="
echo "Test completed!"
echo "Lesson directory: .data/$LESSON_ID"
echo ""
echo "Stopping backend server..."
kill $BACKEND_PID

echo "Done! ✅"
