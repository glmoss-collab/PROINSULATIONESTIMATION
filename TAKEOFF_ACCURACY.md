# Accurate Takeoff from an Uploaded Mechanical PDF

**Assumption:** You can upload the plan set and specs yourself. Inbox / Gmail / Dropbox is out of scope.

**To run the next job the same way:** `estimates/REPEAT_TAKEOFF.md` (venv or Cursor Cloud + `scripts/inventory_mech_pdfs.py`).

**Goal:** Linear feet, sizes, fittings, and insulation rules that are close enough to bid — then the existing `PricingEngine` can price them.

This is what has to be true of the **PDF**, the **extractor**, and the **estimator review**. If any of the three is missing, the bid is a guess.

---

## 1. Short answer

An accurate takeoff is not “the model looked at the PDF.” It is this sequence, in order:

1. Split (or classify) **specs** vs **drawings** vs **schedules**.
2. Read insulation **tables** (23 07 13 / 16 / 19) into size × service × location rows.
3. Read **duct and pipe schedules** (marks, sizes, liner vs wrap, lengths if present).
4. On each plan sheet: title-block **sheet ID + scale**, then measure **vector paths** (or typed lengths), not guessed pixels.
5. Match each run to a spec row (service + size + indoor/outdoor). Apply GI scope (wrap yes, liner no).
6. Dedup floor plan vs enlarged plan vs riser vs isometric.
7. You review the takeoff grid and sign off **before** pricing.

The current upload path (`guaranteed_insulation_app.py` → Gemini/regex + Hough lines + first 15–30 pages) does **not** do steps 2–6. Do not bid from it as-is.

---

## 2. What the uploaded PDF must contain

If the file is missing these, no model can invent a reliable takeoff.

### Must have

| Item | Why |
|------|-----|
| **Mechanical drawing index** | List of M / I / FP sheets so you know if the PDF is complete |
| **Title block on every sheet** | Sheet number (`M-2.01`), title, revision, **scale** |
| **Per-sheet scale** | 1/8" plans, 1/4" enlarged rooms, NTS details — one scale for the whole PDF is wrong |
| **Division 23 insulation sections** | 23 07 13 (duct), 23 07 16 (equipment), 23 07 19 (piping) — usually **tables**, not sentences |
| **Duct schedule and/or pipe schedule** | Marks, sizes, liner/insul columns — often the real quantity source |
| **Floor / roof mechanical plans** | Runs that are not fully quantified on a schedule |
| **Service tags** | `SA`, `RA`, `EA`, `OA`, `CHWS/R`, `HWS/R`, `CWS/R`, `steam`, `condensate` |
| **Size callouts on the run** | `24x16`, `4" CHWR` next to the duct/pipe, not only in a legend |

### Strongly prefer

| Item | Why |
|------|-----|
| **Born-digital / vector PDF** (CAD plot or export) | Text and paths are selectable. Scanned/print-to-image PDFs force OCR and kill length accuracy |
| **Unflattened layers or consistent colors** | Duct vs pipe vs plumbing vs grid can be separated |
| **Insulation notes on the schedule** | `LINED` vs `WRAP` vs `INSUL` vs blank |
| **Kitchen / grease sheets** if there is a kitchen | Listed wrap (3M / UL), not fiberglass wrap |
| **Addenda / revision of record** | Takeoff the issued-for-bid set, not an old plot |
| **Spec and drawings as two files** (or one PDF with a clear index) | Combined 600-page dumps are fine only if classification works |

### Will make takeoff fail

- Scan of a paper set, or “print to PDF” that rasterizes everything
- Details marked **NTS** used as if they were to scale
- Missing mechanical sheets vs the index (you will under-bid)
- Plumbing / fire protection on the same sheets with no service tags
- Spec that says “insulate per energy code” with **no thickness table**
- Only architectural sheets (A-series) — there is nothing to take off for insulation

**Practical upload rule:** upload **two PDFs** when you can: (1) spec book or the 23 07 excerpt, (2) mechanical drawing set. One combined file is OK if the classifier can find the index and 23 07 pages. Do not upload only a cover sheet and three details.

---

## 3. What the software must do with that PDF

### 3.1 Classify every page before measuring

Do **not** send “the first 15 pages” to a vision model (`claude_agent_tools.extract_measurements` does this today). Do **not** pick drawing pages by the word “insulation” (`utils_pdf.smart_page_selection`) — plans rarely say it.

