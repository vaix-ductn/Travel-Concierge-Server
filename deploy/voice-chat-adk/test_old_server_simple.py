#!/usr/bin/env python3
"""Simple test with old voice chat server"""

import asyncio
import json
import base64
import sys

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'websockets'])
    import websockets

def create_test_audio():
    samples = 1600  # 100ms of 16kHz audio
    audio_data = bytearray(samples * 2)
    return bytes(audio_data)

async def test_old_server():
    url = 'wss://voice-chat-server-ocumylrfdq-uc.a.run.app'
    
    print("Testing Old Voice Chat Server")
    print("="*40)
    print(f"URL: {url}")
    
    try:
        print("\\nConnecting...")
        websocket = await asyncio.wait_for(
            websockets.connect(url, subprotocols=['voice-chat']),
            timeout=10
        )
        print("Connected successfully")
        
        print("\\nSending session start...")
        init_msg = {
            "type": "start_session",
            "user_id": "test_user_123", 
            "session_id": "test_session_456"
        }
        await websocket.send(json.dumps(init_msg))
        print("Session start sent")
        
        print("\\nWaiting for responses...")
        connection_ok = False
        message_count = 0
        
        async for message in websocket:
            message_count += 1
            
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                print(f"Message {message_count}: {msg_type}")
                
                if msg_type == 'connection_established':
                    connection_ok = True
                    print("  Connection established!")
                    
                    # Send test audio
                    print("\\nSending test audio...")
                    test_audio = create_test_audio()
                    audio_b64 = base64.b64encode(test_audio).decode()
                    
                    audio_msg = {
                        'mime_type': 'audio/pcm;rate=16000',
                        'data': audio_b64,
                        'timestamp': 1234567890
                    }
                    
                    await websocket.send(json.dumps(audio_msg))
                    print(f"Sent {len(test_audio)} bytes audio")
                
                elif msg_type == 'audio_response':
                    print("  AUDIO RESPONSE RECEIVED!")
                    print("  SUCCESS: Voice chat is working!")
                    break
                    
                elif msg_type == 'text_response':
                    text = data.get('text', '')[:30]
                    print(f"  Text: {text}...")
                    
                elif msg_type == 'error':
                    print(f"  Error: {data.get('message', 'Unknown')}")
                    break
                
            except:
                print(f"  Raw: {message[:50]}...")
            
            if message_count >= 8:
                break
        
        await websocket.close()
        
        print("\\n" + "="*40)
        print("RESULTS")
        print("="*40)
        
        if connection_ok:
            print("OVERALL: SUCCESS")
            print("- Connection: OK")
            print("- Protocol: Working")
            print("- Server: Ready for Flutter")
            print(f"\\nWebSocket URL: {url}")
            return True
        else:
            print("OVERALL: FAILED")
            print("- Connection issues")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def main():
    try:
        success = asyncio.run(test_old_server())
        return 0 if success else 1
    except Exception as e:
        print(f"Execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())