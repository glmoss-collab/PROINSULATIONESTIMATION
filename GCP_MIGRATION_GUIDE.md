# GCP Enterprise Integration Guide

## Professional Insulation Estimation System - Cloud Migration

This document provides a comprehensive pathway for migrating the Professional Insulation Estimation System from a local deployment to Google Cloud Platform (GCP) enterprise infrastructure.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Migration Phases](#migration-phases)
3. [Infrastructure Components](#infrastructure-components)
4. [Code Changes Required](#code-changes-required)
5. [Security Configuration](#security-configuration)
6. [Deployment Instructions](#deployment-instructions)
7. [Cost Estimation](#cost-estimation)
8. [Monitoring & Observability](#monitoring--observability)

---

## Architecture Overview

### Target Architecture

```
                                    ┌─────────────────────────────────────┐
                                    │         INTERNET                    │
                                    └──────────────┬──────────────────────┘
                                                   │
                                    ┌──────────────▼──────────────────────┐
                                    │   Cloud Load Balancer + Cloud CDN   │
                                    │   • SSL/TLS termination             │
                                    │   • DDoS protection (Cloud Armor)   │
                                    └──────────────┬──────────────────────┘
                                                   │
                                    ┌──────────────▼──────────────────────┐
                                    │   Identity-Aware Proxy (IAP)        │
                                    │   • Google Workspace authentication │
                                    │   • Zero-trust access control       │
                                    └──────────────┬──────────────────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    │                              │                              │
         ┌──────────▼──────────┐      ┌───────────▼───────────┐      ┌───────────▼───────────┐
         │    Cloud Run        │      │    Cloud Run          │      │    Cloud Run          │
         │  Streamlit App      │      │  Agent API            │      │  Background Workers   │
         │  (Frontend)         │      │  (Backend)            │      │  (Batch Processing)   │
         │  Port: $PORT        │      │  Port: $PORT          │      │  Port: $PORT          │
         └─────────┬───────────┘      └───────────┬───────────┘      └───────────┬───────────┘
                   │                              │                              │
                   └──────────────────────────────┼──────────────────────────────┘
                                                  │
         ┌────────────────────────────────────────┼────────────────────────────────────────┐
         │                                        │                                        │
┌────────▼────────┐              ┌────────────────▼────────────────┐              ┌────────▼────────┐
│  Secret Manager │              │         Firestore               │              │  Cloud Storage  │
│  • API Keys     │              │  • Session cache                │              │  • PDF uploads  │
│  • Credentials  │              │  • API response cache           │              │  • Quotes       │
│                 │              │  • User preferences             │              │  • Audit logs   │
└─────────────────┘              └─────────────────────────────────┘              └─────────────────┘
                                                  │
                                 ┌────────────────┴────────────────┐
                                 │      External APIs              │
                                 │  • Anthropic Claude API         │
                                 │  • Vertex AI (Gemini)           │
                                 └─────────────────────────────────┘
```

### Current vs. Target State

| Component | Current State | Target State (GCP) |
|-----------|--------------|-------------------|
| **Compute** | Local Docker/VM | Cloud Run (serverless) |
| **Caching** | File-based (`.cache/`) | Firestore + Redis (Memorystore) |
| **File Storage** | Local filesystem | Cloud Storage (GCS) |
| **Secrets** | Environment variables | Secret Manager |
| **Logging** | Python logging | Cloud Logging |
| **Monitoring** | None | Cloud Monitoring |
| **Authentication** | None | Identity-Aware Proxy (IAP) |
| **AI Services** | Direct API calls | Vertex AI (optional) |

---

## Migration Phases

### Phase 1: Foundation (Week 1-2)

**Goal:** Establish cloud-native infrastructure patterns

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Update Dockerfile for Cloud Run | P0 | 4h | ⬜ |
| Create cloud_config.py | P0 | 4h | ⬜ |
| Create gcs_storage.py | P0 | 8h | ⬜ |
| Create firestore_cache.py | P0 | 8h | ⬜ |
| Create secrets_manager.py | P1 | 4h | ⬜ |
| Update requirements.txt | P1 | 1h | ⬜ |
| Create cloudbuild.yaml | P1 | 4h | ⬜ |

### Phase 2: Integration (Week 2-3)

**Goal:** Integrate cloud services into application

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Update streamlit_app.py for GCS | P0 | 8h | ⬜ |
| Update agent_estimation_app.py for GCS | P0 | 8h | ⬜ |
| Update utils_cache.py with Firestore backend | P0 | 6h | ⬜ |
| Update gemini_pdf_extractor.py | P1 | 4h | ⬜ |
| Add Cloud Logging integration | P1 | 4h | ⬜ |

### Phase 3: Security & Observability (Week 3-4)

**Goal:** Enterprise-grade security and monitoring

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Configure Identity-Aware Proxy | P1 | 4h | ⬜ |
| Set up Cloud Monitoring dashboards | P1 | 4h | ⬜ |
| Configure alerting policies | P2 | 2h | ⬜ |
| Security review and hardening | P1 | 8h | ⬜ |
| Load testing | P2 | 4h | ⬜ |

### Phase 4: Production Deployment (Week 4)

**Goal:** Go-live with production environment

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Deploy to production Cloud Run | P0 | 4h | ⬜ |
| Configure production secrets | P0 | 2h | ⬜ |
| Set up CI/CD pipeline | P1 | 4h | ⬜ |
| Documentation and runbooks | P1 | 4h | ⬜ |

---

## Infrastructure Components

### 1. Cloud Run Configuration

```yaml
# cloudrun-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: hvac-estimator
  labels:
    app: hvac-estimator
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "100"
        autoscaling.knative.dev/minScale: "1"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      serviceAccountName: hvac-estimator-sa@PROJECT_ID.iam.gserviceaccount.com
      containerConcurrency: 10
      timeoutSeconds: 300
      containers:
        - image: gcr.io/PROJECT_ID/hvac-estimator:latest
          ports:
            - containerPort: 8501
          env:
            - name: GCP_PROJECT
              value: "PROJECT_ID"
            - name: CACHE_BACKEND
              value: "firestore"
            - name: STORAGE_BACKEND
              value: "gcs"
            - name: GCS_BUCKET
              value: "hvac-estimator-uploads"
          resources:
            limits:
              cpu: "2"
              memory: "2Gi"
```

### 2. IAM Service Account Permissions

```bash
# Required roles for Cloud Run service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:hvac-estimator-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:hvac-estimator-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:hvac-estimator-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:hvac-estimator-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:hvac-estimator-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"
```

### 3. Cloud Storage Bucket Configuration

```bash
# Create bucket for PDF uploads and quotes
gsutil mb -l us-central1 gs://hvac-estimator-uploads

# Set lifecycle policy (auto-delete after 30 days)
gsutil lifecycle set lifecycle.json gs://hvac-estimator-uploads

# lifecycle.json
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 30}
    }
  ]
}

# Enable CORS for Streamlit downloads
gsutil cors set cors.json gs://hvac-estimator-uploads
```

### 4. Firestore Configuration

```bash
# Create Firestore database in native mode
gcloud firestore databases create --location=us-central1

# Recommended indexes (firestore.indexes.json)
{
  "indexes": [
    {
      "collectionGroup": "cache",
      "fields": [
        {"fieldPath": "expires_at", "order": "ASCENDING"}
      ]
    }
  ]
}
```

### 5. Secret Manager Setup

```bash
# Create secrets
echo -n "sk-ant-api..." | gcloud secrets create anthropic-api-key --data-file=-
echo -n "AIza..." | gcloud secrets create gemini-api-key --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member="serviceAccount:hvac-estimator-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Code Changes Required

### New Files to Create

| File | Purpose | Lines |
|------|---------|-------|
| `cloud_config.py` | Centralized configuration management | ~200 |
| `gcs_storage.py` | Cloud Storage abstraction layer | ~250 |
| `firestore_cache.py` | Firestore cache backend | ~300 |
| `secrets_manager.py` | Secret Manager integration | ~150 |
| `cloud_logging_config.py` | Cloud Logging setup | ~100 |
| `cloudbuild.yaml` | CI/CD pipeline configuration | ~50 |

### Files to Modify

| File | Changes Required |
|------|-----------------|
| `Dockerfile` | Multi-stage build, $PORT env var, non-root user |
| `requirements.txt` | Add GCP client libraries |
| `utils_cache.py` | Add Firestore backend option |
| `streamlit_app.py` | Replace tempfile with GCS |
| `agent_estimation_app.py` | Replace tempfile with GCS |
| `gemini_pdf_extractor.py` | Use Secret Manager for API keys |

---

## Security Configuration

### Identity-Aware Proxy (IAP) Setup

1. **Enable IAP API**
   ```bash
   gcloud services enable iap.googleapis.com
   ```

2. **Configure OAuth consent screen**
   - Go to APIs & Services > OAuth consent screen
   - Configure for Internal use (Google Workspace)

3. **Enable IAP for Cloud Run**
   ```bash
   gcloud iap web enable \
     --resource-type=cloud-run \
     --service=hvac-estimator
   ```

4. **Grant user access**
   ```bash
   gcloud iap web add-iam-policy-binding \
     --member="user:employee@company.com" \
     --role="roles/iap.httpsResourceAccessor" \
     --resource-type=cloud-run \
     --service=hvac-estimator
   ```

### VPC Service Controls (Optional)

For additional security, configure VPC Service Controls:

```bash
# Create access policy
gcloud access-context-manager policies create \
  --organization=ORG_ID \
  --title="HVAC Estimator Policy"

# Create service perimeter
gcloud access-context-manager perimeters create hvac-perimeter \
  --policy=POLICY_ID \
  --title="HVAC Estimator Perimeter" \
  --resources="projects/PROJECT_NUMBER" \
  --restricted-services="storage.googleapis.com,firestore.googleapis.com"
```

---

## Deployment Instructions

### Local Development

```bash
# Use local file-based cache and storage
export CACHE_BACKEND=file
export STORAGE_BACKEND=local
export ANTHROPIC_API_KEY=your-key

streamlit run agent_estimation_app.py
```

### GCP Staging

```bash
# Build and push container
gcloud builds submit --tag gcr.io/PROJECT_ID/hvac-estimator:staging

# Deploy to Cloud Run
gcloud run deploy hvac-estimator-staging \
  --image gcr.io/PROJECT_ID/hvac-estimator:staging \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=PROJECT_ID,CACHE_BACKEND=firestore,STORAGE_BACKEND=gcs
```

### GCP Production

```bash
# Build with production tag
gcloud builds submit --tag gcr.io/PROJECT_ID/hvac-estimator:prod

# Deploy with IAP (no unauthenticated access)
gcloud run deploy hvac-estimator \
  --image gcr.io/PROJECT_ID/hvac-estimator:prod \
  --region us-central1 \
  --no-allow-unauthenticated \
  --service-account hvac-estimator-sa@PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT=PROJECT_ID,CACHE_BACKEND=firestore,STORAGE_BACKEND=gcs
```

---

## Cost Estimation

### Monthly GCP Costs (Estimated)

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| **Cloud Run** | 2 vCPU, 2GB RAM, auto-scaling | $15-50/month |
| **Cloud Storage** | 10GB storage, 100k operations | $5-15/month |
| **Firestore** | 100k reads, 50k writes/month | $5-20/month |
| **Secret Manager** | 3 secrets, 10k accesses | $20/month |
| **Cloud Logging** | 10GB logs/month (free tier) | $0/month |
| **Load Balancer** | Standard tier | $18/month |
| **Cloud Armor** | Basic DDoS protection | $0-10/month |
| **Total** | | **$63-133/month** |

### Cost Optimization Tips

1. **Use Cloud Run min instances = 0** for non-production
2. **Enable Firestore TTL** to auto-delete old cache entries
3. **Use lifecycle policies** on GCS buckets
4. **Monitor API usage** with budget alerts

---

## Monitoring & Observability

### Cloud Monitoring Dashboard

Create a dashboard with these widgets:

1. **Cloud Run Metrics**
   - Request latency (p50, p95, p99)
   - Request count
   - Container instance count
   - Memory utilization

2. **Application Metrics**
   - PDF processing time
   - Quote generation time
   - Cache hit rate
   - API error rate

3. **Cost Metrics**
   - API calls per hour
   - Storage usage
   - Firestore operations

### Alerting Policies

```yaml
# Example alerting policy
displayName: "High Error Rate"
conditions:
  - displayName: "Error rate > 5%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class="5xx"'
      aggregations:
        - alignmentPeriod: "60s"
          perSeriesAligner: ALIGN_RATE
      comparison: COMPARISON_GT
      thresholdValue: 0.05
      duration: "300s"
```

---

## Rollback Procedures

### Quick Rollback

```bash
# List previous revisions
gcloud run revisions list --service=hvac-estimator

# Route traffic to previous revision
gcloud run services update-traffic hvac-estimator \
  --to-revisions=hvac-estimator-00001-abc=100
```

### Full Rollback

```bash
# Deploy previous image version
gcloud run deploy hvac-estimator \
  --image gcr.io/PROJECT_ID/hvac-estimator:previous-tag
```

---

## Appendix: Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GCP_PROJECT` | Yes (GCP) | - | GCP project ID |
| `CACHE_BACKEND` | No | `file` | Cache backend: `file`, `firestore`, `redis` |
| `STORAGE_BACKEND` | No | `local` | Storage backend: `local`, `gcs` |
| `GCS_BUCKET` | Yes (GCS) | - | Cloud Storage bucket name |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key (use Secret Manager in GCP) |

---

**Document Version:** 1.0
**Last Updated:** 2025-12-18
**Author:** AI Assistant (Claude)
