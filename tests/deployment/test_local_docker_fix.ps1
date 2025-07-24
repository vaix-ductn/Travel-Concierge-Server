# Test Local Docker Fix and ADK Agent Functionality
# This script tests the fixed local Docker setup

Write-Host "🧪 Testing Local Docker Fix and ADK Agent Functionality" -ForegroundColor Cyan

# Configuration
$LOCAL_URL = "http://localhost:8000"
$ADK_LOCAL_URL = "http://localhost:8002"

# Test data
$test_user = "test_user_123"
$test_session = "test_session_456"
$test_message = "I want to visit Tokyo for 5 days. Can you suggest an itinerary?"

function Test-DockerHealth {
    Write-Host "`n🔍 Testing Docker Health..." -ForegroundColor Yellow

    try {
        # Test Django health
        $health_response = Invoke-RestMethod -Uri "$LOCAL_URL/api/health/" -Method GET
        Write-Host "✅ Django Health: $($health_response | ConvertTo-Json)" -ForegroundColor Green

        # Test agent status
        $status_response = Invoke-RestMethod -Uri "$LOCAL_URL/api/agent/status/" -Method GET
        Write-Host "✅ Agent Status: $($status_response | ConvertTo-Json)" -ForegroundColor Green

        return $true
    }
    catch {
        Write-Host "❌ Docker health test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

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

function Test-DjangoChat {
    Write-Host "`n🔍 Testing Django Chat API..." -ForegroundColor Yellow

    try {
        # Test through Django API
        $chat_endpoint = "$LOCAL_URL/api/agent/chat/"

        $data = @{
            message = $test_message
            user_id = $test_user
            session_id = $test_session
        }

        Write-Host "Sending chat request to: $chat_endpoint"
        $response = Invoke-RestMethod -Uri $chat_endpoint -Method POST -Body ($data | ConvertTo-Json) -ContentType "application/json"

        if ($response.success) {
            Write-Host "✅ Django chat response received" -ForegroundColor Green
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
            Write-Host "❌ Django chat failed: $($response | ConvertTo-Json)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Django chat test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-PyMySQLFix {
    Write-Host "`n🔍 Testing PyMySQL Fix..." -ForegroundColor Yellow

    try {
        # Test database connection through Django
        $db_test_endpoint = "$LOCAL_URL/api/health/"
        $response = Invoke-RestMethod -Uri $db_test_endpoint -Method GET

        if ($response.status -eq "healthy") {
            Write-Host "✅ PyMySQL fix successful - Django is running" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ PyMySQL fix failed - Django not healthy" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ PyMySQL fix test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Run tests
$docker_health = Test-DockerHealth
$pymysql_fix = Test-PyMySQLFix
$adk_agent = Test-ADKAgentLocal
$django_chat = Test-DjangoChat

Write-Host "`n📊 Test Results Summary:" -ForegroundColor Cyan
Write-Host "Docker Health: $(if ($docker_health) { '✅ PASS' } else { '❌ FAIL' })" -ForegroundColor $(if ($docker_health) { 'Green' } else { 'Red' })
Write-Host "PyMySQL Fix: $(if ($pymysql_fix) { '✅ PASS' } else { '❌ FAIL' })" -ForegroundColor $(if ($pymysql_fix) { 'Green' } else { 'Red' })
Write-Host "Local ADK Agent: $(if ($adk_agent) { '✅ PASS' } else { '❌ FAIL' })" -ForegroundColor $(if ($adk_agent) { 'Green' } else { 'Red' })
Write-Host "Django Chat: $(if ($django_chat) { '✅ PASS' } else { '❌ FAIL' })" -ForegroundColor $(if ($django_chat) { 'Green' } else { 'Red' })

if ($docker_health -and $pymysql_fix -and $adk_agent -and $django_chat) {
    Write-Host "`n🎉 All tests passed! Local Docker setup is working correctly!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Check the logs above for details." -ForegroundColor Yellow
}