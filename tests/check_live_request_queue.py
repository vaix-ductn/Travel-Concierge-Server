#!/usr/bin/env python3
"""
Script để kiểm tra methods của LiveRequestQueue
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    from google.adk.agents import LiveRequestQueue
    from google.genai import types

    print("Creating LiveRequestQueue...")
    queue = LiveRequestQueue()

    print(f"LiveRequestQueue type: {type(queue)}")
    print("Available methods and attributes:")
    for attr in dir(queue):
        if not attr.startswith('_'):
            value = getattr(queue, attr)
            if callable(value):
                print(f"  - {attr}() - method")
            else:
                print(f"  - {attr} - attribute")

    print("\nLiveRequestQueue help:")
    print(LiveRequestQueue.__doc__)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()