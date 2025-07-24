#!/usr/bin/env python3
"""
Test script để verify audio processing fix theo ADK documentation
"""
import asyncio
import os
import sys
import django
import time
import math
import struct

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from travel_concierge.voice_chat.adk_live_handler import ADKLiveHandler

async def test_complete_audio_flow():
    """Test hoàn chỉnh audio flow với ADK fix"""
    print("🎯 Testing Complete Audio Flow with ADK Fixes")
    print("=" * 60)

    try:
        # 1. Create handler
        handler = ADKLiveHandler()
        print("✅ ADK Live Handler created")

        # 2. Create session
        user_id = "audio_test_user_001"
        session_info = await handler.create_auto_session(user_id)

        if not session_info:
            print("❌ Failed to create session")
            return False

        session_id = session_info['session_id']
        print(f"✅ Session created: {session_id}")

        # 3. Generate sample audio (sine wave 440Hz, 1 second, 16kHz)
        sample_rate = 16000
        duration = 1.0
        frequency = 440  # A note

        samples = []
        for i in range(int(sample_rate * duration)):
            # Generate sine wave sample
            sample = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
            # Convert to 16-bit little endian
            samples.append(struct.pack('<h', sample))

        audio_data = b''.join(samples)
        print(f"✅ Generated audio data: {len(audio_data)} bytes")

        # 4. Test audio input processing
        print("🧪 Testing audio input processing...")
        success = await handler.process_audio_input(session_id, audio_data)

        if success:
            print("✅ Audio input processed successfully")
        else:
            print("❌ Audio input processing failed")
            return False

        # 5. Test response streaming
        print("🧪 Testing response streaming...")
        response_count = 0
        start_time = time.time()
        timeout = 15.0  # 15 seconds timeout

        async for response in handler.start_live_session(session_id):
            response_count += 1
            event_type = response.get('event_type')

            print(f"📥 Response #{response_count}: {event_type}")

            if event_type == 'text_response':
                text = response['data']['text']
                print(f"   💬 Text: {text[:100]}...")

            elif event_type == 'audio_response':
                audio_size = response['data']['audio_size']
                print(f"   🎵 Audio: {audio_size} bytes")

            elif event_type == 'tool_call':
                tool_name = response['data']['tool_name']
                print(f"   🔧 Tool: {tool_name}")

            elif event_type == 'turn_complete':
                print("   🏁 Turn completed")
                break

            # Check timeout
            if time.time() - start_time > timeout:
                print(f"⏰ Timeout after {timeout} seconds")
                break

        if response_count > 0:
            print(f"✅ Received {response_count} responses")
        else:
            print("⚠️ No responses received")

        # 6. Cleanup
        await handler.close_session(session_id)
        print("✅ Session closed")

        return response_count > 0

    except Exception as e:
        import traceback
        print(f"❌ Test failed: {str(e)}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run audio ADK fix test"""
    print("🚀 ADK Audio Processing Fix Test")
    print("Testing fixes:")
    print("  - send_realtime() for audio input")
    print("  - Proper event structure (content.parts)")
    print("  - Base64 audio encoding for responses")
    print()

    success = await test_complete_audio_flow()

    print("=" * 60)
    if success:
        print("🎉 ADK Audio Fix Test PASSED!")
        print("✅ Audio processing is working correctly")
        return 0
    else:
        print("❌ ADK Audio Fix Test FAILED")
        print("❌ Audio processing needs more debugging")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(1)