#!/usr/bin/env python3
"""Simple End-to-End Production Test for WebSocket ADK Bridge Server"""

import asyncio
import json
import base64
import sys

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'websockets'])
    import websockets

PRODUCTION_URL = 'wss://voice-chat-adk-bridge-ocumylrfdq-uc.a.run.app'
SUBPROTOCOL = 'voice-chat'

def create_test_audio_data():
    """Create mock PCM audio data"""
    # 100ms of 16kHz mono audio (silence)
    samples = 1600  # 16000 * 0.1
    audio_data = bytearray(samples * 2)  # 2 bytes per 16-bit sample
    return bytes(audio_data)

async def test_production():
    """Test production voice chat system"""
    print("Testing Production Voice Chat System")
    print("="*50)
    print(f"URL: {PRODUCTION_URL}")
    print("="*50)
    
    session_started = False
    error_count = 0
    
    try:
        print("\\nConnecting...")
        websocket = await asyncio.wait_for(
            websockets.connect(PRODUCTION_URL, subprotocols=[SUBPROTOCOL]),
            timeout=15
        )
        print("Connected successfully!")
        
        print("\\nWaiting for auto-session...")
        
        # Listen for messages
        message_count = 0
        async for message in websocket:
            message_count += 1
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')
            
            print(f"Message {message_count}: {msg_type}")
            
            if msg_type == 'connection_established':
                print("  Connection confirmed")
            
            elif msg_type == 'auto_session_started':
                session_id = data.get('session_id', 'N/A')
                print(f"  Session started: {session_id[:20]}...")
                session_started = True
                
                # Send test audio
                print("\\nSending test audio...")
                test_audio = create_test_audio_data()
                audio_b64 = base64.b64encode(test_audio).decode()
                
                audio_msg = {
                    'mime_type': 'audio/pcm;rate=16000',
                    'data': audio_b64,
                    'timestamp': 1234567890
                }
                
                await websocket.send(json.dumps(audio_msg))
                print(f"Sent {len(test_audio)} bytes audio")
            
            elif msg_type == 'adk_audio_response':
                audio_size = len(data.get('audio_data_base64', ''))
                print(f"  Audio response: {audio_size} chars")
                print("SUCCESS: Audio response received!")
                break
            
            elif msg_type == 'adk_text_response':
                text = data.get('text', '')[:30]
                print(f"  Text response: {text}...")
            
            elif msg_type == 'error':
                error_msg = data.get('message', 'Unknown')
                print(f"  ERROR: {error_msg}")
                error_count += 1
                break
            
            # Safety limit
            if message_count > 10:
                print("Message limit reached, stopping test")
                break
        
        await websocket.close()
        print("\\nConnection closed")
        
    except Exception as e:
        print(f"Test failed: {e}")
        error_count += 1
    
    # Results
    print("\\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)
    
    if session_started and error_count == 0:
        print("OVERALL: PASS")
        print("- Connection: PASS")
        print("- Auto-session: PASS") 
        print("- Error count: 0")
        print("\\nSUCCESS! Voice chat system is working!")
        return 0
    else:
        print("OVERALL: FAIL")
        print(f"- Session started: {session_started}")
        print(f"- Error count: {error_count}")
        print("\\nCheck server logs for details:")
        print("gcloud run services logs tail voice-chat-adk-bridge --region=us-central1")
        return 1

def main():
    try:
        exit_code = asyncio.run(test_production())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\nTest interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()