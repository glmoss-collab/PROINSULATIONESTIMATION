"""Quantity, pricing and labor engine (the core of the estimator).

Flow per MeasurementItem:  match spec -> insulation LF -> jacket/facing SF -> mastic SF -> accessories -> labor.

Rules that matter (each has a test in tests/test_engine.py):
  * Spec match: same system_type; size band must contain the run's nominal size; indoor/outdoor preferred; else first.
  * Fittings ADD length (``fitting_allowance_lf``) - they never multiply the run.
  * Rectangular duct area uses the perimeter 2(W+H+4t), round/pipe uses pi(D+2t).
  * Nothing is guessed: a missing price key, unparseable size or unsupported system type yields a flagged line or a
    warning in ``engine.warnings`` - never an invented number.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from .models import InsulationSpec, MaterialItem, MeasurementItem
from .pricebook import PriceBook, normalize_key
from .sizes import classify_location, parse_size, parse_size_range, surface_area_sf

logger = logging.getLogger(__name__)

SUPPORTED_SYSTEMS = ("duct", "pipe")  # equipment needs surface-area quantities, not LF - not supported yet
JACKET_REQUIREMENTS = ("aluminum_jacket", "stainless_jacket", "pvc_jacket_30mil", "pvc_jacket_20mil")  # precedence order
NO_FACING = {"", "none", "unfaced", "null"}

# Extra insulated LF per fitting. PLACEHOLDER shop rule - replace with your fitting allowance chart.
DEFAULT_FITTING_ALLOWANCE_LF: Dict[str, float] = {"elbow": 1.5, "tee": 2.5}
DEFAULT_LABOR_RATE = 65.0  # $/hr
DEFAULT_LABOR_HOURS_PER_UNIT = {"duct_insulation": 0.45, "pipe_insulation": 0.35, "jacketing": 0.25, "mastic": 0.15}
LABOR_OVERHEAD = 1.20  # setup, cleanup, supervision


class PricingEngine:
    def __init__(
        self,
        pricebook: Optional[PriceBook] = None,
        markup: float = 1.0,
        labor_rate: float = DEFAULT_LABOR_RATE,
        fitting_allowance_lf: Optional[Dict[str, float]] = None,
        labor_hours_per_unit: Optional[Dict[str, float]] = None,
    ) -> None:
        self.pricebook = pricebook or PriceBook()
        self.markup = markup  # multiplier on material prices (1.15 = +15%)
        self.labor_rate = labor_rate
        self.fitting_allowance_lf = {**DEFAULT_FITTING_ALLOWANCE_LF, **(fitting_allowance_lf or {})}
        self.labor_hours_per_unit = {**DEFAULT_LABOR_HOURS_PER_UNIT, **(labor_hours_per_unit or {})}
        self.warnings: List[str] = []  # reset on every calculate_materials()

    # ------------------------------------------------------------------ public

    def calculate_materials(self, measurements: List[MeasurementItem], specs: List[InsulationSpec]) -> List[MaterialItem]:
        self.warnings = []
        materials: List[MaterialItem] = []
        for m in measurements:
            problem = self._precheck(m)
            if problem:
                self.warnings.append(f"{m.item_id}: {problem} - not priced")
                continue
            spec = self.find_spec(m, specs)
            if spec is None:
                self.warnings.append(
                    f"{m.item_id}: no specification matches {m.system_type} '{m.size}' ({m.location}) - not priced"
                )
                continue
            materials.append(self._insulation_line(m, spec))
            if self._jacket_key(spec):
                materials.append(self._jacket_line(m, spec))
            if "mastic_coating" in spec.special_requirements:
                materials.append(self._mastic_line(m, spec))
            materials.extend(self._accessory_lines(m, spec))
        return materials

    def calculate_labor(self, materials: List[MaterialItem]) -> Tuple[float, float]:
        """(hours, dollars). Insulation hours/LF by system type; jacket and mastic hours/SF; +20% overhead."""
        hours = 0.0
        rates = self.labor_hours_per_unit
        for item in materials:
            if item.category == "insulation":
                hours += item.quantity * rates["duct_insulation" if item.system_type == "duct" else "pipe_insulation"]
            elif item.category == "jacket":
                hours += item.quantity * rates["jacketing"]
            elif item.category == "mastic":
                hours += item.quantity * rates["mastic"]
        hours *= LABOR_OVERHEAD
        return hours, hours * self.labor_rate

    def find_spec(self, m: MeasurementItem, specs: List[InsulationSpec]) -> Optional[InsulationSpec]:
        """Best spec for a run: size band hit > unconstrained > miss (excluded); then location match; then spec order."""
        parsed = parse_size(m.size)
        run_location = classify_location(m.location)
        ranked = []
        for index, spec in enumerate(specs):
            if spec.system_type != m.system_type:
                continue
            band = parse_size_range(spec.size_range)
            if band is None or parsed is None:
                size_score = 1
            elif band[0] <= parsed.nominal <= band[1]:
                size_score = 0
            else:
                continue
            location_score = 0 if classify_location(spec.location) == run_location else 1
            ranked.append(((size_score, location_score, index), spec))
        return min(ranked, key=lambda t: t[0])[1] if ranked else None

    # ----------------------------------------------------------------- helpers

    def _precheck(self, m: MeasurementItem) -> Optional[str]:
        if m.system_type not in SUPPORTED_SYSTEMS:
            return f"system type '{m.system_type}' unsupported (need duct or pipe)"
        if m.length <= 0:
            return f"length {m.length} is not positive"
        return None

    def _insulated_length(self, m: MeasurementItem) -> float:
        extra = 0.0
        for kind, count in (m.fittings or {}).items():
            if count and kind not in self.fitting_allowance_lf:
                self.warnings.append(f"{m.item_id}: no LF allowance configured for fitting '{kind}' x{count} - ignored")
            extra += count * self.fitting_allowance_lf.get(kind, 0.0)
        return m.length + extra

    def _price(self, key: str) -> Optional[float]:
        return self.pricebook.get(key)

    def _flag(self, m: MeasurementItem, description: str, unit: str, qty: float, category: str, why: str) -> MaterialItem:
        message = f"{m.item_id}: {why} - line left unpriced"
        self.warnings.append(message)
        logger.debug(message)
        return MaterialItem(f"[UNPRICED] {description}", unit, qty, 0.0, 0.0, category, m.system_type, m.item_id)

    def _line(self, m: MeasurementItem, description: str, unit: str, qty: float, base_price: float, category: str) -> MaterialItem:
        unit_price = base_price * self.markup
        return MaterialItem(description, unit, qty, unit_price, qty * unit_price, category, m.system_type, m.item_id)

    def _insulation_line(self, m: MeasurementItem, spec: InsulationSpec) -> MaterialItem:
        qty = self._insulated_length(m)
        description = f"{spec.material.replace('_', ' ').title()} Insulation {spec.thickness}\" - {m.size}"
        material = normalize_key(spec.material)
        keys = [f"{material}_{spec.thickness}", f"{material}_{spec.thickness:g}", f"{material}_{spec.thickness:.1f}"]
        for key in keys:
            price = self._price(key)
            if price is not None:
                return self._line(m, description, "LF", qty, price, "insulation")
        return self._flag(m, description, "LF", qty, "insulation", f"price book has no '{keys[0]}'")

    def _jacket_key(self, spec: InsulationSpec) -> Optional[str]:
        """Price-book key for the jacket/facing, or None if the spec has none."""
        for req in JACKET_REQUIREMENTS:
            if req in spec.special_requirements:
                return req
        facing = normalize_key(spec.facing or "")
        return None if facing in NO_FACING else f"{facing}_facing"

    def _jacket_line(self, m: MeasurementItem, spec: InsulationSpec) -> MaterialItem:
        key = self._jacket_key(spec) or ""
        description = f"{key.replace('_', ' ').title()} - {m.size}"
        parsed = parse_size(m.size)
        if parsed is None:
            return self._flag(m, description, "SF", 0.0, "jacket", f"size '{m.size}' unparseable, cannot compute jacket area")
        area = surface_area_sf(parsed, spec.thickness, self._insulated_length(m))
        price = self._price(key)
        if price is None:
            return self._flag(m, description, "SF", area, "jacket", f"price book has no '{key}'")
        return self._line(m, description, "SF", area, price, "jacket")

    def _mastic_line(self, m: MeasurementItem, spec: InsulationSpec) -> MaterialItem:
        parsed = parse_size(m.size)
        if parsed is None:
            return self._flag(m, "Mastic Vapor Seal Coating", "SF", 0.0, "mastic", f"size '{m.size}' unparseable")
        area = surface_area_sf(parsed, spec.thickness, self._insulated_length(m))
        price = self._price("mastic")
        if price is None:
            return self._flag(m, "Mastic Vapor Seal Coating", "SF", area, "mastic", "price book has no 'mastic'")
        return self._line(m, "Mastic Vapor Seal Coating", "SF", area, price, "mastic")

    def _accessory_lines(self, m: MeasurementItem, spec: InsulationSpec) -> List[MaterialItem]:
        lines: List[MaterialItem] = []
        if "stainless_bands" in spec.special_requirements:
            count = int(m.length) + 1  # one band per foot of run
            price = self._price("stainless_bands")
            if price is None:
                lines.append(self._flag(m, "Stainless Steel Bands", "EA", count, "accessories", "price book has no 'stainless_bands'"))
            else:
                lines.append(self._line(m, "Stainless Steel Bands", "EA", count, price, "accessories"))
        return lines
