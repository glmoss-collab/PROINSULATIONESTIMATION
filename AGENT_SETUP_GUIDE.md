# Claude Agents SDK Setup Guide

## Overview

This guide will help you set up and use the **Claude Agents SDK** features for intelligent, conversational insulation estimation.

## What's New

The Claude Agents SDK integration adds:

- **🤖 Conversational Interface**: Chat with an AI agent to create estimates
- **🔧 Intelligent Tools**: Automated document analysis, validation, and pricing
- **📊 Multi-Step Workflows**: Agent orchestrates complex estimation workflows
- **✅ Quality Control**: Automatic validation and cross-referencing
- **💡 Recommendations**: Cost-saving alternatives and optimization suggestions
- **📱 Multiple Interfaces**: CLI, Streamlit app, or programmatic API

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Key new dependencies:
- `anthropic>=0.40.0` - Claude API and Agents SDK
- `python-dotenv>=1.0.0` - Environment configuration
- `pdf2image>=1.16.0` - PDF to image conversion

### 2. Set Up API Key

You'll need an Anthropic API key. Get one at: https://console.anthropic.com/

#### Option A: Environment Variable

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or add to `.env` file:
```
ANTHROPIC_API_KEY=your-api-key-here
```

#### Option B: Streamlit Secrets

For Streamlit deployment, add to `.streamlit/secrets.toml`:
```toml
ANTHROPIC_API_KEY = "your-api-key-here"
```

### 3. Verify Installation

Test your setup:

```bash
python -c "from claude_estimation_agent import create_agent; agent = create_agent(); print('✅ Agent initialized successfully')"
```

---

## Quick Start

### Option 1: Streamlit App (Recommended)

Launch the conversational estimation app:

```bash
streamlit run agent_estimation_app.py
```

Features:
- Upload PDFs (specifications, drawings)
- Chat with AI agent
- Real-time estimation
- Download quotes and material lists

### Option 2: Command-Line Interface

Interactive CLI for terminal users:

```bash
python claude_estimation_agent.py
```

Commands:
- Type your questions naturally
- `upload <path>` - Add a file
- `status` - View session summary
- `export <path>` - Save session data
- `reset` - Start over
- `quit` - Exit

### Option 3: Python API

Use programmatically in your code:

```python
from claude_estimation_agent import create_agent

# Initialize agent
agent = create_agent()

# Conversational workflow
response = agent.run("Analyze this spec PDF: /path/to/spec.pdf")
print(response)

# Follow-up questions
response = agent.run("What's the total cost?")
print(response)

# Get session data
session_data = agent.get_session_data()
print(f"Total: ${session_data['pricing']['total']:,.2f}")
```

---

## Usage Examples

### Example 1: PDF Analysis

**User**: "Analyze this specification PDF and create a quote."

**Agent**:
1. 🔧 Extracts project information
2. 🔧 Analyzes specifications (materials, thicknesses, requirements)
3. 🔧 Validates against industry standards
4. 💬 Asks: "I found outdoor ductwork specs without weather protection. Add aluminum jacketing?"
5. 🔧 Extracts measurements if drawing included
6. 🔧 Calculates pricing
7. 🔧 Generates professional quote

---

### Example 2: Conversational Estimation (No PDFs)

**User**: "I need a quote for insulating a 50-ton rooftop HVAC system in Phoenix."

**Agent**:
1. 💬 Asks clarifying questions:
   - Location/climate zone?
   - Outdoor exposure?
   - Measurements available?

2. 🔧 Recommends specifications based on climate
3. 🔧 Suggests typical measurements for 50-ton system
4. 💬 Presents assumptions for approval
5. 🔧 Calculates pricing
6. 🔧 Generates quote

**Result**: Complete estimate without uploading any documents!

---

### Example 3: Multi-PDF Complex Project

**User**: Uploads 4 PDFs (specs + drawings) and says "Create comprehensive estimate"

