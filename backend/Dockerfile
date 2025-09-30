FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    ffmpeg \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app/ ./app/
COPY workers/ ./workers/
COPY storage_gcs.py .
COPY main.py .

# Создаем директории для данных и ключей
RUN mkdir -p .data/uploads .data/assets .data/exports /app/keys

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]