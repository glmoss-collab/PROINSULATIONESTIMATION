# Estimator & Quote Manager Workflow (GitHub-Integrated)

This expanded manual augments the original Agent‑Builder walkthrough with the
Python and Streamlit utilities that already live in this repository. Follow the
steps below to wire the OpenAI workflow directly into the estimation code so
your agent can analyze bid emails, parse linked plan sets, and output ready-to-
send mechanical HVAC insulation quotes.

---

## 1 — Get set up

1. **Log in to Agent‑Builder**  
   Open platform.openai.com → **Agent Builder** and sign in with the account
   tied to your estimating workspace.

2. **Create a new workflow**  
   * Click **New workflow** → name it **Estimator & Quote Manager** → **Create**.  
   * You will see a blank canvas with a **Start** node.

3. **Understand where the GitHub code fits**  
   Keep this repository cloned locally or synced to cloud storage so the
   workflow can call the existing automation layers:
   * `hvac_insulation_estimator.py` — end‑to‑end estimation engine (spec parsing,
     measurement ingestion, pricing, quoting).
   * `gemini_pdf_extractor.py` — Google Gemini 2.0 Flash powered PDF extractor
     for specs, drawings, and project metadata.
   * `estimation_app.py` — Claude 3.5 Sonnet powered helpers for parsing specs
     and drawings (used today in the Streamlit UI, also callable from a Code
     node).
   * `streamlit_app.py` — production estimator UI that already orchestrates the
     above modules; review it when you need UI copy or workflow prompts.
   * `process_my_pdfs.py` — command‑line PDF text extractor that doubles as a
     fallback inside automation nodes when AI vision is unavailable.

   You will reference these scripts from Code nodes (Python) or Tool nodes (when
   connector support lands).

---

## 2 — Define global variables and resources

Before dropping nodes, surface the artifacts Agent‑Builder will read:

1. **Distributor price book**  
   Store `distribution_international_pricebook_2025_list.json` (or the sample
   `pricebook_sample.json`) in Drive/Dropbox. `PricingEngine` in
   `hvac_insulation_estimator.py` automatically normalizes that schema and pulls
   defaults such as markup percent and labor multipliers.

2. **Mechanical insulation cheat sheet**  
   Keep `Master Cheat Sheet_ Commercial Mechanical HVAC Insulation Cost
   Estimation.txt` accessible. You can embed the most critical rules into the QA
   node or attach it as a knowledge base file.

3. **Estimation libraries**  
   Upload a zipped copy of this repository—or at minimum the following modules—
   to a storage location the workflow can read from a Code node:
   * `hvac_insulation_estimator.py`
   * `gemini_pdf_extractor.py`
   * `estimation_app.py`
   * `process_my_pdfs.py`
   * `measurements_template.csv` (used to seed structured takeoff tables)

4. **Company procedures**  
   Stage `Isolator instruction.txt` and any internal policies. They become the
   basis for the QA checklist, approval rules, and proposal notes.

5. **Threshold variables**  
   Record auto‑approval caps, minimum margins, and contingency defaults. You can
   load them into workflow state once your Code nodes initialize the pricing
   engine.

---

## 3 — Build the workflow nodes

The high‑level flow remains **Start → Spec Extractor → Attachment Parser →
Template Selector → Pricing Fetcher → Estimation Calculator → QA Checker → Draft
Creator → Approval Router → Send & Log**. The sections below show how each node
maps to concrete functions in this repo.

### 3.1 — Spec Extractor (Email + Linked Specs)

1. **Add an Agent node** and rename it **Spec Extractor**.
2. **Instructions:** extend the JSON schema from the original manual so it also
   captures S3/Drive share links and email thread IDs.
3. **Leverage existing code:**
   * Call `GeminiPDFExtractor.extract_project_info` and
     `GeminiPDFExtractor.extract_specifications` when an attachment path or
     Dropbox link is present. The `streamlit_app.py` sidebar already shows how to
     bootstrap `GeminiPDFExtractor` from a user‑supplied API key.
   * When you only have inline email text, fall back to the regex helpers in
     `SpecificationExtractor.extract_from_pdf` or `process_my_pdfs.extract_spec_text`
     to parse plain text dumps.
4. **Outputs:** Return the JSON payload plus an array of `download_tasks` that
   later nodes can process (each task contains a file URL, local cache path, and
   inferred document type).

### 3.2 — Attachment Parser (Drawings & Misc Docs)

