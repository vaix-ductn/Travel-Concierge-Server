#!/usr/bin/env python3
"""Minimal test - just connect and wait for messages"""

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

async def minimal_test():
    """Just connect and see what happens"""
    
    url = 'wss://voice-chat-adk-bridge-ocumylrfdq-uc.a.run.app'
    
    print(f"Minimal test: {url}")
    print("="*40)
    
    try:
        print("Connecting...")
        websocket = await asyncio.wait_for(
            websockets.connect(url, subprotocols=['voice-chat']),
            timeout=10
        )
        print("Connected! Waiting for messages...")
        
        # Just listen for messages
        message_count = 0
        try:
            async for message in websocket:
                message_count += 1
                print(f"\\nMessage {message_count}:")
                
                try:
                    data = json.loads(message)
                    print(f"  Type: {data.get('type', 'unknown')}")
                    if 'message' in data:
                        print(f"  Message: {data['message']}")
                    if 'session_id' in data:
                        print(f"  Session: {data['session_id'][:20]}...")
                except:
                    print(f"  Raw: {message[:100]}...")
                
                # Stop after first few messages to avoid timeout issues
                if message_count >= 3:
                    print("\\nStopping after 3 messages")
                    break
                    
        except Exception as e:
            print(f"\\nMessage loop error: {e}")
        
        await websocket.close()
        print("\\nConnection closed normally")
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def main():
    try:
        success = asyncio.run(minimal_test())
        print(f"\\nResult: {'SUCCESS' if success else 'FAILED'}")
        return 0 if success else 1
    except Exception as e:
        print(f"Test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())