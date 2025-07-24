# 🚀 Travel Concierge - Google Cloud Deployment Guide

## 📋 Tổng quan

Tài liệu này hướng dẫn deploy Travel Concierge application lên Google Cloud Platform, bao gồm:
- **Django Server**: REST API backend với authentication
- **ADK Agent Server**: AI Agent cho travel planning
- **Cloud SQL**: MySQL database
- **Cloud Run**: Containerized services

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flutter App   │    │   Django API    │    │   ADK Agent     │
│                 │◄──►│   Server        │◄──►│   Server        │
│   (Mobile)      │    │   (Cloud Run)   │    │   (Cloud Run)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────────────────────────────┐
                       │           Cloud SQL                    │
                       │         (MySQL Database)               │
                       └─────────────────────────────────────────┘
```

## 🔧 Prerequisites

### 1. Google Cloud Project Setup
```bash
# Set project ID
export PROJECT_ID=travelapp-461806
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Cloud SQL Instance
```bash
# Create Cloud SQL instance (if not exists)
gcloud sql instances create travel-concierge-db \
    --database-version=MYSQL_8_0 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=TravelConcierge2024!

# Create database and user
gcloud sql databases create travel_concierge --instance=travel-concierge-db
gcloud sql users create travel_concierge \
    --instance=travel-concierge-db \
    --password=TravelConcierge2024!
```

### 3. Artifact Registry
```bash
# Create repository for Docker images
gcloud artifacts repositories create travel-server-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Travel Server Docker Repository"
```

## 🐳 Docker Images

### 1. Django Server Image
**File:** `deploy/django/Dockerfile.production`

**Build Command:**
```bash
cd Server/travel_server
gcloud builds submit --config deploy/django/cloudbuild.yaml
```

**Deploy Command:**
```bash
gcloud run deploy django-server \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/django-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --set-env-vars="ENVIRONMENT=production,DB_HOST=127.0.0.1,DB_NAME=travel_concierge,DB_USER=travel_concierge,DB_PASSWORD=TravelConcierge2024!,DB_PORT=3306"
```

### 2. ADK Agent Server Image
**File:** `deploy/adk-agent/adk-agent.Dockerfile`

**Build Command:**
```bash
cd Server/travel_server
gcloud builds submit --config deploy/adk-agent/adk-agent-cloudbuild.yaml
```

**Deploy Command:**
```bash
gcloud run deploy adk-agent-server \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/adk-agent-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8002 \
    --set-env-vars="GOOGLE_CLOUD_API_KEY=AIzaSyAw3l0ADYmXWfAEo-k3a7jWFaqTr3TCJl0,GOOGLE_CLOUD_PROJECT=travelapp-461806,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_PLACES_API_KEY=AIzaSyC6CKHUDCkbDcukn3-U8sG0xkoWGsKv9Xg"
```

## 🔄 Startup Scripts

### 1. Django Server Startup Script
**File:** `deploy/start_production.sh`

```bash
#!/bin/bash

# Production startup script for Travel Server
# Runs both Django application and ADK Agent server

# Function to cleanup child processes
cleanup() {
    echo "Received SIGTERM/SIGINT, cleaning up..."
    echo "Stopping ADK Agent server (PID: $ADK_PID)..."
    kill $ADK_PID 2>/dev/null
    echo "Stopping Django server (PID: $DJANGO_PID)..."
    kill $DJANGO_PID 2>/dev/null
    if [ ! -z "$CLOUD_SQL_PID" ]; then
        echo "Stopping Cloud SQL Proxy (PID: $CLOUD_SQL_PID)..."
        kill $CLOUD_SQL_PID 2>/dev/null
    fi
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Create log directory if it doesn't exist
mkdir -p logs

# Start Cloud SQL Proxy if using Cloud SQL
if [ "$ENVIRONMENT" = "production" ] && [ "$DB_HOST" = "127.0.0.1" ]; then
    echo "Starting Cloud SQL Proxy..."
    /usr/local/bin/cloud_sql_proxy -instances=travelapp-461806:us-central1:travel-concierge-db=tcp:3306 &
    CLOUD_SQL_PID=$!

    # Wait for Cloud SQL Proxy to be ready
    echo "Waiting for Cloud SQL Proxy..."
    sleep 5

    # Wait for database to be ready
    echo "Waiting for database..."
    while ! nc -z 127.0.0.1 3306; do
        sleep 1
    done
    echo "Database is ready!"
elif [ ! -z "$DB_HOST" ]; then
    echo "Waiting for database..."
    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 1
    done
    echo "Database is ready!"
fi

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Start ADK Agent server in the background
echo "Starting ADK Agent server..."
adk api_server travel_concierge --host 0.0.0.0 --port 8002 &
ADK_PID=$!

# Check if ADK server started successfully
sleep 3
if ! ps -p $ADK_PID > /dev/null; then
    echo "Failed to start ADK Agent server"
    exit 1
fi

echo "ADK Agent server started successfully (PID: $ADK_PID) on port 8002"

# Start Django application
echo "Starting Django application..."
gunicorn --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --worker-class gthread \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    config.wsgi:application &
DJANGO_PID=$!

# Check if Django started successfully
sleep 3
if ! ps -p $DJANGO_PID > /dev/null; then
    echo "Failed to start Django application"
    exit 1
fi

echo "Django application started successfully (PID: $DJANGO_PID) on port 8000"

# Wait for both processes
wait
```

