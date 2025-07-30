#!/usr/bin/env python3
"""Check production server status"""

import requests
import asyncio
import sys

async def check_server_status():
    """Check if server is running"""
    
    # Test URLs
    urls = [
        'https://voice-chat-adk-bridge-ocumylrfdq-uc.a.run.app/health',
        'https://voice-chat-adk-bridge-277713629269.us-central1.run.app/health'
    ]
    
    print("Checking server health endpoints...")
    print("="*50)
    
    for url in urls:
        print(f"\\nTesting: {url}")
        try:
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("Health check: OK")
            else:
                print("Health check: FAIL")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
    
    print("\\n" + "="*50)
    print("If health checks fail, the server container might not be starting properly")
    print("This could be due to:")
    print("- Missing dependencies")
    print("- Google ADK import errors")  
    print("- Environment variable issues")
    print("- Authentication problems")

def main():
    try:
        asyncio.run(check_server_status())
        return 0
    except Exception as e:
        print(f"Check failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())