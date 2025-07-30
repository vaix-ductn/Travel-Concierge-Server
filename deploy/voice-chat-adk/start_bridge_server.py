#!/usr/bin/env python3
"""
Startup script for WebSocket ADK Bridge Server
Handles production deployment with proper logging and error handling
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the travel_concierge directory to Python path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/travel_concierge')

try:
    from websocket_adk_bridge import WebSocketADKBridge
except ImportError:
    # Fallback for local development
    sys.path.insert(0, '../../travel_concierge/voice_chat')
    from websocket_adk_bridge import WebSocketADKBridge

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables"""
    required_vars = [
        'GOOGLE_CLOUD_PROJECT',
        'GOOGLE_CLOUD_LOCATION'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    logger.info("✅ Environment validation passed")

async def main():
    """Main startup function"""
    try:
        logger.info("🚀 Starting WebSocket ADK Bridge Server...")
        
        # Validate environment
        validate_environment()
        
        # Get configuration from environment
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', '8003'))
        
        logger.info(f"Server configuration: host={host}, port={port}")
        logger.info(f"Google Cloud Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
        logger.info(f"Google Cloud Location: {os.getenv('GOOGLE_CLOUD_LOCATION')}")
        
        # Create and start bridge server
        bridge = WebSocketADKBridge(host=host, port=port)
        await bridge.start_server()
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user (SIGINT)")
    except Exception as e:
        logger.error(f"❌ Fatal error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())