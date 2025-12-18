"""
Vertex AI Client for Claude Opus 4.5 Integration
=================================================

This module provides a client wrapper for accessing Claude Opus 4.5 through
Google Cloud's Vertex AI Model Garden. Use this for enterprise deployments
where you want to leverage GCP infrastructure and billing.

VERTEX AI MODEL GARDEN SETUP INSTRUCTIONS
-----------------------------------------

1. PREREQUISITES:
   - Google Cloud Project with billing enabled
   - gcloud CLI installed and authenticated
   - Vertex AI API enabled

2. ENABLE VERTEX AI:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

3. ACCESS CLAUDE OPUS 4.5 IN MODEL GARDEN:
   - Go to: Console > Vertex AI > Model Garden
   - Search for "Claude"
   - Select "Claude Opus 4.5" (claude-opus-4-5-20251101)
   - Click "Enable" and accept terms
   - Wait for provisioning (5-10 minutes)

4. CREATE SERVICE ACCOUNT:
   ```bash
   gcloud iam service-accounts create estimator-vertex-ai \\
       --display-name="Estimator Vertex AI Service Account"

   gcloud projects add-iam-policy-binding PROJECT_ID \\
       --member="serviceAccount:estimator-vertex-ai@PROJECT_ID.iam.gserviceaccount.com" \\
       --role="roles/aiplatform.user"
   ```

5. GENERATE CREDENTIALS:
   ```bash
   gcloud iam service-accounts keys create vertex-ai-key.json \\
       --iam-account=estimator-vertex-ai@PROJECT_ID.iam.gserviceaccount.com

   export GOOGLE_APPLICATION_CREDENTIALS="path/to/vertex-ai-key.json"
   ```

6. SET ENVIRONMENT VARIABLES:
   ```bash
   export USE_VERTEX_AI=true
   export GCP_PROJECT_ID=your-project-id
   export GCP_REGION=us-central1  # or your preferred region
   ```

USAGE
-----
```python
from vertex_ai_client import VertexAIClaudeClient, get_claude_client

# Option 1: Automatic selection based on environment
client = get_claude_client()

# Option 2: Explicitly use Vertex AI
client = VertexAIClaudeClient(
    project_id="your-project-id",
    region="us-central1"
)

# Use the client like the standard Anthropic client
response = client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

SUPPORTED REGIONS
-----------------
Claude Opus 4.5 is available in:
- us-central1 (Iowa, USA)
- us-east4 (Virginia, USA)
- europe-west1 (Belgium, Europe)
- asia-northeast1 (Tokyo, Japan)

Check Model Garden for the latest availability.

PRICING (as of 2025)
--------------------
Claude Opus 4.5 on Vertex AI:
- Input: $15.00 per million tokens
- Output: $75.00 per million tokens

Pricing is the same as direct Anthropic API access.
Billing goes through your GCP account.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Claude Opus 4.5 model identifier for Vertex AI Model Garden
VERTEX_CLAUDE_OPUS_MODEL = "claude-opus-4-5-20251101"

# Default Vertex AI endpoint format
VERTEX_ENDPOINT_FORMAT = (
    "https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}/"
    "locations/{region}/publishers/anthropic/models/{model}"
)

# Supported regions for Claude on Vertex AI
SUPPORTED_REGIONS = [
    "us-central1",
    "us-east4",
    "europe-west1",
    "asia-northeast1"
]

# Default region
DEFAULT_REGION = "us-central1"


# ============================================================================
# RESPONSE DATA CLASSES
# ============================================================================

@dataclass
class TokenUsage:
    """Token usage information from API response."""
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


@dataclass
class ContentBlock:
    """Content block from API response."""
    type: str
    text: str


@dataclass
class MessagesResponse:
    """Response object mimicking Anthropic's Messages API response."""
    id: str
    type: str
    role: str
    content: List[ContentBlock]
    model: str
    stop_reason: str
    stop_sequence: Optional[str]
    usage: TokenUsage


# ============================================================================
# VERTEX AI MESSAGES CLIENT
# ============================================================================

