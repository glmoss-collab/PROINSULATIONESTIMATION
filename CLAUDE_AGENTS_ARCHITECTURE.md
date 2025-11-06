# Claude Agents SDK Architecture for Insulation Estimation

## Executive Summary

This document outlines the architecture for integrating **Anthropic Claude Agents SDK** into the Professional Insulation Estimation System. The integration transforms the current sequential workflow into an intelligent, autonomous estimation system powered by Claude with specialized tools and multi-step reasoning capabilities.

## Vision

Transform the estimation workflow from:
- **Manual, sequential steps** → **Conversational, intelligent automation**
- **Static PDF extraction** → **Dynamic validation and clarification**
- **Single-path calculations** → **Multi-option analysis with recommendations**
- **Isolated processing** → **Cross-referenced, validated project analysis**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│  (Streamlit App / CLI / API / Conversational Interface)     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              CLAUDE ESTIMATION AGENT                         │
│  (Claude 3.5 Sonnet with Extended Context & Tool Use)       │
│                                                              │
│  Capabilities:                                               │
│  • Multi-turn conversation                                   │
│  • Tool orchestration                                        │
│  • Intelligent decision making                               │
│  • Error recovery and validation                             │
│  • Parallel processing coordination                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   AGENT TOOL SUITE                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. DOCUMENT ANALYSIS TOOLS                                  │
│     ├── extract_project_info(pdf)                            │
│     ├── extract_specifications(pdf)                          │
│     ├── extract_measurements(pdf)                            │
│     └── analyze_drawing_metadata(pdf)                        │
│                                                              │
│  2. VALIDATION & ENRICHMENT TOOLS                            │
│     ├── validate_specifications(specs)                       │
│     ├── validate_measurements(measurements, specs)           │
│     ├── cross_reference_data(specs, measurements, drawings)  │
│     ├── suggest_missing_specs(project_type, measurements)    │
│     └── identify_conflicts(data)                             │
│                                                              │
│  3. CALCULATION & PRICING TOOLS                              │
│     ├── calculate_material_quantities(specs, measurements)   │
│     ├── calculate_labor_hours(measurements, specs)           │
│     ├── calculate_pricing(quantities, pricebook)             │
│     ├── generate_alternatives(specs, measurements)           │
│     └── optimize_costs(quote_data)                           │
│                                                              │
│  4. QUOTE GENERATION TOOLS                                   │
│     ├── generate_detailed_quote(project_data)                │
│     ├── generate_material_list(quote)                        │
│     ├── generate_executive_summary(quote)                    │
│     ├── generate_comparison_report(alternatives)             │
│     └── export_documents(quote, format)                      │
│                                                              │
│  5. KNOWLEDGE & REASONING TOOLS                              │
│     ├── get_industry_standards(system_type, location)        │
│     ├── recommend_specifications(system_type, environment)   │
│     ├── calculate_energy_savings(specs_comparison)           │
│     └── assess_code_compliance(specs, jurisdiction)          │
│                                                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│               CORE ESTIMATION ENGINE                         │
│  (Existing Python modules - hvac_insulation_estimator.py)   │
│                                                              │
│  • SpecificationExtractor                                    │
│  • DrawingMeasurementExtractor                               │
│  • PricingEngine                                             │
│  • QuoteGenerator                                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  DATA LAYER                                  │
│                                                              │
│  • Distributor Price Books (JSON/CSV/Excel)                  │
│  • Historical Project Database                               │
│  • Material Specifications Library                           │
│  • Labor Rate Tables                                         │
│  • Building Code References                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Workflow Examples

### Example 1: Single PDF Complete Estimation

