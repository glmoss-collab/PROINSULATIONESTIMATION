"""Best-effort extraction of insulation specs from PLAIN TEXT (copy/paste of Division 23 07 xx text - no PDF library).

Strategy: split into sentence-like chunks; a chunk yields a spec only if it names a system (duct/pipe), a thickness
and a material TOGETHER. Anything else is ignored rather than guessed. ALWAYS review the output: this is a convenience,
the reliable path is a spec table (CSV/JSON, see loaders.load_specs).
"""

from __future__ import annotations

import re
from typing import List

from .models import InsulationSpec
from .sizes import NUM, parse_size_range, to_float

MATERIALS = {
    "fiberglass": r"fiberglass|fibreglass|glass fiber|glass fibre",
    "mineral_wool": r"mineral wool|rock wool|stone wool",
    "elastomeric": r"elastomeric|flexible foam|armaflex",
    "cellular_glass": r"cellular glass|foamglass",
}
FACINGS = {"FSK": r"\bfsk\b|foil[- ]scrim[- ]kraft", "ASJ": r"\basj\b|all[- ]service jacket", "PVC": r"\bpvc\b"}
REQUIREMENTS = {
    "aluminum_jacket": r"aluminum\s+jacket|metal\s+jacket",
    "stainless_bands": r"stainless\s+(?:steel\s+)?bands?",
    "mastic_coating": r"mastic|vapor\s+seal",
}
OUTDOOR = r"outdoor|exterior|outside|exposed to weather|roof"


def extract_specs_from_text(text: str) -> List[InsulationSpec]:
    specs: List[InsulationSpec] = []
    for chunk in re.split(r"[\n;]+|(?<=[a-z])\.\s+", text):
        low = chunk.lower()
        system = "duct" if re.search(r"\bduct", low) else "pipe" if re.search(r"\bpip(?:e|ing)\b", low) else None
        material = next((name for name, pat in MATERIALS.items() if re.search(pat, low)), None)
        # Size band first and REMOVE it from the chunk: otherwise "1/2 to 2 inch ... 1 inch" reads thickness as 2.
        size_range = "all"
        for pattern in (rf"({NUM})\s*(?:\bto\b|through|\s-\s)\s*({NUM})\s*(?:inch|in\b|\")", rf"(?:up to|over|above|under)\s*({NUM})\s*(?:inch|in\b|\")"):
            hit = re.search(pattern, low)
            if hit and parse_size_range(hit.group(0)):
                size_range = hit.group(0).strip()
                low = low.replace(hit.group(0), " ", 1)
                break
        thickness = re.search(rf"({NUM})\s*(?:inch(?:es)?|in\b|\"|\u201d)\s*(?:thick)?", low)
        if not (system and thickness and material):
            continue
        facing = next((name for name, pat in FACINGS.items() if re.search(pat, low)), None)
        specs.append(
            InsulationSpec(
                system_type=system,
                size_range=size_range,
                thickness=to_float(thickness.group(1)),
                material=material,
                facing=facing,
                special_requirements=[req for req, pat in REQUIREMENTS.items() if re.search(pat, low)],
                location="outdoor" if re.search(OUTDOOR, low) else "indoor",
            )
        )
    return specs
