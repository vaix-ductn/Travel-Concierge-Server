#!/usr/bin/env python3
"""
Production Voice Chat Server Startup Script for Google Cloud Run
Starts the actual WebSocket server with Django integration
"""
import os
import sys
import asyncio
import logging
import signal
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import threading

# Add the app directory to Python path
sys.path.insert(0, '/app')

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')

def setup_django():
    """Setup Django environment"""
    django.setup()

def setup_logging():
    """Setup logging for production"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# Create FastAPI app for health checks
health_app = FastAPI(title="Voice Chat Health Check")

@health_app.get("/")
async def root():
    return {"message": "Voice Chat Server is running!", "status": "healthy"}

@health_app.get("/health/")
async def health():
    return {"status": "healthy", "service": "voice-chat-server"}

def start_health_server():
    """Start health check HTTP server in separate thread"""
    uvicorn.run(health_app, host="0.0.0.0", port=8080, log_level="warning")

async def start_voice_server():
    """Start the voice WebSocket server"""
    logger = logging.getLogger(__name__)
    
    try:
        # Import after Django setup
        from travel_concierge.voice_chat.websocket_server import voice_websocket_server
        
        # Configure server for Cloud Run
        port = int(os.environ.get('PORT', 8003))
        voice_websocket_server.host = "0.0.0.0"  # Bind all interfaces for Cloud Run
        voice_websocket_server.port = port
        
        logger.info(f"🚀 Starting Voice Chat WebSocket Server on {voice_websocket_server.host}:{port}")
        
        # Start the server
        await voice_websocket_server.start_server()
        
        logger.info("✅ Voice Chat WebSocket Server is running!")
        logger.info(f"🔗 WebSocket URL: ws://{voice_websocket_server.host}:{port}")
        
        # Keep server running
        while voice_websocket_server.is_running:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"❌ Failed to start voice server: {str(e)}")
        raise

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger = logging.getLogger(__name__)
    logger.info(f"🛑 Received signal {signum}, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Setup environment
    setup_logging()
    setup_django()
    
    logger = logging.getLogger(__name__)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start health check server in background thread
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        logger.info("✅ Health check server started on port 8080")
        
        # Start the voice server
        asyncio.run(start_voice_server())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {str(e)}")
        sys.exit(1)