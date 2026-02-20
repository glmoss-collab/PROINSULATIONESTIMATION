# Cursor Skill: Commercial HVAC Insulation Cost Estimation

## Purpose

Use this skill when estimating the cost of HVAC insulation for **commercial projects**. Always use the **database in the environment** (pricebook and estimation engine) to deliver the most accurate and professional quotes.

---

## Environment Database & Data Sources

### Primary price database

- **File:** `pricebook_sample.json` (project root)
- **Usage:** Load this file for all unit prices. Do **not** invent prices; use only keys present in the pricebook or the fallback defaults in `PricingEngine`.
- **Schema:** Flat key-value pairs. Keys are lowercase with underscores (e.g. `fiberglass_1.5`, `aluminum_jacket`, `mastic`).

### Price keys in the database

**Base insulation (per LF unless noted):**

| Key | Typical use |
|-----|--------------|
| `fiberglass_1.5`, `fiberglass_2.0` | Duct wrap, external duct wrap |
| `elastomeric_0.5`, `elastomeric_1.0` | Chilled water, cold piping |
| `cellular_glass_1.0` | Higher temp / specialty piping |
| `mineral_wool_1.5` | Fire-resistant, equipment, some duct |

**Facings and jacketing (per SF):**

| Key | Use |
|-----|-----|
| `fsk_facing` | Standard vapor barrier duct wrap |
| `asj_facing` | All-service jacket (indoor) |
| `aluminum_jacket` | **External duct wrap, weatherproofing, outdoor** |
| `pvc_jacket_20mil`, `pvc_jacket_30mil` | Weatherproofing, wash-down areas |
| `stainless_jacket` | Kitchen exhaust, grease duct, fireproofing exterior |

**Accessories and sealants:**

| Key | Use |
|-----|-----|
| `mastic` | Vapor seal, weather barrier (per SF) |
| `stainless_bands` | Outdoor/exterior banding (per EA) |
| `pvc_fitting_covers` | Fitting covers (per EA) |
| `adhesive`, `vapor_seal` | Adhesives and vapor seal (per gallon) |
| `metal_corner_beads`, `self_adhering_tape` | Corners and seams |

### Code that uses the database

- **`hvac_insulation_estimator.py`**
  - `PricingEngine(price_book_path="pricebook_sample.json")` loads the pricebook.
  - `_load_prices()` supports: (1) flat key→price JSON, (2) `supplier_prices` array with `key`/`supplier_price` (or `price`/`unit_price`).
  - Price keys for insulation: `{material}_{thickness}` (e.g. `fiberglass_1.5`).
  - Jacket/facing keys: `aluminum_jacket`, `fsk_facing`, `asj_facing`, `pvc_jacket_20mil`, `pvc_jacket_30mil`, `stainless_jacket`.
  - Accessories: `mastic`, `stainless_bands`, `pvc_fitting_covers`, etc.
- **`claude_agent_tools.py`** – tools that call the estimator and generate quotes.
- **`streamlit_app.py`** / **`agent_estimation_app.py`** – UIs that pass pricebook path and display quotes.

When generating or checking quotes, use these components and the same price keys so estimates stay consistent with the app.

---

## Scope of Work to Price

### 1. External duct wrap

- **Definition:** Insulation on ductwork that is exposed (interior exposed or exterior).
- **Typical spec:** Fiberglass (1.5" or 2") with FSK or ASJ (indoor) or **aluminum jacket** (outdoor/external).
- **Database usage:**
  - Insulation: `fiberglass_1.5` or `fiberglass_2.0` by linear feet (with fitting allowance).
  - Facing: `fsk_facing` or `asj_facing` by SF.
  - **Exterior/external:** Add `aluminum_jacket` (SF) and often `mastic` (SF), `stainless_bands` (EA) per project standards.
- **Labor:** Use duct insulation and jacketing rates from `PricingEngine` (or agent tools). Outdoor/external may use a labor multiplier (e.g. 1.15).

### 2. HVAC piping insulation

- **Systems:** Chilled water (CHW), hot water (HW), condenser water (CW), steam, condensate.
- **Typical materials:**
  - CHW / cold: elastomeric (`elastomeric_0.5`, `elastomeric_1.0`) or fiberglass with vapor barrier.
  - Higher temp: cellular glass (`cellular_glass_1.0`) or mineral wool (`mineral_wool_1.5`).
- **Database usage:** Price key = `{material}_{thickness}`. Add facing/jacket (FSK, ASJ, or aluminum/PVC for exterior) from pricebook.
- **Fittings:** Include fitting allowance (e.g. 1.5x for elbows, 2x for tees) and `pvc_fitting_covers` or equivalent if in scope.
- **Labor:** Pipe insulation rates from `PricingEngine`; jacketing and mastic per SF.

### 3. Kitchen exhaust / grease duct fireproofing (3M materials)

- **Definition:** Fireproofing of kitchen exhaust ducts and grease ducts (often required by code).
- **Typical products:** 3M Fire Barrier Duct Wrap, 3M Fire Protection Wrap, or equivalent listed systems.
- **Database usage:**
  - If the pricebook has 3M or fireproofing line items, use those keys.
  - If not, map to the closest available: e.g. `mineral_wool_1.5` for base insulation and **`stainless_jacket`** for exterior cladding (common for kitchen exhaust).
  - Add `mastic` and `stainless_bands` for exterior/weather exposure where applicable.
