# Inbox → Takeoff → Guaranteed Insulation Bid

**Audience:** Guaranteed Insulation Inc. (Athens, GA)  
**Status:** Inbox / Gmail / Dropbox intake is **deferred**. If you can upload the PDFs yourself, use `TAKEOFF_ACCURACY.md` — that is the path that matters for a bid.

This document is the earlier end-to-end review (including connectors). Do not implement the inbox pipeline until takeoff from an uploaded set is accurate.

---

## 1. Recommended route (short answer)

Do **not** start with an Agent-Builder canvas that asks a model to “read the email, look at the drawings, and write a quote.” That path is already sketched in `Estimator_Agent_Workflow.md` and it will produce confident, wrong numbers.

Build this instead:

```
Gmail watch (label / query)
        │
        ▼
Email triage (deterministic + light LLM)
  • Is this an RFQ / ITB / addendum / spam?
  • Project name, GC, bid due date, job address
  • Dropbox / Box / Procore / PlanGrid / attached PDF links
        │
        ▼
Human confirm  ──►  download shared folder (whitelist domains)
        │
        ▼
Document classifier
  • Spec book vs drawing set vs addendum vs schedule vs junk
  • Sheet type: cover, index, legend, plan, section, riser,
    isometric, duct schedule, pipe schedule, insulation spec
        │
        ▼
Two extractors (run in parallel)
  ┌─────────────────────┐     ┌──────────────────────────────┐
  │ SPECS (tables first)│     │ QUANTITIES (schedules first) │
  │ 23 07 13 / 07 16 /  │     │ Duct schedule, pipe schedule │
  │ 07 19 thickness by  │     │ THEN plan takeoff for runs   │
  │ size / service /    │     │ not listed on a schedule     │
  │ indoor vs outdoor   │     │ Vector PDF + callouts +      │
  └──────────┬──────────┘     │ per-sheet scale              │
             │                └──────────────┬───────────────┘
             └──────────┬────────────────────┘
                        ▼
              Scope mapper (GI rules)
              Wrap vs liner, HVAC vs plumbing,
              exposed vs concealed, kitchen wrap
                        │
                        ▼
              Deterministic PricingEngine
              (pricebook keys only — no invented $)
                        │
                        ▼
              Estimator review board
              Missing sheets, low-confidence runs,
              unmatched spec rows, exclusions
                        │
                        ▼
              Formal GI bid (PDF/DOCX, not TXT)
              Project-specific scope + clarifications
              + addenda list + due date
```

**What already exists and should be kept:** `PricingEngine`, `ProjectQuote`, GI scope keywords, GI bid-package sections, pricebook loaders.

**What does not exist and is the actual product:** inbox connectors, shared-link download, document classification, insulation-table parsing, schedule takeoff, real drawing measurement, spec-to-size matching, professional bid PDF, and a hard stop when quantities are incomplete.

---

## 2. What the codebase actually is

The repo is a **quote assembler with aspirational PDF vision**, not a takeoff system.

| Layer | Status | Reality |
|-------|--------|---------|
| Gmail inbox triage | Documented only | Zero Gmail API, Pub/Sub, OAuth, or label watcher in code |
| Dropbox / Drive download | Documented only | No shared-link resolver, folder listing, or auth |
| Spec extraction | Partial | Regex + “send page images to a vision model.” Misses CSI thickness tables |
| Drawing takeoff | Unsafe | Hough-line CV labels every line `unknown` / `TBD`. Vision path asks the model to *estimate* LF from a 150 DPI raster, first 15–30 pages only |
| Scope filter | Partial | Exclusion keywords work; **inclusion keywords are never used** |
| Pricing | Usable for demos | 19 sample keys, no size-banded pipe/duct prices, silent `$5.00` fallback |
| Bid package | Demo-grade | Plain TXT, generic scope boilerplate, no addenda / due date / letterhead PDF |
| Human QA gate | Missing | Streamlit can generate a bid as soon as any spec + measurement exist |

`Estimator_Agent_Workflow.md` maps an OpenAI Agent-Builder graph onto these modules. That is a wiring diagram, not an implementation. Do not treat it as the production path.

---

## 3. Why “just use a model on the PDF” fails on commercial jobs

A typical GC drop is not one 10-page PDF. It is:

