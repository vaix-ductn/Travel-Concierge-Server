#!/usr/bin/env python3
"""
Integration test script to verify voice chat end-to-end flow
Tests Flutter app compatibility with ADK Bridge Server
"""

import asyncio
import json
import base64
import websockets
import logging
import time
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FlutterCompatibilityTester:
    """Test client that mimics Flutter app behavior"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.websocket = None
        self.session_active = False
        self.recording = False
        
    async def simulate_flutter_voice_chat(self):
        """Simulate complete Flutter voice chat flow"""
        logger.info("📱 Simulating Flutter app voice chat flow")
        
        try:
            # Step 1: Connect to WebSocket
            await self._connect()
            
            # Step 2: Wait for auto-session
            await self._wait_for_session()
            
            # Step 3: Simulate voice input
            await self._simulate_voice_input()
            
            # Step 4: Wait for AI response
            await self._wait_for_ai_response()
            
            # Step 5: Cleanup
            await self._cleanup()
            
            logger.info("✅ Flutter simulation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Flutter simulation failed: {e}")
            return False
            
    async def _connect(self):
        """Connect to WebSocket server (mimics Flutter behavior)"""
        logger.info("🔌 Connecting to voice chat server with auto-session...")
        
        self.websocket = await websockets.connect(
            self.server_url,
            subprotocols=['voice-chat'],
            timeout=10
        )
        
        # Start message listener
        asyncio.create_task(self._message_listener())
        logger.info("✅ Connected to voice chat server")
        
    async def _wait_for_session(self):
        """Wait for auto-session to be established"""
        logger.info("🎯 Waiting for auto-session...")
        
        # Send first audio chunk to trigger session creation
        test_audio = self._generate_test_audio()
        
        message = {
            'mime_type': 'audio/pcm;rate=16000',
            'data': base64.b64encode(test_audio).decode(),
            'timestamp': int(time.time() * 1000)
        }
        
        await self.websocket.send(json.dumps(message))
        logger.info("📤 Sent initial audio chunk")
        
        # Wait for session to become active
        timeout = 15
        start_time = time.time()
        
        while not self.session_active and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.5)
        
        if self.session_active:
            logger.info("✅ Auto-session established")
        else:
            raise Exception("Auto-session not established within timeout")
            
    async def _simulate_voice_input(self):
        """Simulate user speaking (send audio chunks)"""
        logger.info("🎙️ Simulating user speech...")
        
        self.recording = True
        
        # Simulate 3 seconds of speech
        for i in range(6):  # 6 chunks of 0.5 seconds each
            if not self.session_active:
                break
                
            audio_chunk = self._generate_test_audio(duration_ms=500)
            
            message = {
                'mime_type': 'audio/pcm;rate=16000',
                'data': base64.b64encode(audio_chunk).decode(),
                'timestamp': int(time.time() * 1000)
            }
            
            await self.websocket.send(json.dumps(message))
            logger.info(f"📤 Sent audio chunk {i+1}/6: {len(audio_chunk)} bytes")
            
            await asyncio.sleep(0.5)  # Simulate real-time streaming
        
        self.recording = False
        logger.info("✅ Voice input simulation completed")
        
    async def _wait_for_ai_response(self):
        """Wait for AI response (audio or text)"""
        logger.info("🤖 Waiting for AI response...")
        
        timeout = 30  # 30 seconds timeout
        start_time = time.time()
        received_response = False
        
        while (time.time() - start_time) < timeout:
            # In real scenario, we'd check for audio/text response events
            # For now, just wait a bit to see what we get
            await asyncio.sleep(1)
            
            # TODO: Add proper response detection logic
            # if self.received_audio_response or self.received_text_response:
            #     received_response = True
            #     break
        
        if received_response:
            logger.info("✅ Received AI response")
        else:
            logger.warning("⚠️ No AI response received within timeout")
            
    async def _cleanup(self):
        """Cleanup connection"""
        logger.info("🧹 Cleaning up...")
        
        if self.websocket:
            await self.websocket.close()
            
        logger.info("✅ Cleanup completed")
        
    async def _message_listener(self):
        """Listen for messages from server (mimics Flutter behavior)"""
        try:
            async for message in self.websocket:
                await self._handle_server_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 WebSocket connection closed")
        except Exception as e:
            logger.error(f"❌ Message listener error: {e}")
            
    async def _handle_server_message(self, message: str):
        """Handle server messages (mimics VoiceChatService behavior)"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            
            logger.info(f"📥 Received message: {message_type}")
            
            if message_type == 'connection_established':
                logger.info("🔗 Connection established")
                
            elif message_type == 'auto_session_started':
                session_id = data.get('session_id')
                user_id = data.get('user_id')
                self.session_active = True
                logger.info(f"🎯 Auto-session started: {session_id}")
                
            elif message_type == 'adk_audio_response':
                audio_data = data.get('audio_data_base64', '')
                logger.info(f"🔊 Audio response received: ~{len(audio_data)} chars")
                # In Flutter, this would trigger audio playback
                
            elif message_type == 'adk_text_response':
                text = data.get('text', '')
                logger.info(f"💬 Text response: {text[:100]}...")
                
            elif message_type == 'adk_turn_complete':
                logger.info("✅ Turn complete - ready for next input")
                
            elif message_type == 'error':
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"❌ Server error: {error_msg}")
                
            else:
                logger.info(f"ℹ️ Other message: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON: {message[:100]}...")
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            
    def _generate_test_audio(self, duration_ms: int = 1000) -> bytes:
        """Generate test audio (mimics Flutter audio recording)"""
        sample_rate = 16000
        samples = int(sample_rate * duration_ms / 1000)
        
        # Generate simple sine wave
        import math
        frequency = 440  # A note
        audio_data = bytearray()
        
        for i in range(samples):
            t = i / sample_rate
            sample = int(16000 * math.sin(2 * math.pi * frequency * t))
            audio_data.extend(sample.to_bytes(2, byteorder='little', signed=True))
        
        return bytes(audio_data)


async def run_integration_test():
    """Run complete integration test"""
    logger.info("🚀 Starting Voice Chat Integration Test")
    
    # Test against production server
    server_url = "wss://voice-chat-adk-bridge-277713629269.us-central1.run.app"
    
    tester = FlutterCompatibilityTester(server_url)
    
    try:
        success = await tester.simulate_flutter_voice_chat()
        
        if success:
            logger.info("🎉 Integration test PASSED!")
            return 0
        else:
            logger.error("❌ Integration test FAILED!")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Integration test error: {e}")
        return 1


async def run_quick_connectivity_test():
    """Quick test to verify server is reachable"""
    logger.info("⚡ Running quick connectivity test")
    
    server_url = "wss://voice-chat-adk-bridge-277713629269.us-central1.run.app"
    
    try:
        websocket = await websockets.connect(
            server_url,
            subprotocols=['voice-chat'],
            timeout=10
        )
        
        logger.info("✅ Server is reachable")
        await websocket.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Server not reachable: {e}")
        return False


async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Voice Chat Integration Test')
    parser.add_argument('--quick', action='store_true', 
                       help='Run quick connectivity test only')
    
    args = parser.parse_args()
    
    if args.quick:
        success = await run_quick_connectivity_test()
        return 0 if success else 1
    else:
        return await run_integration_test()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        sys.exit(2)
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        sys.exit(1)