### 2. ADK Agent Startup Script
**File:** `deploy/adk-agent/start_server.py`

```python
#!/usr/bin/env python3
"""
ADK Agent Server Startup Script
"""

import os
import sys
import subprocess
import signal
import time

def signal_handler(signum, frame):
    print(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Start ADK server
    cmd = [
        "adk", "api_server", "travel_concierge",
        "--host", "0.0.0.0",
        "--port", "8002"
    ]

    print("Starting ADK Agent server...")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ADK server failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("ADK server stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

## 🔐 Environment Variables

### Django Server Environment Variables
```bash
ENVIRONMENT=production
DB_HOST=127.0.0.1
DB_NAME=travel_concierge
DB_USER=travel_concierge
DB_PASSWORD=TravelConcierge2024!
DB_PORT=3306
```

### ADK Agent Environment Variables
```bash
GOOGLE_CLOUD_API_KEY=AIzaSyAw3l0ADYmXWfAEo-k3a7jWFaqTr3TCJl0
GOOGLE_CLOUD_PROJECT=travelapp-461806
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_PLACES_API_KEY=AIzaSyC6CKHUDCkbDcukn3-U8sG0xkoWGsKv9Xg
```

## 🚀 Deployment Commands

### 1. Deploy Django Server
```bash
# Build and deploy Django server
cd Server/travel_server

# Build Docker image
gcloud builds submit --config deploy/django/cloudbuild.yaml

# Deploy to Cloud Run
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
# Build and deploy ADK agent server
cd Server/travel_server

# Build Docker image
gcloud builds submit --config deploy/adk-agent/adk-agent-cloudbuild.yaml

# Deploy to Cloud Run
gcloud run deploy adk-agent-server \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/adk-agent-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8002 \
    --set-env-vars="GOOGLE_CLOUD_API_KEY=AIzaSyAw3l0ADYmXWfAEo-k3a7jWFaqTr3TCJl0,GOOGLE_CLOUD_PROJECT=travelapp-461806,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_PLACES_API_KEY=AIzaSyC6CKHUDCkbDcukn3-U8sG0xkoWGsKv9Xg"
```

## 🧪 Testing

### 1. Test Django Auth Login
```bash
# Test authentication endpoint
curl -X POST https://django-server-277713629269.us-central1.run.app/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"nero","password":"1234@pass"}'
```

### 2. Test ADK Web UI
```bash
# Access ADK web UI
open https://adk-agent-server-277713629269.us-central1.run.app/dev-ui?app=travel_concierge
```

### 3. Check Service Status
```bash
# List Cloud Run services
gcloud run services list --region=us-central1

# Check service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=django-server" --limit=10
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=adk-agent-server" --limit=10
```

## 📊 Monitoring

### 1. Cloud Run Metrics
```bash
# View service metrics
gcloud run services describe django-server --region=us-central1
gcloud run services describe adk-agent-server --region=us-central1
```

### 2. Cloud SQL Monitoring
```bash
# Check database status
gcloud sql instances describe travel-concierge-db
```

### 3. Logs
```bash
# Django server logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=django-server" --limit=20

