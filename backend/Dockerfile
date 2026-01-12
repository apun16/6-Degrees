FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (CPU-only torch)
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformers model during build
# This bakes the model into the image so it's instant on startup
ENV TRANSFORMERS_CACHE=/app/models
ENV HF_HOME=/app/models
ENV HF_DATASETS_CACHE=/app/models
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Railway provides PORT environment variable dynamically
# Use PORT from environment, default to 5001 for local dev
ENV PORT=5001

# Run the application with increased timeout and single worker
# Railway sets PORT automatically, so use $PORT
CMD gunicorn run:app --bind 0.0.0.0:${PORT:-5001} --timeout 300 --workers 1 --worker-class sync --preload
