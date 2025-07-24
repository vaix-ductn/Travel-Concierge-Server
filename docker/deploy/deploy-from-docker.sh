#!/bin/bash

# =============================================================================
# Deploy from Docker Container Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DOCKERFILE_PATH="$SCRIPT_DIR/Dockerfile"
CONTAINER_NAME="travel-deploy"

# Default values
ENVIRONMENT="${1:-staging}"
ACTION="${2:-full}"

log_info "Building deployment container..."

# Build the deployment container
docker build -f "$DOCKERFILE_PATH" -t "$CONTAINER_NAME" "$PROJECT_ROOT"

log_info "Running deployment from container..."

# Run the deployment container
docker run --rm -it \
    -v "$HOME/.config/gcloud:/root/.config/gcloud:ro" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e GOOGLE_CLOUD_PROJECT \
    -e GITHUB_SHA \
    "$CONTAINER_NAME" \
    bash -c "cd /app && ./deploy/cloud-deploy.sh $ENVIRONMENT $ACTION"

log_success "Deployment completed!"