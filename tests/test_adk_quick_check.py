#!/usr/bin/env python3
"""
Quick ADK Configuration Check
Validates basic setup before running comprehensive tests
"""
import os
import sys
import asyncio

# Add Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()


def print_status(message: str, status: str = "INFO"):
    """Print formatted status message"""
    icons = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌"
    }
    print(f"{icons.get(status, 'ℹ️')} {message}")


def check_environment():
    """Check essential environment variables"""
    print("🔍 Checking Environment Variables...")

    required_vars = ['GOOGLE_CLOUD_PROJECT']
    optional_vars = ['GOOGLE_CLOUD_LOCATION']

    all_good = True

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print_status(f"{var}: {value}", "SUCCESS")
        else:
            print_status(f"{var}: NOT SET (required)", "ERROR")
            all_good = False

    for var in optional_vars:
        value = os.getenv(var)
        default = 'us-central1' if var == 'GOOGLE_CLOUD_LOCATION' else None
        actual = value or default
        print_status(f"{var}: {actual} {'(default)' if not value else ''}", "SUCCESS")

    return all_good


def check_adk_dependencies():
    """Check if ADK dependencies are available"""
    print("\n🔧 Checking ADK Dependencies...")

    try:
        import vertexai
        print_status("vertexai: Available", "SUCCESS")
    except ImportError:
        print_status("vertexai: NOT AVAILABLE", "ERROR")
        return False

    try:
        from google.adk.agents import Agent, LiveRequestQueue
        print_status("google.adk.agents: Available", "SUCCESS")
    except ImportError:
        print_status("google.adk.agents: NOT AVAILABLE", "ERROR")
        return False

    try:
        from google.adk.runners import Runner
        print_status("google.adk.runners: Available", "SUCCESS")
    except ImportError:
        print_status("google.adk.runners: NOT AVAILABLE", "ERROR")
        return False

    try:
        from google.genai import types
        print_status("google.genai.types: Available", "SUCCESS")
    except ImportError:
        print_status("google.genai.types: NOT AVAILABLE", "ERROR")
        return False

    return True


def check_travel_agent():
    """Check if travel concierge agent is available"""
    print("\n🤖 Checking Travel Concierge Agent...")

    try:
        from travel_concierge.agent import root_agent
        print_status(f"Travel Agent: {root_agent.name if hasattr(root_agent, 'name') else 'Available'}", "SUCCESS")
        return True
    except ImportError as e:
        print_status(f"Travel Agent: NOT AVAILABLE - {str(e)}", "ERROR")
        return False
    except Exception as e:
        print_status(f"Travel Agent: ERROR - {str(e)}", "ERROR")
        return False


async def quick_adk_test():
    """Quick ADK initialization test"""
    print("\n⚡ Quick ADK Initialization Test...")

    try:
        # Set up environment variables for ADK
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')

        if not project_id:
            print_status("Cannot test ADK - GOOGLE_CLOUD_PROJECT not set", "ERROR")
            return False

        # Set environment variables for Google GenAI SDK
        os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'
        os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
        os.environ['GOOGLE_CLOUD_LOCATION'] = location

        print_status(f"Environment configured for Vertex AI (Project: {project_id})", "SUCCESS")

        # Test ADK Live Handler import
        from travel_concierge.voice_chat.adk_live_handler import ADKLiveHandler
        print_status("ADK Live Handler: Import successful", "SUCCESS")

        # Test basic initialization
        handler = ADKLiveHandler()
        print_status(f"ADK Handler initialized (Project: {handler.project_id})", "SUCCESS")

        return True

    except Exception as e:
        print_status(f"ADK Initialization failed: {str(e)}", "ERROR")
        return False


def main():
    """Main check function"""
    print("🚀 ADK Quick Configuration Check")
    print("="*50)

    checks = [
        ("Environment Variables", check_environment),
        ("ADK Dependencies", check_adk_dependencies),
        ("Travel Agent", check_travel_agent),
        ("ADK Initialization", quick_adk_test),
    ]

    all_passed = True

    for check_name, check_func in checks:
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = asyncio.run(check_func())
            else:
                result = check_func()

            if not result:
                all_passed = False

        except Exception as e:
            print_status(f"{check_name}: Exception - {str(e)}", "ERROR")
            all_passed = False

    print("\n" + "="*50)
    if all_passed:
        print_status("All checks passed! ✨ Ready to run comprehensive tests", "SUCCESS")
        print("\nNext steps:")
        print("  python test_adk_voice_chat.py")
    else:
        print_status("Some checks failed! ⚠️ Fix issues before running comprehensive tests", "ERROR")
        print("\nPlease fix the issues above and try again.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)