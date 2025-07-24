# =============================================================================
# Google Cloud Deployment Script for Travel Server (PowerShell Version)
# =============================================================================

param(
    [string]$Environment = "staging",
    [string]$Action = "deploy"
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ConfigFile = Join-Path $ScriptDir "deploy-config.yaml"

# Default values
$ProjectId = ""
$Region = "us-central1"
$ServiceName = "travel-server"
$DatabaseInstanceName = "travel-db"
$StorageBucketName = ""

# Helper Functions
function Write-Info {
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

function Check-Prerequisites {
    Write-Info "Checking prerequisites..."

    # Check if gcloud is installed
    try {
        $null = Get-Command gcloud -ErrorAction Stop
    }
    catch {
        Write-Error "Google Cloud SDK is not installed. Please install it first."
        exit 1
    }

    # Check if docker is installed
    try {
        $null = Get-Command docker -ErrorAction Stop
    }
    catch {
        Write-Error "Docker is not installed. Please install it first."
        exit 1
    }

    # Check if authenticated
    $authResult = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
    if (-not $authResult) {
        Write-Error "Not authenticated with Google Cloud. Run 'gcloud auth login' first."
        exit 1
    }

    Write-Success "Prerequisites check passed"
}

function Load-Config {
    Write-Info "Loading configuration for environment: $Environment"

    # Load config from YAML file if exists
    if (Test-Path $ConfigFile) {
        $configContent = Get-Content $ConfigFile -Raw
        $lines = $configContent -split "`n"

        $inStaging = $false
        foreach ($line in $lines) {
            if ($line -match "^${Environment}:") {
                $inStaging = $true
                continue
            }
            if ($inStaging -and $line -match "^\s*project_id:\s*(.+)") {
                $ProjectId = $matches[1].Trim('"', ' ')
                break
            }
            if ($inStaging -and $line -match "^\s*region:\s*(.+)") {
                $Region = $matches[1].Trim('"', ' ')
                break
            }
        }
    }

    # Fallback to environment variables or current project
    if (-not $ProjectId) {
        if ($env:GOOGLE_CLOUD_PROJECT) {
            $ProjectId = $env:GOOGLE_CLOUD_PROJECT
        }
        else {
            # Get current project from gcloud
            $ProjectId = gcloud config get-value project
            if (-not $ProjectId) {
                $ProjectId = Read-Host "Enter your Google Cloud Project ID"
            }
        }
    }

    # Set derived names
    $ServiceName = "travel-server-${Environment}"
    $DatabaseInstanceName = "travel-db-${Environment}"
    $StorageBucketName = "${ProjectId}-travel-storage-${Environment}"

    Write-Info "Configuration loaded:"
    Write-Info "  Environment: $Environment"
    Write-Info "  Project ID: $ProjectId"
    Write-Info "  Region: $Region"
    Write-Info "  Service Name: $ServiceName"
}

function Enable-APIs {
    Write-Info "Enabling required Google Cloud APIs..."

    # Set the project first
    gcloud config set project $ProjectId

    gcloud services enable `
        cloudbuild.googleapis.com `
        run.googleapis.com `
        sql-component.googleapis.com `
        sqladmin.googleapis.com `
        storage-component.googleapis.com `
        artifactregistry.googleapis.com `
        monitoring.googleapis.com `
        logging.googleapis.com `
        secretmanager.googleapis.com

    Write-Success "APIs enabled"
}

function Setup-Infrastructure {
    Write-Info "Setting up infrastructure for $Environment environment..."

    Check-Prerequisites
    Load-Config
    Enable-APIs
    Setup-ArtifactRegistry
    Setup-Database
    Setup-Storage

    Write-Success "Infrastructure setup completed for $Environment"
}

function Setup-ArtifactRegistry {
    Write-Info "Setting up Artifact Registry..."

    $repoName = "travel-server-repo"

    # Create repository if it doesn't exist
    try {
        gcloud artifacts repositories describe $repoName --location=$Region 2>$null
    }
    catch {
        gcloud artifacts repositories create $repoName `
            --repository-format=docker `
            --location=$Region
    }

    # Configure Docker authentication
    gcloud auth configure-docker "${Region}-docker.pkg.dev" --quiet

    Write-Success "Artifact Registry configured"
}

function Setup-Database {
    Write-Info "Setting up Cloud SQL database..."

    # Create Cloud SQL instance if it doesn't exist
    try {
        $null = gcloud sql instances describe $DatabaseInstanceName 2>$null
        Write-Info "Database instance already exists"
    }
    catch {
        Write-Info "Creating Cloud SQL instance (this may take several minutes)..."
        $rootPassword = -join ((33..126) | Get-Random -Count 32 | ForEach-Object {[char]$_})
        gcloud sql instances create $DatabaseInstanceName `
            --database-version=MYSQL_8_0 `
            --cpu=1 `
            --memory=3.75GB `
            --region=$Region `
            --root-password=$rootPassword

        # Wait for instance to be ready
        Write-Info "Waiting for database instance to be ready..."
        Start-Sleep -Seconds 30
    }

    # Create database
    try {
        $null = gcloud sql databases describe travel_concierge --instance=$DatabaseInstanceName 2>$null
        Write-Info "Database already exists"
    }
    catch {
        Write-Info "Creating database..."
        gcloud sql databases create travel_concierge --instance=$DatabaseInstanceName
    }

    Write-Success "Database setup completed"
}

function Setup-Storage {
    Write-Info "Setting up Cloud Storage..."

    # Create storage bucket if it doesn't exist
    try {
        gsutil ls -b "gs://$StorageBucketName" 2>$null
    }
    catch {
        gsutil mb -l $Region "gs://$StorageBucketName"
        gsutil iam ch allUsers:objectViewer "gs://$StorageBucketName"
    }

    Write-Success "Storage setup completed"
}

function Build-And-Push-Image {
    Write-Info "Building and pushing Docker image..."

    $imageName = "us.gcr.io/${ProjectId}/travel-server-repo/${ServiceName}"
    $tag = if ($env:GITHUB_SHA) { $env:GITHUB_SHA } else { git rev-parse HEAD }

    # Build custom builder first
    Write-Info "Building custom builder with MySQL libraries..."
    gcloud builds submit --tag="us.gcr.io/${ProjectId}/custom-builder:latest" --file="builder.Dockerfile" $ProjectRoot

    # Use custom builder for application build
    Write-Info "Using custom builder for application build..."
    gcloud builds submit --pack builder="us.gcr.io/${ProjectId}/custom-builder:latest",image="$imageName`:$tag" $ProjectRoot

    # Also tag as latest
    gcloud container images add-tag "$imageName`:$tag" "$imageName`:latest"

    Write-Success "Image built and pushed: $imageName`:$tag"
    return "$imageName`:latest"
}

function Deploy-To-CloudRun {
    param([string]$ImageUrl)

    Write-Info "Deploying to Cloud Run..."

    # Get database connection name (with error handling)
    try {
        $dbConnectionName = gcloud sql instances describe $DatabaseInstanceName --format="value(connectionName)"
        Write-Info "Database connection: $dbConnectionName"
    }
    catch {
        Write-Warning "Could not get database connection, deploying without database for now"
        $dbConnectionName = ""
    }

    # Deploy to Cloud Run using direct gcloud command
    $deployCmd = "gcloud run deploy $ServiceName --image=$ImageUrl --platform=managed --region=$Region --allow-unauthenticated --port=8000 --memory=2Gi --cpu=1 --max-instances=10 --min-instances=1 --set-env-vars=ENVIRONMENT=$Environment --set-env-vars=GOOGLE_CLOUD_PROJECT=$ProjectId --set-env-vars=STORAGE_BUCKET=$StorageBucketName"

    if ($dbConnectionName) {
        $deployCmd += " --set-cloudsql-instances=$dbConnectionName"
    }

    Write-Info "Executing: $deployCmd"
    Invoke-Expression $deployCmd

    # Get service URL
    try {
        $serviceUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"
        Write-Success "Deployment completed!"
        Write-Success "Service URL: $serviceUrl"
    }
    catch {
        Write-Warning "Could not get service URL, but deployment may have succeeded"
    }
}

function Deploy-Application {
    Write-Info "Deploying application to $Environment environment..."

    Check-Prerequisites
    Load-Config

    # Build and push image
    $imageUrl = Build-And-Push-Image

    # Deploy to Cloud Run
    Deploy-To-CloudRun $imageUrl

    Write-Success "Deployment completed successfully!"
}

function Full-Deployment {
    Write-Info "Running full deployment pipeline for $Environment environment..."

    Setup-Infrastructure
    Deploy-Application

    Write-Success "Full deployment completed!"
}

function Show-Help {
    Write-Host @"
Google Cloud Deployment Script for Travel Server (PowerShell)

Usage: .\cloud-deploy.ps1 [environment] [action]

Environments:
  staging     - Staging environment (default)
  production  - Production environment

Actions:
  setup-infra - Set up infrastructure only
  build-only  - Build and push image only
  deploy      - Deploy application (default)
  full        - Setup infrastructure + deploy application
  help        - Show this help message

Examples:
  .\cloud-deploy.ps1 staging deploy
  .\cloud-deploy.ps1 production setup-infra
  .\cloud-deploy.ps1 staging build-only
  .\cloud-deploy.ps1 production full

Prerequisites:
  - Google Cloud SDK installed and authenticated
  - Docker installed
  - Appropriate permissions in Google Cloud project

Environment Variables:
  GOOGLE_CLOUD_PROJECT - Google Cloud project ID (optional)
"@
}

# Main Script Logic
switch ($Action) {
    "setup-infra" { Setup-Infrastructure }
    "build-only" { Write-Info "Build only not implemented yet" }
    "deploy" { Deploy-Application }
    "full" { Full-Deployment }
    "help" { Show-Help }
    default {
        Write-Error "Unknown action: $Action"
        Show-Help
        exit 1
    }
}