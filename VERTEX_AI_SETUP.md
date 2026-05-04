# Vertex AI Model Studio Setup Guide
## Integrating Claude Sonnet 4.5 for HVAC Insulation Estimation

---

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Vertex AI API** enabled
3. **Access to Anthropic's Claude models** in Model Garden
4. **Appropriate IAM permissions** (Vertex AI User or Editor)

---

## Step 1: Access Vertex AI Model Garden

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Navigate to **Vertex AI** → **Model Garden**
3. Search for **"Claude"** or **"Anthropic"**
4. Select **Claude 3.5 Sonnet** from the available models

---

## Step 2: Enable Claude API Access

1. Click **"Enable"** on the Claude model card
2. Review and accept Anthropic's terms of service
3. Wait for API access to be provisioned (usually instant)
4. Verify access in **Vertex AI** → **Online Prediction**

---

## Step 3: Configure System Instructions in Model Studio

### Option A: Via Vertex AI Studio UI

1. Navigate to **Vertex AI Studio** → **Language**
2. Select **Claude 3.5 Sonnet** as your model
3. Click **"Create Prompt"** or **"New Chat"**
4. Look for **"System Instructions"** section
5. Paste the entire content from `vertex_ai_system_instructions.md`
6. Save the prompt template with a name like: `hvac-insulation-estimator`

### Option B: Via API/SDK Configuration

```python
from google.cloud import aiplatform
from anthropic import AnthropicVertex

# Initialize Vertex AI
project_id = "your-project-id"
location = "us-east5"  # or your preferred region

# Load system instructions
with open('vertex_ai_system_instructions.md', 'r') as f:
    system_instructions = f.read()

# Initialize Anthropic Vertex client
client = AnthropicVertex(
    project_id=project_id,
    region=location
)

# Example: Analyze specifications
def analyze_specifications(pdf_base64, system_instructions):
    message = client.messages.create(
        model="claude-3-5-sonnet-v2@20241022",
        max_tokens=4000,
        temperature=0.2,
        system=system_instructions,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Analyze this mechanical insulation specification PDF..."
                    }
                ]
            }
        ]
    )
    return message.content[0].text
```

---

## Step 4: Model Configuration Settings

### Recommended Parameters by Task

#### 1. Specification Analysis
```json
{
  "model": "claude-3-5-sonnet-v2@20241022",
  "max_tokens": 4000,
  "temperature": 0.2,
  "top_p": 1.0,
  "top_k": null
}
```

#### 2. Drawing Takeoff
```json
{
  "model": "claude-3-5-sonnet-v2@20241022",
  "max_tokens": 8000,
  "temperature": 0.1,
  "top_p": 1.0,
  "top_k": null
}
```

#### 3. Quote Generation
```json
{
  "model": "claude-3-5-sonnet-v2@20241022",
  "max_tokens": 4000,
  "temperature": 0.3,
  "top_p": 1.0,
  "top_k": null
}
```

---

## Step 5: Test Your Configuration

### Test 1: Simple Interaction
```python
# Simple test without documents
response = client.messages.create(
    model="claude-3-5-sonnet-v2@20241022",
    max_tokens=1000,
    system="You are an HVAC mechanical insulation estimating assistant.",
    messages=[
        {
            "role": "user",
            "content": "What are common insulation materials for chilled water piping?"
        }
    ]
)
print(response.content[0].text)
```

**Expected Response:** Detailed explanation of fiberglass, elastomeric foam, vapor barriers, etc.

### Test 2: Specification Analysis
Upload a sample specification PDF and verify:
- Extracts insulation types and thicknesses
- Identifies system types
- Notes special requirements
- Formats output in structured markdown

### Test 3: Drawing Takeoff
Upload a sample drawing PDF and verify:
- Identifies drawing scale
- Measures ductwork and piping
- Counts fittings accurately
- Formats output in the specified structure

---

## Step 6: Integrate with Your Application

### Update estimation_app.py for Vertex AI

Replace the Anthropic client initialization:

```python
# OLD: Direct Anthropic API
from anthropic import Anthropic
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# NEW: Anthropic Vertex AI
from anthropic import AnthropicVertex

client = AnthropicVertex(
    project_id=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    region=os.environ.get("GOOGLE_CLOUD_REGION", "us-east5")
)

# The rest of your code stays the same!
# Model name changes to: "claude-3-5-sonnet-v2@20241022"
```

### Environment Variables Needed

```bash
# Add to your .env or environment
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-east5"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

---

## Step 7: Set Up Authentication

### Option A: Service Account (Recommended for Production)

1. Create a service account:
   ```bash
   gcloud iam service-accounts create hvac-estimator \
       --display-name="HVAC Estimator Service Account"
   ```

2. Grant necessary permissions:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:hvac-estimator@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/aiplatform.user"
   ```

