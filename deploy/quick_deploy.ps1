# Quick Deploy Script for Travel Concierge (PowerShell)
# Deploys both Django server and ADK agent server to Google Cloud

param(
    [string]$ProjectId = "travelapp-461806",
    [string]$Region = "us-central1",
    [string]$Repository = "travel-server-repo"
)

# Function to write colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if gcloud is installed
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Error "gcloud CLI is not installed. Please install it first."
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "manage.py")) {
    Write-Error "Please run this script from the Server/travel_server directory"
    exit 1
}

Write-Host "🚀 Starting Travel Concierge deployment..." -ForegroundColor Cyan

# Set project
Write-Status "Setting project to $ProjectId..."
gcloud config set project $ProjectId

# Build and deploy Django server
Write-Status "📦 Building Django server..."
gcloud builds submit --config deploy/django/cloudbuild.yaml

Write-Status "🚀 Deploying Django server..."
gcloud run deploy django-server `
    --image "us-central1-docker.pkg.dev/$ProjectId/$Repository/django-server:latest" `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --port 8000 `
    --set-env-vars="ENVIRONMENT=production,DB_HOST=127.0.0.1,DB_NAME=travel_concierge,DB_USER=travel_concierge,DB_PASSWORD=TravelConcierge2024!,DB_PORT=3306"

Write-Success "Django server deployed successfully!"

# Build and deploy ADK agent server
Write-Status "📦 Building ADK agent server..."
gcloud builds submit --config deploy/adk-agent/adk-agent-cloudbuild.yaml

Write-Status "🚀 Deploying ADK agent server..."
gcloud run deploy adk-agent-server `
    --image "us-central1-docker.pkg.dev/$ProjectId/$Repository/adk-agent-server:latest" `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --port 8002 `
    --set-env-vars="GOOGLE_CLOUD_API_KEY=AIzaSyAw3l0ADYmXWfAEo-k3a7jWFaqTr3TCJl0,GOOGLE_CLOUD_PROJECT=$ProjectId,GOOGLE_CLOUD_LOCATION=$Region,GOOGLE_PLACES_API_KEY=AIzaSyC6CKHUDCkbDcukn3-U8sG0xkoWGsKv9Xg"

Write-Success "ADK agent server deployed successfully!"

# Get service URLs
$DjangoUrl = gcloud run services describe django-server --region=$Region --format="value(status.url)"
$AdkUrl = gcloud run services describe adk-agent-server --region=$Region --format="value(status.url)"

Write-Host ""
Write-Success "🎉 Deployment completed successfully!"
Write-Host ""
Write-Host "📋 Service URLs:" -ForegroundColor Cyan
Write-Host "   🌐 Django Server: $DjangoUrl"
Write-Host "   🤖 ADK Agent: $AdkUrl"
Write-Host "   🖥️  ADK Web UI: $AdkUrl/dev-ui?app=travel_concierge"
Write-Host ""
Write-Host "🧪 Quick Tests:" -ForegroundColor Cyan
Write-Host "   Test Django Auth: Invoke-WebRequest -Uri '$DjangoUrl/api/auth/login/' -Method POST -ContentType 'application/json' -Body '{\"username\":\"nero\",\"password\":\"1234@pass\"}'"
Write-Host ""
Write-Host "📊 Monitoring:" -ForegroundColor Cyan
Write-Host "   Django Logs: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=django-server' --limit=10"
Write-Host "   ADK Logs: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=adk-agent-server' --limit=10"
Write-Host ""
Write-Success "Deployment completed at $(Get-Date)"