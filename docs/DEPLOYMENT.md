# Deployment Guide

Complete guide for deploying HypertroQ Backend to Google Cloud Platform.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Google Cloud Setup](#google-cloud-setup)
- [Cloud SQL (Database)](#cloud-sql-database)
- [Cloud Memorystore (Redis)](#cloud-memorystore-redis)
- [Cloud Storage (Media)](#cloud-storage-media)
- [Cloud Run (Application)](#cloud-run-application)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring & Logging](#monitoring--logging)
- [Security](#security)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

---

## Overview

### Architecture

```
                    ┌─────────────┐
                    │   Vercel    │  (Frontend: Next.js)
                    │  Frontend   │
                    └──────┬──────┘
                           │ HTTPS
                           ↓
┌──────────────────────────────────────────────────────┐
│              Google Cloud Platform                    │
│                                                       │
│  ┌──────────────┐      ┌──────────────┐             │
│  │  Cloud Run   │      │  Cloud Build │             │
│  │   (FastAPI)  │◄─────┤   (CI/CD)    │             │
│  └───────┬──────┘      └──────────────┘             │
│          │                                           │
│     ┌────┼────────────────┐                          │
│     ↓    ↓                ↓                          │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Cloud SQL │  │ Memorystore  │  │Cloud Storage │  │
│  │(Postgres)│  │   (Redis)    │  │   (Media)    │  │
│  └──────────┘  └──────────────┘  └──────────────┘  │
│                                                       │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │Secret Manager│  │   Logging    │                 │
│  │  (API Keys)  │  │ & Monitoring │                 │
│  └──────────────┘  └──────────────┘                 │
└──────────────────────────────────────────────────────┘
```

### Components

- **Cloud Run**: Serverless container hosting for FastAPI
- **Cloud SQL**: Managed PostgreSQL database
- **Memorystore**: Managed Redis for caching and sessions
- **Cloud Storage**: Object storage for exercise images/videos
- **Secret Manager**: Secure storage for API keys and secrets
- **Cloud Build**: CI/CD for automated deployments
- **Cloud Logging**: Centralized logging and monitoring

---

## Prerequisites

### Local Setup

1. **Install Google Cloud SDK**:
```bash
# Windows (PowerShell)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe

# macOS/Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

2. **Authenticate**:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

3. **Enable required APIs**:
```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  storage-api.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

### Domain Setup

1. Register domain (e.g., hypertroq.com)
2. Configure DNS to point to Cloud Run
3. Set up SSL certificate (automatic with Cloud Run)

---

## Google Cloud Setup

### Create Project

```bash
# Create new project
gcloud projects create hypertroq-prod --name="HypertroQ Production"

# Set as active project
gcloud config set project hypertroq-prod

# Link billing account
gcloud billing accounts list
gcloud billing projects link hypertroq-prod \
  --billing-account=BILLING_ACCOUNT_ID
```

### Set Default Region

```bash
# Set region (choose closest to users)
gcloud config set run/region us-central1
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
```

---

## Cloud SQL (Database)

### Create PostgreSQL Instance

```bash
# Create instance (db-f1-micro for start, scale up as needed)
gcloud sql instances create hypertroq-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-size=10GB \
  --storage-type=SSD \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=04 \
  --availability-type=zonal

# Set root password
gcloud sql users set-password postgres \
  --instance=hypertroq-db \
  --password=STRONG_PASSWORD_HERE

# Create database
gcloud sql databases create hypertroq \
  --instance=hypertroq-db

# Create application user
gcloud sql users create hypertroq_user \
  --instance=hypertroq-db \
  --password=STRONG_PASSWORD_HERE
```

### Enable Extensions

```bash
# Connect to database
gcloud sql connect hypertroq-db --user=postgres --database=hypertroq

# Run in psql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";  -- For AI embeddings
```

### Connection String

```ini
# For Cloud Run (Unix socket)
DATABASE_URL=postgresql+asyncpg://hypertroq_user:PASSWORD@/hypertroq?host=/cloudsql/hypertroq-prod:us-central1:hypertroq-db

# For local development (public IP)
DATABASE_URL=postgresql+asyncpg://hypertroq_user:PASSWORD@PUBLIC_IP:5432/hypertroq
```

### Enable Public IP (Development Only)

```bash
# Add your IP to authorized networks
gcloud sql instances patch hypertroq-db \
  --authorized-networks=YOUR_PUBLIC_IP/32
```

### Backups

```bash
# Create on-demand backup
gcloud sql backups create \
  --instance=hypertroq-db

# List backups
gcloud sql backups list --instance=hypertroq-db

# Restore from backup
gcloud sql backups restore BACKUP_ID \
  --backup-instance=hypertroq-db \
  --backup-id=BACKUP_ID
```

---

## Cloud Memorystore (Redis)

### Create Redis Instance

```bash
# Create Basic tier Redis (1 GB)
gcloud redis instances create hypertroq-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=basic \
  --zone=us-central1-a

# Get connection details
gcloud redis instances describe hypertroq-redis \
  --region=us-central1 \
  --format="get(host,port)"
```

### Redis Connection

```ini
# Redis URL (internal IP)
REDIS_URL=redis://10.0.0.3:6379/0

# For Celery
CELERY_BROKER_URL=redis://10.0.0.3:6379/0
```

---

## Cloud Storage (Media)

### Create Buckets

```bash
# Public bucket for exercise images/videos
gsutil mb -p hypertroq-prod \
  -c STANDARD \
  -l us-central1 \
  gs://hypertroq-exercises

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://hypertroq-exercises

# Private bucket for user uploads
gsutil mb -p hypertroq-prod \
  -c STANDARD \
  -l us-central1 \
  gs://hypertroq-user-uploads

# Bucket for temporary exports (7-day lifecycle)
gsutil mb -p hypertroq-prod \
  -c STANDARD \
  -l us-central1 \
  gs://hypertroq-exports

# Set lifecycle policy
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 7}
      }
    ]
  }
}
EOF
gsutil lifecycle set lifecycle.json gs://hypertroq-exports
```

### CORS Configuration (if needed)

```bash
cat > cors.json <<EOF
[
  {
    "origin": ["https://hypertroq.com"],
    "method": ["GET", "HEAD", "PUT", "POST"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://hypertroq-exercises
```

---

## Cloud Run (Application)

### Build Docker Image

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/hypertroq-prod/hypertroq-backend
```

### Store Secrets

```bash
# Create secrets in Secret Manager
echo -n "your-64-char-secret-key" | \
  gcloud secrets create SECRET_KEY --data-file=-

echo -n "your-google-api-key" | \
  gcloud secrets create GOOGLE_API_KEY --data-file=-

echo -n "your-lemonsqueezy-api-key" | \
  gcloud secrets create LEMONSQUEEZY_API_KEY --data-file=-

echo -n "webhook-secret" | \
  gcloud secrets create LEMONSQUEEZY_WEBHOOK_SECRET --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding SECRET_KEY \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Repeat for all secrets
```

### Deploy to Cloud Run

```bash
gcloud run deploy hypertroq-backend \
  --image gcr.io/hypertroq-prod/hypertroq-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 1 \
  --memory 512Mi \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars="ENVIRONMENT=production,DEBUG=False,FRONTEND_URL=https://hypertroq.com" \
  --set-secrets="SECRET_KEY=SECRET_KEY:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest,LEMONSQUEEZY_API_KEY=LEMONSQUEEZY_API_KEY:latest,LEMONSQUEEZY_WEBHOOK_SECRET=LEMONSQUEEZY_WEBHOOK_SECRET:latest" \
  --set-cloudsql-instances hypertroq-prod:us-central1:hypertroq-db \
  --vpc-connector projects/hypertroq-prod/locations/us-central1/connectors/hypertroq-connector
```

### Create VPC Connector (for Redis)

```bash
# Create VPC connector for accessing Memorystore
gcloud compute networks vpc-access connectors create hypertroq-connector \
  --region us-central1 \
  --subnet-project hypertroq-prod \
  --subnet default \
  --min-instances 2 \
  --max-instances 3 \
  --machine-type f1-micro
```

### Run Database Migrations

```bash
# One-time migration job
gcloud run jobs create hypertroq-migrate \
  --image gcr.io/hypertroq-prod/hypertroq-backend \
  --command "poetry,run,alembic,upgrade,head" \
  --set-cloudsql-instances hypertroq-prod:us-central1:hypertroq-db \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest"

# Execute migration
gcloud run jobs execute hypertroq-migrate
```

### Configure Custom Domain

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service hypertroq-backend \
  --domain api.hypertroq.com \
  --region us-central1

# Update DNS with provided records
# Cloud Run automatically provisions SSL certificate
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      
      - name: Run tests
        run: poetry run pytest
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
      
      - name: Build and push Docker image
        run: |
          gcloud builds submit --tag gcr.io/hypertroq-prod/hypertroq-backend
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy hypertroq-backend \
            --image gcr.io/hypertroq-prod/hypertroq-backend \
            --region us-central1 \
            --platform managed
      
      - name: Run migrations
        run: |
          gcloud run jobs execute hypertroq-migrate --wait
```

### Set GitHub Secrets

1. Create service account:
```bash
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# Grant permissions
gcloud projects add-iam-policy-binding hypertroq-prod \
  --member="serviceAccount:github-actions@hypertroq-prod.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding hypertroq-prod \
  --member="serviceAccount:github-actions@hypertroq-prod.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@hypertroq-prod.iam.gserviceaccount.com
```

2. Add `GCP_SA_KEY` secret to GitHub repository settings

---

## Monitoring & Logging

### Cloud Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=hypertroq-backend" \
  --limit 50 \
  --format json

# Stream logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=hypertroq-backend"
```

### Metrics & Alerts

1. **Create Uptime Check**:
```bash
# Via Console: Monitoring → Uptime checks → Create
# URL: https://api.hypertroq.com/api/v1/health
```

2. **CPU/Memory Alerts**:
```bash
# Via Console: Monitoring → Alerting → Create Policy
# Condition: CPU > 80% for 5 minutes
# Notification: Email/SMS
```

3. **Error Rate Alerts**:
```bash
# Alert if error rate > 5% for 10 minutes
```

### Sentry Integration

```bash
# Add Sentry DSN to environment
gcloud run services update hypertroq-backend \
  --set-env-vars="SENTRY_DSN=https://xxx@sentry.io/xxx"
```

---

## Security

### IAM Best Practices

1. **Principle of Least Privilege**:
```bash
# Grant only necessary permissions
# Avoid Owner role in production
```

2. **Service Accounts**:
```bash
# Use separate service accounts for each service
# Rotate keys regularly
```

3. **Secret Rotation**:
```bash
# Rotate secrets every 90 days
# Use Secret Manager versioning
```

### Network Security

1. **VPC Configuration**:
- Use private IPs for database and Redis
- VPC connector for Cloud Run access
- Firewall rules to restrict access

2. **HTTPS Only**:
```bash
# Cloud Run enforces HTTPS by default
# Redirect HTTP → HTTPS in app
```

3. **CORS Configuration**:
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hypertroq.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### DDoS Protection

```bash
# Enable Cloud Armor (requires Load Balancer)
gcloud compute security-policies create hypertroq-policy \
  --description "DDoS protection"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy hypertroq-policy \
  --expression "true" \
  --action rate-based-ban \
  --rate-limit-threshold-count 100 \
  --rate-limit-threshold-interval-sec 60
```

---

## Scaling

### Auto-Scaling Configuration

```bash
# Update scaling settings
gcloud run services update hypertroq-backend \
  --min-instances 1 \
  --max-instances 50 \
  --cpu 2 \
  --memory 1Gi \
  --concurrency 100
```

### Database Scaling

```bash
# Upgrade instance tier
gcloud sql instances patch hypertroq-db \
  --tier=db-custom-2-7680

# Enable high availability
gcloud sql instances patch hypertroq-db \
  --availability-type=REGIONAL
```

### Redis Scaling

```bash
# Upgrade to Standard tier (HA + larger size)
gcloud redis instances update hypertroq-redis \
  --size=5 \
  --tier=standard-ha \
  --region=us-central1
```

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 100

# Common causes:
# - Missing environment variables
# - Database connection failed
# - Invalid secret references
```

#### 2. Database Connection Timeout

```bash
# Verify Cloud SQL connector is attached
gcloud run services describe hypertroq-backend --format="value(spec.template.spec.containers[0].env)"

# Check if service account has cloudsql.client role
```

#### 3. Redis Connection Failed

```bash
# Verify VPC connector
gcloud compute networks vpc-access connectors describe hypertroq-connector --region=us-central1

# Check Redis IP is correct in REDIS_URL
```

#### 4. High Latency

```bash
# Check if too many cold starts (increase min-instances)
gcloud run services update hypertroq-backend --min-instances 2

# Check database connection pool size
# Increase --cpu and --memory if needed
```

#### 5. Out of Memory

```bash
# Increase memory allocation
gcloud run services update hypertroq-backend --memory 1Gi

# Check for memory leaks in application code
```

---

## Cost Optimization

### Current Pricing Estimates

**Cloud Run** (1M requests/month):
- 1 vCPU, 512 MB: ~$10/month
- 2 vCPU, 1 GB: ~$20/month

**Cloud SQL** (db-f1-micro):
- Instance: ~$7/month
- Storage (10 GB): ~$2/month

**Memorystore** (Basic, 1 GB):
- ~$35/month

**Cloud Storage** (10 GB):
- ~$0.20/month

**Total estimated**: ~$55-75/month for starter setup

### Optimization Tips

1. **Use minimum instances = 0** for development
2. **Set max instances** to prevent runaway costs
3. **Use lifecycle policies** for Cloud Storage
4. **Monitor usage** with billing alerts
5. **Clean up unused resources**:
```bash
# List all Cloud Run services
gcloud run services list

# Delete unused services
gcloud run services delete SERVICE_NAME
```

---

## Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] Secrets stored in Secret Manager
- [ ] Database migrations applied
- [ ] Database seeded with initial data
- [ ] CORS origins updated
- [ ] Domain configured and SSL enabled
- [ ] Monitoring and alerts set up
- [ ] Backups enabled
- [ ] CI/CD pipeline tested

### Post-Deployment

- [ ] Health check passes
- [ ] Authentication works
- [ ] Database connectivity confirmed
- [ ] Redis connectivity confirmed
- [ ] Logs are being collected
- [ ] Metrics are being recorded
- [ ] Alerts are triggering correctly
- [ ] Performance is acceptable

---

## Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Memorystore for Redis](https://cloud.google.com/memorystore/docs/redis)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Build](https://cloud.google.com/build/docs)

---

**Deployment successful! 🚀**