```
User: "Analyze this specification PDF and create a quote."

Agent Workflow:
  1. 🔧 extract_project_info(pdf)
     → Project: "Commercial Office HVAC Retrofit"

  2. 🔧 extract_specifications(pdf)
     → 15 specifications found

  3. 🔧 validate_specifications(specs)
     → ⚠️  Warning: Outdoor duct spec missing weather protection

  4. 💬 Agent asks user: "I noticed outdoor ductwork specifications
     don't include aluminum jacketing. Should I add this requirement?"

  5. 🔧 extract_measurements(pdf)
     → Attempts measurement extraction from drawings
     → ⚠️  No drawing sheets found in PDF

  6. 💬 Agent asks: "This PDF contains only specifications.
     Do you have a separate drawing PDF for measurements?"

  7. User uploads drawing PDF

  8. 🔧 extract_measurements(drawing_pdf)
     → 47 measurement items extracted

  9. 🔧 cross_reference_data(specs, measurements)
     → ✅ All measurements have matching specifications

 10. 🔧 calculate_material_quantities(specs, measurements)
     → Materials calculated

 11. 🔧 calculate_pricing(quantities, pricebook)
     → Quote total: $127,450

 12. 🔧 generate_alternatives(specs, measurements)
     → Alternative spec with elastomeric saves $8,200

 13. 💬 Agent presents: "I've generated your quote. Would you like
     to see the cost-saving alternative I identified?"

 14. 🔧 generate_detailed_quote(project_data)
     → Professional quote document created

 15. 🔧 export_documents(quote, ['pdf', 'csv', 'txt'])
     → Files ready for download
```

### Example 2: Conversational Estimation (No PDFs)

```
User: "I need a quote for insulating a 50-ton rooftop HVAC system."

Agent: "I'd be happy to help! Let me ask a few questions:

        1. What's the location/climate zone?
        2. Will any ductwork be exposed outdoors?
        3. Do you have measurements, or should I use typical sizing?"

User: "It's in Phoenix, AZ. About 30% of supply duct is on the roof.
       I don't have exact measurements yet."

Agent workflow:
  1. 🔧 recommend_specifications(
         system_type="rooftop_hvac",
         environment="hot_dry_climate",
         outdoor_exposure=true
     )
     → Recommends: R-8 ductwork, aluminum jacketing, FSK facing

  2. 🔧 suggest_typical_measurements(
         system_size="50_ton",
         system_type="rooftop"
     )
     → Estimates: 280 LF supply duct (18x12 avg),
                  200 LF return duct (24x18 avg)

  3. 💬 Agent presents: "Based on typical 50-ton systems:

     SPECIFICATIONS:
     • Supply duct: 2" fiberglass, FSK facing
     • Return duct: 1.5" fiberglass, FSK facing
     • Outdoor ductwork: Aluminum jacket, stainless bands

     ESTIMATED MEASUREMENTS:
     • Supply duct: 280 LF (18x12 avg)
       - Indoor: 196 LF
       - Outdoor: 84 LF
     • Return duct: 200 LF (24x18 avg) - indoor only

     Would you like me to proceed with these assumptions?"

  4. User: "Yes, proceed."

  5. 🔧 calculate_material_quantities()
     🔧 calculate_pricing()
     🔧 generate_detailed_quote()

  6. 💬 Agent: "Quote complete! Total: $18,750

     Note: This is based on typical system sizing. I recommend
     getting actual field measurements for a firm quote.
     Would you like me to generate a measurement worksheet?"
```

### Example 3: Multi-PDF Complex Project

```
User uploads:
  - specs_mechanical.pdf (50 pages)
  - specs_architectural.pdf (30 pages)
  - drawings_sheet_1-5.pdf
  - drawings_sheet_6-12.pdf

User: "Create a comprehensive estimate for this hospital project."

Agent workflow:
  1. 🔧 Parallel extraction:
     - extract_specifications(specs_mechanical.pdf)
     - extract_project_info(specs_architectural.pdf)
     - extract_measurements(drawings_1-5)
     - extract_measurements(drawings_6-12)

  2. 🔧 cross_reference_data(all_specs, all_measurements, all_drawings)
     → Identifies overlaps and conflicts

  3. 💬 Agent: "I found specifications in 2 documents and measurements
     across 12 drawing sheets. I've identified:

     ✅ 143 measurement items
     ✅ 28 unique specifications
     ⚠️  3 potential conflicts (e.g., Sheet M-3 shows 2" insulation
         but spec calls for 1.5")

     Would you like me to:
     A) Use the drawing notes (2") as authoritative
     B) Use the spec document (1.5") as authoritative
     C) Flag these items for your review"

  4. User: "Use drawings as authoritative."

  5. 🔧 validate_specifications() with override rules

  6. 🔧 identify_project_zones(measurements)
     → Categorizes by building zone: OR suites, patient rooms,
        mechanical rooms, service corridors

  7. 💬 Agent: "This project has 4 distinct zones with different
     requirements. Would you like:
     A) Single unified quote
     B) Separate quotes per zone (for phased construction)
     C) Both"

  8. User: "Separate quotes per zone."

  9. 🔧 generate_detailed_quote() × 4 zones
     🔧 generate_material_list() × 4 zones
     🔧 generate_executive_summary() (consolidated)

 10. 💬 Agent: "4 zone quotes generated:
     - OR Suites: $87,200
     - Patient Rooms: $124,500
     - Mechanical Rooms: $43,750
     - Service Corridors: $31,100
     Total Project: $286,550

     All quotes include 10% contingency. Export all documents?"
```

