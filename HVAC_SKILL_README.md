# HVAC Insulation Estimation Skill

A comprehensive Agent SDK skill for estimating HVAC insulation projects using Claude AI.

## Overview

This skill provides intelligent tools for analyzing construction documents, extracting insulation specifications and measurements, validating against industry standards, and generating professional quotes for HVAC insulation projects.

## Features

- **Document Analysis**: Extract project information, specifications, and measurements from PDFs
- **AI-Powered Extraction**: Use Claude's vision and language capabilities to understand construction documents
- **Industry Standards**: Validate specifications against ASHRAE, SMACNA, and mechanical codes
- **Automatic Cross-Referencing**: Match specifications with measurements to identify gaps
- **Pricing Calculation**: Calculate material quantities and labor estimates
- **Quote Generation**: Generate professional, detailed project quotes
- **Conversational Interface**: Natural language interaction with the agent
- **Session Management**: Track data across multiple document analyses

## Installation

### Prerequisites

- Python 3.8 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Dependencies

```bash
pip install anthropic>=0.40.0 python-dotenv>=1.0.0 pdfplumber>=0.10.0 pdf2image>=1.16.0 pymupdf>=1.23.0 opencv-python-headless>=4.8.0 pandas>=2.0.0 numpy>=1.24.0 pydantic>=2.0.0
```

Or install all project requirements:

```bash
pip install -r requirements.txt
```

### Setup

1. Clone this repository or copy the skill files:
   - `hvac_insulation_skill.py` - Main skill implementation
   - `hvac_skill_example.py` - Usage examples
   - `claude_agent_tools.py` - Tool implementations (required)
   - `hvac_insulation_estimator.py` - Estimation engine (required)
   - `pydantic_models.py` - Data models (required)
   - `errors.py` - Error handling (required)

2. Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Or create a `.env` file:

```
ANTHROPIC_API_KEY=your-api-key-here
```

## Quick Start

### Basic Usage

```python
from hvac_insulation_skill import HVACInsulationSkill

# Initialize the skill
skill = HVACInsulationSkill(api_key="your-api-key")

# Ask the agent to analyze a document
result = skill.run(
    "Extract insulation specifications from /path/to/specs.pdf"
)

print(result['response'])
print(result['session_data'])
```

### Complete Estimation Workflow

```python
from hvac_insulation_skill import quick_estimate

# Perform complete estimation in one call
result = quick_estimate("/path/to/project.pdf")

print(result['response'])
print(result['session_data']['quote'])
```

### Direct Tool Access

```python
skill = HVACInsulationSkill(api_key="your-api-key")

# Call a specific tool directly
result = skill.call_tool_directly(
    "extract_specifications",
    pdf_path="/path/to/specs.pdf",
    pages=[15, 16, 17, 18, 19]
)

if result['success']:
    specs = result['data']['specifications']
    for spec in specs:
        print(f"{spec['system_type']}: {spec['thickness']}\" {spec['material']}")
```

## Available Tools

The skill provides 7 specialized tools:

### 1. extract_project_info

Extract project metadata from the cover sheet or first pages.

```python
result = skill.call_tool_directly(
    "extract_project_info",
    pdf_path="/path/to/specs.pdf"
)
```

**Extracts:**
- Project name
- Client/owner
- Location
- Architect
- Building type
- Square footage
- Project number

### 2. extract_specifications

Extract insulation specifications from specification documents.

```python
result = skill.call_tool_directly(
    "extract_specifications",
    pdf_path="/path/to/specs.pdf",
    pages=[15, 16, 17, 18, 19]  # Optional
)
```

**Extracts:**
- System types (ducts, pipes, equipment)
- Material types (fiberglass, elastomeric, etc.)
- Insulation thicknesses
- Facing requirements (FSK, ASJ, etc.)
- Special requirements
- Location specifications

### 3. extract_measurements

Extract measurements from mechanical drawings.

```python
result = skill.call_tool_directly(
    "extract_measurements",
    pdf_path="/path/to/drawings.pdf",
    scale="1/4\" = 1'"  # Optional
)
```

**Extracts:**
- Duct and pipe sizes
- Linear footage
- Locations and zones
- Elevation changes
- Fittings and accessories

### 4. validate_specifications

Validate specifications against industry standards.

