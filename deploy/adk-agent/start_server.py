#!/usr/bin/env python3
"""
Simple script to start ADK Agent server
"""

import os
import sys
import subprocess

def main():
    try:
        # Get port from environment variable or use default
        port = int(os.environ.get('PORT', 8002))
        host = '0.0.0.0'

        print(f"Starting ADK Agent server on {host}:{port}")

        # Use google-adk command directly
        cmd = [
            "google-adk",
            "start",
            "--host", host,
            "--port", str(port)
        ]

        print(f"Running command: {' '.join(cmd)}")

        # Start the server
        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()