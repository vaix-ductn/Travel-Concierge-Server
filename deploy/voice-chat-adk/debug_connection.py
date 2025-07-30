#!/usr/bin/env python3
"""Debug connection to production server"""

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'websockets'])
    import websockets

async def debug_connection():
    """Debug connection issues"""
    url = 'wss://voice-chat-adk-bridge-ocumylrfdq-uc.a.run.app'
    
    print(f"Testing connection to: {url}")
    
    try:
        # Test basic connection first
        print("\\nStep 1: Basic WebSocket connection...")
        websocket = await asyncio.wait_for(
            websockets.connect(url),
            timeout=10
        )
        print("Basic connection: OK")
        await websocket.close()
        
        # Test with subprotocol
        print("\\nStep 2: Connection with subprotocol...")
        websocket = await asyncio.wait_for(
            websockets.connect(url, subprotocols=['voice-chat']),
            timeout=10
        )
        print("Subprotocol connection: OK")
        
        # Try to receive first message
        print("\\nStep 3: Waiting for first message...")
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=10)
            print(f"First message received: {len(message)} chars")
            
            try:
                data = json.loads(message)
                print(f"Message type: {data.get('type', 'unknown')}")
            except:
                print("Message is not JSON")
                
        except asyncio.TimeoutError:
            print("No message received within 10 seconds")
        
        await websocket.close()
        print("\\nConnection test completed successfully")
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def main():
    try:
        success = asyncio.run(debug_connection())
        if success:
            print("\\nDEBUG: Connection tests passed")
            print("Issue might be in the auto-session initialization")
        else:
            print("\\nDEBUG: Basic connection failed") 
            print("Server might be down or misconfigured")
        return 0 if success else 1
    except Exception as e:
        print(f"Debug failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())