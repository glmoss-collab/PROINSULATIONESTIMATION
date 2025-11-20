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
**Primary AI Model:** Claude 3.5 Sonnet (via Anthropic Agents SDK)
**Secondary AI:** Google Gemini (legacy support for PDF extraction)

### What This System Does

This system transforms manual insulation estimation (2-4 hours) into an intelligent, automated process (5-15 minutes) with:

- **Conversational AI estimation** using Claude Agents SDK
- **Automated document analysis** of PDF specifications and drawings
- **Intelligent validation** and cross-referencing
- **Professional quote generation** with material lists and pricing
- **Cost-saving alternatives** and recommendations
- **Multiple deployment options** (Web, CLI, API)

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
│   ├── claude_estimation_agent.py      # Main agent orchestrator (400 lines)
│   ├── claude_agent_tools.py           # Agent tool implementations (650 lines)
│   ├── hvac_insulation_estimator.py    # Core estimation engine (1000 lines)
│   ├── agent_estimation_app.py         # Agent-powered Streamlit UI (400 lines)
│   ├── streamlit_app.py                # Full-featured SaaS app (1200 lines)
│   ├── estimation_app.py               # Simple Claude app (600 lines)
│   └── demo_agent.py                   # Demo scripts and examples (400 lines)
│
├── Utility Modules (Production-Ready)
│   ├── utils_cache.py                  # Caching system (90% cost savings)
│   ├── utils_async.py                  # Async batch processing (5-10x faster)
│   ├── utils_tracking.py               # API cost tracking and monitoring
│   ├── utils_pdf.py                    # Optimized PDF processing (PyMuPDF)
│   ├── pydantic_models.py              # Type-safe data validation
│   └── errors.py                       # Custom exception hierarchy
│
├── Legacy/Alternative Systems
│   ├── gemini_pdf_extractor.py         # Google Gemini PDF processor
│   └── process_my_pdfs.py              # Simple PDF helper script
│
├── Frontend (React/TypeScript)
│   ├── App.tsx                         # React application (1500 lines)
│   ├── estimator.ts                    # TypeScript estimation engine
│   ├── geminiService.ts                # Gemini API integration
│   ├── types.ts                        # TypeScript type definitions
│   └── constants.ts                    # Configuration constants
│
├── Testing
│   └── tests/
│       └── test_agent_tools.py         # Test suite (45+ tests, 600 lines)
│
├── Documentation (10,000+ lines total)
│   ├── README.md                       # Main entry point
│   ├── PROJECT_SUMMARY.md              # Complete project overview
│   ├── CLAUDE_AGENTS_ARCHITECTURE.md   # System architecture
│   ├── USER_MANUAL.md                  # Complete user guide
│   ├── AGENT_SETUP_GUIDE.md            # Technical setup
│   ├── DEPLOYMENT_GUIDE.md             # Hosting options
│   ├── PRODUCTION_ENHANCEMENTS.md      # Optimizations
│   ├── QUICK_START_CHECKLIST.md        # 30-min setup
│   └── STREAMLIT_README.md             # Streamlit app docs
│
├── Configuration
│   ├── requirements.txt                # Python dependencies
│   ├── package.json                    # JavaScript dependencies
│   ├── .streamlit/config.toml          # Streamlit configuration
│   ├── Dockerfile                      # Container definition
│   ├── docker-compose.yml              # Multi-container setup
│   └── .gitignore                      # Git ignore patterns
│
├── Data Files
│   ├── pricebook_sample.json           # Sample pricing data
│   ├── measurements_template.csv       # Measurement template
│   └── metadata.json                   # Project metadata
│
└── Scripts
    ├── run.sh                          # Unix startup script
    └── run.bat                         # Windows startup script
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

# Web Framework
streamlit>=1.30.0              # UI framework

# Data Processing
pandas>=2.0.0                  # DataFrames
numpy>=1.24.0                  # Numerical operations
openpyxl>=3.1.0                # Excel support

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
┌─────────────────────────────────────────┐
│         USER INTERFACES                 │
├─────────────────────────────────────────┤
│  • agent_estimation_app.py (Streamlit)  │  ← RECOMMENDED: Conversational
│  • streamlit_app.py (Streamlit)         │  ← Full-featured SaaS
│  • App.tsx (React/TypeScript)           │  ← Web UI
│  • claude_estimation_agent.py (CLI)     │  ← Terminal
│  • Python API (programmatic)            │  ← Code integration
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│      CLAUDE ESTIMATION AGENT            │
├─────────────────────────────────────────┤
│  • Multi-turn conversations             │
│  • Tool orchestration                   │
│  • Intelligent decision-making          │
│  • Error recovery & validation          │
│  • Parallel processing coordination     │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│         AGENT TOOL SUITE                │
├─────────────────────────────────────────┤
│  1. extract_project_info                │
│  2. extract_specifications              │
│  3. extract_measurements                │
│  4. validate_specifications             │
│  5. cross_reference_data                │
│  6. calculate_material_quantities       │
│  7. generate_detailed_quote             │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│      CORE ESTIMATION ENGINE             │
├─────────────────────────────────────────┤
│  • SpecificationExtractor               │
│  • DrawingMeasurementExtractor          │
│  • PricingEngine                        │
│  • QuoteGenerator                       │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│          DATA LAYER                     │
├─────────────────────────────────────────┤
│  • Distributor Price Books (JSON/CSV)   │
│  • Material Specifications Library      │
│  • Labor Rate Tables                    │
│  • Building Code References             │
└─────────────────────────────────────────┘
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