class VertexAIMessagesClient:
    """
    Messages API client for Claude via Vertex AI.

    Provides the same interface as anthropic.Anthropic().messages
    """

    def __init__(
        self,
        project_id: str,
        region: str = DEFAULT_REGION,
        credentials: Any = None
    ):
        """
        Initialize the Vertex AI Messages client.

        Args:
            project_id: GCP project ID
            region: GCP region (must be a supported region)
            credentials: Optional Google credentials object
        """
        self.project_id = project_id
        self.region = region
        self.credentials = credentials

        # Validate region
        if region not in SUPPORTED_REGIONS:
            logger.warning(
                f"Region '{region}' may not support Claude. "
                f"Supported regions: {SUPPORTED_REGIONS}"
            )

        # Import Google libraries (lazy import for optional dependency)
        try:
            from google.auth import default as google_auth_default
            from google.auth.transport.requests import Request
            import requests

            self._requests = requests
            self._Request = Request

            # Get credentials if not provided
            if self.credentials is None:
                self.credentials, _ = google_auth_default()

        except ImportError:
            raise ImportError(
                "Google Cloud libraries required for Vertex AI integration. "
                "Install with: pip install google-auth google-auth-oauthlib requests"
            )

        logger.info(
            f"Initialized Vertex AI client for project={project_id}, region={region}"
        )

    def _get_endpoint(self, model: str) -> str:
        """Get the Vertex AI endpoint URL for the specified model."""
        return VERTEX_ENDPOINT_FORMAT.format(
            region=self.region,
            project_id=self.project_id,
            model=model
        )

    def _refresh_credentials(self) -> str:
        """Refresh credentials and return access token."""
        if not self.credentials.valid:
            self.credentials.refresh(self._Request())
        return self.credentials.token

    def create(
        self,
        model: str = VERTEX_CLAUDE_OPUS_MODEL,
        max_tokens: int = 4096,
        messages: List[Dict[str, Any]] = None,
        system: Optional[Union[str, List[Dict]]] = None,
        tools: Optional[List[Dict]] = None,
        temperature: float = 1.0,
        **kwargs
    ) -> MessagesResponse:
        """
        Create a message using Claude via Vertex AI.

        This method provides the same interface as anthropic.Anthropic().messages.create()

        Args:
            model: Model identifier (default: claude-opus-4-5-20251101)
            max_tokens: Maximum tokens in response
            messages: List of message dictionaries with 'role' and 'content'
            system: Optional system prompt (string or list of content blocks)
            tools: Optional list of tool definitions for tool use
            temperature: Sampling temperature (0.0-1.0)
            **kwargs: Additional parameters passed to the API

        Returns:
            MessagesResponse object with response content and metadata

        Raises:
            RuntimeError: If API call fails
        """
        # Build request payload
        payload = {
            "anthropic_version": "vertex-2023-10-16",
            "max_tokens": max_tokens,
            "messages": messages or [],
            "temperature": temperature
        }

        # Add system prompt if provided
        if system:
            if isinstance(system, str):
                payload["system"] = system
            else:
                payload["system"] = system

        # Add tools if provided
        if tools:
            payload["tools"] = tools

        # Add any additional parameters
        payload.update(kwargs)

        # Get endpoint and auth token
        endpoint = self._get_endpoint(model)
        token = self._refresh_credentials()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        logger.debug(f"Calling Vertex AI endpoint: {endpoint}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)[:500]}...")

        try:
            # Make API request
            response = self._requests.post(
                f"{endpoint}:streamRawPredict",
                headers=headers,
                json=payload,
                timeout=300  # 5 minute timeout for long responses
            )

            # Check for errors
            if response.status_code != 200:
                error_detail = response.text[:500]
                raise RuntimeError(
                    f"Vertex AI API error (status {response.status_code}): {error_detail}"
                )

            # Parse response
            result = response.json()

            # Build response object
            content_blocks = [
                ContentBlock(type=c.get("type", "text"), text=c.get("text", ""))
                for c in result.get("content", [])
            ]

            usage_data = result.get("usage", {})
            usage = TokenUsage(
                input_tokens=usage_data.get("input_tokens", 0),
                output_tokens=usage_data.get("output_tokens", 0),
                cache_read_input_tokens=usage_data.get("cache_read_input_tokens", 0),
                cache_creation_input_tokens=usage_data.get("cache_creation_input_tokens", 0)
            )

            return MessagesResponse(
                id=result.get("id", ""),
                type=result.get("type", "message"),
                role=result.get("role", "assistant"),
                content=content_blocks,
                model=result.get("model", model),
                stop_reason=result.get("stop_reason", "end_turn"),
                stop_sequence=result.get("stop_sequence"),
                usage=usage
            )

        except self._requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to call Vertex AI API: {e}") from e


# ============================================================================
# VERTEX AI CLAUDE CLIENT
# ============================================================================

