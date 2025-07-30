#!/usr/bin/env python3
"""Test both production URLs to find the correct one"""

import asyncio
import sys

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'websockets'])
    import websockets

async def test_url(url, description):
    """Test a single URL"""
    print(f"\nTesting {description}")
    print(f"URL: {url}")
    
    try:
        websocket = await asyncio.wait_for(
            websockets.connect(
                url,
                subprotocols=['voice-chat']
            ),
            timeout=15
        )
        print("Connection successful!")
        await websocket.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

async def main():
    """Test both production URLs"""
    
    urls_to_test = [
        {
            'url': 'wss://voice-chat-adk-bridge-ocumylrfdq-uc.a.run.app',
            'description': 'Production URL #1 (from gcloud describe)'
        },
        {
            'url': 'wss://voice-chat-adk-bridge-277713629269.us-central1.run.app',
            'description': 'Production URL #2 (from gcloud list)'
        }
    ]
    
    print("Testing Production WebSocket ADK Bridge Server URLs")
    print("="*60)
    
    results = {}
    
    for test_config in urls_to_test:
        url = test_config['url']
        description = test_config['description']
        results[url] = await test_url(url, description)
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    working_urls = [url for url, success in results.items() if success]
    
    if working_urls:
        print(f"{len(working_urls)} URL(s) working:")
        for url in working_urls:
            print(f"  - {url}")
        
        print(f"\nRecommended URL for Flutter app:")
        print(f"  {working_urls[0]}")
        
        return 0
    else:
        print("No URLs working!")
        print("Check Cloud Run service logs:")
        print("  gcloud run services logs tail voice-chat-adk-bridge --region=us-central1")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)