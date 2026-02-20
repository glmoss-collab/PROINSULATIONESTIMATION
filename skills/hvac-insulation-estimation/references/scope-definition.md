# Scope Definition — Guaranteed Insulation Inc.

## Company

- **Name:** Guaranteed Insulation Inc.
- **Location:** Athens, GA
- **Scope:** External HVAC and mechanical insulation only

---

## In-Scope System Types

Only items with one of these system types are considered:

```
duct | pipe | equipment
```

## In-Scope Keywords

Items matching any of these keywords (case-insensitive) are candidates for
pricing. The item must also pass the exclusion filter below.

```
duct wrap          ductwork           supply duct        return duct
exhaust duct       external duct      exterior duct      outdoor duct
chilled water      hot water          condenser water    chw
hw                 cw                 steam              condensate
hvac piping        mechanical piping  equipment insulation
ahu                fcu                boiler             chiller
tank               kitchen exhaust    grease duct        fireproofing
weatherproof       aluminum jacket    pvc jacket         external
exterior           exposed
```

---

## Excluded Keywords

Items matching any of these keywords are **removed** from the estimate,
regardless of system type:

```
duct liner         liner              internal liner     acoustic liner
waste              sanitary           domestic water     plumbing
drain              sewer              fire sprinkler     sprinkler pipe
fire protection pipe                  underground        buried
below grade
```

## Additional Exclusion Notes

Specs with any of these in their notes field are also excluded:

```
liner | internal | acoustic only | waste | plumbing | sprinkler
```

## Special Rule

If `system_type == "duct"` and the word `liner` appears anywhere in the
combined text (type + size range + notes), the item is excluded.

---

## Scope Filter Functions

Source: `guaranteed_insulation_scope.py`

| Function | Purpose |
|----------|---------|
| `filter_specs_to_scope(specs)` | Remove out-of-scope `InsulationSpec` items |
| `filter_measurements_to_scope(measurements)` | Remove out-of-scope `MeasurementItem` items |
| `get_scope_exclusion_summary(before, after)` | Generate one-line exclusion summary for bid |

---

## Bid Package Exclusion Statement

The formal bid package always includes this exclusion block:

> **Exclusions (not included in this bid):**
> - Duct liner and internal acoustic liner
> - Waste, sanitary, or domestic plumbing insulation
> - Fire sprinkler piping (non-mechanical)
> - Any scope not explicitly listed above
