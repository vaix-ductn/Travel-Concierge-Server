# Travel Concierge Deployment Guide

## 🚀 Overview

This guide covers the deployment of the Travel Concierge application to Google Cloud Platform using multiple Cloud Run services.

## 📁 Project Structure

```
deploy/
├── django/                    # Django App Service
│   ├── cloudbuild.yaml        # Cloud Build config
│   ├── cloud-deploy.sh        # Deployment script
│   ├── cloud-deploy.ps1       # PowerShell deployment script
│   └── Dockerfile.production  # Production Dockerfile
│
├── adk-agent/                 # ADK Agent Service
│   ├── adk-agent-cloudbuild.yaml  # Cloud Build config
│   ├── adk-agent.Dockerfile   # ADK Agent Dockerfile
│   ├── start_server.py        # ADK Agent startup script
│   └── test_server.py         # Test server for deployment
│
├── voice-chat/                # Voice Chat Service
│   ├── voice-chat-cloudbuild.yaml  # Cloud Build config
│   ├── voice-chat.Dockerfile  # Voice Chat Dockerfile
│   └── test_voice_server.py   # Test server for deployment
│
└── shared/                    # Shared deployment files
    ├── deploy-all-services.sh # Deploy all services script
    └── deploy-config.yaml     # Shared configuration
```

## 🌐 Deployed Services

### 1. Django Server (Main API)
- **URL**: https://travel-server-staging-277713629269.us-central1.run.app
- **Port**: 8000
- **Purpose**: Main API server with authentication, user management, and AI agent integration
- **Key Endpoints**:
  - `/` - Health check
  - `/api/health/` - API health check
  - `/api/agent/chat/` - AI chat endpoint
  - `/api/agent/status/` - Agent status
  - `/api/auth/` - Authentication endpoints
  - `/api/user_manager/` - User management endpoints

### 2. ADK Agent Server
- **URL**: https://adk-agent-server-277713629269.us-central1.run.app
- **Port**: 8002
- **Purpose**: AI Agent server for travel planning and assistance
- **Key Endpoints**:
  - `/` - Health check
  - `/health/` - Health status
  - `/test/` - Test endpoint
  - `/docs` - ADK Web UI and API documentation
  - `/run_sse` - Server-Sent Events endpoint for chat

### 3. Voice Chat Server
- **URL**: https://voice-chat-server-277713629269.us-central1.run.app
- **Port**: 8003
- **Purpose**: WebSocket server for voice chat functionality
- **Key Endpoints**:
  - `/` - Health check
  - `/health/` - Health status
  - `/test/` - Test endpoint

## 🌐 Web Interfaces

### ADK Web UI
- **URL**: https://adk-agent-server-277713629269.us-central1.run.app/docs
- **Purpose**: Interactive web interface to test AI Agent responses
- **Features**:
  - Real-time chat with AI Agent
  - Session management
  - Message history
  - API documentation
  - Interactive testing interface

### Django Admin Panel
- **URL**: https://travel-server-staging-277713629269.us-central1.run.app/admin/
- **Purpose**: Administrative interface for Django backend
- **Features**:
  - User management
  - Database administration
  - System monitoring

## 🚀 Deployment Commands

### Quick Deploy All Services
```bash
cd Server/travel_server
chmod +x deploy/shared/deploy-all-services.sh
./deploy/shared/deploy-all-services.sh
```

### Deploy Individual Services

#### ADK Agent Service
```bash
gcloud builds submit --config deploy/adk-agent/adk-agent-cloudbuild.yaml .
gcloud run deploy adk-agent-server \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/adk-agent-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8002
```

#### Voice Chat Service
```bash
gcloud builds submit --config deploy/voice-chat/voice-chat-cloudbuild.yaml .
gcloud run deploy voice-chat-server \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/voice-chat-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8003
```

#### Django Service
```bash
gcloud builds submit --config deploy/django/cloudbuild.yaml .
gcloud run deploy travel-server-staging \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/django-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --set-env-vars ADK_AGENT_URL=https://adk-agent-server-277713629269.us-central1.run.app
```

## 🧪 Testing

### Run Production Tests
```powershell
cd Server/travel_server
powershell -ExecutionPolicy Bypass -File "tests/deployment/test_production_services.ps1"
```

### Manual Testing

#### Test Django Server
```bash
curl https://travel-server-staging-277713629269.us-central1.run.app/
curl https://travel-server-staging-277713629269.us-central1.run.app/api/health/
```

#### Test ADK Agent Server
```bash
curl https://adk-agent-server-277713629269.us-central1.run.app/
curl https://adk-agent-server-277713629269.us-central1.run.app/health/
```

