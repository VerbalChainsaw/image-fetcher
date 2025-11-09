# Multi-stage build for Video Fetcher Pro
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    ffprobe \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY templates/ ./templates/
COPY VIDEO_*.md ./

# Create directories
RUN mkdir -p video_collections logs cache

# Set permissions
RUN chmod +x video_fetcher_pro.py video_web_app_pro.py

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5001/health')"

# Default command (can be overridden)
CMD ["python3", "video_web_app_pro.py", "--host", "0.0.0.0", "--port", "5001"]
