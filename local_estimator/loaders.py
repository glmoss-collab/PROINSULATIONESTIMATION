"""Read takeoff lines and spec tables from CSV or JSON. Tolerant of Bluebeam-style exports (column aliases, 125' 6" lengths).

NOTE: the Bluebeam column aliases are an educated guess about a Markups List / Measurements CSV export - verify against a
real export from your Bluebeam setup and add aliases to MEASUREMENT_ALIASES if a column is not picked up. Skipped rows are
reported in the returned warnings, never silently dropped.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from .models import InsulationSpec, MeasurementItem
from .sizes import NUM, parse_length_ft

MEASUREMENT_ALIASES: Dict[str, Tuple[str, ...]] = {
    "item_id": ("item_id", "id", "mark", "label", "name", "tag"),
    "system_type": ("system_type", "system", "service", "type"),
    "size": ("size", "dimensions", "dimension", "diameter", "nominal_size"),
    "length": ("length", "length_ft", "lf", "measurement", "total_length", "qty", "quantity"),
    "location": ("location", "layer", "space", "area", "sheet", "page_label"),
    "notes": ("notes", "comments", "comment", "description", "subject"),
}
FITTING_COLUMNS = {"elbow": "elbow", "elbows": "elbow", "tee": "tee", "tees": "tee",
                   "reducer": "reducer", "reducers": "reducer", "valve": "valve", "valves": "valve",
                   "flange": "flange", "flanges": "flange"}
_DUCT = re.compile(r"duct|plenum|\b(?:sa|ra|ea|oa)\b|supply air|return air|exhaust")
_PIPE = re.compile(r"pipe|piping|\b(?:chw|hw|cw|chws|chwr|hws|hwr|cws|cwr)\b|steam|condensate|glycol|refrigerant")

Row = Dict[str, Any]


def _norm_row(row: Row) -> Row:
    return {re.sub(r"\s+", "_", str(k).strip().lower()): v for k, v in row.items() if k is not None}


def _pick(row: Row, field: str) -> Optional[Any]:
    for alias in MEASUREMENT_ALIASES[field]:
        value = row.get(alias)
        if value not in (None, ""):
            return value
    return None


def _infer_system(row: Row) -> str:
    declared = str(_pick(row, "system_type") or "").strip().lower()
    if declared in ("duct", "pipe"):
        return declared
    text = " ".join(str(v) for v in row.values()).lower()
    if _DUCT.search(text) and not _PIPE.search(text):
        return "duct"
    if _PIPE.search(text) and not _DUCT.search(text):
        return "pipe"
    return ""


def _infer_size(row: Row, item_id: str) -> str:
    """Bluebeam labels often carry the size ('24x16 SA-1', '2\" CHWS'). Look in id/notes/comments when no size column."""
    text = " ".join(str(row.get(k) or "") for k in ("notes", "comments", "comment", "description", "subject", "label", "name")) + " " + item_id
    rect = re.search(rf"\b({NUM})\s*[x\u00d7]\s*({NUM})\b", text)
    if rect:
        return f"{rect.group(1)}x{rect.group(2)}"
    round_ = re.search(rf"({NUM})\s*(?:\"|\u201d|\u2033|in\b|inch)", text)
    return f'{round_.group(1)}"' if round_ else ""


def measurements_from_rows(rows: Iterable[Row]) -> Tuple[List[MeasurementItem], List[str]]:
    items: List[MeasurementItem] = []
    warnings: List[str] = []
    for n, raw in enumerate(rows, 1):
        row = _norm_row(raw)
        item_id = str(_pick(row, "item_id") or f"M-{n}")
        raw_length = _pick(row, "length")
        try:
            length = parse_length_ft(raw_length) if raw_length is not None else float("nan")
            if length != length:
                raise ValueError("missing length")
        except ValueError as exc:
            warnings.append(f"row {n} ({item_id}): {exc} - row skipped")
            continue
        fittings: Dict[str, int] = {}
        for col, kind in FITTING_COLUMNS.items():
            if row.get(col) not in (None, ""):
                try:
                    fittings[kind] = fittings.get(kind, 0) + int(float(row[col]))
                except ValueError:
                    warnings.append(f"row {n} ({item_id}): fitting column '{col}'={row[col]!r} not a number - ignored")
        if isinstance(row.get("fittings"), dict):
            fittings.update({str(k): int(v) for k, v in row["fittings"].items()})
        note = _pick(row, "notes")
        system = _infer_system(row)
        if not system:
            warnings.append(f"row {n} ({item_id}): cannot tell duct from pipe - set system_type; it will not be priced")
        items.append(
            MeasurementItem(
                item_id=item_id,
                system_type=system,
                size=str(_pick(row, "size") or "").strip() or _infer_size(row, item_id),
                length=length,
                location=str(_pick(row, "location") or "indoor"),
                elevation_changes=int(float(row.get("elevation_changes") or 0)),
                fittings=fittings,
                notes=[str(note)] if note else [],
            )
        )
    return items, warnings


def _read_rows(path: Union[str, Path], json_key: str) -> List[Row]:
    path = Path(path)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get(json_key, [])
        if not isinstance(data, list):
            raise ValueError(f"{path}: expected a JSON list (or an object with '{json_key}')")
        return data
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_measurements(path: Union[str, Path]) -> Tuple[List[MeasurementItem], List[str]]:
    """CSV or JSON file -> (measurements, load warnings)."""
    return measurements_from_rows(_read_rows(path, "measurements"))


def load_specs(path: Union[str, Path]) -> List[InsulationSpec]:
    """Spec table (CSV or JSON). Columns: system_type,size_range,thickness,material[,facing,special_requirements,location].
    special_requirements in CSV is a ';'-separated list."""
    specs: List[InsulationSpec] = []
    for n, raw in enumerate(_read_rows(path, "specifications"), 1):
        row = _norm_row(raw)
        for required in ("system_type", "thickness", "material"):
            if row.get(required) in (None, ""):
                raise ValueError(f"{path} row {n}: missing required column '{required}'")
        reqs = row.get("special_requirements") or []
        if isinstance(reqs, str):
            reqs = [r.strip() for r in reqs.split(";") if r.strip()]
        specs.append(
            InsulationSpec(
                system_type=str(row["system_type"]).strip().lower(),
                size_range=str(row.get("size_range") or "all"),
                thickness=float(row["thickness"]),
                material=str(row["material"]).strip().lower().replace(" ", "_"),
                facing=(str(row["facing"]).strip() or None) if row.get("facing") else None,
                special_requirements=list(reqs),
                location=str(row.get("location") or "indoor").strip().lower(),
            )
        )
    return specs
