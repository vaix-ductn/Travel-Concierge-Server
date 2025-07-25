# =============================================================================
# Voice Chat WebSocket Server Dockerfile for Google Cloud Run
# Separate service for Voice Chat functionality
# =============================================================================

FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    curl \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy voice chat code
COPY travel_concierge/voice_chat/ ./travel_concierge/voice_chat/
COPY travel_concierge/management/ ./travel_concierge/management/

# Create logs directory
RUN mkdir -p logs

# Expose voice chat server port and health check port
EXPOSE 8003 8080

# Health check for voice chat server
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health/ || exit 1

# Copy Django settings and base configuration
COPY base/ ./base/

# Copy production voice server startup script
COPY deploy/voice-chat/start_voice_server.py ./start_voice_server.py

# Start production voice server
CMD ["python", "start_voice_server.py"]