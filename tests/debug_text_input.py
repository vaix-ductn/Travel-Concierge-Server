#!/usr/bin/env python3
"""
Debug script để test text input processing
"""
import asyncio
import json
import websockets
import time

async def test_text_input():
    """Test text input functionality"""
    print("🧪 Testing text input processing...")

    websocket_url = "ws://localhost:8003"

    try:
        # Connect to WebSocket
        websocket = await websockets.connect(websocket_url, subprotocols=["voice-chat"])
        print("✅ Connected to WebSocket server")

        # Wait for connection established message
        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        data = json.loads(message)
        print(f"📥 Connection: {data}")

        # Wait for auto-session creation
        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        data = json.loads(message)
        print(f"📥 Session: {data}")

        if data.get('type') == 'auto_session_started':
            print("✅ Auto-session created successfully")

            # Send text input
            text_message = {
                'type': 'text_input',
                'text': 'Xin chào! Tôi muốn du lịch Nhật Bản.',
                'timestamp': int(time.time() * 1000)
            }

            await websocket.send(json.dumps(text_message))
            print("📤 Sent text input message")

            # Wait for response or error
            timeout = 10.0
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    print(f"📥 Response: {data}")

                    if data.get('type') == 'error':
                        print(f"❌ Error: {data.get('message')}")
                        break
                    elif data.get('type') in ['adk_text_response', 'adk_audio_response']:
                        print("✅ Received AI response!")
                        break

                except asyncio.TimeoutError:
                    print("⏰ Waiting for response...")
                    continue

            print("🏁 Test completed")

        await websocket.close()

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_text_input())