class VertexAIClaudeClient:
    """
    Main client for Claude via Vertex AI Model Garden.

    This class provides the same interface as anthropic.Anthropic()
    for easy drop-in replacement.

    Example:
        # Instead of:
        from anthropic import Anthropic
        client = Anthropic(api_key="...")

        # Use:
        from vertex_ai_client import VertexAIClaudeClient
        client = VertexAIClaudeClient(project_id="...", region="...")

        # Same API:
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=4096,
            messages=[...]
        )
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        region: str = DEFAULT_REGION,
        credentials: Any = None
    ):
        """
        Initialize the Vertex AI Claude client.

        Args:
            project_id: GCP project ID (reads from GCP_PROJECT_ID env var if not provided)
            region: GCP region (reads from GCP_REGION env var if not provided)
            credentials: Optional Google credentials object
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            raise ValueError(
                "GCP project ID required. Set GCP_PROJECT_ID environment variable "
                "or pass project_id parameter."
            )

        self.region = region or os.getenv("GCP_REGION", DEFAULT_REGION)

        # Initialize the messages client
        self.messages = VertexAIMessagesClient(
            project_id=self.project_id,
            region=self.region,
            credentials=credentials
        )

        logger.info(
            f"VertexAIClaudeClient initialized - "
            f"Project: {self.project_id}, Region: {self.region}"
        )


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_claude_client(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    use_vertex_ai: Optional[bool] = None
) -> Union['VertexAIClaudeClient', Any]:
    """
    Get the appropriate Claude client based on configuration.

    This factory function automatically selects between:
    - Direct Anthropic API (when ANTHROPIC_API_KEY is set)
    - Vertex AI Model Garden (when USE_VERTEX_AI=true)

    Priority:
    1. Explicit use_vertex_ai parameter
    2. USE_VERTEX_AI environment variable
    3. ANTHROPIC_API_KEY availability

    Args:
        api_key: Anthropic API key (for direct API access)
        project_id: GCP project ID (for Vertex AI)
        region: GCP region (for Vertex AI)
        use_vertex_ai: Force Vertex AI usage (overrides environment)

    Returns:
        Either Anthropic or VertexAIClaudeClient

    Raises:
        ValueError: If neither API key nor Vertex AI is configured

    Example:
        # Automatic selection based on environment:
        client = get_claude_client()

        # Force Vertex AI:
        client = get_claude_client(use_vertex_ai=True, project_id="my-project")

        # Force direct API:
        client = get_claude_client(api_key="sk-ant-...")
    """
    # Determine which client to use
    should_use_vertex = use_vertex_ai

    if should_use_vertex is None:
        should_use_vertex = os.getenv("USE_VERTEX_AI", "").lower() == "true"

    if should_use_vertex:
        # Use Vertex AI
        logger.info("Using Vertex AI Model Garden for Claude access")
        return VertexAIClaudeClient(
            project_id=project_id or os.getenv("GCP_PROJECT_ID"),
            region=region or os.getenv("GCP_REGION", DEFAULT_REGION)
        )
    else:
        # Use direct Anthropic API
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "No API credentials configured. Set either:\n"
                "  - ANTHROPIC_API_KEY for direct Anthropic API access\n"
                "  - USE_VERTEX_AI=true with GCP_PROJECT_ID for Vertex AI access"
            )

        try:
            from anthropic import Anthropic
            logger.info("Using direct Anthropic API for Claude access")
            return Anthropic(api_key=key)
        except ImportError:
            raise ImportError(
                "Anthropic library required. Install with: pip install anthropic"
            )


# ============================================================================
# CONFIGURATION HELPERS
# ============================================================================

def print_vertex_ai_setup_instructions():
    """Print detailed setup instructions for Vertex AI integration."""
    instructions = """
================================================================================
              VERTEX AI MODEL GARDEN SETUP FOR CLAUDE OPUS 4.5
================================================================================

STEP 1: ENABLE REQUIRED APIS
-----------------------------
Run in your terminal:

    gcloud services enable aiplatform.googleapis.com
    gcloud services enable iam.googleapis.com

STEP 2: ACCESS CLAUDE IN MODEL GARDEN
--------------------------------------
1. Open Google Cloud Console
2. Navigate to: Vertex AI > Model Garden
3. Search for "Claude"
4. Select "Claude Opus 4.5" (claude-opus-4-5-20251101)
5. Click "Enable" and accept the terms
6. Wait 5-10 minutes for provisioning

STEP 3: CREATE SERVICE ACCOUNT
-------------------------------
Run these commands (replace PROJECT_ID with your project):

    # Create service account
    gcloud iam service-accounts create estimator-vertex-ai \\
        --display-name="Estimator Vertex AI Service Account"

    # Grant Vertex AI User role
    gcloud projects add-iam-policy-binding PROJECT_ID \\
        --member="serviceAccount:estimator-vertex-ai@PROJECT_ID.iam.gserviceaccount.com" \\
        --role="roles/aiplatform.user"

STEP 4: GENERATE AND SET CREDENTIALS
------------------------------------
    # Generate key file
    gcloud iam service-accounts keys create vertex-ai-key.json \\
        --iam-account=estimator-vertex-ai@PROJECT_ID.iam.gserviceaccount.com

    # Set environment variable
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/vertex-ai-key.json"

STEP 5: CONFIGURE APPLICATION
------------------------------
Set these environment variables:

    export USE_VERTEX_AI=true
    export GCP_PROJECT_ID=your-project-id
    export GCP_REGION=us-central1

STEP 6: TEST CONNECTION
------------------------
Run this Python code:

    from vertex_ai_client import get_claude_client

    client = get_claude_client()
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=100,
        messages=[{"role": "user", "content": "Say hello!"}]
    )
    print(response.content[0].text)

================================================================================
                         TROUBLESHOOTING
================================================================================

ERROR: "Permission denied"
-> Verify service account has 'roles/aiplatform.user' role

ERROR: "Model not found"
-> Ensure Claude Opus 4.5 is enabled in Model Garden for your project

ERROR: "Region not available"
-> Try us-central1, us-east4, europe-west1, or asia-northeast1

ERROR: "Quota exceeded"
-> Check your Vertex AI quotas in Cloud Console

For more help, see:
https://cloud.google.com/vertex-ai/docs/generative-ai/model-garden/use-models

================================================================================
"""
    print(instructions)


