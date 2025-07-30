"""
ADK Live API Handler for Voice Chat
Integrates Google ADK with Live API for bidirectional audio streaming
Updated for automatic session management and simplified voice chat flow
"""
import asyncio
import logging
import time
import os
import json
import base64
import uuid
from typing import AsyncGenerator, Optional, Dict, Any
from collections import deque

from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions import InMemorySessionService
from google.genai import types
import vertexai

# Import existing travel concierge agent
from travel_concierge.agent import root_agent

# Configure environment for ADK Live API
def configure_environment():
    """Configure environment variables for ADK Live API"""
    # Set environment variables for telemetry and performance
    os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'
    os.environ['ADK_DISABLE_TELEMETRY'] = 'true'
    os.environ['GOOGLE_GENAI_DISABLE_TELEMETRY'] = 'true'
    os.environ['OTEL_SDK_DISABLED'] = 'true'

    # Set default location if not configured
    if not os.getenv('GOOGLE_CLOUD_LOCATION'):
        os.environ['GOOGLE_CLOUD_LOCATION'] = 'us-central1'

# Patch telemetry for safe handling
def patch_telemetry_safe():
    """Patch telemetry to safely handle non-serializable data"""
    try:
        import google.adk.core.telemetry as telemetry

        original_record_event = telemetry.record_event

        def safe_record_event(event_name: str, **kwargs):
            try:
                # Filter out non-serializable data like bytes
                safe_kwargs = {}
                for k, v in kwargs.items():
                    if isinstance(v, (str, int, float, bool, list, dict)) or v is None:
                        safe_kwargs[k] = v
                    elif isinstance(v, bytes):
                        safe_kwargs[k] = f"<bytes:{len(v)}>"
                    else:
                        safe_kwargs[k] = str(type(v).__name__)

                return original_record_event(event_name, **safe_kwargs)
            except Exception:
                # If telemetry fails, just skip it
                pass

        telemetry.record_event = safe_record_event

    except ImportError:
        # Telemetry not available, skip patching
        pass