1. Insert a second Agent node labeled **Attachment Parser**.
2. Use the following logic inside a Code tool:
   ```python
   from gemini_pdf_extractor import GeminiPDFExtractor
   extractor = GeminiPDFExtractor(api_key=state["gemini_api_key"])
   takeoff_rows = extractor.extract_measurements_from_drawings(local_pdf)
   ```
3. If Gemini vision is unavailable, run `process_my_pdfs.py` to harvest raw
   measurements, normalize them into dictionaries, and feed them through
   `DrawingMeasurementExtractor.manual_entry_measurements`. The data class definitions in
   `hvac_insulation_estimator.py` (`MeasurementItem`, `InsulationSpec`) keep the
   schema consistent downstream.

### 3.3 — Template Selector

1. Add an Agent node called **Template Selector**.
2. Extend its prompt so it checks the project location and scope against your
   stored templates. `streamlit_app.render_header` demonstrates how project name
   and location are surfaced; reuse that formatting for template metadata.
3. Optionally wire a File Search tool that looks up `.docx` templates stored in a
   Drive folder named after the job. Return the template path plus a default when
   nothing matches.

### 3.4 — Pricing Fetcher (Load distributor data)

1. Add a **Code** node (Python runtime). Mount or download the chosen price book.
2. Use the in‑repo pricing engine:
   ```python
   from hvac_insulation_estimator import PricingEngine

   pricebook_path = state.get("pricebook_path")
   markup = state.get("markup_multiplier", 1.15)
   pricing_engine = PricingEngine(price_book_path=pricebook_path, markup=markup)
   state["pricing_engine"] = pricing_engine
   state["price_defaults"] = getattr(pricing_engine, "_file_defaults", {})
   ```
3. Expose normalized unit costs and any defaults (e.g., markup percent) to the
   next node. `PricingEngine._load_prices` already understands both the supplier
   schema and a simple key → price JSON.

### 3.5 — Estimation Calculator (Quantities + Totals)

1. Add another Code node named **Estimation Calculator**.
2. Load measurement/spec dictionaries emitted by previous nodes and convert them
   into strongly typed objects:
   ```python
   from hvac_insulation_estimator import (
       InsulationSpec,
       MeasurementItem,
       PricingEngine,
       QuoteGenerator,
   )

   specs = [InsulationSpec(**s) for s in inputs["specs"]]
   measurements = [MeasurementItem(**m) for m in inputs["measurements"]]
   pricing_engine: PricingEngine = state["pricing_engine"]

   materials = pricing_engine.calculate_materials(measurements, specs)
   labor_hours, labor_cost = pricing_engine.calculate_labor(materials)
   labor_rate = state.get("labor_rate")
   if labor_rate is not None:
       labor_cost = labor_hours * float(labor_rate)

   quote = QuoteGenerator().generate_quote(
       project_name=inputs["project_name"],
       measurements=measurements,
       materials=materials,
       labor_hours=labor_hours,
       labor_cost=labor_cost,
       specs=specs,
   )
   ```
3. Persist both the detailed line items and the summarized totals into workflow
   state. If you want LLM reasoning in the mix, wrap the calculator with the
   `estimation_app.analyze_specifications` or
   `estimation_app.analyze_drawings_and_get_takeoff` helpers to compare AI takeoff
   text with the deterministic pricing output.

### 3.6 — QA Checker

1. Add an Agent node named **QA Checker**.
2. Feed it:
   * The `quote` structure from the previous node (materials, labor, totals).
   * Policy text from `Isolator instruction.txt`.
   * Any generated notes from `QuoteGenerator._generate_quote_notes` for context.
3. In the instructions, require JSON output such as:
   ```json
   {
     "qa_pass": true,
     "math_check": "OK",
     "policy_issues": [],
     "clarifications": []
   }
   ```
4. If `qa_pass` is `false`, branch back to Estimation Calculator for revisions or
   route to a human approver immediately.

### 3.7 — Draft Creator

1. Add an Agent node labeled **Draft Creator**.
2. Provide it with:
   * The selected template path (from Template Selector).
   * The structured quote object and alternatives from `QuoteGenerator`.
   * Boilerplate email copy from `streamlit_app.render_header` and the
     `QuoteGenerator.export_quote_to_file` format for reference.
3. Ask the model to:
   * Populate the template placeholders.
   * Produce an email summary with bullet assumptions.
   * Output a list of documents to attach (`quote_pdf`, `material_list.csv`).