def validate_vertex_ai_config() -> Dict[str, Any]:
    """
    Validate Vertex AI configuration and return status.

    Returns:
        Dictionary with configuration status and any issues found
    """
    status = {
        "configured": False,
        "project_id": None,
        "region": None,
        "credentials": None,
        "issues": []
    }

    # Check project ID
    project_id = os.getenv("GCP_PROJECT_ID")
    if project_id:
        status["project_id"] = project_id
    else:
        status["issues"].append("GCP_PROJECT_ID environment variable not set")

    # Check region
    region = os.getenv("GCP_REGION", DEFAULT_REGION)
    status["region"] = region
    if region not in SUPPORTED_REGIONS:
        status["issues"].append(
            f"Region '{region}' may not support Claude. "
            f"Consider: {', '.join(SUPPORTED_REGIONS)}"
        )

    # Check credentials
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        if os.path.exists(creds_path):
            status["credentials"] = creds_path
        else:
            status["issues"].append(
                f"Credentials file not found: {creds_path}"
            )
    else:
        # Check for default credentials
        try:
            from google.auth import default as google_auth_default
            creds, project = google_auth_default()
            status["credentials"] = "Default credentials (ADC)"
            if project and not status["project_id"]:
                status["project_id"] = project
        except Exception:
            status["issues"].append(
                "No credentials found. Set GOOGLE_APPLICATION_CREDENTIALS "
                "or configure Application Default Credentials"
            )

    # Determine if configured
    status["configured"] = (
        status["project_id"] is not None and
        status["credentials"] is not None and
        len(status["issues"]) == 0
    )

    return status


# ============================================================================
# MAIN - SETUP HELPER
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Vertex AI Claude Integration Helper"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Print setup instructions"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate current configuration"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test connection with a simple message"
    )

    args = parser.parse_args()

    if args.setup:
        print_vertex_ai_setup_instructions()

    elif args.validate:
        print("\n=== Validating Vertex AI Configuration ===\n")
        status = validate_vertex_ai_config()

        print(f"Project ID:  {status['project_id'] or 'NOT SET'}")
        print(f"Region:      {status['region']}")
        print(f"Credentials: {status['credentials'] or 'NOT SET'}")
        print()

        if status["configured"]:
            print("Status: CONFIGURED")
        else:
            print("Status: NOT CONFIGURED")
            print("\nIssues found:")
            for issue in status["issues"]:
                print(f"  - {issue}")

    elif args.test:
        print("\n=== Testing Vertex AI Connection ===\n")
        try:
            client = get_claude_client()
            print("Client initialized successfully!")

            print("Sending test message...")
            response = client.messages.create(
                model=VERTEX_CLAUDE_OPUS_MODEL,
                max_tokens=100,
                messages=[{"role": "user", "content": "Say 'Hello from Vertex AI!' in exactly those words."}]
            )

            print(f"\nResponse: {response.content[0].text}")
            print(f"Model: {response.model}")
            print(f"Tokens used: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
            print("\nConnection test PASSED!")

        except Exception as e:
            print(f"\nConnection test FAILED: {e}")
            print("\nRun with --setup to see configuration instructions.")

    else:
        parser.print_help()
        print("\n\nQuick start:")
        print("  python vertex_ai_client.py --setup     # Show setup instructions")
        print("  python vertex_ai_client.py --validate  # Check configuration")
        print("  python vertex_ai_client.py --test      # Test connection")