For each page, record:

- `sheet_id` (from title block)
- `sheet_title`
- `kind`: cover | index | legend | spec_230713 | spec_230716 | spec_230719 | duct_schedule | pipe_schedule | floor_plan | roof_plan | enlarged_plan | section | riser | isometric | grease | plumbing | other
- `scale` or `NTS`
- `revision`

**Gate:** if the index lists `M-2.01`–`M-2.08` and you only classified `M-2.01` and `M-2.02`, stop. The takeoff is incomplete.

### 3.2 Specs: parse tables, not slogans

Target one **rule row** per combination:

```
service + size_min + size_max + location → material, thickness, facing, jacket, specials
```

Example: `CHW | 0.5–2" | outdoor → 1.5" elastomeric + aluminum jacket + bands`.

Wire `_find_applicable_spec` to that row. Today it returns the **first spec with the same `system_type`**, so every duct gets one thickness.

Keep `section`, `page`, and raw cell text on the row so the bid can say “per 23 07 19 Table 1.”

### 3.3 Quantities: schedules first, graphics second

**Schedules (highest accuracy per hour):**

- Duct mark, WxH, length if shown, `LINED` / `WRAP` / `INSUL`
- Pipe service, NPS, insulation reference, length if shown

If `SA-1` is **lined**, do not price wrap for that mark.  
If the schedule has **no length**, the schedule still gives you *what* to insulate; LF still comes from the plan.

**Plans (only for unscheduled or unlengthed runs):**

1. Prefer **vector paths** (`page.get_drawings()` / text dicts in PyMuPDF), not Canny + HoughLinesP.
2. Associate nearby callouts (`24x16`, `4" CHWS`) with that path.
3. Convert path length with **that sheet’s** scale (title block), never page 1’s scale.
4. Count fittings from geometry or fitting symbols — do not multiply the whole run by `1 + 0.5 × elbows` unless that is your written shop rule (see §5).

Vision may say: “this is M-2.03, 1/8" = 1'-0", hydronic, these tags are CHW.”  
Vision may **not** be the source of `length: 245` unless a path or a schedule length backs it.

**Do not use** `DrawingMeasurementExtractor._detect_lines_and_measure`. It measures grids, leaders, and walls and labels them `unknown` / `TBD`.

### 3.4 Dedup (or you will double-bid)

Count a main **once** across:

- Floor plan + roof plan of the same run
- Enlarged mechanical room that also appears on the floor plan
- Isometric / riser (use for **vertical LF and fittings**, not a second copy of the floor)

### 3.5 Scope on each line, not on the whole PDF

| Decision | Source |
|----------|--------|
| Wrap vs liner | Schedule column or spec “liner” vs “wrap” **per mark** |
| HVAC vs domestic / waste / sprinkler | Service tag (`HWS` vs `DHW`, `CHW` vs `CW` condenser vs domestic) |
| Indoor wrap vs outdoor jacket | Spec table + sheet location (roof, yard, penthouse) |
| Kitchen grease | Grease/kitchen sheets + listed-system spec — not `mineral_wool_1.5` by default |
| Equipment | Surface area (SF), not LF — `MeasurementItem` cannot store this today |

`IN_SCOPE_KEYWORDS` in `guaranteed_insulation_scope.py` are **never used**. The filter only drops exclusion words. A pipe tagged `pipe` with no “sprinkler” in the notes will be priced.

### 3.6 Match spec → measurement before pricing

Each takeoff line needs:

- `sheet_id`
- `service`
- `size`
- `length_lf` (and how it was obtained: schedule | vector | typed)
- `location`
- `spec_row_id`
- `in_scope` + reason
- `confidence`

No `spec_row_id` → do not price that line. Missing pricebook key → **fail the line**, do not use `$5.00` (`PricingEngine._calculate_insulation` does that today).

---

## 4. Hard gates before you generate a bid

Block pricing unless all of these pass:

1. Drawing index reconciled — every in-scope mechanical sheet is present and classified.
2. At least one insulation table row exists for each in-scope **service** on the drawings.
3. Every priced line has size, LF > 0, spec row, and a real pricebook key.
4. Every plan used for geometry has a parsed scale (not NTS, not “default 48”).
5. Liner-only marks are $0 and listed as exclusions.
6. Rectangular duct SF uses perimeter, not “first number as diameter.”
7. You have reviewed the takeoff grid (or accepted a typed/manual takeoff).

