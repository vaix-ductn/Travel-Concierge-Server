# =============================================================================
# Production Services Test Script
# Tests all deployed services on Google Cloud Platform
# =============================================================================

Write-Host "🚀 Testing Production Services on Google Cloud Platform" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Service URLs
$DJANGO_URL = "https://django-server-277713629269.us-central1.run.app"
$ADK_AGENT_URL = "https://adk-agent-server-277713629269.us-central1.run.app"
$VOICE_CHAT_URL = "https://voice-chat-server-277713629269.us-central1.run.app"

# Test results
$testResults = @()

# Function to test service
function Test-Service {
    param(
        [string]$ServiceName,
        [string]$Url,
        [string]$Endpoint = "/"
    )

    Write-Host "`n🔍 Testing $ServiceName..." -ForegroundColor Yellow
    Write-Host "URL: $Url$Endpoint"

    try {
        $response = Invoke-RestMethod -Uri "$Url$Endpoint" -Method Get -TimeoutSec 30
        Write-Host "✅ $ServiceName is running!" -ForegroundColor Green
        Write-Host "Response: $($response | ConvertTo-Json -Depth 2)"

        $testResults += @{
            Service = $ServiceName
            Status = "SUCCESS"
            Response = $response
        }
    }
    catch {
        Write-Host "❌ $ServiceName failed!" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)"

        $testResults += @{
            Service = $ServiceName
            Status = "FAILED"
            Error = $_.Exception.Message
        }
    }
}

# Test 1: Django Server
Test-Service -ServiceName "Django Server" -Url $DJANGO_URL

# Test 2: ADK Agent Server
Test-Service -ServiceName "ADK Agent Server" -Url $ADK_AGENT_URL

# Test 3: Voice Chat Server
Test-Service -ServiceName "Voice Chat Server" -Url $VOICE_CHAT_URL

# Test 4: Django Health Check
Test-Service -ServiceName "Django Health Check" -Url $DJANGO_URL -Endpoint "/api/health/"

# Test 5: ADK Agent Health Check
Test-Service -ServiceName "ADK Agent Health Check" -Url $ADK_AGENT_URL -Endpoint "/health/"

# Test 6: Voice Chat Health Check
Test-Service -ServiceName "Voice Chat Health Check" -Url $VOICE_CHAT_URL -Endpoint "/health/"

# Test 7: Django API Endpoints
Write-Host "`n🔍 Testing Django API Endpoints..." -ForegroundColor Yellow

$apiEndpoints = @(
    "/api/agent/",
    "/api/agent/chat/",
    "/api/agent/status/",
    "/api/agent/health/",
    "/api/auth/",
    "/api/user_manager/",
    "/admin/"
)

foreach ($endpoint in $apiEndpoints) {
    try {
        $response = Invoke-RestMethod -Uri "$DJANGO_URL$endpoint" -Method Get -TimeoutSec 10
        Write-Host "✅ $endpoint - OK" -ForegroundColor Green
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "⚠️  $endpoint - Status: $statusCode" -ForegroundColor Yellow
    }
}

# Test 8: Integrated Chat Test
Write-Host "`n🔍 Testing Integrated Chat Functionality..." -ForegroundColor Yellow

try {
    $chatData = @{
        message = "Hello, can you help me plan a trip to Paris?"
        user_id = "test_user_123"
        session_id = "test_session_456"
    }

    $headers = @{
        "Content-Type" = "application/json"
    }

    $response = Invoke-RestMethod -Uri "$DJANGO_URL/api/agent/chat/" -Method Post -Body ($chatData | ConvertTo-Json) -Headers $headers -TimeoutSec 30

    Write-Host "✅ Chat API is working!" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json -Depth 3)"

    $testResults += @{
        Service = "Chat API"
        Status = "SUCCESS"
        Response = $response
    }
}
catch {
    Write-Host "❌ Chat API failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)"

    $testResults += @{
        Service = "Chat API"
        Status = "FAILED"
        Error = $_.Exception.Message
    }
}

# Summary
Write-Host "`n📊 Test Summary" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan

$successCount = ($testResults | Where-Object { $_.Status -eq "SUCCESS" }).Count
$totalCount = $testResults.Count

Write-Host "Total Tests: $totalCount" -ForegroundColor White
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $($totalCount - $successCount)" -ForegroundColor Red

if ($successCount -eq $totalCount) {
    Write-Host "`n🎉 All services are working correctly!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some services have issues. Check the details above." -ForegroundColor Yellow
}

# Service URLs Summary
Write-Host "`n🌐 Service URLs" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan
Write-Host "Django Server: $DJANGO_URL" -ForegroundColor White
Write-Host "ADK Agent Server: $ADK_AGENT_URL" -ForegroundColor White
Write-Host "Voice Chat Server: $VOICE_CHAT_URL" -ForegroundColor White

Write-Host "`n✅ Testing completed!" -ForegroundColor Green