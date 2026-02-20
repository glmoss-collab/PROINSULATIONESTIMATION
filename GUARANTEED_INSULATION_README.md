# Guaranteed Insulation Inc. — Bid Package Workflow

This workflow lets you **upload commercial mechanical drawings and specification PDFs** and receive a **formal bid package** with an **executive summary of scope of work** and a **financial breakdown**, branded for **Guaranteed Insulation Inc.**

## Scope

**Included (what we bid):**

- External duct wrap and ductwork insulation (supply, return, exhaust, OA)
- HVAC piping insulation (chilled water, hot water, condenser water, steam, condensate) with specified jacketing
- Equipment insulation (AHUs, FCUs, boilers, chillers, tanks)
- Kitchen exhaust / grease duct fireproofing and weatherproofing
- Weatherproofing and jacketing for exterior systems (aluminum or PVC as specified)

**Excluded (not in our scope):**

- Duct liner and internal acoustic liner
- Waste, sanitary, or domestic plumbing insulation
- Fire sprinkler piping (non-mechanical)
- Any scope not explicitly listed above

The app applies a **scope filter** so that only external HVAC/mechanical insulation is priced; duct liner, waste plumbing, and other excluded items are stripped out before pricing.

---

## Files

| File | Purpose |
|------|--------|
| **`guaranteed_insulation_app.py`** | Streamlit app: PDF upload → process → bid package download |
| **`guaranteed_insulation_scope.py`** | Scope filter: include only external HVAC/mechanical; exclude duct liner, waste plumbing, etc. |
| **`guaranteed_insulation_bid_package.py`** | Formal bid package generator: executive summary, financial breakdown, Guaranteed Insulation Inc. branding |

---

## How to run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) AI extraction

For automatic extraction from PDFs, set your Gemini API key:

- In the app sidebar, or
- Environment variable: `GEMINI_API_KEY`

Without an API key, you can still use “Basic text extract” from a spec PDF, or add one sample spec and one sample measurement manually to test the bid.

### 3. Launch the app

```bash
streamlit run guaranteed_insulation_app.py
```

### 4. Use the workflow

1. **Upload PDFs**
   - **Specification PDF** (required): mechanical specs, Division 23, insulation sections.
   - **Drawing PDF** (optional): mechanical plans for takeoff.

2. **Process**
   - Click **“Process PDFs and prepare bid (scope filter applied)”**.
   - The app extracts specs and measurements, then applies the scope filter (external HVAC/mechanical only).

3. **Generate bid**
   - Set **Labor rate**, **Markup**, and **Contingency %** in the sidebar if desired.
   - Click **“Generate formal bid package”**.

4. **Download**
   - Download the **formal bid package (TXT)**. It includes:
     - **Executive summary** (scope of work and exclusions)
     - **Financial breakdown** (materials by category, labor, contingency, total)
     - **Material schedule** (line items)
     - **Terms and notes**
   - All content is branded **Guaranteed Insulation Inc.** and states that scope is external HVAC/mechanical insulation only.

---

## Bid package contents

The downloaded file includes:

1. **Executive summary (scope of work)**  
   What is included (external duct wrap, HVAC piping, equipment, kitchen exhaust, weatherproofing) and what is excluded (duct liner, waste plumbing, sprinkler, etc.). If a scope filter was applied, a short summary of exclusions is included.

2. **Financial breakdown**  
   Materials by category, materials subtotal, labor (hours × rate), subtotal, contingency %, and **total bid**.

3. **Material schedule**  
   Line-item list: description, quantity, unit, total.

4. **Terms and notes**  
   Standard terms (e.g. 30-day validity, field verification).

Pricing uses the **environment pricebook** (`pricebook_sample.json` in the project root) so quotes stay consistent with your database.

---

## Customization

- **Company name / tagline**  
  Edit `COMPANY_NAME` and `SCOPE_DESCRIPTION` in `guaranteed_insulation_scope.py`. The bid package generator and app use these for branding.

- **Scope rules**  
  Edit `guaranteed_insulation_scope.py`: adjust `IN_SCOPE_KEYWORDS`, `EXCLUDED_KEYWORDS`, and the filter logic to match your exact scope and exclusions.

- **Labor rate, markup, contingency**  
  Set in the app sidebar before generating the bid; no code change needed.

- **Pricebook**  
  Replace or edit `pricebook_sample.json` to use your own unit prices. The app loads it from the project root by default.

---

## Summary

- **Upload:** Commercial mechanical specification PDF and (optional) drawing PDF.  
- **Steps:** Extract → scope filter (external HVAC/mechanical only) → price from pricebook → generate bid.  
- **Output:** Formal bid package (TXT) with executive summary, financial breakdown, and Guaranteed Insulation Inc. branding.  
- **Exclusions:** Duct liner, waste plumbing, domestic water, fire sprinkler, and other non-external mechanical insulation are excluded from the bid.