---

## Tool Implementation Details

### 1. Document Analysis Tools

#### `extract_project_info(pdf_path: str) → ProjectInfo`

```python
"""
Extracts high-level project information from cover sheets and title blocks.

Returns:
  - project_name: str
  - project_number: str
  - location: str
  - client: str
  - architect: str
  - engineer: str
  - project_type: str (commercial, industrial, healthcare, etc.)
  - total_square_footage: Optional[float]
  - system_description: str
"""
```

#### `extract_specifications(pdf_path: str, pages: Optional[List[int]]) → List[InsulationSpec]`

```python
"""
Extracts insulation specifications with Claude vision analysis.

Uses:
  - Existing SpecificationExtractor class
  - Claude 3.5 Sonnet vision for PDF analysis
  - Regex patterns for spec detection
  - Contextual understanding of spec language

Returns structured InsulationSpec objects with confidence scores.
"""
```

#### `extract_measurements(pdf_path: str, scale: Optional[str]) → List[MeasurementItem]`

```python
"""
Extracts measurements from architectural/mechanical drawings.

Methods:
  1. Claude vision analysis of drawing sheets
  2. Automatic scale detection
  3. Line/dimension extraction
  4. Schedule table parsing
  5. Legend/symbol interpretation

Returns MeasurementItem objects with location references.
"""
```

### 2. Validation & Enrichment Tools

#### `validate_specifications(specs: List[InsulationSpec]) → ValidationReport`

```python
"""
Validates specifications against industry standards and best practices.

Checks:
  - Material/thickness compatibility
  - Climate-appropriate specifications
  - Code compliance (energy codes, fire ratings)
  - Indoor vs outdoor requirements
  - Missing critical details (facing, jacketing)

Returns ValidationReport with warnings and recommendations.
"""
```

#### `cross_reference_data(specs, measurements, drawings) → CrossReferenceReport`

```python
"""
Intelligently cross-references all project data for consistency.

Validates:
  - Every measurement has a matching specification
  - Specifications cover all system types found
  - Drawing notes match spec requirements
  - Special requirements are consistently applied
  - Zone/area assignments are logical

Returns detailed report with conflicts flagged.
"""
```

#### `suggest_missing_specs(project_type: str, measurements: List[MeasurementItem]) → List[InsulationSpec]`

```python
"""
Proactively suggests missing specifications based on project context.

Logic:
  - Analyzes measurement items found
  - Identifies system types without specs
  - Recommends typical specs for project type
  - Considers climate/location if known
  - Flags critical omissions

Returns suggested specs with reasoning.
"""
```

### 3. Calculation & Pricing Tools

#### `calculate_material_quantities(specs, measurements) → MaterialQuantities`

```python
"""
Calculates precise material quantities using PricingEngine.

Process:
  1. Match measurements to specifications
  2. Calculate base insulation quantities (LF, SF)
  3. Add fitting allowances (elbows, tees)
  4. Calculate jacketing/facing areas
  5. Calculate accessories (mastic, bands)
  6. Apply waste factors

Returns detailed quantity breakdown by material category.
"""
```

#### `generate_alternatives(specs, measurements) → List[AlternativeQuote]`

