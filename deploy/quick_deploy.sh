#!/bin/bash
# Quick Deploy Script for Travel Concierge
# Deploys both Django server and ADK agent server to Google Cloud

set -e

echo "🚀 Starting Travel Concierge deployment..."

# Set project variables
PROJECT_ID="travelapp-461806"
REGION="us-central1"
REPOSITORY="travel-server-repo"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "Please run this script from the Server/travel_server directory"
    exit 1
fi

# Set project
print_status "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Build and deploy Django server
print_status "📦 Building Django server..."
gcloud builds submit --config deploy/django/cloudbuild.yaml

print_status "🚀 Deploying Django server..."
gcloud run deploy django-server \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/django-server:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --set-env-vars="ENVIRONMENT=production,DB_HOST=127.0.0.1,DB_NAME=travel_concierge,DB_USER=travel_concierge,DB_PASSWORD=TravelConcierge2024!,DB_PORT=3306"

print_success "Django server deployed successfully!"

# Build and deploy ADK agent server
print_status "📦 Building ADK agent server..."
gcloud builds submit --config deploy/adk-agent/adk-agent-cloudbuild.yaml

print_status "🚀 Deploying ADK agent server..."
gcloud run deploy adk-agent-server \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/adk-agent-server:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8002 \
    --set-env-vars="GOOGLE_CLOUD_API_KEY=AIzaSyAw3l0ADYmXWfAEo-k3a7jWFaqTr3TCJl0,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_PLACES_API_KEY=AIzaSyC6CKHUDCkbDcukn3-U8sG0xkoWGsKv9Xg"

print_success "ADK agent server deployed successfully!"

# Get service URLs
DJANGO_URL=$(gcloud run services describe django-server --region=$REGION --format="value(status.url)")
ADK_URL=$(gcloud run services describe adk-agent-server --region=$REGION --format="value(status.url)")

echo ""
print_success "🎉 Deployment completed successfully!"
echo ""
echo "📋 Service URLs:"
echo "   🌐 Django Server: $DJANGO_URL"
echo "   🤖 ADK Agent: $ADK_URL"
echo "   🖥️  ADK Web UI: $ADK_URL/dev-ui?app=travel_concierge"
echo ""
echo "🧪 Quick Tests:"
echo "   Test Django Auth: curl -X POST $DJANGO_URL/api/auth/login/ -H 'Content-Type: application/json' -d '{\"username\":\"nero\",\"password\":\"1234@pass\"}'"
echo ""
echo "📊 Monitoring:"
echo "   Django Logs: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=django-server' --limit=10"
echo "   ADK Logs: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=adk-agent-server' --limit=10"
echo ""
print_success "Deployment completed at $(date)"