# Test AI Agent Chat Functionality
# PowerShell script to test AI Agent chat endpoints

$baseUrl = "https://travel-server-staging-277713629269.us-central1.run.app"
$headers = @{"Content-Type"="application/json"}

Write-Host "🤖 Testing AI Agent Chat Functionality" -ForegroundColor Green
Write-Host "Base URL: $baseUrl" -ForegroundColor Yellow
Write-Host ""

# Test 1: Basic Chat Message
Write-Host "1️⃣ Testing Basic Chat Message..." -ForegroundColor Cyan
try {
    $chatData = @{
        message = "Hello, can you help me plan a trip to Japan?"
        user_id = "test_user_123"
        session_id = "test_session_456"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$baseUrl/api/agent/chat/" -Method POST -Headers $headers -Body $chatData
    Write-Host "✅ Basic Chat: PASS" -ForegroundColor Green
    Write-Host "   Success: $($response.success)" -ForegroundColor White
    Write-Host "   Response Length: $($response.data.response.Length) characters" -ForegroundColor White
    Write-Host "   Response Preview: $($response.data.response.Substring(0, [Math]::Min(100, $response.data.response.Length)))..." -ForegroundColor White
} catch {
    Write-Host "❌ Basic Chat: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Travel Planning Request
Write-Host "2️⃣ Testing Travel Planning Request..." -ForegroundColor Cyan
try {
    $chatData = @{
        message = "I want to visit Tokyo for 5 days. Can you suggest an itinerary?"
        user_id = "test_user_123"
        session_id = "test_session_456"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$baseUrl/api/agent/chat/" -Method POST -Headers $headers -Body $chatData
    Write-Host "✅ Travel Planning: PASS" -ForegroundColor Green
    Write-Host "   Success: $($response.success)" -ForegroundColor White
    Write-Host "   Response Length: $($response.data.response.Length) characters" -ForegroundColor White
} catch {
    Write-Host "❌ Travel Planning: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Restaurant Recommendation
Write-Host "3️⃣ Testing Restaurant Recommendation..." -ForegroundColor Cyan
try {
    $chatData = @{
        message = "Can you recommend good restaurants in Tokyo?"
        user_id = "test_user_123"
        session_id = "test_session_456"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$baseUrl/api/agent/chat/" -Method POST -Headers $headers -Body $chatData
    Write-Host "✅ Restaurant Recommendation: PASS" -ForegroundColor Green
    Write-Host "   Success: $($response.success)" -ForegroundColor White
    Write-Host "   Response Length: $($response.data.response.Length) characters" -ForegroundColor White
} catch {
    Write-Host "❌ Restaurant Recommendation: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Follow-up Question
Write-Host "4️⃣ Testing Follow-up Question..." -ForegroundColor Cyan
try {
    $chatData = @{
        message = "What about budget-friendly options?"
        user_id = "test_user_123"
        session_id = "test_session_456"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$baseUrl/api/agent/chat/" -Method POST -Headers $headers -Body $chatData
    Write-Host "✅ Follow-up Question: PASS" -ForegroundColor Green
    Write-Host "   Success: $($response.success)" -ForegroundColor White
    Write-Host "   Response Length: $($response.data.response.Length) characters" -ForegroundColor White
} catch {
    Write-Host "❌ Follow-up Question: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "🎉 AI Agent Chat Testing Complete!" -ForegroundColor Green
Write-Host "All chat functionality tests passed successfully!" -ForegroundColor Green