#!/usr/bin/env python3
"""
Comprehensive test script for WebSocket ADK Bridge Server
Tests end-to-end voice chat functionality with ADK Live API
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

# Test configuration
BRIDGE_SERVER_URL = os.getenv('BRIDGE_SERVER_URL', 'ws://localhost:8003')
TEST_DURATION = 30  # seconds
AUDIO_CHUNK_SIZE = 2560  # bytes (matches Flutter app)

class VoiceChatTester:
    """Test client for WebSocket ADK Bridge Server"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.websocket = None
        self.test_results = {
            'connection': False,
            'session_creation': False,
            'audio_sending': False,
            'adk_response': False,
            'audio_response': False,
            'text_response': False,
            'turn_complete': False,
            'errors': []
        }
        self.received_messages = []
        self.session_id = None
        
    async def run_full_test(self):
        """Run comprehensive test suite"""
        logger.info("🧪 Starting WebSocket ADK Bridge Server Test Suite")
        logger.info(f"🔗 Connecting to: {self.server_url}")
        
        try:
            # Test 1: Basic connection
            await self._test_connection()
            
            # Test 2: Session initialization  
            await self._test_session_creation()
            
            # Test 3: Audio sending
            await self._test_audio_sending()
            
            # Test 4: Wait for ADK responses
            await self._test_adk_responses()
            
            # Test 5: Cleanup
            await self._test_cleanup()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            self.test_results['errors'].append(str(e))
        finally:
            await self._close_connection()
            
        self._print_test_results()
        return self.test_results
    
    async def _test_connection(self):
        """Test WebSocket connection"""
        logger.info("🔌 Testing WebSocket connection...")
        
        try:
            self.websocket = await websockets.connect(
                self.server_url,
                subprotocols=['voice-chat'],
                timeout=10
            )
            
            self.test_results['connection'] = True
            logger.info("✅ WebSocket connection successful")
            
            # Start message listener
            asyncio.create_task(self._message_listener())
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            self.test_results['errors'].append(f"Connection failed: {e}")
            raise
    
    async def _test_session_creation(self):
        """Test session creation by sending audio (auto-session)"""
        logger.info("🎯 Testing session creation...")
        
        try:
            # Send first audio chunk to trigger auto-session creation
            test_audio = self._generate_test_audio(1000)  # 1 second of test audio
            
            message = {
                'mime_type': 'audio/pcm;rate=16000',
                'data': base64.b64encode(test_audio).decode(),
                'timestamp': int(time.time() * 1000)
            }
            
            await self.websocket.send(json.dumps(message))
            logger.info("📤 Sent initial audio chunk for session creation")
            
            # Wait for session creation response
            await asyncio.sleep(2)
            
            # Check if session was created
            if self.session_id:
                self.test_results['session_creation'] = True
                logger.info(f"✅ Session created: {self.session_id}")
            else:
                logger.error("❌ Session creation failed - no session_id received")
                
        except Exception as e:
            logger.error(f"❌ Session creation test failed: {e}")
            self.test_results['errors'].append(f"Session creation failed: {e}")
    
    async def _test_audio_sending(self):
        """Test sending multiple audio chunks"""
        logger.info("🎤 Testing audio sending...")
        
        try:
            # Send multiple audio chunks
            for i in range(5):
                test_audio = self._generate_test_audio(500)  # 0.5 seconds each
                
                message = {
                    'mime_type': 'audio/pcm;rate=16000', 
                    'data': base64.b64encode(test_audio).decode(),
                    'timestamp': int(time.time() * 1000)
                }
                
                await self.websocket.send(json.dumps(message))
                logger.info(f"📤 Sent audio chunk {i+1}/5: {len(test_audio)} bytes")
                
                await asyncio.sleep(0.5)  # Simulate real-time audio
            
            self.test_results['audio_sending'] = True
            logger.info("✅ Audio sending test completed")
            
        except Exception as e:
            logger.error(f"❌ Audio sending test failed: {e}")
            self.test_results['errors'].append(f"Audio sending failed: {e}")
    
    async def _test_adk_responses(self):
        """Wait for and verify ADK responses"""
        logger.info("🤖 Waiting for ADK responses...")
        
        timeout = 30  # 30 seconds timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if (self.test_results['audio_response'] or 
                self.test_results['text_response']):
                break
            await asyncio.sleep(1)
        
        if self.test_results['audio_response'] or self.test_results['text_response']:
            self.test_results['adk_response'] = True
            logger.info("✅ Received ADK responses")
        else:
            logger.error("❌ No ADK responses received within timeout")
            self.test_results['errors'].append("No ADK responses within 30 seconds")
    
    async def _test_cleanup(self):
        """Test cleanup and disconnection"""
        logger.info("🧹 Testing cleanup...")
        
        try:
            # Wait a bit more for any final messages
            await asyncio.sleep(2)
            logger.info("✅ Cleanup test completed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup test failed: {e}")
            self.test_results['errors'].append(f"Cleanup failed: {e}")
    
    async def _message_listener(self):
        """Listen for messages from server"""
        try:
            async for message in self.websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 WebSocket connection closed")
        except Exception as e:
            logger.error(f"❌ Message listener error: {e}")
    
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            
            self.received_messages.append(data)
            logger.info(f"📥 Received: {message_type}")
            
            # Handle different message types
            if message_type == 'connection_established':
                logger.info("🔗 Connection established")
                
            elif message_type == 'auto_session_started':
                self.session_id = data.get('session_id')
                logger.info(f"🎯 Auto session started: {self.session_id}")
                
            elif message_type == 'adk_audio_response':
                self.test_results['audio_response'] = True
                audio_size = len(data.get('audio_data_base64', ''))
                logger.info(f"🔊 Audio response received: ~{audio_size} base64 chars")
                
            elif message_type == 'adk_text_response':
                self.test_results['text_response'] = True
                text = data.get('text', '')
                logger.info(f"💬 Text response: {text[:100]}...")
                
            elif message_type == 'adk_turn_complete':
                self.test_results['turn_complete'] = True
                logger.info("✅ Turn complete")
                
            elif message_type == 'error':
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"❌ Server error: {error_msg}")
                self.test_results['errors'].append(f"Server error: {error_msg}")
            
            else:
                logger.info(f"ℹ️ Other message: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON received: {message[:100]}...")
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
    
    def _generate_test_audio(self, duration_ms: int) -> bytes:
        """Generate test audio data (PCM 16-bit, 16kHz, mono)"""
        sample_rate = 16000
        samples = int(sample_rate * duration_ms / 1000)
        
        # Generate simple sine wave for testing
        import math
        frequency = 440  # A note
        audio_data = bytearray()
        
        for i in range(samples):
            # Generate sine wave sample
            t = i / sample_rate
            sample = int(16000 * math.sin(2 * math.pi * frequency * t))
            
            # Convert to 16-bit PCM little-endian
            audio_data.extend(sample.to_bytes(2, byteorder='little', signed=True))
        
        return bytes(audio_data)
    
    async def _close_connection(self):
        """Close WebSocket connection"""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("🔌 WebSocket connection closed")
            except Exception as e:
                logger.error(f"❌ Error closing connection: {e}")
    
    def _print_test_results(self):
        """Print comprehensive test results"""
        logger.info("\n" + "="*60)
        logger.info("🧪 TEST RESULTS SUMMARY")
        logger.info("="*60)
        
        total_tests = len(self.test_results) - 1  # Exclude 'errors' key
        passed_tests = sum(1 for k, v in self.test_results.items() 
                          if k != 'errors' and v is True)
        
        logger.info(f"📊 Overall: {passed_tests}/{total_tests} tests passed")
        
        # Individual test results
        for test_name, result in self.test_results.items():
            if test_name == 'errors':
                continue
            status = "✅ PASS" if result else "❌ FAIL" 
            logger.info(f"{status} {test_name.replace('_', ' ').title()}")
        
        # Error summary
        if self.test_results['errors']:
            logger.info("\n❌ ERRORS:")
            for i, error in enumerate(self.test_results['errors'], 1):
                logger.info(f"  {i}. {error}")
        
        # Message summary
        logger.info(f"\n📨 Total messages received: {len(self.received_messages)}")
        message_types = {}
        for msg in self.received_messages:
            msg_type = msg.get('type', 'unknown')
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        for msg_type, count in message_types.items():
            logger.info(f"  - {msg_type}: {count}")
        
        # Final verdict
        if passed_tests == total_tests and not self.test_results['errors']:
            logger.info("\n🎉 ALL TESTS PASSED! Voice chat bridge is working correctly.")
        else:
            logger.info(f"\n⚠️ {total_tests - passed_tests} tests failed. See errors above.")
        
        logger.info("="*60)


