# local_estimator

Offline HVAC insulation estimating. **Python standard library only** - no `pip install`, no Streamlit, no PDF/AI libraries,
no network, no API keys. Runs anywhere Python 3.9+ runs (verified with site-packages disabled: `python -S`).

```
takeoff (CSV / JSON / Bluebeam export)  ─┐
spec table (CSV / JSON) or spec text     ─┼─►  estimate()  ─►  priced quote  ─►  bid.txt · estimate.json · material_list.csv
price book (JSON, optional)              ─┘        │
                                                   └─► warnings → result is a DRAFT until every one is cleared
```

## Run it (from the repo root, the folder that contains `local_estimator/`)

```bash
python -m local_estimator demo                                   # smoke test on bundled sample data
python -m local_estimator estimate \
    --measurements my_takeoff.csv --specs my_specs.csv \
    --pricebook my_prices.json --project "Acme HQ" \
    --markup-percent 15 --labor-rate 65 --out-dir out/           # writes bid.txt, estimate.json, material_list.csv
python -m local_estimator estimate --measurements t.csv --spec-text spec_excerpt.txt   # best-effort text spec
python -m local_estimator describe                               # machine-readable manifest (JSON)
python -m local_estimator bundle > bundle.txt                    # ALL docs + source in one file for an AI chat
python -m unittest discover -s local_estimator/tests -t .        # tests (pytest also works)
```

Exit code is **0** when the estimate is clean and **1** when it is a draft (something unpriced/unmatched/skipped).

As a library:

```python
from local_estimator import estimate, load_measurements, load_specs, PriceBook, render_bid_text

measurements, load_warnings = load_measurements("my_takeoff.csv")
result = estimate("Acme HQ", measurements, load_specs("my_specs.csv"),
                  pricebook=PriceBook.load("my_prices.json"), markup_percent=15,
                  extra_warnings=load_warnings)
print(result.quote.total, result.is_draft, result.warnings)
print(render_bid_text(result))
```

## Where things are

| File | Job |
|---|---|
| `models.py` | The 4 dataclasses everything passes around |
| `sizes.py` | `18x12`, `1-1/2"`, `125' 6"` parsing; surface-area geometry |
| `pricebook.py` | Price book loading + the key naming convention |
| `engine.py` | **The core**: spec matching, quantities, pricing, labor |
| `scope.py` | Company exclusions (liner, waste plumbing, sprinkler, buried) with reasons |
| `spec_text.py` | Plain-text spec → specs (best effort) |
| `loaders.py` | CSV/JSON/Bluebeam-style rows → models |
| `quote.py` | `estimate()` pipeline, quote assembly, upgrade alternatives |
| `report.py` | Text bid / JSON / material CSV |
| `cli.py`, `__main__.py` | Command line |
| `manifest.py` | Generates `MANIFEST.json` and the AI bundle |
| `data/` | Sample takeoff, specs, price book, Bluebeam-style CSV, spec text |
| `tests/` | 23 `unittest` tests incl. "stdlib-only" and "manifest not stale" guards |

## Input formats

**Takeoff** (`data/measurements_template.csv`): `item_id, system_type, size, length, location, elbows, tees`.
Sizes: `18x12` (rect duct) or `4"` / `1-1/2"` (round/pipe). Lengths: feet (`125.5`, `1,250 ft`, `125' 6"`).
Bluebeam-style exports work too (`data/bluebeam_export_example.csv`): columns are matched by alias and a missing
`system_type`/`size` is inferred from the label/comments (`24x16 supply duct`). *The aliases are an informed guess at
Bluebeam's CSV layout - check against a real export and extend `MEASUREMENT_ALIASES` in `loaders.py` if needed.*

**Specs** (`data/specs_example.csv`): `system_type, size_range, thickness, material, facing, special_requirements, location`
(`special_requirements` is `;`-separated, e.g. `aluminum_jacket;stainless_bands`).

**Price book** (`data/pricebook_sample.json`): flat `{ "fiberglass_1.5": 4.10, "fsk_facing": 1.10, ... }`.
Key convention is documented at the top of `pricebook.py`.

## Read before trusting a number

Open decisions are listed in `AI_CONTEXT.md` § "Known limitations". The two that move dollars most:
the **labor rates are inherited and unvalidated** (the facing double count is fixed; sample labor is still ≈ 2.9× materials),
and the **fitting allowance
(1.5 LF elbow / 2.5 LF tee) is a placeholder**. This package prices a takeoff; it does not measure drawings.

*Extracted from the root-level modules (`hvac_insulation_estimator.py`, `guaranteed_insulation_*.py`), which are unchanged.*
