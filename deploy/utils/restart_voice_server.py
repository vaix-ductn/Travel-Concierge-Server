#!/usr/bin/env python3
"""
Quick restart script for voice server with updated buffering logic
"""
import subprocess
import sys
import time
import os

def restart_voice_server():
    print("Restarting voice server with updated buffering logic...")
    
    # Change to the correct directory (go up 2 levels from deploy/utils)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    os.chdir(project_root)
    
    # Kill any existing voice server processes
    print("Stopping any existing voice server processes...")
    try:
        subprocess.run(["docker", "exec", "travel_concierge", "pkill", "-f", "unified_voice_server"], 
                      capture_output=True, text=True)
        time.sleep(2)
    except:
        pass
    
    # Start the updated server
    print("Starting updated voice server...")
    try:
        # Run the server directly in the container
        result = subprocess.run([
            "docker", "exec", "-d", "travel_concierge", 
            "python", "-m", "travel_concierge.voice_chat.unified_voice_server"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Voice server started successfully!")
            print("Test interface: http://localhost:8003/")
            print("WebSocket endpoint: ws://localhost:8003/ws/{client_id}")
            print("Health check: http://localhost:8003/health")
            print()
            print("Key improvements in this update:")
            print("  - Advanced transcript buffering to handle streaming chunks")
            print("  - 1.5-second consolidation timer to wait for complete messages")
            print("  - Server-side deduplication with intelligent longest-message selection")
            print("  - Proper cleanup of consolidation timers")
            print("  - Simplified client-side deduplication logic")
            print()
            print("Test suggestions:")
            print("  1. Try voice mode and check for duplicate message elimination")
            print("  2. Monitor debug logs to see buffering in action")
            print("  3. Test both short and long voice inputs")
        else:
            print(f"Failed to start server: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error starting server: {e}")
        return False
    
    # Wait a moment for server to start
    time.sleep(3)
    
    # Test server health
    print("Testing server health...")
    try:
        result = subprocess.run([
            "curl", "-s", "http://localhost:8003/health"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Server health check passed: {result.stdout}")
        else:
            print("Health check failed, but server may still be starting...")
            
    except Exception as e:
        print(f"Could not test health (curl not available): {e}")
    
    return True

if __name__ == "__main__":
    success = restart_voice_server()
    
    if success:
        print("\nVoice server restart completed!")
        print("Ready to test the improved duplicate message handling.")
    else:
        print("\nVoice server restart failed!")
        sys.exit(1)