async def test_local_development():
    """Test against local development server"""
    logger.info("🔧 Testing against local development server")
    local_url = "ws://localhost:8003"
    
    tester = VoiceChatTester(local_url)
    return await tester.run_full_test()


async def test_production_server():
    """Test against production server"""
    logger.info("☁️ Testing against production server")
    prod_url = "wss://voice-chat-adk-bridge-277713629269.us-central1.run.app"
    
    tester = VoiceChatTester(prod_url)
    return await tester.run_full_test()


async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test WebSocket ADK Bridge Server')
    parser.add_argument('--environment', choices=['local', 'production', 'both'], 
                       default='both', help='Test environment')
    parser.add_argument('--url', help='Custom server URL to test')
    
    args = parser.parse_args()
    
    if args.url:
        logger.info(f"🎯 Testing custom URL: {args.url}")
        tester = VoiceChatTester(args.url)
        results = await tester.run_full_test()
        return results
    
    all_results = {}
    
    if args.environment in ['local', 'both']:
        try:
            all_results['local'] = await test_local_development()
        except Exception as e:
            logger.error(f"❌ Local test failed: {e}")
            all_results['local'] = {'error': str(e)}
    
    if args.environment in ['production', 'both']:
        try:
            all_results['production'] = await test_production_server()
        except Exception as e:
            logger.error(f"❌ Production test failed: {e}")
            all_results['production'] = {'error': str(e)}
    
    return all_results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        
        # Exit with appropriate code
        if any('error' in result for result in results.values() if isinstance(result, dict)):
            sys.exit(1)
            
        # Check if all tests passed
        all_passed = True
        for env_results in results.values():
            if isinstance(env_results, dict) and 'errors' in env_results:
                if env_results['errors'] or not all(env_results.get(k, False) 
                    for k in env_results if k != 'errors'):
                    all_passed = False
                    break
        
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        sys.exit(2)
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        sys.exit(1)