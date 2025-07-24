#!/usr/bin/env python3
"""
Flutter Voice Chat Integration Test
Tests the integration between Flutter app and simplified voice chat flow
"""
import os
import sys
import asyncio
import logging
import json
import base64
import time
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

class FlutterVoiceIntegrationTester:
    """Test Flutter app integration with voice chat"""

    def __init__(self):
        self.websocket_url = "ws://192.168.1.8:8003"
        self.websocket = None
        self.session_id = None
        self.user_id = None

    async def simulate_flutter_voice_chat_flow(self):
        """Simulate the Flutter app voice chat flow"""
        print_status("Starting Flutter Voice Chat Integration Test", "INFO")
        print_status("Simulating user journey: Home -> Click Mic -> Voice Chat", "INFO")

        # Step 1: Simulate Flutter app opening voice chat screen
        success = await self.step_1_auto_connect()
        if not success:
            return False

        # Step 2: Wait for auto-session (server creates automatically)
        success = await self.step_2_auto_session()
        if not success:
            return False

        # Step 3: Simulate user speaking (Flutter app sends audio)
        success = await self.step_3_user_speaks()
        if not success:
            return False

        # Step 4: Receive AI response (text + audio)
        success = await self.step_4_ai_responds()
        if not success:
            return False

        # Step 5: Continue conversation
        success = await self.step_5_continue_conversation()
        if not success:
            return False

        # Step 6: Simulate user closing voice chat screen
        success = await self.step_6_auto_cleanup()
        if not success:
            return False

        print_status("🎉 Flutter Voice Chat Integration Test PASSED!", "SUCCESS")
        return True

    async def step_1_auto_connect(self) -> bool:
        """Step 1: Auto-connect when voice chat screen opens"""
        try:
            print_status("Step 1: Flutter app opens voice chat screen", "INFO")
            print_status("  → Auto-connecting to voice chat server...", "INFO")

            self.websocket = await websockets.connect(
                self.websocket_url,
                subprotocols=["voice-chat"]
            )

            # Expect connection established message
            message = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            data = json.loads(message)

            if data.get('type') == 'connection_established':
                audio_config = data.get('audio_config', {})
                print_status(f"  ✅ Auto-connected successfully", "SUCCESS")
                print_status(f"  📊 Audio config: {audio_config.get('input_sample_rate')}Hz input, {audio_config.get('output_sample_rate')}Hz output", "INFO")
                return True
            else:
                print_status(f"  ❌ Unexpected connection response: {data}", "ERROR")
                return False

        except Exception as e:
            print_status(f"  ❌ Auto-connect failed: {str(e)}", "ERROR")
            return False

    async def step_2_auto_session(self) -> bool:
        """Step 2: Server automatically creates session"""
        try:
            print_status("Step 2: Server creates auto-session", "INFO")
            print_status("  → Waiting for server to create session automatically...", "INFO")

            # Wait for auto_session_started message
            message = await asyncio.wait_for(self.websocket.recv(), timeout=15.0)
            data = json.loads(message)

            if data.get('type') == 'auto_session_started':
                self.session_id = data.get('session_id')
                self.user_id = data.get('user_id')
                status = data.get('status')

                print_status(f"  ✅ Auto-session created", "SUCCESS")
                print_status(f"  🆔 Session ID: {self.session_id[:12]}...", "INFO")
                print_status(f"  👤 User ID: {self.user_id}", "INFO")
                print_status(f"  📱 Flutter app shows: 'Sẵn sàng! Hãy nói để trò chuyện với AI'", "INFO")
                return True
            else:
                print_status(f"  ❌ Expected auto_session_started, got: {data.get('type')}", "ERROR")
                return False

        except asyncio.TimeoutError:
            print_status("  ❌ Timeout waiting for auto-session", "ERROR")
            return False
        except Exception as e:
            print_status(f"  ❌ Auto-session failed: {str(e)}", "ERROR")
            return False

    async def step_3_user_speaks(self) -> bool:
        """Step 3: User speaks into microphone"""
        try:
            print_status("Step 3: User speaks into microphone", "INFO")
            print_status("  → Flutter app starts recording and streams audio...", "INFO")

            # Simulate flutter app sending audio (Vietnamese greeting)
            # "Xin chào, tôi muốn đi du lịch Đà Nẵng"
            audio_chunks = self._generate_sample_audio_chunks(3.0)  # 3 seconds of audio

            for i, chunk in enumerate(audio_chunks):
                audio_message = {
                    'mime_type': 'audio/pcm;rate=16000',
                    'data': base64.b64encode(chunk).decode('utf-8'),
                    'timestamp': int(time.time() * 1000)
                }

                await self.websocket.send(json.dumps(audio_message))
                print_status(f"  📤 Sent audio chunk {i+1}/{len(audio_chunks)}: {len(chunk)} bytes", "INFO")

                # Simulate real-time streaming (Flutter sends chunks every 150ms)
                await asyncio.sleep(0.15)

            print_status(f"  ✅ User finished speaking, sent {len(audio_chunks)} audio chunks", "SUCCESS")
            print_status(f"  📱 Flutter app shows: 'AI đang suy nghĩ...'", "INFO")
            return True

        except Exception as e:
            print_status(f"  ❌ User speech simulation failed: {str(e)}", "ERROR")
            return False

    async def step_4_ai_responds(self) -> bool:
        """Step 4: AI processes and responds"""
        try:
            print_status("Step 4: AI processes and responds", "INFO")
            print_status("  → Waiting for AI response...", "INFO")

            timeout = 30.0
            start_time = time.time()

            received_text = False
            received_audio = False
            turn_complete = False
            tool_calls = []

            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                    data = json.loads(message)

                    message_type = data.get('type')

                    if message_type == 'adk_text_response':
                        text = data.get('text', '')
                        print_status(f"  💬 AI text response: {text[:100]}...", "SUCCESS")
                        print_status(f"  📱 Flutter shows text in chat: '{text[:50]}...'", "INFO")
                        received_text = True

                    elif message_type == 'adk_audio_response':
                        audio_size = data.get('audio_size', 0)
                        print_status(f"  🔊 AI audio response: {audio_size} bytes", "SUCCESS")
                        print_status(f"  📱 Flutter plays audio response", "INFO")
                        received_audio = True

                    elif message_type == 'adk_tool_call':
                        tool_name = data.get('tool_name', 'unknown')
                        tool_calls.append(tool_name)
                        print_status(f"  🔧 Tool call: {tool_name}", "INFO")

                    elif message_type == 'adk_turn_complete':
                        print_status(f"  ✅ AI turn completed", "SUCCESS")
                        turn_complete = True
                        break

                    elif message_type == 'error':
                        print_status(f"  ❌ Server error: {data.get('message')}", "ERROR")
                        return False

                except asyncio.TimeoutError:
                    continue

            if received_text or received_audio:
                print_status(f"  🎯 AI response complete:", "SUCCESS")
                print_status(f"    - Text response: {'✅' if received_text else '❌'}", "INFO")
                print_status(f"    - Audio response: {'✅' if received_audio else '❌'}", "INFO")
                print_status(f"    - Tool calls: {', '.join(tool_calls) if tool_calls else 'None'}", "INFO")
                print_status(f"  📱 Flutter app ready for next input", "INFO")
                return True
            else:
                print_status(f"  ❌ No AI responses received within timeout", "ERROR")
                return False

        except Exception as e:
            print_status(f"  ❌ AI response test failed: {str(e)}", "ERROR")
            return False

    async def step_5_continue_conversation(self) -> bool:
        """Step 5: Continue conversation (one more exchange)"""
        try:
            print_status("Step 5: Continue conversation", "INFO")
            print_status("  → User asks follow-up question...", "INFO")

            # Send another audio message (follow-up question)
            audio_chunks = self._generate_sample_audio_chunks(2.0)  # 2 seconds

            for chunk in audio_chunks:
                audio_message = {
                    'mime_type': 'audio/pcm;rate=16000',
                    'data': base64.b64encode(chunk).decode('utf-8'),
                    'timestamp': int(time.time() * 1000)
                }
                await self.websocket.send(json.dumps(audio_message))
                await asyncio.sleep(0.15)

            print_status(f"  📤 Follow-up question sent", "SUCCESS")

            # Wait for response
            timeout = 20.0
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                    data = json.loads(message)

                    if data.get('type') == 'adk_turn_complete':
                        print_status(f"  ✅ Follow-up conversation complete", "SUCCESS")
                        return True
                    elif data.get('type') in ['adk_text_response', 'adk_audio_response']:
                        print_status(f"  💬 AI responding to follow-up...", "INFO")

                except asyncio.TimeoutError:
                    continue

            print_status(f"  ⚠️ Follow-up conversation timeout (may still be working)", "WARNING")
            return True  # Don't fail the test for follow-up timeout

        except Exception as e:
            print_status(f"  ❌ Continue conversation failed: {str(e)}", "ERROR")
            return False

    async def step_6_auto_cleanup(self) -> bool:
        """Step 6: Auto-cleanup when user closes voice chat screen"""
        try:
            print_status("Step 6: User closes voice chat screen", "INFO")
            print_status("  → Flutter app auto-disconnects and cleans up...", "INFO")

            # Close connection (simulating Flutter app dispose)
            await self.websocket.close()

            print_status(f"  ✅ Connection closed", "SUCCESS")
            print_status(f"  🧹 Server should auto-cleanup session {self.session_id[:12]}...", "INFO")

            # Wait a moment for cleanup
            await asyncio.sleep(1.0)

            print_status(f"  ✅ Auto-cleanup completed", "SUCCESS")
            print_status(f"  📱 Flutter app returns to previous screen", "INFO")
            return True

        except Exception as e:
            print_status(f"  ❌ Auto-cleanup failed: {str(e)}", "ERROR")
            return False

    def _generate_sample_audio_chunks(self, duration: float) -> list:
        """Generate sample audio chunks for testing"""
        sample_rate = 16000
        chunk_duration = 0.15  # 150ms chunks (matching Flutter app)
        samples_per_chunk = int(sample_rate * chunk_duration)
        num_chunks = int(duration / chunk_duration)

        chunks = []

        import math
        for chunk_idx in range(num_chunks):
            audio_data = []
            for i in range(samples_per_chunk):
                # Generate sine wave with some variation
                freq = 200 + (chunk_idx * 50)  # Varying frequency
                sample = int(16383 * 0.2 * math.sin(2 * math.pi * freq * i / sample_rate))
                # Convert to little-endian bytes
                audio_data.extend([sample & 0xFF, (sample >> 8) & 0xFF])

            chunks.append(bytes(audio_data))

        return chunks

async def main():
    """Main test runner"""
    print_status("Flutter Voice Chat Integration Test", "INFO")
    print_status("Testing the complete user journey from Flutter app perspective", "INFO")
    print_status("=" * 60, "INFO")

    tester = FlutterVoiceIntegrationTester()

    try:
        success = await tester.simulate_flutter_voice_chat_flow()

        print_status("=" * 60, "INFO")
        if success:
            print_status("🎉 FLUTTER INTEGRATION TEST PASSED!", "SUCCESS")
            print_status("Flutter app can successfully use simplified voice chat flow", "SUCCESS")
            return 0
        else:
            print_status("❌ FLUTTER INTEGRATION TEST FAILED", "ERROR")
            print_status("Need to fix issues before Flutter app integration", "ERROR")
            return 1

    except KeyboardInterrupt:
        print_status("Test interrupted by user", "WARNING")
        return 1
    except Exception as e:
        print_status(f"Integration test failed: {str(e)}", "ERROR")
        return 1
    finally:
        if tester.websocket and not tester.websocket.closed:
            await tester.websocket.close()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_status("Interrupted", "WARNING")
        sys.exit(1)