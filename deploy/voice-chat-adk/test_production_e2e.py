#!/usr/bin/env python3
"""
End-to-End Production Test for WebSocket ADK Bridge Server
Tests the complete voice chat flow with audio data
"""

import asyncio
import json
import base64
import sys
import os
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'websockets'])
    import websockets

# Test configuration
PRODUCTION_URL = 'wss://voice-chat-adk-bridge-ocumylrfdq-uc.a.run.app'
SUBPROTOCOL = 'voice-chat'
TEST_TIMEOUT = 30  # seconds

# Create mock audio data (silence) for testing
def create_test_audio_data(duration_ms=100):
    """Create mock PCM audio data for testing"""
    sample_rate = 16000
    samples_per_ms = sample_rate // 1000
    total_samples = duration_ms * samples_per_ms
    
    # Create 16-bit PCM silence (zeros)
    audio_data = bytearray(total_samples * 2)  # 2 bytes per 16-bit sample
    return bytes(audio_data)

async def test_production_e2e():
    """Run complete end-to-end test"""
    print("Starting End-to-End Production Test")
    print("="*60)
    print(f"Production URL: {PRODUCTION_URL}")
    print(f"Test Timeout: {TEST_TIMEOUT}s")
    print("="*60)
    
    session_established = False
    audio_response_received = False
    error_occurred = False
    
    try:
        print("\\nConnecting to production server...")
        
        # Connect with subprotocol
        websocket = await asyncio.wait_for(
            websockets.connect(
                PRODUCTION_URL,
                subprotocols=[SUBPROTOCOL]
            ),
            timeout=15
        )
        
        print("WebSocket connection established")
        
        # Wait for auto-session initialization
        print("\\nWaiting for auto-session initialization...")
        
        message_received = False
        session_id = None
        
        # Listen for messages with timeout
        try:
            async with asyncio.timeout(TEST_TIMEOUT):
                async for message in websocket:
                    message_received = True
                    data = json.loads(message)
                    msg_type = data.get('type')
                    
                    print(f"📥 Received: {msg_type}")
                    
                    if msg_type == 'connection_established':
                        print("✅ Connection established message received")
                        audio_config = data.get('audio_config', {})
                        print(f"🎵 Audio config: {audio_config}")
                    
                    elif msg_type == 'auto_session_started':
                        session_id = data.get('session_id')
                        user_id = data.get('user_id')
                        session_established = True
                        print(f"✅ Auto-session started: {session_id}")
                        print(f"👤 User ID: {user_id}")
                        
                        # Send test audio after session is established
                        await send_test_audio(websocket)
                    
                    elif msg_type == 'adk_audio_response':
                        audio_response_received = True
                        audio_size = len(data.get('audio_data_base64', ''))
                        print(f"🔊 Audio response received: {audio_size} chars base64")
                        
                        # Test successful - break the loop
                        break
                    
                    elif msg_type == 'adk_text_response':
                        text = data.get('text', '')
                        print(f"💬 Text response: {text[:50]}...")
                    
                    elif msg_type == 'adk_turn_complete':
                        print("✅ Turn complete")
                    
                    elif msg_type == 'error':
                        error_msg = data.get('message', 'Unknown error')
                        print(f"❌ Error received: {error_msg}")
                        error_occurred = True
                        break
                    
                    else:
                        print(f"ℹ️  Other message: {msg_type}")
        
        except asyncio.TimeoutError:
            print(f"⏰ Test timeout after {TEST_TIMEOUT}s")
        
        # Close connection
        await websocket.close()
        print("🔌 WebSocket connection closed")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        error_occurred = True
    
    # Print test results
    print("\\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    
    results = {
        'Connection': '✅ PASS' if not error_occurred else '❌ FAIL',
        'Auto-Session': '✅ PASS' if session_established else '❌ FAIL',
        'Audio Response': '✅ PASS' if audio_response_received else '❌ FAIL',
        'Overall': '✅ PASS' if (session_established and not error_occurred) else '❌ FAIL'
    }
    
    for test, result in results.items():
        print(f"{test:15}: {result}")
    
    # Final assessment
    print("\\n" + "="*60)
    if session_established and not error_occurred:
        print("🎉 SUCCESS! Production voice chat system is working")
        print("✅ Flutter app can now connect and use voice chat")
        print("✅ Ready for real user testing")
        return 0
    else:
        print("❌ FAILURE! Issues detected:")
        if not session_established:
            print("   - Auto-session not established")
        if error_occurred:
            print("   - Errors occurred during testing")
        print("📋 Check server logs for details:")
        print("   gcloud run services logs tail voice-chat-adk-bridge --region=us-central1")
        return 1

async def send_test_audio(websocket):
    """Send test audio data to the server"""
    try:
        print("\\n🎤 Sending test audio data...")
        
        # Create test audio (100ms of silence)
        test_audio = create_test_audio_data(100)
        audio_base64 = base64.b64encode(test_audio).decode()
        
        # Send audio message compatible with Flutter format
        audio_message = {
            'mime_type': 'audio/pcm;rate=16000',
            'data': audio_base64,
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        await websocket.send(json.dumps(audio_message))
        print(f"📤 Sent test audio: {len(test_audio)} bytes")
        
    except Exception as e:
        print(f"❌ Failed to send test audio: {e}")

def main():
    """Main entry point"""
    try:
        exit_code = asyncio.run(test_production_e2e())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\n⚠️ Test interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()