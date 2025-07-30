#!/usr/bin/env python3
"""
Test script for Unified Voice Chat Server
Tests the implementation against Design_future_Voice_Chat_AI_Agent_.md specifications
"""
import asyncio
import websockets
import json
import base64
import logging
import time
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
SERVER_URL = "ws://localhost:8003/ws/test_client"
TEST_DURATION = 30  # seconds

class VoiceServerTester:
    """Test client for unified voice server"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.websocket = None
        self.received_messages = []
        self.test_results = {
            'connection_test': False,
            'audio_test': False,
            'protocol_test': False,
            'cleanup_test': False,
            'errors': []
        }
    
    async def test_connection(self):
        """Test WebSocket connection as per design section 2.2"""
        try:
            logger.info(f"🔌 Testing connection to {self.server_url}")
            
            self.websocket = await websockets.connect(
                self.server_url,
                subprotocols=["voice-chat"]
            )
            
            logger.info("✅ WebSocket connection established")
            self.test_results['connection_test'] = True
            
            # Wait for initial messages
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            self.test_results['errors'].append(f"Connection: {e}")
            return False
    
    async def test_audio_protocol(self):
        """Test audio protocol as per design section 3.4"""
        try:
            logger.info("🎵 Testing audio protocol")
            
            # Create test PCM audio data (16-bit, 16kHz mono)
            sample_rate = 16000
            duration = 1.0  # 1 second
            samples = int(sample_rate * duration)
            
            # Generate simple sine wave test audio
            import math
            frequency = 440  # A4 note
            audio_data = bytearray()
            
            for i in range(samples):
                t = i / sample_rate
                sample = int(32767 * 0.5 * math.sin(2 * math.pi * frequency * t))
                # Convert to 16-bit little-endian
                audio_data.extend(sample.to_bytes(2, byteorder='little', signed=True))
            
            # Send binary audio data as per design document
            logger.info(f"📤 Sending {len(audio_data)} bytes of test audio")
            await self.websocket.send(bytes(audio_data))
            
            # Wait for responses
            await asyncio.sleep(3)
            
            self.test_results['audio_test'] = True
            logger.info("✅ Audio protocol test completed")
            
        except Exception as e:
            logger.error(f"❌ Audio protocol test failed: {e}")
            self.test_results['errors'].append(f"Audio: {e}")
    
    async def test_message_protocol(self):
        """Test message protocol as per design section 3.4"""
        try:
            logger.info("💬 Testing message protocol")
            
            # Listen for messages from server
            message_types_expected = ['transcript', 'audio_chunk', 'turn_complete']
            message_types_received = set()
            
            timeout = 10  # seconds
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=2.0
                    )
                    
                    if isinstance(message, str):
                        # JSON message
                        try:
                            data = json.loads(message)
                            msg_type = data.get('type')
                            
                            logger.info(f"📥 Received message type: {msg_type}")
                            
                            if msg_type in message_types_expected:
                                message_types_received.add(msg_type)
                            
                            self.received_messages.append(data)
                            
                            # Validate message structure as per design
                            if msg_type == 'transcript':
                                assert 'data' in data, "Transcript message missing 'data' field"
                                logger.info(f"📝 Transcript: {data['data']}")
                            
                            elif msg_type == 'audio_chunk':
                                assert 'data' in data, "Audio chunk message missing 'data' field"
                                # Verify base64 encoding
                                try:
                                    audio_bytes = base64.b64decode(data['data'])
                                    logger.info(f"🔊 Audio chunk: {len(audio_bytes)} bytes")
                                except:
                                    raise AssertionError("Audio data not valid base64")
                            
                            elif msg_type == 'turn_complete':
                                logger.info("✅ Turn complete received")
                                break  # Test complete
                                
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Invalid JSON message: {message}")
                    
                    else:
                        # Binary message (not expected from server)
                        logger.warning(f"⚠️ Unexpected binary message: {len(message)} bytes")
                        
                except asyncio.TimeoutError:
                    continue
            
            if message_types_received:
                self.test_results['protocol_test'] = True
                logger.info(f"✅ Protocol test completed. Received: {message_types_received}")
            else:
                logger.warning("⚠️ No expected message types received")
                
        except Exception as e:
            logger.error(f"❌ Message protocol test failed: {e}")
            self.test_results['errors'].append(f"Protocol: {e}")
    
    async def test_cleanup(self):
        """Test connection cleanup as per design section 3.3"""
        try:
            logger.info("🧹 Testing connection cleanup")
            
            if self.websocket:
                await self.websocket.close()
                logger.info("✅ WebSocket connection closed cleanly")
                self.test_results['cleanup_test'] = True
            
        except Exception as e:
            logger.error(f"❌ Cleanup test failed: {e}")
            self.test_results['errors'].append(f"Cleanup: {e}")
    
    async def run_full_test(self):
        """Run complete test suite"""
        logger.info("🚀 Starting unified voice server test suite")
        
        # Test 1: Connection
        if not await self.test_connection():
            return self.generate_report()
        
        # Test 2: Audio Protocol
        await self.test_audio_protocol()
        
        # Test 3: Message Protocol
        await self.test_message_protocol()
        
        # Test 4: Cleanup
        await self.test_cleanup()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        logger.info("📊 Generating test report")
        
        total_tests = len([k for k in self.test_results.keys() if k != 'errors'])
        passed_tests = len([k for k, v in self.test_results.items() if k != 'errors' and v])
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': f"{(passed_tests/total_tests)*100:.1f}%"
            },
            'details': self.test_results,
            'received_messages': len(self.received_messages),
            'message_samples': self.received_messages[:5],  # First 5 messages
            'timestamp': time.time()
        }
        
        return report

async def test_server_health():
    """Test server health endpoint"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8003/health') as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health check passed: {data}")
                    return True
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🎤 Unified Voice Chat Server Test Suite")
    logger.info("=" * 50)
    
    # Check if server is running
    logger.info("🏥 Checking server health...")
    if not await test_server_health():
        logger.error("❌ Server health check failed. Is the server running?")
        logger.info("💡 Start server with: python -m travel_concierge.voice_chat.unified_voice_server")
        return 1
    
    # Run main tests
    tester = VoiceServerTester(SERVER_URL)
    report = await tester.run_full_test()
    
    # Print report
    logger.info("=" * 50)
    logger.info("📊 TEST REPORT")
    logger.info("=" * 50)
    
    summary = report['summary']
    logger.info(f"✅ Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
    logger.info(f"📈 Success Rate: {summary['success_rate']}")
    logger.info(f"📨 Messages Received: {report['received_messages']}")
    
    if report['details']['errors']:
        logger.info("\n❌ ERRORS:")
        for error in report['details']['errors']:
            logger.info(f"   - {error}")
    
    if report['message_samples']:
        logger.info("\n📄 MESSAGE SAMPLES:")
        for i, msg in enumerate(report['message_samples'][:3]):
            logger.info(f"   {i+1}. {msg}")
    
    # Return exit code
    return 0 if summary['passed_tests'] == summary['total_tests'] else 1

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        sys.exit(1)