Until those pass, the app should show a **draft takeoff**, not a bid total.

---

## 5. Math the engine must get right (or LF is wasted)

These are independent of PDF quality. They are wrong in the current calculator.

| Issue | Current behavior | What you need |
|-------|------------------|---------------|
| Rectangular duct area | `"18x12"` → diameter `18` → `π(D+2t)/12 × LF` | `2 × (W + H + 4t) / 12 × LF` (or your shop formula) |
| Fittings | `LF × (1 + 0.5×elbows + 1.0×tees)` → 2 elbows on 100 LF = **200 LF** | One written rule: additive LF, fitting SF chart, or published fitting allowance — and tests |
| Missing price key | `prices.get(key, 5.0)` invents $5/LF | Skip + flag |
| Spec match | First `duct` spec wins | Size band + location + service |
| Labor rate | Hardcoded `$65` in two places, then overwritten in the UI | One source |

Equipment and 3M listed wrap need their own quantity types (SF × layers), not a duct LF key.

---

## 6. What you (the estimator) still have to do

Upload does not remove judgment. On every job, check:

1. **Completeness** — index vs files; addenda after the plot date.
2. **Liner vs wrap** — a model will miss “1" lining” in a note and wrap the same duct.
3. **Outdoor / roof** — aluminum jacket and bands only where the spec table says so.
4. **Domestic vs HVAC** on M sheets — especially “HW” without a service prefix.
5. **Verticals** — shafts and risers are easy to miss or double-count.
6. **Access** — occupied building, height, night work: not on the PDF; adjust labor yourself.
7. **Spot-check** 2–3 long runs with a scale ruler or CAD measure. If those are off by more than ~10%, the whole takeoff is untrusted.

Keep `measurements_template.csv` (or the review grid) as the place you correct LF and fittings. The bid should come from **that** table, not from raw model JSON.

---

## 7. What “accurate” means (so you can test it)

Pick one **past GI job** you already took off by hand. Upload the same PDFs. Compare:

| Check | Pass |
|-------|------|
| In-scope duct + pipe LF | within **±10%** of your marked takeoff (tighter if a schedule had lengths) |
| Liner-only duct | $0, named on the exclusion list |
| Outdoor jacket SF | present only on outdoor/exposed rows |
| Price keys | 100% from the dated pricebook |
| Missing sheets | flagged, not silently skipped |

If you do not have a past job to compare, you cannot know whether the extractor is accurate. Demo numbers (`100 LF` of `12"`) do not count.

---

## 8. Minimum build vs current upload app

`guaranteed_insulation_app.py` today: upload spec PDF + optional drawing PDF → Gemini or regex → scope keyword strip → price → TXT bid.

**Replace the middle with:**

| Build | Replaces |
|-------|----------|
| Page/sheet classifier + index reconcile | First-N-pages + insulation-keyword page pick |
| Table extract for 23 07 xx | Sentence regex / unstructured vision JSON |
| Schedule extract | “Estimate all visible ductwork” prompt |
| Vector path + callout + per-sheet scale | Hough lines and vision-guessed LF |
| Spec-row match + liner/wrap flag | `_find_applicable_spec` by `system_type` |
| Takeoff review table (edit LF, exclude lines) | Immediate “Generate formal bid package” |
| Fail closed on missing key / missing scale | `$5` default and `scale = 48` |

Keep `PricingEngine`, `ProjectQuote`, and the GI bid outline. They are downstream of a correct takeoff, not a substitute for one.

---

## 9. Upload checklist (print this)

Before you process a job:

- [ ] Issued-for-bid mechanical set (revision matches addenda)
- [ ] Drawing index present; page count matches listed M/I sheets
- [ ] Spec includes 23 07 13 / 16 / 19 (or a project insulation schedule)
- [ ] Duct and/or pipe schedule included when the set has one
- [ ] PDF is vector/text, not a scan (or you accept OCR + manual takeoff)
- [ ] Spec PDF and drawing PDF uploaded separately if the book is huge
- [ ] After extract: every plan sheet has a scale; every priced line has a spec row
- [ ] You edited the takeoff grid and spot-checked three runs
- [ ] Then — and only then — run pricing