class ADKLiveHandler:
    """
    Simplified ADK Live Handler for automatic voice chat sessions
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Configure environment
        configure_environment()
        patch_telemetry_safe()

        # ADK Configuration
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'travelapp-461806')
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        self.model_name = "gemini-2.0-flash-live-preview-04-09"
        self.voice_name = "Aoede"

        # Audio configuration
        self.input_sample_rate = 16000   # 16kHz input (Flutter app)
        self.output_sample_rate = 24000  # 24kHz output (ADK Live API)

        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id mapping
        self.max_sessions = 10  # Limit maximum concurrent sessions

        # Initialize Vertex AI
        try:
            vertexai.init(project=self.project_id, location=self.location)
        except Exception as e:
            self.logger.warning(f"Failed to initialize Vertex AI: {e}")

        self.logger.info(f"✅ ADK Live Handler configured:")
        self.logger.info(f"   - Project: {self.project_id}")
        self.logger.info(f"   - Location: {self.location}")
        self.logger.info(f"   - Model: {self.model_name}")
        self.logger.info(f"   - Voice: {self.voice_name}")
        self.logger.info(f"   - Input Rate: {self.input_sample_rate}Hz")
        self.logger.info(f"   - Output Rate: {self.output_sample_rate}Hz")

    async def create_auto_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Create an automatic voice chat session for simplified flow
        This combines connection, session creation, and initialization
        """
        try:
            # Clean up old sessions if too many
            await self._cleanup_old_sessions()
            
            # Generate unique session ID
            session_id = f"auto_voice_{user_id}_{int(time.time())}_{str(uuid.uuid4())[:8]}"

            self.logger.info(f"🎬 Creating auto voice session {session_id} for user {user_id}")

                        # Create session service
            session_service = InMemorySessionService()

            # Create session
            session = await session_service.create_session(
                app_name="travel_concierge_voice",
                user_id=user_id
            )

            # Create runner with travel concierge agent
            runner = InMemoryRunner(
                app_name="travel_concierge_voice",
                agent=root_agent
            )

            # Configure for live audio/text responses (Python uses strings for modalities)
            run_config = RunConfig(
                response_modalities=["AUDIO", "TEXT"],  # Use strings as per ADK Python docs
                streaming_mode=StreamingMode.BIDI
            )

            # Create live request queue
            live_request_queue = LiveRequestQueue()

            # Start live session
            live_events = runner.run_live(
                session=session,
                live_request_queue=live_request_queue,
                run_config=run_config
            )

            # Store session info
            session_info = {
                'session_id': session_id,
                'user_id': user_id,
                'runner': runner,
                'session': session,
                'live_request_queue': live_request_queue,
                'live_events': live_events,
                'created_at': time.time(),
                'is_active': True,
                'conversation_started': True
            }

            self.active_sessions[session_id] = session_info
            self.user_sessions[user_id] = session_id

            # Send initial greeting to start conversation
            initial_greeting = "Chào bạn! Tôi là trợ lý du lịch AI. Hãy nói để tôi giúp bạn lên kế hoạch chuyến đi mơ ước!"
            await self._send_text_to_session(session_id, initial_greeting)

            self.logger.info(f"✅ Created auto voice session {session_id} for user {user_id}")
            return session_info

        except Exception as e:
            import traceback
            self.logger.error(f"❌ Failed to create auto session: {str(e)}")
            self.logger.error(f"❌ Exception details: {traceback.format_exc()}")
            return None

    async def _send_text_to_session(self, session_id: str, text: str):
        """Send text message to ADK session to start conversation"""
        try:
            session_info = self.active_sessions.get(session_id)
            if not session_info:
                return False

            live_request_queue = session_info['live_request_queue']

            # Create text content
            text_content = types.Content(
                parts=[types.Part(text=text)],
                role="user"
            )

            # Send to live queue (send_content is not async)
            live_request_queue.send_content(text_content)
            self.logger.info(f"🎬 Sent initial greeting for session {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to send initial text: {str(e)}")
            return False

    async def process_audio_input(self, session_id: str, audio_data: bytes) -> bool:
        """Process audio input from client"""
        try:
            session_info = self.active_sessions.get(session_id)
            if not session_info:
                self.logger.error(f"❌ No active session found for {session_id}")
                self.logger.error(f"❌ Available sessions: {list(self.active_sessions.keys())}")
                
                # Don't try to recreate session - this causes session ID mismatch
                self.logger.error(f"❌ Session {session_id} was requested but not found")
                self.logger.error(f"❌ This indicates session ID synchronization issue between client and server")
                return False
                
            if not session_info['is_active']:
                self.logger.error(f"❌ Session {session_id} is not active")
                # Try to reactivate session
                session_info['is_active'] = True
                self.logger.info(f"🔄 Reactivated session {session_id}")

            live_request_queue = session_info['live_request_queue']
            
            # Validate live_request_queue
            if not live_request_queue:
                self.logger.error(f"❌ No live_request_queue for session {session_id}")
                return False

            # Create audio blob
            audio_blob = types.Blob(
                mime_type="audio/pcm;rate=16000",
                data=audio_data
            )

            # Send audio to live queue using realtime method (ADK requirement for audio)
            live_request_queue.send_realtime(audio_blob)

            self.logger.debug(f"📥 Processed {len(audio_data)} bytes audio for session {session_id}")
            return True

        except Exception as e:
            import traceback
            self.logger.error(f"❌ Failed to process audio input for session {session_id}: {str(e)}")
            self.logger.error(f"❌ Exception details: {traceback.format_exc()}")
            return False

    async def start_live_session(self, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Start live session streaming for responses"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            self.logger.error(f"❌ Session {session_id} not found for streaming")
            return

        self.logger.info(f"🎤 Starting live session stream for {session_id}")

        try:
            live_events = session_info['live_events']

            async for event in live_events:
                try:
                    # Handle turn complete/interrupted events
                    if hasattr(event, 'turn_complete') and event.turn_complete:
                        yield {
                            'event_type': 'turn_complete',
                            'data': {
                                'session_id': session_id,
                                'turn_complete': True
                            },
                            'timestamp': time.time()
                        }
                        continue

                    if hasattr(event, 'interrupted') and event.interrupted:
                        yield {
                            'event_type': 'interrupted',
                            'data': {
                                'session_id': session_id,
                                'interrupted': True
                            },
                            'timestamp': time.time()
                        }
                        continue

                    # Process content and parts (ADK structure)
                    if hasattr(event, 'content') and event.content:
                        content = event.content
                        if hasattr(content, 'parts') and content.parts:
                            for part in content.parts:
                                # Handle text responses
                                if hasattr(part, 'text') and part.text:
                                    yield {
                                        'event_type': 'text_response',
                                        'data': {
                                            'text': part.text,
                                            'session_id': session_id,
                                            'partial': getattr(event, 'partial', False)
                                        },
                                        'timestamp': time.time()
                                    }

                                # Handle audio responses (inline_data)
                                elif hasattr(part, 'inline_data') and part.inline_data:
                                    inline_data = part.inline_data
                                    if (hasattr(inline_data, 'mime_type') and
                                        inline_data.mime_type.startswith('audio/pcm') and
                                        hasattr(inline_data, 'data') and inline_data.data):

                                        # Convert audio data to base64 for transmission
                                        audio_base64 = base64.b64encode(inline_data.data).decode('utf-8')
                                        yield {
                                            'event_type': 'audio_response',
                                            'data': {
                                                'audio_data_base64': audio_base64,
                                                'audio_size': len(inline_data.data),
                                                'session_id': session_id,
                                                'mime_type': inline_data.mime_type
                                            },
                                            'timestamp': time.time()
                                        }

                    # Handle function calls
                    elif hasattr(event, 'function_call') and event.function_call:
                        yield {
                            'event_type': 'tool_call',
                            'data': {
                                'tool_name': getattr(event.function_call, 'name', 'unknown'),
                                'session_id': session_id
                            },
                            'timestamp': time.time()
                        }

                    # Handle completion events
                    elif 'turn_complete' in str(event).lower() or 'complete' in event_type.lower():
                        yield {
                            'event_type': 'turn_complete',
                            'data': {
                                'session_id': session_id
                            },
                            'timestamp': time.time()
                        }

                except Exception as e:
                    self.logger.error(f"❌ Error processing live event: {str(e)}")
                    continue

        except Exception as e:
            self.logger.error(f"❌ Error in live session streaming: {str(e)}")
        finally:
            # Auto-cleanup session if streaming ends unexpectedly
            if session_id in self.active_sessions:
                self.logger.info(f"🧹 Auto-cleaning up session {session_id} after streaming ended")

    async def close_session(self, session_id: str) -> bool:
        """Close and cleanup a voice chat session"""
        try:
            session_info = self.active_sessions.get(session_id)
            if not session_info:
                self.logger.warning(f"⚠️ Session {session_id} not found for closing")
                return True  # Already closed

            self.logger.info(f"🛑 Closing voice session {session_id}")

            # Mark as inactive
            session_info['is_active'] = False

            # Close live request queue
            live_request_queue = session_info.get('live_request_queue')
            if live_request_queue:
                try:
                    live_request_queue.close()
                except Exception as e:
                    self.logger.debug(f"Error closing live request queue: {e}")

            # Remove from active sessions
            del self.active_sessions[session_id]

            # Remove user mapping
            user_id = session_info.get('user_id')
            if user_id and user_id in self.user_sessions:
                del self.user_sessions[user_id]

            self.logger.info(f"✅ Successfully closed session {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error closing session {session_id}: {str(e)}")
            return False

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a voice chat session"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            return None

        return {
            'session_id': session_id,
            'user_id': session_info['user_id'],
            'is_active': session_info['is_active'],
            'created_at': session_info['created_at'],
            'conversation_started': session_info.get('conversation_started', False)
        }

    def get_user_session(self, user_id: str) -> Optional[str]:
        """Get active session ID for a user"""
        return self.user_sessions.get(user_id)

    async def cleanup_all_sessions(self):
        """Cleanup all active sessions"""
        try:
            session_ids = list(self.active_sessions.keys())
            self.logger.info(f"🧹 Cleaning up {len(session_ids)} active sessions")

            for session_id in session_ids:
                await self.close_session(session_id)

            self.active_sessions.clear()
            self.user_sessions.clear()

            self.logger.info("✅ All sessions cleaned up")

        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {str(e)}")

    async def _cleanup_old_sessions(self):
        """Cleanup old sessions if too many are active"""
        try:
            if len(self.active_sessions) <= self.max_sessions:
                return
                
            self.logger.warning(f"⚠️ Too many sessions ({len(self.active_sessions)}), cleaning up oldest")
            
            # Get oldest sessions (sort by created_at)
            session_items = list(self.active_sessions.items())
            session_items.sort(key=lambda x: x[1].get('created_at', 0))
            
            # Close oldest sessions to keep only max_sessions
            sessions_to_close = len(self.active_sessions) - self.max_sessions + 1
            for i in range(sessions_to_close):
                if i < len(session_items):
                    session_id = session_items[i][0]
                    await self.close_session(session_id)
                    self.logger.info(f"🧹 Closed old session: {session_id}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error during old session cleanup: {str(e)}")


    async def process_text_input(self, session_id: str, text: str) -> bool:
        """Process text input and send to ADK session"""
        try:
            session_info = self.active_sessions.get(session_id)
            if not session_info:
                self.logger.error(f"❌ No active session found: {session_id}")
                return False

            live_request_queue = session_info['live_request_queue']

            # Create text content
            text_content = types.Content(
                parts=[types.Part(text=text)],
                role="user"
            )

            # Send to live queue (send_content is not async)
            live_request_queue.send_content(text_content)
            self.logger.info(f"📝 Sent text input to session {session_id}: {text}")
            return True

        except Exception as e:
            import traceback
            self.logger.error(f"❌ Failed to process text input: {str(e)}")
            self.logger.error(f"❌ Exception details: {traceback.format_exc()}")
            return False


# Global instance
adk_live_handler = ADKLiveHandler()

# Initialize the handler
try:
    adk_live_handler.logger.info("ADK Live Handler initialized")
except Exception as e:
    logging.error(f"Failed to initialize ADK Live Handler: {e}")