```python
result = skill.call_tool_directly(
    "validate_specifications",
    specifications=[{
        "system_type": "supply_duct",
        "thickness": 2.0,
        "material": "fiberglass",
        "location": "outdoor"
    }]
)
```

**Validates:**
- Thickness requirements (ASHRAE)
- Material compatibility
- Outdoor/indoor requirements
- Code compliance
- Industry best practices

### 5. cross_reference_data

Cross-reference specifications with measurements.

```python
result = skill.call_tool_directly(
    "cross_reference_data",
    specifications=[...],
    measurements=[...]
)
```

**Identifies:**
- Gaps (measurements without specs)
- Conflicts (spec/measurement mismatches)
- Coverage analysis
- Recommendations

### 6. calculate_pricing

Calculate material quantities and pricing.

```python
result = skill.call_tool_directly(
    "calculate_pricing",
    specifications=[...],
    measurements=[...],
    pricing_data={...}  # Optional
)
```

**Calculates:**
- Material quantities (square feet, linear feet)
- Labor hours
- Material costs
- Labor costs
- Total project cost

### 7. generate_quote

Generate a professional project quote.

```python
result = skill.call_tool_directly(
    "generate_quote",
    project_info={...},
    specifications=[...],
    measurements=[...],
    pricing={...}
)
```

**Generates:**
- Quote number and date
- Project summary
- Itemized material list
- Labor breakdown
- Total pricing
- Terms and conditions

## Conversational Interface

The skill supports natural language conversations:

```python
skill = HVACInsulationSkill(api_key="your-api-key")

# Multi-turn conversation
skill.run("Extract specs from /path/to/specs.pdf")
skill.run("What are the most common insulation thicknesses?")
skill.run("Validate those specifications")
skill.run("Calculate pricing for the project")
```

The agent maintains context across turns and can:
- Answer questions about extracted data
- Provide recommendations
- Explain standards and requirements
- Guide you through the estimation process

## Session Management

### Get Session Data

```python
session_data = skill.get_session_data()
print(session_data['project_info'])
print(session_data['specifications'])
print(session_data['measurements'])
print(session_data['pricing'])
print(session_data['quote'])
```

### Export/Import Sessions

```python
# Export session to file
skill.export_session("/path/to/session.json")

# Import session from file
skill.import_session("/path/to/session.json")

# Reset session for new project
skill.reset_session()
```

## Advanced Usage

### Custom Model Selection

```python
skill = HVACInsulationSkill(
    api_key="your-api-key",
    model="claude-sonnet-4-5-20250929",  # Default
    max_tokens=8192
)
```

### Error Handling

```python
result = skill.run("Extract specs from /path/to/specs.pdf")

if result['success']:
    print(result['response'])
    print(result['session_data'])
else:
    print(f"Error: {result['error']}")
    print(f"Stop reason: {result['stop_reason']}")
```

### Monitoring Tool Calls

```python
result = skill.run("Complete estimation for project.pdf")

print(f"Tool calls made: {result['tool_calls']}")
print(f"Iterations: {result['iterations']}")
```

## Examples

See `hvac_skill_example.py` for comprehensive examples including:

1. Basic skill usage
2. Extracting project information
3. Direct tool calls
4. Complete estimation workflow
5. Specification validation
6. Session management
7. Convenience functions
8. Multi-turn conversations
9. Querying available tools
10. Error handling

Run examples:

```bash
python hvac_skill_example.py
```

## Architecture

The skill is built on:

- **Claude Agent SDK**: Anthropic's official SDK for building AI agents
- **Tool-based Architecture**: Each capability is a discrete tool that Claude can use
- **OpenAPI Schemas**: Tools are defined with structured input/output schemas
- **Pydantic Models**: Data validation and type safety
- **Existing Estimation Engine**: Leverages proven HVAC estimation algorithms

### Skill Components

```
hvac_insulation_skill.py
├── HVACInsulationSkill (main class)
│   ├── __init__() - Initialize client and tools
│   ├── run() - Main agent loop
│   ├── _execute_tools() - Execute tool calls
│   ├── _update_session_data() - Track extracted data
│   ├── call_tool_directly() - Programmatic tool access
│   ├── reset_session() - Clear session data
│   ├── get_session_data() - Retrieve current data
│   ├── export_session() - Save to file
│   └── import_session() - Load from file
└── Convenience Functions
    ├── quick_estimate() - All-in-one estimation
    ├── extract_specs_only() - Spec extraction only
    └── extract_measurements_only() - Measurement extraction only
```

