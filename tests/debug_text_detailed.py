#!/usr/bin/env python3
"""
Debug script chi tiết cho text input processing
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
from google.genai import types

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_text_processing_detailed():
    """Test text processing step by step"""
    try:
        logger.info("🧪 Testing text processing in detail...")

        # Test handler creation
        handler = ADKLiveHandler()
        logger.info("✅ ADK Live Handler created")

        # Test session creation
        user_id = "debug_user_text_001"
        session_info = await handler.create_auto_session(user_id)

        if not session_info:
            logger.error("❌ Failed to create session")
            return False

        session_id = session_info['session_id']
        logger.info(f"✅ Session created: {session_id}")

        # Check session components
        live_request_queue = session_info.get('live_request_queue')
        if not live_request_queue:
            logger.error("❌ No live_request_queue in session")
            return False
        logger.info(f"✅ Live request queue found: {type(live_request_queue)}")

        # Test content creation
        test_text = "Xin chào!"
        try:
            text_content = types.Content(
                parts=[types.Part(text=test_text)],
                role="user"
            )
            logger.info(f"✅ Content created: {type(text_content)}")
        except Exception as e:
            logger.error(f"❌ Failed to create content: {str(e)}")
            return False

        # Test send_content method
        try:
            logger.info("🧪 Testing send_content...")

            # Check if send_content is available
            if not hasattr(live_request_queue, 'send_content'):
                logger.error("❌ send_content method not found")
                logger.info(f"Available methods: {[m for m in dir(live_request_queue) if not m.startswith('_')]}")
                return False

            # Try to send content
            result = await live_request_queue.send_content(text_content)
            logger.info(f"✅ send_content result: {result}")

        except Exception as e:
            import traceback
            logger.error(f"❌ Failed to send content: {str(e)}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

        # Cleanup
        await handler.close_session(session_id)
        logger.info("✅ Session closed")

        return True

    except Exception as e:
        import traceback
        logger.error(f"❌ Test failed: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run detailed debug test"""
    logger.info("=" * 60)
    logger.info("🚀 Detailed Text Input Debug Test")
    logger.info("=" * 60)

    success = await test_text_processing_detailed()

    logger.info("=" * 60)
    if success:
        logger.info("🎉 Test passed!")
        return 0
    else:
        logger.error("❌ Test failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(1)