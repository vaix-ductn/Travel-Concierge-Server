#!/bin/bash

# =============================================================================
# Google Cloud Deployment Script for Travel Server
# =============================================================================
# This script automates the deployment of the Travel Server Django application
# to Google Cloud using Cloud Run and supporting services.
#
# Prerequisites:
# - Google Cloud SDK (gcloud) installed and authenticated
# - Docker installed (for local builds)
# - Project configured with necessary APIs enabled
#
# Usage: ./deploy/cloud-deploy.sh [environment] [action]
# Examples:
#   ./deploy/cloud-deploy.sh production deploy
#   ./deploy/cloud-deploy.sh staging setup-infra
#   ./deploy/cloud-deploy.sh production build-only
# =============================================================================

set -euo pipefail  # Exit on errors, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$SCRIPT_DIR/deploy-config.yaml"

# Default values
ENVIRONMENT="${1:-staging}"
ACTION="${2:-deploy}"
PROJECT_ID=""
REGION="us-central1"
SERVICE_NAME="travel-server"
DATABASE_INSTANCE_NAME="travel-db"
STORAGE_BUCKET_NAME=""

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud SDK is not installed. Please install it first."
        exit 1
    fi

    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi

    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        log_error "Not authenticated with Google Cloud. Run 'gcloud auth login' first."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

