#!/usr/bin/env python3
"""Test WebSocket connection directly without subprotocol"""

import asyncio
import sys

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'websockets'])
    import websockets

async def test_direct_websocket():
    """Test direct WebSocket connection"""
    
    url = 'wss://voice-chat-adk-bridge-ocumylrfdq-uc.a.run.app'
    
    print(f"Testing direct WebSocket connection to: {url}")
    print("="*60)
    
    # Test 1: Without subprotocol
    print("\\nTest 1: Connection without subprotocol")
    try:
        websocket = await asyncio.wait_for(
            websockets.connect(url),
            timeout=10
        )
        print("SUCCESS: Connected without subprotocol")
        await websocket.close()
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 2: With subprotocol
    print("\\nTest 2: Connection with voice-chat subprotocol")
    try:
        websocket = await asyncio.wait_for(
            websockets.connect(url, subprotocols=['voice-chat']),
            timeout=10
        )
        print("SUCCESS: Connected with subprotocol")
        await websocket.close()
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 3: With wrong subprotocol
    print("\\nTest 3: Connection with wrong subprotocol")
    try:
        websocket = await asyncio.wait_for(
            websockets.connect(url, subprotocols=['wrong-protocol']),
            timeout=10
        )
        print("SUCCESS: Connected with wrong subprotocol (unexpected)")
        await websocket.close()
    except Exception as e:
        print(f"FAILED (expected): {e}")
    
    print("\\n" + "="*60)
    print("ANALYSIS:")
    print("- If Test 1 succeeds: Server is running but has subprotocol issues")
    print("- If Test 2 succeeds: Everything is working fine")
    print("- If all fail: Server is not running or has major issues")

def main():
    try:
        asyncio.run(test_direct_websocket())
        return 0
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())