FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for document processing and monitoring
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    ffmpeg \
    poppler-utils \
    libreoffice \
    libreoffice-writer \
    libreoffice-impress \
    libreoffice-draw \
    fonts-liberation \
    libmagic1 \
    libmagic-dev \
    curl \
    netcat-openbsd \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY workers/ ./workers/
COPY storage_gcs.py .
COPY alembic.ini .
COPY alembic/ ./alembic/

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh

# Create directories for data, keys, and secrets
RUN mkdir -p .data/uploads .data/assets .data/exports /app/keys /app/secrets

# Set environment variables for multiprocess Prometheus
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc_dir

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /entrypoint.sh && \
    chown root:root /entrypoint.sh
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use entrypoint to ensure Prometheus directory exists
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]