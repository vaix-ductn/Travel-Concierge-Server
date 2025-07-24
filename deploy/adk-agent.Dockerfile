# =============================================================================
# ADK Agent Server Dockerfile for Google Cloud Run
# Separate service for ADK Agent functionality
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
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies including ADK
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install --no-cache-dir google-adk

# Copy ADK agent code
COPY travel_concierge/ ./travel_concierge/
COPY requirements.txt ./

# Create logs directory
RUN mkdir -p logs

# Expose ADK server port
EXPOSE 8000

# Health check for ADK server
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Start ADK Agent server
CMD ["adk", "api_server", "travel_concierge", "--host", "0.0.0.0", "--port", "8000"]