4. When automation connectors are available, this node can call a Code tool that
   renders a PDF using the same formatting as `export_quote_to_file`.

### 3.8 — Approval Router

1. Insert an **If/Else** node.
2. Configure thresholds using state values loaded earlier (e.g.,
   `total <= 25000` **and** `margin >= 0.18` → auto send).
3. For anything higher risk, fan out to **User approval** nodes representing the
   estimator or VP. Include the QA notes and quote summary in the approval task.

### 3.9 — Send & Log

1. Add a final Code/Agent node.
2. Responsibilities:
   * Email delivery: call the Gmail connector (once enabled) with the draft body
     and attachments produced earlier.
   * Document storage: push the exported quote to Drive/Dropbox. Use the
     `QuoteGenerator.export_quote_to_file` path as the canonical filename format.
   * CRM logging: post a summary payload including project name, value, margin,
     and due date.
3. Append a success/failure flag to state so downstream automations (follow-ups)
   can react.

### 3.10 — Optional Follow‑up Scheduler

Use a Set State node or a Code node that calls your calendar/CRM API. Seed the
follow-up description with the same verbiage produced by the Draft Creator.

---

## 4 — Integrate external services

1. **Gmail ingestion**  
   * Search for bids labeled `GI/RFQ`. Store message IDs, subjects, and Dropbox
     links in state.  
   * Reuse the email parsing heuristics embedded in `estimation_app.py` (the
     Streamlit UI shows how file uploads are encoded to base64 before calling an
     LLM).  
   * Always ask for confirmation before downloading files from unknown senders.

2. **Dropbox or Drive**  
   * List the bid folder contents chronologically. Build `download_tasks` that
     pair each PDF with a detector: `"spec"` → `extract_specifications`,
     `"drawing"` → `extract_measurements_from_drawings`.

3. **File parsing fallbacks**  
   * When the Gemini API is throttled, run `process_my_pdfs.py` to harvest text
     and then push the raw string into `SpecificationExtractor._parse_insulation_specs`.
   * Maintain parity with `DrawingMeasurementExtractor` so measurement objects
     keep their required keys (`item_id`, `system_type`, `size`, `length`, etc.).

4. **Pricing data**  
   * Cache the distributor file locally after the first download. `PricingEngine`
     stores supplier defaults in `pricing_engine.file_defaults`, so you can reuse
     them for margin checks and approval rules.

---

## 5 — Test the workflow

1. **Preview runs**  
   * Feed a sample email plus spec/drawing PDFs through Preview. Validate that
     the Spec Extractor populates the JSON schema and registers `download_tasks`.

2. **Node-by-node validation**
   * Inspect outputs after each node. Compare quantities and unit costs with the
     deterministic calculations shown in the `main()` demonstration inside
     `hvac_insulation_estimator.py`, which walks through pricing, labor, and
     quote generation end-to-end.
   * Cross-check LLM summaries with the deterministic helper functions in
     `estimation_app.py`.

3. **Connector dry runs**  
   * After enabling Gmail/Dropbox, process a single real email. Pause before the
     Send & Log node to verify pricing, QA, and approval routing behave as
     expected.

---

## 6 — Safety & prompt-injection precautions

* **Link validation** — Require explicit user approval before downloading any
  URL that was not pre-approved. Keep a whitelist of trusted domains in state.
* **Sensitive pricing** — Mask distributor net prices when generating customer
  deliverables; expose markup-only numbers externally. `PricingEngine.calculate_materials`
  keeps base costs separate so you can redact them in templates.
* **Prompt integrity** — Strip instructions found inside attachments before
  sending them to LLM nodes. Feed sanitized text into the deterministic parsers
  first, and only pass structured summaries into downstream Agents.
* **Error handling** — Surround each Code node call with try/except blocks that
  push human-readable error states forward (e.g.,
  `state["qa_pass"] = False; state["qa_errors"] = ["Gemini timeout"]`).

---

### Summary

You now have a blueprint that maps every Agent‑Builder node to working Python
modules in this repository. Follow the node wiring described above, reuse the
existing extraction, pricing, and quote-generation helpers, and layer your
company policies through QA and approval checks. Once Gmail/Dropbox connectors
are enabled, the workflow can pull bid packages directly from email and output
polished mechanical HVAC insulation estimates without leaving the Agent‑Builder
canvas.
