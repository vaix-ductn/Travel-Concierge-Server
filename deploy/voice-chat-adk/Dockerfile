# Dockerfile for WebSocket ADK Bridge Server
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    libasound-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY websocket_adk_bridge.py .
COPY start_bridge_server.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_CLOUD_PROJECT=sascha-playground-doit
ENV GOOGLE_CLOUD_LOCATION=us-central1

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', 8003)); s.close()" || exit 1

# Run the server
CMD ["python", "start_bridge_server.py"]