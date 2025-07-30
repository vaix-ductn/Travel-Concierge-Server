#!/bin/bash

# Deploy WebSocket ADK Bridge Server to Google Cloud Run
# This script builds and deploys the voice chat ADK bridge service

set -euo pipefail

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"sascha-playground-doit"}
REGION=${GOOGLE_CLOUD_LOCATION:-"us-central1"}
SERVICE_NAME="voice-chat-adk-bridge"

echo "🚀 Deploying WebSocket ADK Bridge Server..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# Check if gcloud is configured
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ No active gcloud authentication found"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set the project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "📋 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Copy source files to deployment directory
echo "📁 Preparing deployment files..."
cp ../../travel_concierge/voice_chat/websocket_adk_bridge.py .

# Build and deploy using Cloud Build
echo "🔨 Building and deploying with Cloud Build..."
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions=_SERVICE_NAME="$SERVICE_NAME" \
    ../../../

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --format="value(status.url)")

echo "✅ Deployment completed successfully!"
echo "🔗 Service URL: $SERVICE_URL"
echo "🎤 WebSocket URL: ${SERVICE_URL/https/wss}"

# Test the service
echo "🧪 Testing service health..."
curl -f "$SERVICE_URL/health" || echo "⚠️ Health check failed (expected for WebSocket-only service)"

echo ""
echo "📝 Next steps:"
echo "1. Update Flutter app to use WebSocket URL: ${SERVICE_URL/https/wss}"
echo "2. Test voice chat functionality"
echo "3. Monitor logs: gcloud run services logs tail $SERVICE_NAME --region=$REGION"

# Clean up copied files
rm -f websocket_adk_bridge.py