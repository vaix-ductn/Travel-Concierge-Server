"""
WebSocket ADK Bridge Server
Bridges Flutter WebSocket client with Google ADK Live API
"""

import asyncio
import json
import base64
import logging
import os
import websockets
from datetime import datetime
from typing import Dict, Set, Optional
from collections import deque
import uuid

# Google ADK imports
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
import vertexai
from vertexai.generative_models import GenerationConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "sascha-playground-doit")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL = "gemini-2.0-flash-live-preview-04-09"
VOICE_NAME = "Aoede"

# Audio configuration
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
AUDIO_FORMAT = "audio/pcm"

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
logger.info(f"Initialized Vertex AI with project: {PROJECT_ID}, location: {LOCATION}")


class VoiceChatSession:
    """Manages individual voice chat session with ADK Live API"""
    
    def __init__(self, session_id: str, user_id: str, websocket):
        self.session_id = session_id
        self.user_id = user_id
        self.websocket = websocket
        self.live_request_queue = LiveRequestQueue()
        self.runner = None
        self.session = None
        self.session_service = None
        self.agent = None
        self.is_active = False
        self.audio_buffer = deque(maxlen=100)  # Buffer for audio chunks
        self.response_task = None
        
    async def initialize(self):
        """Initialize ADK components"""
        try:
            logger.info(f"Initializing ADK session: {self.session_id}")
            
            # Create Travel Concierge agent with tools
            self.agent = Agent(
                name="travel_concierge_agent",
                model=MODEL,
                instruction="""You are a helpful Travel Concierge AI assistant. You can help users with:
                - Travel planning and destination recommendations
                - Booking assistance and travel advice
                - Local information and cultural insights
                - Weather and transportation guidance
                
                Be friendly, knowledgeable, and provide helpful travel-related information.
                Keep responses concise but informative for voice conversations.""",
                tools=[],  # Add travel-specific tools here if needed
            )
            
            # Create session service and session
            self.session_service = InMemorySessionService()
            self.session = self.session_service.create_session(
                app_name="travel_concierge_voice", 
                user_id=self.user_id, 
                session_id=self.session_id
            )
            
            # Create runner
            self.runner = Runner(
                app_name="travel_concierge_voice",
                agent=self.agent,
                session_service=self.session_service,
            )
            
            logger.info(f"✅ ADK session initialized: {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ADK session: {e}")
            return False
    
    async def start_streaming(self):
        """Start ADK Live API streaming"""
        try:
            if not self.runner:
                raise ValueError("Session not initialized")
                
            # Create run config with audio settings
            run_config = RunConfig(
                streaming_mode=StreamingMode.BIDI,
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
                    )
                ),
                response_modalities=["AUDIO"],
                output_audio_transcription=types.AudioTranscriptionConfig(),
                input_audio_transcription=types.AudioTranscriptionConfig(),
            )
            
            self.is_active = True
            logger.info(f"🎤 Starting ADK streaming for session: {self.session_id}")
            
            # Send connection established message
            await self.send_to_client({
                'type': 'connection_established',
                'session_id': self.session_id,
                'audio_config': {
                    'input_sample_rate': INPUT_SAMPLE_RATE,
                    'output_sample_rate': OUTPUT_SAMPLE_RATE,
                    'format': AUDIO_FORMAT
                }
            })
            
            # Send auto session started
            await self.send_to_client({
                'type': 'auto_session_started',
                'session_id': self.session_id,
                'user_id': self.user_id
            })
            
            # Start response processing task
            self.response_task = asyncio.create_task(self._process_adk_responses(run_config))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start streaming: {e}")
            await self.send_error(f"Failed to start streaming: {e}")
            return False
    
    async def _process_adk_responses(self, run_config):
        """Process responses from ADK Live API"""
        try:
            async for event in self.runner.run_live(
                session=self.session,
                live_request_queue=self.live_request_queue,
                run_config=run_config,
            ):
                if not self.is_active:
                    break
                    
                await self._handle_adk_event(event)
                
        except Exception as e:
            logger.error(f"❌ Error processing ADK responses: {e}")
            await self.send_error(f"ADK processing error: {e}")
    
    async def _handle_adk_event(self, event):
        """Handle individual ADK event"""
        try:
            # Handle model response with audio/text
            if event.content and event.content.parts:
                for part in event.content.parts:
                    # Handle audio response
                    if hasattr(part, 'inline_data') and part.inline_data:
                        audio_data = part.inline_data.data
                        await self.send_to_client({
                            'type': 'adk_audio_response',
                            'audio_data_base64': base64.b64encode(audio_data).decode(),
                            'sample_rate': OUTPUT_SAMPLE_RATE
                        })
                        logger.info(f"📤 Sent audio response: {len(audio_data)} bytes")
                    
                    # Handle text response
                    if hasattr(part, 'text') and part.text:
                        logger.info(f"🤖 Model response: {part.text}")
                        await self.send_to_client({
                            'type': 'adk_text_response',
                            'text': part.text
                        })

            # Handle turn completion
            if event.actions.state_delta.get("turn_complete", False):
                logger.info("✅ Turn complete")
                await self.send_to_client({
                    'type': 'adk_turn_complete'
                })
                
            # Handle interruption
            if event.actions.state_delta.get("interrupted", False):
                logger.info("🤐 Interruption detected")
                await self.send_to_client({
                    'type': 'adk_interrupted'
                })
                
        except Exception as e:
            logger.error(f"❌ Error handling ADK event: {e}")
    
    async def process_audio(self, audio_data: bytes):
        """Process audio data from client and send to ADK"""
        try:
            if not self.is_active:
                return
                
            # Send audio to ADK Live API
            self.live_request_queue.send_realtime(
                types.Blob(
                    data=audio_data,
                    mime_type=f"{AUDIO_FORMAT};rate={INPUT_SAMPLE_RATE}",
                )
            )
            
            logger.debug(f"📥 Processed audio chunk: {len(audio_data)} bytes")
            
        except Exception as e:
            logger.error(f"❌ Error processing audio: {e}")
            await self.send_error(f"Audio processing error: {e}")
    
    async def send_to_client(self, message: Dict):
        """Send message to WebSocket client"""
        try:
            if self.websocket and not self.websocket.closed:
                await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Error sending to client: {e}")
    
    async def send_error(self, message: str):
        """Send error message to client"""
        await self.send_to_client({
            'type': 'error',
            'message': message
        })
    
    async def stop(self):
        """Stop the session"""
        self.is_active = False
        
        if self.response_task:
            self.response_task.cancel()
            try:
                await self.response_task
            except asyncio.CancelledError:
                pass
        
        await self.send_to_client({
            'type': 'session_stopped',
            'session_id': self.session_id
        })
        
        logger.info(f"🛑 Session stopped: {self.session_id}")


