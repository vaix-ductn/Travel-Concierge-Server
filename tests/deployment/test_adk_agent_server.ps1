# Test ADK Agent Server Functionality
# This script tests both local and production ADK Agent servers

Write-Host "🧪 Testing ADK Agent Server Functionality" -ForegroundColor Cyan

# Configuration
$PRODUCTION_URL = "https://travel-server-staging-277713629269.us-central1.run.app"
$LOCAL_URL = "http://localhost:8000"
$ADK_LOCAL_URL = "http://localhost:8002"

# Test data
$test_user = "test_user_123"
$test_session = "test_session_456"
$test_message = "I want to visit Tokyo for 5 days. Can you suggest an itinerary?"

function Test-ADKAgentLocal {
    Write-Host "`n🔍 Testing Local ADK Agent Server..." -ForegroundColor Yellow

    try {
        # Test ADK Agent server directly
        $session_endpoint = "$ADK_LOCAL_URL/apps/travel_concierge/users/$test_user/sessions/$test_session"
        $run_endpoint = "$ADK_LOCAL_URL/run_sse"

        Write-Host "Creating session at: $session_endpoint"
        $session_response = Invoke-RestMethod -Uri $session_endpoint -Method POST -ContentType "application/json"
        Write-Host "✅ Session created: $($session_response | ConvertTo-Json)"

        # Test SSE endpoint
        $data = @{
            session_id = $test_session
            app_name = "travel_concierge"
            user_id = $test_user
            new_message = @{
                role = "user"
                parts = @(@{ text = $test_message })
            }
        }

        Write-Host "Sending message to: $run_endpoint"
        $headers = @{
            "Content-Type" = "application/json; charset=UTF-8"
            "Accept" = "text/event-stream"
        }

        $response = Invoke-RestMethod -Uri $run_endpoint -Method POST -Body ($data | ConvertTo-Json -Depth 10) -Headers $headers
        Write-Host "✅ ADK Agent response received: $($response | ConvertTo-Json)"

        return $true
    }
    catch {
        Write-Host "❌ Local ADK Agent test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-ADKAgentProduction {
    Write-Host "`n🌐 Testing Production ADK Agent Server..." -ForegroundColor Yellow

    try {
        # Test through Django API (which should use ADK Agent if available)
        $chat_endpoint = "$PRODUCTION_URL/api/agent/chat/"

        $data = @{
            message = $test_message
            user_id = $test_user
            session_id = $test_session
        }

        Write-Host "Sending chat request to: $chat_endpoint"
        $response = Invoke-RestMethod -Uri $chat_endpoint -Method POST -Body ($data | ConvertTo-Json) -ContentType "application/json"

        if ($response.success) {
            Write-Host "✅ Production chat response received" -ForegroundColor Green
            Write-Host "Response length: $($response.response.Length) characters"
            Write-Host "Response preview: $($response.response.Substring(0, [Math]::Min(100, $response.response.Length)))..."

            # Check if response looks like ADK Agent (not simple response)
            if ($response.response -match "I'd be happy to help you plan a trip to Japan" -or
                $response.response -match "Here are some great restaurants in Tokyo") {
                Write-Host "⚠️  Response appears to be simple response, not ADK Agent" -ForegroundColor Yellow
            } else {
                Write-Host "✅ Response appears to be from ADK Agent" -ForegroundColor Green
            }

            return $true
        } else {
            Write-Host "❌ Production chat failed: $($response | ConvertTo-Json)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Production ADK Agent test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-ADKAgentHealth {
    Write-Host "`n🏥 Testing ADK Agent Health..." -ForegroundColor Yellow

    try {
        # Test health endpoint
        $health_endpoint = "$PRODUCTION_URL/api/health/"
        $response = Invoke-RestMethod -Uri $health_endpoint -Method GET
        Write-Host "✅ Health check passed: $($response | ConvertTo-Json)"

        # Test agent status
        $status_endpoint = "$PRODUCTION_URL/api/agent/status/"
        $response = Invoke-RestMethod -Uri $status_endpoint -Method GET
        Write-Host "✅ Agent status: $($response | ConvertTo-Json)"

        return $true
    }
    catch {
        Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Run tests
$local_result = Test-ADKAgentLocal
$production_result = Test-ADKAgentProduction
$health_result = Test-ADKAgentHealth

Write-Host "`n📊 Test Results Summary:" -ForegroundColor Cyan
Write-Host "Local ADK Agent: $(if ($local_result) { '✅ PASS' } else { '❌ FAIL' })" -ForegroundColor $(if ($local_result) { 'Green' } else { 'Red' })
Write-Host "Production ADK Agent: $(if ($production_result) { '✅ PASS' } else { '❌ FAIL' })" -ForegroundColor $(if ($production_result) { 'Green' } else { 'Red' })
Write-Host "Health Check: $(if ($health_result) { '✅ PASS' } else { '❌ FAIL' })" -ForegroundColor $(if ($health_result) { 'Green' } else { 'Red' })

if ($local_result -and $production_result -and $health_result) {
    Write-Host "`n🎉 All ADK Agent tests passed!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Check the logs above for details." -ForegroundColor Yellow
}