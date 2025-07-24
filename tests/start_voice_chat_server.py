#!/usr/bin/env python3
"""
Voice Chat Server Startup Script
Starts the voice chat WebSocket server and provides testing utilities
"""
import os
import sys
import asyncio
import logging
import signal
import json
from typing import Optional

# Add Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_status(message: str, status: str = "INFO"):
    """Print colored status messages"""
    colors = {
        "INFO": "\033[0;34m",      # Blue
        "SUCCESS": "\033[0;32m",   # Green
        "WARNING": "\033[1;33m",   # Yellow
        "ERROR": "\033[0;31m",     # Red
        "RESET": "\033[0m"         # Reset
    }

    color = colors.get(status, colors["INFO"])
    reset = colors["RESET"]

    icons = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌"
    }

    icon = icons.get(status, "ℹ️")
    print(f"{color}{icon} {message}{reset}")

def setup_environment():
    """Setup environment for voice chat"""
    print_status("Setting up environment for voice chat...", "INFO")

    # Set required environment variables
    os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'
    os.environ['ADK_DISABLE_TELEMETRY'] = 'true'
    os.environ['GOOGLE_GENAI_DISABLE_TELEMETRY'] = 'true'
    os.environ['OTEL_SDK_DISABLED'] = 'true'

    # Check required environment variables
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')

    if not project_id:
        print_status("GOOGLE_CLOUD_PROJECT environment variable not set", "ERROR")
        print_status("Please run: export GOOGLE_CLOUD_PROJECT=your-project-id", "INFO")
        return False

    print_status(f"Google Cloud Project: {project_id}", "SUCCESS")
    print_status(f"Google Cloud Location: {location}", "SUCCESS")

    return True

async def start_voice_server():
    """Start the voice chat WebSocket server"""
    try:
        from travel_concierge.voice_chat.websocket_server import voice_websocket_server

        print_status("Starting Voice Chat WebSocket Server...", "INFO")

        # Start the server
        await voice_websocket_server.start_server()

        print_status(f"🎤 Voice Chat Server started successfully!", "SUCCESS")
        print_status(f"WebSocket URL: ws://{voice_websocket_server.host}:{voice_websocket_server.port}", "INFO")
        print_status(f"Subprotocol: voice-chat", "INFO")

        return voice_websocket_server

    except Exception as e:
        print_status(f"Failed to start voice chat server: {e}", "ERROR")
        logger.exception("Voice chat server startup failed")
        raise

async def test_server_health():
    """Test server health and configuration"""
    print_status("Testing server health...", "INFO")

    try:
        from travel_concierge.voice_chat.adk_live_handler import adk_live_handler
        from travel_concierge.voice_chat.websocket_server import voice_websocket_server

        # Test ADK handler
        print_status("ADK Live Handler:", "INFO")
        print_status(f"  Project: {adk_live_handler.project_id}", "SUCCESS")
        print_status(f"  Model: {adk_live_handler.model_name}", "SUCCESS")
        print_status(f"  Voice: {adk_live_handler.voice_name}", "SUCCESS")
        print_status(f"  Input Rate: {adk_live_handler.input_sample_rate}Hz", "SUCCESS")
        print_status(f"  Output Rate: {adk_live_handler.output_sample_rate}Hz", "SUCCESS")

        # Test WebSocket server
        print_status("WebSocket Server:", "INFO")
        print_status(f"  Host: {voice_websocket_server.host}", "SUCCESS")
        print_status(f"  Port: {voice_websocket_server.port}", "SUCCESS")
        print_status(f"  Running: {voice_websocket_server.is_running}", "SUCCESS")

        # Test session management
        active_sessions = len(adk_live_handler.active_sessions)
        print_status(f"  Active Sessions: {active_sessions}", "SUCCESS")

        return True

    except Exception as e:
        print_status(f"Server health check failed: {e}", "ERROR")
        return False