- An email: “ITB — Midtown Medical MOB — Bid due Friday 2pm — plans in Dropbox”
- A Dropbox folder: 80–250 sheet drawing set + 400–800 page spec book + addenda
- Mechanical sheets at **different scales** (1/8" plans, 1/4" enlarged plans, NTS details)
- Duct shown as double-line with size tags (`24x16`), not a single polyline
- Pipe shown as single-line with service tags (`4" CHWS`), often overlapping plumbing
- **The quantities you can actually bid** often live in **duct and pipe schedules**, not in the plan graphics
- Insulation requirements live in **Division 23 tables** (thickness by NPS and service temperature), not in a sentence like `duct insulation 1.5" fiberglass`

Current extractors fight that reality:

1. `DrawingMeasurementExtractor._detect_lines_and_measure` (`hvac_insulation_estimator.py`) runs Canny + HoughLinesP on a raster. It measures *every* line (grids, walls, leaders) and cannot tell duct from dimension string. `system_type="unknown"`, `size="TBD"`.
2. `GeminiPDFExtractor.extract_measurements_from_drawings` rasterizes ≤30 pages at 150 DPI and asks the model to “estimate length from scale.” That is not takeoff.
3. `extract_measurements` in `claude_agent_tools.py` only analyzes the **first 15 pages**. On a real set those are cover, index, legends, and details — not the floor plans.
4. Spec regex looks for `duct ... insulation ... 1.5" fiberglass`. Real specs are tables: “CHW ≤2" : 1" elastomeric indoor / 2" + aluminum jacket outdoor.”
5. `_find_applicable_spec` matches **system_type only**. First duct spec wins for every duct, ignoring size band and indoor/outdoor.

A model can *help classify sheets and read a schedule row*. It cannot be the source of record for linear feet on a 40-sheet mechanical set.

---

## 4. Recommended pipeline in detail

### 4.1 Gmail triage (build this first)

**Mechanism (pick one, keep it boring):**

- Gmail API + `users.watch` → Pub/Sub push, **or**
- Poll `users.messages.list` on a dedicated mailbox / label every few minutes

**Query to start with (tune after two weeks of real mail):**

```
(label:GI-RFQ OR subject:(ITB OR RFQ OR "invitation to bid" OR "bid package" OR addendum)
 OR filename:pdf)
-category:promotions -category:social
```

**Extract from each message (structured, validated):**

| Field | Why it matters |
|-------|----------------|
| Message ID + thread ID | Dedup, addenda on same job |
| From / GC or CM name | Bid log |
| Subject | Project name heuristic |
| Bid due date / time | Calendar + “do not start late jobs” |
| Job address / city | Travel, weather, wage |
| Attachment PDFs | Direct download |
| Shared links | Dropbox, Box, Procore, Autodesk, PlanGrid, BuildingConnected |
| Classification | `new_bid` / `addendum` / `rfi` / `award` / `not_a_bid` |
| Confidence + reason | Estimator inbox UI |

Use a small model only to classify and fill those fields. Do **not** download links until a human (or a tight domain whitelist) approves.

**Security (already called out in the Agent-Builder doc — keep it):**

- Whitelist: `dropbox.com`, `box.com`, `procore.com`, `autodesk.com`, `plangrid.com`, known GC domains
- Never follow arbitrary URLs from unknown senders
- Store files in a job folder named `{due-date}_{project-slug}_{message-id}`
- Strip prompt-like text from PDFs before any LLM sees raw attachment text

**What to build in this repo:** `intake/gmail_watcher.py`, `intake/email_triage.py`, `intake/link_resolver.py`. None of these files exist today.

### 4.2 Dropbox (and other plan rooms)

GCs do not send one PDF. They send a folder.

**Required operations:**

1. Resolve shared URL → list folder recursively
2. Download PDFs / ZIPs only (skip marketing PPTX, walkthrough MP4)
3. Version by `server_modified` / content hash (addenda overwrite)
4. Classify each file: `spec_book`, `drawing_set`, `addendum`, `schedule`, `other`
5. Split drawing sets by sheet number from the title block (`M-2.01`, `M-5.10`, `I-1.0`)

Dropbox API (`/2/sharing/get_shared_link_metadata` + `/2/files/list_folder` + `/2/files/download`) is enough. Same adapter interface for Box later.

