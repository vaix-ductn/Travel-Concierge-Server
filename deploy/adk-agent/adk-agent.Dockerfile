# =============================================================================
# ADK Agent Server Dockerfile for Google Cloud Run
# Separate service for ADK Agent functionality with Web UI
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

# Copy requirements and environment file
COPY requirements.txt ./
COPY .env.copy ./.env

# Install Python dependencies including google-adk
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install google-adk

# Copy ADK Agent code
COPY travel_concierge/__init__.py ./travel_concierge/
COPY travel_concierge/agent.py ./travel_concierge/
COPY travel_concierge/prompt.py ./travel_concierge/
COPY travel_concierge/sub_agents/ ./travel_concierge/sub_agents/
COPY travel_concierge/tools/ ./travel_concierge/tools/
COPY travel_concierge/shared_libraries/ ./travel_concierge/shared_libraries/
COPY travel_concierge/profiles/ ./travel_concierge/profiles/

# Create logs directory
RUN mkdir -p logs

# Expose ADK Web UI port
EXPOSE 8002

# Health check for ADK Web UI server
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/ || exit 1

# Start ADK Web UI server (interactive chat interface)
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8002"]