#### Test Voice Chat Server
```bash
curl https://voice-chat-server-277713629269.us-central1.run.app/
curl https://voice-chat-server-277713629269.us-central1.run.app/health/
```

#### Test Chat API
```bash
curl -X POST https://travel-server-staging-277713629269.us-central1.run.app/api/agent/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, can you help me plan a trip to Paris?",
    "user_id": "test_user_123",
    "session_id": "test_session_456"
  }'
```

#### Test ADK Agent Directly
```bash
curl -X POST https://adk-agent-server-277713629269.us-central1.run.app/run_sse \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "session_id": "test_session",
    "app_name": "travel_concierge",
    "user_id": "test_user",
    "new_message": {
      "role": "user",
      "parts": [{"text": "Hello, can you help me plan a trip to Paris?"}]
    }
  }'
```

#### Access ADK Web UI
- **URL**: https://adk-agent-server-277713629269.us-central1.run.app/docs
- **Features**: Interactive web interface to test AI Agent responses
- **Usage**: Open in browser to chat directly with the AI Agent

## 🔧 Configuration

### Environment Variables

#### Django Service
- `ADK_AGENT_URL`: URL of the ADK Agent server
- `DATABASE_URL`: Cloud SQL connection string
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to False for production

#### ADK Agent Service
- `PORT`: Server port (default: 8002)

#### Voice Chat Service
- `PORT`: Server port (default: 8003)

### Artifact Registry
- **Repository**: `travel-server-repo`
- **Location**: `us-central1`
- **Format**: Docker

## 📊 Monitoring

### View Service Logs
```bash
# Django logs
gcloud run services logs read travel-server-staging --region us-central1

# ADK Agent logs
gcloud run services logs read adk-agent-server --region us-central1

# Voice Chat logs
gcloud run services logs read voice-chat-server --region us-central1
```

### Service Status
```bash
gcloud run services list --region us-central1
```

## 🔄 Update Process

### Update All Services
1. Make code changes
2. Run the deployment script: `./deploy/shared/deploy-all-services.sh`
3. Run tests: `./tests/deployment/test_production_services.ps1`

### Update Individual Service
1. Make code changes
2. Build and deploy the specific service
3. Test the updated service

## 🛠️ Troubleshooting

### Common Issues

#### Service Not Starting
- Check logs: `gcloud run services logs read <service-name> --region us-central1`
- Verify Dockerfile and startup scripts
- Check environment variables

#### API Endpoints Not Working
- Verify URL patterns in Django URLs
- Check authentication requirements
- Test with curl or Postman

#### ADK Agent Integration Issues
- Verify `ADK_AGENT_URL` environment variable
- Check network connectivity between services
- Test ADK Agent server directly
- Use ADK Web UI for interactive testing

### Debug Commands
```bash
# Check service status
gcloud run services describe <service-name> --region us-central1

# View recent logs
gcloud run services logs read <service-name> --region us-central1 --limit 50

# Test service health
curl <service-url>/health/

# Test ADK Agent via Web UI
# Open: https://adk-agent-server-277713629269.us-central1.run.app/docs
```

## 📱 Flutter App Integration

### Update Flutter App Configuration
Update the following URLs in your Flutter app:

```dart
// API Configuration
const String baseUrl = 'https://travel-server-staging-277713629269.us-central1.run.app';
const String adkAgentUrl = 'https://adk-agent-server-277713629269.us-central1.run.app';
const String voiceChatUrl = 'https://voice-chat-server-277713629269.us-central1.run.app';

// API Endpoints
const String chatEndpoint = '$baseUrl/api/agent/chat/';
const String authEndpoint = '$baseUrl/api/auth/';
const String userEndpoint = '$baseUrl/api/user_manager/';
```

## 🔐 Security Considerations

- All services are configured with `--allow-unauthenticated` for testing
- For production, implement proper authentication and authorization
- Use Cloud IAM for service-to-service communication
- Enable Cloud Audit Logging for monitoring
- Use Secret Manager for sensitive configuration

## 📈 Scaling

### Current Configuration
- **Django**: 2 CPU, 2GB RAM, max 10 instances
- **ADK Agent**: 1 CPU, 1GB RAM, max 5 instances
- **Voice Chat**: 1 CPU, 1GB RAM, max 5 instances

### Scaling Options
- Adjust CPU and memory allocation
- Increase max instances for higher traffic
- Enable auto-scaling based on metrics
- Use Cloud Load Balancing for global distribution

## 📞 Support

For deployment issues:
1. Check the troubleshooting section
2. Review service logs
3. Test individual components
4. Use ADK Web UI for interactive testing
5. Contact the development team

---

**Last Updated**: July 23, 2025
**Version**: 1.0.0