**Do not** pass a Dropbox URL to a vision model and hope it “opens the link.” Download locally, then process.

### 4.3 Document intelligence — classify before you extract

Add a sheet/page classifier **before** any takeoff:

| Class | Action |
|-------|--------|
| Cover / title | Project info only |
| Drawing index | Sheet list + expected mechanical sheets (gap check) |
| Legend / abbreviations | Service tags (`CHWS`, `HWR`, `EA`, `OA`) |
| Insulation spec (23 07 xx) | Table extract → `InsulationSpec` rows |
| Duct schedule | Primary duct quantity source |
| Pipe / hydronic schedule | Primary pipe quantity source |
| Floor / roof mechanical plan | Geometry takeoff for unscheduled runs |
| Section / detail / isometric | Fitting density, outdoor vs indoor, grease duct wrap |
| Kitchen / grease | 3M / listed wrap system, not fiberglass wrap |
| Plumbing / fire protection | Exclude unless tagged mechanical |
| Addendum | Overlay revisions; never ignore |

`utils_pdf.smart_page_selection` scores pages by the word “insulation.” That is useful for spec books and **wrong** for drawing sets (plans rarely say “insulation” on the sheet). Drawing selection must use **sheet number + title block**, not keyword score.

### 4.4 Spec extraction that matches how Division 23 is written

Replace sentence-regex as the primary path.

**Target schema (one row per rule, not one spec for “all duct”):**

```
service          : CHW | HW | CW | steam | condensate | supply_duct | ...
size_min_in      : 0.5
size_max_in      : 2.0
location         : indoor | outdoor | shaft | mechanical_room
material         : elastomeric
thickness_in     : 1.0
facing           : ASJ
jacket           : none | aluminum | pvc_20 | pvc_30 | stainless
specials         : [vapor_barrier, mastic, stainless_bands]
source           : {file, section, page, table_row}
```

**How to get it:**

1. `pdfplumber` / PyMuPDF table extraction on 23 07 13, 23 07 16, 23 07 19
2. Vision model **only** on scanned/image-only spec pages, constrained to the same JSON schema
3. Validate with existing `InsulationSpecExtracted` (then map down to the engine dataclass)
4. Keep the raw table cell text on every row for the bid “per spec” citation

Pydantic models in `pydantic_models.py` are already richer than `InsulationSpec` (service-specific types, page, section, confidence). The engine still uses the thin dataclass. **Unify these** or the agent and the calculator will keep disagreeing.

### 4.5 Quantity takeoff — schedules first, graphics second

This is the accuracy bottleneck. Order of operations:

**A. Extract schedules (highest ROI)**

Duct schedule columns typically: mark, size, CFM, insulation (yes/no or type), lining (yes/no).  
Pipe schedule: service, size, insulation spec reference.

If the schedule says `SA-1 24x16 40'-0" lined` — **do not price wrap** for that mark.  
If it says `CHWS 4" insul.` — that is a quantity *hint*; you still need LF from plans or a length column.

**B. Plan takeoff for runs not fully quantified**

Do **not** use Hough lines. Use:

1. Vector PDF path extraction (PyMuPDF `get_drawings()` / `get_cdrawings()`) — CAD exports keep duct/pipe as stroked paths with consistent color/layer
2. Text callouts near those paths (`24x16`, `4" CHWR`) via `page.get_text("dict")`
3. Per-sheet scale from title block, **never** a single scale for the whole PDF
4. Matchline / split-sheet handling so floor 2 is not counted twice
5. Risers and isometrics counted as **fittings / vertical LF**, not a second copy of the floor plan

Vision model role: “this sheet is M-2.03 second floor hydronic, scale 1/8", these callouts are CHW.”  
Vision model is **not** allowed to invent `length: 245.0` as the bid quantity without a measured path or a schedule length.

**C. Equipment**

`MeasurementItem` only supports `duct` | `pipe` plus linear feet. Equipment (AHU casings, tanks, chillers) is **surface area**, not LF. Add an `equipment` measurement type with SF or a bounding box × height. Kitchen grease duct is a listed **wrap system** (layers × SF), not `mineral_wool_1.5` + `stainless_jacket` unless the spec says that.

**D. Dedup rules (you will over-bid without these)**

