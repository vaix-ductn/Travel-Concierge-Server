#!/usr/bin/env python3
"""
Comprehensive Test Script for ADK Live Voice Chat Functionality
Tests configuration, session management, and voice streaming capabilities
"""
import os
import sys
import asyncio
import logging
import time
import json
import signal
from typing import Dict, Any, Optional
from pathlib import Path

# Add Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

# Now import Django components
from travel_concierge.voice_chat.adk_live_handler import ADKLiveHandler
from travel_concierge.voice_chat.websocket_server import VoiceWebSocketServer


class ADKVoiceChatTester:
    """Comprehensive tester for ADK Live Voice Chat functionality"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.results = {}
        self.test_user_id = "test_user"
        self.test_session_id = f"voice_test_session_{int(time.time())}"

    def setup_logging(self):
        """Setup detailed logging for tests"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/adk_voice_chat_test.log')
            ]
        )

    def print_header(self, title: str):
        """Print formatted test section header"""
        print("\n" + "="*80)
        print(f" {title}")
        print("="*80)

    def print_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Print formatted test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.results[test_name] = {'passed': passed, 'details': details}

    def check_environment_variables(self) -> bool:
        """Test 1: Check required environment variables"""
        self.print_header("TEST 1: Environment Variables Validation")

        required_vars = {
            'GOOGLE_CLOUD_PROJECT': 'Google Cloud Project ID',
            'GOOGLE_CLOUD_LOCATION': 'Google Cloud Location (optional, defaults to us-central1)'
        }

        all_good = True

        for var, description in required_vars.items():
            value = os.getenv(var)
            if var == 'GOOGLE_CLOUD_PROJECT':
                if value:
                    self.print_test_result(f"Environment Variable: {var}", True, f"Value: {value}")
                else:
                    self.print_test_result(f"Environment Variable: {var}", False, "Missing required variable")
                    all_good = False
            else:
                # Optional variables
                default_value = 'us-central1' if var == 'GOOGLE_CLOUD_LOCATION' else None
                actual_value = value or default_value
                self.print_test_result(f"Environment Variable: {var}", True,
                                     f"Value: {actual_value} {'(default)' if not value else ''}")

        return all_good

    def test_adk_configuration(self) -> bool:
        """Test 2: ADK configuration and initialization"""
        self.print_header("TEST 2: ADK Configuration and Initialization")

        try:
            # Test ADK Live Handler initialization
            handler = ADKLiveHandler()

            # Check if Vertex AI is properly configured
            if handler.project_id:
                self.print_test_result("ADK Handler Initialization", True,
                                     f"Project: {handler.project_id}, Location: {handler.location}")
            else:
                self.print_test_result("ADK Handler Initialization", False, "Project ID not set")
                return False

            # Check Google GenAI environment variables
            genai_vertexai = os.getenv('GOOGLE_GENAI_USE_VERTEXAI')
            if genai_vertexai == 'TRUE':
                self.print_test_result("Google GenAI Vertex AI Config", True,
                                     f"GOOGLE_GENAI_USE_VERTEXAI: {genai_vertexai}")
            else:
                self.print_test_result("Google GenAI Vertex AI Config", False,
                                     f"GOOGLE_GENAI_USE_VERTEXAI: {genai_vertexai} (should be TRUE)")
                return False

            # Test run config creation
            run_config = handler.create_run_config()
            if run_config:
                self.print_test_result("ADK Run Config Creation", True,
                                     f"Streaming mode: {run_config.streaming_mode}")
            else:
                self.print_test_result("ADK Run Config Creation", False, "Failed to create run config")
                return False

            return True

        except Exception as e:
            self.print_test_result("ADK Configuration", False, f"Exception: {str(e)}")
            return False

    async def test_session_management(self) -> bool:
        """Test 3: Session creation and management"""
        self.print_header("TEST 3: Session Management")

        try:
            handler = ADKLiveHandler()

            # Test session creation
            session_info = await handler.create_session(self.test_user_id, self.test_session_id)

            if session_info and session_info.get('session'):
                self.print_test_result("Session Creation", True,
                                     f"Session ID: {self.test_session_id}")
            else:
                self.print_test_result("Session Creation", False, "Failed to create session")
                return False

            # Test session status
            status = handler.get_session_status(self.test_session_id)
            if status and status.get('is_active'):
                self.print_test_result("Session Status Check", True,
                                     f"Session active, User: {status.get('user_id')}")
            else:
                self.print_test_result("Session Status Check", False, "Session not active or not found")
                return False

            # Test session cleanup
            closed = await handler.close_session(self.test_session_id)
            if closed:
                self.print_test_result("Session Cleanup", True, "Session closed successfully")
            else:
                self.print_test_result("Session Cleanup", False, "Failed to close session")
                return False

            return True

        except Exception as e:
            self.print_test_result("Session Management", False, f"Exception: {str(e)}")
            return False

    async def test_live_streaming_setup(self) -> bool:
        """Test 4: Live streaming setup and configuration"""
        self.print_header("TEST 4: Live Streaming Setup")

        try:
            handler = ADKLiveHandler()

            # Create a test session for streaming
            test_session_id = f"stream_test_{int(time.time())}"
            session_info = await handler.create_session(self.test_user_id, test_session_id)

            if not session_info:
                self.print_test_result("Live Streaming Session Creation", False, "Failed to create session")
                return False

            self.print_test_result("Live Streaming Session Creation", True, f"Session: {test_session_id}")

            # Test live request queue
            live_queue = session_info.get('live_request_queue')
            if live_queue:
                self.print_test_result("Live Request Queue", True, "Queue created successfully")
            else:
                self.print_test_result("Live Request Queue", False, "Queue not created")
                await handler.close_session(test_session_id)
                return False

            # Test runner configuration
            runner = session_info.get('runner')
            if runner:
                self.print_test_result("ADK Runner Configuration", True, "Runner configured with travel agent")
            else:
                self.print_test_result("ADK Runner Configuration", False, "Runner not configured")
                await handler.close_session(test_session_id)
                return False

            # Cleanup
            await handler.close_session(test_session_id)
            self.print_test_result("Live Streaming Cleanup", True, "Test session cleaned up")

            return True

        except Exception as e:
            self.print_test_result("Live Streaming Setup", False, f"Exception: {str(e)}")
            return False

    async def test_websocket_server_integration(self) -> bool:
        """Test 5: WebSocket server integration"""
        self.print_header("TEST 5: WebSocket Server Integration")

        try:
            # Test WebSocket server initialization
            ws_server = VoiceWebSocketServer(host="127.0.0.1", port=8004)  # Use different port for testing

            self.print_test_result("WebSocket Server Initialization", True,
                                 f"Server configured on {ws_server.host}:{ws_server.port}")

            # Test server startup (don't actually start, just validate config)
            if hasattr(ws_server, 'connections') and hasattr(ws_server, 'user_sessions'):
                self.print_test_result("WebSocket Server Configuration", True,
                                     "Connection and session management ready")
            else:
                self.print_test_result("WebSocket Server Configuration", False,
                                     "Missing connection or session management")
                return False

            return True

        except Exception as e:
            self.print_test_result("WebSocket Server Integration", False, f"Exception: {str(e)}")
            return False

    def test_audio_configuration(self) -> bool:
        """Test 6: Audio configuration validation"""
        self.print_header("TEST 6: Audio Configuration")

        try:
            handler = ADKLiveHandler()

            # Check audio sample rates
            if handler.input_sample_rate == 16000:
                self.print_test_result("Input Sample Rate", True, f"{handler.input_sample_rate} Hz")
            else:
                self.print_test_result("Input Sample Rate", False,
                                     f"{handler.input_sample_rate} Hz (should be 16000)")

            if handler.output_sample_rate == 24000:
                self.print_test_result("Output Sample Rate", True, f"{handler.output_sample_rate} Hz")
            else:
                self.print_test_result("Output Sample Rate", False,
                                     f"{handler.output_sample_rate} Hz (should be 24000)")

            # Check voice configuration
            if handler.voice_name:
                self.print_test_result("Voice Configuration", True, f"Voice: {handler.voice_name}")
            else:
                self.print_test_result("Voice Configuration", False, "No voice configured")

            return True

        except Exception as e:
            self.print_test_result("Audio Configuration", False, f"Exception: {str(e)}")
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print("🚀 Starting ADK Live Voice Chat Comprehensive Tests")
        print(f"Test User: {self.test_user_id}")
        print(f"Test Session: {self.test_session_id}")

        start_time = time.time()

        # Run tests in sequence
        tests = [
            ("Environment Variables", self.check_environment_variables),
            ("ADK Configuration", self.test_adk_configuration),
            ("Session Management", self.test_session_management),
            ("Live Streaming Setup", self.test_live_streaming_setup),
            ("WebSocket Integration", self.test_websocket_server_integration),
            ("Audio Configuration", self.test_audio_configuration),
        ]

        overall_success = True

        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()

                if not result:
                    overall_success = False

            except Exception as e:
                self.print_test_result(f"{test_name} (Exception)", False, str(e))
                overall_success = False

        # Final results
        end_time = time.time()
        duration = end_time - start_time

        self.print_header("TEST RESULTS SUMMARY")

        passed_tests = sum(1 for result in self.results.values() if result['passed'])
        total_tests = len(self.results)

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")

        # Detailed results
        if not overall_success:
            print("\n📋 Failed Tests Details:")
            for test_name, result in self.results.items():
                if not result['passed']:
                    print(f"  ❌ {test_name}: {result['details']}")

        return {
            'overall_success': overall_success,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'duration': duration,
            'detailed_results': self.results
        }


async def main():
    """Main test runner"""
    tester = ADKVoiceChatTester()

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\n🛑 Test interrupted by user")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        results = await tester.run_all_tests()

        # Save results to file
        results_file = 'logs/adk_voice_chat_test_results.json'
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved to: {results_file}")

        # Exit with appropriate code
        sys.exit(0 if results['overall_success'] else 1)

    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())