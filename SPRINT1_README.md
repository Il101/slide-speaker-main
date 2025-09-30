# Sprint 1: Document Processing and Real Slide Display

## Overview

Sprint 1 реализует базовую функциональность для загрузки и обработки презентаций (PDF/PPTX) с автоматическим извлечением слайдов, детекцией элементов и генерацией визуальных эффектов.

## Features

### Backend (Document Processing)

- **PDF Parsing**: Использует PyMuPDF для извлечения страниц как PNG изображений
- **PPTX Parsing**: Использует python-pptx для извлечения слайдов и конверсии в PNG
- **OCR Detection**: EasyOCR для автоматического обнаружения текстовых элементов
- **Element Detection**: Автоматическое определение bounding boxes для текста
- **Timeline Generation**: Автоматическая генерация правил для визуальных эффектов

### Frontend (Player)

- **Real Slide Display**: Отображение настоящих слайдов вместо mock данных
- **Visual Effects**: Поддержка highlight, underline и laser_move эффектов
- **Multi-slide Support**: Навигация между несколькими слайдами
- **Timeline Sync**: Синхронизация эффектов с временной шкалой

## API Endpoints

### POST /upload
Загружает и обрабатывает документ (PDF/PPTX).

**Request:**
```bash
curl -X POST "http://localhost:8001/upload" \
  -F "file=@presentation.pdf"
```

**Response:**
```json
{
  "lesson_id": "uuid-string",
  "status": "completed"
}
```

### GET /lessons/{lesson_id}/manifest
Получает manifest с данными о слайдах и эффектах.

**Response:**
```json
{
  "slides": [...],
  "timeline": {...},
  "metadata": {...}
}
```

## Manifest Structure

### Example manifest.json

```json
{
  "slides": [
    {
      "id": 1,
      "image": "/assets/lesson-uuid/slides/001.png",
      "audio": "/assets/lesson-uuid/audio/001.mp3",
      "elements": [
        {
          "id": "element_abc123",
          "type": "text",
          "bbox": [120, 80, 980, 150],
          "text": "Welcome to Slide Speaker",
          "confidence": 0.95
        },
        {
          "id": "element_def456",
          "type": "text",
          "bbox": [140, 220, 860, 260],
          "text": "AI-powered presentation converter",
          "confidence": 0.92
        }
      ],
      "cues": [
        {
          "t0": 0.5,
          "t1": 2.5,
          "action": "highlight",
          "bbox": [120, 80, 980, 150],
          "element_id": "element_abc123"
        },
        {
          "t0": 1.0,
          "t1": 3.0,
          "action": "underline",
          "bbox": [140, 220, 860, 4],
          "element_id": "element_def456"
        },
        {
          "t0": 2.5,
          "t1": 3.0,
          "action": "laser_move",
          "to": [900, 520]
        }
      ]
    }
  ],
  "timeline": {
    "rules": [
      {
        "type": "highlight",
        "duration": 2.0,
        "priority": 1
      },
      {
        "type": "underline",
        "duration": 1.5,
        "priority": 2
      },
      {
        "type": "laser_move",
        "duration": 0.5,
        "priority": 3
      }
    ],
    "default_duration": 2.0,
    "transition_duration": 0.5
  },
  "metadata": {
    "source_file": "/path/to/presentation.pdf",
    "parser": "pdf",
    "total_slides": 1
  }
}
```

### Schema Definitions

#### SlideElement
```json
{
  "id": "string",           // Unique element identifier
  "type": "string",          // Element type (text, image, shape)
  "bbox": [x, y, w, h],     // Bounding box coordinates
  "text": "string",          // Text content (optional)
  "confidence": 0.95         // Detection confidence (0-1)
}
```

#### Cue (Visual Effect)
```json
{
  "t0": 0.5,                // Start time in seconds
  "t1": 2.5,                // End time in seconds
  "action": "highlight",     // Effect type: highlight, underline, laser_move
  "bbox": [x, y, w, h],     // Bounding box (for highlight/underline)
  "to": [x, y],             // Target position (for laser_move)
  "element_id": "string"     // Reference to slide element (optional)
}
```

#### Timeline Rules
```json
{
  "rules": [
    {
      "type": "highlight",
      "duration": 2.0,
      "priority": 1
    }
  ],
  "default_duration": 2.0,
  "transition_duration": 0.5
}
```

## Visual Effects

### Highlight
- **Purpose**: Выделение текстовых блоков
- **Visual**: Полупрозрачный желтый фон с рамкой
- **Timing**: Обычно 2 секунды
- **Usage**: `{"action": "highlight", "bbox": [x, y, w, h]}`

### Underline
- **Purpose**: Подчеркивание текста
- **Visual**: Красная линия под текстом
- **Timing**: Обычно 1.5 секунды
- **Usage**: `{"action": "underline", "bbox": [x, y, w, 4]}`

### Laser Move
- **Purpose**: Перемещение лазерной указки
- **Visual**: Красная точка с анимацией пульсации
- **Timing**: Обычно 0.5 секунды
- **Usage**: `{"action": "laser_move", "to": [x, y]}`

## File Structure

```
/data/
  {lesson_id}/
    slides/
      001.png
      002.png
      003.png
    audio/
      001.mp3
      002.mp3
      003.mp3
    manifest.json
    original_file.pdf
```

## Dependencies

### Backend
- `PyMuPDF` - PDF processing
- `python-pptx` - PowerPoint processing
- `EasyOCR` - Text detection
- `OpenCV` - Image processing
- `Pillow` - Image manipulation

### Frontend
- React with TypeScript
- Tailwind CSS for styling
- Lucide React for icons

## Usage Example

1. **Upload Document**:
   ```bash
   curl -X POST "http://localhost:8001/upload" \
     -F "file=@my_presentation.pdf"
   ```

2. **Get Manifest**:
   ```bash
   curl "http://localhost:8001/lessons/{lesson_id}/manifest"
   ```

3. **View in Player**:
   - Open frontend application
   - Enter lesson_id in the player
   - Watch slides with automatic visual effects

## Demo

Для тестирования используйте demo lesson:
- Lesson ID: `demo-lesson`
- URL: `http://localhost:8001/lessons/demo-lesson/manifest`

## Next Steps (Sprint 2)

- AI-generated speaker notes
- Text-to-speech audio generation
- Content editing capabilities
- Advanced timeline customization