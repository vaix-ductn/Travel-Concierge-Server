# PowerShell script to test ADK Bridge Server with Docker
# Usage: .\test_with_docker.ps1

Write-Host "🐳 Testing WebSocket ADK Bridge Server with Docker" -ForegroundColor Cyan

# Set Python path
$pythonPath = "C:\Users\nerot\AppData\Local\Programs\Python\Python313\python.exe"

# Check if Docker is running
Write-Host "🔍 Checking Docker..." -ForegroundColor Yellow
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker is running" -ForegroundColor Green

# Build Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
docker build -t voice-chat-adk-bridge:test .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker image built successfully" -ForegroundColor Green

# Start container with different port
Write-Host "🚀 Starting container..." -ForegroundColor Yellow
docker run -d --name voice-chat-adk-bridge-test -p 8004:8003 `
    -e GOOGLE_CLOUD_PROJECT=sascha-playground-doit `
    -e GOOGLE_CLOUD_LOCATION=us-central1 `
    voice-chat-adk-bridge:test

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start container" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Container started" -ForegroundColor Green

# Wait for container to be ready
Write-Host "⏳ Waiting for service to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check container logs
Write-Host "📋 Container logs:" -ForegroundColor Yellow
docker logs voice-chat-adk-bridge-test

# Test connectivity
Write-Host "🧪 Testing connectivity..." -ForegroundColor Yellow

# Create simple Python test script
$testScript = @"
import asyncio
import websockets
import sys

async def test_connection():
    try:
        print('🔌 Testing WebSocket connection...')
        websocket = await websockets.connect(
            'ws://localhost:8004',
            subprotocols=['voice-chat'],
            timeout=10
        )
        print('✅ WebSocket connection successful')
        await websocket.close()
        return True
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        return False

async def main():
    success = await test_connection()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    try:
        import websockets
        asyncio.run(main())
    except ImportError:
        print('⚠️ websockets module not installed')
        print('💡 Install with: pip install websockets')
        sys.exit(2)
"@

$testScript | Out-File -FilePath "test_connection.py" -Encoding UTF8

# Run connectivity test
& $pythonPath test_connection.py
$testResult = $LASTEXITCODE

# Cleanup
Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
docker stop voice-chat-adk-bridge-test > $null 2>&1
docker rm voice-chat-adk-bridge-test > $null 2>&1
Remove-Item "test_connection.py" -ErrorAction SilentlyContinue

# Results
if ($testResult -eq 0) {
    Write-Host "🎉 All tests PASSED! ADK Bridge Server is working locally." -ForegroundColor Green
    Write-Host "✅ Ready for cloud deployment" -ForegroundColor Green
} elseif ($testResult -eq 2) {
    Write-Host "⚠️ Test incomplete - missing dependencies" -ForegroundColor Yellow
    Write-Host "💡 Install websockets: pip install websockets" -ForegroundColor Yellow
} else {
    Write-Host "❌ Tests FAILED!" -ForegroundColor Red
    Write-Host "📋 Check container logs above for details" -ForegroundColor Yellow
}

exit $testResult