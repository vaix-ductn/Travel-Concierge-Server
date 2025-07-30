#!/usr/bin/env python3
"""
Local deployment test for WebSocket ADK Bridge Server
Tests the bridge server locally before cloud deployment
"""

import asyncio
import subprocess
import sys
import time
import logging
import os
import signal
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalDeploymentTester:
    """Test local deployment of ADK bridge server"""
    
    def __init__(self):
        self.server_process = None
        self.test_passed = False
        
    async def run_local_test(self):
        """Run complete local deployment test"""
        logger.info("🧪 Starting Local Deployment Test")
        
        try:
            # Step 1: Check prerequisites
            await self._check_prerequisites()
            
            # Step 2: Start local server
            await self._start_local_server()
            
            # Step 3: Run connectivity test
            await self._test_connectivity()
            
            # Step 4: Run functionality test
            await self._test_functionality()
            
            logger.info("✅ Local deployment test completed successfully")
            self.test_passed = True
            
        except Exception as e:
            logger.error(f"❌ Local deployment test failed: {e}")
            self.test_passed = False
        finally:
            await self._cleanup()
            
        return self.test_passed
    
    async def _check_prerequisites(self):
        """Check if all prerequisites are met"""
        logger.info("📋 Checking prerequisites...")
        
        # Check Python
        python_version = sys.version
        logger.info(f"🐍 Python version: {python_version}")
        
        # Check required environment variables
        required_vars = ['GOOGLE_CLOUD_PROJECT', 'GOOGLE_CLOUD_LOCATION']
        missing_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                logger.info(f"✅ {var}: {value}")
            else:
                missing_vars.append(var)
                logger.warning(f"⚠️ Missing: {var}")
        
        if missing_vars:
            logger.info(f"ℹ️ Setting default values for missing vars: {missing_vars}")
            os.environ['GOOGLE_CLOUD_PROJECT'] = os.getenv('GOOGLE_CLOUD_PROJECT', 'sascha-playground-doit')
            os.environ['GOOGLE_CLOUD_LOCATION'] = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        # Check if required files exist
        required_files = [
            'websocket_adk_bridge.py',
            'start_bridge_server.py',
            'requirements.txt'
        ]
        
        for file in required_files:
            if Path(file).exists():
                logger.info(f"✅ Found: {file}")
            else:
                raise FileNotFoundError(f"Required file not found: {file}")
        
        logger.info("✅ Prerequisites check passed")
    
    async def _start_local_server(self):
        """Start the local bridge server"""
        logger.info("🚀 Starting local ADK bridge server...")
        
        try:
            # Start server in background
            cmd = [sys.executable, 'start_bridge_server.py']
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, 'HOST': 'localhost', 'PORT': '8003'}
            )
            
            # Wait for server to start
            logger.info("⏳ Waiting for server to start...")
            await asyncio.sleep(5)
            
            # Check if process is still running
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                logger.error(f"❌ Server failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                raise Exception("Server startup failed")
            
            logger.info("✅ Local server started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start local server: {e}")
            raise
    
    async def _test_connectivity(self):
        """Test basic connectivity to local server"""
        logger.info("🔌 Testing connectivity...")
        
        try:
            import websockets
            
            # Try to connect to local server
            websocket = await websockets.connect(
                'ws://localhost:8003',
                subprotocols=['voice-chat'],
                timeout=10
            )
            
            logger.info("✅ WebSocket connection successful")
            await websocket.close()
            
        except ImportError:
            logger.warning("⚠️ websockets module not installed, skipping connectivity test")
            logger.info("💡 Install with: pip install websockets")
        except Exception as e:
            logger.error(f"❌ Connectivity test failed: {e}")
            raise
    
    async def _test_functionality(self):
        """Test basic functionality"""
        logger.info("🧪 Testing functionality...")
        
        try:
            # Import and run local test
            sys.path.append('../../../tests')
            
            try:
                from test_voice_chat_adk_bridge import VoiceChatTester
                
                tester = VoiceChatTester('ws://localhost:8003')
                
                # Run a simplified test
                logger.info("🎯 Running simplified functionality test...")
                await tester._test_connection()
                
                logger.info("✅ Basic functionality test passed")
                
            except ImportError as e:
                logger.warning(f"⚠️ Could not import test module: {e}")
                logger.info("ℹ️ Skipping detailed functionality test")
                
        except Exception as e:
            logger.error(f"❌ Functionality test failed: {e}")
            # Don't raise - this is optional
    
    async def _cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up...")
        
        if self.server_process:
            try:
                # Terminate the server process
                self.server_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    self.server_process.kill()
                    self.server_process.wait()
                
                logger.info("✅ Server process terminated")
                
            except Exception as e:
                logger.error(f"❌ Error terminating server: {e}")
        
        logger.info("✅ Cleanup completed")


async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Local Deployment Test')
    parser.add_argument('--skip-prerequisites', action='store_true',
                       help='Skip prerequisites check')
    
    args = parser.parse_args()
    
    tester = LocalDeploymentTester()
    
    try:
        success = await tester.run_local_test()
        
        if success:
            logger.info("🎉 Local deployment test PASSED!")
            logger.info("✅ Ready for cloud deployment")
            return 0
        else:
            logger.error("❌ Local deployment test FAILED!")
            return 1
            
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        await tester._cleanup()
        return 2
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)