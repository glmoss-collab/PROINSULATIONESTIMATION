# AI-Powered PDF Extraction Setup Guide

The HVAC Insulation Estimator now includes AI-powered automatic extraction of specifications, measurements, and project information from your PDFs using Google's Gemini API.

## Quick Start

### 1. Get Your Free Gemini API Key

1. **Go to**: https://aistudio.google.com/app/apikey
2. **Sign in** with your Google account
3. **Click**: "Create API Key"
4. **Select**: Your Google Cloud project (or create new)
5. **Copy**: Your API key (starts with "AIza...")

**Important**: Free tier includes:
- 15 requests per minute
- 1,500 requests per day
- 1 million tokens per day

This is MORE than enough for daily estimation work!

### 2. Add API Key to Your App

#### Option A: Streamlit Cloud (Deployed App)

1. Go to your app dashboard: https://share.streamlit.io/
2. Click on your app
3. Click **Settings** (⚙️) > **Secrets**
4. Add this line:
   ```toml
   GEMINI_API_KEY = "your-api-key-here"
   ```
5. Click **Save**
6. App will automatically restart with AI enabled

#### Option B: Local Development

1. Create `.streamlit/secrets.toml` in your project folder
2. Add:
   ```toml
   GEMINI_API_KEY = "your-api-key-here"
   ```
3. Or set environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```
4. Restart the app

#### Option C: Enter in App

1. Run the app
2. Look in the sidebar under "🤖 AI Extraction"
3. Paste your API key in the password field
4. Click outside the field to save

---

## How It Works

### 🎯 What the AI Can Extract

#### From Specification PDFs:
- ✅ **All insulation specifications** (material, thickness, facing)
- ✅ **System types** (duct, pipe, equipment)
- ✅ **Size ranges** for each spec
- ✅ **Special requirements** (outdoor, jacketing, mastic, etc.)
- ✅ **Project information** (name, location, contractor, date)

#### From Drawing PDFs:
- ✅ **Duct measurements** (sizes, lengths, fittings)
- ✅ **Pipe measurements** (diameters, lengths, fittings)
- ✅ **Locations** and area descriptions
- ✅ **Fitting counts** (elbows, tees, crosses)
- ✅ **Elevation changes** and vertical runs

### 📋 Usage Steps

1. **Upload Specification PDF**
   - Click "Upload Specification PDF"
   - Select your project specs (mechanical/insulation section)

2. **Upload Drawing PDF (Optional)**
   - Click "Upload Drawing PDF (Optional)"
   - Select your mechanical drawings

3. **Click "🤖 AI Extract Specs & Measurements"**
   - AI analyzes both PDFs (30-60 seconds)
   - Watch progress in real-time

4. **Review Results**
   - Project info appears in header
   - Specifications shown in table
   - Measurements added automatically
   - Make any needed adjustments manually

5. **Calculate Estimate**
   - Proceed to calculation step
   - Download quotes and material lists

---

## Best Practices

### ✅ Do's

- **Use clear, scanned PDFs** - Better quality = better extraction
- **Upload full spec sections** - Include all insulation specs
- **Review AI results** - Always verify extracted data
- **Combine PDFs** - Upload both specs and drawings together
- **Use consistent formats** - Standard specification formats work best

### ❌ Don'ts

- **Don't upload hand-drawn sketches** - AI works best with typed/printed docs
- **Don't upload photos of paper** - Use actual PDF files
- **Don't skip verification** - AI is smart but not perfect
- **Don't upload huge files** - Split large drawing sets into sections

---

## Troubleshooting

### "API Key Invalid" Error

**Problem**: API key not recognized

**Solutions**:
1. Check you copied the full key (starts with "AIza")
2. Make sure no extra spaces
3. Verify key is active at: https://console.cloud.google.com/apis/credentials
4. Generate a new key if needed

### "No Specifications Found" Warning

**Problem**: AI couldn't extract specs

**Solutions**:
1. Check PDF has actual insulation specifications
2. Look for spec tables or specification text
3. Try uploading just the insulation/mechanical section
4. Use manual entry for unusual formats
5. Use "📄 Basic Text Extract" as fallback

### "Quota Exceeded" Error

**Problem**: Hit API rate limits

**Solutions**:
1. **Free tier limits**:
   - Wait 1 minute (15 requests/minute limit)
   - Wait until tomorrow (1,500 requests/day limit)
2. **Upgrade** to paid plan if needed
3. **Process smaller batches** of PDFs

### "AI is Slow" Issue

**Problem**: Extraction takes too long

**Expected**:
- Small PDFs (1-10 pages): 10-30 seconds
- Medium PDFs (10-30 pages): 30-60 seconds
- Large PDFs (30+ pages): 60-120 seconds

**Solutions**:
1. Split large PDFs into sections
2. Upload only relevant pages
3. Be patient - quality extraction takes time

---

## Cost & Limits

### Free Tier (Google AI Studio)

**Limits**:
- 15 requests per minute
- 1,500 requests per day
- 1 million tokens per day

**Typical Usage**:
- 1 spec PDF = 1-3 requests
- 1 drawing PDF = 2-5 requests
- **You can process 100-300 projects per day for FREE**

### Paid Tier (Google Cloud)

If you need more:
- **Gemini 1.5 Flash**: $0.075 per 1M tokens (very cheap!)
- **Gemini 1.5 Pro**: $1.25 per 1M tokens (best quality)

**Cost estimate**:
- Process 1,000 projects/month: ~$5-10
- Process 10,000 projects/month: ~$50-100

Still way cheaper than manual data entry!

---

## Privacy & Security

### What Gets Sent to Google?

- PDF pages converted to images
- Sent to Google's secure Gemini API
- Processed and discarded immediately
- **NOT** stored or used for training

### How to Keep Data Private?

1. **Remove sensitive info** before upload
2. **Redact client names** if needed
3. **Use local environment variables** for API key
4. **Don't commit** secrets.toml to git
5. **Review** Google's privacy policy: https://ai.google/privacy/

### Enterprise Options

Need maximum security?
- Run **self-hosted AI models** (Llama, etc.)
- Use **Azure OpenAI** (your tenant only)
- Deploy **on-premises** with local AI
- Contact us for enterprise deployment

---

## Advanced Tips

### Better Extraction Results

1. **Pre-process PDFs**
   - Ensure good scan quality (300+ DPI)
   - Remove unnecessary pages
   - Combine related sections

2. **Optimize Prompts** (for developers)
   - Edit `gemini_pdf_extractor.py`
   - Customize extraction prompts
   - Add industry-specific keywords

3. **Batch Processing**
   - Process multiple projects in sequence
   - Use CSV import for measurements
   - Combine automated + manual data

### API Key Best Practices

1. **Use environment variables** in production
2. **Rotate keys** periodically
3. **Set quota alerts** in Google Cloud Console
4. **Monitor usage** in AI Studio dashboard
5. **Use separate keys** for dev/prod

---

## Examples

### Example 1: Complete Project

```
1. Upload: "Project_ABC_Specs.pdf" (20 pages)
2. Upload: "Project_ABC_Drawings.pdf" (15 pages)
3. Click "🤖 AI Extract Specs & Measurements"
4. Wait 45 seconds
5. Results:
   ✓ Project: ABC Commercial Building | Chicago, IL
   ✓ 8 specifications extracted
   ✓ 142 measurements extracted