load_config() {
    log_info "Loading configuration for environment: $ENVIRONMENT"

    # Load config from YAML file if exists
    if [[ -f "$CONFIG_FILE" ]]; then
        # Simple YAML parsing for our needs
        PROJECT_ID=$(grep -E "^${ENVIRONMENT}:" -A 10 "$CONFIG_FILE" | grep "project_id:" | awk '{print $2}' | tr -d '"')
        REGION=$(grep -E "^${ENVIRONMENT}:" -A 10 "$CONFIG_FILE" | grep "region:" | awk '{print $2}' | tr -d '"' || echo "us-central1")
    fi

    # Fallback to environment variables or prompts
    if [[ -z "$PROJECT_ID" ]]; then
        if [[ -n "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
            PROJECT_ID="$GOOGLE_CLOUD_PROJECT"
        else
            read -p "Enter your Google Cloud Project ID: " PROJECT_ID
        fi
    fi

    # Set derived names
    SERVICE_NAME="travel-server-${ENVIRONMENT}"
    DATABASE_INSTANCE_NAME="travel-db-${ENVIRONMENT}"
    STORAGE_BUCKET_NAME="${PROJECT_ID}-travel-storage-${ENVIRONMENT}"

    log_info "Configuration loaded:"
    log_info "  Environment: $ENVIRONMENT"
    log_info "  Project ID: $PROJECT_ID"
    log_info "  Region: $REGION"
    log_info "  Service Name: $SERVICE_NAME"
}

enable_apis() {
    log_info "Enabling required Google Cloud APIs..."

    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        sql-component.googleapis.com \
        sqladmin.googleapis.com \
        storage-component.googleapis.com \
        artifactregistry.googleapis.com \
        --project="$PROJECT_ID"

    log_success "APIs enabled"
}

setup_artifact_registry() {
    log_info "Setting up Artifact Registry..."

    local repo_name="travel-server-repo"

    # Create repository if it doesn't exist
    if ! gcloud artifacts repositories describe "$repo_name" \
        --location="$REGION" \
        --project="$PROJECT_ID" &>/dev/null; then

        gcloud artifacts repositories create "$repo_name" \
            --repository-format=docker \
            --location="$REGION" \
            --project="$PROJECT_ID"
    fi

    # Configure Docker authentication
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

    log_success "Artifact Registry configured"
}

setup_database() {
    log_info "Setting up Cloud SQL database..."

    # Create Cloud SQL instance if it doesn't exist
    if ! gcloud sql instances describe "$DATABASE_INSTANCE_NAME" \
        --project="$PROJECT_ID" &>/dev/null; then

        log_info "Creating Cloud SQL instance (this may take several minutes)..."
        gcloud sql instances create "$DATABASE_INSTANCE_NAME" \
            --database-version=MYSQL_8_0 \
            --cpu=1 \
            --memory=3.75GB \
            --region="$REGION" \
            --root-password="$(openssl rand -base64 32)" \
            --project="$PROJECT_ID"
    fi

    # Create database
    if ! gcloud sql databases describe travel_concierge \
        --instance="$DATABASE_INSTANCE_NAME" \
        --project="$PROJECT_ID" &>/dev/null; then

        gcloud sql databases create travel_concierge \
            --instance="$DATABASE_INSTANCE_NAME" \
            --project="$PROJECT_ID"
    fi

    log_success "Database setup completed"
}

setup_storage() {
    log_info "Setting up Cloud Storage..."

    # Create storage bucket if it doesn't exist
    if ! gsutil ls -b "gs://$STORAGE_BUCKET_NAME" &>/dev/null; then
        gsutil mb -l "$REGION" "gs://$STORAGE_BUCKET_NAME"

        # Set appropriate permissions
        gsutil iam ch allUsers:objectViewer "gs://$STORAGE_BUCKET_NAME"
    fi

    log_success "Storage setup completed"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."

    local image_name="${REGION}-docker.pkg.dev/${PROJECT_ID}/travel-server-repo/${SERVICE_NAME}"
    local tag="${GITHUB_SHA:-$(git rev-parse HEAD)}"

    # Build image using Cloud Build (recommended for production)
    if command -v gcloud &> /dev/null && [[ "$ENVIRONMENT" == "production" ]]; then
        gcloud builds submit \
            --tag="$image_name:$tag" \
            --project="$PROJECT_ID" \
            "$PROJECT_ROOT"
    else
        # Local build for development/staging
        docker build -t "$image_name:$tag" -f "$PROJECT_ROOT/docker/app/Dockerfile" "$PROJECT_ROOT"
        docker push "$image_name:$tag"
    fi

    # Also tag as latest
    gcloud container images add-tag \
        "$image_name:$tag" \
        "$image_name:latest" \
        --project="$PROJECT_ID"

    log_success "Image built and pushed: $image_name:$tag"
    echo "$image_name:latest"  # Return image URL for deployment
}

deploy_to_cloud_run() {
    local image_url="$1"

    log_info "Deploying to Cloud Run..."

    # Get database connection name
    local db_connection_name
    db_connection_name=$(gcloud sql instances describe "$DATABASE_INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --format="value(connectionName)")

    # Deploy to Cloud Run
    gcloud run deploy "$SERVICE_NAME" \
        --image="$image_url" \
        --platform=managed \
        --region="$REGION" \
        --allow-unauthenticated \
        --port=8000 \
        --memory=2Gi \
        --cpu=1 \
        --max-instances=10 \
        --min-instances=1 \
        --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
        --set-env-vars="STORAGE_BUCKET=$STORAGE_BUCKET_NAME" \
        --set-cloudsql-instances="$db_connection_name" \
        --project="$PROJECT_ID"

    # Get service URL
    local service_url
    service_url=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")

    log_success "Deployment completed!"
    log_success "Service URL: $service_url"

    return 0
}

run_migrations() {
    log_info "Running database migrations..."

    # Run migrations using Cloud Run Jobs (if available) or one-off container
    local migration_job_name="${SERVICE_NAME}-migration"

    # Create and run migration job
    gcloud run jobs create "$migration_job_name" \
        --image="$1" \
        --region="$REGION" \
        --set-cloudsql-instances="$(gcloud sql instances describe "$DATABASE_INSTANCE_NAME" --project="$PROJECT_ID" --format="value(connectionName)")" \
        --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
        --command="python" \
        --args="manage.py,migrate" \
        --project="$PROJECT_ID" \
        --replace || true  # Allow replace if job exists

    gcloud run jobs execute "$migration_job_name" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --wait

    log_success "Database migrations completed"
}

setup_monitoring() {
    log_info "Setting up monitoring and logging..."

    # Enable Cloud Monitoring and Logging (usually enabled by default)
    gcloud services enable \
        monitoring.googleapis.com \
        logging.googleapis.com \
        --project="$PROJECT_ID"

    log_success "Monitoring setup completed"
}

cleanup_old_resources() {
    log_info "Cleaning up old resources..."

    # Clean up old Cloud Run revisions (keep last 3)
    local revisions
    revisions=$(gcloud run revisions list \
        --service="$SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(metadata.name)" \
        --sort-by="~metadata.creationTimestamp" \
        --limit=100)

    local count=0
    while IFS= read -r revision; do
        ((count++))
        if [[ $count -gt 3 ]]; then
            gcloud run revisions delete "$revision" \
                --region="$REGION" \
                --project="$PROJECT_ID" \
                --quiet || true
        fi
    done <<< "$revisions"

    log_success "Cleanup completed"
}

# =============================================================================
# Main Deployment Functions
# =============================================================================

setup_infrastructure() {
    log_info "Setting up infrastructure for $ENVIRONMENT environment..."

    check_prerequisites
    load_config
    enable_apis
    setup_artifact_registry
    setup_database
    setup_storage
    setup_monitoring

    log_success "Infrastructure setup completed for $ENVIRONMENT"
}

build_only() {
    log_info "Building application..."

    check_prerequisites
    load_config
    setup_artifact_registry
    build_and_push_image

    log_success "Build completed"
}

deploy_application() {
    log_info "Deploying application to $ENVIRONMENT environment..."

    check_prerequisites
    load_config

    # Build and push image
    local image_url
    image_url=$(build_and_push_image)

    # Deploy to Cloud Run
    deploy_to_cloud_run "$image_url"

    # Run migrations
    run_migrations "$image_url"

    # Cleanup old resources
    cleanup_old_resources

    log_success "Deployment completed successfully!"
}

full_deployment() {
    log_info "Running full deployment pipeline for $ENVIRONMENT environment..."

    setup_infrastructure
    deploy_application

    log_success "Full deployment completed!"
}

show_help() {
    cat << EOF
Google Cloud Deployment Script for Travel Server

Usage: $0 [environment] [action]

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
  $0 staging deploy
  $0 production setup-infra
  $0 staging build-only
  $0 production full

Prerequisites:
  - Google Cloud SDK installed and authenticated
  - Docker installed
  - Appropriate permissions in Google Cloud project

Environment Variables:
  GOOGLE_CLOUD_PROJECT - Google Cloud project ID (optional)
EOF
}

# =============================================================================
# Main Script Logic
# =============================================================================

main() {
    case "$ACTION" in
        "setup-infra")
            setup_infrastructure
            ;;
        "build-only")
            build_only
            ;;
        "deploy")
            deploy_application
            ;;
        "full")
            full_deployment
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Unknown action: $ACTION"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"