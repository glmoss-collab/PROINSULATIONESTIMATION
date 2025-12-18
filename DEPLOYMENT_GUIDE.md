# Deployment Guide - Hosting Options

**Complete guide for deploying the Estimation App to the cloud**

---

## 📋 Table of Contents

1. [Deployment Options Overview](#deployment-options-overview)
2. [Option 1: Streamlit Cloud (Easiest)](#option-1-streamlit-cloud)
3. [Option 2: Claude Console (API Only)](#option-2-claude-console)
4. [Option 3: Google Vertex AI Model Garden](#option-3-google-vertex-ai-model-garden)
5. [Option 4: Docker Deployment](#option-4-docker-deployment)
6. [Option 5: AWS/Azure/GCP](#option-5-cloud-platforms)
7. [Comparison Table](#comparison-table)

---

## Deployment Options Overview

| Option | Difficulty | Cost | Best For |
|--------|------------|------|----------|
| **Streamlit Cloud** | ⭐ Easy | Free tier | Small teams, testing |
| **Claude Console** | ⭐⭐ Medium | API only | API integration |
| **Vertex AI** | ⭐⭐⭐ Advanced | Pay-per-use | Google Cloud users |
| **Docker** | ⭐⭐⭐ Advanced | Infrastructure cost | Enterprise |
| **Cloud Platforms** | ⭐⭐⭐⭐ Expert | Variable | Scale & control |

---

## Option 1: Streamlit Cloud

**⏱️ Setup Time: 15 minutes**
**💰 Cost: Free (up to 1GB RAM, public apps)**
**👥 Best for: Teams of 1-10 users**

### Why Choose Streamlit Cloud?

✅ **Pros:**
- Completely free for public apps
- Zero infrastructure management
- Automatic deployments from GitHub
- Built-in HTTPS and domains
- Very easy setup

❌ **Cons:**
- Apps are public (unless paid plan)
- Limited resources on free tier
- Requires GitHub account

### Step-by-Step Deployment

#### Prerequisites

- [ ] GitHub account
- [ ] Your code in a GitHub repository
- [ ] Anthropic API key

#### Step 1: Prepare Your Repository

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Create `secrets.toml` template:**

   Create `.streamlit/secrets.toml.example`:
   ```toml
   # Copy this file to secrets.toml and fill in your API keys
   # DO NOT commit the actual secrets.toml file!

   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   GEMINI_API_KEY = "your-gemini-key-here"  # Optional
   ```

3. **Update `.gitignore`:**
   ```
   .streamlit/secrets.toml
   .env
   .cache/
   __pycache__/
   *.pyc
   ```

#### Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud:**
   - Visit: https://share.streamlit.io/
   - Click "Sign in with GitHub"
   - Authorize Streamlit

2. **Create New App:**
   - Click "New app"
   - Repository: Select your repo
   - Branch: `main`
   - Main file path: `agent_estimation_app.py`
   - App URL: Choose a name (e.g., `your-company-estimator`)

3. **Add Secrets:**
   - Click "Advanced settings"
   - Scroll to "Secrets"
   - Add:
     ```toml
     ANTHROPIC_API_KEY = "sk-ant-your-actual-key"
     ```
   - Click "Save"

4. **Deploy:**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your app will be live at: `https://your-app-name.streamlit.app`

#### Step 3: Share with Your Team

1. **Get the URL:**
   - Copy your app URL
   - Example: `https://insulation-estimator.streamlit.app`

2. **Share:**
   - Send link to team members
   - They can use it immediately - no setup needed!

3. **Make Private (Optional - Paid Plan):**
   - Upgrade to Streamlit Cloud Pro ($25/month)
   - Get password protection
   - Add team members
   - More resources (up to 4GB RAM)

#### Updating Your App

Apps auto-deploy when you push to GitHub:
```bash
# Make changes locally
git add .
git commit -m "Update app"
git push origin main

# Streamlit Cloud automatically redeploys!
```

#### Monitoring

- **View logs**: Click "Manage app" → "Logs"
- **Resource usage**: Check "Analytics"
- **Errors**: Automatically shown in logs

---

## Option 2: Claude Console

**⏱️ Setup Time: 10 minutes**
**💰 Cost: API usage only**
**👥 Best for: API integrations, custom UIs**

### What Is This?

The Claude Console is where you manage your API keys and usage. The app uses Claude's API - you don't "deploy" to Claude Console, you just use their API.

### Setup Guide

#### Step 1: Get Your API Access

1. **Sign up for Anthropic:**
   - Go to: https://console.anthropic.com/
   - Create account
   - Verify email

2. **Add payment method:**
   - Click "Settings" → "Billing"
   - Add credit card
   - Set spending limits (optional)
   - New accounts get $5 free credit

3. **Create API key:**
   - Click "API Keys"
   - Click "Create Key"
   - Name it (e.g., "Production Estimator")
   - **Copy the key immediately**
   - Store securely (password manager recommended)

#### Step 2: Configure Your App

1. **Set API key:**

   In `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

2. **Test connection:**
   ```bash
   python -c "from claude_estimation_agent import create_agent; agent = create_agent(); print('✅ Connected!')"
   ```

#### Step 3: Monitor Usage

1. **Check usage:**
   - Console → "Usage"
   - See token counts
   - See costs

2. **Set budgets:**
   - Console → "Settings" → "Limits"
   - Set monthly budget
   - Get email alerts

3. **Track costs with app:**
   ```python
   from utils_tracking import get_tracker
   tracker = get_tracker()
   tracker.print_summary()
   ```

### Best Practices

**Security:**
- ✅ Rotate API keys monthly
- ✅ Use different keys for dev/prod
- ✅ Never commit keys to Git
- ✅ Use environment variables
- ✅ Set spending limits

**Cost Optimization:**
- ✅ Enable caching (built-in)
- ✅ Use smart page selection
- ✅ Monitor with cost tracker
- ✅ Set reasonable limits

---

## Option 3: Google Vertex AI Model Garden

**⏱️ Setup Time: 45 minutes**
**💰 Cost: Google Cloud + Model usage**
**👥 Best for: Google Cloud ecosystem users**

### What Is Vertex AI Model Garden?

Google's platform for deploying and using AI models, including Claude (via partnership).

### Prerequisites

- [ ] Google Cloud account
- [ ] Billing enabled
- [ ] Basic GCP knowledge

### Step-by-Step Deployment

#### Step 1: Set Up Google Cloud Project

1. **Create project:**
   - Go to: https://console.cloud.google.com/
   - Click "Create Project"
   - Name: "Insulation Estimator"
   - Note your Project ID

2. **Enable billing:**
   - Project → Billing
   - Link billing account
   - Set budget alerts ($50/month recommended)

3. **Enable APIs:**
   ```bash
   gcloud services enable \
     compute.googleapis.com \
     aiplatform.googleapis.com \
     storage.googleapis.com
   ```

#### Step 2: Access Claude via Vertex AI

1. **Go to Model Garden:**
   - Console → Vertex AI → Model Garden
   - Search "Claude"
   - Select "Claude Opus 4.5" (claude-opus-4-5-20251101)

2. **Enable access:**
   - Click "Enable"
   - Accept terms
   - Wait for provisioning (5-10 minutes)

3. **Get endpoint:**
   - Note your endpoint URL
   - Format: `https://REGION-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/REGION/publishers/anthropic/models/claude-opus-4-5-20251101`

#### Step 3: Configure Authentication

1. **Create service account:**
   ```bash
   gcloud iam service-accounts create estimator-app \
     --display-name="Estimation App Service Account"
   ```

2. **Grant permissions:**
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:estimator-app@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

3. **Create key:**
   ```bash
   gcloud iam service-accounts keys create key.json \
     --iam-account=estimator-app@PROJECT_ID.iam.gserviceaccount.com
   ```

4. **Set environment:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
   ```

#### Step 4: Use the Vertex AI Client Module

The codebase includes a dedicated `vertex_ai_client.py` module for Vertex AI integration.

**Option A: Using the factory function (recommended)**

```python
# In any file that needs Claude access:
from vertex_ai_client import get_claude_client

# Automatically selects Vertex AI or direct API based on environment
client = get_claude_client()

# Use exactly like the standard Anthropic client
response = client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

**Option B: Explicit Vertex AI usage**

```python
from vertex_ai_client import VertexAIClaudeClient

# Create Vertex AI client directly
client = VertexAIClaudeClient(
    project_id="your-project-id",
    region="us-central1"  # or us-east4, europe-west1, asia-northeast1
)

response = client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

**Option C: Update existing agent code**

```python
# In claude_estimation_agent.py or similar:
import os
from vertex_ai_client import get_claude_client

# Replace direct Anthropic client initialization:
# OLD: self.client = Anthropic(api_key=self.api_key)
# NEW:
self.client = get_claude_client(api_key=self.api_key)
```

#### Step 5: Deploy to Cloud Run

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   EXPOSE 8501

   CMD ["streamlit", "run", "agent_estimation_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Build and push:**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/estimator-app
   ```

3. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy estimator-app \
     --image gcr.io/PROJECT_ID/estimator-app \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="USE_VERTEX_AI=true,GCP_PROJECT_ID=PROJECT_ID"
   ```

4. **Get URL:**
   ```
   Service URL: https://estimator-app-xxxxx-uc.a.run.app
   ```

#### Step 6: Monitor and Scale

1. **View logs:**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=estimator-app"
   ```

2. **Configure autoscaling:**
   ```bash
   gcloud run services update estimator-app \
     --min-instances=0 \
     --max-instances=10 \
     --concurrency=80
   ```

3. **Monitor costs:**
   - Cloud Console → Billing → Reports
   - Filter by "Cloud Run" and "Vertex AI"

### Vertex AI Pricing

**Claude Opus 4.5 on Vertex AI (claude-opus-4-5-20251101):**
- Input: ~$15.00 per million tokens
- Output: ~$75.00 per million tokens
- **Same as direct Anthropic pricing**
- **Benefits:** GCP billing, enterprise support, VPC integration

**Cloud Run:**
- First 2 million requests free/month
- CPU: $0.00002400 per vCPU-second
- Memory: $0.00000250 per GiB-second
- **Typical cost: $5-20/month for moderate usage**

---

## Option 4: Docker Deployment

**⏱️ Setup Time: 30 minutes**
**💰 Cost: Infrastructure only**
**👥 Best for: On-premise or custom hosting**

### Why Use Docker?

✅ Consistent environment
✅ Easy to move between servers
✅ Isolated from host system
✅ Scalable with orchestration

### Step-by-Step

#### Step 1: Create Dockerfile

**`Dockerfile`:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache directory
RUN mkdir -p .cache

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run app
CMD ["streamlit", "run", "agent_estimation_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

**`.dockerignore`:**
```
.git
.gitignore
.cache
__pycache__
*.pyc
.env
.streamlit/secrets.toml
```

#### Step 2: Build Image

```bash
# Build
docker build -t estimator-app:latest .

# Test locally
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY="your-key" \
  estimator-app:latest
```

Open http://localhost:8501

#### Step 3: Deploy to Production

**Docker Compose:**

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  estimator:
    build: .
    ports:
      - "8501:8501"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./cache:/app/.cache
      - ./data:/app/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - estimator
    restart: unless-stopped
```

**Deploy:**
```bash
docker-compose up -d
```

#### Step 4: HTTPS with Let's Encrypt

```bash
# Install certbot
apt-get install certbot

# Get certificate
certbot certonly --standalone -d yourdomain.com

# Copy to nginx certs
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./certs/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./certs/

# Restart
docker-compose restart nginx
```

---

## Option 5: Cloud Platforms

### AWS Deployment

**Using AWS ECS + Fargate:**

1. **Push to ECR:**
   ```bash
   aws ecr create-repository --repository-name estimator-app
   docker tag estimator-app:latest AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/estimator-app:latest
   docker push AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/estimator-app:latest
   ```

2. **Create task definition:**
   - ECS → Task Definitions → Create
   - Launch type: Fargate
   - Image: Your ECR image
   - CPU: 1 vCPU, Memory: 2GB
   - Environment: Add API keys

3. **Create service:**
   - Create ECS cluster
   - Create service from task
   - Configure load balancer
   - Set auto-scaling

**Cost:** ~$30-50/month

### Azure Deployment

**Using Azure Container Instances:**

```bash
az container create \
  --resource-group estimator-rg \
  --name estimator-app \
  --image estimator-app:latest \
  --dns-name-label estimator-yourcompany \
  --ports 8501 \
  --environment-variables \
    ANTHROPIC_API_KEY=$API_KEY
```

**Cost:** ~$20-40/month

### Google Cloud Platform

See [Option 3: Vertex AI](#option-3-google-vertex-ai-model-garden) above

---

## Comparison Table

| Feature | Streamlit Cloud | Claude Console | Vertex AI | Docker | AWS/Azure |
|---------|----------------|----------------|-----------|--------|-----------|
| **Setup Time** | 15 min | 10 min | 45 min | 30 min | 60 min |
| **Technical Skill** | Low | Low | High | Medium | High |
| **Free Tier** | Yes | $5 credit | $300 credit | No | Limited |
| **Monthly Cost** | $0-25 | API only | $20-100 | $15-50 | $30-100 |
| **Scalability** | Limited | Unlimited | High | Medium | Unlimited |
| **Control** | Low | N/A | Medium | High | High |
| **Maintenance** | None | None | Low | Medium | Medium |
| **Best For** | Small teams | Integration | GCP users | On-premise | Enterprise |

---

## Security Best Practices

### All Deployments

1. **API Keys:**
   - ✅ Use environment variables
   - ✅ Never commit to Git
   - ✅ Rotate regularly
   - ✅ Use different keys for dev/prod

2. **Access Control:**
   - ✅ Require authentication
   - ✅ Use HTTPS only
   - ✅ Implement rate limiting
   - ✅ Monitor for abuse

3. **Data Protection:**
   - ✅ Encrypt data in transit
   - ✅ Don't log sensitive data
   - ✅ Regular backups
   - ✅ Comply with regulations (GDPR, etc.)

### Monitoring

**Set up alerts for:**
- High API usage
- Error rates
- Cost thresholds
- Security issues

**Tools:**
- Google Cloud Monitoring
- AWS CloudWatch
- Azure Monitor
- Datadog
- New Relic

---

## Next Steps

1. **Choose deployment option**
2. **Follow step-by-step guide**
3. **Test thoroughly**
4. **Monitor usage and costs**
5. **Scale as needed**

---

## Getting Help

- **Streamlit**: https://docs.streamlit.io/streamlit-cloud
- **Claude API**: https://docs.anthropic.com/
- **Vertex AI**: https://cloud.google.com/vertex-ai/docs
- **Docker**: https://docs.docker.com/
- **AWS**: https://docs.aws.amazon.com/
- **Azure**: https://docs.microsoft.com/azure/

**Happy deploying!** 🚀
