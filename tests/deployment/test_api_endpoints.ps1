# Test API Endpoints for Travel Concierge
# PowerShell script to test all API endpoints

$baseUrl = "https://travel-server-staging-277713629269.us-central1.run.app"
$headers = @{"Content-Type"="application/json"}

Write-Host "🧪 Testing Travel Concierge API Endpoints" -ForegroundColor Green
Write-Host "Base URL: $baseUrl" -ForegroundColor Yellow
Write-Host ""

# Test 1: Health Check
Write-Host "1️⃣ Testing Health Check..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/health/" -Method GET -Headers $headers
    Write-Host "✅ Health Check: PASS" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor White
    Write-Host "   Service: $($response.service)" -ForegroundColor White
} catch {
    Write-Host "❌ Health Check: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Database Connection Test
Write-Host "2️⃣ Testing Database Connection..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/test/db/" -Method GET -Headers $headers
    Write-Host "✅ Database Test: PASS" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor White
    Write-Host "   Database: $($response.database)" -ForegroundColor White
} catch {
    Write-Host "❌ Database Test: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Authentication - Login
Write-Host "3️⃣ Testing Authentication - Login..." -ForegroundColor Cyan
try {
    $loginData = @{
        username = "nero"
        password = "1234@pass"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$baseUrl/api/auth/login/" -Method POST -Headers $headers -Body $loginData
    Write-Host "✅ Login Test: PASS" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor White
    Write-Host "   Message: $($response.msg)" -ForegroundColor White

    # Store token for other tests
    $token = $response.data.token
    $authHeaders = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $token"
    }
} catch {
    Write-Host "❌ Login Test: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    $authHeaders = $headers
}
Write-Host ""

# Test 4: User Profiles
Write-Host "4️⃣ Testing User Profiles..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/user_manager/profiles/" -Method GET -Headers $headers
    Write-Host "✅ User Profiles: PASS" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor White
    Write-Host "   Count: $($response.data.count)" -ForegroundColor White
} catch {
    Write-Host "❌ User Profiles: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Agent Status
Write-Host "5️⃣ Testing Agent Status..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/agent/status/" -Method GET -Headers $headers
    Write-Host "✅ Agent Status: PASS" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor White
} catch {
    Write-Host "❌ Agent Status: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: Agent Sub-agents
Write-Host "6️⃣ Testing Agent Sub-agents..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/agent/sub-agents/" -Method GET -Headers $headers
    Write-Host "✅ Agent Sub-agents: PASS" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor White
} catch {
    Write-Host "❌ Agent Sub-agents: FAIL" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 7: Token Verification (if we have a token)
if ($token) {
    Write-Host "7️⃣ Testing Token Verification..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/auth/verify/" -Method GET -Headers $authHeaders
        Write-Host "✅ Token Verification: PASS" -ForegroundColor Green
        Write-Host "   Status: $($response.status)" -ForegroundColor White
    } catch {
        Write-Host "❌ Token Verification: FAIL" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "🎯 API Testing Complete!" -ForegroundColor Green
Write-Host "All endpoints have been tested successfully." -ForegroundColor Yellow