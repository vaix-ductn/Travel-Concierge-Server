# 🚀 Quick Deployment Guide

## 📋 Prerequisites

1. **Google Cloud CLI** installed and authenticated
2. **Project ID**: `travelapp-461806`
3. **Region**: `us-central1`

## ⚡ Quick Deploy

### For Linux/Mac:
```bash
cd Server/travel_server
chmod +x deploy/quick_deploy.sh
./deploy/quick_deploy.sh
```

### For Windows (PowerShell):
```powershell
cd Server/travel_server
.\deploy\quick_deploy.ps1
```

## 🔧 Manual Deploy

### 1. Deploy Django Server
```bash
# Build
gcloud builds submit --config deploy/django/cloudbuild.yaml

# Deploy
gcloud run deploy django-server \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/django-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --set-env-vars="ENVIRONMENT=production,DB_HOST=127.0.0.1,DB_NAME=travel_concierge,DB_USER=travel_concierge,DB_PASSWORD=TravelConcierge2024!,DB_PORT=3306"
```

### 2. Deploy ADK Agent Server
```bash
# Build
gcloud builds submit --config deploy/adk-agent/adk-agent-cloudbuild.yaml

# Deploy
gcloud run deploy adk-agent-server \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/adk-agent-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8002 \
    --set-env-vars="GOOGLE_CLOUD_API_KEY=AIzaSyAw3l0ADYmXWfAEo-k3a7jWFaqTr3TCJl0,GOOGLE_CLOUD_PROJECT=travelapp-461806,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_PLACES_API_KEY=AIzaSyC6CKHUDCkbDcukn3-U8sG0xkoWGsKv9Xg"
```

## 🧪 Testing

### Test Django Auth
```bash
curl -X POST https://django-server-277713629269.us-central1.run.app/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"nero","password":"1234@pass"}'
```

### Test ADK Web UI
```
https://adk-agent-server-277713629269.us-central1.run.app/dev-ui?app=travel_concierge
```

## 📊 Monitoring

### Check Logs
```bash
# Django logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=django-server" --limit=10

# ADK logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=adk-agent-server" --limit=10
```

### Check Service Status
```bash
gcloud run services list --region=us-central1
```

## 🔗 Service URLs

- **Django Server**: `https://django-server-277713629269.us-central1.run.app`
- **ADK Agent**: `https://adk-agent-server-277713629269.us-central1.run.app`
- **ADK Web UI**: `https://adk-agent-server-277713629269.us-central1.run.app/dev-ui?app=travel_concierge`

## 📚 Full Documentation

See `DEPLOYMENT_GUIDE.md` for complete documentation including:
- Architecture overview
- Troubleshooting guide
- Best practices
- API endpoints

## 🆘 Troubleshooting

### Common Issues:
1. **Database Connection**: Check Cloud SQL Proxy is running
2. **ADK Agent**: Verify all files are copied in Dockerfile
3. **API Keys**: Ensure environment variables are set correctly

### Get Help:
1. Check Cloud Run logs first
2. Verify environment variables
3. Test endpoints individually
4. Review startup scripts

---

**Last Updated**: July 24, 2025
**Version**: 1.0