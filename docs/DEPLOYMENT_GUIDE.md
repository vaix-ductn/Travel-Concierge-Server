# 🚀 Travel Server - Google Cloud Deployment Guide

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Deployment](#manual-deployment)
- [GitHub Actions Setup](#github-actions-setup)
- [Environment Configuration](#environment-configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

---

## 🛠 Prerequisites

### 1. Required Tools

**Install Google Cloud SDK:**
```bash
# macOS (using Homebrew)
brew install google-cloud-sdk

# Ubuntu/Debian
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows (download installer)
# https://cloud.google.com/sdk/docs/install
```

**Install Docker:**
```bash
# macOS
brew install docker

# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# Windows (download Docker Desktop)
# https://www.docker.com/products/docker-desktop
```

**Install Git (if not already installed):**
```bash
# Most systems have git pre-installed
git --version
```

### 2. Google Cloud Setup

**Create Google Cloud Project:**
```bash
# Create new project
gcloud projects create travel-concierge-prod --name="Travel Concierge Production"
gcloud projects create travel-concierge-staging --name="Travel Concierge Staging"

# Set current project
gcloud config set project travel-concierge-prod
```

**Enable Billing:**
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Navigate to Billing and link a billing account

**Authenticate:**
```bash
# Login to Google Cloud
gcloud auth login

# Set application default credentials
gcloud auth application-default login
```

---

## ⚡ Quick Start

### Option 1: One-Command Deployment

```bash
# Clone the repository
git clone https://github.com/your-username/travel-concierge.git
cd travel-concierge/Server/travel_server

# Make deployment script executable
chmod +x deploy/cloud-deploy.sh

# Deploy to staging (includes infrastructure setup)
./deploy/cloud-deploy.sh staging full

# Deploy to production
./deploy/cloud-deploy.sh production full
```

### Option 2: Step-by-Step Deployment

```bash
# 1. Setup infrastructure
./deploy/cloud-deploy.sh staging setup-infra

# 2. Deploy application
./deploy/cloud-deploy.sh staging deploy

# 3. Verify deployment
curl https://travel-server-staging-[hash]-uc.a.run.app/health/
```

---

## 🔧 Manual Deployment

### Step 1: Configure Environment

**Edit deployment configuration:**
```bash
# Edit deploy/deploy-config.yaml
nano deploy/deploy-config.yaml
```

**Update project IDs:**
```yaml
staging:
  project_id: "your-staging-project-id"

production:
  project_id: "your-production-project-id"
```

### Step 2: Setup Infrastructure

**Enable required APIs:**
```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  storage-component.googleapis.com \
  artifactregistry.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  --project=your-project-id
```

**Create Artifact Registry:**
```bash
gcloud artifacts repositories create travel-server-repo \
  --repository-format=docker \
  --location=us-central1 \
  --project=your-project-id
```

**Setup Cloud SQL:**
```bash
# Create MySQL instance
gcloud sql instances create travel-db-staging \
  --database-version=MYSQL_8_0 \
  --cpu=1 \
  --memory=3.75GB \
  --region=us-central1 \
  --project=your-project-id

# Create database
gcloud sql databases create travel_concierge \
  --instance=travel-db-staging \
  --project=your-project-id
```

**Create Storage Bucket:**
```bash
gsutil mb -l us-central1 gs://your-project-id-travel-storage-staging
```

### Step 3: Build and Deploy

**Configure Docker for Artifact Registry:**
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

**Build and push image:**
```bash
# Build image
docker build -t us-central1-docker.pkg.dev/your-project-id/travel-server-repo/travel-server:latest \
  -f deploy/Dockerfile.production .

# Push image
docker push us-central1-docker.pkg.dev/your-project-id/travel-server-repo/travel-server:latest
```

**Deploy to Cloud Run:**
```bash
gcloud run deploy travel-server-staging \
  --image=us-central1-docker.pkg.dev/your-project-id/travel-server-repo/travel-server:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8000 \
  --memory=2Gi \
  --cpu=1 \
  --max-instances=10 \
  --min-instances=1 \
  --set-env-vars="ENVIRONMENT=staging,GOOGLE_CLOUD_PROJECT=your-project-id" \
  --set-cloudsql-instances=your-project-id:us-central1:travel-db-staging \
  --project=your-project-id
```

### Step 4: Run Migrations

```bash
# Create migration job
gcloud run jobs create travel-server-staging-migration \
  --image=us-central1-docker.pkg.dev/your-project-id/travel-server-repo/travel-server:latest \
  --region=us-central1 \
  --set-cloudsql-instances=your-project-id:us-central1:travel-db-staging \
  --set-env-vars="ENVIRONMENT=staging,GOOGLE_CLOUD_PROJECT=your-project-id" \
  --command="python" \
  --args="manage.py,migrate" \
  --project=your-project-id

# Execute migration
gcloud run jobs execute travel-server-staging-migration \
  --region=us-central1 \
  --project=your-project-id \
  --wait
```

---

## 🔄 GitHub Actions Setup

### Step 1: Setup Workload Identity Federation

**Create Workload Identity Pool:**
```bash
gcloud iam workload-identity-pools create "github-pool" \
  --location="global" \
  --description="Pool for GitHub Actions" \
  --project=your-project-id
```

**Create Workload Identity Provider:**
```bash
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --project=your-project-id
```

**Create Service Account:**
```bash
gcloud iam service-accounts create "github-actions-sa" \
  --description="Service account for GitHub Actions" \
  --project=your-project-id
```

**Bind Service Account:**
```bash
gcloud iam service-accounts add-iam-policy-binding \
  "github-actions-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe your-project-id --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/attribute.repository/your-username/travel-concierge" \
  --project=your-project-id
```

**Grant Permissions:**
```bash
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/cloudsql.admin"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"
```

### Step 2: Configure GitHub Secrets

**Add the following secrets in your GitHub repository:**

```
# Workload Identity Federation
WIF_PROVIDER: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider
WIF_SERVICE_ACCOUNT: github-actions-sa@your-project-id.iam.gserviceaccount.com

# Project IDs
GOOGLE_CLOUD_PROJECT_STAGING: your-staging-project-id
GOOGLE_CLOUD_PROJECT_PRODUCTION: your-production-project-id
```

### Step 3: Trigger Deployment

**Push to staging branch:**
```bash
git checkout -b staging
git push origin staging
```

**Push to main branch for production:**
```bash
git checkout main
git push origin main
```

**Manual deployment:**
- Go to Actions tab in GitHub
- Run "Deploy Travel Server to Google Cloud" workflow
- Select environment

---

## ⚙️ Environment Configuration

### Environment Variables

**Staging Environment:**
```bash
# Core settings
ENVIRONMENT=staging
DEBUG=false
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=mysql://user:password@/database?unix_socket=/cloudsql/project:region:instance

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/etc/gcp/service-account.json

# Storage
STORAGE_BUCKET=your-project-id-travel-storage-staging

# API Keys
GOOGLE_GENAI_USE_VERTEXAI=TRUE
VERTEX_AI_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1
```

**Production Environment:**
```bash
# Core settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-production-secret-key

# Additional security
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_CONTENT_TYPE_NOSNIFF=true
SECURE_BROWSER_XSS_FILTER=true
```

### Secret Management

**Store secrets in Secret Manager:**
```bash
# Create secrets
echo -n "your-secret-key" | gcloud secrets create django-secret-key --data-file=-
echo -n "your-db-password" | gcloud secrets create db-password --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding django-secret-key \
  --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 📊 Monitoring and Maintenance

### Health Checks

**Application health endpoint:**
```bash
curl https://your-service-url/health/
```

**Database connectivity:**
```bash
curl https://your-service-url/health/database/
```

### Logging

**View application logs:**
```bash
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=travel-server-staging" \
  --limit=50 \
  --project=your-project-id
```

**Real-time logs:**
```bash
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=travel-server-staging" \
  --project=your-project-id
```

### Monitoring

**Set up uptime checks:**
```bash
# Create uptime check
gcloud alpha monitoring uptime create \
  --display-name="Travel Server Uptime" \
  --resource-type=url \
  --host=your-service-url \
  --path=/health/ \
  --project=your-project-id
```

### Backup and Recovery

**Database backups:**
```bash
# Manual backup
gcloud sql backups create \
  --instance=travel-db-staging \
  --project=your-project-id

# List backups
gcloud sql backups list \
  --instance=travel-db-staging \
  --project=your-project-id
```

**Restore from backup:**
```bash
gcloud sql backups restore BACKUP_ID \
  --restore-instance=travel-db-staging \
  --project=your-project-id
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Cloud SQL Connection Issues:**
```bash
# Check if Cloud SQL Admin API is enabled
gcloud services list --enabled --filter="name:sqladmin.googleapis.com"

# Test connection with Cloud SQL Proxy
cloud_sql_proxy -instances=your-project-id:us-central1:travel-db-staging=tcp:3306
```

**2. Build Failures:**
```bash
# Check build logs
gcloud builds log BUILD_ID --project=your-project-id

# Check container image
gcloud container images list --repository=us-central1-docker.pkg.dev/your-project-id/travel-server-repo
```

**3. Memory Issues:**
```bash
# Increase memory allocation
gcloud run services update travel-server-staging \
  --memory=4Gi \
  --region=us-central1 \
  --project=your-project-id
```

**4. Permission Issues:**
```bash
# Check service account permissions
gcloud projects get-iam-policy your-project-id \
  --flatten="bindings[].members" \
  --format="table(bindings.role,bindings.members)"
```

### Debug Commands

**Check service status:**
```bash
gcloud run services describe travel-server-staging \
  --region=us-central1 \
  --project=your-project-id
```

**View service logs:**
```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=100 \
  --project=your-project-id
```

**Test local container:**
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///db.sqlite3 \
  -e DEBUG=true \
  us-central1-docker.pkg.dev/your-project-id/travel-server-repo/travel-server:latest
```

---

## 💰 Cost Optimization

### Resource Sizing

**Staging Environment:**
- Cloud Run: 1 CPU, 2GB RAM, min 0 instances
- Cloud SQL: db-f1-micro, 10GB storage
- Storage: Standard class

**Production Environment:**
- Cloud Run: 2 CPU, 4GB RAM, min 1-2 instances
- Cloud SQL: db-standard-2, 100GB storage
- Storage: Standard class with lifecycle policy

### Cost Monitoring

**Set up billing alerts:**
```bash
# Create budget
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Travel Server Budget" \
  --budget-amount=100USD \
  --threshold-rules-percent=80,100 \
  --notification-channels=NOTIFICATION_CHANNEL_ID
```

**Monitor costs:**
```bash
# Export billing data to BigQuery
gcloud logging sinks create travel-server-billing-export \
  bigquery.googleapis.com/projects/your-project-id/datasets/billing_export
```

---

## 🔗 Useful Links

- [Google Cloud Console](https://console.cloud.google.com)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Django on Google Cloud](https://cloud.google.com/python/django)

---

## 📞 Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review application logs in Google Cloud Console
3. Check GitHub Actions workflow logs
4. Create an issue in the project repository

**Emergency contacts:**
- DevOps Team: devops@travel-concierge.com
- On-call Engineer: +1-XXX-XXX-XXXX

---

*Last updated: January 2025*