- **Quote language:** Specify "3M Fire Barrier Duct Wrap" (or exact product per spec) and note compliance (e.g. UL/listing) when you have that from specs.
- **Labor:** Use duct insulation + jacketing labor; fireproofing often has a premium (e.g. 1.2–1.25x) if not already in labor rates.

### 4. Weatherproofing exterior systems

- **Definition:** Insulation on outdoor/exterior duct, pipe, or equipment with weather barrier.
- **Typical:** Insulation (fiberglass, mineral wool, or elastomeric per spec) + **aluminum jacket** or **PVC jacket** (20 mil / 30 mil) + mastic at seams + stainless bands.
- **Database usage:**
  - Insulation: appropriate `fiberglass_*`, `elastomeric_*`, `mineral_wool_1.5`, or `cellular_glass_1.0`.
  - Jacket: `aluminum_jacket` or `pvc_jacket_20mil` / `pvc_jacket_30mil` by SF.
  - `mastic` (SF), `stainless_bands` (EA).
- **Labor:** Apply outdoor/exterior multiplier if defined in `PricingEngine` (e.g. 1.15).

### 5. Other common commercial scopes

- **Equipment:** AHUs, FCUs, boilers, chillers, tanks – use `mineral_wool_1.5` or spec’d material and matching jacket from pricebook.
- **Plenum/return ducts:** Often fiberglass with FSK or ASJ; use `fiberglass_*` and `fsk_facing` or `asj_facing`.
- **Acoustic:** Same materials; labor may include acoustic sealing (mastic/tape) from pricebook.

---

## Rules for Accurate, Professional Quotes

1. **Always use the environment database**
   - Read unit prices from `pricebook_sample.json` (or the path the app uses).
   - Use only keys that exist in the pricebook or in `PricingEngine._load_prices()` defaults.
   - Do not invent or assume prices; if a key is missing, say so and suggest adding it to the pricebook.

2. **Match spec to price keys**
   - Spec material + thickness → `{material}_{thickness}` (e.g. 1.5" fiberglass → `fiberglass_1.5`).
   - Spec facing/jacket → `fsk_facing`, `asj_facing`, `aluminum_jacket`, `pvc_jacket_20mil`, `pvc_jacket_30mil`, `stainless_jacket`.
   - Special requirements (vapor seal, outdoor, fireproofing) → `mastic`, `stainless_bands`, etc.

3. **Quantities**
   - Duct: linear feet × fitting multiplier; convert to SF for facing/jacket (circumference × length).
   - Pipe: linear feet × fitting multiplier; SF for jacket and mastic.
   - Use the same formulas as `PricingEngine` (e.g. circumference = π × (diameter + 2×thickness) / 12 for SF).

4. **Professional quote format**
   - Project name, quote number, date.
   - Line items: description, quantity, unit, unit price, total (from database).
   - Subtotal, labor (from engine or stated rate), tax if applicable, contingency (e.g. 10%), total.
   - Exclusions and assumptions (e.g. "Prices from pricebook_sample.json as of [date]").
   - For 3M kitchen exhaust: product name and compliance note.

5. **When writing or modifying code**
   - Keep `PricingEngine` and pricebook as the single source of truth.
   - Add new price keys to the JSON (or supplier_prices) rather than hardcoding.
   - Preserve support for both flat key→price and `supplier_prices` schema in `_load_prices()`.

---

## Quick reference: scope → price keys

| Scope | Insulation keys | Jacket/facing keys | Accessories |
|-------|-----------------|--------------------|-------------|
| External duct wrap | `fiberglass_1.5`, `fiberglass_2.0` | `aluminum_jacket`, `fsk_facing`, `asj_facing` | `mastic`, `stainless_bands` |
| HVAC piping | `elastomeric_0.5`, `elastomeric_1.0`, `cellular_glass_1.0`, `mineral_wool_1.5` | `fsk_facing`, `asj_facing`, `aluminum_jacket`, `pvc_jacket_*` | `mastic`, `pvc_fitting_covers` |
| Kitchen exhaust fireproofing (3M) | `mineral_wool_1.5` (or 3M key if in DB) | `stainless_jacket` | `mastic`, `stainless_bands` |
| Weatherproofing exterior | Same as duct/pipe per spec | `aluminum_jacket`, `pvc_jacket_20mil`, `pvc_jacket_30mil` | `mastic`, `stainless_bands` |

---

## Related files

- **Database:** `pricebook_sample.json`
- **Engine:** `hvac_insulation_estimator.py` – `PricingEngine`, `InsulationSpec`, `MeasurementItem`, `MaterialItem`, `QuoteGenerator`
- **Tools:** `claude_agent_tools.py` – estimation and quote tools
- **Agent:** `claude_estimation_agent.py` – orchestrator and system prompt
- **Skills:** `skills/skill.md` – full HVAC estimation skills (PDF extraction, takeoff, validation)

Use the database in the environment to deliver the most accurate and professional quotes for external duct wrap, HVAC piping insulation, kitchen exhaust fireproofing with 3M materials, weatherproofing of exterior systems, and related commercial scopes.
