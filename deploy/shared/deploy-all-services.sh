#!/bin/bash
# =============================================================================
# Deploy All Services to Google Cloud Platform
# Deploys Django, ADK Agent, and Voice Chat services
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
REPO_NAME="travel-server-repo"

# Service names
DJANGO_SERVICE="travel-server-staging"
ADK_SERVICE="adk-agent-server"
VOICE_SERVICE="voice-chat-server"

echo -e "${BLUE}🚀 Deploying All Services to Google Cloud Platform${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "Project ID: ${YELLOW}$PROJECT_ID${NC}"
echo -e "Region: ${YELLOW}$REGION${NC}"
echo -e "Repository: ${YELLOW}$REPO_NAME${NC}"
echo ""

# Function to check if service exists
check_service_exists() {
    local service_name=$1
    gcloud run services describe $service_name --region=$REGION --format="value(status.url)" >/dev/null 2>&1
    return $?
}

# Function to deploy service
deploy_service() {
    local service_name=$1
    local config_file=$2
    local image_name=$3
    local port=$4

    echo -e "${YELLOW}📦 Building and deploying $service_name...${NC}"

    # Build and push image
    if gcloud builds submit --config $config_file .; then
        echo -e "${GREEN}✅ Image built and pushed successfully${NC}"

        # Deploy to Cloud Run
        if gcloud run deploy $service_name \
            --image $image_name \
            --region $REGION \
            --platform managed \
            --allow-unauthenticated \
            --port $port; then

            echo -e "${GREEN}✅ $service_name deployed successfully${NC}"

            # Get service URL
            local service_url=$(gcloud run services describe $service_name --region=$REGION --format="value(status.url)")
            echo -e "${BLUE}🌐 Service URL: ${YELLOW}$service_url${NC}"

            return 0
        else
            echo -e "${RED}❌ Failed to deploy $service_name to Cloud Run${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Failed to build $service_name image${NC}"
        return 1
    fi
}

# Step 1: Deploy ADK Agent Service
echo -e "${BLUE}Step 1: Deploying ADK Agent Service${NC}"
if deploy_service \
    "$ADK_SERVICE" \
    "deploy/adk-agent/adk-agent-cloudbuild.yaml" \
    "us-central1-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/adk-agent-server:latest" \
    "8002"; then

    ADK_URL=$(gcloud run services describe $ADK_SERVICE --region=$REGION --format="value(status.url)")
    echo -e "${GREEN}✅ ADK Agent Service deployed: $ADK_URL${NC}"
else
    echo -e "${RED}❌ ADK Agent Service deployment failed${NC}"
    exit 1
fi

echo ""

# Step 2: Deploy Voice Chat Service
echo -e "${BLUE}Step 2: Deploying Voice Chat Service${NC}"
if deploy_service \
    "$VOICE_SERVICE" \
    "deploy/voice-chat/voice-chat-cloudbuild.yaml" \
    "us-central1-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/voice-chat-server:latest" \
    "8003"; then

    VOICE_URL=$(gcloud run services describe $VOICE_SERVICE --region=$REGION --format="value(status.url)")
    echo -e "${GREEN}✅ Voice Chat Service deployed: $VOICE_URL${NC}"
else
    echo -e "${RED}❌ Voice Chat Service deployment failed${NC}"
    exit 1
fi

echo ""

# Step 3: Deploy Django Service (if not exists)
echo -e "${BLUE}Step 3: Deploying Django Service${NC}"
if check_service_exists "$DJANGO_SERVICE"; then
    echo -e "${YELLOW}⚠️  Django service already exists, updating environment variables...${NC}"

    # Update environment variables for Django service
    if gcloud run services update $DJANGO_SERVICE \
        --region=$REGION \
        --set-env-vars ADK_AGENT_URL=$ADK_URL; then

        DJANGO_URL=$(gcloud run services describe $DJANGO_SERVICE --region=$REGION --format="value(status.url)")
        echo -e "${GREEN}✅ Django Service environment updated${NC}"
        echo -e "${BLUE}🌐 Django URL: ${YELLOW}$DJANGO_URL${NC}"
    else
        echo -e "${RED}❌ Failed to update Django service environment${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}📦 Building and deploying Django Service...${NC}"

    if deploy_service \
        "$DJANGO_SERVICE" \
        "deploy/django/cloudbuild.yaml" \
        "us-central1-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/django-server:latest" \
        "8000"; then

        DJANGO_URL=$(gcloud run services describe $DJANGO_SERVICE --region=$REGION --format="value(status.url)")
        echo -e "${GREEN}✅ Django Service deployed: $DJANGO_URL${NC}"

        # Set environment variables
        gcloud run services update $DJANGO_SERVICE \
            --region=$REGION \
            --set-env-vars ADK_AGENT_URL=$ADK_URL
    else
        echo -e "${RED}❌ Django Service deployment failed${NC}"
        exit 1
    fi
fi

echo ""

# Step 4: Test all services
echo -e "${BLUE}Step 4: Testing All Services${NC}"
echo -e "${YELLOW}Running health checks...${NC}"

# Test Django
if curl -s "$DJANGO_URL/" > /dev/null; then
    echo -e "${GREEN}✅ Django Service is healthy${NC}"
else
    echo -e "${RED}❌ Django Service health check failed${NC}"
fi

# Test ADK Agent
if curl -s "$ADK_URL/" > /dev/null; then
    echo -e "${GREEN}✅ ADK Agent Service is healthy${NC}"
else
    echo -e "${RED}❌ ADK Agent Service health check failed${NC}"
fi

# Test Voice Chat
if curl -s "$VOICE_URL/" > /dev/null; then
    echo -e "${GREEN}✅ Voice Chat Service is healthy${NC}"
else
    echo -e "${RED}❌ Voice Chat Service health check failed${NC}"
fi

echo ""

# Final summary
echo -e "${BLUE}🎉 Deployment Summary${NC}"
echo -e "${BLUE}==================${NC}"
echo -e "${GREEN}✅ All services deployed successfully!${NC}"
echo ""
echo -e "${BLUE}🌐 Service URLs:${NC}"
echo -e "Django Server: ${YELLOW}$DJANGO_URL${NC}"
echo -e "ADK Agent Server: ${YELLOW}$ADK_URL${NC}"
echo -e "Voice Chat Server: ${YELLOW}$VOICE_URL${NC}"
echo ""
echo -e "${BLUE}🔧 Next Steps:${NC}"
echo -e "1. Run the test script: ${YELLOW}./tests/deployment/test_production_services.ps1${NC}"
echo -e "2. Update your Flutter app with the new service URLs"
echo -e "3. Test the integrated chat functionality"
echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"