#!/usr/bin/env python3
"""
Script để kiểm tra các StreamingMode có sẵn trong ADK
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    from google.adk.agents.run_config import RunConfig, StreamingMode
    print("Available StreamingMode values:")
    for attr in dir(StreamingMode):
        if not attr.startswith('_'):
            value = getattr(StreamingMode, attr)
            print(f"  - {attr}: {value}")

    print("\nRunConfig help:")
    print(RunConfig.__doc__)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()