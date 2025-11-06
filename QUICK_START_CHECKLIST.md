# Quick Start Checklist

**Print this page and check off each step as you complete it!**

---

## ✅ Pre-Installation (5 minutes)

- [ ] Have a computer with internet connection
- [ ] Have 30 minutes for setup
- [ ] Have a credit card for API signup (or free trial)
- [ ] Optional: Have a test PDF specification ready

---

## ✅ Get API Key (5 minutes)

- [ ] Go to https://console.anthropic.com/
- [ ] Sign up or log in
- [ ] Click "API Keys" in sidebar
- [ ] Click "Create Key"
- [ ] Copy the API key (starts with `sk-ant-`)
- [ ] Save it somewhere safe (password manager or secure note)

**Your API Key:** `sk-ant-_________________________`
(Write it down temporarily - you'll need it soon!)

---

## ✅ Install Software (10 minutes)

### Install Python

**Windows:**
- [ ] Download from https://www.python.org/downloads/
- [ ] Run installer
- [ ] ⚠️ CHECK "Add Python to PATH"
- [ ] Click "Install Now"
- [ ] Wait for completion

**Mac:**
- [ ] Open Terminal
- [ ] Install Homebrew (if needed):
      ```bash
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      ```
- [ ] Install Python:
      ```bash
      brew install python
      ```

**Linux:**
- [ ] Open Terminal
- [ ] Run:
      ```bash
      sudo apt-get update && sudo apt-get install python3 python3-pip
      ```

### Verify Installation

- [ ] Open Terminal/Command Prompt
- [ ] Type: `python --version`
- [ ] See: `Python 3.x.x` (3.8 or higher)

✅ Python is installed!

---

## ✅ Download App (5 minutes)

**Option 1: Download ZIP (Easier)**
- [ ] Go to https://github.com/glmoss-collab/PROINSULATIONESTIMATION
- [ ] Click green "Code" button
- [ ] Click "Download ZIP"
- [ ] Unzip to a folder (e.g., `C:\EstimationApp`)
- [ ] Remember this folder location!

**Option 2: Using Git**
- [ ] Open Terminal
- [ ] Run:
      ```bash
      git clone https://github.com/glmoss-collab/PROINSULATIONESTIMATION.git
      cd PROINSULATIONESTIMATION
      ```

**App Folder Location:** `____________________________`
(Write down where you saved it!)

---

## ✅ Install Dependencies (5 minutes)

- [ ] Open Terminal/Command Prompt in the app folder
      - **Windows**: Right-click folder → "Open in Terminal"
      - **Mac**: Right-click folder → Services → "New Terminal"
      - **Linux**: Right-click → "Open in Terminal"

- [ ] Run this command:
      ```bash
      pip install -r requirements.txt
      ```

- [ ] Wait for installation (2-5 minutes)
- [ ] See "Successfully installed" message

✅ Dependencies installed!

---

## ✅ Configure API Key (3 minutes)

**Option 1: Create .env File (Easiest)**

- [ ] In app folder, create a new file named `.env`
      - **Windows**: Right-click → New → Text Document → Rename to `.env`
      - **Mac/Linux**: Use TextEdit or nano

- [ ] Open `.env` in Notepad/TextEdit
- [ ] Add this line:
      ```
      ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
      ```
      (Replace with your real API key!)

- [ ] Save the file

**Option 2: Environment Variable (Permanent)**

- [ ] Follow instructions in USER_MANUAL.md section "Configuring API Keys"

✅ API key configured!

---

## ✅ Test Installation (2 minutes)

### Test 1: Verify API Key

- [ ] Run:
      ```bash
      python -c "from claude_estimation_agent import create_agent; agent = create_agent(); print('✅ Success!')"
      ```

- [ ] See: `✅ Success!`

### Test 2: Run Demo

- [ ] Run:
      ```bash
      python demo_agent.py --demo 1
      ```

- [ ] See demo output (conversational example)

✅ Tests passed!

---

## ✅ Run the App (1 minute)

### Start Web Interface

- [ ] Run:
      ```bash
      streamlit run agent_estimation_app.py
      ```

- [ ] Browser opens automatically
- [ ] See: `http://localhost:8501`
- [ ] App loads with chat interface

✅ **App is running!**

---

## ✅ Create Your First Estimate (5 minutes)

### Try a Simple Conversation

- [ ] In the chat box, type:
      ```
      I need a quote for insulating ductwork in a small office building
      ```

- [ ] AI responds with questions
- [ ] Answer the questions
- [ ] Get an estimate!

### Or Upload a PDF

- [ ] Click "Specification PDF" in sidebar
- [ ] Choose a PDF file
- [ ] Click "🔍 Analyze All Documents"
- [ ] Wait ~30 seconds
- [ ] Review results
- [ ] Click "💰 Calculate Pricing"
- [ ] Click "📄 Generate Quote"
- [ ] Click "Download" to save

✅ **First estimate created!**

---

## ✅ Next Steps

Now that everything works:

- [ ] Read USER_MANUAL.md for detailed usage
- [ ] Try with your real project files
- [ ] Explore advanced features in PRODUCTION_ENHANCEMENTS.md
- [ ] Set up deployment if needed (DEPLOYMENT_GUIDE.md)

---

## 🎉 Congratulations!

**You've successfully set up the AI Estimation App!**

### Quick Reference

**Start App:**
```bash
streamlit run agent_estimation_app.py
```

**Stop App:**
- Press `Ctrl + C` in terminal

**Get Help:**
- Read USER_MANUAL.md
- Check troubleshooting section
- Create GitHub issue for bugs

---

## 📊 Troubleshooting Quick Fixes

### Problem: "Command not found: python"
**Fix:** Try `python3` instead of `python`

### Problem: "ANTHROPIC_API_KEY not set"
**Fix:** Check your `.env` file, make sure key is correct

### Problem: "Module not found: anthropic"
**Fix:** Run `pip install -r requirements.txt` again

### Problem: Web page won't load
**Fix:** Manually open http://localhost:8501 in browser

### Problem: "API Error: Invalid authentication"
**Fix:** Check API key has no typos, try generating new key

---

## 💡 Tips for Success

1. **Save your API key safely** - You can't retrieve it later
2. **Start with small PDFs** - Test with 5-10 page documents first
3. **Use the cache** - Re-analyzing same PDFs is nearly free
4. **Monitor costs** - Check console.anthropic.com regularly
5. **Read the manuals** - Lots of helpful info in the docs!

---

## 📞 Need Help?

**Documentation:**
- `USER_MANUAL.md` - Complete user guide
- `AGENT_SETUP_GUIDE.md` - Technical details
- `PRODUCTION_ENHANCEMENTS.md` - Advanced features
- `DEPLOYMENT_GUIDE.md` - Hosting options

**Online:**
- GitHub Issues: Report bugs
- Anthropic Docs: https://docs.anthropic.com/
- Streamlit Docs: https://docs.streamlit.io/

---

**Happy Estimating!** 🚀

---

**Print Date:** _______________
**Completed Date:** _______________
**App Version:** 2.0