def print_connection_info():
    """Print connection information for clients"""
    print_status("\n=== CONNECTION INFORMATION ===", "INFO")
    print_status("For Flutter app configuration:", "INFO")
    print_status("WebSocket URL: ws://192.168.1.8:8003", "SUCCESS")
    print_status("Subprotocol: voice-chat", "SUCCESS")
    print_status("Audio Format: 16-bit PCM", "SUCCESS")
    print_status("Input Sample Rate: 16000 Hz", "SUCCESS")
    print_status("Output Sample Rate: 24000 Hz", "SUCCESS")

    print_status("\nWebSocket Message Types:", "INFO")
    print_status("- start_session: Start a voice chat session", "INFO")
    print_status("- stop_session: Stop the current session", "INFO")
    print_status("- ping: Ping server for connectivity test", "INFO")
    print_status("- get_status: Get server status", "INFO")
    print_status("- audio/pcm messages: Send audio data", "INFO")

    print_status("\nExpected Responses:", "INFO")
    print_status("- connection_established: Connection confirmed", "INFO")
    print_status("- session_started: Session created successfully", "INFO")
    print_status("- adk_event: AI agent responses (text/audio)", "INFO")
    print_status("- session_stopped: Session closed", "INFO")

def print_testing_commands():
    """Print testing commands"""
    print_status("\n=== TESTING COMMANDS ===", "INFO")
    print_status("Run comprehensive tests:", "INFO")
    print_status("  python test_voice_chat_complete.py", "SUCCESS")

    print_status("Test audio formats:", "INFO")
    print_status("  python test_voice_audio_formats.py", "SUCCESS")

    print_status("Test Django integration:", "INFO")
    print_status("  curl http://localhost:8001/api/voice-chat/status/", "SUCCESS")
    print_status("  curl http://localhost:8001/api/voice-chat/health/", "SUCCESS")

    print_status("Monitor logs:", "INFO")
    print_status("  tail -f logs/voice_chat.log", "SUCCESS")

async def monitor_server(server):
    """Monitor server and handle shutdown gracefully"""
    def signal_handler(signum, frame):
        print_status(f"\nReceived signal {signum}, shutting down...", "WARNING")
        asyncio.create_task(shutdown_server(server))

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print_status("\n🎯 Voice Chat Server is running!", "SUCCESS")
    print_status("Press Ctrl+C to stop the server", "INFO")

    try:
        # Keep server running
        while server.is_running:
            await asyncio.sleep(1)

            # Print periodic status
            await asyncio.sleep(30)  # Every 30 seconds
            active_sessions = len(server.websocket_sessions)
            if active_sessions > 0:
                print_status(f"Server status: {active_sessions} active sessions", "INFO")

    except asyncio.CancelledError:
        print_status("Server monitoring cancelled", "INFO")

async def shutdown_server(server):
    """Shutdown server gracefully"""
    try:
        print_status("Shutting down voice chat server...", "INFO")

        # Close all active sessions
        from travel_concierge.voice_chat.adk_live_handler import adk_live_handler

        active_sessions = list(adk_live_handler.active_sessions.keys())
        if active_sessions:
            print_status(f"Closing {len(active_sessions)} active sessions...", "INFO")
            for session_id in active_sessions:
                await adk_live_handler.close_session(session_id)

        # Stop WebSocket server
        await server.stop_server()

        print_status("Voice chat server shutdown complete", "SUCCESS")

    except Exception as e:
        print_status(f"Error during shutdown: {e}", "ERROR")

async def main():
    """Main function"""
    print_status("=== VOICE CHAT SERVER STARTUP ===", "INFO")

    try:
        # Setup environment
        if not setup_environment():
            sys.exit(1)

        # Start voice server
        server = await start_voice_server()

        # Test server health
        await test_server_health()

        # Print connection information
        print_connection_info()

        # Print testing commands
        print_testing_commands()

        # Monitor server
        await monitor_server(server)

    except KeyboardInterrupt:
        print_status("\nShutdown requested by user", "WARNING")
    except Exception as e:
        print_status(f"Server startup failed: {e}", "ERROR")
        logger.exception("Voice chat server failed")
        sys.exit(1)
    finally:
        print_status("Voice chat server stopped", "INFO")

if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists('travel_concierge'):
        print_status("Please run this script from the Server/travel_server directory", "ERROR")
        sys.exit(1)

    # Run server
    asyncio.run(main())