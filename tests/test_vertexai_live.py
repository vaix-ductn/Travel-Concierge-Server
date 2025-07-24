import vertexai
from google.cloud import aiplatform
import os

print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
print("GOOGLE_CLOUD_PROJECT:", os.getenv("GOOGLE_CLOUD_PROJECT"))
print("GOOGLE_CLOUD_LOCATION:", os.getenv("GOOGLE_CLOUD_LOCATION"))

try:
    vertexai.init()
    print("✅ Vertex AI initialized!")
except Exception as e:
    print("❌ Vertex AI init failed:", e)

try:
    aiplatform.init()
    print("✅ AI Platform initialized!")
except Exception as e:
    print("❌ AI Platform init failed:", e)

try:
    print("🔍 Listing Vertex AI models...")
    models = list(aiplatform.Model.list())
    print(f"✅ Found {len(models)} models.")
    for m in models[:3]:
        print("-", m.resource_name)
except Exception as e:
    print("❌ Error listing models:", e)