#### 3. Core Engine (`hvac_insulation_estimator.py`)

**Purpose:** Domain-specific estimation logic

**Key Classes:**
- `SpecificationExtractor`: Extracts insulation specs from documents
- `DrawingMeasurementExtractor`: Extracts measurements from drawings
- `PricingEngine`: Calculates material quantities and pricing
- `QuoteGenerator`: Generates professional quotes

**Data Models:**
- `InsulationSpec`: Specification data structure
- `MeasurementItem`: Measurement data structure
- `MaterialItem`: Material list item
- `ProjectQuote`: Complete quote data

#### 4. Production Utilities

**Caching (`utils_cache.py`):**
- Intelligent caching for 90% API cost reduction
- File-based and memory caching strategies
- TTL management and cache invalidation

**Async Processing (`utils_async.py`):**
- Batch processing for 5-10x speed improvement
- Parallel API calls with rate limiting
- Progress tracking and callbacks

**Cost Tracking (`utils_tracking.py`):**
- Real-time API cost monitoring
- Budget alerts and limits
- Usage analytics and reporting

**PDF Processing (`utils_pdf.py`):**
- Optimized rendering with PyMuPDF (3-5x faster)
- Smart page selection (85% cost reduction)
- Vision-ready image conversion

**Data Validation (`pydantic_models.py`):**
- Type-safe data models
- Automatic validation and error messages
- Prevents malformed data

**Error Handling (`errors.py`):**
- Custom exception hierarchy (12 types)
- Clear, actionable error messages
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

# Local imports last
from hvac_insulation_estimator import SpecificationExtractor
from utils_cache import cache_result
from errors import ProcessingError
```

### API Conventions

#### Environment Variables

```bash
# REQUIRED
ANTHROPIC_API_KEY="sk-ant-..."     # Claude API key

# OPTIONAL
GEMINI_API_KEY="..."               # Google Gemini (legacy)
CACHE_DIR="/path/to/cache"         # Cache directory (default: ./.cache)
LOG_LEVEL="INFO"                   # Logging level (default: INFO)
MAX_TOKENS=4096                    # Max tokens per request
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
# ALWAYS cache expensive operations
from utils_cache import cache_result

@cache_result(ttl=3600)  # Cache for 1 hour
def analyze_pdf(pdf_path: str) -> Dict:
    """This will be cached automatically."""
    # Expensive PDF analysis
    pass

# Cache key based on file content hash
# Same content = cache hit (even different filename)
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

### Running Applications

```bash
# Agent-powered Streamlit app (RECOMMENDED)
streamlit run agent_estimation_app.py

# Full-featured SaaS app
streamlit run streamlit_app.py

# CLI interface
python claude_estimation_agent.py

# React web app
npm install
npm run dev
```

### Testing Workflow

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agent_tools.py

# Run with coverage
pytest --cov=. --cov-report=html tests/

# Run specific test
pytest tests/test_agent_tools.py::test_extract_specifications
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
└── test_agent_tools.py     # Main test suite (45+ tests)
    ├── Unit Tests          # Test individual functions
    ├── Integration Tests   # Test tool interactions
    └── Performance Tests   # Test optimization effectiveness
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

#### 3. Performance Tests

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

### Test Fixtures

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_spec_pdf():
    """Provide sample specification PDF."""
    return "tests/fixtures/sample_spec.pdf"

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    # Return mock client
    pass
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

### Task 3: Optimizing API Costs

```python
# Use caching for repeated operations
from utils_cache import CacheManager

cache = CacheManager(cache_dir=".cache")

# This will cache results
@cache.cache_result(ttl=3600)
def expensive_operation(data):
    # API calls here
    pass

# Enable cost tracking
from utils_tracking import CostTracker

tracker = CostTracker()
tracker.start_session()

# ... do work ...

report = tracker.end_session()
print(f"Total cost: ${report['total_cost']:.2f}")
```

### Task 4: Batch Processing Multiple PDFs

```python
from utils_async import batch_process_pdfs

pdfs = ["spec1.pdf", "spec2.pdf", "spec3.pdf"]

results = await batch_process_pdfs(
    pdf_paths=pdfs,
    processor_func=extract_specifications_handler,
    max_concurrent=3
)

# Results returned in same order as input
```

### Task 5: Validating Data

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

---

## File Organization

