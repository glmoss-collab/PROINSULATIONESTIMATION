"""Top-level pipeline: scope filter -> engine -> labor -> quote (+ optional upgrade alternatives).

``estimate()`` is THE entry point for programmatic use and what the CLI calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date as _date
from typing import Any, Dict, List, Optional

from .engine import DEFAULT_LABOR_RATE, PricingEngine
from .models import InsulationSpec, MaterialItem, MeasurementItem, ProjectQuote
from .pricebook import PriceBook
from .scope import apply_scope

DEFAULT_CONTINGENCY_PERCENT = 10.0


@dataclass
class EstimateResult:
    quote: ProjectQuote
    alternatives: Dict[str, Dict[str, float]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)  # anything a human must review before the number is used
    exclusions: List[Dict[str, str]] = field(default_factory=list)  # out-of-scope items dropped, with reasons

    @property
    def is_draft(self) -> bool:
        """True while any warning is open: unpriced lines, unmatched runs, skipped rows. Do not bid a draft."""
        return bool(self.warnings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_draft": self.is_draft,
            "warnings": self.warnings,
            "exclusions": self.exclusions,
            "alternatives": self.alternatives,
            "quote": self.quote.to_dict(),
        }


def estimate(
    project_name: str,
    measurements: List[MeasurementItem],
    specs: List[InsulationSpec],
    *,
    pricebook: Optional[PriceBook] = None,
    markup_percent: float = 0.0,
    labor_rate: float = DEFAULT_LABOR_RATE,
    contingency_percent: float = DEFAULT_CONTINGENCY_PERCENT,
    fitting_allowance_lf: Optional[Dict[str, float]] = None,
    apply_scope_filter: bool = True,
    include_alternatives: bool = True,
    extra_warnings: Optional[List[str]] = None,
    quote_number: Optional[str] = None,
    quote_date: Optional[str] = None,
) -> EstimateResult:
    """Price a takeoff. ``markup_percent`` applies to material prices only (15 -> x1.15)."""
    warnings = list(extra_warnings or [])
    exclusions: List[Dict[str, str]] = []
    if apply_scope_filter:
        specs, measurements, exclusions = apply_scope(specs, measurements)

    def make_engine() -> PricingEngine:
        return PricingEngine(pricebook, 1 + markup_percent / 100, labor_rate, fitting_allowance_lf)

    engine = make_engine()
    materials = engine.calculate_materials(measurements, specs)
    warnings.extend(engine.warnings)
    hours, labor_cost = engine.calculate_labor(materials)

    subtotal = sum(m.total_price for m in materials) + labor_cost
    total = subtotal * (1 + contingency_percent / 100)
    today = quote_date or _date.today().isoformat()
    quote = ProjectQuote(
        project_name=project_name,
        quote_number=quote_number or f"Q{today.replace('-', '')}",
        date=today,
        measurements=measurements,
        materials=materials,
        labor_hours=hours,
        labor_rate=labor_rate,
        subtotal=subtotal,
        contingency_percent=contingency_percent,
        total=total,
        notes=quote_notes(specs, measurements),
        material_list=consolidate_materials(materials),
    )
    alternatives = upgrade_alternatives(measurements, specs, make_engine) if include_alternatives else {}
    return EstimateResult(quote, alternatives, warnings, exclusions)


def quote_notes(specs: List[InsulationSpec], measurements: List[MeasurementItem]) -> List[str]:
    notes: List[str] = []
    if any(s.location == "outdoor" for s in specs):
        notes.append("Weather protection jacketing included for outdoor applications")
    if any("mastic_coating" in s.special_requirements for s in specs):
        notes.append("Vapor seal mastic coating per specifications")
    vertical = sum(m.elevation_changes for m in measurements)
    if vertical > 10:
        notes.append(f"Significant vertical work: {vertical} elevation changes")
    notes += [
        "Pricing valid for 30 days",
        "Subject to final site verification",
        "Assumes clear access to work areas",
        "All work per project specifications and applicable codes",
    ]
    return notes


def consolidate_materials(materials: List[MaterialItem]) -> List[Dict[str, Any]]:
    """Merge identical lines (same description+unit) into a distributor-ready list sorted by category."""
    merged: Dict[str, Dict[str, Any]] = {}
    for m in materials:
        row = merged.setdefault(
            f"{m.description}|{m.unit}",
            {"description": m.description, "unit": m.unit, "quantity": 0.0, "category": m.category, "total_price": 0.0},
        )
        row["quantity"] += m.quantity
        row["total_price"] += m.total_price
    return sorted(merged.values(), key=lambda r: (r["category"], r["description"]))


def upgrade_alternatives(measurements, specs, make_engine) -> Dict[str, Dict[str, float]]:
    """Price two common upgrades. An alternative is omitted if it cannot be fully priced from the price book."""
    result: Dict[str, Dict[str, float]] = {}

    def cost(kind: str, transform) -> Optional[Dict[str, float]]:
        runs = [m for m in measurements if m.system_type == kind]
        if not runs:
            return None
        base_engine, alt_engine = make_engine(), make_engine()
        base = sum(i.total_price for i in base_engine.calculate_materials(runs, specs))
        alt_specs = [transform(s) if s.system_type == kind else s for s in specs]
        alt = sum(i.total_price for i in alt_engine.calculate_materials(runs, alt_specs))
        if base_engine.warnings or alt_engine.warnings:
            return None
        return {"base_cost": base, "upgrade_cost": alt, "difference": alt - base}

    def to_pvc(s: InsulationSpec) -> InsulationSpec:
        keep = [r for r in s.special_requirements if r not in ("aluminum_jacket", "stainless_jacket", "pvc_jacket_30mil")]
        return replace(s, special_requirements=keep + ["pvc_jacket_20mil"])

    pvc = cost("pipe", to_pvc)
    if pvc:
        result["pvc_jacket_option"] = pvc
    premium = cost("duct", lambda s: replace(s, material="mineral_wool"))
    if premium:
        result["mineral_wool_duct_option"] = premium
    return result
