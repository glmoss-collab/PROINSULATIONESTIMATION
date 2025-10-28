# HVAC Insulation Estimator - Deployment Guide

Professional SaaS deployment guide for the HVAC Insulation Estimator Streamlit application.

## Quick Start

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Access the App**
   Open your browser to: http://localhost:8501

---

## Deployment Options

### Option 1: Streamlit Community Cloud (Recommended - FREE)

Streamlit Community Cloud is the easiest way to deploy, host, and share Streamlit apps for free.

#### Prerequisites
- GitHub account
- Streamlit Community Cloud account (sign up at https://streamlit.io/cloud)

#### Deployment Steps

1. **Push Code to GitHub**
   ```bash
   git add .
   git commit -m "Deploy HVAC Insulation Estimator to Streamlit Cloud"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Click "New app"
   - Select your repository: `glmoss-collab/PROINSULATIONESTIMATION`
   - Main file path: `streamlit_app.py`
   - Click "Deploy"

3. **Your App is Live!**
   - URL will be: `https://[your-app-name].streamlit.app`
   - Share this URL with your team

#### Configuration
- The app will automatically install dependencies from `requirements.txt`
- Streamlit settings are loaded from `.streamlit/config.toml`
- Free tier includes:
  - Unlimited public apps
  - 1GB resources per app
  - Community support

---

### Option 2: Docker Deployment

For more control and custom infrastructure.

#### Create Dockerfile

Create a file named `Dockerfile` in the project root:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Build and Run

```bash
# Build Docker image
docker build -t hvac-estimator .

# Run container
docker run -p 8501:8501 hvac-estimator
```

#### Deploy to Cloud Platforms

**AWS ECS/Fargate:**
1. Push image to ECR
2. Create ECS task definition
3. Deploy as Fargate service

**Google Cloud Run:**
```bash
gcloud run deploy hvac-estimator \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Azure Container Instances:**
```bash
az container create \
  --resource-group myResourceGroup \
  --name hvac-estimator \
  --image hvac-estimator:latest \
  --dns-name-label hvac-estimator \
  --ports 8501
```

---

### Option 3: Heroku Deployment

#### Prerequisites
- Heroku account
- Heroku CLI installed

#### Setup Files

1. **Create `setup.sh`**
   ```bash
   mkdir -p ~/.streamlit/
   echo "\
   [server]\n\
   headless = true\n\
   port = $PORT\n\
   enableCORS = false\n\
   \n\
   " > ~/.streamlit/config.toml
   ```

2. **Create `Procfile`**
   ```
   web: sh setup.sh && streamlit run streamlit_app.py
   ```

#### Deploy

```bash
# Login to Heroku
heroku login

# Create app
heroku create hvac-insulation-estimator

# Deploy
git push heroku main

# Open app
heroku open
```

---

### Option 4: AWS Elastic Beanstalk

#### Prerequisites
- AWS account
- EB CLI installed

#### Setup

1. **Initialize EB**
   ```bash
   eb init -p python-3.10 hvac-estimator --region us-east-1
   ```

2. **Create Environment**
   ```bash
   eb create hvac-estimator-env
   ```

3. **Deploy Updates**
   ```bash
   eb deploy
   ```

4. **Open Application**
   ```bash
   eb open
   ```

---

## Environment Configuration

### Required Files

1. **requirements.txt** - Python dependencies ✓
2. **.streamlit/config.toml** - Streamlit configuration ✓
3. **streamlit_app.py** - Main application ✓
4. **hvac_insulation_estimator.py** - Core estimation engine ✓
5. **pricebook_sample.json** - Sample distributor pricing ✓

### Optional Enhancements

#### Secrets Management

For Streamlit Cloud, add secrets in the dashboard:
- Go to App Settings > Secrets
- Add API keys, database credentials, etc.

Access in code:
```python
import streamlit as st
api_key = st.secrets["api_key"]
```

#### Custom Domain

**Streamlit Cloud:**
- Available on paid plans
- Settings > Custom domain

**Other platforms:**
- Configure DNS to point to your deployment
- Set up SSL/TLS certificates

---

## Production Optimization

### Performance Tips

1. **Enable Caching**
   ```python
   @st.cache_data
   def load_pricebook(path):
       # Expensive operation
       return data
   ```

2. **Reduce File Sizes**
   - Optimize PDF processing
   - Compress uploaded files
   - Limit file upload sizes

3. **Add Loading Indicators**
   ```python
   with st.spinner("Calculating..."):
       # Long-running operation
   ```

### Security Best Practices

1. **Input Validation**
   - Already implemented in the app
   - Validate all user inputs
   - Sanitize file uploads

2. **Rate Limiting**
   - Implement on server level
   - Prevent abuse

3. **Authentication** (for enterprise)
   - Add user authentication
   - Implement role-based access
   - Track usage per user

### Monitoring

**Streamlit Cloud:**
- Built-in analytics
- View app logs
- Monitor resource usage

**Custom Deployment:**
- Add logging: `logging.info()`
- Use monitoring tools: Datadog, New Relic
- Track errors: Sentry

---

## Scaling

### Vertical Scaling
- Increase instance size
- More RAM for large files
- Faster CPU for calculations

### Horizontal Scaling
- Deploy multiple instances
- Use load balancer
- Session state in Redis/database

### Database Integration

For multi-user SaaS:

```python
import sqlite3

# Store projects in database
conn = sqlite3.connect('estimator.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT,
    specs JSON,
    measurements JSON,
    created_at TIMESTAMP
)
''')
```

---

## Cost Estimates

### Streamlit Community Cloud
- **Free tier**: $0/month
  - Perfect for getting started
  - Unlimited public apps
  - Community support

- **Paid tier**: $250/month per workspace
  - Private apps
  - Priority support
  - Custom domains

### AWS (Medium usage)
- **Elastic Beanstalk**: ~$25-50/month
- **Fargate**: ~$30-60/month
- **EC2 (t3.medium)**: ~$30/month + bandwidth

### Heroku
- **Hobby tier**: $7/month
- **Standard**: $25-50/month
- **Performance**: $250+/month

### Google Cloud Run
- **Pay per use**: ~$10-30/month for low traffic
- Auto-scales to zero
- Only pay when running

---

## Maintenance

### Regular Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Test locally
streamlit run streamlit_app.py

# Deploy
git push origin main  # Auto-deploys on Streamlit Cloud
```

### Backup Strategy

1. **Code**: Version controlled in Git
2. **Data**:
   - Export user data regularly
   - Backup uploaded pricebooks
3. **Configurations**: Stored in config files

### Monitoring Checklist

- [ ] App is accessible
- [ ] All features working
- [ ] File uploads functioning
- [ ] Calculations accurate
- [ ] Downloads working
- [ ] No errors in logs

---

## Support & Resources

### Streamlit Resources
- Documentation: https://docs.streamlit.io
- Community Forum: https://discuss.streamlit.io
- Gallery: https://streamlit.io/gallery

### Application Support
- GitHub Issues: https://github.com/glmoss-collab/PROINSULATIONESTIMATION/issues
- Email: [your-support-email]

---

## Next Steps

1. **Deploy to Streamlit Cloud** (Quickest option)
2. **Test with real data** (Upload your actual pricebook)
3. **Gather feedback** (Share with team)
4. **Iterate and improve** (Add requested features)
5. **Scale as needed** (Upgrade plan when ready)

---

## Troubleshooting

### Common Issues

**"ModuleNotFoundError"**
- Solution: Check `requirements.txt` is complete
- Run: `pip install -r requirements.txt`

**"Port already in use"**
- Solution: Change port in config or kill existing process
- Run: `streamlit run streamlit_app.py --server.port 8502`

**"Upload file too large"**
- Solution: Increase max upload size in `.streamlit/config.toml`:
  ```toml
  [server]
  maxUploadSize = 200
  ```

**"App is slow"**
- Solution: Add caching to expensive operations
- Use `@st.cache_data` decorator

---

**Ready to deploy? Start with Streamlit Community Cloud - it's free and takes 5 minutes!**
