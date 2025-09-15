# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Build-time metadata (inject via --build-arg)
ARG COMMIT_SHA=unknown
ARG BUILD_VERSION=dev

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p output

# Expose port for Flask app
EXPOSE 5000

# Set environment variables (include build metadata for runtime visibility)
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONPATH=/app/src \
    APP_VERSION=${BUILD_VERSION} \
    GIT_COMMIT=${COMMIT_SHA}

# Run the Flask application with Gunicorn for production
CMD ["gunicorn", "--config", "config/gunicorn.conf.py", "app:app"]