```python
"""
Generates cost-effective alternative specifications.

Strategies:
  - Material substitutions (fiberglass ↔ elastomeric)
  - Thickness optimization (energy analysis)
  - Facing alternatives (FSK ↔ ASJ ↔ Aluminum)
  - Bundled vs itemized labor
  - Volume discount scenarios

Returns up to 3 alternative quotes with cost deltas and pros/cons.
"""
```

#### `optimize_costs(quote_data) → OptimizationReport`

```python
"""
Identifies cost optimization opportunities.

Analysis:
  - Material volume discounts
  - Labor efficiency improvements
  - Spec over-engineering
  - Value engineering options
  - Lifecycle cost analysis

Returns actionable recommendations with estimated savings.
"""
```

### 4. Quote Generation Tools

#### `generate_detailed_quote(project_data) → ProjectQuote`

```python
"""
Generates comprehensive, professional quote document.

Sections:
  - Executive summary
  - Project information
  - Scope of work
  - Specifications summary
  - Detailed material list
  - Labor breakdown
  - Pricing summary
  - Terms and conditions
  - Assumptions and exclusions

Returns ProjectQuote object with formatted text output.
"""
```

#### `generate_comparison_report(alternatives) → ComparisonReport`

```python
"""
Creates side-by-side comparison of quote alternatives.

Format:
  - Feature comparison matrix
  - Cost breakdown by category
  - Performance differences
  - Pros/cons analysis
  - Recommendation with reasoning

Returns formatted report (Markdown, PDF).
"""
```

### 5. Knowledge & Reasoning Tools

#### `get_industry_standards(system_type, location) → StandardsInfo`

```python
"""
Retrieves relevant industry standards and code requirements.

Sources:
  - ASHRAE standards (90.1, 90.2)
  - ASTM specifications
  - Local energy codes
  - SMACNA guidelines
  - Building code requirements

Returns applicable standards with references.
"""
```

#### `recommend_specifications(system_type, environment) → List[InsulationSpec]`

```python
"""
Recommends appropriate specifications based on best practices.

Considers:
  - System type (HVAC, plumbing, process)
  - Operating temperatures
  - Indoor vs outdoor exposure
  - Climate zone
  - Ambient conditions
  - Budget constraints

Returns ranked recommendations with explanations.
"""
```

---

## Technical Implementation

### Stack

```python
# Core Dependencies
anthropic               # Claude API and Agents SDK
pydantic               # Data validation and tool schemas
streamlit              # UI framework
langchain-anthropic    # Optional: LangChain integration
python-dotenv          # Configuration management

# Existing Dependencies (leverage)
pdfplumber             # PDF text extraction
pdf2image              # PDF to image conversion
opencv-python          # Computer vision for measurements
pandas                 # Data manipulation
openpyxl              # Excel support
```

### Agent Tool Definition Example

```python
from anthropic import Anthropic
from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractSpecificationsTool(BaseModel):
    """Tool for extracting insulation specifications from PDF documents."""

    name: str = "extract_specifications"
    description: str = """
    Extracts structured insulation specifications from PDF specification documents.
    Returns a list of specification items with system type, material, thickness,
    facing, and special requirements.
    """

    class InputSchema(BaseModel):
        pdf_path: str = Field(description="Path to the PDF specification document")
        pages: Optional[List[int]] = Field(
            default=None,
            description="Specific page numbers to analyze (optional, analyzes all if not specified)"
        )

    class OutputSchema(BaseModel):
        specifications: List[dict]
        confidence_scores: List[float]
        warnings: List[str]
        page_references: dict

def extract_specifications_handler(pdf_path: str, pages: Optional[List[int]] = None):
    """
    Handler function that implements the tool logic.
    """
    # Implementation using existing SpecificationExtractor
    # Enhanced with Claude vision analysis
    extractor = SpecificationExtractor()

    # Convert PDF to images for Claude vision
    if pages:
        images = pdf_to_images(pdf_path, pages)
    else:
        images = pdf_to_images(pdf_path)

    # Use Claude to analyze each page
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    specifications = []
    for page_num, image in enumerate(images):
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_to_base64(image)
                        }
                    },
                    {
                        "type": "text",
                        "text": """
                        Analyze this specification page for HVAC insulation requirements.
                        Extract all specifications including:
                        - System type (duct, pipe, equipment)
                        - Size ranges
                        - Material (fiberglass, elastomeric, etc.)
                        - Thickness
                        - Facing type
                        - Special requirements (mastic, jacketing, etc.)
                        - Location (indoor/outdoor/exposed)

                        Return as structured JSON.
                        """
                    }
                ]
            }]
        )

        # Parse Claude's response
        spec_data = parse_claude_response(response)
        specifications.extend(spec_data)

    # Validate and enrich with existing patterns
    validated_specs = extractor.validate_and_enrich(specifications)

    return {
        "specifications": validated_specs,
        "confidence_scores": [s.get("confidence", 0.9) for s in validated_specs],
        "warnings": generate_warnings(validated_specs),
        "page_references": create_page_map(validated_specs, pages)
    }
```

