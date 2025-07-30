# PowerShell script to deploy voice chat server
# Usage: .\deploy_voice_chat.ps1

Write-Host "🚀 Deploying Voice Chat Server to Google Cloud Run..." -ForegroundColor Cyan

# Set Python path for gcloud
$env:PATH = "C:\Users\nerot\AppData\Local\Programs\Python\Python313;C:\Users\nerot\AppData\Local\Programs\Python\Python313\Scripts;" + $env:PATH

# Check gcloud
Write-Host "🔍 Checking gcloud..." -ForegroundColor Yellow
gcloud version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ gcloud is not working properly" -ForegroundColor Red
    exit 1
}

# Project configuration
$PROJECT_ID = "travelapp-461806"
$REGION = "us-central1"
$SERVICE_NAME = "voice-chat-server"

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   Project ID: $PROJECT_ID"
Write-Host "   Region: $REGION"  
Write-Host "   Service: $SERVICE_NAME"
Write-Host ""

# Build the image
Write-Host "🔨 Building Docker image..." -ForegroundColor Blue
gcloud builds submit --config deploy/voice-chat/voice-chat-cloudbuild.yaml .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Image build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Image built successfully" -ForegroundColor Green

# Deploy to Cloud Run
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Blue
gcloud run deploy $SERVICE_NAME `
    --image "us-central1-docker.pkg.dev/$PROJECT_ID/travel-server-repo/voice-chat-server:latest" `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --port 8003 `
    --memory 1Gi `
    --cpu 1 `
    --max-instances 5 `
    --timeout 3600 `
    --concurrency 1000

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Deployment successful!" -ForegroundColor Green

# Get service URL
Write-Host "📍 Getting service URL..." -ForegroundColor Blue
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format "value(status.url)"

Write-Host ""
Write-Host "🎉 Voice Chat Server deployed successfully!" -ForegroundColor Green
Write-Host "📍 Service URL: $SERVICE_URL" -ForegroundColor Blue
Write-Host ""
Write-Host "🔗 WebSocket URL for Flutter app:" -ForegroundColor Green
$WS_URL = $SERVICE_URL -replace "https://", "wss://"
Write-Host "   $WS_URL" -ForegroundColor Blue
Write-Host ""
Write-Host "✨ Voice Chat Server deployment complete!" -ForegroundColor Green