- Floor plan + roof plan + isometric of the same main
- Enlarged mechanical room that also appears on the floor plan
- Spec “insulate all ductwork” vs schedule “liner only”
- Domestic water drawn on M sheets (exclude) vs HVAC HW (include)

### 4.6 Scope mapper (Guaranteed Insulation rules)

Keep `guaranteed_insulation_scope.py`, but fix the logic.

**In scope:** external duct **wrap**, HVAC piping (CHW/HW/CW/steam/condensate), equipment insulation, kitchen/grease listed wrap, outdoor jacketing.

**Out of scope:** duct **liner**, waste/sanitary/domestic plumbing, fire sprinkler, buried/underground.

**Bugs / gaps to fix before trusting the filter:**

- `IN_SCOPE_KEYWORDS` is defined and **never consulted**. Anything typed `duct`/`pipe`/`equipment` is priced unless an exclusion keyword hits.
- `liner` as a bare exclusion token is too broad **and** too late: liner vs wrap must be decided per duct mark from the schedule, not by grepping the whole spec.
- `hw` / `cw` as keywords will false-hit random text if you start using inclusion matching without word boundaries.
- `drain` can exclude condensate drain piping that you *do* insulate.
- Domestic hot water vs HVAC heating hot water is a **service tag** problem (`DHWxx` vs `HWS`/`HWR`), not a keyword problem.
- Concealed indoor wrap vs exposed outdoor jacket is a **location + spec table** problem. “External” in GI marketing language means “we wrap the outside of the duct,” not “outdoor only.” The current copy mixes those meanings.

Every excluded item must survive into the bid as a named exclusion (“Duct liner on SA-1 through SA-12 not included”) — not only the generic boilerplate.

### 4.7 Pricing — keep the engine, stop inventing numbers

`PricingEngine` is the right place to compute. Before it can bid commercial work:

| Change | Why |
|--------|-----|
| **Refuse missing keys** | `_calculate_insulation` does `self.prices.get(price_key, 5.0)`. That invents $5/LF. Violates the project rule. Fail the line and flag it. |
| **Size-banded keys** | ½" elastomeric on ¾" CHW is not the same money as 2" on 8" CHW. Need `{material}_{thickness}_{nps}` or a lookup table. |
| **Rectangular duct SF** | `_parse_size_to_diameter("18x12")` returns `18` and then uses `π(D+2t)/12`. Wrong. Use `2 * (W + H + 4*t) / 12 * LF` (or the shop standard you actually buy). |
| **Fitting math** | Code multiplies the **entire run** by `(1 + 0.5*elbows + 1.0*tees)`. Two elbows on 100 LF → 200 LF. The skill doc adds `0.5` LF per elbow → 101 LF. Pick one shop standard (fitting SF or published fitting chart) and test it. |
| **3M / listed wrap** | No price keys for Fire Barrier Duct Wrap or layer counts. Do not map grease duct to `mineral_wool_1.5` on a bid. |
| **Labor** | Hours are category averages (0.45 hr/LF duct). Real production varies by size, height, outdoor, occupied building. Override from a GI production-rate table, not a constant. |
| **Pricebook** | `pricebook_sample.json` is 19 demo keys. Load the live distributor book. Track quote date vs book date. |

Labor rate is hardcoded `65.0` inside `calculate_labor` and again in `generate_quote`, then overwritten in the Streamlit sidebar. One source of truth.

### 4.8 Estimator review board (mandatory)

A model must **not** emit a customer-facing bid when any of these are true:

- Drawing index lists mechanical sheets that were not downloaded or not classified
- Any in-scope system has no matched spec row
- Any measurement has `confidence < threshold` or `size` / `length` missing
- Scale missing on a plan used for geometry
- Price key missing
- Bid due date has passed
- Addendum files arrived after the takeoff snapshot

UI: spreadsheet of takeoff lines (same columns as `measurements_template.csv`, plus sheet, spec row, confidence, include/exclude). Estimator edits LF and fittings. **Then** generate the bid.

This is how you get from “5–15 minute demo” to “we will stand behind the number.”

### 4.9 Formal bid package

`generate_bid_package_text` is the right *outline*. It is not a bid a GC will accept as-is.

**Add:**

