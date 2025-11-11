<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Professional Insulation Estimation System

**AI-powered HVAC insulation estimation with multiple interfaces and intelligent agents.**

This system provides comprehensive tools for creating professional insulation estimates with:
- 🤖 **Claude Agents SDK** - Conversational AI estimation
- 📊 **Streamlit Apps** - Multiple web interfaces
- 🎨 **React/TypeScript** - Modern web UI
- 🐍 **Python Library** - Programmatic API
- 📱 **CLI Tools** - Command-line interfaces

---

## 🚀 Quick Start Options

### Option 1: Claude Agent (Recommended - NEW!)

**Conversational AI estimation with intelligent multi-step workflows**

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
streamlit run agent_estimation_app.py
```

Features:
- Chat naturally to create estimates
- Automatic document analysis
- Intelligent validation and recommendations
- Cost-saving alternatives
- Professional quote generation

[📖 Agent Setup Guide](AGENT_SETUP_GUIDE.md) | [🏗️ Architecture](CLAUDE_AGENTS_ARCHITECTURE.md)

---

### Option 2: Full-Featured Streamlit App

**Complete SaaS-style estimation application**

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

### Option 3: Google AI Studio App

**React/TypeScript web application with Gemini AI**

View your app in AI Studio: https://ai.studio/apps/drive/15RabTSs7Ap3rBj_xjSgY0L7x0ibyC596

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

---

## 🎯 What's New: Claude Agents SDK Integration

The latest version integrates **Anthropic's Claude Agents SDK** for intelligent, conversational estimation:

### Key Features

1. **🤖 Conversational Interface**
   - Chat naturally: "I need a quote for a 50-ton rooftop unit"
   - Agent asks clarifying questions
   - Multi-turn conversations with context

2. **🔧 Intelligent Tools**
   - Automatic document analysis (PDFs)
   - Specification extraction with validation
   - Measurement takeoff from drawings
   - Cross-referencing and quality control

3. **💡 Smart Recommendations**
   - Cost-saving alternatives
   - Specification optimization
   - Industry best practices
   - Code compliance checks

4. **📊 Multi-Step Workflows**
   - Orchestrates complex estimation tasks
   - Parallel processing where possible
   - Error recovery and retry logic
   - Automatic validation

### Example Usage

```python
from claude_estimation_agent import create_agent

agent = create_agent()

# Natural language workflow
response = agent.run("Analyze spec.pdf and create a quote")
print(response)

# Agent automatically:
# - Extracts project info
# - Analyzes specifications
# - Validates requirements
# - Calculates pricing
# - Generates professional quote
```

### Try It Now

**Streamlit App:**
```bash
streamlit run agent_estimation_app.py
```

**CLI Interface:**
```bash
python claude_estimation_agent.py
```

**Demo Script:**
```bash
python demo_agent.py --demo 1
```

[📖 Full Setup Guide](AGENT_SETUP_GUIDE.md) | [🏗️ Architecture Details](CLAUDE_AGENTS_ARCHITECTURE.md)

---

## 📚 Documentation

### 🚀 Getting Started (New Users Start Here!)

1. **[Quick Start Checklist](QUICK_START_CHECKLIST.md)** ⭐ - 30-minute setup guide (print & follow!)
2. **[User Manual](USER_MANUAL.md)** ⭐ - Complete beginner-friendly guide
3. **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Hosting options (Cloud, Docker, etc.)

### 🔧 Technical Documentation

- **[Agent Setup Guide](AGENT_SETUP_GUIDE.md)** - Getting started with Claude Agents SDK
- **[Agent Architecture](CLAUDE_AGENTS_ARCHITECTURE.md)** - System design and workflows
- **[Production Enhancements](PRODUCTION_ENHANCEMENTS.md)** - Performance & cost optimizations
- **[Streamlit App Guide](STREAMLIT_README.md)** - Full-featured app documentation
- **[AI Setup Guide](AI_SETUP_GUIDE.md)** - Google Gemini integration

---

## 🛠️ System Components

### Core Modules

| Module | Description | Interface |
|--------|-------------|-----------|
| `claude_estimation_agent.py` | Main agent orchestrator | CLI, API |
| `claude_agent_tools.py` | Agent tool implementations | Library |
| `agent_estimation_app.py` | Agent-powered Streamlit UI | Web |
| `hvac_insulation_estimator.py` | Core estimation engine | Library |
| `streamlit_app.py` | Full-featured SaaS app | Web |
| `estimation_app.py` | Claude-powered app (simple) | Web |
| `gemini_pdf_extractor.py` | Google Gemini PDF processor | Library |

### Available Interfaces

```
┌─────────────────────────────────────────┐
│         User Interfaces                 │
├─────────────────────────────────────────┤
│  • agent_estimation_app.py (Streamlit)  │  ← NEW! Conversational
│  • streamlit_app.py (Streamlit)         │  ← Full-featured SaaS
│  • App.tsx (React/TypeScript)           │  ← Web UI
│  • claude_estimation_agent.py (CLI)     │  ← Terminal
│  • Python API (programmatic)            │  ← Code integration
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│      Estimation Engine                  │
├─────────────────────────────────────────┤
│  • Specification extraction             │
│  • Measurement analysis                 │
│  • Pricing calculations                 │
│  • Quote generation                     │
└─────────────────────────────────────────┘
```

---

## 🚀 Quick Commands

```bash
# Install dependencies
pip install -r requirements.txt
npm install  # For React app

# Set up API keys
export ANTHROPIC_API_KEY="your-claude-key"
export GEMINI_API_KEY="your-gemini-key"

# Run applications
streamlit run agent_estimation_app.py     # Agent-powered (recommended)
streamlit run streamlit_app.py            # Full-featured
python claude_estimation_agent.py         # CLI
npm run dev                               # React app

# Run demos
python demo_agent.py --demo 1            # Conversational demo
python demo_agent.py --spec spec.pdf     # PDF analysis demo
```

---

## 📖 Process PDF Specifications

Multiple tools available for PDF processing:

### Option 1: Agent-Powered (Recommended)
```bash
python claude_estimation_agent.py
> Analyze spec.pdf and extract all requirements
```

### Option 2: Simple Helper Script
```bash
pip install pdfplumber
python process_my_pdfs.py /path/to/specifications.pdf
```

The script saves extracted text and highlights insulation-related keywords.

---

## 🎓 Learning Resources

### For New Users
1. Start with [Agent Setup Guide](AGENT_SETUP_GUIDE.md)
2. Try `python demo_agent.py --demo 1`
3. Launch `streamlit run agent_estimation_app.py`
4. Explore example prompts in the app

### For Developers
1. Review [Architecture Document](CLAUDE_AGENTS_ARCHITECTURE.md)
2. Examine `claude_agent_tools.py` for tool implementations
3. Check `demo_agent.py` for API usage examples
4. Read inline documentation in source files

### For Power Users
1. Use CLI: `python claude_estimation_agent.py`
2. Integrate into your scripts (see Python API examples)
3. Customize agent tools for your workflow
4. Export session data for analysis

---

## 🤝 Contributing

This project combines multiple AI technologies:
- **Anthropic Claude** for conversational AI and agents
- **Google Gemini** for document understanding
- **Streamlit** for rapid UI development
- **React/TypeScript** for modern web UIs

Contributions welcome! Please maintain compatibility across all interfaces.

---

## 📄 License

See individual component licenses. Claude Agents SDK integration uses Anthropic's API terms of service.