class WebSocketADKBridge:
    """Main WebSocket server that bridges clients with ADK Live API"""
    
    def __init__(self, host='0.0.0.0', port=8003):
        self.host = host
        self.port = port
        self.active_sessions: Dict[str, VoiceChatSession] = {}
        self.websocket_to_session: Dict[websockets.WebSocketServerProtocol, str] = {}
        
    async def handle_client(self, websocket, path):
        """Handle new WebSocket client connection"""
        session_id = None
        try:
            logger.info(f"🔌 New client connected from {websocket.remote_address}")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                    
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid JSON received from {websocket.remote_address}")
                    await self._send_error(websocket, "Invalid JSON format")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Client disconnected: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"❌ Error handling client: {e}")
        finally:
            # Cleanup session
            if websocket in self.websocket_to_session:
                session_id = self.websocket_to_session[websocket]
                await self._cleanup_session(websocket, session_id)
    
    async def _handle_message(self, websocket, data: Dict):
        """Handle message from WebSocket client"""
        message_type = data.get('type')
        
        if not message_type:
            # Handle audio data (legacy format)
            await self._handle_audio_data(websocket, data)
            return
        
        if message_type == 'initialize_session':
            await self._initialize_session(websocket, data)
        elif message_type == 'audio_data':
            await self._handle_audio_message(websocket, data)
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _initialize_session(self, websocket, data: Dict):
        """Initialize new voice chat session"""
        try:
            user_id = data.get('user_id', f"user_{uuid.uuid4().hex[:8]}")
            session_id = f"auto_voice_voice_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            # Create session
            session = VoiceChatSession(session_id, user_id, websocket)
            
            # Initialize ADK components
            if await session.initialize():
                self.active_sessions[session_id] = session
                self.websocket_to_session[websocket] = session_id
                
                # Start streaming
                await session.start_streaming()
                logger.info(f"✅ Session created and started: {session_id}")
            else:
                await self._send_error(websocket, "Failed to initialize session")
                
        except Exception as e:
            logger.error(f"❌ Error initializing session: {e}")
            await self._send_error(websocket, f"Session initialization failed: {e}")
    
    async def _handle_audio_data(self, websocket, data: Dict):
        """Handle audio data in legacy format"""
        try:
            # Check if this is first message (auto-initialize session)
            if websocket not in self.websocket_to_session:
                await self._initialize_session(websocket, {})
            
            session_id = self.websocket_to_session.get(websocket)
            if not session_id or session_id not in self.active_sessions:
                await self._send_error(websocket, "No active session")
                return
            
            session = self.active_sessions[session_id]
            
            # Extract and decode audio data
            audio_base64 = data.get('data')
            if audio_base64:
                audio_bytes = base64.b64decode(audio_base64)
                await session.process_audio(audio_bytes)
            
        except Exception as e:
            logger.error(f"❌ Error handling audio data: {e}")
            await self._send_error(websocket, f"Audio processing failed: {e}")
    
    async def _handle_audio_message(self, websocket, data: Dict):
        """Handle structured audio message"""
        try:
            session_id = self.websocket_to_session.get(websocket)
            if not session_id or session_id not in self.active_sessions:
                await self._send_error(websocket, "No active session")
                return
            
            session = self.active_sessions[session_id]
            
            # Extract and decode audio data
            audio_base64 = data.get('audio_data')
            if audio_base64:
                audio_bytes = base64.b64decode(audio_base64)
                await session.process_audio(audio_bytes)
            
        except Exception as e:
            logger.error(f"❌ Error handling audio message: {e}")
            await self._send_error(websocket, f"Audio processing failed: {e}")
    
    async def _send_error(self, websocket, message: str):
        """Send error message to WebSocket client"""
        try:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': message
            }))
        except Exception as e:
            logger.error(f"❌ Error sending error message: {e}")
    
    async def _cleanup_session(self, websocket, session_id: str):
        """Cleanup session when client disconnects"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                await session.stop()
                del self.active_sessions[session_id]
            
            if websocket in self.websocket_to_session:
                del self.websocket_to_session[websocket]
                
            logger.info(f"🧹 Cleaned up session: {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up session: {e}")
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"🚀 Starting WebSocket ADK Bridge Server on {self.host}:{self.port}")
        
        # Add health check handler
        async def health_check(path, request_headers):
            if path == "/health":
                return (200, {}, b"OK")
            # Continue with WebSocket protocol
            return None
        
        async with websockets.serve(
            self.handle_client, 
            self.host, 
            self.port,
            subprotocols=["voice-chat"],
            process_request=health_check
        ):
            logger.info(f"✅ WebSocket ADK Bridge Server running on ws://{self.host}:{self.port}")
            logger.info(f"✅ Health check available at http://{self.host}:{self.port}/health")
            await asyncio.Future()  # Run forever


async def main():
    """Main entry point"""
    try:
        bridge = WebSocketADKBridge()
        await bridge.start_server()
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())