"""Price book: unit prices keyed by normalised string ("fiberglass_1.5", "fsk_facing", "mastic").

Key convention (this is the contract the engine relies on):
  insulation : "<material>_<thickness>"   e.g. fiberglass_1.5, elastomeric_0.5      -> $/LF
  facing     : "<facing>_facing"          e.g. fsk_facing, asj_facing               -> $/SF
  jackets    : aluminum_jacket, stainless_jacket, pvc_jacket_20mil, pvc_jacket_30mil -> $/SF
  mastic ($/SF), stainless_bands ($/each)
Keys are lower-cased with spaces -> underscores on load. A missing key is NEVER defaulted: the engine flags the line.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

DEFAULT_PRICES: Dict[str, float] = {
    "fiberglass_1.5": 4.50, "fiberglass_2.0": 5.75,
    "elastomeric_0.5": 3.25, "elastomeric_1.0": 4.50,
    "cellular_glass_1.0": 6.75, "mineral_wool_1.5": 5.25,
    "fsk_facing": 1.25, "asj_facing": 1.75,
    "aluminum_jacket": 8.50, "pvc_jacket_20mil": 3.75, "pvc_jacket_30mil": 4.50, "stainless_jacket": 12.50,
    "mastic": 0.75, "stainless_bands": 2.50,
}


def normalize_key(key: Any) -> str:
    return str(key).strip().lower().replace(" ", "_")


class PriceBook:
    """Immutable-ish lookup table. Build with ``PriceBook.load(path)`` or ``PriceBook(dict)``."""

    def __init__(self, prices: Optional[Dict[str, float]] = None, source: str = "built-in defaults") -> None:
        self.prices: Dict[str, float] = {normalize_key(k): float(v) for k, v in (prices or DEFAULT_PRICES).items()}
        self.source = source

    def get(self, key: str) -> Optional[float]:
        return self.prices.get(normalize_key(key))

    def with_overrides(self, overrides: Dict[str, float]) -> "PriceBook":
        return PriceBook({**self.prices, **{normalize_key(k): float(v) for k, v in overrides.items()}}, self.source)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "PriceBook":
        """Load a flat ``{key: price}`` JSON, or ``{"supplier_prices": [{key|material, supplier_price|price}, ...]}``."""
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        prices: Dict[str, float] = {}
        if isinstance(raw, dict) and isinstance(raw.get("supplier_prices"), list):
            for item in raw["supplier_prices"]:
                key = item.get("key") or item.get("material") or item.get("description")
                price = item.get("supplier_price", item.get("price", item.get("unit_price")))
                if key is None or price is None:
                    continue
                try:
                    prices[normalize_key(key)] = float(price)
                except (TypeError, ValueError):
                    logger.warning("Skipping non-numeric price for %r", key)
        elif isinstance(raw, dict):
            for key, value in raw.items():
                try:
                    prices[normalize_key(key)] = float(value)
                except (TypeError, ValueError):
                    continue  # e.g. metadata entries
        else:
            raise ValueError(f"{path}: price book must be a JSON object")
        if not prices:
            raise ValueError(f"{path}: no numeric prices found")
        return cls(prices, source=str(path))
