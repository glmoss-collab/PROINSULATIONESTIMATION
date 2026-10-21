"""Self-describing manifest + single-file bundle for AI bots. Generated from the code, so it cannot drift.

``MANIFEST.json`` in this folder is the committed output of ``python -m local_estimator describe``; a test fails if stale.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
from pathlib import Path
from typing import Any, Dict, List

from . import __version__
from .engine import (DEFAULT_FITTING_ALLOWANCE_LF, DEFAULT_LABOR_HOURS_PER_UNIT, DEFAULT_LABOR_RATE, JACKET_REQUIREMENTS,
                     LABOR_OVERHEAD, SUPPORTED_SYSTEMS)
from .loaders import FITTING_COLUMNS, MEASUREMENT_ALIASES
from .models import InsulationSpec, MaterialItem, MeasurementItem, ProjectQuote
from .pricebook import DEFAULT_PRICES
from .scope import EXCLUDED_KEYWORDS

PKG = Path(__file__).resolve().parent
# (module, role) in reading order - this IS the navigation map.
MODULES = [
    ("models", "Data contracts (dataclasses)"),
    ("sizes", "Parse sizes/lengths, surface-area geometry"),
    ("pricebook", "Price book + key naming convention"),
    ("engine", "Quantities, pricing, labor (the core)"),
    ("scope", "Company exclusions (what we do not bid)"),
    ("spec_text", "Plain-text spec -> InsulationSpec (best effort)"),
    ("loaders", "CSV/JSON/Bluebeam-style rows -> models"),
    ("quote", "Pipeline entry point estimate(), quote assembly, alternatives"),
    ("report", "Bid text, JSON, material CSV"),
    ("cli", "Command line"),
    ("manifest", "This manifest + AI bundle"),
]


def _summary(obj: Any) -> str:
    doc = inspect.getdoc(obj) or ""
    return doc.split("\n\n")[0].replace("\n", " ")


def _public(module_name: str) -> List[Dict[str, str]]:
    module = importlib.import_module(f"{__package__}.{module_name}")
    items = []
    for name, obj in inspect.getmembers(module):
        if name.startswith("_") or getattr(obj, "__module__", None) != module.__name__:
            continue
        if inspect.isfunction(obj):
            items.append({"name": name, "kind": "function", "signature": f"{name}{inspect.signature(obj)}", "summary": _summary(obj)})
        elif inspect.isclass(obj):
            items.append({"name": name, "kind": "class", "summary": _summary(obj)})
    return items


def _schema(cls: Any) -> Dict[str, str]:
    return {f.name: str(f.type) for f in dataclasses.fields(cls)}


def build_manifest() -> Dict[str, Any]:
    return {
        "package": "local_estimator",
        "version": __version__,
        "purpose": "Offline HVAC insulation takeoff pricing: measurements + specs + price book -> priced quote.",
        "constraints": ["Python standard library only", "no network", "no AI/API calls", "Python >= 3.9"],
        "read_first": ["AI_CONTEXT.md", "README.md", "MANIFEST.json"],
        "entry_points": {
            "python": "from local_estimator import estimate, load_measurements, load_specs",
            "cli": ["python -m local_estimator demo", "python -m local_estimator estimate --measurements M.csv --specs S.csv",
                    "python -m local_estimator describe", "python -m local_estimator bundle"],
        },
        "modules": [{"module": f"{name}.py", "role": role, "public": _public(name)} for name, role in MODULES],
        "schemas": {c.__name__: _schema(c) for c in (InsulationSpec, MeasurementItem, MaterialItem, ProjectQuote)},
        "inputs": {
            "measurement_columns_and_aliases": {k: list(v) for k, v in MEASUREMENT_ALIASES.items()},
            "fitting_columns": FITTING_COLUMNS,
            "spec_table_columns": ["system_type", "size_range", "thickness", "material", "facing", "special_requirements (; separated)", "location"],
            "price_book_keys_default": sorted(DEFAULT_PRICES),
        },
        "assumptions_to_review": {
            "fitting_allowance_lf_placeholder": DEFAULT_FITTING_ALLOWANCE_LF,
            "labor_hours_per_unit": DEFAULT_LABOR_HOURS_PER_UNIT,
            "labor_overhead_multiplier": LABOR_OVERHEAD,
            "default_labor_rate_usd_per_hour": DEFAULT_LABOR_RATE,
            "supported_systems": list(SUPPORTED_SYSTEMS),
            "jacket_requirement_precedence": list(JACKET_REQUIREMENTS),
            "scope_excluded_keywords": EXCLUDED_KEYWORDS,
        },
        "data_files": sorted(p.name for p in (PKG / "data").iterdir()),
    }


def render_manifest() -> str:
    return json.dumps(build_manifest(), indent=2, sort_keys=False)


def render_bundle() -> str:
    """One text document: docs, manifest, source, data, tests. Paste into a chat with an AI that cannot read your files."""
    parts: List[str] = []

    def add(title: str, body: str) -> None:
        parts.append(f"\n{'=' * 100}\nFILE: {title}\n{'=' * 100}\n{body}")

    for doc in ("AI_CONTEXT.md", "README.md"):
        if (PKG / doc).exists():
            add(doc, (PKG / doc).read_text(encoding="utf-8"))
    add("MANIFEST.json (generated)", render_manifest())
    for name in ["__init__"] + [m for m, _ in MODULES]:
        add(f"{name}.py", (PKG / f"{name}.py").read_text(encoding="utf-8"))
    for path in sorted((PKG / "data").iterdir()):
        add(f"data/{path.name}", path.read_text(encoding="utf-8"))
    for path in sorted((PKG / "tests").glob("test_*.py")):
        add(f"tests/{path.name}", path.read_text(encoding="utf-8"))
    return "local_estimator - complete source bundle\n" + "".join(parts)
