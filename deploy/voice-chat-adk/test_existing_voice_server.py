#!/usr/bin/env python3
"""Test existing voice chat server"""

import asyncio
import json
import sys

try:
    import websockets
    import requests
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'websockets', 'requests'])
    import websockets
    import requests

async def test_existing_voice_server():
    """Test existing voice chat server"""
    
    base_url = 'voice-chat-server-ocumylrfdq-uc.a.run.app'
    https_url = f'https://{base_url}'
    wss_url = f'wss://{base_url}'
    
    print(f"Testing existing voice chat server")
    print("="*50)
    print(f"Base URL: {base_url}")
    print("")
    
    # Test 1: HTTP health check
    print("Test 1: HTTP health endpoints")
    try:
        # Test root endpoint
        response = requests.get(f"{https_url}/", timeout=10)
        print(f"  Root endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.text[:100]}...")
        
        # Test health endpoint
        response = requests.get(f"{https_url}/health/", timeout=10)
        print(f"  Health endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"  HTTP test failed: {e}")
    
    print("")
    
    # Test 2: WebSocket connection
    print("Test 2: WebSocket connection")
    try:
        # Test basic WebSocket connection
        print("  Testing basic WebSocket connection...")
        websocket = await asyncio.wait_for(
            websockets.connect(wss_url),
            timeout=10
        )
        print("  Basic connection: SUCCESS")
        await websocket.close()
        
        # Test with voice-chat subprotocol
        print("  Testing with voice-chat subprotocol...")
        websocket = await asyncio.wait_for(
            websockets.connect(wss_url, subprotocols=['voice-chat']),
            timeout=10
        )
        print("  Subprotocol connection: SUCCESS")
        
        # Listen for initial messages
        print("  Waiting for initial messages...")
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"  Received message: {message[:100]}...")
        except asyncio.TimeoutError:
            print("  No initial message (normal for this server)")
        
        await websocket.close()
        
    except Exception as e:
        print(f"  WebSocket test failed: {e}")
    
    print("")
    
    # Test 3: Voice chat protocol test
    print("Test 3: Voice chat protocol test")
    try:
        websocket = await asyncio.wait_for(
            websockets.connect(wss_url, subprotocols=['voice-chat']),
            timeout=10
        )
        
        # Send session start message
        session_msg = {
            "type": "start_session",
            "user_id": "test_user_123",
            "session_id": "test_session_456"
        }
        
        await websocket.send(json.dumps(session_msg))
        print("  Sent session start message")
        
        # Wait for response
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            print(f"  Received response: {response[:100]}...")
        except asyncio.TimeoutError:
            print("  No response to session start (may be normal)")
        
        await websocket.close()
        print("  Voice chat protocol test completed")
        
    except Exception as e:
        print(f"  Voice chat protocol test failed: {e}")
    
    print("")
    print("="*50)
    print("CONCLUSION:")
    print("If HTTP and WebSocket tests pass, this server can be used for Flutter app")
    print(f"WebSocket URL for Flutter: {wss_url}")

def main():
    try:
        asyncio.run(test_existing_voice_server())
        return 0
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())