# ADK agent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=adk-agent-server" --limit=20
```

## 🔧 Troubleshooting

### 1. Database Connection Issues
**Problem:** `UnicodeError: encoding with 'idna' codec failed (UnicodeError: label too long)`

**Solution:**
- Ensure Cloud SQL Proxy is running
- Check environment variables are set correctly
- Verify Cloud SQL instance is accessible

### 2. ADK Agent Issues
**Problem:** `"module 'travel_concierge' has no attribute 'agent'"`

**Solution:**
- Ensure all required files are copied in Dockerfile
- Check `__init__.py` and `prompt.py` are included
- Verify ADK installation

### 3. API Key Issues
**Problem:** `"Missing key inputs argument! To use the Google AI API, provide (api_key) arguments"`

**Solution:**
- Set environment variables correctly
- Ensure `.env` file is copied to container
- Verify API keys are valid

### 4. Service Not Starting
**Problem:** Service fails to start or returns 404

**Solution:**
- Check startup script permissions
- Verify Docker image builds successfully
- Check Cloud Run logs for errors

## 📝 Quick Deploy Script

Create a quick deploy script for easy deployment:

```bash
#!/bin/bash
# quick_deploy.sh

set -e

echo "🚀 Starting Travel Concierge deployment..."

# Build and deploy Django server
echo "📦 Building Django server..."
gcloud builds submit --config deploy/django/cloudbuild.yaml

echo "🚀 Deploying Django server..."
gcloud run deploy django-server \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/django-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --set-env-vars="ENVIRONMENT=production,DB_HOST=127.0.0.1,DB_NAME=travel_concierge,DB_USER=travel_concierge,DB_PASSWORD=TravelConcierge2024!,DB_PORT=3306"

# Build and deploy ADK agent server
echo "📦 Building ADK agent server..."
gcloud builds submit --config deploy/adk-agent/adk-agent-cloudbuild.yaml

echo "🚀 Deploying ADK agent server..."
gcloud run deploy adk-agent-server \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/adk-agent-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8002 \
    --set-env-vars="GOOGLE_CLOUD_API_KEY=AIzaSyAw3l0ADYmXWfAEo-k3a7jWFaqTr3TCJl0,GOOGLE_CLOUD_PROJECT=travelapp-461806,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_PLACES_API_KEY=AIzaSyC6CKHUDCkbDcukn3-U8sG0xkoWGsKv9Xg"

echo "✅ Deployment completed successfully!"
echo "🌐 Django Server: https://django-server-277713629269.us-central1.run.app"
echo "🤖 ADK Agent: https://adk-agent-server-277713629269.us-central1.run.app"
```

## 🔗 Service URLs

- **Django Server**: `https://django-server-277713629269.us-central1.run.app`
- **ADK Agent Server**: `https://adk-agent-server-277713629269.us-central1.run.app`
- **ADK Web UI**: `https://adk-agent-server-277713629269.us-central1.run.app/dev-ui?app=travel_concierge`

## 📚 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `GET /api/auth/verify/` - Token verification
- `POST /api/auth/logout/` - User logout

### User Management
- `GET /api/user_manager/profile/` - Get user profile
- `PUT /api/user_manager/profile/` - Update user profile

### Travel Services
- `POST /api/travel/recommendations/` - Get travel recommendations
- `GET /api/travel/tools/status/` - Check tools status

### AI Agent
- `POST /api/agent/chat/` - Chat with AI agent
- `GET /api/agent/status/` - Check agent status
- `GET /api/agent/sub-agents/` - List sub-agents

## 🎯 Best Practices

1. **Environment Variables**: Always use environment variables for sensitive data
2. **Health Checks**: Implement proper health checks for services
3. **Logging**: Use structured logging for better debugging
4. **Monitoring**: Set up alerts for service failures
5. **Security**: Use least privilege principle for service accounts
6. **Backup**: Regular database backups
7. **Testing**: Test deployments in staging environment first

## 📞 Support

For issues and questions:
1. Check Cloud Run logs first
2. Verify environment variables
3. Test endpoints individually
4. Check Cloud SQL connectivity
5. Review startup scripts

---

**Last Updated:** July 24, 2025
**Version:** 1.0
**Author:** Travel Concierge Team