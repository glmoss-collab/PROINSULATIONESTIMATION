"""Data contracts shared by every module (plain dataclasses, no validation library).

Units: lengths in feet (LF), sizes/thickness in inches, money in USD.
Every dataclass has ``to_dict()`` so results can be dumped to JSON for another tool or an AI bot.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


class _Dictable:
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)  # type: ignore[call-overload]


@dataclass
class InsulationSpec(_Dictable):
    """One insulation rule from the project spec (Division 23 07 xx), e.g. 'CHW pipe 0.5-2 in -> 1 in elastomeric'."""

    system_type: str  # "duct" | "pipe"
    size_range: str  # "4-12 inch", "1/2-2 inch", "up to 6 inch", "over 12 inch", or "all"
    thickness: float  # inches
    material: str  # "fiberglass" | "elastomeric" | "cellular_glass" | "mineral_wool" (price-book key prefix)
    facing: str | None = None  # "FSK", "ASJ", ... None/"unfaced" = no facing line
    special_requirements: List[str] = field(default_factory=list)  # e.g. "aluminum_jacket", "mastic_coating", "stainless_bands"
    location: str = "indoor"  # "indoor" | "outdoor"


@dataclass
class MeasurementItem(_Dictable):
    """One takeoff line: a run of duct or pipe (from Bluebeam, a CSV, or typed by hand)."""

    item_id: str
    system_type: str  # "duct" | "pipe"  ("" if unknown -> flagged, not priced)
    size: str  # round/pipe: '4"', '1-1/2"'; rectangular duct: '18x12'
    length: float  # linear feet of the run, fittings excluded
    location: str = "indoor"  # free text ("Roof", "Mech room 101"); classified indoor/outdoor when matching specs
    elevation_changes: int = 0
    fittings: Dict[str, int] = field(default_factory=dict)  # {"elbow": 3, "tee": 1}
    notes: List[str] = field(default_factory=list)


@dataclass
class MaterialItem(_Dictable):
    """A priced (or flagged-unpriced) material line."""

    description: str
    unit: str  # "LF" | "SF" | "EA"
    quantity: float
    unit_price: float
    total_price: float
    category: str  # "insulation" | "jacket" | "mastic" | "accessories"
    system_type: str = ""  # run type this line belongs to; drives labor rates
    item_id: str = ""  # MeasurementItem.item_id this line came from (traceability)


@dataclass
class ProjectQuote(_Dictable):
    project_name: str
    quote_number: str
    date: str
    measurements: List[MeasurementItem]
    materials: List[MaterialItem]
    labor_hours: float
    labor_rate: float
    subtotal: float  # materials + labor, before contingency
    contingency_percent: float
    total: float
    notes: List[str]
    material_list: List[Dict[str, Any]]  # consolidated distributor list