**Agent**:
1. 🔧 Analyzes all documents in parallel
2. 🔧 Cross-references specifications across files
3. 🔧 Extracts measurements from 12 drawing sheets
4. ⚠️  Identifies 3 conflicts between drawings and specs
5. 💬 Asks user which to use as authoritative
6. 🔧 Calculates pricing with resolution
7. 🔧 Generates zone-based quotes
8. 📥 Exports all documents

---

## Agent Tools Reference

The agent has access to these specialized tools:

### Document Analysis
- **extract_project_info**: Cover sheet and title block parsing
- **extract_specifications**: Insulation spec detection and parsing
- **extract_measurements**: Drawing takeoff and measurement extraction

### Validation & Quality Control
- **validate_specifications**: Industry standards compliance check
- **cross_reference_data**: Consistency validation across all data
- **suggest_missing_specs**: Proactive gap identification

### Calculation
- **calculate_pricing**: Materials, labor, markup, contingency
- **generate_alternatives**: Cost-effective alternative options
- **optimize_costs**: Cost optimization recommendations

### Output Generation
- **generate_quote**: Professional quote document
- **export_documents**: Multiple format exports

---

## Advanced Usage

### Custom Workflows

Create custom estimation workflows:

```python
from claude_estimation_agent import quick_estimate

# One-line complete estimate
result = quick_estimate(
    spec_pdf="project_specs.pdf",
    drawing_pdf="mechanical_drawings.pdf",
    pricebook="distributor_prices.json"
)

print(result["response"])
print(f"Quote Ready: {result['quote_ready']}")
```

### Session Management

Work with session data:

```python
agent = create_agent()

# Run workflow
agent.run("Analyze spec.pdf and drawing.pdf")

# Get session data
data = agent.get_session_data()

# Access specific data
specifications = data["specifications"]
measurements = data["measurements"]
pricing = data["pricing"]

# Export session
agent.export_session("my_project_session.json")

# Reset for new project
agent.reset_session()
```

### Error Handling

```python
try:
    response = agent.run("Create estimate for project.pdf")
    print(response)
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Architecture

```
User Interface (CLI / Streamlit / API)
          ↓
Claude Estimation Agent (Orchestrator)
          ↓
Claude 3.5 Sonnet with Tool Use
          ↓
Agent Tools (7 specialized tools)
          ↓
Core Estimation Engine (Existing modules)
          ↓
Data Layer (PDFs, Pricebooks, etc.)
```

**Key Benefits**:
- Agent decides which tools to use
- Multi-step reasoning and validation
- Conversational clarification
- Parallel processing where possible
- Automatic error recovery

---

## Best Practices

### 1. Document Organization

Structure your project documents:
```
project_name/
  ├── specifications.pdf    # Mechanical specs
  ├── drawings_sheet_1-5.pdf
  ├── drawings_sheet_6-10.pdf
  └── pricebook.json        # Optional custom pricing
