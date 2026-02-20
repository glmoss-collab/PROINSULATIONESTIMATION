# Pricebook Schema — Guaranteed Insulation Inc.

## File Location

`pricebook_sample.json` in the project root.

## Format

Flat JSON object with `key → unit_price` pairs:

```json
{
  "fiberglass_1.5": 4.10,
  "aluminum_jacket": 8.00,
  "mastic": 0.65
}
```

An alternative `supplier_prices` array format is also supported by
`PricingEngine._load_prices()`:

```json
{
  "supplier_prices": [
    { "key": "fiberglass_1.5", "supplier_price": 4.10 }
  ]
}
```

---

## Complete Price Key Reference

### Base Insulation (per Linear Foot)

| Key | Price | Typical Application |
|-----|-------|---------------------|
| `fiberglass_1.5` | $4.10/LF | 1.5" duct wrap, standard external duct |
| `fiberglass_2.0` | $5.25/LF | 2.0" duct wrap, higher-R external duct |
| `elastomeric_0.5` | $2.95/LF | 0.5" pipe insulation (small CHW piping) |
| `elastomeric_1.0` | $4.10/LF | 1.0" pipe insulation (CHW, cold piping) |
| `cellular_glass_1.0` | $6.25/LF | 1.0" high-temp or specialty piping |
| `mineral_wool_1.5` | $4.85/LF | 1.5" fire-resistant, equipment, kitchen exhaust |

### Facings and Jacketing (per Square Foot)

| Key | Price | Typical Application |
|-----|-------|---------------------|
| `fsk_facing` | $1.10/SF | Foil-scrim-kraft, indoor duct vapor barrier |
| `asj_facing` | $1.60/SF | All-service jacket, indoor pipe/duct |
| `aluminum_jacket` | $8.00/SF | Outdoor/external weatherproofing |
| `pvc_jacket_20mil` | $3.40/SF | 20-mil PVC, wash-down areas |
| `pvc_jacket_30mil` | $4.10/SF | 30-mil PVC, heavy-duty exterior |
| `stainless_jacket` | $12.00/SF | Kitchen exhaust, grease duct, fireproofing |

### Accessories and Sealants

| Key | Price | Unit | Typical Application |
|-----|-------|------|---------------------|
| `mastic` | $0.65 | SF | Vapor seal coating, weather barrier |
| `stainless_bands` | $2.20 | EA | Outdoor/exterior banding |
| `pvc_fitting_covers` | $7.90 | EA | Pre-formed fitting covers |
| `adhesive` | $11.80 | GAL | Contact adhesive |
| `vapor_seal` | $14.00 | GAL | Vapor seal coating |
| `metal_corner_beads` | $1.10 | LF | Corner protection |
| `self_adhering_tape` | $0.40 | LF | Seam tape |

---

## Key Naming Convention

- **Insulation:** `{material}_{thickness}` — e.g. `fiberglass_1.5`
- **Facings/jackets:** full descriptive name — e.g. `aluminum_jacket`
- **Accessories:** full name — e.g. `stainless_bands`

All keys are **lowercase with underscores**. Thickness is in inches with one
decimal place.

---

## Adding New Price Keys

1. Add the key-value pair to `pricebook_sample.json`
2. Follow the naming convention above
3. The `PricingEngine` will pick it up automatically on next load
4. No code changes needed unless the material requires a new calculation path

---

## Scope-to-Key Quick Reference

| Scope | Insulation | Jacket / Facing | Accessories |
|-------|-----------|-----------------|-------------|
| External duct wrap | `fiberglass_1.5` or `_2.0` | `aluminum_jacket` (outdoor), `fsk_facing`/`asj_facing` (indoor) | `mastic`, `stainless_bands` |
| HVAC piping (CHW/HW/CW) | `elastomeric_0.5` or `_1.0` | `fsk_facing`, `asj_facing`, `pvc_jacket_*` | `mastic`, `pvc_fitting_covers` |
| Steam / high-temp | `cellular_glass_1.0`, `mineral_wool_1.5` | `aluminum_jacket` | `mastic`, `stainless_bands` |
| Kitchen exhaust | `mineral_wool_1.5` | `stainless_jacket` | `mastic`, `stainless_bands` |
| Weatherproofing | per spec | `aluminum_jacket`, `pvc_jacket_*` | `mastic`, `stainless_bands` |
