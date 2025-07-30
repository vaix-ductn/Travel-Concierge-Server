#!/usr/bin/env python3
"""Simple WebSocket connection test"""

import asyncio
import sys

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'websockets'])
    import websockets

async def test_connection():
    try:
        print("Testing WebSocket connection...")
        websocket = await asyncio.wait_for(
            websockets.connect(
                'ws://localhost:8004',
                subprotocols=['voice-chat']
            ),
            timeout=10
        )
        print("WebSocket connection successful!")
        await websocket.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

async def main():
    success = await test_connection()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())