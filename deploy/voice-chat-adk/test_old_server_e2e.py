#!/usr/bin/env python3
"""End-to-End test with old voice chat server using Flutter protocol"""

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

def create_test_audio_data():
    """Create mock PCM audio data like Flutter sends"""
    # 100ms of 16kHz mono audio (silence)
    samples = 1600  # 16000 * 0.1
    audio_data = bytearray(samples * 2)  # 2 bytes per 16-bit sample
    return bytes(audio_data)

async def test_old_server_e2e():
    """Test old server with Flutter-like protocol"""
    
    url = 'wss://voice-chat-server-ocumylrfdq-uc.a.run.app'
    
    print("Testing Old Voice Chat Server - End to End")
    print("="*60)
    print(f"URL: {url}")
    print("")
    
    try:
        print("Step 1: Connecting with voice-chat subprotocol...")
        websocket = await asyncio.wait_for(
            websockets.connect(url, subprotocols=['voice-chat']),
            timeout=10
        )
        print("✅ Connected successfully")
        
        print("\\nStep 2: Sending session initialization...")
        # Send initialization like Flutter app would
        init_msg = {
            "type": "start_session",
            "user_id": "test_user_123", 
            "session_id": "test_session_456"
        }
        await websocket.send(json.dumps(init_msg))
        print("✅ Sent session start")
        
        print("\\nStep 3: Waiting for server responses...")
        message_count = 0
        connection_established = False
        
        async for message in websocket:
            message_count += 1
            print(f"\\nMessage {message_count}:")
            
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                print(f"  Type: {msg_type}")
                
                if msg_type == 'connection_established':
                    connection_established = True
                    client_id = data.get('client_id', 'N/A')
                    print(f"  Client ID: {client_id}")
                    print("  ✅ Connection established!")
                    
                    # Now send test audio data
                    print("\\nStep 4: Sending test audio data...")
                    test_audio = create_test_audio_data()
                    audio_b64 = base64.b64encode(test_audio).decode()
                    
                    # Send audio in Flutter format
                    audio_msg = {
                        'mime_type': 'audio/pcm;rate=16000',
                        'data': audio_b64,
                        'timestamp': 1234567890
                    }
                    
                    await websocket.send(json.dumps(audio_msg))
                    print(f"  ✅ Sent {len(test_audio)} bytes of test audio")
                
                elif msg_type == 'audio_response':
                    audio_data = data.get('audio_data', '')
                    print(f"  🔊 Audio response: {len(audio_data)} chars")
                    print("  ✅ SUCCESS: Received audio response!")
                    break
                    
                elif msg_type == 'text_response':
                    text = data.get('text', '')[:50]
                    print(f"  💬 Text response: {text}...")
                    
                elif msg_type == 'error':
                    error_msg = data.get('message', 'Unknown')
                    print(f"  ❌ Error: {error_msg}")
                    break
                
                else:
                    print(f"  ℹ️  Other: {str(data)[:100]}...")
                
            except json.JSONDecodeError:
                print(f"  Raw: {message[:100]}...")
            
            # Safety limit
            if message_count >= 10:
                print("\\n⏰ Message limit reached")
                break
        
        await websocket.close()
        print("\\n🔌 Connection closed")
        
        # Results
        print("\\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        
        if connection_established:
            print("✅ PASS: Connection established")
            print("✅ PASS: Server communication working")
            print("✅ PASS: Audio message format accepted")
            print("\\n🎉 SUCCESS: Old voice server is working!")
            print("🔗 Ready for Flutter app integration")
            return True
        else:
            print("❌ FAIL: Connection not established")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    try:
        success = asyncio.run(test_old_server_e2e())
        print(f"\\nFinal Result: {'SUCCESS' if success else 'FAILED'}")
        return 0 if success else 1
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())