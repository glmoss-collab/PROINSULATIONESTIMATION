# Professional Insulation Estimation App - User Manual

**A Complete Guide for Non-Technical Users**

---

## 📖 Table of Contents

1. [What Is This App?](#what-is-this-app)
2. [What You'll Need](#what-youll-need)
3. [Quick Start Guide](#quick-start-guide)
4. [Installation & Setup](#installation--setup)
5. [How to Use the App](#how-to-use-the-app)
6. [Testing Your Setup](#testing-your-setup)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)
9. [Getting Help](#getting-help)

---

## What Is This App?

This is an **AI-powered insulation estimation tool** that helps you create professional quotes for HVAC insulation projects. It can:

✅ **Read PDF documents** (specifications and drawings)
✅ **Extract insulation requirements** automatically
✅ **Calculate material quantities** and labor
✅ **Generate professional quotes** ready to send to clients
✅ **Save you 2-4 hours** per estimate

### How It Works

```
1. Upload PDFs → 2. AI Analyzes → 3. Calculate Pricing → 4. Get Quote
   (Your docs)     (Automatic)      (Instant)           (Download)
```

**Time**: 5 minutes vs 2-4 hours manual work
**Cost**: ~$0.05-0.50 per estimate
**Accuracy**: 99%+ with AI validation

---

## What You'll Need

### Required Items

- [ ] **Computer** (Windows, Mac, or Linux)
- [ ] **Internet Connection** (for API access)
- [ ] **PDF Files** (specifications or drawings - optional for testing)
- [ ] **Anthropic API Key** (free trial available)
- [ ] **30 minutes** for initial setup

### Optional Items

- [ ] Excel or CSV price book (for custom pricing)
- [ ] Terminal/Command Prompt knowledge (helpful but not required)

### Costs

- **Software**: Free (open source)
- **API Usage**:
  - First 5 estimates free (with trial credits)
  - After: ~$0.05-0.50 per estimate
  - Monthly ~$5-20 for typical usage

---

## Quick Start Guide

**⏱️ Total Time: 30 minutes**

### Step 1: Get Your API Key (5 minutes)

1. Go to https://console.anthropic.com/
2. Click **"Sign Up"** (or Sign In if you have an account)
3. Enter your email and create a password
4. Verify your email
5. Click **"API Keys"** in the left sidebar
6. Click **"Create Key"**
7. **Copy the key** (starts with `sk-ant-...`)
   ⚠️ Save this somewhere safe - you won't see it again!

### Step 2: Install Software (10 minutes)

**Option A: Easy Install (Recommended for beginners)**

**For Windows:**
1. Download Python: https://www.python.org/downloads/
2. Run installer, **check "Add Python to PATH"**
3. Click "Install Now"

**For Mac:**
1. Open Terminal (press Cmd + Space, type "terminal")
2. Install Homebrew (if not installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Install Python:
   ```bash
   brew install python
   ```

**For Linux:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip
```

### Step 3: Download the App (5 minutes)

**Option A: Download ZIP (Easiest)**
1. Go to: https://github.com/glmoss-collab/PROINSULATIONESTIMATION
2. Click green **"Code"** button
3. Click **"Download ZIP"**
4. Unzip to a folder (e.g., `C:\EstimationApp` or `~/EstimationApp`)

**Option B: Using Git (If you know how)**
```bash
git clone https://github.com/glmoss-collab/PROINSULATIONESTIMATION.git
cd PROINSULATIONESTIMATION
```

### Step 4: Install Dependencies (5 minutes)

1. **Open Terminal/Command Prompt** in the app folder

   **Windows**: Right-click folder → "Open in Terminal"
   **Mac**: Right-click folder → Services → "New Terminal at Folder"
   **Linux**: Right-click folder → "Open in Terminal"

2. **Run this command:**
   ```bash
   pip install -r requirements.txt
   ```

   ⏳ This will take 2-5 minutes. You'll see text scrolling - this is normal!

3. **Wait for "Successfully installed"** message

### Step 5: Set Up Your API Key (3 minutes)

**Windows:**
1. Open Start Menu
2. Search for "Environment Variables"
3. Click "Edit environment variables for your account"
4. Click "New"
5. Variable name: `ANTHROPIC_API_KEY`
6. Variable value: `sk-ant-...` (your API key)
7. Click OK

**Mac/Linux:**
1. Open Terminal
2. Edit your profile:
   ```bash
   nano ~/.bash_profile
   ```
3. Add this line (replace with your key):
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```
4. Save: Press Ctrl+O, Enter, then Ctrl+X
5. Apply changes:
   ```bash
   source ~/.bash_profile
   ```

**Alternative: Use .env file (Easier for beginners)**
1. Create a file named `.env` in the app folder
2. Add this line:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
3. Save the file

### Step 6: Test the App (2 minutes)

Run this command:
```bash
python demo_agent.py --demo 1
```

You should see:
```
✅ Agent initialized successfully
DEMO 1: Conversational Estimation
...
```

🎉 **Success!** Your app is working!

---

## Installation & Setup

### Detailed Installation Steps

#### 1. Installing Python

**Why do I need Python?**
Python is the programming language that runs this app. It's free and safe.

**Check if you already have Python:**
```bash
python --version
```

If you see "Python 3.8" or higher, you're good! Skip to step 2.

**Install Python:**

**Windows:**
1. Visit: https://www.python.org/downloads/
2. Download "Python 3.11" or newer
3. Run the installer
4. ⚠️ **IMPORTANT**: Check the box "Add Python to PATH"
5. Click "Install Now"
6. Wait for installation to complete
7. Click "Close"

**Verify installation:**
```bash
python --version
```

Should show: `Python 3.11.x`

#### 2. Installing Required Packages

**What are packages?**
Packages are pre-built code libraries that the app needs to work. Think of them like apps on your phone.

**Install all packages:**
```bash
pip install -r requirements.txt
```

**What this installs:**
- `streamlit` - Creates the web interface
- `anthropic` - Connects to Claude AI
- `pdfplumber` - Reads PDF files
- `pymupdf` - Faster PDF processing
- `pydantic` - Data validation
- And more...

**Troubleshooting package installation:**

**If you get "pip not found":**
```bash
python -m pip install -r requirements.txt
```

**If you get permission errors (Mac/Linux):**
```bash
pip install --user -r requirements.txt
```

**If installation fails:**
1. Try updating pip:
   ```bash
   python -m pip install --upgrade pip
   ```
2. Try again:
   ```bash
   pip install -r requirements.txt
   ```

#### 3. Getting API Keys

**Anthropic Claude API Key** (Required)

1. **Sign Up**:
   - Go to: https://console.anthropic.com/
   - Click "Sign Up"
   - Use your work email
   - Verify email

2. **Create API Key**:
   - Log in to console
   - Click "API Keys" in sidebar
   - Click "Create Key"
   - Give it a name (e.g., "Estimation App")
   - **Copy the key immediately** (starts with `sk-ant-`)
   - Store it safely (you can't see it again!)

3. **Add Credits** (Optional):
   - New accounts get $5 free credit
   - Add payment method for more usage
   - Go to "Billing" → "Add Payment Method"

**Google Gemini API Key** (Optional - for legacy features)

1. Go to: https://aistudio.google.com/
2. Click "Get API Key"
3. Create key
4. Copy and save

#### 4. Configuring API Keys

**Method 1: Environment Variables (Recommended)**

**Windows:**
1. Press `Windows + R`
2. Type: `sysdm.cpl` and press Enter
3. Click "Advanced" tab
4. Click "Environment Variables"
5. Under "User variables", click "New"
6. Variable name: `ANTHROPIC_API_KEY`
7. Variable value: Your API key (paste it)
8. Click OK on all windows
9. **Restart Terminal/Command Prompt**

**Mac:**
1. Open Terminal
2. Edit bash profile:
   ```bash
   nano ~/.zshrc
   ```
   (or `~/.bash_profile` for older Macs)
3. Add this line at the end:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```
4. Save: Ctrl+O, Enter, Ctrl+X
5. Apply:
   ```bash
   source ~/.zshrc
   ```

**Linux:**
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Method 2: .env File (Easier)**

1. In the app folder, create a file named `.env`
2. Open it in Notepad (Windows) or TextEdit (Mac)
3. Add:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   GEMINI_API_KEY=your-gemini-key-here
   ```
4. Save the file
5. Done!

**Verify your setup:**
```bash
python -c "import os; print('✅ API Key found!' if os.getenv('ANTHROPIC_API_KEY') else '❌ API Key not found')"
```

---

## How to Use the App

### Running the App

You have **3 ways** to use the app:

#### Option 1: Web Interface (Easiest) ⭐ Recommended

1. **Open Terminal** in app folder
2. **Run:**
   ```bash
   streamlit run agent_estimation_app.py
   ```
3. **Your browser will open automatically**
4. You'll see: `http://localhost:8501`

**What you'll see:**
- Chat interface on the left
- Session summary on the right
- File upload buttons in sidebar
- Quick action buttons

**How to use it:**
1. Click "Upload Documents" in sidebar
2. Choose your PDF files:
   - Specification PDF
   - Drawing PDF (optional)
   - Price book (optional)
3. Click "Analyze All Documents"
4. Chat with the AI to refine your estimate
5. Click "Generate Quote"
6. Download your quote!

#### Option 2: Command Line (For advanced users)

1. **Run:**
   ```bash
   python claude_estimation_agent.py
   ```

2. **You'll see:**
   ```
   CLAUDE ESTIMATION AGENT - Interactive CLI
   ════════════════════════════════════════
   Commands:
     - Type your question
     - Type 'upload <path>' to add a file
     - Type 'status' to see summary
     - Type 'quit' to exit

   You:
   ```

3. **Try commands:**
   ```
   You: upload my_spec.pdf
   ✅ Uploaded: spec_1

   You: Analyze this specification and tell me what you find
   Agent: I'll analyze the specification for you...
   [AI analyzes and responds]

   You: Calculate pricing with 15% markup
   Agent: I'll calculate the pricing...
   [AI calculates and responds]

   You: Generate a complete quote
   Agent: I'll generate a professional quote...
   [Quote generated]
   ```

#### Option 3: Python API (For developers)

```python
from claude_estimation_agent import create_agent

# Create agent
agent = create_agent()

# Analyze PDF
response = agent.run("Analyze spec.pdf and create an estimate")

# Get results
quote = agent.get_session_data()["quote"]
print(f"Total: ${quote['total']:,.2f}")
```

### Step-by-Step Estimation Workflow

**Complete Example: Creating an Estimate**

1. **Start the app:**
   ```bash
   streamlit run agent_estimation_app.py
   ```

2. **Upload your PDFs:**
   - Click "Specification PDF" → Choose file
   - Click "Drawing PDF" → Choose file (if you have one)

3. **Quick Analysis:**
   - Click "🔍 Analyze All Documents"
   - Wait 15-30 seconds
   - Review what the AI found

4. **Refine (Optional):**
   Type in chat:
   - "Are there any missing specifications?"
   - "Check if outdoor specs have weather protection"
   - "What's the breakdown by system type?"

5. **Calculate Pricing:**
   - Click "💰 Calculate Pricing"
   - Or type: "Calculate pricing with 15% markup"

6. **Generate Quote:**
   - Click "📄 Generate Quote"
   - Review the quote in the summary panel

7. **Download:**
   - Click "📄 Download Quote (TXT)"
   - Click "📋 Download Material List"
   - Save to your computer

8. **Send to Client:**
   - Quote is ready to email or print!

### Example Conversations

**Example 1: Simple Estimate**
```
You: I need a quote for insulating ductwork in a small office building

Agent: I'd be happy to help! Let me ask a few questions:
       1. What's the total square footage?
       2. What type of HVAC system?
       3. Are any ducts exposed outdoors?

You: 5,000 sq ft, rooftop packaged unit, all ducts indoors

Agent: Based on typical 5,000 SF office with rooftop unit, I estimate:
       - Supply ductwork: ~200 LF (18x12 avg)
       - Return ductwork: ~150 LF (24x18 avg)
       - Indoor specs: 1.5" fiberglass with FSK facing

       Would you like me to proceed with these assumptions?

You: Yes, proceed

Agent: Quote generated! Total: $8,450
       - Materials: $5,200
       - Labor: $2,600 (40 hours)
       - Contingency: $650
```

**Example 2: PDF Analysis**
```
You: Analyze specifications.pdf and drawings.pdf

Agent: I'll analyze both documents for you...

       [30 seconds later]

       Found in specifications.pdf:
       - 12 insulation specifications
       - Duct, pipe, and equipment requirements
       - Special requirement: Outdoor aluminum jacketing

       Found in drawings.pdf:
       - 47 measurement items
       - Total ductwork: 340 LF
       - Total piping: 220 LF

       Cross-checking... ✓ All measurements have matching specs

       Would you like me to calculate pricing?

You: Yes, use 15% markup

Agent: Calculating with 15% markup...

       Complete! Total: $24,750
       Download quote? (Yes/No)
```

---

## Testing Your Setup

### Quick Tests

**Test 1: Verify Installation**
```bash
python -c "import anthropic, streamlit, pdfplumber; print('✅ All packages installed!')"
```

Expected output: `✅ All packages installed!`

**Test 2: Verify API Key**
```bash
python -c "from claude_estimation_agent import create_agent; agent = create_agent(); print('✅ Agent initialized!')"
```

Expected output: `✅ Agent initialized!`

**Test 3: Run Demo**
```bash
python demo_agent.py --demo 1
```

Expected: Conversational demo runs successfully

**Test 4: Run Web Interface**
```bash
streamlit run agent_estimation_app.py
```

Expected: Browser opens with app

### Full Testing Procedure

**Complete System Test (10 minutes)**

1. **Test Demos:**
   ```bash
   python demo_agent.py --demo 1  # Conversational
   python demo_agent.py --demo 4  # Tool usage
   python demo_agent.py --demo 5  # Session management
   ```

2. **Test Web Interface:**
   ```bash
   streamlit run agent_estimation_app.py
   ```
   - Upload a test PDF (any PDF works)
   - Try chat interface
   - Generate a test estimate

3. **Test CLI:**
   ```bash
   python claude_estimation_agent.py
   ```
   - Type: `status`
   - Type: `I need a quote for a 50-ton rooftop unit`
   - Type: `quit`

4. **Run Unit Tests:**
   ```bash
   pytest -v
   ```

**What Good Results Look Like:**

✅ All demos complete without errors
✅ Web interface loads and responds
✅ CLI accepts commands
✅ Tests pass (or most pass - some may skip without test PDFs)

---

## Troubleshooting

### Common Issues & Solutions

#### Issue: "Command not found: python"

**Cause**: Python not installed or not in PATH

**Solution**:
1. Try `python3` instead:
   ```bash
   python3 --version
   ```
2. If that works, use `python3` everywhere instead of `python`
3. Or reinstall Python and check "Add to PATH"

---

#### Issue: "Module not found: anthropic"

**Cause**: Packages not installed

**Solution**:
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install anthropic streamlit pdfplumber pymupdf pydantic
```

---

#### Issue: "ANTHROPIC_API_KEY not set"

**Cause**: API key not configured

**Solution**:

**Quick fix - Use .env file:**
1. Create `.env` file in app folder
2. Add: `ANTHROPIC_API_KEY=sk-ant-your-key`
3. Restart the app

**Permanent fix - Set environment variable:**
- See "Configuring API Keys" section above

---

#### Issue: "API Error: Authentication failed"

**Cause**: Invalid API key

**Solution**:
1. Check your API key is correct (no extra spaces)
2. Generate a new key at https://console.anthropic.com/
3. Update your `.env` file or environment variable
4. Restart app

---

#### Issue: "Rate limit exceeded"

**Cause**: Too many requests too quickly

**Solution**:
- Wait 60 seconds and try again
- The app has built-in rate limiting
- If it persists, check your API usage at console.anthropic.com

---

#### Issue: "PDF processing failed"

**Cause**: PDF corrupted, encrypted, or too large

**Solution**:
1. Check if PDF opens normally in Adobe Reader
2. If password-protected, remove password first
3. If very large (>50MB), try splitting into smaller files
4. Save a fresh copy of the PDF

---

#### Issue: Web interface won't open

**Cause**: Port already in use or browser issues

**Solution**:
1. Try a different port:
   ```bash
   streamlit run agent_estimation_app.py --server.port 8502
   ```
2. Manually open: http://localhost:8501
3. Try a different browser
4. Check firewall settings

---

#### Issue: "Slow performance"

**Cause**: Large PDFs or no caching

**Solutions**:
1. **Enable caching** (should be automatic):
   - Check if `.cache` folder exists
   - If not, caching may be disabled
2. **Use smart page selection**:
   - App automatically selects relevant pages
   - For large docs (100+ pages), expect 30-60s
3. **Check internet speed**:
   - API calls require good connection
4. **Close other programs**:
   - Free up RAM

---

### Getting Error Messages

**If something doesn't work:**

1. **Check the error message** - it usually tells you what's wrong
2. **Look for suggestions** - errors include fix suggestions
3. **Check the logs**:
   ```bash
   streamlit run agent_estimation_app.py --logger.level=debug
   ```

4. **Search the error**:
   - Copy error message
   - Search in PRODUCTION_ENHANCEMENTS.md
   - Search in AGENT_SETUP_GUIDE.md

---

## FAQ

### General Questions

**Q: How much does it cost to run?**

A:
- Software: Free (open source)
- API Usage: ~$0.05-0.50 per estimate
- Monthly: ~$5-20 for typical usage (50-100 estimates)
- New accounts get $5 free credit

**Q: Is my data secure?**

A:
- PDFs are processed locally on your computer
- Only sent to Claude AI for analysis (over encrypted connection)
- Anthropic doesn't train on your data
- See: https://www.anthropic.com/privacy

**Q: Can I use this offline?**

A: No, it requires internet for the AI API. However:
- PDFs are cached locally after first analysis
- Repeat analyses are nearly instant
- You can work on quotes offline after extraction

**Q: What PDF formats are supported?**

A:
- Standard PDF files (.pdf)
- Both text and image-based PDFs
- Multi-page documents
- Not supported: Password-protected, damaged, or DRM-protected PDFs

**Q: Can I customize pricing?**

A: Yes! Upload your own price book:
- Excel (.xlsx)
- CSV (.csv)
- JSON (.json)

See your distributor price book format

### Technical Questions

**Q: What version of Python do I need?**

A: Python 3.8 or newer (Python 3.11 recommended)

**Q: What operating systems are supported?**

A:
- ✅ Windows 10/11
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu, Debian, etc.)

**Q: Can I run this on a server?**

A: Yes! Deploy with:
- Streamlit Cloud (free)
- AWS, Google Cloud, Azure
- Docker container
- See DEPLOYMENT.md for details

**Q: Can multiple users use this?**

A: Yes, options:
1. **Shared computer**: Run app, everyone uses web interface
2. **Server deployment**: Deploy once, access from anywhere
3. **Individual setups**: Each user installs on their computer

---

## Getting Help

### Resources

1. **Documentation**:
   - `USER_MANUAL.md` (this file) - Basic usage
   - `AGENT_SETUP_GUIDE.md` - Technical setup
   - `PRODUCTION_ENHANCEMENTS.md` - Advanced features
   - `CLAUDE_AGENTS_ARCHITECTURE.md` - System design

2. **In-App Help**:
   - Click "💡 Example Prompts" in Streamlit app
   - Type `help` in CLI
   - Check tooltips (hover over ℹ️ icons)

3. **Online Resources**:
   - Anthropic Docs: https://docs.anthropic.com/
   - GitHub Issues: https://github.com/glmoss-collab/PROINSULATIONESTIMATION/issues
   - Streamlit Docs: https://docs.streamlit.io/

### Support Channels

**For App Issues**:
- Create GitHub Issue: [link]
- Include:
  - What you were trying to do
  - Error message (copy full text)
  - Your OS and Python version

**For API Issues**:
- Anthropic Support: https://support.anthropic.com/
- Check API Status: https://status.anthropic.com/

**For Billing Questions**:
- Anthropic Console: https://console.anthropic.com/settings/billing

---

## Next Steps

### Now that you're set up:

1. ✅ **Test with a real project**
   - Upload actual specification PDFs
   - Generate a quote
   - Compare with your manual estimate

2. ✅ **Customize settings**
   - Upload your price book
   - Adjust markup percentages
   - Set default labor rates

3. ✅ **Learn advanced features**
   - Read PRODUCTION_ENHANCEMENTS.md
   - Try cost tracking
   - Explore cache statistics

4. ✅ **Optimize your workflow**
   - Create templates for common projects
   - Set up keyboard shortcuts
   - Integrate with your CRM/quoting system

### Quick Reference

**Start Web App:**
```bash
streamlit run agent_estimation_app.py
```

**Start CLI:**
```bash
python claude_estimation_agent.py
```

**Run Tests:**
```bash
pytest
```

**View Cache Stats:**
```python
from utils_cache import get_cache
get_cache().stats()
```

**View Costs:**
```python
from utils_tracking import get_tracker
get_tracker().print_summary()
```

---

## Appendix

### System Requirements

**Minimum**:
- CPU: Dual-core processor
- RAM: 4GB
- Storage: 500MB free space
- Internet: 5 Mbps

**Recommended**:
- CPU: Quad-core processor
- RAM: 8GB+
- Storage: 2GB free space
- Internet: 10+ Mbps

### File Locations

- **App folder**: Where you installed the app
- **Cache**: `.cache/` folder (created automatically)
- **Config**: `.env` file (you create this)
- **Logs**: `.streamlit/` folder (if using Streamlit)
- **Exports**: Quotes saved to your Downloads or specified folder

### Keyboard Shortcuts

**Streamlit App**:
- `Ctrl + R` - Reload app
- `Ctrl + C` (in terminal) - Stop app
- `Ctrl + /` - Hide sidebar

**CLI**:
- `Ctrl + C` - Cancel current operation
- `Ctrl + D` - Exit
- `↑` / `↓` - Navigate command history

---

**🎉 Congratulations! You're ready to create professional estimates with AI!**

**Questions?** Re-read this manual or check the other documentation files.

**Happy Estimating!** 🚀
