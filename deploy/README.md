# Travel Concierge Deployment Structure

## 📁 Directory Organization

```
deploy/
├── django/                    # Django App Service
│   ├── cloud-deploy.sh        # Django deployment script
│   ├── cloud-deploy.ps1       # Django deployment script (PowerShell)
│   └── Dockerfile.production  # Django production Dockerfile
│
├── adk-agent/                 # ADK Agent Service
│   ├── adk-agent-cloudbuild.yaml  # Cloud Build config
│   └── adk-agent.Dockerfile   # ADK Agent Dockerfile
│
├── voice-chat/                # Voice Chat Service
│   ├── voice-chat-cloudbuild.yaml  # Cloud Build config
│   └── voice-chat.Dockerfile  # Voice Chat Dockerfile
│
└── shared/                    # Shared deployment files
    ├── deploy-all-services.sh # Deploy all services script
    └── deploy-config.yaml     # Shared configuration
```

## 🚀 Deployment Services

### 1. Django App Service
- **Port**: 8000
- **URL**: `https://travel-server-staging-277713629269.us-central1.run.app`
- **Purpose**: Main API endpoints, authentication, database operations

### 2. ADK Agent Service
- **Port**: 8002
- **URL**: `https://adk-agent-server-277713629269.us-central1.run.app`
- **Purpose**: AI Agent functionality, SSE streaming, ADK Web UI

### 3. Voice Chat Service
- **Port**: 8003
- **URL**: `https://voice-chat-server-277713629269.us-central1.run.app`
- **Purpose**: WebSocket voice chat, audio processing

## 🔧 Deployment Commands

### Deploy All Services
```bash
cd Server/travel_server
./deploy/shared/deploy-all-services.sh
```

### Deploy Individual Services

#### Django Service
```bash
cd Server/travel_server
gcloud builds submit --config deploy/django/cloudbuild.yaml .
gcloud run deploy travel-server-staging --image gcr.io/travelapp-461806/travel-server-repo/travel-server-staging:latest --region us-central1
```

#### ADK Agent Service
```bash
cd Server/travel_server
gcloud builds submit --config deploy/adk-agent/adk-agent-cloudbuild.yaml .
gcloud run deploy adk-agent-server --image gcr.io/travelapp-461806/travel-server-repo/adk-agent-server:latest --region us-central1
```

#### Voice Chat Service
```bash
cd Server/travel_server
gcloud builds submit --config deploy/voice-chat/voice-chat-cloudbuild.yaml .
gcloud run deploy voice-chat-server --image gcr.io/travelapp-461806/travel-server-repo/voice-chat-server:latest --region us-central1
```

## 🧪 Testing

Test scripts are located in `tests/deployment/`:
- `test_production_services.ps1` - Test all production services
- `test_local_docker_fix.ps1` - Test local Docker setup
- `test_adk_agent_server.ps1` - Test ADK Agent server
- `test_ai_agent_chat.ps1` - Test AI Agent chat
- `test_api_endpoints.ps1` - Test API endpoints

## 🔗 Service Communication

- Django Service calls ADK Agent via `ADK_AGENT_URL` environment variable
- Voice Chat Service operates independently via WebSocket
- All services are accessible via their respective Cloud Run URLs

## 📊 Monitoring

- Health checks are configured for all services
- Logs are available in Google Cloud Console
- Metrics can be viewed in Cloud Monitoring