```

### 2. Effective Prompts

**Good prompts**:
- "Analyze specs.pdf and identify any missing outdoor requirements"
- "Compare cost of R-6 vs R-8 ductwork for this project"
- "Generate quote with 20% markup and 8% contingency"

**Less effective**:
- "Do stuff with the file" (too vague)
- Single-word commands (provide context)

### 3. Iterative Refinement

Work iteratively with the agent:
1. Initial analysis
2. Review findings
3. Ask follow-up questions
4. Refine specifications
5. Generate final quote

### 4. Validation

Always review:
- Extracted specifications (accuracy)
- Measurements (completeness)
- Cross-reference conflicts (resolution)
- Pricing calculations (reasonableness)

---

## Troubleshooting

### API Key Issues

```
Error: ANTHROPIC_API_KEY environment variable not set
```

**Solution**: Set environment variable or add to `.env` file

### PDF Processing Errors

```
Error: Failed to convert PDF to images
```

**Solution**: Install system dependencies for pdf2image:
- **Ubuntu/Debian**: `sudo apt-get install poppler-utils`
- **macOS**: `brew install poppler`
- **Windows**: Download from http://blog.alivate.com.au/poppler-windows/

### Model Access Errors

```
Error: The model: claude-3-5-sonnet-20241022 is not available
```

**Solution**: Check API key has access to Claude 3.5 Sonnet. Contact Anthropic support if needed.

### Memory Issues

```
Error: Out of memory processing large PDF
```

**Solution**:
- Process large PDFs in batches (specify page ranges)
- Use page limits: `extract_specifications(pdf, pages=[1, 2, 3])`
- Split large projects into separate sessions

---

## Performance & Cost

### API Usage

Typical costs per estimate:
- Simple project (5-10 pages): **$0.20 - $0.50**
- Medium project (10-30 pages): **$0.50 - $1.50**
- Complex project (30+ pages): **$1.50 - $3.00**

### Optimization Tips

1. **Use caching**: Agent reuses extracted data
2. **Batch operations**: Upload all files at once
3. **Specific queries**: Ask targeted questions
4. **Page limits**: Process only relevant pages

### Response Times

- Simple extraction: 5-15 seconds
- Complex analysis: 15-45 seconds
- Full workflow: 45-90 seconds
- Multi-PDF projects: 1-3 minutes

---

## Integration with Existing Apps

### Migrate from estimation_app.py

Old workflow:
```python
# estimation_app.py (manual steps)
1. Upload PDF
2. Click "Analyze with Claude"
3. Review results
4. Click "Extract measurements"
5. Click "Calculate pricing"
6. Click "Generate quote"
```

New workflow:
```python
# agent_estimation_app.py (conversational)
1. Upload PDFs
2. Say "Create a complete estimate"
3. Agent does all steps automatically
4. Review and download
```

### Keep using existing apps

All existing apps still work:
- `streamlit_app.py` - Full-featured SaaS app
- `estimation_app.py` - Claude-powered Streamlit app
- `hvac_insulation_estimator.py` - Core Python library

New agent-powered app: **`agent_estimation_app.py`**

---

## Examples & Demos

### Demo 1: Quick Estimate

```bash
python demo_agent.py --spec example_spec.pdf --drawing example_drawing.pdf
```

### Demo 2: Conversational

```bash
python claude_estimation_agent.py

You: I need to insulate ductwork for a 100-ton chiller plant
Agent: [Asks questions, provides estimate]
```

### Demo 3: API Integration

```python
from claude_estimation_agent import create_agent

agent = create_agent()

# Natural language workflow
agent.run("Analyze spec.pdf")
agent.run("Extract measurements from drawing.pdf")
agent.run("Calculate with 15% markup")
agent.run("Generate quote")

# Export results
agent.export_session("project_estimate.json")
```

---

## What's Next?

### Phase 1 ✅ (Current)
- Core agent tools
- Conversational interface
- Streamlit app integration
- CLI interface

### Phase 2 🚧 (Coming Soon)
- Historical data analysis
- ML-powered recommendations
- Multi-project batch processing
- Advanced cost optimization

### Phase 3 📋 (Planned)
- Web API service
- Mobile app integration
- Real-time collaboration
- Database integration

---

## Support

### Documentation
- **Architecture**: See `CLAUDE_AGENTS_ARCHITECTURE.md`
- **Original Setup**: See `STREAMLIT_README.md`
- **API Docs**: See inline docstrings in `claude_agent_tools.py`

### Getting Help
1. Check this guide first
2. Review architecture documentation
3. Check code comments and docstrings
4. Review example prompts in Streamlit app
5. Submit GitHub issue with:
   - What you're trying to do
   - What error you're seeing
   - Relevant code/prompts

---

## License & Credits

Built on top of:
- **Anthropic Claude 3.5 Sonnet** - AI agent and tool use
- **Streamlit** - Web interface
- **pdfplumber & pdf2image** - PDF processing
- **Existing estimation engine** - Core calculation logic

---

**Ready to get started? Launch the app:**

```bash
streamlit run agent_estimation_app.py
```

Or try the CLI:

```bash
python claude_estimation_agent.py
```

Happy estimating! 🚀