- PDF/DOCX on Guaranteed Insulation letterhead (Athens, GA; license / insurance / contact)
- **Project-specific** inclusions pulled from matched spec rows (not the same five bullets every time)
- Named exclusions from the scope filter
- Addenda acknowledged (`Addendum 1 dated …, Addendum 2 …`)
- Bid due date, project address, GC, architect/engineer
- Clarifications (“quantities from sheets M-2.01–M-2.06 Rev B; field verify”)
- Alternate prices only when requested
- Validity, exclusions, unit-price vs lump-sum statement
- Material schedule **without** distributor net cost (already noted in the workflow doc)

TXT download can stay as a debug export.

---

## 5. Flag list — what is missing for a model to bid accurately

These are the gaps that will make an automated bid wrong or incomplete. Starred items are deal-breakers.

### Intake

1. * Gmail API watcher, label, and bid-log database  
2. * Dropbox (and Box/Procore) shared-link download + folder versioning  
3. * Bid due date / timezone parsing and calendar  
4. Addendum detection on the same thread/project  
5. Domain whitelist + human confirm before download  
6. Job folder + content-hash cache (do not re-vision 200 sheets every poll)

### Documents

7. * Sheet / file classifier (index, plan, schedule, 23 07 xx, addendum)  
8. * Insulation **table** parser (thickness × size × service × location)  
9. * Duct schedule and pipe schedule parsers  
10. * Per-sheet scale + title-block sheet number  
11. Vector-path takeoff (replace Hough-line detector)  
12. Callout-to-path association (`24x16` belongs to *this* run)  
13. Matchline / enlarged-plan dedup  
14. Riser / isometric / vertical LF handling  
15. Equipment SF takeoff type  
16. Scanned vs born-digital PDF routing (OCR vs text/tables/vectors)  
17. Drawing-set page selection by sheet ID, not “first 15 pages” or “pages that say insulation”

### Scope and matching

18. * Spec row ↔ measurement match on **service + size + location**, not `system_type` only  
19. * Liner vs wrap per duct mark  
20. HVAC HW vs domestic HW via service tags  
21. Kitchen / grease listed-system detection (2-hr wrap, 3M, UL)  
22. Use inclusion rules, not “all pipes that are not sprinkler”  
23. Concealed vs exposed vs outdoor jacket rules from the spec table  
24. Underground / below-grade exclusion that does not kill condensate

### Pricing and labor

