"""
Unified Voice Chat WebSocket Server
Implements the exact design from Design_future_Voice_Chat_AI_Agent_.md
Single FastAPI server with WebSocket endpoint /ws/{client_id}
"""
import asyncio
import logging
import json
import time
import uuid
import base64
from typing import Dict, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Google ADK imports
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
import vertexai

# Import travel concierge agent
from travel_concierge.agent import root_agent

# Configure detailed logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

# Also log to console with colors if available
import sys
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.info("🚀 Voice Chat Server Logger Initialized with DEBUG level")

# Configuration
PROJECT_ID = "travelapp-461806"
LOCATION = "us-central1"
MODEL = "gemini-2.0-flash-exp"  # Primary model
VOICE_NAME = "Aoede"  # Voice that worked in previous sessions

# Initialize Vertex AI
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info(f"Initialized Vertex AI with project: {PROJECT_ID}, location: {LOCATION}")
except Exception as e:
    logger.warning(f"Failed to initialize Vertex AI: {e}")

# FastAPI app
app = FastAPI(title="Travel Concierge Voice Chat Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request, call_next):
    logger.debug(f"🌐 HTTP Request: {request.method} {request.url}")
    logger.debug(f"📋 Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.debug(f"📤 Response: {response.status_code}")
    return response

# Static files for web test interface
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Get static directory path
static_dir = os.path.join(os.getcwd(), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Static files mounted from: {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}")

# Global session storage as per design
active_sessions: Dict[str, Dict[str, Any]] = {}

def define_travel_agent() -> Agent:
    """Define Travel Concierge AI Agent as per design section 3.2"""
    # Try multiple models in order of preference
    models_to_try = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    for model in models_to_try:
        try:
            logger.debug(f"🤖 Trying to create agent with model: {model}")
            agent = Agent(
                name="travel_concierge_agent",
                model=model,
                instruction="You are a helpful travel assistant. Respond briefly and clearly.",
                tools=[],
            )
            logger.info(f"✅ Agent created successfully with model: {model}")
            return agent
        except Exception as e:
            logger.warning(f"⚠️ Failed to create agent with model {model}: {str(e)}")
            continue
    
    # If all models fail, raise error
    raise Exception(f"Failed to create agent with any of these models: {models_to_try}")

async def listen_to_client(websocket: WebSocket, queue: LiveRequestQueue, session_id: str):
    """Listen to client audio data and send to ADK - Design section 3.4"""
    try:
        while True:
            data = await websocket.receive_bytes()
            
            # Log audio chunk received as per design table
            logger.debug(f"AUDIO_CHUNK_RECV - client_id: {session_id}, chunk_size_bytes: {len(data)}")
            
            # Send data to ADK Live Request Queue
            queue.send_realtime(
                types.Blob(
                    data=data,
                    mime_type="audio/pcm;rate=16000",
                )
            )
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected during audio listening: {session_id}")
    except Exception as e:
        logger.error(f"Error in listen_to_client for {session_id}: {str(e)}")

async def process_transcript_with_buffering(websocket: WebSocket, session_id: str, transcript_text: str):
    """Process transcript with advanced buffering to handle streaming chunks"""
    try:
        session_data = active_sessions.get(session_id, {})
        if not session_data:
            return
            
        transcript_buffer = session_data.get('transcript_buffer', [])
        last_chunk_time = session_data.get('last_chunk_time', time.time())
        consolidation_timer = session_data.get('consolidation_timer', None)
        
        current_time = time.time()
        
        # Log incoming transcript chunk
        logger.debug(f"📝 Processing transcript chunk: '{transcript_text[:100]}{'...' if len(transcript_text) > 100 else ''}' (length: {len(transcript_text)})")
        
        # Cancel existing consolidation timer if exists
        if consolidation_timer:
            consolidation_timer.cancel()
            logger.debug(f"⏰ Cancelled previous consolidation timer")
        
        # Add to buffer
        transcript_buffer.append({
            'text': transcript_text,
            'timestamp': current_time,
            'length': len(transcript_text)
        })
        
        # Keep only recent chunks (last 10 seconds)
        transcript_buffer = [chunk for chunk in transcript_buffer if current_time - chunk['timestamp'] < 10.0]
        
        logger.debug(f"📦 Buffer now contains {len(transcript_buffer)} chunks")
        
        # Create consolidation timer - wait 1.5 seconds for more chunks
        async def consolidate_and_send():
            await asyncio.sleep(1.5)  # Wait for streaming to complete
            
            # Get current buffer state
            current_session_data = active_sessions.get(session_id, {})
            current_buffer = current_session_data.get('transcript_buffer', [])
            
            if not current_buffer:
                logger.debug(f"📦 Buffer empty during consolidation, skipping")
                return
                
            # Find the longest/most complete transcript in the buffer
            longest_transcript = max(current_buffer, key=lambda x: x['length'])['text']
            
            # Additional check: use the most recent long transcript if significantly longer
            recent_long_transcripts = [chunk for chunk in current_buffer if chunk['length'] > 50]
            if recent_long_transcripts:
                most_recent_long = max(recent_long_transcripts, key=lambda x: x['timestamp'])
                if most_recent_long['length'] >= longest_transcript.__len__() * 0.8:  # Within 80% of longest
                    longest_transcript = most_recent_long['text']
            
            # Get last sent transcript for final deduplication check
            last_sent = current_session_data.get('last_transcript', '')
            
            # Skip if this transcript was already sent
            if longest_transcript == last_sent:
                logger.debug(f"🔄 Consolidated transcript is same as last sent, skipping: '{longest_transcript[:50]}...'")
                # Clear buffer
                if session_id in active_sessions:
                    active_sessions[session_id]['transcript_buffer'] = []
                    active_sessions[session_id]['consolidation_timer'] = None
                return
                
            # Skip if this is a substring of what was already sent
            if last_sent and longest_transcript in last_sent:
                logger.debug(f"🔄 Consolidated transcript is substring of last sent, skipping: '{longest_transcript[:50]}...'")
                # Clear buffer
                if session_id in active_sessions:
                    active_sessions[session_id]['transcript_buffer'] = []
                    active_sessions[session_id]['consolidation_timer'] = None
                return
            
            # Send the consolidated transcript
            logger.debug(f"✅ Sending consolidated transcript: '{longest_transcript[:100]}{'...' if len(longest_transcript) > 100 else ''}' (length: {len(longest_transcript)})")
            
            message = {
                'type': 'transcript',
                'data': longest_transcript
            }
            
            try:
                await websocket.send_text(json.dumps(message))
                logger.debug(f"📤 WEBSOCKET_SEND - client_id: {session_id}, message_type: transcript, length: {len(longest_transcript)}")
                
                # Update session state
                if session_id in active_sessions:
                    active_sessions[session_id]['last_transcript'] = longest_transcript
                    active_sessions[session_id]['transcript_buffer'] = []
                    active_sessions[session_id]['consolidation_timer'] = None
                    
            except Exception as send_error:
                logger.error(f"❌ Error sending consolidated transcript: {send_error}")
        
        # Start consolidation timer
        consolidation_timer = asyncio.create_task(consolidate_and_send())
        
        # Update session state with new buffer and timer
        if session_id in active_sessions:
            active_sessions[session_id]['transcript_buffer'] = transcript_buffer
            active_sessions[session_id]['last_chunk_time'] = current_time
            active_sessions[session_id]['consolidation_timer'] = consolidation_timer
            
        logger.debug(f"⏰ Set consolidation timer for 1.5 seconds")
        
    except Exception as e:
        logger.error(f"❌ Error in transcript buffering: {str(e)}")
        # Fallback: send transcript immediately
        message = {
            'type': 'transcript',
            'data': transcript_text
        }
        try:
            await websocket.send_text(json.dumps(message))
        except:
            pass

async def listen_to_adk(websocket: WebSocket, runner: Runner, queue: LiveRequestQueue, session_id: str):
    """Listen to ADK events and send to client - Design section 3.4"""
    try:
        logger.debug(f"🎧 Starting ADK listener for session: {session_id}")
        logger.debug(f"📊 Session data keys: {list(active_sessions[session_id].keys())}")
        
        try:
            async for event in runner.run_live(
                session=active_sessions[session_id]['session'],
                live_request_queue=queue,
                run_config=active_sessions[session_id]['run_config']
            ):
                # Log ADK event received as per design table
                event_type = type(event).__name__
                logger.debug(f"ADK_EVENT_RECV - client_id: {session_id}, event_type: {event_type}")
                logger.debug(f"🔍 Event details: {event}")
                
                # Handle different event types as per design section 3.4
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        # Handle text responses (ON_TRANSCRIPT equivalent)
                        if hasattr(part, 'text') and part.text:
                            transcript_text = part.text.strip()
                            
                            # Skip empty or very short transcripts
                            if len(transcript_text) < 2:
                                logger.debug(f"⏭️ Skipping very short transcript: '{transcript_text}'")
                                continue
                                
                            # Use advanced buffering to handle streaming chunks
                            await process_transcript_with_buffering(websocket, session_id, transcript_text)
                        
                        # Handle audio responses (ON_AUDIO equivalent)
                        elif hasattr(part, 'inline_data') and part.inline_data:
                            audio_base64 = base64.b64encode(part.inline_data.data).decode()
                            message = {
                                'type': 'audio_chunk', 
                                'data': audio_base64
                            }
                            await websocket.send_text(json.dumps(message))
                            logger.debug(f"WEBSOCKET_SEND - client_id: {session_id}, message_type: audio_chunk, message_size: {len(audio_base64)}")
                
                # Handle turn completion
                if hasattr(event, 'actions') and event.actions and event.actions.state_delta:
                    if event.actions.state_delta.get("turn_complete", False):
                        message = {
                            'type': 'turn_complete',
                            'data': {}
                        }
                        await websocket.send_text(json.dumps(message))
                        logger.debug(f"WEBSOCKET_SEND - client_id: {session_id}, message_type: turn_complete")
                    
                    # Handle interruption
                    if event.actions.state_delta.get("interrupted", False):
                        message = {
                            'type': 'interrupted', 
                            'data': {}
                        }
                        await websocket.send_text(json.dumps(message))
                        logger.debug(f"WEBSOCKET_SEND - client_id: {session_id}, message_type: interrupted")
        
        except Exception as adk_error:
            logger.error(f"❌ ADK runner.run_live error for {session_id}: {str(adk_error)}")
            logger.error(f"📍 ADK error details:", exc_info=True)
            # Send error to client
            try:
                error_message = {
                    'type': 'error',
                    'data': {'error_message': f'ADK Live API error: {str(adk_error)}'}
                }
                await websocket.send_text(json.dumps(error_message))
            except:
                pass
                    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected during ADK listening: {session_id}")
    except Exception as e:
        logger.error(f"ADK_ERROR - client_id: {session_id}, error_message: {str(e)}")
        # Send error to client
        try:
            error_message = {
                'type': 'error',
                'data': {'error_message': str(e)}
            }
            await websocket.send_text(json.dumps(error_message))
        except:
            pass  # Client may be disconnected

async def handle_test_mode(websocket: WebSocket, client_id: str, session_id: str):
    """Handle test mode connections without ADK"""
    try:
        logger.info(f"🧪 Starting test mode for client: {client_id}")
        
        # Store minimal session info
        active_sessions[session_id] = {
            'client_id': client_id,
            'session_id': session_id,
            'test_mode': True,
            'created_at': time.time()
        }
        
        # Listen for messages
        async for message in websocket.iter_bytes():
            logger.debug(f"📥 Test mode received: {len(message)} bytes from {client_id}")
            
            # Echo response
            response = {
                'type': 'test_echo',
                'data': {
                    'received_bytes': len(message),
                    'message': f'Echo from server - received {len(message)} bytes'
                }
            }
            await websocket.send_text(json.dumps(response))
            logger.debug(f"📤 Test mode sent echo response to {client_id}")
            
    except Exception as e:
        logger.error(f"❌ Test mode error for {client_id}: {str(e)}")
    finally:
        if session_id in active_sessions:
            del active_sessions[session_id]
        logger.info(f"🧪 Test mode ended for client: {client_id}")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Main WebSocket endpoint as per design section 3.3"""
    session_id = None
    
    try:
        logger.debug(f"🔌 New WebSocket connection attempt from client_id: {client_id}")
        logger.debug(f"📍 WebSocket headers: {dict(websocket.headers)}")
        logger.debug(f"🌐 WebSocket URL: {websocket.url}")
        
        # Accept WebSocket connection
        await websocket.accept()
        logger.debug(f"✅ WebSocket connection accepted for client_id: {client_id}")
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Log connection as per design table
        logger.info(f"WEBSOCKET_CONNECT - client_id: {client_id}, session_id: {session_id}")
        logger.debug(f"🆔 Generated session_id: {session_id} for client: {client_id}")
        
        # Send welcome message
        welcome_message = {
            'type': 'connected',
            'data': {
                'session_id': session_id,
                'message': 'WebSocket connected successfully!'
            }
        }
        await websocket.send_text(json.dumps(welcome_message))
        logger.debug(f"📤 Sent welcome message to client: {client_id}")
        
        # Check if this is a simple test client (no ADK needed)
        if client_id.startswith('test_') or client_id.startswith('debug_'):
            logger.info(f"🧪 Test mode detected for client: {client_id} - skipping ADK initialization")
            await handle_test_mode(websocket, client_id, session_id)
            return
        
        logger.info(f"🎤 Voice mode detected for client: {client_id} - initializing ADK")
        
        # Initialize Travel Concierge agent
        logger.debug(f"🤖 Initializing Travel Concierge agent for session: {session_id}")
        try:
            agent = define_travel_agent()
            logger.debug(f"✅ Agent initialized: {agent.name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agent: {str(e)}")
            error_message = {
                'type': 'error',
                'data': {'error_message': f'Agent initialization failed: {str(e)}'}
            }
            await websocket.send_text(json.dumps(error_message))
            return
        
        # Create session service and session
        logger.debug(f"🗂️ Creating session service for session: {session_id}")
        try:
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="travel_concierge_voice",
                user_id=client_id,
                session_id=session_id
            )
            logger.debug(f"✅ Session created: {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create session: {str(e)}")
            error_message = {
                'type': 'error',
                'data': {'error_message': f'Session creation failed: {str(e)}'}
            }
            await websocket.send_text(json.dumps(error_message))
            return
        
        # Create Live Request Queue
        logger.debug(f"📥 Creating Live Request Queue for session: {session_id}")
        try:
            request_queue = LiveRequestQueue()
            logger.debug(f"✅ Request queue created")
        except Exception as e:
            logger.error(f"❌ Failed to create request queue: {str(e)}")
            error_message = {
                'type': 'error',
                'data': {'error_message': f'Request queue creation failed: {str(e)}'}
            }
            await websocket.send_text(json.dumps(error_message))
            return
        
        # Create Run Config with simplified config first
        logger.debug(f"⚙️ Creating RunConfig with simplified config for session: {session_id}")
        try:
            # First try with both TEXT and AUDIO response modalities
            run_config = RunConfig(
                streaming_mode=StreamingMode.BIDI,
                response_modalities=["TEXT", "AUDIO"],  # Enable both text and audio responses
                voice_config=types.VoiceConfig(voice_name=VOICE_NAME)  # Add voice configuration
            )
            logger.debug(f"✅ RunConfig created with TEXT and AUDIO response modalities")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create RunConfig with AUDIO, falling back to TEXT-only: {str(e)}")
            try:
                # Fallback to TEXT-only mode if AUDIO fails
                run_config = RunConfig(
                    streaming_mode=StreamingMode.BIDI,
                    response_modalities=["TEXT"]  # TEXT-only fallback
                )
                logger.debug(f"✅ RunConfig created with TEXT-only fallback")
            except Exception as e2:
                logger.error(f"❌ Failed to create even TEXT-only RunConfig: {str(e2)}")
                error_message = {
                    'type': 'error',
                    'data': {'error_message': f'RunConfig creation failed: {str(e2)}'}
                }
                await websocket.send_text(json.dumps(error_message))
                return
        
        # Create Runner
        logger.debug(f"🏃 Creating Runner for session: {session_id}")
        runner = Runner(
            app_name="travel_concierge_voice",
            agent=agent,
            session_service=session_service,
        )
        logger.debug(f"✅ Runner created")
        
        # Store session info with advanced transcript tracking
        active_sessions[session_id] = {
            'client_id': client_id,
            'session': session,
            'runner': runner,
            'request_queue': request_queue,
            'run_config': run_config,
            'created_at': time.time(),
            'last_transcript': '',  # Track last complete transcript
            'transcript_buffer': [],  # Buffer for streaming chunks
            'last_chunk_time': time.time(),  # Time of last chunk
            'consolidation_timer': None  # Timer for consolidation
        }
        
        # Log ADK session start as per design table
        logger.info(f"ADK_SESSION_START - client_id: {client_id}, session_id: {session_id}")
        
        # Send simple initial greeting to start conversation
        logger.debug(f"📤 Sending simple initial greeting to ADK for session: {session_id}")
        try:
            # Send simple text message to initialize
            initial_greeting = types.Content(
                parts=[types.Part(text="Hello")],
                role="user"
            )
            request_queue.send_content(initial_greeting)
            logger.debug(f"✅ Initial greeting sent successfully for session: {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send initial greeting: {str(e)}")
            error_message = {
                'type': 'error',
                'data': {'error_message': f'Failed to send initial greeting: {str(e)}'}
            }
            await websocket.send_text(json.dumps(error_message))
        
        # Create two concurrent tasks as per design section 3.3
        listen_client_task = asyncio.create_task(
            listen_to_client(websocket, request_queue, session_id)
        )
        listen_adk_task = asyncio.create_task(
            listen_to_adk(websocket, runner, request_queue, session_id)
        )
        
        # Run both tasks concurrently
        await asyncio.gather(listen_client_task, listen_adk_task)
        
    except WebSocketDisconnect:
        logger.info(f"WEBSOCKET_DISCONNECT - client_id: {client_id}, session_id: {session_id}")
        logger.debug(f"🔌 WebSocket disconnected normally for client: {client_id}")
    except Exception as e:
        logger.error(f"❌ Error in WebSocket for {client_id}: {str(e)}")
        logger.error(f"📍 Exception details:", exc_info=True)
        logger.debug(f"💥 WebSocket error for session_id: {session_id}, client: {client_id}")
    finally:
        # Cleanup resources as per design section 3.3
        if session_id and session_id in active_sessions:
            try:
                # Cancel any active consolidation timer
                session_data = active_sessions[session_id]
                consolidation_timer = session_data.get('consolidation_timer', None)
                if consolidation_timer:
                    consolidation_timer.cancel()
                    logger.debug(f"⏰ Cancelled consolidation timer during cleanup")
                
                # Close live request queue
                active_sessions[session_id]['request_queue'].close()
            except:
                pass
            
            # Remove from active sessions
            del active_sessions[session_id]
            
            logger.info(f"ADK_SESSION_END - client_id: {client_id}, session_id: {session_id}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "server_time": time.time()
    }

@app.get("/status")
async def server_status():
    """Server status endpoint"""
    return {
        "server": "Travel Concierge Voice Chat Server",
        "version": "1.0.0",
        "active_sessions": len(active_sessions),
        "model": MODEL,
        "voice": VOICE_NAME,
        "uptime": time.time()
    }

@app.get("/")
async def web_test_interface():
    """Serve web test interface"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/voice_chat_test.html")

@app.get("/test")
async def redirect_to_test():
    """Redirect to test interface"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/voice_chat_test.html")

def run_server(host: str = "0.0.0.0", port: int = 8003):
    """Run the unified voice server"""
    logger.info(f"🚀 Starting Travel Concierge Voice Chat Server on {host}:{port}")
    logger.info(f"📋 WebSocket endpoint: ws://{host}:{port}/ws/{{client_id}}")
    logger.info(f"🏥 Health check: http://{host}:{port}/health")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()