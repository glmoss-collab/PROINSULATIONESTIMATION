# CLAUDE.md - AI Assistant Guide for Professional Insulation Estimation System

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Codebase Structure](#codebase-structure)
3. [Technology Stack](#technology-stack)
4. [Architecture Overview](#architecture-overview)
5. [Key Conventions](#key-conventions)
6. [Development Workflows](#development-workflows)
7. [Testing Strategy](#testing-strategy)
8. [Common Tasks](#common-tasks)
9. [File Organization](#file-organization)
10. [AI Assistant Guidelines](#ai-assistant-guidelines)

---

## Repository Overview

**Project Name:** Professional Insulation Estimation System
**Primary Purpose:** AI-powered HVAC insulation estimation with multiple interfaces and intelligent agents
**Primary AI Model:** Claude Opus 4.5 (via Anthropic Agents SDK and Vertex AI Model Garden)
**Secondary AI:** Google Gemini (legacy support for PDF extraction)
**Primary Deployment Target:** Google Cloud Platform (Cloud Run, Firestore, GCS, Secret Manager)

### What This System Does

This system transforms manual insulation estimation (2-4 hours) into an intelligent, automated process (5-15 minutes) with:

- **Conversational AI estimation** using Claude Agents SDK
- **Automated document analysis** of PDF specifications and drawings
- **Intelligent validation** and cross-referencing
- **Professional quote generation** with material lists and pricing
- **Cost-saving alternatives** and recommendations
- **Multiple deployment options** (Web, CLI, API, Cloud Run)
- **Enterprise GCP integration** with Vertex AI, Firestore, GCS, and Secret Manager
- **Multi-stage workflow orchestration** with validation gates and quality metrics

### Key Metrics

- **Time Savings:** 90-95% reduction in estimation time
- **Cost Efficiency:** 95% API cost reduction through optimization
- **Accuracy:** 99%+ with Pydantic validation
- **ROI:** 400x-4000x vs manual estimation

---

## Codebase Structure

### Directory Layout

```
PROINSULATIONESTIMATION/
├── Core Application Files (Python)
│   ├── claude_estimation_agent.py      # Main agent orchestrator (616 lines)
│   ├── claude_agent_tools.py           # Agent tool implementations (1107 lines)
│   ├── hvac_insulation_estimator.py    # Core estimation engine (1081 lines)
│   ├── agent_estimation_app.py         # Agent-powered Streamlit UI (431 lines)
│   ├── streamlit_app.py                # Full-featured SaaS app (841 lines)
│   ├── estimation_app.py               # Simple Claude app (524 lines)
│   └── demo_agent.py                   # Demo scripts and examples (374 lines)
│
├── Utility Modules (Production-Ready)
│   ├── utils_cache.py                  # File-based caching (339 lines)
│   ├── utils_async.py                  # Async batch processing (326 lines)
│   ├── utils_tracking.py               # API cost tracking (300 lines)
│   ├── utils_pdf.py                    # Optimized PDF processing (369 lines)
│   ├── pydantic_models.py              # Type-safe data validation (417 lines)
│   └── errors.py                       # Custom exception hierarchy (410 lines)
│
├── GCP Integration Modules
│   ├── cloud_config.py                 # Centralized cloud configuration (325 lines)
│   ├── gcs_storage.py                  # Google Cloud Storage abstraction (541 lines)
│   ├── firestore_cache.py              # Distributed Firestore caching (613 lines)
│   ├── secrets_manager.py              # Google Secret Manager integration (281 lines)
│   └── vertex_ai_client.py            # Vertex AI Model Garden client (723 lines)
│
├── Workflow & Orchestration
│   ├── claude_workflow_enhancement.py  # Multi-stage workflow orchestrator (818 lines)
│   └── workflow_simple_example.py      # Workflow integration examples (303 lines)
│
├── Skill Modules
│   ├── hvac_insulation_skill.py        # Standalone Agent SDK skill (588 lines)
│   └── hvac_skill_example.py           # Skill usage examples (339 lines)
│
├── Legacy/Alternative Systems
│   ├── gemini_pdf_extractor.py         # Google Gemini PDF processor (339 lines)
│   └── process_my_pdfs.py              # Simple PDF helper script (195 lines)
│
├── Frontend (React/TypeScript)
│   ├── App.tsx                         # React application (1281 lines)
│   ├── estimator.ts                    # TypeScript estimation engine (269 lines)
│   ├── geminiService.ts                # Gemini API integration (345 lines)
│   ├── services/geminiService.ts       # Gemini service (services dir) (345 lines)
│   ├── types.ts                        # TypeScript type definitions (101 lines)
│   ├── constants.ts                    # Configuration constants (79 lines)
│   ├── index.tsx                       # React entry point (16 lines)
│   └── vite.config.ts                  # Vite build configuration (23 lines)
│
├── Figma Plugin (figma-plugin/)
│   ├── manifest.json                   # Figma plugin manifest
│   ├── package.json                    # Plugin dependencies
│   ├── tsconfig.json                   # TypeScript configuration
│   ├── webpack.config.js               # Sandbox code build config
│   ├── webpack.ui.config.js            # UI build config
│   └── src/
│       ├── code.ts                     # Figma sandbox (scene graph access)
│       ├── ui.tsx                       # Plugin UI (React, tabbed interface)
│       ├── ui.html                      # UI HTML shell
│       ├── types.ts                     # Plugin-specific type definitions
│       ├── services/
│       │   └── estimationService.ts    # Backend API + local estimation
│       └── utils/
│           └── measurementExtractor.ts # HVAC node classification & measurement
│
├── Testing
│   ├── tests/
│   │   └── test_agent_tools.py         # Main test suite (45+ tests, 544 lines)
│   └── test_easiest_workflow.py        # Workflow orchestration tests (452 lines)
│
├── Documentation (18 files, 250+ KB)
│   ├── README.md                       # Main entry point
│   ├── CLAUDE.md                       # AI assistant guide (this file)
│   ├── PROJECT_SUMMARY.md              # Complete project overview
│   ├── CLAUDE_AGENTS_ARCHITECTURE.md   # System architecture
│   ├── USER_MANUAL.md                  # Complete user guide
│   ├── AGENT_SETUP_GUIDE.md            # Technical setup
│   ├── AI_SETUP_GUIDE.md               # AI setup instructions
│   ├── DEPLOYMENT_GUIDE.md             # Hosting options (detailed)
│   ├── DEPLOYMENT.md                   # Deployment overview
│   ├── GCP_MIGRATION_GUIDE.md          # Enterprise GCP integration guide
│   ├── PRODUCTION_ENHANCEMENTS.md      # Performance optimizations
│   ├── QUICK_START_CHECKLIST.md        # 30-min setup
│   ├── STREAMLIT_README.md             # Streamlit app docs
│   ├── TECHNOLOGY_ROADMAP_2025.md      # 2025 SaaS platform roadmap
│   ├── Estimator_Agent_Workflow.md     # Agent workflow documentation
│   ├── HVAC_SKILL_README.md            # HVAC skill documentation
│   └── README_STUDIO.md               # Google AI Studio notes
│
├── Configuration
│   ├── requirements.txt                # Python dependencies (83 lines)
│   ├── package.json                    # JavaScript dependencies
│   ├── tsconfig.json                   # TypeScript configuration
│   ├── .streamlit/config.toml          # Streamlit configuration
│   ├── .streamlit/secrets.toml.example # Secrets template
│   ├── Dockerfile                      # Container definition (Cloud Run)
│   ├── docker-compose.yml              # Local dev multi-container setup
│   ├── cloudbuild.yaml                 # Google Cloud Build CI/CD
│   ├── .gitignore                      # Git ignore patterns
│   ├── .devcontainer/devcontainer.json # VS Code dev container
│   └── .github/copilot-instructions.md # GitHub Copilot instructions
│
├── Data Files
│   ├── pricebook_sample.json           # Sample pricing data (19 items)
│   ├── measurements_template.csv       # Measurement template
│   └── metadata.json                   # Project metadata
│
├── Scripts
│   ├── run.sh                          # Unix startup script
│   └── run.bat                         # Windows startup script
│
└── Other
    ├── studio_wrapper.js               # Google AI Studio JS wrapper
    ├── google_ai_studio_package.zip    # AI Studio package
    └── index.html                      # Vite HTML entry point
```

---

## Technology Stack

### Python Backend

```python
# Core AI/ML
anthropic>=0.40.0              # Claude Agents SDK (PRIMARY)
google-generativeai>=0.8.0     # Gemini (legacy support)
pydantic>=2.0.0                # Data validation

# PDF Processing
pdfplumber>=0.10.0             # Text extraction
pdf2image>=1.16.0              # Image conversion
pymupdf>=1.23.0                # Fast rendering (3-5x faster)
opencv-python-headless>=4.8.0  # Computer vision
pillow>=10.0.0                 # Image processing

# Web Framework
streamlit>=1.30.0              # UI framework

# Data Processing
pandas>=2.0.0                  # DataFrames
numpy>=1.24.0                  # Numerical operations
openpyxl>=3.1.0                # Excel support

# Visualization
plotly>=5.18.0                 # Interactive charts
altair>=5.2.0                  # Declarative visualizations

# Google Cloud Platform
google-cloud-storage>=2.10.0       # GCS for PDF uploads/files
google-cloud-firestore>=2.11.0     # Distributed caching
google-cloud-secret-manager>=2.16.0 # Secure API key storage
google-cloud-logging>=3.5.0        # Structured logging in GCP

# Performance
aiofiles>=23.0.0               # Async file operations
python-dotenv>=1.0.0           # Environment management

# Testing
pytest>=7.4.0                  # Test framework
pytest-asyncio>=0.21.0         # Async testing
pytest-cov>=4.1.0              # Coverage reporting
```

### JavaScript/TypeScript Frontend

```json
{
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "@google/genai": "^1.23.0",
    "uuid": "^13.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.14.0",
    "typescript": "~5.8.2",
    "vite": "^6.2.0",
    "@vitejs/plugin-react": "^5.0.0"
  }
}
```

---

## Architecture Overview

### System Architecture (High-Level)

```
┌──────────────────────────────────────────────┐
│            USER INTERFACES                   │
├──────────────────────────────────────────────┤
│  • agent_estimation_app.py (Streamlit)       │  ← RECOMMENDED: Conversational
│  • streamlit_app.py (Streamlit)              │  ← Full-featured SaaS
│  • App.tsx (React/TypeScript)                │  ← Web UI
│  • figma-plugin/ (Figma Plugin)              │  ← Design tool integration
│  • claude_estimation_agent.py (CLI)          │  ← Terminal
│  • hvac_insulation_skill.py (Agent SDK)      │  ← Embeddable skill
│  • Python API (programmatic)                 │  ← Code integration
└──────────────────┬───────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────┐
│     WORKFLOW ORCHESTRATION LAYER             │
├──────────────────────────────────────────────┤
│  • WorkflowOrchestrator (5-stage pipeline)   │
│  • ValidationGate (quality checks)           │
│  • RecommendationEngine (suggestions)        │
│  • Audit trail and metrics tracking          │
│  Stages: discovery → document_analysis →     │
│    data_enrichment → calculation →           │
│    quote_generation                          │
└──────────────────┬───────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────┐
│       CLAUDE ESTIMATION AGENT                │
├──────────────────────────────────────────────┤
│  • Multi-turn conversations                  │
│  • Tool orchestration                        │
│  • Intelligent decision-making               │
│  • Error recovery & validation               │
│  • Parallel processing coordination          │
└──────────────────┬───────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────┐
│          AGENT TOOL SUITE                    │
├──────────────────────────────────────────────┤
│  1. extract_project_info                     │
│  2. extract_specifications                   │
│  3. extract_measurements                     │
│  4. validate_specifications                  │
│  5. cross_reference_data                     │
│  6. calculate_material_quantities            │
│  7. generate_detailed_quote                  │
└──────────────────┬───────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────┐
│       CORE ESTIMATION ENGINE                 │
├──────────────────────────────────────────────┤
│  • SpecificationExtractor                    │
│  • DrawingMeasurementExtractor               │
│  • PricingEngine                             │
│  • QuoteGenerator                            │
└──────────────────┬───────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────┐
│     GCP INFRASTRUCTURE LAYER                 │
├──────────────────────────────────────────────┤
│  • Vertex AI Model Garden (Claude API)       │
│  • Google Cloud Storage (file management)    │
│  • Firestore (distributed caching)           │
│  • Secret Manager (API key storage)          │
│  • Cloud Run (container hosting)             │
│  • Cloud Build (CI/CD pipeline)              │
└──────────────────┬───────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────┐
│           DATA LAYER                         │
├──────────────────────────────────────────────┤
│  • Distributor Price Books (JSON/CSV)        │
│  • Material Specifications Library           │
│  • Labor Rate Tables                         │
│  • Building Code References                  │
└──────────────────────────────────────────────┘
```

### Core Components

#### 1. Agent Layer (`claude_estimation_agent.py`)

**Purpose:** Main orchestrator for conversational estimation workflow

**Key Classes:**
- `InsulationEstimationAgent`: Main agent with conversation state management

**Key Methods:**
- `run(user_message, context)`: Execute agent loop with tool use
- `_register_tools()`: Register available tools
- `_format_tools_for_claude()`: Format tools for Claude API

**Design Patterns:**
- Agentic workflow with tool calling
- Conversation state management
- Error recovery and retry logic

#### 2. Tool Suite (`claude_agent_tools.py`)

**Purpose:** Specialized AI tools for estimation tasks

**Available Tools:**
1. `extract_project_info`: Extracts project metadata from cover sheets
2. `extract_specifications`: Analyzes spec documents for insulation requirements
3. `extract_measurements`: Extracts measurements from drawings
4. `validate_specifications`: Validates specs against industry standards
5. `cross_reference_data`: Cross-references specs, measurements, and drawings
6. `calculate_material_quantities`: Calculates precise material quantities
7. `generate_detailed_quote`: Creates professional quote documents

**Design Patterns:**
- Tool handler functions with type hints
- Pydantic schemas for input/output validation
- Claude vision API integration for PDF analysis
- PDF-to-base64 conversion utilities

#### 3. Core Engine (`hvac_insulation_estimator.py`)

**Purpose:** Domain-specific estimation logic

**Key Classes:**
- `SpecificationExtractor`: Extracts insulation specs from documents
- `DrawingMeasurementExtractor`: Extracts measurements from drawings
- `PricingEngine`: Calculates material quantities and pricing
- `QuoteGenerator`: Generates professional quotes

**Data Models (dataclasses):**
- `InsulationSpec`: Specification data structure
- `MeasurementItem`: Measurement data structure
- `MaterialItem`: Material list item
- `ProjectQuote`: Complete quote data

#### 4. Workflow Orchestration (`claude_workflow_enhancement.py`)

**Purpose:** Multi-stage estimation pipeline with validation and quality tracking

**Key Classes:**
- `WorkflowOrchestrator`: Manages 5-stage estimation pipeline
- `ValidationGate`: Enforces quality checks between stages
- `RecommendationEngine`: Generates intelligent suggestions

**Workflow Stages:**
1. `discovery` — Gather project info and requirements
2. `document_analysis` — Extract specs and measurements from PDFs
3. `data_enrichment` — Cross-reference, validate, and augment data
4. `calculation` — Calculate material quantities and pricing
5. `quote_generation` — Generate professional quote document

#### 5. GCP Integration Layer

**Cloud Configuration (`cloud_config.py`):**
- `CloudConfig` dataclass auto-detects environment (local vs GCP)
- Configures backends for caching, storage, and secrets
- Supports local development and Cloud Run production

**Storage (`gcs_storage.py`):**
- `StorageBackend` interface with local filesystem and GCS implementations
- Upload/download/delete operations
- Signed URL generation for temporary file access

**Distributed Caching (`firestore_cache.py`):**
- `CacheBackend` interface with Firestore, memory, and optional Redis backends
- TTL-based expiration for multi-instance Cloud Run deployments
- Automatic fallback to memory caching when Firestore is unavailable

**Secrets (`secrets_manager.py`):**
- `SecretManager` class integrating Google Secret Manager
- Falls back to environment variables for local development
- Caches secrets in memory with version support

**Vertex AI (`vertex_ai_client.py`):**
- `VertexAIClaudeClient` wrapper for Claude Opus 4.5 via Vertex AI Model Garden
- Enterprise GCP deployment with region support (us-central1, us-east4)
- Handles authentication, retries, and token management

#### 6. HVAC Skill Module (`hvac_insulation_skill.py`)

**Purpose:** Standalone Agent SDK skill wrapping the estimation engine

**Key Features:**
- Embeddable into any Claude-powered application
- Provides tool handlers and session state management
- Can be integrated as a skill into other agents

**Usage:** See `hvac_skill_example.py` for conversational, PDF analysis, and direct tool call examples.

#### 7. Figma Plugin (`figma-plugin/`)

**Purpose:** Figma design tool integration for extracting HVAC measurements directly from drawings and generating insulation estimates without leaving Figma.

**Architecture:**
- **Sandbox (`code.ts`):** Runs in the Figma main thread with scene graph access. Handles node traversal, measurement extraction, annotation layers, and SVG export.
- **UI (`ui.tsx`):** React-based tabbed interface running in an iframe. Four tabs: Extract, Estimate, Quote, Settings.
- **Measurement Extractor (`utils/measurementExtractor.ts`):** Classifies Figma nodes as HVAC elements by layer-name keywords, converts geometry to real-world units using configurable drawing scales.
- **Estimation Service (`services/estimationService.ts`):** Dual-mode estimation — local built-in engine (offline-capable) or remote API connecting to the Python backend.

**Key Features:**
- Automatic HVAC element detection from Figma layer names (duct, pipe, equipment keywords)
- Configurable drawing scale presets (1/4" = 1'-0", 1/8" = 1'-0", custom)
- Fitting detection from sibling node names (elbows, tees, reducers)
- Visual insulation annotation overlay on Figma elements
- Quote generation with material/labor breakdown and cost alternatives
- SVG export of annotated drawings
- Works offline with local estimation engine; optionally connects to backend API

**Communication:** Uses `postMessage` between sandbox and UI iframe with typed message contracts (`UIToPluginMessage`, `PluginToUIMessage`).

#### 8. Production Utilities

**Caching (`utils_cache.py`):**
- `FileCache` class with file-based caching
- TTL management and cache invalidation
- 90% API cost reduction through intelligent caching

**Async Processing (`utils_async.py`):**
- `AsyncBatchProcessor` for parallel PDF analysis
- Batch processing for 5-10x speed improvement
- Rate limiting and progress tracking
- Uses `AsyncAnthropic` client

**Cost Tracking (`utils_tracking.py`):**
- `APIUsageTracker` for real-time cost monitoring
- Supports Claude Opus 4.5 pricing with prompt caching (cache reads 90% cheaper)
- Budget alerts and usage analytics

**PDF Processing (`utils_pdf.py`):**
- Optimized rendering with PyMuPDF (3-5x faster than pdf2image)
- Smart page selection (85% cost reduction)
- DPI optimization and Claude-compatible image sizing

**Data Validation (`pydantic_models.py`):**
- 12+ Pydantic models: `InsulationSpecExtracted`, `MeasurementItemExtracted`, `ProjectInfoExtracted`, `ValidationReport`, `QuoteLineItem`, etc.
- Automatic validation with custom validators
- Type-safe data throughout the pipeline

**Error Handling (`errors.py`):**
- Custom exception hierarchy (12 types): `EstimationError`, `PDFError`, `PDFNotFoundError`, `SpecificationValidationError`, `APIKeyMissingError`, etc.
- Context-rich error messages with suggestions
- Structured error reporting

---

## Key Conventions

### Coding Standards

#### Python Code Style

```python
# ALWAYS use type hints
def extract_project_info(
    pdf_path: str,
    pages: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Extract project information from PDF.

    Args:
        pdf_path: Path to PDF file
        pages: Optional specific pages to analyze

    Returns:
        Dictionary with project metadata

    Raises:
        FileNotFoundError: If PDF doesn't exist
        InvalidPDFError: If PDF is corrupted
    """
    pass

# ALWAYS use Pydantic for data validation
from pydantic import BaseModel, Field

class InsulationSpec(BaseModel):
    """Validated insulation specification."""

    system_type: Literal["duct", "pipe", "equipment"]
    thickness: float = Field(gt=0, le=6)
    material: str

# ALWAYS handle errors explicitly
try:
    result = process_pdf(pdf_path)
except FileNotFoundError:
    logger.error(f"PDF not found: {pdf_path}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error processing PDF: {e}")
    raise ProcessingError(f"Failed to process PDF: {e}") from e

# ALWAYS use logging instead of print
import logging
logger = logging.getLogger(__name__)

logger.info("Processing started")
logger.warning("Missing optional data")
logger.error("Processing failed", exc_info=True)
```

#### File Naming Conventions

- **Python modules:** `lowercase_with_underscores.py`
- **Utilities:** `utils_*.py` pattern
- **GCP modules:** Named by service (e.g., `gcs_storage.py`, `firestore_cache.py`)
- **Tests:** `test_*.py` pattern
- **TypeScript:** `camelCase.ts`
- **React components:** `PascalCase.tsx`
- **Documentation:** `UPPERCASE.md` for guides, `README.md` for instructions

#### Import Organization

```python
# Standard library imports first
import os
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

# Third-party imports second
import pandas as pd
from anthropic import Anthropic
from pydantic import BaseModel

# GCP imports third (when applicable)
from google.cloud import storage
from google.cloud import firestore

# Local imports last
from hvac_insulation_estimator import SpecificationExtractor
from utils_cache import cache_result
from errors import ProcessingError
```

### API Conventions

#### Environment Variables

```bash
# REQUIRED
ANTHROPIC_API_KEY="sk-ant-..."        # Claude API key (direct or via Secret Manager)

# GCP CONFIGURATION (for cloud deployment)
GCP_PROJECT_ID="your-project-id"      # Google Cloud project
GCP_REGION="us-central1"              # Default region
GOOGLE_APPLICATION_CREDENTIALS="..."   # Service account key (local dev only)

# OPTIONAL
GEMINI_API_KEY="..."                  # Google Gemini (legacy)
CACHE_DIR="/path/to/cache"            # Cache directory (default: ./.cache)
LOG_LEVEL="INFO"                      # Logging level (default: INFO)
MAX_TOKENS=4096                       # Max tokens per request
MAX_CONCURRENT_REQUESTS=5             # Concurrency limit
```

#### Agent Tool Design

Every tool should follow this pattern:

```python
def tool_name_handler(
    required_param: str,
    optional_param: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tool description for Claude.

    This is what Claude sees when deciding to use this tool.
    Be clear about what the tool does and when to use it.

    Args:
        required_param: Description
        optional_param: Description

    Returns:
        Dictionary with:
        - result: Main result data
        - metadata: Additional context
        - warnings: Any issues found

    Raises:
        ToolError: If tool execution fails
    """
    try:
        # Validate inputs
        if not required_param:
            raise ValueError("required_param cannot be empty")

        # Execute tool logic
        result = perform_operation(required_param)

        # Return structured response
        return {
            "result": result,
            "metadata": {"timestamp": datetime.now().isoformat()},
            "warnings": []
        }

    except Exception as e:
        logger.exception(f"Tool {tool_name} failed")
        raise ToolError(f"Tool execution failed: {e}") from e

# Tool schema for Claude API
TOOL_SCHEMA = {
    "name": "tool_name",
    "description": "Clear description of what this tool does",
    "input_schema": {
        "type": "object",
        "properties": {
            "required_param": {
                "type": "string",
                "description": "What this parameter is for"
            },
            "optional_param": {
                "type": "string",
                "description": "Optional parameter"
            }
        },
        "required": ["required_param"]
    }
}
```

### Data Flow Conventions

#### Session State Management

```python
# Agent maintains session state
session_data = {
    "project_info": None,           # ProjectInfo object
    "specifications": [],           # List[InsulationSpec]
    "measurements": [],             # List[MeasurementItem]
    "pricing": None,                # PricingResult
    "quote": None,                  # ProjectQuote
    "uploaded_files": {}            # {filename: filepath}
}

# Access pattern
if session_data["specifications"]:
    # Process specifications
    pass
```

#### Caching Strategy

```python
# Local caching (utils_cache.py)
from utils_cache import cache_result

@cache_result(ttl=3600)  # Cache for 1 hour
def analyze_pdf(pdf_path: str) -> Dict:
    """This will be cached automatically."""
    # Expensive PDF analysis
    pass

# Cache key based on file content hash
# Same content = cache hit (even different filename)

# Distributed caching for Cloud Run (firestore_cache.py)
from firestore_cache import FirestoreCacheBackend

cache = FirestoreCacheBackend(project_id="my-project")
cache.set("key", value, ttl=3600)
result = cache.get("key")
```

---

## Development Workflows

### Setting Up Development Environment

```bash
# 1. Clone repository
git clone <repository-url>
cd PROINSULATIONESTIMATION

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
export ANTHROPIC_API_KEY="your-key"

# 5. Run tests to verify setup
pytest tests/

# 6. Run demo to verify everything works
python demo_agent.py --demo 1
```

### Setting Up GCP Development

```bash
# 1. Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# 2. Authenticate
gcloud auth application-default login

# 3. Set project
gcloud config set project YOUR_PROJECT_ID

# 4. Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# 5. Verify GCP modules work
python -c "from cloud_config import CloudConfig; print(CloudConfig())"
```

### Running Applications

```bash
# Agent-powered Streamlit app (RECOMMENDED)
streamlit run agent_estimation_app.py

# Full-featured SaaS app
streamlit run streamlit_app.py

# Simple Claude app
streamlit run estimation_app.py

# CLI interface
python claude_estimation_agent.py

# React web app
npm install
npm run dev

# Figma plugin (development)
cd figma-plugin && npm install && npm run dev

# Workflow example
python workflow_simple_example.py
```

### Testing Workflow

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agent_tools.py

# Run workflow tests
pytest test_easiest_workflow.py

# Run with coverage
pytest --cov=. --cov-report=html tests/

# Run specific test
pytest tests/test_agent_tools.py::test_extract_specifications

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "extract"
```

### Docker / Cloud Run Deployment

```bash
# Local Docker
docker build -t insulation-estimator .
docker run -p 8501:8501 -e ANTHROPIC_API_KEY="..." insulation-estimator

# Local with docker-compose (hot reload)
docker-compose up

# GCP Cloud Build (CI/CD)
gcloud builds submit --config=cloudbuild.yaml
```

### Adding New Features

#### 1. Adding a New Agent Tool

```python
# Step 1: Implement handler in claude_agent_tools.py
def new_tool_handler(param: str) -> Dict[str, Any]:
    """Tool description."""
    # Implementation
    pass

# Step 2: Define tool schema
NEW_TOOL_SCHEMA = {
    "name": "new_tool",
    "description": "What it does",
    "input_schema": {...}
}

# Step 3: Register in AGENT_TOOLS
AGENT_TOOLS = {
    # ... existing tools ...
    "new_tool": new_tool_handler
}

# Step 4: Add to tool schemas
def get_tool_schemas():
    return [..., NEW_TOOL_SCHEMA]

# Step 5: Write tests
def test_new_tool():
    result = new_tool_handler("test")
    assert result["success"]
```

#### 2. Adding a New Pydantic Model

```python
# In pydantic_models.py
from pydantic import BaseModel, Field, validator

class NewModel(BaseModel):
    """Model description."""

    required_field: str = Field(description="What this is")
    optional_field: Optional[int] = Field(default=None)

    @validator('required_field')
    def validate_required_field(cls, v):
        """Custom validation logic."""
        if not v.strip():
            raise ValueError("Cannot be empty")
        return v.strip()
```

#### 3. Modifying the Agent System Prompt

```python
# In claude_estimation_agent.py
@property
def system_prompt(self) -> str:
    """
    System prompt defining agent behavior.

    IMPORTANT: Changes here affect ALL agent interactions.
    Test thoroughly before deploying.
    """
    return """
    You are an expert HVAC insulation estimator...

    [Your modifications here]
    """
```

#### 4. Adding a New GCP Integration

```python
# Follow the pattern established by existing GCP modules:
# 1. Define an interface/base class
# 2. Implement local fallback for development
# 3. Implement GCP backend for production
# 4. Use cloud_config.py for environment detection

from cloud_config import CloudConfig

config = CloudConfig()
if config.is_gcp:
    # Use GCP backend
    backend = GCPBackend(project_id=config.project_id)
else:
    # Use local fallback
    backend = LocalBackend()
```

### Git Workflow

```bash
# ALWAYS work on feature branches
git checkout -b feature/new-tool

# Make changes, commit frequently
git add claude_agent_tools.py tests/test_agent_tools.py
git commit -m "Add new_tool for extracting XYZ"

# Push to feature branch
git push -u origin feature/new-tool

# Create pull request for review
# (Follow PR template if available)
```

---

## Testing Strategy

### Test Organization

```
tests/
└── test_agent_tools.py          # Main test suite (45+ tests, 544 lines)
    ├── Unit Tests               # Test individual functions
    ├── Integration Tests        # Test tool interactions
    └── Performance Tests        # Test optimization effectiveness

test_easiest_workflow.py         # Workflow orchestration tests (452 lines, 5 tests)
    ├── Workflow creation
    ├── Stage access
    ├── Data updates
    ├── Stage completion
    └── Recommendation engine
```

### Test Categories

#### 1. Unit Tests

```python
def test_extract_specifications_basic():
    """Test basic specification extraction."""
    result = extract_specifications_handler(
        pdf_path="tests/fixtures/sample_spec.pdf"
    )

    assert len(result["specifications"]) > 0
    assert all(isinstance(s, dict) for s in result["specifications"])
```

#### 2. Integration Tests

```python
def test_full_estimation_workflow():
    """Test complete end-to-end workflow."""
    agent = InsulationEstimationAgent(api_key=TEST_API_KEY)

    # Upload spec
    response1 = agent.run("Analyze spec.pdf")
    assert "specifications" in response1.lower()

    # Request quote
    response2 = agent.run("Generate a quote")
    assert "$" in response2
```

#### 3. Workflow Tests

```python
def test_workflow_stage_completion():
    """Test workflow stage progression."""
    orchestrator = WorkflowOrchestrator()

    assert orchestrator.current_stage == "discovery"
    orchestrator.complete_stage("discovery")
    assert orchestrator.current_stage == "document_analysis"
```

#### 4. Performance Tests

```python
def test_cache_effectiveness():
    """Verify caching reduces API calls."""
    # First call - should hit API
    start = time.time()
    result1 = analyze_pdf("test.pdf")
    duration1 = time.time() - start

    # Second call - should hit cache
    start = time.time()
    result2 = analyze_pdf("test.pdf")
    duration2 = time.time() - start

    # Cache should be 10x+ faster
    assert duration2 < duration1 / 10
    assert result1 == result2
```

### Running Tests

```bash
# All tests
pytest

# With output
pytest -v

# Specific test
pytest tests/test_agent_tools.py::test_extract_specifications

# With coverage
pytest --cov=. --cov-report=html

# Stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "extract"
```

---

## Common Tasks

### Task 1: Analyzing a PDF Specification

```python
# Using agent (recommended)
from claude_estimation_agent import create_agent

agent = create_agent()
response = agent.run("Analyze specification.pdf")

# Using tools directly
from claude_agent_tools import extract_specifications_handler

result = extract_specifications_handler(
    pdf_path="specification.pdf"
)

specifications = result["specifications"]
warnings = result["warnings"]
```

### Task 2: Generating a Quote

```python
# Complete workflow
agent = create_agent()

# Step 1: Upload documents
agent.run("I have a spec.pdf and drawing.pdf")

# Step 2: Request analysis
agent.run("Extract all specifications and measurements")

# Step 3: Generate quote
agent.run("Generate a detailed quote")

# Quote is automatically saved to file
```

### Task 3: Using the Workflow Orchestrator

```python
from claude_workflow_enhancement import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()

# Check current stage
print(orchestrator.current_stage)  # "discovery"

# Add data to the workflow
orchestrator.add_data("project_info", {...})

# Complete a stage and move to next
orchestrator.complete_stage("discovery")

# Get recommendations
recommendations = orchestrator.get_recommendations()
```

### Task 4: Optimizing API Costs

```python
# Use caching for repeated operations
from utils_cache import FileCache

cache = FileCache(cache_dir=".cache")

# Enable cost tracking
from utils_tracking import APIUsageTracker

tracker = APIUsageTracker()
# ... do work, tracker records usage ...
report = tracker.get_report()
print(f"Total cost: ${report['total_cost']:.2f}")
```

### Task 5: Batch Processing Multiple PDFs

```python
from utils_async import AsyncBatchProcessor

processor = AsyncBatchProcessor()
pdfs = ["spec1.pdf", "spec2.pdf", "spec3.pdf"]

results = await processor.process_batch(
    pdf_paths=pdfs,
    max_concurrent=3
)

# Results returned in same order as input
```

### Task 6: Validating Data

```python
from pydantic_models import InsulationSpecExtracted

# This will automatically validate
try:
    spec = InsulationSpecExtracted(
        system_type="supply_duct",
        size_range="12-24 inch",
        thickness=2.0,
        material="fiberglass",
        facing="FSK",
        location="indoor",
        confidence=0.95,
        spec_text="2\" fiberglass with FSK",
        page_number=15
    )
except ValidationError as e:
    # Handle validation errors
    print(e.errors())
```

### Task 7: Using Vertex AI (Enterprise)

```python
from vertex_ai_client import VertexAIClaudeClient

client = VertexAIClaudeClient(
    project_id="your-project",
    region="us-central1"
)

response = client.create_message(
    model="claude-opus-4-5-20251101",
    messages=[{"role": "user", "content": "Analyze this spec..."}],
    max_tokens=4096
)
```

### Task 8: Using the HVAC Skill

```python
from hvac_insulation_skill import HVACInsulationSkill

skill = HVACInsulationSkill()

# Conversational estimation
response = skill.run("I need insulation for a 24-inch supply duct")

# Or integrate into another agent as a tool
```

### Task 9: Using the Figma Plugin

```bash
# 1. Build the plugin
cd figma-plugin
npm install
npm run build

# 2. In Figma Desktop:
#    Plugins → Development → Import plugin from manifest...
#    Select figma-plugin/manifest.json

# 3. Usage within Figma:
#    - Open a drawing with HVAC layers named using keywords
#      (e.g., "24x20 Supply Duct", "2\" CHW Pipe", "AHU-1")
#    - Run the plugin: Plugins → Pro Insulation Estimator
#    - Set the drawing scale on the Extract tab
#    - Click "Extract All from Page" or select elements first
#    - Review measurements, configure pricing on the Estimate tab
#    - Generate a quote and export
```

```typescript
// Programmatic use of the estimation service (outside Figma)
import { estimateLocally, buildEstimationRequest } from './services/estimationService';

const request = buildEstimationRequest(
  { projectName: 'Building A', location: 'Denver', customer: 'ACME', date: '2026-02-19', quoteNumber: '' },
  measurements,  // FigmaMeasurement[]
  { figmaUnitsPerFoot: 24, label: '1/4" = 1\'-0"' },
  { materialMarkup: 15, laborMarkup: 10, overheadProfit: 15, contingency: 10, laborRate: 85, includeAlternatives: true }
);

const result = estimateLocally(request);
console.log(`Grand Total: $${result.grandTotal}`);
```

---

## File Organization

### Python Modules

| File | Purpose | Lines | Key Classes/Functions |
|------|---------|-------|----------------------|
| `claude_estimation_agent.py` | Agent orchestrator | 616 | `InsulationEstimationAgent` |
| `claude_agent_tools.py` | Tool implementations | 1107 | 7 tool handlers + schemas |
| `hvac_insulation_estimator.py` | Core engine | 1081 | `SpecificationExtractor`, `PricingEngine`, `QuoteGenerator` |
| `claude_workflow_enhancement.py` | Workflow orchestration | 818 | `WorkflowOrchestrator`, `ValidationGate`, `RecommendationEngine` |
| `vertex_ai_client.py` | Vertex AI integration | 723 | `VertexAIClaudeClient` |
| `firestore_cache.py` | Distributed caching | 613 | `CacheBackend`, `FirestoreCacheBackend` |
| `hvac_insulation_skill.py` | Agent SDK skill | 588 | `HVACInsulationSkill` |
| `gcs_storage.py` | Cloud storage | 541 | `StorageBackend`, GCS operations |
| `pydantic_models.py` | Data validation | 417 | 12+ Pydantic models |
| `errors.py` | Error handling | 410 | 12 custom exception types |
| `utils_pdf.py` | PDF processing | 369 | PyMuPDF optimized rendering |
| `utils_cache.py` | File-based caching | 339 | `FileCache`, TTL management |
| `utils_async.py` | Async processing | 326 | `AsyncBatchProcessor` |
| `cloud_config.py` | Cloud configuration | 325 | `CloudConfig` (auto-detect env) |
| `utils_tracking.py` | Cost tracking | 300 | `APIUsageTracker` |
| `secrets_manager.py` | Secret management | 281 | `SecretManager` |

### Streamlit Apps

| File | Purpose | Lines | Features |
|------|---------|-------|----------|
| `agent_estimation_app.py` | Agent-powered UI | 431 | Conversational interface, chat history, file uploads |
| `streamlit_app.py` | Full-featured SaaS | 841 | Complete workflow, advanced features, dashboards |
| `estimation_app.py` | Simple Claude app | 524 | Basic Claude integration, minimal UI |

### TypeScript/React

| File | Purpose | Lines | Technologies |
|------|---------|-------|--------------|
| `App.tsx` | Main React app | 1281 | React 19, TypeScript, Vite |
| `geminiService.ts` | Gemini integration | 345 | Google Gemini API |
| `estimator.ts` | Estimation logic | 269 | TypeScript calculation engine |
| `types.ts` | Type definitions | 101 | TypeScript interfaces |
| `constants.ts` | Pricing constants | 79 | Pricing data, labor rates |

### Figma Plugin (`figma-plugin/`)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `src/code.ts` | Figma sandbox (main thread) | Scene graph access, node traversal, annotation |
| `src/ui.tsx` | Plugin UI (React) | Tabbed interface: Extract, Estimate, Quote, Settings |
| `src/types.ts` | Plugin type definitions | `FigmaMeasurement`, `EstimationResult`, message types |
| `src/services/estimationService.ts` | Estimation engine | `estimateLocally()`, `estimateViaAPI()` |
| `src/utils/measurementExtractor.ts` | Node classification | `extractMeasurements()`, `classifyNode()` |

### Test Files

| File | Purpose | Lines | Test Count |
|------|---------|-------|------------|
| `tests/test_agent_tools.py` | Main test suite | 544 | 45+ tests |
| `test_easiest_workflow.py` | Workflow tests | 452 | 5 tests |

---

## AI Assistant Guidelines

### When Working With This Codebase

#### DO:

1. **Read existing documentation first**
   - Check README.md for overview
   - Review CLAUDE_AGENTS_ARCHITECTURE.md for design
   - Consult GCP_MIGRATION_GUIDE.md for cloud infrastructure
   - Review Estimator_Agent_Workflow.md for workflow details

2. **Use type hints everywhere**
   ```python
   # Good
   def process(data: Dict[str, Any]) -> List[str]:
       pass

   # Bad
   def process(data):
       pass
   ```

3. **Use Pydantic for data validation**
   ```python
   # Good - automatic validation
   spec = InsulationSpecExtracted(**data)

   # Bad - no validation
   spec = data
   ```

4. **Handle errors explicitly**
   ```python
   # Good
   try:
       result = risky_operation()
   except SpecificError as e:
       logger.error(f"Failed: {e}")
       raise

   # Bad
   result = risky_operation()  # May crash silently
   ```

5. **Use logging, not print**
   ```python
   # Good
   logger.info("Processing started")

   # Bad
   print("Processing started")
   ```

6. **Cache expensive operations**
   ```python
   # Good
   @cache_result(ttl=3600)
   def expensive_api_call():
       pass

   # Bad - hits API every time
   def expensive_api_call():
       pass
   ```

7. **Write tests for new features**
   ```python
   def test_new_feature():
       result = new_feature("test")
       assert result == expected
   ```

8. **Update documentation when changing behavior**
   - Update docstrings
   - Update relevant .md files
   - Add examples if needed

9. **Use `cloud_config.py` for environment detection**
   ```python
   from cloud_config import CloudConfig
   config = CloudConfig()
   if config.is_gcp:
       # GCP-specific behavior
   ```

10. **Follow the GCP module pattern** for new cloud integrations
    - Define an interface/base class
    - Implement local fallback
    - Implement cloud backend
    - Use `CloudConfig` for detection

#### DON'T:

1. **Don't modify core estimation logic without testing**
   - `hvac_insulation_estimator.py` is critical
   - Changes affect all interfaces
   - Always run full test suite

2. **Don't commit API keys or credentials**
   ```python
   # Bad
   api_key = "sk-ant-..."

   # Good
   api_key = os.getenv("ANTHROPIC_API_KEY")
   # Or use secrets_manager.py for production
   ```

3. **Don't use print() for logging**
   - Use `logging` module
   - Maintains consistency
   - Can be configured

4. **Don't skip validation**
   ```python
   # Bad
   thickness = data.get("thickness")  # Could be None, string, etc.

   # Good
   spec = InsulationSpecExtracted(**data)  # Validates type
   thickness = spec.thickness
   ```

5. **Don't make API calls without caching**
   - API calls are expensive
   - Caching saves 90%+ costs
   - Use `@cache_result` decorator or `firestore_cache.py`

6. **Don't modify system prompts without approval**
   - System prompt affects all agent behavior
   - Test thoroughly
   - Document changes

7. **Don't create new files without good reason**
   - Use existing modules
   - Keep codebase organized
   - Follow naming conventions

8. **Don't hardcode GCP configuration**
   - Use `cloud_config.py` for environment detection
   - Use `secrets_manager.py` for API keys
   - Support both local and cloud environments

### Code Review Checklist

Before submitting changes:

- [ ] Type hints added to all functions
- [ ] Docstrings added/updated
- [ ] Pydantic models used for data validation
- [ ] Error handling implemented
- [ ] Logging used instead of print
- [ ] Tests written and passing
- [ ] No API keys or secrets committed
- [ ] Documentation updated if needed
- [ ] Code follows existing patterns
- [ ] Caching used for expensive operations
- [ ] GCP modules support local fallback

### Common Pitfalls

1. **Not using type hints**
   - Makes code harder to maintain
   - Reduces IDE autocomplete
   - Harder to catch bugs

2. **Skipping Pydantic validation**
   - Runtime errors instead of validation errors
   - Harder to debug
   - Data corruption possible

3. **Not caching API calls**
   - Wastes money (95% more expensive)
   - Slower performance
   - Hits rate limits

4. **Modifying state incorrectly**
   - Agent state must be immutable
   - Use session_data pattern
   - Don't modify tool inputs

5. **Poor error messages**
   ```python
   # Bad
   raise Exception("Error")

   # Good
   raise ProcessingError(
       f"Failed to process {pdf_path}: {error_details}",
       context={"pdf": pdf_path, "page": page_num}
   )
   ```

6. **Ignoring local/cloud duality**
   - Always provide local fallbacks for GCP services
   - Test both code paths
   - Use `CloudConfig` for detection

### Best Practices for AI Assistants

1. **Understand the domain**
   - HVAC insulation is specialized
   - Read industry terminology
   - Ask before making assumptions

2. **Preserve existing patterns**
   - Don't reinvent wheels
   - Use established utilities
   - Follow coding conventions

3. **Test with real PDFs**
   - Sample PDFs in tests/fixtures
   - Real-world documents vary
   - Edge cases are common

4. **Consider performance**
   - API calls are expensive
   - Use async for I/O operations
   - Cache aggressively

5. **Maintain documentation**
   - Code is read more than written
   - Future AI assistants will thank you
   - Users rely on accurate docs

6. **Understand the GCP integration**
   - Review `GCP_MIGRATION_GUIDE.md` before touching cloud modules
   - `cloud_config.py` is the entry point for environment detection
   - All GCP modules have local development fallbacks

---

## Deployment Considerations

### Environment Variables Required

```bash
# Production (Direct Anthropic)
ANTHROPIC_API_KEY="sk-ant-..."

# Production (Vertex AI / GCP)
GCP_PROJECT_ID="your-project-id"
GCP_REGION="us-central1"

# Optional
GEMINI_API_KEY="..."
CACHE_DIR="/var/cache/estimation"
LOG_LEVEL="WARNING"
MAX_CONCURRENT_REQUESTS=5
```

### Docker Deployment (Local)

```bash
# Build image
docker build -t insulation-estimator .

# Run container
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY="..." \
  insulation-estimator

# Docker Compose (with hot reload)
docker-compose up
```

### GCP Cloud Run Deployment

```bash
# Using Cloud Build CI/CD (recommended)
gcloud builds submit --config=cloudbuild.yaml

# Manual deployment
gcloud run deploy insulation-estimator \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### Streamlit Cloud Deployment

1. Push to GitHub
2. Connect repository in Streamlit Cloud
3. Add secrets in dashboard:
   - `ANTHROPIC_API_KEY`
4. Deploy automatically

### Performance Optimization

- **Enable caching:** Set `CACHE_DIR` environment variable (local) or use Firestore (GCP)
- **Use async processing:** For batch operations via `utils_async.py`
- **Monitor costs:** Use `APIUsageTracker` in production
- **Limit concurrent requests:** Set `MAX_CONCURRENT_REQUESTS`
- **Use Vertex AI:** For enterprise deployments with SLA guarantees

---

## Quick Reference

### Key Commands

```bash
# Development
python demo_agent.py --demo 1          # Run demo
streamlit run agent_estimation_app.py  # Start web app
pytest tests/                          # Run tests
pytest test_easiest_workflow.py        # Run workflow tests

# Production
docker-compose up                      # Start containers (local)
gcloud builds submit --config=cloudbuild.yaml  # Deploy to GCP
python claude_estimation_agent.py      # CLI interface

# React frontend
npm install && npm run dev             # Development
npm run build                          # Production build

# Figma plugin
cd figma-plugin && npm install && npm run build  # Build plugin
cd figma-plugin && npm run dev                   # Watch mode
```

### Key Files to Modify

- **Add agent tool:** `claude_agent_tools.py`
- **Modify agent behavior:** `claude_estimation_agent.py` (system_prompt)
- **Add data model:** `pydantic_models.py`
- **Add utility:** `utils_*.py`
- **Update UI:** `agent_estimation_app.py` or `streamlit_app.py`
- **Add GCP service:** Follow pattern in `cloud_config.py` / `gcs_storage.py`
- **Add workflow stage:** `claude_workflow_enhancement.py`
- **Create embeddable skill:** `hvac_insulation_skill.py`
- **Modify Figma plugin:** `figma-plugin/src/` (code.ts, ui.tsx, services/, utils/)

### Getting Help

- **User guides:** `USER_MANUAL.md`, `QUICK_START_CHECKLIST.md`
- **Technical docs:** `CLAUDE_AGENTS_ARCHITECTURE.md`, `AGENT_SETUP_GUIDE.md`
- **Deployment:** `DEPLOYMENT_GUIDE.md`, `DEPLOYMENT.md`
- **GCP integration:** `GCP_MIGRATION_GUIDE.md`
- **Optimizations:** `PRODUCTION_ENHANCEMENTS.md`
- **Roadmap:** `TECHNOLOGY_ROADMAP_2025.md`
- **Workflow:** `Estimator_Agent_Workflow.md`
- **HVAC Skill:** `HVAC_SKILL_README.md`

---

## Version History

- **v2.5 (Current):** Enterprise GCP integration, workflow orchestration, HVAC skill module
- **v2.0:** Production-ready with Claude Agents SDK
- **v1.5:** Basic Claude integration
- **v1.0:** Initial release with Gemini

---

**Last Updated:** 2026-02-19
**Maintained By:** Development Team
**For Questions:** See documentation or GitHub issues
