import os
import time
import google.generativeai as genai
from google.api_core import retry

def test_api_key():
    # Get the API key from environment variable
    api_key = os.getenv('GOOGLE_CLOUD_API_KEY')

    if not api_key:
        print("❌ ERROR: GOOGLE_CLOUD_API_KEY environment variable is not set")
        print("Please set it using:")
        print('$env:GOOGLE_CLOUD_API_KEY="your-api-key-here"')
        return False

    try:
        # Configure the API
        genai.configure(api_key=api_key)

        # List available models to verify access
        print("Checking available models...")
        available_models = []
        target_model = 'models/gemini-2.0-flash-live-001'
        target_model_found = False

        for m in genai.list_models():
            model_name = m.name
            available_models.append(model_name)
            print(f"Found model: {model_name}")

            # Check if this is the target model we're looking for
            if target_model in model_name:
                target_model_found = True
                print(f"✅ TARGET MODEL FOUND: {model_name}")

        print(f"\nTotal available models: {len(available_models)}")

        if target_model_found:
            print(f"✅ SUCCESS: The model 'gemini-2.0-flash-live-001' is available!")

            # Try to test the specific model
            print(f"\nTesting the target model: {target_model}...")
            try:
                model = genai.GenerativeModel(model_name=target_model)
                response = model.generate_content('Hello, this is a test for gemini-2.0-flash-live-001.')
                print("✅ SUCCESS: Target model is working correctly!")
                print("Test response:", response.text)
                return True
            except Exception as e:
                print(f"⚠️  WARNING: Model exists but failed to generate content: {str(e)}")
                return False
        else:
            print(f"❌ ERROR: The model 'gemini-2.0-flash-live-001' was NOT found in available models")
            print("\nAvailable Gemini 2.0 models:")
            gemini_2_models = [m for m in available_models if 'gemini-2.0' in m.lower()]
            if gemini_2_models:
                for model in gemini_2_models:
                    print(f"  - {model}")
            else:
                print("  No Gemini 2.0 models found")

            # Fallback test with gemini-1.5-pro
            print("\nTrying fallback test with Gemini 1.5 Pro...")
            model = genai.GenerativeModel(model_name='models/gemini-1.5-pro')

            # Add retry logic with exponential backoff
            max_retries = 3
            retry_delay = 5  # Start with 5 seconds delay

            for attempt in range(max_retries):
                try:
                    response = model.generate_content('Hello, this is a test.')
                    print("✅ Success! API key is valid and working with fallback model")
                    print("Test response:", response.text)
                    return False  # Return False because target model not found
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        print(f"Rate limit hit. Waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    raise e

    except Exception as e:
        print("❌ ERROR: Failed to use the API key")
        print(f"Error message: {str(e)}")
        print("\nPossible issues and solutions:")
        print("1. You've hit the free tier quota limits. Solutions:")
        print("   a. Wait a few minutes before trying again")
        print("   b. Upgrade to a paid plan in Google Cloud Console")
        print("   c. Use a different API key with higher quotas")
        print("2. For more information about quotas, visit:")
        print("   https://ai.google.dev/gemini-api/docs/rate-limits")
        return False

if __name__ == "__main__":
    test_api_key()