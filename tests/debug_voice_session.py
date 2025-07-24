#!/usr/bin/env python3
"""
Debug script để test voice session initialization step by step
"""
import asyncio
import os
import sys
import django
import logging

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from travel_concierge.voice_chat.adk_live_handler import ADKLiveHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_adk_initialization():
    """Test ADK Live Handler initialization"""
    try:
        logger.info("🧪 Testing ADK Live Handler Initialization")

        # Test handler creation
        handler = ADKLiveHandler()
        logger.info("✅ ADK Live Handler created successfully")

        # Test session creation
        logger.info("🧪 Testing session creation...")
        user_id = "debug_user_001"
        session_info = await handler.create_auto_session(user_id)

        if session_info:
            logger.info(f"✅ Session created successfully: {session_info['session_id']}")
            logger.info(f"   - User ID: {session_info['user_id']}")
            logger.info(f"   - Active: {session_info['is_active']}")
            logger.info(f"   - Conversation Started: {session_info['conversation_started']}")

            # Test session cleanup
            session_id = session_info['session_id']
            await handler.close_session(session_id)
            logger.info(f"✅ Session {session_id} closed successfully")

        else:
            logger.error("❌ Failed to create session")
            return False

        return True

    except Exception as e:
        import traceback
        logger.error(f"❌ Test failed: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

async def test_imports():
    """Test required imports"""
    try:
        logger.info("🧪 Testing imports...")

        # Test Google ADK imports
        from google.adk.agents import Agent, LiveRequestQueue
        from google.adk.runners import InMemoryRunner
        from google.adk.agents.run_config import RunConfig, StreamingMode
        from google.adk.sessions import InMemorySessionService
        logger.info("✅ Google ADK imports successful")

        # Test Vertex AI import
        import vertexai
        logger.info("✅ Vertex AI import successful")

        # Test travel concierge agent import
        from travel_concierge.agent import root_agent
        logger.info(f"✅ Travel concierge agent import successful: {type(root_agent)}")

        return True

    except Exception as e:
        import traceback
        logger.error(f"❌ Import test failed: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

async def test_environment():
    """Test environment variables"""
    try:
        logger.info("🧪 Testing environment...")

        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')

        logger.info(f"   - Project ID: {project_id}")
        logger.info(f"   - Location: {location}")

        if not project_id:
            logger.warning("⚠️ GOOGLE_CLOUD_PROJECT not set")
            return False

        # Test Vertex AI initialization
        import vertexai
        vertexai.init(project=project_id, location=location)
        logger.info("✅ Vertex AI initialization successful")

        return True

    except Exception as e:
        import traceback
        logger.error(f"❌ Environment test failed: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run all debug tests"""
    logger.info("=" * 60)
    logger.info("🚀 Voice Chat Debug Test Suite")
    logger.info("=" * 60)

    results = []

    # Test imports
    results.append(await test_imports())

    # Test environment
    results.append(await test_environment())

    # Test ADK initialization
    results.append(await test_adk_initialization())

    # Summary
    passed = sum(results)
    total = len(results)

    logger.info("=" * 60)
    logger.info(f"🎯 Test Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(1)