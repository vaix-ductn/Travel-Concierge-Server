# Manual Deployment Guide - WebSocket ADK Bridge Server

## Prerequisites

1. Google Cloud SDK installed and authenticated
2. Project: `sascha-playground-doit`
3. Required APIs enabled:
   - Cloud Run API
   - Cloud Build API
   - Container Registry API
   - AI Platform API

## Step 1: Authenticate with Google Cloud

```bash
gcloud auth login
gcloud config set project sascha-playground-doit
```

## Step 2: Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com 
gcloud services enable containerregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

## Step 3: Build and Deploy

From the `voice-chat-adk` directory:

```bash
# Submit build to Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# OR manual Docker build and deploy:
docker build -t gcr.io/sascha-playground-doit/voice-chat-adk-bridge .
docker push gcr.io/sascha-playground-doit/voice-chat-adk-bridge

gcloud run deploy voice-chat-adk-bridge \
  --image gcr.io/sascha-playground-doit/voice-chat-adk-bridge \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8003 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=sascha-playground-doit,GOOGLE_CLOUD_LOCATION=us-central1
```

## Step 4: Get Service URL

```bash
gcloud run services describe voice-chat-adk-bridge \
  --region us-central1 \
  --format "value(status.url)"
```

## Step 5: Test Deployment

```bash
# Test with Python script
python ../../../tests/test_voice_chat_adk_bridge.py --environment production

# Or quick connectivity test
python ../../../tests/test_voice_chat_integration.py --quick
```

## Environment Variables

The service needs these environment variables:

- `GOOGLE_CLOUD_PROJECT`: sascha-playground-doit
- `GOOGLE_CLOUD_LOCATION`: us-central1
- `PORT`: 8003 (automatically set by Cloud Run)

## Expected Service URL

After deployment, the service should be available at:
`https://voice-chat-adk-bridge-277713629269.us-central1.run.app`

WebSocket URL for Flutter app:
`wss://voice-chat-adk-bridge-277713629269.us-central1.run.app`

## Troubleshooting

### Check service logs:
```bash
gcloud run services logs tail voice-chat-adk-bridge --region us-central1
```

### Check service status:
```bash
gcloud run services list --region us-central1
```

### Check build logs:
```bash
gcloud builds list --limit 5
```

## Security Notes

- Service allows unauthenticated access for WebSocket connections
- Uses service account credentials for Google ADK access
- Audio data is processed in real-time and not stored