### Agent Loop Implementation

```python
from anthropic import Anthropic
from typing import Dict, List, Callable
import json

class InsulationEstimationAgent:
    """
    Main agent orchestrator for insulation estimation workflow.
    """

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.tools = self._register_tools()
        self.conversation_history = []

    def _register_tools(self) -> Dict[str, Callable]:
        """Register all available tools."""
        return {
            "extract_project_info": extract_project_info_handler,
            "extract_specifications": extract_specifications_handler,
            "extract_measurements": extract_measurements_handler,
            "validate_specifications": validate_specifications_handler,
            "cross_reference_data": cross_reference_data_handler,
            "calculate_material_quantities": calculate_quantities_handler,
            "calculate_pricing": calculate_pricing_handler,
            "generate_alternatives": generate_alternatives_handler,
            "generate_detailed_quote": generate_quote_handler,
            "export_documents": export_documents_handler,
        }

    def run(self, user_message: str, context: dict = None) -> str:
        """
        Main agent loop with tool use.
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Agent system prompt
        system_prompt = """
        You are an expert HVAC insulation estimator with access to specialized tools.
        Your goal is to help users create accurate, professional insulation estimates.

        Workflow:
        1. Understand the user's request
        2. Determine what information you need
        3. Use tools to extract/analyze/calculate data
        4. Validate and cross-reference information
        5. Ask clarifying questions when needed
        6. Generate comprehensive quotes
        7. Provide alternatives and recommendations

        Always be professional, thorough, and proactive in identifying issues.
        """

        while True:
            # Call Claude with tool use
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_prompt,
                tools=self._format_tools_for_claude(),
                messages=self.conversation_history
            )

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Agent is done, return final message
                assistant_message = next(
                    (block.text for block in response.content if hasattr(block, "text")),
                    ""
                )
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })
                return assistant_message

            elif response.stop_reason == "tool_use":
                # Agent wants to use tools
                assistant_message_content = []
                tool_results = []

                for block in response.content:
                    if hasattr(block, "text"):
                        assistant_message_content.append(block)
                    elif block.type == "tool_use":
                        # Execute the tool
                        tool_name = block.name
                        tool_input = block.input

                        print(f"🔧 Agent using tool: {tool_name}")
                        print(f"   Input: {json.dumps(tool_input, indent=2)}")

                        try:
                            # Call the tool handler
                            tool_handler = self.tools[tool_name]
                            result = tool_handler(**tool_input)

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result)
                            })

                            print(f"   ✅ Tool succeeded")

                        except Exception as e:
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps({"error": str(e)}),
                                "is_error": True
                            })

                            print(f"   ❌ Tool failed: {e}")

                # Add assistant's message with tool use
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Add tool results
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })

                # Continue the loop - Claude will process tool results
                continue

    def _format_tools_for_claude(self) -> List[dict]:
        """Format tools for Claude API."""
        return [
            {
                "name": "extract_project_info",
                "description": "Extracts project information from PDF cover sheets and title blocks",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string", "description": "Path to PDF file"}
                    },
                    "required": ["pdf_path"]
                }
            },
            {
                "name": "extract_specifications",
                "description": "Extracts insulation specifications from specification documents",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string", "description": "Path to PDF file"},
                        "pages": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Optional specific pages to analyze"
                        }
                    },
                    "required": ["pdf_path"]
                }
            },
            # ... more tools ...
        ]
```