### Python Modules

| File | Purpose | Size | Key Classes/Functions |
|------|---------|------|----------------------|
| `claude_estimation_agent.py` | Agent orchestrator | 400 lines | `InsulationEstimationAgent` |
| `claude_agent_tools.py` | Tool implementations | 650 lines | 7 tool handlers + schemas |
| `hvac_insulation_estimator.py` | Core engine | 1000 lines | `SpecificationExtractor`, `PricingEngine`, `QuoteGenerator` |
| `pydantic_models.py` | Data validation | 400 lines | 12+ Pydantic models |
| `utils_cache.py` | Caching system | 500 lines | `CacheManager`, decorators |
| `utils_async.py` | Async processing | 350 lines | `batch_process_*` functions |
| `utils_tracking.py` | Cost tracking | 400 lines | `CostTracker`, analytics |
| `utils_pdf.py` | PDF processing | 450 lines | Optimized rendering |
| `errors.py` | Error handling | 350 lines | 12 custom exception types |

### Streamlit Apps

| File | Purpose | Features |
|------|---------|----------|
| `agent_estimation_app.py` | Agent-powered UI | Conversational interface, chat history, file uploads |
| `streamlit_app.py` | Full-featured SaaS | Complete workflow, advanced features, dashboards |
| `estimation_app.py` | Simple Claude app | Basic Claude integration, minimal UI |

### TypeScript/React

| File | Purpose | Technologies |
|------|---------|--------------|
| `App.tsx` | Main React app | React 19, TypeScript, Vite |
| `estimator.ts` | Estimation logic | TypeScript calculation engine |
| `geminiService.ts` | Gemini integration | Google Gemini API |
| `types.ts` | Type definitions | TypeScript interfaces |

---

## AI Assistant Guidelines

### When Working With This Codebase

#### DO:

1. **Read existing documentation first**
   - Check README.md for overview
   - Review CLAUDE_AGENTS_ARCHITECTURE.md for design
   - Consult relevant guides before asking

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

#### DON'T:

1. **Don't modify core estimation logic without testing**
   - `hvac_insulation_estimator.py` is critical
   - Changes affect all interfaces
   - Always run full test suite

2. **Don't commit API keys**
   ```python
   # Bad
   api_key = "sk-ant-..."

   # Good
   api_key = os.getenv("ANTHROPIC_API_KEY")
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
   - Use `@cache_result` decorator

6. **Don't modify system prompts without approval**
   - System prompt affects all agent behavior
   - Test thoroughly
   - Document changes

7. **Don't create new files without good reason**
   - Use existing modules
   - Keep codebase organized
   - Follow naming conventions

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

---

## Deployment Considerations

### Environment Variables Required

```bash
# Production
ANTHROPIC_API_KEY="sk-ant-..."

# Optional
GEMINI_API_KEY="..."
CACHE_DIR="/var/cache/estimation"
LOG_LEVEL="WARNING"
MAX_CONCURRENT_REQUESTS=5
```

### Docker Deployment

```bash
# Build image
docker build -t insulation-estimator .

# Run container
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY="..." \
  insulation-estimator
```

### Streamlit Cloud Deployment

1. Push to GitHub
2. Connect repository in Streamlit Cloud
3. Add secrets in dashboard:
   - `ANTHROPIC_API_KEY`
4. Deploy automatically

### Performance Optimization

- **Enable caching:** Set `CACHE_DIR` environment variable
- **Use async processing:** For batch operations
- **Monitor costs:** Use `CostTracker` in production
- **Limit concurrent requests:** Set `MAX_CONCURRENT_REQUESTS`

---

## Quick Reference

### Key Commands

```bash
# Development
python demo_agent.py --demo 1          # Run demo
streamlit run agent_estimation_app.py  # Start web app
pytest tests/                          # Run tests

# Production
docker-compose up                      # Start containers
python claude_estimation_agent.py      # CLI interface
```

### Key Files to Modify

- **Add agent tool:** `claude_agent_tools.py`
- **Modify agent behavior:** `claude_estimation_agent.py` (system_prompt)
- **Add data model:** `pydantic_models.py`
- **Add utility:** `utils_*.py`
- **Update UI:** `agent_estimation_app.py` or `streamlit_app.py`

### Getting Help

- **User guides:** `USER_MANUAL.md`, `QUICK_START_CHECKLIST.md`
- **Technical docs:** `CLAUDE_AGENTS_ARCHITECTURE.md`, `AGENT_SETUP_GUIDE.md`
- **Deployment:** `DEPLOYMENT_GUIDE.md`
- **Optimizations:** `PRODUCTION_ENHANCEMENTS.md`

---

## Version History

- **v2.0 (Current):** Production-ready with Claude Agents SDK
- **v1.5:** Basic Claude integration
- **v1.0:** Initial release with Gemini

---

**Last Updated:** 2025-11-20
**Maintained By:** Development Team
**For Questions:** See documentation or GitHub issues
