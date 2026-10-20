"""Parsing of sizes, size ranges and lengths, plus insulated surface-area geometry. Pure functions, stdlib only."""

from __future__ import annotations

import math
import re
from typing import NamedTuple, Optional, Tuple, Union

# number token: mixed fraction "1-1/2" / "1 1/2", fraction "1/2", or decimal/integer
NUM = r"\d+\s*[- ]\s*\d+/\d+|\d+/\d+|\d+(?:\.\d+)?"


class ParsedSize(NamedTuple):
    kind: str  # "round" (pipe or round duct) | "rect"
    dims: Tuple[float, ...]  # (diameter,) or (width, height), inches

    @property
    def nominal(self) -> float:
        """Diameter, or the larger side of a rectangle - the number spec size bands compare against."""
        return max(self.dims)


def to_float(token: str) -> float:
    """'4' '2.5' '1/2' '1-1/2' '1 1/2' -> float."""
    token = token.strip()
    mixed = re.fullmatch(r"(\d+)\s*[- ]\s*(\d+)/(\d+)", token)
    if mixed:
        return int(mixed.group(1)) + int(mixed.group(2)) / int(mixed.group(3))
    frac = re.fullmatch(r"(\d+)/(\d+)", token)
    if frac:
        return int(frac.group(1)) / int(frac.group(2))
    return float(token)


def parse_size(size: str) -> Optional[ParsedSize]:
    """'18x12' -> rect(18,12); '4"' / '4 inch' / '1-1/2"' -> round; unparseable -> None (never a silent default)."""
    text = (size or "").lower().replace("×", "x")
    text = re.sub(r'(inches|inch|\bin\b|["″”])', "", text)
    rect = re.fullmatch(rf"\s*({NUM})\s*x\s*({NUM})\s*(?:x.*)?", text)
    if rect:
        return ParsedSize("rect", (to_float(rect.group(1)), to_float(rect.group(2))))
    num = re.search(NUM, text)
    if num:
        return ParsedSize("round", (to_float(num.group(0)),))
    return None


_RANGE = rf"({NUM})\s*(?:-|\u2013|\bto\b|through)\s*({NUM})"
_UNIT = r'\s*(?:"|\u201d|\u2033|inch|in\b)'


def find_size_range(text: str, require_unit: bool = False) -> Optional[Tuple[str, Tuple[float, float]]]:
    """First 'lo-hi' / 'lo to hi' range in text -> (matched text, (lo, hi)); None if absent.

    Ranges must be written ascending. That rejects a mixed number misread as a range ('1-1/2' -> 1 to 1/2),
    while '1/2-2', '1-1/2 to 3' and '2-1/2 - 4' still parse.
    """
    pattern = _RANGE + (_UNIT if require_unit else "")
    for hit in re.finditer(pattern, (text or "").lower()):
        lo, hi = to_float(hit.group(1)), to_float(hit.group(2))
        if lo <= hi:
            return hit.group(0), (lo, hi)
    return None


def parse_size_range(size_range: str) -> Optional[Tuple[float, float]]:
    """'4-12 inch' -> (4,12); '1/2-2 inch' -> (0.5,2); 'up to 6"' -> (0,6); 'over 12"' -> (12,inf); 'all'/free text -> None.

    A single size like '1-1/2 inch' is not a range and returns None (treated as unconstrained, not as 1 to 1/2).
    """
    text = (size_range or "").lower()
    text = re.sub(r'(inches|inch|\bin\b\.?|["\u2033\u201d])', "", text)
    found = find_size_range(text)
    if found:
        return found[1]
    upto = re.search(rf"(?:up to|under|<=?|through)\s*({NUM})|({NUM})\s*(?:and smaller|or less)", text)
    if upto:
        return (0.0, to_float(upto.group(1) or upto.group(2)))
    over = re.search(rf"(?:over|above|>=?|larger than)\s*({NUM})|({NUM})\s*(?:and larger|or more)", text)
    if over:
        return (to_float(over.group(1) or over.group(2)), math.inf)
    return None


def parse_length_ft(value: Union[str, int, float]) -> float:
    """Bluebeam/CSV length -> feet. Accepts 125.5, '125.5', '1,250 ft', "125' 6\\"", '18 in'. Raises ValueError otherwise."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower().replace(",", "")
    plain = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*(?:ft|feet|foot|lf|')?", text)
    if plain:
        return float(plain.group(1))
    ft_in = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:'|ft|feet)\s*-?\s*(\d+(?:\.\d+)?)\s*(?:\"|in|inches)?", text)
    if ft_in:
        return float(ft_in.group(1)) + float(ft_in.group(2)) / 12
    inches = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:\"|in|inches)", text)
    if inches:
        return float(inches.group(1)) / 12
    raise ValueError(f"unrecognised length {value!r} (expected feet, e.g. 125.5, '125.5 ft' or \"125' 6\\\"\")")


def surface_area_sf(size: ParsedSize, thickness_in: float, length_lf: float) -> float:
    """Outside surface area of an insulated run.

    round/pipe : pi x (D + 2t) / 12 per LF
    rectangular: 2 x (W + H + 4t) / 12 per LF   (perimeter of the insulated outline)
    """
    if size.kind == "rect":
        width, height = size.dims
        perimeter_ft = 2 * (width + height + 4 * thickness_in) / 12
    else:
        perimeter_ft = math.pi * (size.dims[0] + 2 * thickness_in) / 12
    return length_lf * perimeter_ft


def classify_location(text: str) -> str:
    """Free-text location -> 'outdoor' | 'indoor'. Used to match a run to an indoor/outdoor spec."""
    if re.search(r"outdoor|exterior|outside|roof|rooftop|exposed|yard|weather|penthouse", (text or "").lower()):
        return "outdoor"
    return "indoor"
