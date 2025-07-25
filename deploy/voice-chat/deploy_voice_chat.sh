#!/bin/bash
# =============================================================================
# Deploy Voice Chat Server to Google Cloud Run
# This script fixes the WebSocket server deployment issue
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_ID="travelapp-461806"
REGION="us-central1"
SERVICE_NAME="voice-chat-server"
REPO_NAME="travel-server-repo"
IMAGE_NAME="voice-chat-server"

echo -e "${BLUE}🚀 Deploying Voice Chat Server to Google Cloud Run...${NC}"
echo -e "${YELLOW}📋 Configuration:${NC}"
echo -e "   Project ID: ${PROJECT_ID}"
echo -e "   Region: ${REGION}"
echo -e "   Service: ${SERVICE_NAME}"
echo -e "   Image: ${IMAGE_NAME}"
echo ""

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed${NC}"
    exit 1
fi

# Build the image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
gcloud builds submit --config deploy/voice-chat/voice-chat-cloudbuild.yaml .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Image built successfully${NC}"
else
    echo -e "${RED}❌ Image build failed${NC}"
    exit 1
fi

# Deploy to Cloud Run
echo -e "${BLUE}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image us-central1-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --port 8003 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 5 \
    --timeout 3600 \
    --concurrency 1000

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo -e "${GREEN}🎉 Voice Chat Server deployed successfully!${NC}"
echo -e "${BLUE}📍 Service URL: ${SERVICE_URL}${NC}"
echo ""
echo -e "${YELLOW}🧪 Testing endpoints:${NC}"

# Test health endpoint
echo -e "${BLUE}🔍 Testing health endpoint...${NC}"
curl -s "${SERVICE_URL}/health/" | grep -q "healthy" && \
    echo -e "${GREEN}✅ Health check passed${NC}" || \
    echo -e "${RED}❌ Health check failed${NC}"

# Test root endpoint
echo -e "${BLUE}🔍 Testing root endpoint...${NC}"
curl -s "${SERVICE_URL}/" | grep -q "Voice Chat" && \
    echo -e "${GREEN}✅ Root endpoint working${NC}" || \
    echo -e "${RED}❌ Root endpoint failed${NC}"

echo ""
echo -e "${GREEN}🔗 WebSocket URL for Flutter app:${NC}"
echo -e "${BLUE}   ws://${SERVICE_URL#https://}${NC}"
echo ""
echo -e "${YELLOW}📱 Update your Flutter app configuration:${NC}"
echo -e "   const String voiceChatUrl = '${SERVICE_URL}';"

echo ""
echo -e "${BLUE}📊 View logs:${NC}"
echo -e "   gcloud run services logs read ${SERVICE_NAME} --region ${REGION}"

echo ""
echo -e "${GREEN}✨ Voice Chat Server deployment complete!${NC}"