25. * No silent default unit prices  
26. * Size-banded material prices (NPS and duct width)  
27. * Correct rectangular duct area formula  
28. * One documented fitting-allowance rule, tested  
29. 3M / listed wrap product keys and layer SF  
30. GI production rates (size, height >12', outdoor, occupied)  
31. Freight, tax, bond, insurance, dumpsters, lifts, scaffolding  
32. Prevailing wage / after-hours if the ITB requires it  
33. Live distributor book dated and versioned (sample book is not bid-ready)

### Bid and QA

34. * Hard stop when takeoff is incomplete  
35. * Professional PDF/DOCX bid, project-specific scope  
36. Addenda list and revision of record  
37. Clarification / exclusion appendix generated from real gaps  
38. Estimator sign-off (name, date) before anything is emailed  
39. Ground-truth set: 3–5 **past GI jobs** with known LF, fittings, and winning/losing bid — without this you cannot tell if the model is accurate  
40. Dual-model or human spot-check on a sample of sheets (not the whole set)

### Data the model cannot invent

41. Athens-area labor burden and crew makeup  
42. Your actual buy prices and waste factors  
43. Access notes the drawings will not show (occupied hospital, night work, roof staging)  
44. GC bid form / unit-price schedule if they require *their* spreadsheet, not your TXT

---

## 6. Accuracy bugs already in the engine (fix regardless of inbox)

These will poison every bid even with perfect takeoff.

1. **Fitting multiplier vs additive allowance** — code vs skill doc disagree by roughly 2× on runs with a few elbows. See §4.7.  
2. **Rectangular duct treated as round** — `_parse_size_to_diameter` takes the first number. `18x12` jackets like an 18" round.  
3. **Invented unit price** — `prices.get(price_key, 5.0)`. Missing `fiberglass_2.5` still prices.  
4. **Unreachable / duplicate spec logic** — `_extract_special_requirements` runs one pass, then a leftover docstring, then a second pass that appends the same requirements again. Outdoor + aluminum jacket can be double-tagged.  
5. **Scope inclusion keywords unused** — `filter_specs_to_scope` / `filter_measurements_to_scope` only exclude.  
6. **Dataclass vs Pydantic split** — agent tools emit `supply_duct` / `chilled_water_pipe`; engine expects `duct` / `pipe`. Easy to drop rows on the floor.  
7. **Labor rate written three times** — engine, quote generator, Streamlit sidebar.  
8. **First-N-pages takeoff** — systematically misses the sheets that matter.

---

## 7. What to implement, in order

Do this in the existing repo. Do not start a second project folder. Do not wait on a SaaS multi-tenant roadmap (`TECHNOLOGY_ROADMAP_2025.md`) — that is a different product.

**Slice 1 — Intake that an estimator can trust**

- Gmail poller + bid log (project, due date, links, status)
- Dropbox shared-folder download into a job directory
- File classifier + sheet index
- UI: “New bids” list → open job → see files

**Slice 2 — Specs that match Division 23**

- Table extraction for 23 07 13 / 16 / 19
- Size/service/location rows
- Wire those rows through `_find_applicable_spec`
- Fail closed on missing keys

**Slice 3 — Quantities from schedules + measured paths**

- Schedule parsers
- Vector takeoff + per-sheet scale
- Review grid for the estimator
- Dedup + liner/wrap split

**Slice 4 — Pricebook and math**

- Live book, size bands, rectangular SF, one fitting rule
- 3M / listed wrap as first-class items
- Production-rate table

**Slice 5 — Bid the GC will open**

- PDF/DOCX package from `guaranteed_insulation_bid_package.py`
- Project-specific scope, addenda, clarifications
- Send only after sign-off (Gmail draft, not auto-send)

Each slice should have fixtures from **one real past job** (redact owner names if needed). Unit tests that only use `18x12` / `100 LF` will not catch takeoff failure.

---

## 8. How this maps to files you already have

| Keep / extend | Role |
|---------------|------|
| `hvac_insulation_estimator.py` | Pricing + quote dataclasses. Replace CV takeoff. Fix spec match, SF, fittings, default price. |
| `guaranteed_insulation_scope.py` | Scope rules. Use inclusion + service tags. Persist named exclusions. |
| `guaranteed_insulation_bid_package.py` | Structure is right. Add PDF/DOCX + project-specific sections. |
| `guaranteed_insulation_app.py` | Becomes the review board + bid button, not the intake front door. |
| `pydantic_models.py` | Canonical extracted objects. Align with engine types. |
| `utils_pdf.py` | Rendering + text. Add sheet-id selection; do not use insulation-keyword selection on drawings. |
| `pricebook_sample.json` | Demo only. Point production at the live book. |
| `measurements_template.csv` | Good review-grid seed. Add sheet, service, spec_id, confidence. |
| `claude_agent_tools.py` / `gemini_pdf_extractor.py` | Optional vision helpers for classification and ugly scans. Not quantity source of record. |
| `claude_workflow_enhancement.py` | Stage names are fine (`discovery` → `quote_generation`). Add intake + human gate stages. |

| Do not treat as the backbone | Why |
|------------------------------|-----|
| `Estimator_Agent_Workflow.md` Agent-Builder graph | Connectors are fictional; nodes skip schedule/vector takeoff |
| Vision “estimate LF from this page” prompts | Not measurable, not auditable |
| SaaS / multi-tenant roadmap | Does not make the next school or hospital bid accurate |

---

## 9. Success test (falsifiable)

The system is ready to draft a GI bid when, on a **held-out past job** with a known takeoff:

1. The RFQ email is triaged within minutes and the Dropbox folder is complete vs the drawing index.  
2. Every 23 07 xx insulation table row is captured with size band and location.  
3. In-scope duct/pipe LF is within **±10%** of the estimator’s marked-up takeoff (tighter on scheduled equipment).  
4. Liner-only duct is $0 in the bid and listed under exclusions.  
5. No line item uses a price key that is not in the dated pricebook.  
6. The PDF bid names the sheets, addenda, and clarifications a GC expects.  
7. A second estimator can open the review grid and see *why* each LF exists (sheet + path or schedule row).

Until (3), (4), and (5) pass, keep the model in **draft / assist** mode. Auto-sending a bid from Gmail is the last feature, not the first.
