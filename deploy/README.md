# Deployment Infrastructure

This directory contains all deployment-related files and scripts for the Travel Concierge Voice Chat service.

## Directory Structure

```
deploy/
├── docker/                     # Docker configurations
│   ├── Dockerfile.voice-test   # Docker image for testing
│   └── docker-compose.voice-test.yml  # Docker Compose setup
├── scripts/                    # Deployment automation scripts  
│   ├── deploy_voice_chat.ps1   # PowerShell deployment to GCP
│   └── deploy_voice_test.ps1   # PowerShell testing deployment
├── utils/                      # Utility scripts
│   ├── restart_voice_server.py # Voice server restart utility
│   └── start_unified_voice_server.py  # Unified server starter
├── voice-chat/                 # Production voice chat deployment
│   ├── start_voice_server.py   # Production server starter
│   ├── voice-chat.Dockerfile   # Production Docker image
│   └── voice-chat-cloudbuild.yaml  # GCP Cloud Build config
└── voice-chat-adk/            # ADK bridge deployment
    ├── Dockerfile              # ADK bridge Docker image
    ├── cloudbuild.yaml         # ADK bridge Cloud Build
    └── ...                     # Testing and deployment scripts
```

## Usage Instructions

### Local Development
```bash
# Start voice server locally
cd deploy/utils
python start_unified_voice_server.py

# Restart voice server in Docker
python restart_voice_server.py
```

### Docker Testing
```bash
# Run with Docker Compose
cd deploy/docker
docker-compose -f docker-compose.voice-test.yml up --build
```

### Production Deployment
```powershell
# Deploy to Google Cloud Run
cd deploy/scripts
.\deploy_voice_chat.ps1
```

### Testing Deployment
```powershell
# Run comprehensive deployment tests
cd deploy/scripts  
.\deploy_voice_test.ps1
```

## Configuration

All deployment scripts are configured for:
- **Project ID**: travelapp-461806
- **Region**: us-central1
- **Voice Server Port**: 8003
- **Health Check Port**: 8080

## Requirements

- Docker and Docker Compose
- Google Cloud SDK (`gcloud`)
- Python 3.10+
- PowerShell (for Windows deployment scripts)

## Notes

- All paths in deployment files have been updated to work from their new locations
- Scripts automatically detect project root directory for proper path resolution
- Health checks and monitoring are included in all deployment configurations
