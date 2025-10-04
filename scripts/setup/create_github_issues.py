#!/usr/bin/env python3
"""
Script to create GitHub Issues for Slide Speaker roadmap
Run this script to generate issues for the 3-sprint roadmap
"""

import json
from datetime import datetime, timedelta

def create_issues():
    """Create GitHub Issues for the roadmap"""
    
    issues = []
    
    # Epic: Sprint 1 - Document Parsing
    sprint1_epic = {
        "title": "🎯 Epic: Sprint 1 - Real Document Parsing (PPTX/PDF → PNG + bbox + manifest.json)",
        "body": """## Overview
Replace mock data with real document parsing capabilities for PPTX and PDF files.

## Goals
- Extract slides/pages as high-quality PNG images
- Detect text elements and their bounding boxes
- Generate structured manifest.json files
- Optimize images without quality loss
- Validate uploaded files

## Acceptance Criteria
- [ ] PPTX files are parsed and converted to PNG slides
- [ ] PDF files are parsed and converted to PNG pages  
- [ ] Text elements are detected with accurate bounding boxes
- [ ] Manifest.json is generated with slide metadata
- [ ] Images are optimized for web delivery
- [ ] File validation prevents corrupted uploads

## Technical Requirements
- Use python-pptx for PPTX parsing
- Use PyMuPDF/pdf2image for PDF parsing
- Implement OCR (Tesseract/EasyOCR) for text detection
- Create efficient image processing pipeline
- Add comprehensive error handling

## Estimated Effort: 2-3 weeks
""",
        "labels": ["epic", "sprint-1", "document-parsing", "high-priority"],
        "milestone": "Sprint 1: Document Parsing"
    }
    
    # Sprint 1 Issues
    sprint1_issues = [
        {
            "title": "📄 Implement PPTX parsing with slide extraction",
            "body": """## Description
Implement PPTX file parsing to extract individual slides as PNG images.

## Tasks
- [ ] Install and configure python-pptx library
- [ ] Create PPTXParser class in document_parser.py
- [ ] Implement slide extraction to PNG conversion
- [ ] Handle different slide layouts and content types
- [ ] Add error handling for corrupted PPTX files
- [ ] Write unit tests for PPTX parsing

## Acceptance Criteria
- PPTX files are successfully parsed
- Each slide is converted to high-quality PNG
- Slides are saved to organized directory structure
- Error handling for invalid PPTX files

## Estimated Effort: 1 week
""",
            "labels": ["sprint-1", "pptx", "parsing", "medium-priority"]
        },
        {
            "title": "📑 Implement PDF parsing with page extraction", 
            "body": """## Description
Implement PDF file parsing to extract pages as PNG images.

## Tasks
- [ ] Install and configure PyMuPDF/pdf2image libraries
- [ ] Create PDFParser class in document_parser.py
- [ ] Implement page extraction to PNG conversion
- [ ] Handle different PDF formats and layouts
- [ ] Add error handling for corrupted PDF files
- [ ] Write unit tests for PDF parsing

## Acceptance Criteria
- PDF files are successfully parsed
- Each page is converted to high-quality PNG
- Pages are saved to organized directory structure
- Error handling for invalid PDF files

## Estimated Effort: 1 week
""",
            "labels": ["sprint-1", "pdf", "parsing", "medium-priority"]
        },
        {
            "title": "🔍 Implement OCR text detection with bounding boxes",
            "body": """## Description
Implement OCR-based text detection to identify text elements and their coordinates.

## Tasks
- [ ] Install and configure Tesseract/EasyOCR
- [ ] Implement text detection algorithm
- [ ] Extract bounding boxes for text elements
- [ ] Handle different fonts and text sizes
- [ ] Optimize OCR accuracy and performance
- [ ] Write unit tests for text detection

## Acceptance Criteria
- Text elements are accurately detected
- Bounding boxes are precise and consistent
- OCR works with various text styles
- Performance is acceptable for large documents

## Estimated Effort: 1 week
""",
            "labels": ["sprint-1", "ocr", "text-detection", "medium-priority"]
        },
        {
            "title": "📋 Generate structured manifest.json files",
            "body": """## Description
Create structured manifest.json files with slide metadata and element information.

## Tasks
- [ ] Define manifest.json schema
- [ ] Implement manifest generation logic
- [ ] Include slide images, audio placeholders, and cues
- [ ] Add metadata (source file, parser type, etc.)
- [ ] Validate manifest structure
- [ ] Write unit tests for manifest generation

## Acceptance Criteria
- Manifest.json is properly structured
- All slide information is included
- Metadata is accurate and complete
- Schema validation passes

## Estimated Effort: 3 days
""",
            "labels": ["sprint-1", "manifest", "json", "low-priority"]
        }
    ]
    
    # Epic: Sprint 2 - AI Generation
    sprint2_epic = {
        "title": "🤖 Epic: Sprint 2 - AI Speaker Notes + TTS with Timing Synchronization",
        "body": """## Overview
Add AI-powered speaker notes generation and text-to-speech with visual effect synchronization.

## Goals
- Generate contextual speaker notes using LLM
- Convert text to high-quality speech
- Synchronize audio with visual effects
- Provide editing interface for generated content
- Support multiple TTS voices and settings

## Acceptance Criteria
- [ ] LLM generates relevant speaker notes for each slide
- [ ] TTS produces high-quality audio
- [ ] Visual effects are synchronized with audio timing
- [ ] Users can edit generated content
- [ ] Multiple voice options are available
- [ ] Preview functionality works correctly

## Technical Requirements
- Integrate OpenAI/Anthropic APIs
- Implement TTS (OpenAI/ElevenLabs/Azure)
- Create timing synchronization system
- Build content editing interface
- Add preview and validation features

## Estimated Effort: 3-4 weeks
""",
        "labels": ["epic", "sprint-2", "ai-generation", "tts", "high-priority"],
        "milestone": "Sprint 2: AI Generation"
    }
    
    # Sprint 2 Issues
    sprint2_issues = [
        {
            "title": "🧠 Integrate LLM for speaker notes generation",
            "body": """## Description
Integrate Large Language Model (OpenAI/Anthropic) to generate contextual speaker notes.

## Tasks
- [ ] Set up OpenAI/Anthropic API integration
- [ ] Create AIGenerator service class
- [ ] Implement speaker notes generation logic
- [ ] Add custom prompt support
- [ ] Handle API rate limiting and errors
- [ ] Write unit tests for LLM integration

## Acceptance Criteria
- LLM generates relevant speaker notes
- Custom prompts are supported
- Error handling for API failures
- Rate limiting is properly managed

## Estimated Effort: 1 week
""",
            "labels": ["sprint-2", "llm", "speaker-notes", "medium-priority"]
        },
        {
            "title": "🎤 Implement TTS with multiple voice options",
            "body": """## Description
Implement text-to-speech conversion with multiple voice options and quality settings.

## Tasks
- [ ] Integrate TTS service (OpenAI/ElevenLabs/Azure)
- [ ] Create TTSService class
- [ ] Implement voice selection and settings
- [ ] Add audio quality optimization
- [ ] Handle TTS API errors and retries
- [ ] Write unit tests for TTS functionality

## Acceptance Criteria
- High-quality audio generation
- Multiple voice options available
- Configurable speed and tone
- Robust error handling

## Estimated Effort: 1 week
""",
            "labels": ["sprint-2", "tts", "audio", "medium-priority"]
        },
        {
            "title": "⏱️ Implement timing synchronization system",
            "body": """## Description
Create system to synchronize visual effects with audio timing.

## Tasks
- [ ] Analyze audio duration and timing
- [ ] Generate visual cue timestamps
- [ ] Implement timing validation
- [ ] Create synchronization algorithm
- [ ] Add timing adjustment features
- [ ] Write unit tests for timing system

## Acceptance Criteria
- Visual effects are properly timed
- Timing validation prevents errors
- Users can adjust timing manually
- Synchronization is accurate

## Estimated Effort: 1 week
""",
            "labels": ["sprint-2", "timing", "synchronization", "medium-priority"]
        },
        {
            "title": "✏️ Build content editing interface",
            "body": """## Description
Create interface for editing generated speaker notes and audio timing.

## Tasks
- [ ] Design editing UI components
- [ ] Implement speaker notes editor
- [ ] Add audio timing adjustment controls
- [ ] Create preview functionality
- [ ] Implement save/undo features
- [ ] Write unit tests for editing features

## Acceptance Criteria
- Users can edit speaker notes
- Audio timing can be adjusted
- Preview shows changes immediately
- Changes are saved properly

## Estimated Effort: 1 week
""",
            "labels": ["sprint-2", "ui", "editing", "medium-priority"]
        }
    ]
    
    # Epic: Sprint 3 - Export and Production
    sprint3_epic = {
        "title": "🎬 Epic: Sprint 3 - Video Export + Production Stability",
        "body": """## Overview
Implement final video export to MP4 and create production-ready system with queues and monitoring.

## Goals
- Export lessons to high-quality MP4 videos
- Implement background task processing
- Add reliable file storage and management
- Create monitoring and logging system
- Optimize performance for large presentations
- Add comprehensive testing

## Acceptance Criteria
- [ ] MP4 videos are exported with visual effects
- [ ] Background processing handles long operations
- [ ] File storage is reliable and scalable
- [ ] System monitoring and logging work
- [ ] Performance is optimized
- [ ] Comprehensive test coverage exists

## Technical Requirements
- FFmpeg integration for video export
- Celery/Redis for task queues
- Robust file storage system
- Monitoring and alerting
- Performance optimization
- Unit and integration tests

## Estimated Effort: 2-3 weeks
""",
        "labels": ["epic", "sprint-3", "video-export", "production", "high-priority"],
        "milestone": "Sprint 3: Production Ready"
    }
    
    # Sprint 3 Issues
    sprint3_issues = [
        {
            "title": "🎥 Implement MP4 video export with FFmpeg",
            "body": """## Description
Implement video export functionality using FFmpeg to create MP4 videos with visual effects.

## Tasks
- [ ] Integrate FFmpeg for video processing
- [ ] Create VideoExporter service class
- [ ] Implement slide-to-video conversion
- [ ] Add visual effects rendering
- [ ] Support different quality settings
- [ ] Write unit tests for video export

## Acceptance Criteria
- MP4 videos are successfully exported
- Visual effects are rendered correctly
- Multiple quality options available
- Export process is reliable

## Estimated Effort: 1 week
""",
            "labels": ["sprint-3", "video", "ffmpeg", "export", "medium-priority"]
        },
        {
            "title": "⚡ Implement background task processing with Celery",
            "body": """## Description
Implement background task processing using Celery and Redis for long-running operations.

## Tasks
- [ ] Set up Celery and Redis
- [ ] Create background task definitions
- [ ] Implement task status tracking
- [ ] Add task retry and error handling
- [ ] Create task monitoring interface
- [ ] Write unit tests for task processing

## Acceptance Criteria
- Long operations run in background
- Task status is trackable
- Error handling and retries work
- Monitoring interface is functional

## Estimated Effort: 1 week
""",
            "labels": ["sprint-3", "celery", "redis", "background-tasks", "medium-priority"]
        },
        {
            "title": "💾 Implement reliable file storage and management",
            "body": """## Description
Create robust file storage system with cleanup, monitoring, and backup capabilities.

## Tasks
- [ ] Design file storage architecture
- [ ] Implement file cleanup system
- [ ] Add storage monitoring and statistics
- [ ] Create backup and recovery features
- [ ] Add file validation and integrity checks
- [ ] Write unit tests for storage system

## Acceptance Criteria
- File storage is reliable and scalable
- Cleanup prevents storage bloat
- Monitoring provides useful insights
- Backup system works correctly

## Estimated Effort: 1 week
""",
            "labels": ["sprint-3", "storage", "file-management", "medium-priority"]
        },
        {
            "title": "📊 Add monitoring, logging, and performance optimization",
            "body": """## Description
Implement comprehensive monitoring, logging, and performance optimization for production use.

## Tasks
- [ ] Set up application logging
- [ ] Implement performance monitoring
- [ ] Add error tracking and alerting
- [ ] Optimize database queries and file operations
- [ ] Create health check endpoints
- [ ] Write performance tests

## Acceptance Criteria
- Comprehensive logging is in place
- Performance monitoring works
- Error tracking and alerts function
- System performance is optimized

## Estimated Effort: 1 week
""",
            "labels": ["sprint-3", "monitoring", "logging", "performance", "medium-priority"]
        },
        {
            "title": "🧪 Add comprehensive testing suite",
            "body": """## Description
Create comprehensive test suite with unit tests, integration tests, and end-to-end tests.

## Tasks
- [ ] Write unit tests for all services
- [ ] Create integration tests for API endpoints
- [ ] Add end-to-end tests for user workflows
- [ ] Implement test data fixtures
- [ ] Set up CI/CD testing pipeline
- [ ] Add performance and load tests

## Acceptance Criteria
- High test coverage (>80%)
- All critical paths are tested
- CI/CD pipeline runs tests automatically
- Performance tests validate system limits

## Estimated Effort: 1 week
""",
            "labels": ["sprint-3", "testing", "ci-cd", "quality", "medium-priority"]
        }
    ]
    
    # Combine all issues
    all_issues = [
        sprint1_epic,
        *sprint1_issues,
        sprint2_epic, 
        *sprint2_issues,
        sprint3_epic,
        *sprint3_issues
    ]
    
    return all_issues

def save_issues_to_file():
    """Save issues to JSON file for manual GitHub import"""
    issues = create_issues()
    
    output = {
        "issues": issues,
        "created_at": datetime.now().isoformat(),
        "total_count": len(issues)
    }
    
    with open("github_issues.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Created {len(issues)} GitHub issues")
    print("Issues saved to github_issues.json")
    print("\nTo create these issues on GitHub:")
    print("1. Go to your repository on GitHub")
    print("2. Click 'Issues' tab")
    print("3. Click 'New issue'")
    print("4. Copy and paste the content from github_issues.json")
    print("5. Or use GitHub CLI: gh issue create --title 'Title' --body 'Body'")

if __name__ == "__main__":
    save_issues_to_file()