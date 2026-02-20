FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libportaudio2 \
    ffmpeg \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements/*.txt requirements/
RUN pip install --no-cache-dir -r requirements/base.txt \
    && pip install --no-cache-dir -r requirements/rag.txt \
    && pip install --no-cache-dir -r requirements/emotion.txt \
    && pip install --no-cache-dir -r requirements/voice.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