## Best Practices

### 1. Document Quality

For best results:
- Use clear, high-resolution PDFs
- Ensure text is searchable (not scanned images)
- Provide mechanical drawings with visible labels
- Include specification sections 23 07 00 (HVAC Insulation)

### 2. Workflow Order

Recommended estimation sequence:
1. Extract project information
2. Extract specifications
3. Extract measurements
4. Validate specifications
5. Cross-reference specs and measurements
6. Calculate pricing
7. Generate quote

### 3. Session Management

- Reset session when starting a new project
- Export sessions for record-keeping
- Use descriptive filenames for session exports

### 4. Error Handling

- Always check `result['success']` before using data
- Handle PDF file paths carefully
- Validate API key is set correctly

### 5. Cost Optimization

- Use direct tool calls when you know exactly what you need
- Limit agent iterations for simple tasks
- Cache pricing data to avoid recalculation

## Troubleshooting

### API Key Issues

```
ValueError: API key required
```

**Solution**: Set the `ANTHROPIC_API_KEY` environment variable or pass it to the constructor.

### PDF Not Found

```
PDFNotFoundError: PDF file not found
```

**Solution**: Verify the PDF path is correct and the file exists.

### Tool Execution Errors

```
success: False, error: "Unknown tool: tool_name"
```

**Solution**: Check available tools with `skill.get_available_tools()`.

### Max Iterations Reached

```
stop_reason: "max_iterations"
```

**Solution**: The task is too complex. Break it into smaller steps or increase `max_iterations`.

## Integration Examples

### Streamlit App

```python
import streamlit as st
from hvac_insulation_skill import HVACInsulationSkill

skill = HVACInsulationSkill(api_key=st.secrets["ANTHROPIC_API_KEY"])

uploaded_file = st.file_uploader("Upload PDF")
if uploaded_file:
    # Save temporarily
    with open("/tmp/upload.pdf", "wb") as f:
        f.write(uploaded_file.read())

    # Process
    result = skill.run(f"Extract specifications from /tmp/upload.pdf")
    st.write(result['response'])
    st.json(result['session_data'])
```

### FastAPI Endpoint

```python
from fastapi import FastAPI, UploadFile
from hvac_insulation_skill import HVACInsulationSkill

app = FastAPI()
skill = HVACInsulationSkill()

@app.post("/estimate")
async def estimate(file: UploadFile):
    # Save file
    path = f"/tmp/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())

    # Process
    result = skill.run(f"Complete estimation for {path}")

    return {
        "success": result['success'],
        "quote": result['session_data'].get('quote'),
        "pricing": result['session_data'].get('pricing')
    }
```

### CLI Tool

```python
import argparse
from hvac_insulation_skill import quick_estimate

parser = argparse.ArgumentParser()
parser.add_argument("pdf_path", help="Path to project PDF")
args = parser.parse_args()

result = quick_estimate(args.pdf_path)
print(result['session_data']['quote'])
```

## Contributing

Contributions are welcome! Areas for improvement:

- Additional validation rules
- More material types
- Regional pricing databases
- Export formats (Excel, Word)
- Drawing recognition improvements

## License

This skill is part of the PROINSULATIONESTIMATION project.

## Support

For issues or questions:
- Check the examples in `hvac_skill_example.py`
- Review the architecture in `CLAUDE_AGENTS_ARCHITECTURE.md`
- See setup instructions in `AGENT_SETUP_GUIDE.md`

## Version History

- **1.0.0** (2025-11-12): Initial release
  - 7 core tools
  - Complete estimation workflow
  - Session management
  - Multi-turn conversations
  - Direct tool access

## Credits

Built with:
- [Anthropic Claude](https://www.anthropic.com/claude) - AI capabilities
- [Claude Agent SDK](https://github.com/anthropics/anthropic-sdk-python) - Agent framework
- PDFPlumber, PyMuPDF - PDF processing
- Pydantic - Data validation

---

**Ready to estimate HVAC insulation with AI?**

```python
from hvac_insulation_skill import HVACInsulationSkill

skill = HVACInsulationSkill(api_key="your-key")
result = skill.run("Help me estimate my HVAC insulation project")
print(result['response'])
```
