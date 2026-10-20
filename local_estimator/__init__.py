"""local_estimator - offline HVAC insulation estimating. Python stdlib only; no installs, no network, no AI calls.

Start here:  README.md (humans) / AI_CONTEXT.md (AI bots) / MANIFEST.json (machine-readable map).
Public API (everything else is internal):
"""

from .engine import PricingEngine
from .loaders import load_measurements, load_specs, measurements_from_rows
from .models import InsulationSpec, MaterialItem, MeasurementItem, ProjectQuote
from .pricebook import PriceBook
from .quote import EstimateResult, estimate
from .report import render_bid_text, render_json, render_material_csv
from .scope import apply_scope
from .spec_text import extract_specs_from_text

__version__ = "1.0.0"
__all__ = [
    "estimate", "EstimateResult", "PricingEngine", "PriceBook",
    "InsulationSpec", "MeasurementItem", "MaterialItem", "ProjectQuote",
    "load_measurements", "load_specs", "measurements_from_rows", "extract_specs_from_text", "apply_scope",
    "render_bid_text", "render_json", "render_material_csv",
]
