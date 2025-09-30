"""Application configuration"""
import os
from pathlib import Path
from typing import Optional

class Settings:
    """Application settings"""
    
    # API Configuration
    API_TITLE: str = "Slide Speaker API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080"
    ]
    
    # Data Storage
    DATA_DIR: Path = Path(".data")
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    ASSETS_DIR: Path = DATA_DIR / "assets"
    EXPORTS_DIR: Path = DATA_DIR / "exports"
    
    # File Processing
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: list = ['.pptx', '.pdf']
    
    # Google Cloud Services
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    GCP_PROJECT_ID: Optional[str] = os.getenv("GCP_PROJECT_ID")
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
    
    # Provider Configuration
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "easyocr")  # google|easyocr|paddle
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # gemini|openai|openrouter|ollama|anthropic
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "mock")  # google|azure|mock
    STORAGE: str = os.getenv("STORAGE", "minio")  # gcs|minio
    
    # Google Cloud Document AI
    GCP_DOC_AI_PROCESSOR_ID: Optional[str] = os.getenv("GCP_DOC_AI_PROCESSOR_ID")
    OCR_BATCH_SIZE: int = int(os.getenv("OCR_BATCH_SIZE", "10"))
    
    # Google Cloud Gemini
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_LOCATION: str = os.getenv("GEMINI_LOCATION", "us-central1")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    
    # Google Cloud TTS
    GOOGLE_TTS_VOICE: str = os.getenv("GOOGLE_TTS_VOICE", "ru-RU-Neural2-B")
    GOOGLE_TTS_SPEAKING_RATE: float = float(os.getenv("GOOGLE_TTS_SPEAKING_RATE", "1.0"))
    GOOGLE_TTS_PITCH: float = float(os.getenv("GOOGLE_TTS_PITCH", "0.0"))
    
    # Google Cloud Storage
    GCS_BUCKET: Optional[str] = os.getenv("GCS_BUCKET")
    GCS_BASE_URL: Optional[str] = os.getenv("GCS_BASE_URL")
    
    # Legacy AI Services (Sprint 2)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    TTS_SERVICE: str = os.getenv("TTS_SERVICE", "openai")  # openai, elevenlabs, azure
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "x-ai/grok-4-fast:free")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Azure TTS (Legacy)
    AZURE_TTS_KEY: Optional[str] = os.getenv("AZURE_TTS_KEY")
    AZURE_TTS_REGION: Optional[str] = os.getenv("AZURE_TTS_REGION")
    TTS_VOICE: str = os.getenv("TTS_VOICE", "ru-RU-SvetlanaNeural")
    TTS_SPEED: float = float(os.getenv("TTS_SPEED", "1.0"))
    
    # Queue Configuration (Sprint 3)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Video Export (Sprint 3)
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    VIDEO_QUALITY: str = "high"  # low, medium, high
    
    # S3 Storage (Sprint 3)
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET: Optional[str] = os.getenv("S3_BUCKET")
    S3_ENDPOINT_URL: Optional[str] = os.getenv("S3_ENDPOINT_URL")  # For MinIO or other S3-compatible services
    
    # Export Settings
    MAX_EXPORT_SIZE_MB: int = int(os.getenv("MAX_EXPORT_SIZE_MB", "500"))  # 500MB max
    EXPORT_RETRY_ATTEMPTS: int = int(os.getenv("EXPORT_RETRY_ATTEMPTS", "3"))
    EXPORT_TIMEOUT_SECONDS: int = int(os.getenv("EXPORT_TIMEOUT_SECONDS", "1800"))  # 30 minutes
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    # Metrics Configuration
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "8000"))
    
    def __init__(self):
        """Initialize directories"""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.ASSETS_DIR.mkdir(exist_ok=True)
        self.EXPORTS_DIR.mkdir(exist_ok=True)

settings = Settings()