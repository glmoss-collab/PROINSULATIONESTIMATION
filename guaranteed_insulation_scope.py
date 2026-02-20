"""
Guaranteed Insulation Inc. - Scope Filter

External HVAC/mechanical insulation ONLY.
Excludes: duct liner, waste plumbing, domestic water, fire sprinkler (non-mechanical),
and any non-external mechanical insulation scope.
"""

from typing import List, Optional

from hvac_insulation_estimator import InsulationSpec, MeasurementItem

# Company scope
COMPANY_NAME = "Guaranteed Insulation Inc."
SCOPE_DESCRIPTION = "External HVAC and mechanical insulation only."

# Keywords that indicate IN SCOPE (external / mechanical insulation we do)
IN_SCOPE_SYSTEM_TYPES = {"duct", "pipe", "equipment"}
IN_SCOPE_KEYWORDS = [
    "duct wrap", "ductwork", "supply duct", "return duct", "exhaust duct",
    "external duct", "exterior duct", "outdoor duct",
    "chilled water", "hot water", "condenser water", "chw", "hw", "cw",
    "steam", "condensate", "hvac piping", "mechanical piping",
    "equipment insulation", "ahu", "fcu", "boiler", "chiller", "tank",
    "kitchen exhaust", "grease duct", "fireproofing", "weatherproof",
    "aluminum jacket", "pvc jacket", "external", "exterior", "exposed",
]

# Keywords that indicate EXCLUDED (we do not price these)
EXCLUDED_KEYWORDS = [
    "duct liner", "liner", "internal liner", "acoustic liner",
    "waste", "sanitary", "domestic water", "plumbing", "drain", "sewer",
    "fire sprinkler", "sprinkler pipe", "fire protection pipe",
    "underground", "buried", "below grade",
]
EXCLUDED_SYSTEM_TYPES = set()  # We keep duct, pipe, equipment but filter by description/notes
EXCLUDED_SPEC_NOTES = ["liner", "internal", "acoustic only", "waste", "plumbing", "sprinkler"]


def _normalize(s: str) -> str:
    return (s or "").lower().strip()


def _spec_matches_excluded(spec: InsulationSpec) -> bool:
    """True if this spec should be excluded from our scope."""
    notes = " ".join(spec.special_requirements or [])
    text = _normalize(f"{spec.system_type} {spec.size_range} {notes}")
    for kw in EXCLUDED_KEYWORDS:
        if kw in text:
            return True
    for kw in EXCLUDED_SPEC_NOTES:
        if kw in text:
            return True
    # Explicit "duct liner" type: sometimes indicated by spec note or system_type + "liner"
    if spec.system_type == "duct" and "liner" in text:
        return True
    return False


def _measurement_matches_excluded(m: MeasurementItem) -> bool:
    """True if this measurement should be excluded (e.g. waste plumbing)."""
    text = _normalize(f"{m.system_type} {m.size} {m.location} " + " ".join(m.notes or []))
    for kw in EXCLUDED_KEYWORDS:
        if kw in text:
            return True
    return False


def filter_specs_to_scope(specs: List[InsulationSpec]) -> List[InsulationSpec]:
    """
    Return only specs that are in Guaranteed Insulation Inc. scope:
    external HVAC/mechanical insulation. Excludes duct liner, waste plumbing, etc.
    """
    return [s for s in specs if s.system_type in IN_SCOPE_SYSTEM_TYPES and not _spec_matches_excluded(s)]


def filter_measurements_to_scope(measurements: List[MeasurementItem]) -> List[MeasurementItem]:
    """
    Return only measurements that are in scope.
    Excludes waste plumbing, sprinkler, duct liner-only items, etc.
    """
    return [m for m in measurements if m.system_type in IN_SCOPE_SYSTEM_TYPES and not _measurement_matches_excluded(m)]


def get_scope_exclusion_summary(
    specs_before: int,
    specs_after: int,
    measurements_before: int,
    measurements_after: int,
) -> str:
    """One-line summary of what was excluded for the bid package."""
    parts = []
    if specs_before > specs_after:
        parts.append(f"{specs_before - specs_after} specification(s) excluded (out of scope)")
    if measurements_before > measurements_after:
        parts.append(f"{measurements_before - measurements_after} measurement(s) excluded (out of scope)")
    if not parts:
        return "All extracted items fall within Guaranteed Insulation Inc. scope (external HVAC/mechanical insulation only)."
    return "Scope filter applied: " + "; ".join(parts) + ". Excluded items: duct liner, waste plumbing, domestic water, fire sprinkler, and other non-external mechanical insulation."
