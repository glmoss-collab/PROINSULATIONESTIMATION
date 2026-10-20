# AI_CONTEXT - local_estimator

Audience: an AI assistant (Claude, Gemini, Grok, GPT, ...) asked to run, debug or extend this package. Read this file first,
then `MANIFEST.json` (generated, exact signatures), then the one module you need. Everything is plain Python stdlib.
`python -m local_estimator bundle` prints docs + manifest + all source in one text blob if you cannot read files.

## 1. What it is (and is not)

Prices a **takeoff**: given runs of duct/pipe (size, length, fittings, location), an insulation **spec table** and a **price
book**, it produces material lines, labor, contingency and a bid. It does **not** read PDFs, measure drawings, call AI, or use
the network. Domain: commercial mechanical (HVAC) insulation for Guaranteed Insulation Inc.; external HVAC scope only.

## 2. Pipeline (single path - follow it when debugging)

```
loaders.load_measurements / load_specs / spec_text.extract_specs_from_text      -> models
quote.estimate():
   scope.apply_scope()                    drop out-of-scope specs/runs (reason recorded)
   engine.PricingEngine.calculate_materials()   per run: find_spec -> insulation -> jacket -> mastic -> accessories
   engine.PricingEngine.calculate_labor()
   subtotal = materials + labor ;  total = subtotal x (1 + contingency%)
   quote.upgrade_alternatives()           optional upgrade pricing (skipped if not fully priceable)
report.render_bid_text / render_json / render_material_csv
```

## 3. Data contracts (`models.py`) - units: feet for length, inches for size/thickness, USD

- `InsulationSpec(system_type, size_range, thickness, material, facing, special_requirements, location)`
- `MeasurementItem(item_id, system_type, size, length, location, elevation_changes, fittings{kind:count}, notes)`
- `MaterialItem(description, unit, quantity, unit_price, total_price, category, system_type, item_id)`
- `ProjectQuote(...)`; `EstimateResult(quote, alternatives, warnings, exclusions)` with `.is_draft` (= any warning).

## 4. Formulas (`engine.py`, `sizes.py`)

| Quantity | Formula |
|---|---|
| Insulated length | `length + Σ count × fitting_allowance_lf[kind]` (additive; default elbow 1.5, tee 2.5 - **placeholder**) |
| Insulation $ | `insulated_length × pricebook["<material>_<thickness>"] × markup` |
| Round / pipe area (SF) | `π (D + 2t) / 12 × insulated_length` |
| Rectangular duct area (SF) | `2 (W + H + 4t) / 12 × insulated_length` |
| Jacket / facing $ | `area × pricebook[key] × markup`; key = first of `aluminum_jacket, stainless_jacket, pvc_jacket_30mil, pvc_jacket_20mil` found in `special_requirements`, else `"<facing>_facing"`; none if unfaced |
| Mastic $ | only if `"mastic_coating"` in requirements: `area × pricebook["mastic"]` |
| Bands | only if `"stainless_bands"`: `int(length)+1` each (one per foot of run) |
| Labor hours | `(Σ insulation_qty × 0.45 duct | 0.35 pipe  +  Σ jacket_SF × 0.25  +  Σ mastic_SF × 0.15) × 1.20`; cost = hours × `labor_rate` (default $65) |
| Total | `(materials + labor) × (1 + contingency%)`, contingency default 10% |
| Markup | `markup_percent` applies to **material prices only** |

Spec matching (`PricingEngine.find_spec`): same `system_type`; spec `size_range` must contain the run's *nominal* size
(diameter, or the larger rectangle side) - a range that cannot be parsed (e.g. `all`) matches anything but ranks below an explicit hit;
then the spec whose `location` (indoor/outdoor) matches the run's `location` text (`classify_location`: roof/exterior/exposed/outdoor ⇒ outdoor); then file order.

## 5. Invariants - do not break these

1. **Never invent a number.** Missing price key, unparseable size, unsupported system type, zero length, unmatched spec,
   unknown fitting ⇒ a `warnings` entry and (for price keys) a `[UNPRICED]` $0 line. `is_draft` stays true until fixed.
2. **Fittings add length; they never multiply it.**
3. **Rectangular ducts use perimeter, not a diameter.**
4. **Stdlib only.** `tests/test_pipeline.py::Hygiene` fails on any third-party import.
5. **Nothing is silently dropped.** Skipped CSV rows → load warnings; scope exclusions → `result.exclusions` with reasons.
6. Keep `MANIFEST.json` current: `python -m local_estimator describe > local_estimator/MANIFEST.json` (a test enforces it).

## 6. Recipes

- **New material/thickness**: add price key `"<material>_<thickness>"` to the price book (`pricebook.py` doc has the convention). No code change.
- **New jacket type**: add its key to `JACKET_REQUIREMENTS` (`engine.py`) and the price book.
- **New fitting type**: add to `DEFAULT_FITTING_ALLOWANCE_LF` (or pass `fitting_allowance_lf=`) and, if it comes from a CSV column, to `FITTING_COLUMNS` (`loaders.py`).
- **Change labor**: pass `labor_hours_per_unit={...}` / `labor_rate=` to `PricingEngine`, or edit `DEFAULT_LABOR_HOURS_PER_UNIT`.
- **Change scope exclusions**: edit `EXCLUDED_KEYWORDS` (`scope.py`) or pass `apply_scope_filter=False`.
- **New input column alias** (e.g. a real Bluebeam export): `MEASUREMENT_ALIASES` in `loaders.py`.
- **Equipment (AHUs, tanks)**: unsupported. Needs a surface-area quantity type (SF), not LF - new model field + engine branch + tests.
- Always add a test in `tests/` and regenerate the manifest.

## 7. Known limitations / open decisions (be honest about these when giving numbers)

1. **Labor model is inherited and unvalidated.** Jacket/facing SF is charged 0.25 h/SF *in addition to* insulation LF hours, including
   factory-applied FSK/ASJ facing - likely double counting. Sample output: labor ≈ 9× materials. Calibrate against a past job.
2. **Fitting allowance is a placeholder** (elbow 1.5 LF, tee 2.5 LF); other fittings (valve, flange, reducer) default to *no* allowance and warn.
3. **No drawing measurement.** Lengths come from the takeoff (Bluebeam, CSV, hand). Per-sheet scale, vector measurement, sheet classification, duplicate-run removal (floor vs riser vs enlarged plan) are out of scope - see root `TAKEOFF_ACCURACY.md`.
4. **Bluebeam column names are a guess** about the CSV layout; verify with a real export.
5. **Scope filter is keyword-based**; `drain` also drops insulated HVAC condensate drains. Review `result.exclusions`.
6. **Text-spec parsing is best effort** (one sentence = one spec; needs system + thickness + material together). Prefer a spec table.
7. **Indoor/outdoor** is inferred from free text; a run on a roof not labeled so is priced as indoor.
8. Price keys must match thickness spelling (`1.5`, `1.50`, `1` are all tried); other mismatches are flagged, not guessed.
9. Contingency, quote number format and the 30-day validity note are defaults, not policy.

## 8. Prompting tips

- "Run `python -m local_estimator demo` and show me the warnings" - fastest health check.
- Give the AI `bundle.txt` plus your CSVs; ask it to explain any line using sections 3-4 and `item_id` (every material line carries its source `item_id`).
- When asking for changes, name the invariant(s) from section 5 that must still hold.
