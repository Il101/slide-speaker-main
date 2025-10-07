"""Application configuration with secrets management"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from .secrets import (
    get_database_url, get_redis_url, get_jwt_secret, get_openai_key,
    get_azure_tts_key, get_minio_credentials, get_cors_origins, get_grafana_password
)


def _load_env_files() -> None:
    """Load environment variables from known dotenv files if present."""
    project_root = Path(__file__).resolve().parent.parent.parent
    candidates = [
        project_root / ".env",
        project_root / "backend" / ".env",
        project_root / "docker.env",
    ]

    for env_file in candidates:
        if env_file.exists():
            load_dotenv(env_file, override=False)


_load_env_files()

class Settings:
    """Application settings"""
    
    # API Configuration
    API_TITLE: str = "Slide Speaker API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS Configuration
    CORS_ORIGINS: list = get_cors_origins().split(",") if get_cors_origins() else [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
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
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us")
    
    # Provider Configuration
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "google")  # google|vision|easyocr|paddle
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openrouter")  # gemini|openai|openrouter|ollama|anthropic
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "google")  # google|azure|mock
    STORAGE: str = os.getenv("STORAGE", "gcs")  # gcs|minio
    
    # Google Cloud Document AI
    GCP_DOC_AI_PROCESSOR_ID: Optional[str] = os.getenv("GCP_DOC_AI_PROCESSOR_ID")
    OCR_BATCH_SIZE: int = int(os.getenv("OCR_BATCH_SIZE", "10"))
    
    # Google Cloud Gemini
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_LOCATION: str = os.getenv("GEMINI_LOCATION", "us")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_LANGUAGE: str = os.getenv("LLM_LANGUAGE", "ru")
    
    # Google Cloud TTS
    GOOGLE_TTS_VOICE: str = os.getenv("GOOGLE_TTS_VOICE", "ru-RU-Wavenet-D")
    GOOGLE_TTS_SPEAKING_RATE: float = float(os.getenv("GOOGLE_TTS_SPEAKING_RATE", "1.0"))
    GOOGLE_TTS_PITCH: float = float(os.getenv("GOOGLE_TTS_PITCH", "0.0"))
    
    # Google Cloud Storage
    GCS_BUCKET: str = os.getenv("GCS_BUCKET", "slide-speaker-storage")
    GCS_BASE_URL: str = os.getenv("GCS_BASE_URL", "https://storage.googleapis.com/slide-speaker-storage")
    
    # Legacy AI Services (Sprint 2)
    OPENAI_API_KEY: Optional[str] = get_openai_key()
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    TTS_SERVICE: str = os.getenv("TTS_SERVICE", "openai")  # openai, elevenlabs, azure
    
    # Pipeline Configuration
    USE_NEW_PIPELINE: bool = os.getenv("USE_NEW_PIPELINE", "true").lower() in ("true", "1", "yes")  # Default: TRUE (new pipeline)
    PIPELINE_MAX_PARALLEL_SLIDES: int = int(os.getenv("PIPELINE_MAX_PARALLEL_SLIDES", "5"))
    PIPELINE_MAX_PARALLEL_TTS: int = int(os.getenv("PIPELINE_MAX_PARALLEL_TTS", "10"))
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-8b-instruct:free")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Azure TTS (Legacy)
    AZURE_TTS_KEY: Optional[str] = get_azure_tts_key()
    AZURE_TTS_REGION: Optional[str] = os.getenv("AZURE_TTS_REGION")
    TTS_VOICE: str = os.getenv("TTS_VOICE", "ru-RU-SvetlanaNeural")
    TTS_SPEED: float = float(os.getenv("TTS_SPEED", "1.0"))
    
    # Database Configuration
    DATABASE_URL: str = get_database_url()
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    
    # Queue Configuration (Sprint 3)
    REDIS_URL: Optional[str] = get_redis_url()
    CELERY_BROKER_URL: str = get_redis_url()
    CELERY_RESULT_BACKEND: str = get_redis_url()
    
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
    
    # Security Configuration
    JWT_SECRET_KEY: str = get_jwt_secret()
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    CSRF_SECRET_KEY: str = os.getenv("CSRF_SECRET_KEY", "your-csrf-secret-key-change-in-production")
    
    def __init__(self):
        """Initialize directories"""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.ASSETS_DIR.mkdir(exist_ok=True)
        self.EXPORTS_DIR.mkdir(exist_ok=True)

settings = Settings()