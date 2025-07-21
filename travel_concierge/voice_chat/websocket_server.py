"""
WebSocket Server for Voice Chat
Handles real-time audio communication between Flutter app and ADK Live API
Updated for automatic session management and simplified flow
"""
import asyncio
import websockets
import json
import logging
import uuid
import time
import os
from typing import Dict, Set, Optional
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

from .adk_live_handler import adk_live_handler


class VoiceWebSocketServer:
    """
    WebSocket server for handling voice chat connections
    Routes audio between Flutter app and Google ADK Live API with automatic session management
    """

    def __init__(self, host=None, port=8003):
        # Default to bind all interfaces if running in Docker or host not specified
        if host is None:
            # Check if running in Docker container
            if os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER'):
                self.host = "0.0.0.0"  # Bind all interfaces in Docker
            else:
                self.host = "192.168.1.8"  # Specific IP for local development
        else:
            self.host = host

        self.port = port
        self.logger = logging.getLogger(__name__)

        # Connection management
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.websocket_sessions: Dict[WebSocketServerProtocol, str] = {}  # websocket -> session_id

        # Server state
        self.server = None
        self.is_running = False

        self.logger.info(f"Voice WebSocket Server initialized on {self.host}:{self.port}")

    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self.handle_client_direct,
                self.host,
                self.port,
                subprotocols=["voice-chat"]
            )
            self.is_running = True
            self.logger.info(f"🎤 Voice WebSocket Server started on ws://{self.host}:{self.port}")

        except Exception as e:
            self.logger.error(f"Failed to start WebSocket server: {str(e)}")
            # Try fallback to localhost if specific IP fails
            if self.host != "0.0.0.0":
                self.logger.info("Retrying with 0.0.0.0 (all interfaces)")
                self.host = "0.0.0.0"
                try:
                    self.server = await websockets.serve(
                        self.handle_client_direct,
                        self.host,
                        self.port,
                        subprotocols=["voice-chat"]
                    )
                    self.is_running = True
                    self.logger.info(f"🎤 Voice WebSocket Server started on ws://{self.host}:{self.port}")
                except Exception as e2:
                    self.logger.error(f"Failed to start WebSocket server on fallback: {str(e2)}")
                    raise e2
            else:
                raise e

    async def handle_client_direct(self, websocket: WebSocketServerProtocol):
        """WebSocket handler compatible with websockets 12.0+ (only websocket parameter)"""
        # Log the connection for debugging
        self.logger.info(f"🔗 New WebSocket connection from {websocket.remote_address}")
        await self.handle_client(websocket)

    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.is_running = False
            self.logger.info("Voice WebSocket Server stopped")

    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle individual client connections with automatic session management"""
        client_id = f"client_{int(time.time())}_{id(websocket)}"
        session_id = None

        try:
            self.logger.info(f"🔌 New WebSocket connection: {client_id}")

            # Send welcome message with auto-session info
            await self.send_message(websocket, {
                'type': 'connection_established',
                'client_id': client_id,
                'server_time': time.time(),
                'auto_session': True,  # Indicate automatic session management
                'audio_config': {
                    'input_sample_rate': adk_live_handler.input_sample_rate,
                    'output_sample_rate': adk_live_handler.output_sample_rate,
                    'voice_name': adk_live_handler.voice_name,
                    'supported_formats': ['audio/pcm;rate=16000']
                }
            })

            # Auto-create session immediately on connection
            user_id = f"voice_user_{int(time.time())}_{client_id[-8:]}"
            session_info = await adk_live_handler.create_auto_session(user_id)

            if session_info:
                session_id = session_info['session_id']
                self.websocket_sessions[websocket] = session_id

                await self.send_message(websocket, {
                    'type': 'auto_session_started',
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'ready_for_audio'
                })

                # Start live streaming task automatically
                asyncio.create_task(self.stream_responses(websocket, session_id))

                self.logger.info(f"🎯 Auto-started voice session {session_id} for {client_id}")
            else:
                await self.send_error(websocket, "Failed to initialize voice session")
                return

            async for message in websocket:
                try:
                    if isinstance(message, bytes):
                        # Handle audio data directly
                        await self.handle_audio_data(websocket, message, session_id)
                    else:
                        # Handle text messages (JSON)
                        await self.handle_text_message(websocket, json.loads(message), client_id)

                except json.JSONDecodeError as e:
                    await self.send_error(websocket, f"Invalid JSON: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Error processing message: {str(e)}")
                    await self.send_error(websocket, f"Processing error: {str(e)}")

        except ConnectionClosed:
            self.logger.info(f"🔌 WebSocket connection closed: {client_id}")
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {str(e)}")
        finally:
            # Automatic cleanup
            await self.cleanup_connection(websocket, session_id)

    async def handle_text_message(self, websocket: WebSocketServerProtocol, message: dict, client_id: str):
        """Handle text-based control messages"""
        message_type = message.get('type')

        if message_type == 'ping':
            await self.send_message(websocket, {'type': 'pong', 'timestamp': time.time()})
        elif message_type == 'get_status':
            await self.handle_get_status(websocket, message)
        elif message_type == 'stop_session':
            # Allow manual session stop if needed
            await self.handle_stop_session(websocket, message)
        elif message_type == 'text_input':
            # Handle text input for AI responses
            await self.handle_text_input(websocket, message)
        elif 'mime_type' in message and message['mime_type'].startswith('audio/pcm'):
            # Handle JSON audio messages from Flutter app (ADK protocol)
            await self.handle_json_audio_message(websocket, message)
        else:
            self.logger.debug(f"Ignoring message type: {message_type}")

    async def handle_stop_session(self, websocket: WebSocketServerProtocol, message: dict):
        """Stop the current voice chat session"""
        session_id = self.websocket_sessions.get(websocket)
        if not session_id:
            await self.send_error(websocket, "No active session to stop")
            return

        try:
            success = await adk_live_handler.close_session(session_id)
            if success:
                await self.send_message(websocket, {
                    'type': 'session_stopped',
                    'session_id': session_id
                })
                self.logger.info(f"🛑 Stopped voice session {session_id}")
            else:
                await self.send_error(websocket, "Failed to stop session")

        except Exception as e:
            self.logger.error(f"Error stopping session: {str(e)}")
            await self.send_error(websocket, f"Error stopping session: {str(e)}")

    async def handle_get_status(self, websocket: WebSocketServerProtocol, message: dict):
        """Get status information"""
        session_id = self.websocket_sessions.get(websocket)

        status_info = {
            'type': 'status_response',
            'server_status': 'running' if self.is_running else 'stopped',
            'active_connections': len(self.connections),
            'total_sessions': len(adk_live_handler.active_sessions),
            'current_session': adk_live_handler.get_session_status(session_id) if session_id else None,
            'auto_session_mode': True
        }

        await self.send_message(websocket, status_info)

    async def handle_json_audio_message(self, websocket: WebSocketServerProtocol, message: dict):
        """Handle JSON audio messages from Flutter app (ADK protocol)"""
        session_id = self.websocket_sessions.get(websocket)
        if not session_id:
            await self.send_error(websocket, "No active session for audio data")
            return

        try:
            # Extract and decode base64 audio data
            base64_data = message.get('data')
            if not base64_data:
                await self.send_error(websocket, "No audio data in message")
                return

            # Decode base64 to bytes
            import base64
            audio_data = base64.b64decode(base64_data)

            # Log the audio transmission
            self.logger.debug(f"📥 Received JSON audio message: {len(base64_data)} chars (base64) -> {len(audio_data)} bytes (binary)")

            # Process using existing audio handler
            success = await adk_live_handler.process_audio_input(session_id, audio_data)

            if not success:
                self.logger.warning(f"⚠️ Audio processing failed for session {session_id}")
                # Don't send error to client for audio processing failures to avoid spam
            else:
                self.logger.debug(f"✅ Successfully processed JSON audio for session {session_id}")

        except Exception as e:
            self.logger.error(f"❌ Error processing JSON audio message: {str(e)}")
            await self.send_error(websocket, f"JSON audio processing error: {str(e)}")

    async def handle_audio_data(self, websocket: WebSocketServerProtocol, audio_data: bytes, session_id: Optional[str]):
        """Handle incoming binary audio data from client"""
        if not session_id:
            await self.send_error(websocket, "No active session for audio data")
            return

        try:
            self.logger.debug(f"📥 Received binary audio data: {len(audio_data)} bytes")

            # Process audio through ADK Live Handler
            success = await adk_live_handler.process_audio_input(session_id, audio_data)

            if not success:
                self.logger.warning(f"⚠️ Binary audio processing failed for session {session_id}")
                # Don't send error to client for audio processing failures to avoid spam
            else:
                self.logger.debug(f"✅ Successfully processed binary audio for session {session_id}")

        except Exception as e:
            self.logger.error(f"❌ Error processing binary audio data: {str(e)}")
            await self.send_error(websocket, f"Binary audio processing error: {str(e)}")

    async def stream_responses(self, websocket: WebSocketServerProtocol, session_id: str):
        """Stream responses from ADK back to client"""
        try:
            async for response in adk_live_handler.start_live_session(session_id):
                try:
                    if response['event_type'] == 'audio_response':
                        # Send audio response in structured format for Flutter
                        await self.send_message(websocket, {
                            'type': 'adk_audio_response',
                            'audio_data_base64': response['data']['audio_data_base64'],
                            'audio_size': response['data']['audio_size'],
                            'session_id': session_id,
                            'timestamp': response['timestamp']
                        })
                        self.logger.debug(f"📤 Sent {response['data']['audio_size']} bytes audio to client")

                    elif response['event_type'] == 'text_response':
                        # Send text response
                        await self.send_message(websocket, {
                            'type': 'adk_text_response',
                            'text': response['data']['text'],
                            'session_id': session_id,
                            'timestamp': response['timestamp']
                        })
                        self.logger.debug(f"💬 Sent text response: {response['data']['text'][:50]}...")

                    elif response['event_type'] == 'tool_call':
                        # Send tool call event
                        await self.send_message(websocket, {
                            'type': 'adk_tool_call',
                            'tool_name': response['data']['tool_name'],
                            'session_id': session_id,
                            'timestamp': response['timestamp']
                        })
                        self.logger.debug(f"🔧 Tool call: {response['data']['tool_name']}")

                    elif response['event_type'] == 'turn_complete':
                        # Send completion event
                        await self.send_message(websocket, {
                            'type': 'adk_turn_complete',
                            'session_id': session_id,
                            'timestamp': response['timestamp']
                        })
                        self.logger.debug(f"✅ Turn completed for session {session_id}")

                except ConnectionClosed:
                    self.logger.info(f"Client disconnected during response streaming for session {session_id}")
                    break
                except Exception as e:
                    self.logger.error(f"Error sending response: {str(e)}")
                    break

        except Exception as e:
            self.logger.error(f"Error in response streaming for session {session_id}: {str(e)}")
        finally:
            # Cleanup session when streaming ends
            await adk_live_handler.close_session(session_id)

    async def send_message(self, websocket: WebSocketServerProtocol, message: dict):
        """Send JSON message to client"""
        try:
            await websocket.send(json.dumps(message))
        except ConnectionClosed:
            pass  # Client disconnected
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")

    async def send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """Send error message to client"""
        await self.send_message(websocket, {
            'type': 'error',
            'message': error_message,
            'timestamp': time.time()
        })

    async def cleanup_connection(self, websocket: WebSocketServerProtocol, session_id: Optional[str]):
        """Clean up connection and associated resources"""
        try:
            # Remove from tracking
            if websocket in self.websocket_sessions:
                del self.websocket_sessions[websocket]

            # Close ADK session if exists
            if session_id:
                await adk_live_handler.close_session(session_id)

            self.logger.info(f"🧹 Cleaned up connection for session {session_id}")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


    async def handle_text_input(self, websocket: WebSocketServerProtocol, message: dict):
        """Handle text input messages for AI responses"""
        session_id = self.websocket_sessions.get(websocket)
        if not session_id:
            await self.send_error(websocket, "No active session for text input")
            return

        try:
            text = message.get('text', '')
            if not text:
                await self.send_error(websocket, "No text in message")
                return

            self.logger.info(f"📝 Received text input: {text}")

            # Send text to ADK session
            success = await adk_live_handler.process_text_input(session_id, text)

            if not success:
                self.logger.warning(f"⚠️ Text processing failed for session {session_id}")
                await self.send_error(websocket, "Failed to process text input")
            else:
                self.logger.info(f"✅ Successfully processed text for session {session_id}")

        except Exception as e:
            self.logger.error(f"❌ Error processing text input: {str(e)}")
            await self.send_error(websocket, f"Error processing text input: {str(e)}")


# Global server instance
voice_websocket_server = VoiceWebSocketServer()


async def start_voice_server():
    """Convenience function to start the voice server"""
    await voice_websocket_server.start_server()
    return voice_websocket_server