---

## Integration with Existing System

### Streamlit UI Integration

```python
# enhanced_estimation_app.py
import streamlit as st
from claude_estimation_agent import InsulationEstimationAgent

def main():
    st.title("🤖 AI-Powered Insulation Estimator")
    st.caption("Powered by Claude Agents SDK")

    # Initialize agent
    if "agent" not in st.session_state:
        st.session_state.agent = InsulationEstimationAgent(
            api_key=st.secrets["ANTHROPIC_API_KEY"]
        )

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # File upload area
    with st.sidebar:
        st.header("📁 Upload Documents")

        spec_pdf = st.file_uploader("Specification PDF", type=["pdf"])
        drawing_pdf = st.file_uploader("Drawing PDF", type=["pdf"])
        pricebook = st.file_uploader("Price Book", type=["json", "csv", "xlsx"])

        if spec_pdf:
            # Save to temp file
            spec_path = save_temp_file(spec_pdf)
            st.session_state.spec_pdf_path = spec_path
            st.success(f"✅ Uploaded: {spec_pdf.name}")

        if drawing_pdf:
            drawing_path = save_temp_file(drawing_pdf)
            st.session_state.drawing_pdf_path = drawing_path
            st.success(f"✅ Uploaded: {drawing_pdf.name}")

    # Chat input
    if prompt := st.chat_input("Ask me anything about your estimate..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.write(prompt)

        # Build context from uploaded files
        context = {
            "spec_pdf": st.session_state.get("spec_pdf_path"),
            "drawing_pdf": st.session_state.get("drawing_pdf_path"),
        }

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.agent.run(prompt, context)
                st.write(response)

        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Quick action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Analyze Specifications"):
            if st.session_state.get("spec_pdf_path"):
                prompt = f"Analyze the specifications in {st.session_state.spec_pdf_path}"
                # Trigger agent...

    with col2:
        if st.button("📐 Extract Measurements"):
            if st.session_state.get("drawing_pdf_path"):
                prompt = f"Extract measurements from {st.session_state.drawing_pdf_path}"
                # Trigger agent...

    with col3:
        if st.button("💰 Generate Quote"):
            prompt = "Generate a complete quote with all available data"
            # Trigger agent...

if __name__ == "__main__":
    main()
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DEPLOYMENT OPTIONS                       │
└─────────────────────────────────────────────────────────────┘

Option 1: Streamlit Cloud
  • Host Streamlit app on Streamlit Cloud
  • Store API keys in Streamlit secrets
  • Free tier available, easy deployment
  • Best for: Internal tools, demos, MVP

Option 2: Docker Container
  • Containerize app with Docker
  • Deploy to any cloud (AWS, GCP, Azure)
  • Scalable with Kubernetes
  • Best for: Production, enterprise

Option 3: API Service
  • FastAPI backend with agent endpoints
  • React/Next.js frontend
  • Separate scaling of frontend/backend
  • Best for: Web applications, integrations

Option 4: CLI Tool
  • Command-line interface using Click/Typer
  • Local execution, no server needed
  • Best for: Power users, scripting, automation
```

---

## Performance & Cost Optimization

### Caching Strategy

```python
from functools import lru_cache
import hashlib

def cache_pdf_analysis(pdf_path: str):
    """Cache PDF analysis results to avoid re-processing."""
    pdf_hash = hash_file(pdf_path)
    cache_key = f"analysis_{pdf_hash}"

    if cached := get_from_cache(cache_key):
        return cached

    # Perform analysis
    result = analyze_pdf(pdf_path)

    # Cache for 24 hours
    save_to_cache(cache_key, result, ttl=86400)
    return result
```

### Token Usage Optimization

```python
# Use Claude Haiku for simple extraction tasks
# Use Claude Sonnet for complex reasoning
# Use caching for repeated document access

def smart_model_selection(task_complexity: str):
    if task_complexity == "simple":
        return "claude-3-haiku-20240307"  # Faster, cheaper
    elif task_complexity == "complex":
        return "claude-3-5-sonnet-20241022"  # Best reasoning
    else:
        return "claude-3-5-sonnet-20241022"
```

