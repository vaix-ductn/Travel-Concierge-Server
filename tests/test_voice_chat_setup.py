#!/usr/bin/env python3
"""
Simple Voice Chat Setup Test
Run this to verify your ADK Voice Chat configuration
"""
import os
import sys


def test_environment_variables():
    """Test if required environment variables are set"""
    print("🔍 Testing Environment Variables...")

    required_vars = [
        'GOOGLE_CLOUD_PROJECT',
        'GOOGLE_CLOUD_LOCATION',
        'GOOGLE_APPLICATION_CREDENTIALS'
    ]

    # Load .env file manually if needed
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"📄 Loading {env_file}...")
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

    all_good = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'GOOGLE_APPLICATION_CREDENTIALS':
                if os.path.exists(value):
                    print(f"✅ {var}: File exists")
                else:
                    print(f"❌ {var}: File not found - {value}")
                    all_good = False
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            all_good = False

    return all_good


def test_vertexai_import():
    """Test Vertex AI import"""
    print("\n🔍 Testing Vertex AI Import...")
    try:
        import vertexai
        print("✅ Vertex AI import successful")
        return True
    except ImportError as e:
        print(f"❌ Vertex AI import failed: {e}")
        print("💡 Install with: pip install google-cloud-aiplatform")
        return False


def test_vertexai_init():
    """Test Vertex AI initialization"""
    print("\n🔍 Testing Vertex AI Initialization...")
    try:
        import vertexai

        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')

        if not project_id:
            print("❌ GOOGLE_CLOUD_PROJECT not set")
            return False

        vertexai.init(project=project_id, location=location)
        print(f"✅ Vertex AI initialized for project: {project_id}")
        return True
    except Exception as e:
        print(f"❌ Vertex AI initialization failed: {e}")
        return False


def test_adk_imports():
    """Test ADK imports"""
    print("\n🔍 Testing Google ADK Imports...")

    modules = [
        'google.adk.agents',
        'google.adk.runners',
        'google.adk.sessions',
        'google.genai'
    ]

    all_good = True
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            all_good = False

    if not all_good:
        print("💡 Install with: pip install google-genai")

    return all_good


def test_authentication():
    """Test Google Cloud authentication"""
    print("\n🔍 Testing Google Cloud Authentication...")
    try:
        from google.auth import default
        credentials, project = default()

        if project:
            print(f"✅ Authentication successful, project: {project}")
        else:
            print("✅ Authentication successful (no default project)")

        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Run: gcloud auth application-default login")
        return False


def main():
    """Run all tests"""
    print("🎤 Voice Chat Setup Verification")
    print("=" * 50)

    tests = [
        ("Environment Variables", test_environment_variables),
        ("Vertex AI Import", test_vertexai_import),
        ("Vertex AI Initialization", test_vertexai_init),
        ("ADK Imports", test_adk_imports),
        ("Google Cloud Authentication", test_authentication),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Unexpected error - {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("🎯 Test Summary")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        emoji = "✅" if result else "❌"
        print(f"{emoji} {test_name}: {status}")

    print("-" * 50)
    print(f"📊 Total: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Voice Chat setup is ready!")
        print("\n📋 Next steps:")
        print("1. Restart your Django server")
        print("2. Test voice chat from Flutter app")
        return 0
    else:
        print("⚠️ Voice Chat setup needs attention")
        print("\n📋 Follow these steps:")
        print("1. Fix the failed tests above")
        print("2. See docs/VOICE_CHAT_SETUP.md for detailed instructions")
        return 1


if __name__ == "__main__":
    sys.exit(main())