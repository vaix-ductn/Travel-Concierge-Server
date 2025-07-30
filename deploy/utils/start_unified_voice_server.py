#!/usr/bin/env python3
"""
Start script for unified voice server to run within Docker container
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path (go up 2 levels from deploy/utils)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Now we can import our voice server
from travel_concierge.voice_chat.unified_voice_server import run_server

if __name__ == "__main__":
    print("🎤 Starting Travel Concierge Unified Voice Server...")
    print("📋 Server will be available at: ws://localhost:8003/ws/{client_id}")
    
    # Run on all interfaces to accept connections from outside Docker
    run_server(host="0.0.0.0", port=8003)