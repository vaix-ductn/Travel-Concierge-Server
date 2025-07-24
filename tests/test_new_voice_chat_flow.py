#!/usr/bin/env python3
"""
Test Script for New Simplified Voice Chat Flow
Tests auto-session management and simplified user experience
"""
import os
import sys
import asyncio
import logging
import json
import base64
import time
import signal
import websockets
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_status(message: str, status: str = "INFO"):
    """Print colored status messages"""
    colors = {
        "INFO": "\033[0;34m",      # Blue
        "SUCCESS": "\033[0;32m",   # Green
        "WARNING": "\033[1;33m",   # Yellow
        "ERROR": "\033[0;31m",     # Red
        "RESET": "\033[0m"         # Reset
    }

    color = colors.get(status, colors["INFO"])
    reset = colors["RESET"]
    print(f"{color}[{status}] {message}{reset}")

class VoiceChatFlowTester:
    """Test the new simplified voice chat flow"""

    def __init__(self):
        self.websocket_url = "ws://192.168.1.8:8003"
        self.websocket = None
        self.session_id = None
        self.user_id = None
        self.messages_received = []
        self.auto_session_ready = False

    async def run_complete_flow_test(self):
        """Test the complete simplified voice chat flow"""
        print_status("Starting New Voice Chat Flow Test", "INFO")

        tests = [
            self.test_auto_connection,
            self.test_auto_session_creation,
            self.test_audio_streaming,
            self.test_ai_responses,
            self.test_auto_cleanup,
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            try:
                print_status(f"Running {test.__name__}...", "INFO")
                success = await test()
                if success:
                    print_status(f"✅ {test.__name__} PASSED", "SUCCESS")
                    passed += 1
                else:
                    print_status(f"❌ {test.__name__} FAILED", "ERROR")
            except Exception as e:
                print_status(f"❌ {test.__name__} ERROR: {str(e)}", "ERROR")

        print_status(f"Test Results: {passed}/{total} tests passed",
                    "SUCCESS" if passed == total else "WARNING")
        return passed == total

    async def test_auto_connection(self) -> bool:
        """Test automatic WebSocket connection"""
        try:
            print_status("Connecting to WebSocket server...", "INFO")

            self.websocket = await websockets.connect(
                self.websocket_url,
                subprotocols=["voice-chat"]
            )

            # Wait for connection established message
            message = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            data = json.loads(message)

            if data.get('type') == 'connection_established':
                print_status(f"Connection established with config: {data.get('audio_config')}", "SUCCESS")
                return True
            else:
                print_status(f"Unexpected connection message: {data}", "ERROR")
                return False

        except Exception as e:
            print_status(f"Connection failed: {str(e)}", "ERROR")
            return False

    async def test_auto_session_creation(self) -> bool:
        """Test automatic session creation by server"""
        try:
            print_status("Waiting for auto-session creation...", "INFO")

            # Wait for auto_session_started message
            message = await asyncio.wait_for(self.websocket.recv(), timeout=15.0)
            data = json.loads(message)

            if data.get('type') == 'auto_session_started':
                self.session_id = data.get('session_id')
                self.user_id = data.get('user_id')
                self.auto_session_ready = True

                print_status(f"Auto-session created successfully:", "SUCCESS")
                print_status(f"  Session ID: {self.session_id}", "INFO")
                print_status(f"  User ID: {self.user_id}", "INFO")
                print_status(f"  Status: {data.get('status')}", "INFO")

                return True
            else:
                print_status(f"Expected auto_session_started, got: {data}", "ERROR")
                return False

        except asyncio.TimeoutError:
            print_status("Timeout waiting for auto-session creation", "ERROR")
            return False
        except Exception as e:
            print_status(f"Auto-session creation failed: {str(e)}", "ERROR")
            return False

    async def test_audio_streaming(self) -> bool:
        """Test audio streaming to server"""
        try:
            if not self.auto_session_ready:
                print_status("Auto-session not ready for audio streaming", "ERROR")
                return False

            print_status("Testing audio streaming...", "INFO")

            # Create sample audio data (16kHz PCM)
            sample_rate = 16000
            duration = 1.0  # 1 second
            samples = int(sample_rate * duration)

            # Generate a simple sine wave (440Hz A note)
            import math
            audio_data = []
            for i in range(samples):
                # Generate 16-bit PCM sine wave
                sample = int(32767 * 0.3 * math.sin(2 * math.pi * 440 * i / sample_rate))
                # Convert to little-endian bytes
                audio_data.extend([sample & 0xFF, (sample >> 8) & 0xFF])

            audio_bytes = bytes(audio_data)

            # Send audio chunk using ADK protocol
            audio_message = {
                'mime_type': 'audio/pcm;rate=16000',
                'data': base64.b64encode(audio_bytes).decode('utf-8'),
                'timestamp': int(time.time() * 1000)
            }

            await self.websocket.send(json.dumps(audio_message))
            print_status(f"Sent audio chunk: {len(audio_bytes)} bytes", "SUCCESS")

            # Wait a bit for processing
            await asyncio.sleep(2.0)

            return True

        except Exception as e:
            print_status(f"Audio streaming failed: {str(e)}", "ERROR")
            return False

    async def test_ai_responses(self) -> bool:
        """Test AI responses from server"""
        try:
            print_status("Testing AI responses...", "INFO")

            # Send a text message to trigger AI response
            text_message = {
                'type': 'text_input',
                'text': 'Xin chào! Tôi muốn du lịch Nhật Bản.',
                'timestamp': int(time.time() * 1000)
            }

            await self.websocket.send(json.dumps(text_message))
            print_status("Sent text message to trigger AI response", "INFO")

            # Listen for responses for up to 30 seconds
            timeout = 30.0
            start_time = time.time()

            received_text = False
            received_audio = False
            turn_complete = False

            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                    data = json.loads(message)

                    message_type = data.get('type')

                    if message_type == 'adk_text_response':
                        text = data.get('text', '')
                        print_status(f"Received text response: {text[:100]}...", "SUCCESS")
                        received_text = True

                    elif message_type == 'adk_audio_response':
                        audio_size = data.get('audio_size', 0)
                        print_status(f"Received audio response: {audio_size} bytes", "SUCCESS")
                        received_audio = True

                    elif message_type == 'adk_turn_complete':
                        print_status("Turn completed", "SUCCESS")
                        turn_complete = True
                        break

                    elif message_type == 'adk_tool_call':
                        tool_name = data.get('tool_name', 'unknown')
                        print_status(f"Tool call: {tool_name}", "INFO")

                    elif message_type == 'error':
                        print_status(f"Server error: {data.get('message')}", "ERROR")
                        return False

                except asyncio.TimeoutError:
                    # Continue listening
                    continue

            # Check if we received appropriate responses
            if received_text or received_audio:
                print_status("AI responses received successfully", "SUCCESS")
                return True
            else:
                print_status("No AI responses received within timeout", "WARNING")
                return False

        except Exception as e:
            print_status(f"AI response test failed: {str(e)}", "ERROR")
            return False

    async def test_auto_cleanup(self) -> bool:
        """Test automatic cleanup when connection closes"""
        try:
            print_status("Testing auto-cleanup...", "INFO")

            # Close the WebSocket connection
            await self.websocket.close()

            print_status("WebSocket connection closed", "SUCCESS")
            print_status("Server should auto-cleanup session", "INFO")

            # Try to reconnect to verify session was cleaned up
            await asyncio.sleep(1.0)

            try:
                test_websocket = await websockets.connect(
                    self.websocket_url,
                    subprotocols=["voice-chat"]
                )

                # Should get a new session
                message = await asyncio.wait_for(test_websocket.recv(), timeout=5.0)
                data = json.loads(message)

                if data.get('type') == 'connection_established':
                    print_status("New connection established successfully", "SUCCESS")

                    # Wait for new auto-session
                    message = await asyncio.wait_for(test_websocket.recv(), timeout=10.0)
                    data = json.loads(message)

                    if data.get('type') == 'auto_session_started':
                        new_session_id = data.get('session_id')
                        if new_session_id != self.session_id:
                            print_status(f"New session created: {new_session_id}", "SUCCESS")
                            await test_websocket.close()
                            return True
                        else:
                            print_status("Session ID not cleaned up properly", "ERROR")
                            await test_websocket.close()
                            return False
                    else:
                        print_status("New auto-session not created", "ERROR")
                        await test_websocket.close()
                        return False
                else:
                    print_status("Reconnection failed", "ERROR")
                    await test_websocket.close()
                    return False

            except Exception as e:
                print_status(f"Reconnection test failed: {str(e)}", "ERROR")
                return False

        except Exception as e:
            print_status(f"Auto-cleanup test failed: {str(e)}", "ERROR")
            return False

async def main():
    """Main test runner"""
    print_status("New Voice Chat Flow Test Suite", "INFO")
    print_status("=" * 50, "INFO")

    tester = VoiceChatFlowTester()

    try:
        success = await tester.run_complete_flow_test()

        print_status("=" * 50, "INFO")
        if success:
            print_status("🎉 ALL TESTS PASSED - Voice Chat Flow Working!", "SUCCESS")
            return 0
        else:
            print_status("❌ SOME TESTS FAILED - Need fixes", "ERROR")
            return 1

    except KeyboardInterrupt:
        print_status("Test interrupted by user", "WARNING")
        return 1
    except Exception as e:
        print_status(f"Test suite failed: {str(e)}", "ERROR")
        return 1
    finally:
        if tester.websocket and tester.websocket.close_code is None:
            await tester.websocket.close()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_status("Interrupted", "WARNING")
        sys.exit(1)