6. Review and adjust as needed
7. Calculate estimate
```

### Example 2: Specs Only

```
1. Upload: "Insulation_Specs_Section_23_07_00.pdf"
2. Click "🤖 AI Extract Specs & Measurements"
3. Wait 20 seconds
4. Results:
   ✓ Project: Healthcare Facility Renovation
   ✓ 12 specifications extracted
5. Add measurements manually or via CSV
6. Calculate estimate
```

---

## Getting Help

### Resources

- **API Documentation**: https://ai.google.dev/docs
- **AI Studio Dashboard**: https://aistudio.google.com/
- **Quota Management**: https://console.cloud.google.com/apis/dashboard
- **Pricing**: https://ai.google.dev/pricing

### Support

- **App Issues**: GitHub Issues
- **API Questions**: Google AI Studio Support
- **Feature Requests**: GitHub Discussions

---

## FAQ

**Q: Is the API key required?**
A: No, you can still use manual entry and CSV import. AI extraction is optional but highly recommended.

**Q: Does it work offline?**
A: No, requires internet connection to Google's API.

**Q: How accurate is the AI?**
A: Very good (90-95%+ accuracy) on standard specs. Always review results.

**Q: Can I use other AI models?**
A: Yes! Code is modular. You can add OpenAI, Anthropic, or local models.

**Q: Will this work with my old PDFs?**
A: Usually yes, if text is readable. Scanned images may have lower accuracy.

**Q: Can I extract from Word docs?**
A: Convert to PDF first, then upload.

---

**Ready to try AI extraction? Get your free API key now!**

https://aistudio.google.com/app/apikey
