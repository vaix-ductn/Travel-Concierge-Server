"""
Django management command to start the Voice Chat WebSocket server
Usage: python manage.py start_voice_server
"""
import asyncio
import logging
import signal
import sys
from django.core.management.base import BaseCommand
from django.conf import settings

from travel_concierge.voice_chat.websocket_server import voice_websocket_server


class Command(BaseCommand):
    help = 'Start the Voice Chat WebSocket server for real-time audio streaming'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='192.168.1.8',
            help='Host to bind the WebSocket server (default: 192.168.1.8)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8003,
            help='Port to bind the WebSocket server (default: 8003)'
        )
        parser.add_argument(
            '--log-level',
            type=str,
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            help='Logging level (default: INFO)'
        )

    def handle(self, *args, **options):
        # Setup logging
        log_level = getattr(logging, options['log_level'])
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)

        # Update server configuration
        voice_websocket_server.host = options['host']
        voice_websocket_server.port = options['port']

        logger.info(f"🚀 Starting Voice Chat WebSocket Server...")
        logger.info(f"📍 Host: {options['host']}")
        logger.info(f"🔌 Port: {options['port']}")
        logger.info(f"📊 Log Level: {options['log_level']}")

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, shutting down...")
            asyncio.create_task(self.shutdown_server())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start the server
        try:
            asyncio.run(self.run_server())
        except KeyboardInterrupt:
            logger.info("🛑 Server stopped by user")
        except Exception as e:
            logger.error(f"❌ Server error: {str(e)}")
            sys.exit(1)

    async def run_server(self):
        """Run the WebSocket server"""
        logger = logging.getLogger(__name__)

        try:
            # Start the WebSocket server
            await voice_websocket_server.start_server()

            logger.info("✅ Voice Chat WebSocket Server is running!")
            logger.info(f"🔗 WebSocket URL: ws://{voice_websocket_server.host}:{voice_websocket_server.port}")
            logger.info("📱 Flutter apps can now connect for voice chat")
            logger.info("⚡ Press Ctrl+C to stop the server")

            # Keep the server running
            while voice_websocket_server.is_running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Failed to start server: {str(e)}")
            raise

    async def shutdown_server(self):
        """Gracefully shutdown the server"""
        logger = logging.getLogger(__name__)

        try:
            logger.info("🔄 Shutting down Voice Chat WebSocket Server...")
            await voice_websocket_server.stop_server()
            logger.info("✅ Server shutdown complete")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {str(e)}")
        finally:
            # Force exit
            import os
            os._exit(0)