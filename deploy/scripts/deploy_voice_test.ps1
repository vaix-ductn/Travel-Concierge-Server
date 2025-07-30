# Deploy Voice Chat Server for Testing
# PowerShell script for Windows

param(
    [switch]$Build,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Test,
    [switch]$Logs,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

# Configuration
$COMPOSE_FILE = "docker-compose.voice-test.yml"
$SERVICE_NAME = "voice-chat-server"
$SERVER_URL = "http://localhost:8003"

function Write-Info($message) {
    Write-Host "🔧 $message" -ForegroundColor Cyan
}

function Write-Success($message) {
    Write-Host "✅ $message" -ForegroundColor Green
}

function Write-Error($message) {
    Write-Host "❌ $message" -ForegroundColor Red
}

function Test-Docker() {
    try {
        docker --version | Out-Null
        docker-compose --version | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Build-Server() {
    Write-Info "Building voice chat server Docker image..."
    
    try {
        docker-compose -f $COMPOSE_FILE build --no-cache
        Write-Success "Server image built successfully"
    } catch {
        Write-Error "Failed to build server image: $_"
        exit 1
    }
}

function Start-Server() {
    Write-Info "Starting voice chat server..."
    
    try {
        docker-compose -f $COMPOSE_FILE up -d
        Write-Success "Server started successfully"
        
        # Wait for server to be ready
        Write-Info "Waiting for server to be ready..."
        $maxAttempts = 30
        $attempt = 0
        
        do {
            Start-Sleep -Seconds 2
            $attempt++
            
            try {
                $response = Invoke-RestMethod -Uri "$SERVER_URL/health" -TimeoutSec 5
                if ($response.status -eq "healthy") {
                    Write-Success "Server is ready! Health check passed"
                    Write-Host "🌐 Server URL: $SERVER_URL"
                    Write-Host "🔌 WebSocket URL: ws://localhost:8003/ws/{client_id}"
                    return
                }
            } catch {
                # Continue waiting
            }
            
            Write-Host "⏳ Attempt $attempt/$maxAttempts - Server not ready yet..."
            
        } while ($attempt -lt $maxAttempts)
        
        Write-Error "Server failed to become ready within $maxAttempts attempts"
        Show-Logs
        exit 1
        
    } catch {
        Write-Error "Failed to start server: $_"
        exit 1
    }
}

function Stop-Server() {
    Write-Info "Stopping voice chat server..."
    
    try {
        docker-compose -f $COMPOSE_FILE down
        Write-Success "Server stopped successfully"
    } catch {
        Write-Error "Failed to stop server: $_"
        exit 1
    }
}

function Test-Server() {
    Write-Info "Running server tests..."
    
    # Check if server is running
    try {
        $response = Invoke-RestMethod -Uri "$SERVER_URL/health" -TimeoutSec 5
        if ($response.status -ne "healthy") {
            Write-Error "Server health check failed"
            return
        }
    } catch {
        Write-Error "Server is not running. Start it first with: .\deploy_voice_test.ps1 -Start"
        return
    }
    
    # Run Python test script
    try {
        Write-Info "Running unified voice server tests..."
        python tests/test_unified_voice_server.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "All tests passed!"
        } else {
            Write-Error "Some tests failed (exit code: $LASTEXITCODE)"
        }
    } catch {
        Write-Error "Failed to run tests: $_"
    }
}

function Show-Logs() {
    Write-Info "Showing server logs..."
    docker-compose -f $COMPOSE_FILE logs --follow $SERVICE_NAME
}

function Clean-Environment() {
    Write-Info "Cleaning up Docker environment..."
    
    try {
        # Stop and remove containers
        docker-compose -f $COMPOSE_FILE down --volumes --remove-orphans
        
        # Remove images
        docker image prune -f
        
        Write-Success "Environment cleaned successfully"
    } catch {
        Write-Error "Failed to clean environment: $_"
    }
}

function Show-Status() {
    Write-Info "Voice Chat Server Status"
    Write-Host "========================"
    
    # Check Docker status
    if (Test-Docker) {
        Write-Success "Docker is available"
    } else {
        Write-Error "Docker is not available"
        return
    }
    
    # Check server status
    try {
        $response = Invoke-RestMethod -Uri "$SERVER_URL/health" -TimeoutSec 3
        Write-Success "Server is running"
        Write-Host "📊 Active sessions: $($response.active_sessions)"
        Write-Host "⏰ Server time: $($response.server_time)"
    } catch {
        Write-Error "Server is not running"
    }
    
    # Show Docker containers
    Write-Host "`n🐳 Docker Containers:"
    docker-compose -f $COMPOSE_FILE ps
}

# Main logic
if (-not $Build -and -not $Start -and -not $Stop -and -not $Test -and -not $Logs -and -not $Clean) {
    Write-Host "🎤 Voice Chat Server Deployment Script" -ForegroundColor Yellow
    Write-Host "======================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\deploy_voice_test.ps1 -Build     # Build Docker image"
    Write-Host "  .\deploy_voice_test.ps1 -Start     # Start server"
    Write-Host "  .\deploy_voice_test.ps1 -Stop      # Stop server"
    Write-Host "  .\deploy_voice_test.ps1 -Test      # Run tests"
    Write-Host "  .\deploy_voice_test.ps1 -Logs      # Show logs"
    Write-Host "  .\deploy_voice_test.ps1 -Clean     # Clean environment"
    Write-Host ""
    Write-Host "Quick start:"
    Write-Host "  .\deploy_voice_test.ps1 -Build -Start -Test"
    Write-Host ""
    
    Show-Status
    exit 0
}

# Check Docker availability
if (-not (Test-Docker)) {
    Write-Error "Docker and docker-compose are required but not available"
    Write-Host "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
}

# Execute commands
if ($Clean) {
    Clean-Environment
}

if ($Build) {
    Build-Server
}

if ($Start) {
    Start-Server
}

if ($Test) {
    Test-Server
}

if ($Logs) {
    Show-Logs
}

if ($Stop) {
    Stop-Server
}

Write-Success "Voice chat deployment script completed!"