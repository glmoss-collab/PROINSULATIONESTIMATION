"""Company scope filter: what Guaranteed Insulation Inc. does NOT bid (liner, waste/domestic plumbing, sprinkler, buried).

Keyword based and deliberately simple. Every exclusion is returned WITH its reason so a human can overturn it.
Judgment call to review: 'drain' is excluded, which also drops insulated HVAC condensate drains - edit EXCLUDED_KEYWORDS.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .models import InsulationSpec, MeasurementItem

COMPANY_NAME = "Guaranteed Insulation Inc."
SCOPE_DESCRIPTION = "External HVAC and mechanical insulation only."

EXCLUDED_KEYWORDS: List[str] = [
    "duct liner", "liner", "internal liner", "acoustic liner", "acoustic only",
    "waste", "sanitary", "domestic water", "plumbing", "drain", "sewer",
    "fire sprinkler", "sprinkler", "fire protection pipe",
    "underground", "buried", "below grade",
]


def _first_hit(text: str, keywords: List[str]) -> Optional[str]:
    text = text.lower()
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}", text):
            return kw
    return None


def spec_exclusion_reason(spec: InsulationSpec, keywords: List[str] = EXCLUDED_KEYWORDS) -> Optional[str]:
    hit = _first_hit(f"{spec.system_type} {spec.size_range} {spec.material} {' '.join(spec.special_requirements)}", keywords)
    return f"matches excluded term '{hit}'" if hit else None


def measurement_exclusion_reason(m: MeasurementItem, keywords: List[str] = EXCLUDED_KEYWORDS) -> Optional[str]:
    hit = _first_hit(f"{m.system_type} {m.size} {m.location} {' '.join(m.notes)} {m.item_id}", keywords)
    return f"matches excluded term '{hit}'" if hit else None


def apply_scope(
    specs: List[InsulationSpec], measurements: List[MeasurementItem], keywords: List[str] = EXCLUDED_KEYWORDS
) -> Tuple[List[InsulationSpec], List[MeasurementItem], List[Dict[str, str]]]:
    """Return (kept specs, kept measurements, exclusions[{kind,id,reason}])."""
    excluded: List[Dict[str, str]] = []
    kept_specs: List[InsulationSpec] = []
    for s in specs:
        reason = spec_exclusion_reason(s, keywords)
        if reason:
            excluded.append({"kind": "spec", "id": f"{s.system_type} {s.size_range} {s.material}", "reason": reason})
        else:
            kept_specs.append(s)
    kept_meas: List[MeasurementItem] = []
    for m in measurements:
        reason = measurement_exclusion_reason(m, keywords)
        if reason:
            excluded.append({"kind": "measurement", "id": m.item_id, "reason": reason})
        else:
            kept_meas.append(m)
    return kept_specs, kept_meas, excluded