---

## Testing Strategy

```python
# tests/test_agent_tools.py
import pytest
from claude_estimation_agent import InsulationEstimationAgent

def test_extract_specifications():
    """Test specification extraction tool."""
    result = extract_specifications_handler(
        pdf_path="tests/fixtures/sample_spec.pdf"
    )

    assert len(result["specifications"]) > 0
    assert all(s["system_type"] in ["duct", "pipe", "equipment"]
               for s in result["specifications"])

def test_agent_conversation_flow():
    """Test multi-turn agent conversation."""
    agent = InsulationEstimationAgent(api_key=TEST_API_KEY)

    # User uploads PDF and asks for analysis
    response1 = agent.run("Analyze this spec PDF: tests/fixtures/sample_spec.pdf")
    assert "specifications" in response1.lower()

    # User asks follow-up question
    response2 = agent.run("What's the total estimated cost?")
    assert "$" in response2 or "cost" in response2.lower()

def test_cross_reference_validation():
    """Test data validation across specs and measurements."""
    specs = [...]  # Sample specs
    measurements = [...]  # Sample measurements

    report = cross_reference_data_handler(specs, measurements, None)

    assert report["validation_status"] in ["pass", "warning", "error"]
    assert "conflicts" in report
```

---

## Security & Privacy

```python
# Security best practices:

1. API Key Management
   - Store in environment variables or secrets manager
   - Never commit API keys to git
   - Rotate keys regularly

2. File Upload Validation
   - Validate file types (PDF only)
   - Scan for malware
   - Limit file sizes (< 50MB)
   - Use temporary storage with auto-cleanup

3. Data Privacy
   - Don't log sensitive project data
   - Provide option to disable cloud processing
   - Support on-premise deployment
   - Comply with data retention policies

4. Rate Limiting
   - Implement per-user rate limits
   - Prevent abuse of API endpoints
   - Monitor usage and costs
```

---

## Roadmap

### Phase 1: Foundation (Weeks 1-2)
- ✅ Architecture design
- ⬜ Core tool implementation (6 essential tools)
- ⬜ Basic agent loop
- ⬜ Streamlit integration
- ⬜ Testing framework

### Phase 2: Enhancement (Weeks 3-4)
- ⬜ Advanced validation tools
- ⬜ Alternative quote generation
- ⬜ Multi-PDF orchestration
- ⬜ Conversational interface
- ⬜ Export capabilities

### Phase 3: Intelligence (Weeks 5-6)
- ⬜ Industry standards database
- ⬜ Cost optimization engine
- ⬜ Historical data analysis
- ⬜ Recommendation system
- ⬜ Code compliance checking

### Phase 4: Production (Weeks 7-8)
- ⬜ Performance optimization
- ⬜ Comprehensive testing
- ⬜ Documentation
- ⬜ Deployment automation
- ⬜ User training materials

---

## Success Metrics

```
Accuracy:
  • Specification extraction: >95% accuracy
  • Measurement extraction: >90% accuracy
  • Pricing calculations: 100% accuracy (deterministic)

Efficiency:
  • Time to quote: <5 minutes (vs 2-4 hours manual)
  • User interactions: <10 questions per project
  • Re-work rate: <5%

User Satisfaction:
  • Ease of use: >4.5/5
  • Quote quality: >4.5/5
  • Would recommend: >90%

Cost:
  • API costs: <$2 per quote
  • ROI: 10x (time savings vs cost)
```

---

## Conclusion

The Claude Agents SDK integration transforms the Professional Insulation Estimation System from a **manual, sequential workflow** into an **intelligent, autonomous assistant** that:

1. **Understands** complex project documents with vision analysis
2. **Validates** data for consistency and completeness
3. **Recommends** cost-effective alternatives
4. **Generates** professional quotes automatically
5. **Learns** from user feedback and corrections

This architecture provides the foundation for the **next generation** of construction estimation software, powered by AI that truly understands the domain.

---

**Next Steps:**
1. Review and approve architecture
2. Begin Phase 1 implementation
3. Set up development environment
4. Create first prototype with core tools
