"""
Pytest configuration and shared fixtures for Slide Speaker tests
"""
import pytest
import pytest_asyncio
import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock

# Set test environment
os.environ["TESTING"] = "true"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_slidespeaker"

# Import app after setting env vars
from app.core.config import settings
from app.core.database import Base, engine, get_db
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


# ============================================================================
# Session-scoped fixtures (created once per test session)
# ============================================================================

@pytest.fixture(scope="function")
def event_loop():
    """Create event loop for async tests"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    # Use in-memory SQLite for fast tests
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


# ============================================================================
# Function-scoped fixtures (created for each test)
# ============================================================================

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create clean database session for each test"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_data_dir() -> Path:
    """Get test data directory"""
    return Path(__file__).parent / "tests" / "data"


@pytest.fixture
def sample_pptx(test_data_dir: Path) -> Path:
    """Get sample PPTX file for testing"""
    # Create a minimal PPTX if it doesn't exist
    sample_file = test_data_dir / "sample.pptx"
    if not sample_file.exists():
        test_data_dir.mkdir(exist_ok=True, parents=True)
        # Create minimal PPTX (you can replace with real file)
        sample_file.write_bytes(b"PK\x03\x04")  # Placeholder
    return sample_file


@pytest.fixture
def sample_png(temp_dir: Path) -> Path:
    """Create sample PNG for testing"""
    from PIL import Image
    
    png_path = temp_dir / "test_slide.png"
    img = Image.new('RGB', (1920, 1080), color='white')
    img.save(png_path)
    return png_path


# ============================================================================
# Mock fixtures for external services
# ============================================================================

@pytest.fixture
def mock_ocr_provider():
    """Mock OCR provider"""
    mock = Mock()
    mock.extract_elements_from_pages.return_value = [
        [
            {
                "id": "element_1",
                "type": "heading",
                "text": "Test Heading",
                "bbox": [100, 50, 800, 120],
                "confidence": 0.95
            },
            {
                "id": "element_2",
                "type": "paragraph",
                "text": "Test paragraph content",
                "bbox": [100, 150, 800, 200],
                "confidence": 0.92
            }
        ]
    ]
    return mock


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider"""
    mock = AsyncMock()
    mock.generate_speaker_notes.return_value = {
        "talk_track": [
            {
                "segment": "introduction",
                "text": "Welcome to this test presentation",
                "group_id": "group_1",
            }
        ],
        "speaker_notes": "This is a test slide about testing",
        "estimated_duration": 45
    }
    return mock


@pytest.fixture
def mock_tts_provider():
    """Mock TTS provider"""
    mock = AsyncMock()
    
    # Create mock audio file
    import wave
    import struct
    
    def create_mock_audio():
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            # 1 second of silence
            samples = [0] * 22050
            wav_file.writeframes(struct.pack(f'{len(samples)}h', *samples))
        return temp_file.name
    
    audio_path = create_mock_audio()
    
    mock.synthesize.return_value = (
        audio_path,
        {
            "sentences": [
                {"text": "Test sentence", "t0": 0.0, "t1": 2.5}
            ],
            "word_timings": [
                {"mark_name": "w0", "time_seconds": 0.0},
                {"mark_name": "w1", "time_seconds": 0.5},
            ]
        }
    )
    
    yield mock
    
    # Cleanup
    if os.path.exists(audio_path):
        os.unlink(audio_path)


@pytest.fixture
def mock_storage_provider():
    """Mock storage provider"""
    mock = Mock()
    mock.upload_file.return_value = "https://storage.example.com/test/file.mp4"
    mock.upload_bytes.return_value = "https://storage.example.com/test/image.png"
    mock.get_download_url.return_value = "https://storage.example.com/test/file.mp4?signed=true"
    return mock


# ============================================================================
# Test user fixtures
# ============================================================================

@pytest.fixture
def test_user() -> dict:
    """Create test user data"""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "role": "user",
        "is_active": True,
    }


@pytest.fixture
def test_admin_user() -> dict:
    """Create test admin user data"""
    return {
        "user_id": "admin-user-123",
        "email": "admin@example.com",
        "role": "admin",
        "is_active": True,
    }


# ============================================================================
# Sample data fixtures
# ============================================================================

@pytest.fixture
def sample_manifest() -> dict:
    """Create sample lesson manifest"""
    return {
        "slides": [
            {
                "id": 1,
                "image": "/assets/test-lesson/slides/001.png",
                "audio": "/assets/test-lesson/audio/001.wav",
                "duration": 10.5,
                "elements": [
                    {
                        "id": "elem_1",
                        "type": "heading",
                        "text": "Introduction",
                        "bbox": [100, 50, 800, 120],
                        "confidence": 0.95
                    }
                ],
                "cues": [
                    {
                        "cue_id": "cue_1",
                        "t0": 0.5,
                        "t1": 2.0,
                        "action": "highlight",
                        "bbox": [100, 50, 800, 120],
                        "element_id": "elem_1"
                    }
                ],
                "speaker_notes": "Welcome to the presentation"
            },
            {
                "id": 2,
                "image": "/assets/test-lesson/slides/002.png",
                "audio": "/assets/test-lesson/audio/002.wav",
                "duration": 15.0,
                "elements": [
                    {
                        "id": "elem_2",
                        "type": "paragraph",
                        "text": "Main content",
                        "bbox": [100, 150, 800, 400],
                        "confidence": 0.92
                    }
                ],
                "cues": [],
                "speaker_notes": "This is the main content slide"
            }
        ],
        "timeline": {
            "rules": [],
            "default_duration": 10.0,
            "smoothness_enabled": True
        },
        "metadata": {
            "source_file": "test.pptx",
            "total_slides": 2,
            "stage": "completed"
        }
    }


@pytest.fixture
def sample_elements() -> list:
    """Create sample slide elements"""
    return [
        {
            "id": "elem_1",
            "type": "heading",
            "text": "Test Heading",
            "bbox": [100, 50, 800, 120],
            "confidence": 0.95
        },
        {
            "id": "elem_2",
            "type": "paragraph",
            "text": "Test paragraph with some content",
            "bbox": [100, 150, 800, 300],
            "confidence": 0.92
        },
        {
            "id": "elem_3",
            "type": "image",
            "text": "",
            "bbox": [100, 350, 500, 600],
            "confidence": 1.0
        }
    ]


# ============================================================================
# API client fixtures
# ============================================================================

@pytest_asyncio.fixture
async def test_client() -> AsyncGenerator:
    """Create test HTTP client for API testing"""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================================
# Environment cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Cleanup temporary files after each test"""
    yield
    
    # Cleanup any temp files
    import glob
    for pattern in ["/tmp/mock_*.wav", "/tmp/test_*.png", "/tmp/lesson_*"]:
        for file in glob.glob(pattern):
            try:
                os.unlink(file)
            except:
                pass


# ============================================================================
# Database fixtures
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock AsyncSession for database tests"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    return session


# ============================================================================
# Pytest hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")


def pytest_collection_modifyitems(config, items):
    """Modify collected tests"""
    # Add markers based on test path
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