3. Create and download key:
   ```bash
   gcloud iam service-accounts keys create ~/hvac-estimator-key.json \
       --iam-account=hvac-estimator@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

4. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="$HOME/hvac-estimator-key.json"
   ```

### Option B: User Credentials (For Development)

```bash
gcloud auth application-default login
```

---

## Step 8: Monitor and Optimize

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.INFO)

# Vertex AI automatically logs to Cloud Logging
# View logs: Cloud Console → Logging → Logs Explorer
```

### Monitor Usage
1. Go to **Vertex AI** → **Dashboard**
2. Check **Model Garden** usage
3. Monitor **API calls** and **token consumption**
4. Set up **budget alerts** in Billing

### Cost Estimation

**Claude 3.5 Sonnet via Vertex AI Pricing (as of 2024):**
- Input tokens: ~$3 per million tokens
- Output tokens: ~$15 per million tokens

**Typical Usage per Estimate:**
- Specification analysis: ~10K input, ~2K output = $0.06
- Drawing takeoff: ~20K input, ~3K output = $0.11
- Quote generation: ~5K input, ~2K output = $0.05
- **Total per estimate: ~$0.22**

**Monthly Estimates:**
- 100 projects/month: ~$22
- 500 projects/month: ~$110
- 1,000 projects/month: ~$220

---

## Troubleshooting

### Issue: "Permission Denied" Error

**Solution:**
```bash
# Verify IAM permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:YOUR_SERVICE_ACCOUNT"

# Add missing permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
    --role="roles/aiplatform.user"
```

### Issue: "Model Not Found" Error

**Solution:**
1. Verify model name: `claude-3-5-sonnet-v2@20241022`
2. Check region availability (Claude may not be available in all regions)
3. Use supported regions: `us-east5`, `us-central1`, `europe-west1`

### Issue: "Quota Exceeded" Error

**Solution:**
1. Check quotas: **IAM & Admin** → **Quotas**
2. Search for "Vertex AI" quotas
3. Request quota increase if needed
4. Consider rate limiting in your application

### Issue: "Invalid Document Format" Error

**Solution:**
1. Ensure PDF is not encrypted
2. Maximum file size: 32 MB per document
3. For large PDFs, consider splitting into sections
4. Verify base64 encoding is correct

---

## Best Practices

### 1. System Instructions Management
- Store system instructions in version control
- Update instructions based on user feedback
- Test changes with sample documents before deploying

### 2. Error Handling
```python
from anthropic import APIError, APIConnectionError

try:
    response = client.messages.create(...)
except APIConnectionError as e:
    # Network error, retry with exponential backoff
    print(f"Connection error: {e}")
except APIError as e:
    # API error, log and handle gracefully
    print(f"API error: {e.status_code} - {e.message}")
```

### 3. Caching Strategy
- Cache specification analyses for repeated projects
- Store takeoff results in database
- Implement prompt caching for long system instructions

### 4. Security
- Never commit service account keys to git
- Use Secret Manager for sensitive credentials
- Implement proper authentication and authorization
- Audit API access regularly

### 5. Performance Optimization
- Use appropriate token limits (don't over-allocate)
- Batch similar requests when possible
- Implement client-side validation before API calls
- Consider streaming for long responses

---

## Migration Checklist

- [ ] Google Cloud project created and billing enabled
- [ ] Vertex AI API enabled
- [ ] Claude model access enabled in Model Garden
- [ ] Service account created with proper permissions
- [ ] System instructions loaded and tested
- [ ] Sample PDFs tested with all three functions
- [ ] Application code updated to use AnthropicVertex
- [ ] Environment variables configured
- [ ] Error handling implemented
- [ ] Logging and monitoring set up
- [ ] Cost alerts configured
- [ ] Documentation updated for team

---

## Additional Resources

- **Anthropic Vertex AI Docs:** https://docs.anthropic.com/en/api/claude-on-vertex-ai
- **Vertex AI Documentation:** https://cloud.google.com/vertex-ai/docs
- **Claude API Reference:** https://docs.anthropic.com/en/api/
- **Google Cloud Pricing:** https://cloud.google.com/vertex-ai/pricing
- **Best Practices:** https://cloud.google.com/vertex-ai/docs/generative-ai/learn/best-practices

---

## Support

For issues specific to:
- **Vertex AI:** Google Cloud Support
- **Claude Model:** Anthropic Support
- **Application:** Check GitHub issues or internal support

---

**Setup Version:** 1.0
**Last Updated:** 2025-11-06
**Tested With:** Claude 3.5 Sonnet (claude-3-5-sonnet-v2@20241022)
