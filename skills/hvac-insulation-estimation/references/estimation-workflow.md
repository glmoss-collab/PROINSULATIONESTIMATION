# Estimation Workflow — Guaranteed Insulation Inc.

## End-to-End Flowchart

```
PDF Upload (specs + drawings)
        |
        v
  Extract Specifications ──> InsulationSpec[]
        |
        v
  Extract Measurements ───> MeasurementItem[]
        |
        v
  Apply Scope Filter ─────> Filtered specs & measurements
        |                    (excluded items tracked)
        v
  Calculate Materials ─────> MaterialItem[] with pricing
        |
        v
  Calculate Labor ─────────> total_hours, labor_cost
        |
        v
  Generate Quote ──────────> ProjectQuote
        |
        v
  Format Bid Package ─────> Formal text document
```

---

## Step-by-Step Detail

### 1. Extract Specifications

**Source:** Mechanical specification PDF (Division 23 — HVAC)

**Output:** List of `InsulationSpec` objects with fields:
- `system_type` — duct, pipe, or equipment
- `size_range` — e.g. "4-12 inch"
- `thickness` — inches (float)
- `material` — fiberglass, elastomeric, mineral_wool, cellular_glass
- `facing` — FSK, ASJ, or None
- `special_requirements` — list: aluminum_jacket, mastic_coating, stainless_bands, etc.
- `location` — indoor, outdoor, exposed

**Method:** `SpecificationExtractor.extract_from_pdf()` uses regex patterns
to locate insulation sections and parse material/thickness/facing data.

### 2. Extract Measurements

**Source:** Drawing PDFs or user-entered data

**Output:** List of `MeasurementItem` objects:
- `item_id` — D-1, P-2, etc.
- `system_type` — duct, pipe
- `size` — "18x12" or "2\" diameter"
- `length` — linear feet (float)
- `location` — Roof, Mechanical Room, etc.
- `elevation_changes` — count of rises/drops
- `fittings` — dict: {"elbow": 3, "tee": 1}
- `notes` — special notes list

### 3. Apply Scope Filter

**Functions:** `filter_specs_to_scope()`, `filter_measurements_to_scope()`

Removes items matching excluded keywords. Generates an exclusion summary
string for the bid package.

### 4. Calculate Materials

**Class:** `PricingEngine.calculate_materials(measurements, specs)`

For each measurement:

#### Insulation (LF)
```
base_quantity = length_ft
fitting_allowance = sum(elbow_count * 0.5 + tee_count * 1.0)
total_LF = base_quantity + fitting_allowance
price = total_LF * pricebook["{material}_{thickness}"]
```

#### Facing / Jacketing (SF)
```
diameter_inches = parse_size(measurement.size)
circumference_ft = pi * (diameter_inches + 2 * thickness_inches) / 12
total_SF = circumference_ft * length_ft
price = total_SF * pricebook["aluminum_jacket"]  # or fsk, asj, etc.
```

#### Mastic (SF)
```
total_SF = same as jacket SF
price = total_SF * pricebook["mastic"]
```

#### Accessories
```
stainless_bands_count = length_ft + 1   (one per foot plus one)
price = count * pricebook["stainless_bands"]
```

### 5. Calculate Labor

**Class:** `PricingEngine.calculate_labor(materials)`

| Material Category | Rate |
|-------------------|------|
| Duct insulation | 0.45 hr/LF |
| Pipe insulation | 0.35 hr/LF |
| Jacketing | 0.25 hr/SF |
| Mastic | 0.15 hr/SF |

```
raw_hours = sum(quantity * rate for each material category)
total_hours = raw_hours * 1.20   (20% overhead)
labor_cost = total_hours * labor_rate   (default $65/hr)
```

### 6. Generate Quote

**Class:** `QuoteGenerator.generate_quote()`

```
materials_total = sum(item.total_price for item in materials)
labor_total = total_hours * labor_rate
subtotal = materials_total + labor_total
contingency = subtotal * contingency_percent / 100
total = subtotal + contingency
```

Output: `ProjectQuote` dataclass with all fields populated.

### 7. Format Bid Package

**Function:** `generate_bid_package_text(quote, scope_exclusion_summary)`

Sections:
1. Header — company name, project, quote number, date
2. Scope of Work — inclusions and exclusions
3. Financial Breakdown — materials by category, labor, contingency, total
4. Material Schedule — line items
5. Terms and Notes — validity, field verification, code compliance

---

## Worked Example

**Project:** 100 LF of 18"x12" rectangular duct, outdoor, 1.5" fiberglass,
FSK facing, aluminum jacket, with 2 elbows.

### Materials

| Item | Calculation | Price |
|------|-------------|-------|
| Fiberglass 1.5" | 100 + (2 * 0.5) = 101 LF x $4.10 | $414.10 |
| FSK facing | circ = pi*(18+3)/12 = 5.50 ft; 5.50*100 = 550 SF x $1.10 | $605.00 |
| Aluminum jacket | 550 SF x $8.00 | $4,400.00 |
| Mastic | 550 SF x $0.65 | $357.50 |
| Stainless bands | 101 EA x $2.20 | $222.20 |
| **Materials Total** | | **$5,998.80** |

### Labor

| Category | Calculation | Hours |
|----------|-------------|-------|
| Duct insulation | 101 LF x 0.45 | 45.45 |
| Jacketing | 550 SF x 0.25 | 137.50 |
| Mastic | 550 SF x 0.15 | 82.50 |
| **Raw total** | | **265.45** |
| +20% overhead | 265.45 x 1.20 | **318.54** |
| **Labor cost** | 318.54 x $65/hr | **$20,705.10** |

### Quote Summary

| Line | Amount |
|------|--------|
| Materials | $5,998.80 |
| Labor | $20,705.10 |
| Subtotal | $26,703.90 |
| Contingency (10%) | $2,670.39 |
| **TOTAL** | **$29,374.29** |
