#!/usr/bin/env python3
"""
Standalone HVAC insulation estimate calculator for Guaranteed Insulation Inc.

Reads measurements and specs from JSON files, applies the company scope filter,
calculates materials and labor from the pricebook, and prints a quote summary.

Usage:
    python calculate_estimate.py \
        --measurements measurements.json \
        --specs specs.json \
        [--pricebook pricebook_sample.json] \
        [--labor-rate 65] \
        [--markup 1.0] \
        [--contingency 10] \
        [--output quote_output.txt]

JSON input formats:

  measurements.json — list of measurement objects:
    [
      {
        "item_id": "D-1",
        "system_type": "duct",
        "size": "18x12",
        "length": 100.0,
        "location": "Roof",
        "elevation_changes": 0,
        "fittings": {"elbow": 2, "tee": 0},
        "notes": ["outdoor", "aluminum jacket"]
      }
    ]

  specs.json — list of specification objects:
    [
      {
        "system_type": "duct",
        "size_range": "12-24 inch",
        "thickness": 1.5,
        "material": "fiberglass",
        "facing": "FSK",
        "special_requirements": ["aluminum_jacket", "mastic_coating"],
        "location": "outdoor"
      }
    ]
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path so we can import the estimator modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from hvac_insulation_estimator import (
    InsulationSpec,
    MeasurementItem,
    PricingEngine,
    QuoteGenerator,
)
from guaranteed_insulation_scope import (
    filter_specs_to_scope,
    filter_measurements_to_scope,
    get_scope_exclusion_summary,
)
from guaranteed_insulation_bid_package import generate_bid_package_text


def load_measurements(path: str) -> list[MeasurementItem]:
    """Load measurements from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = []
    for entry in data:
        items.append(MeasurementItem(
            item_id=entry.get("item_id", ""),
            system_type=entry.get("system_type", "duct"),
            size=entry.get("size", ""),
            length=float(entry.get("length", 0)),
            location=entry.get("location", ""),
            elevation_changes=int(entry.get("elevation_changes", 0)),
            fittings=entry.get("fittings", {}),
            notes=entry.get("notes", []),
        ))
    return items


def load_specs(path: str) -> list[InsulationSpec]:
    """Load insulation specifications from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    specs = []
    for entry in data:
        specs.append(InsulationSpec(
            system_type=entry.get("system_type", "duct"),
            size_range=entry.get("size_range", ""),
            thickness=float(entry.get("thickness", 1.5)),
            material=entry.get("material", "fiberglass"),
            facing=entry.get("facing"),
            special_requirements=entry.get("special_requirements", []),
            location=entry.get("location", "indoor"),
        ))
    return specs


def main():
    parser = argparse.ArgumentParser(
        description="Calculate HVAC insulation estimate for Guaranteed Insulation Inc."
    )
    parser.add_argument(
        "--measurements", required=True,
        help="Path to measurements JSON file"
    )
    parser.add_argument(
        "--specs", required=True,
        help="Path to specifications JSON file"
    )
    parser.add_argument(
        "--pricebook", default=str(PROJECT_ROOT / "pricebook_sample.json"),
        help="Path to pricebook JSON (default: pricebook_sample.json)"
    )
    parser.add_argument(
        "--labor-rate", type=float, default=65.0,
        help="Labor rate in $/hr (default: 65)"
    )
    parser.add_argument(
        "--markup", type=float, default=1.0,
        help="Markup multiplier (default: 1.0 = no markup)"
    )
    parser.add_argument(
        "--contingency", type=float, default=10.0,
        help="Contingency percentage (default: 10)"
    )
    parser.add_argument(
        "--project-name", default="Untitled Project",
        help="Project name for the quote header"
    )
    parser.add_argument(
        "--output", default=None,
        help="Output file path for formal bid package (optional)"
    )
    args = parser.parse_args()

    # Load inputs
    print(f"Loading measurements from: {args.measurements}")
    measurements = load_measurements(args.measurements)
    print(f"  {len(measurements)} measurement(s) loaded")

    print(f"Loading specifications from: {args.specs}")
    specs = load_specs(args.specs)
    print(f"  {len(specs)} specification(s) loaded")

    # Apply scope filter
    specs_before = len(specs)
    measurements_before = len(measurements)
    specs = filter_specs_to_scope(specs)
    measurements = filter_measurements_to_scope(measurements)
    scope_summary = get_scope_exclusion_summary(
        specs_before, len(specs),
        measurements_before, len(measurements),
    )
    print(f"\nScope filter: {scope_summary}")

    if not measurements:
        print("\nNo in-scope measurements to price. Exiting.")
        sys.exit(0)

    # Calculate
    print(f"\nUsing pricebook: {args.pricebook}")
    engine = PricingEngine(price_book_path=args.pricebook, markup=args.markup)
    materials = engine.calculate_materials(measurements, specs)
    labor_hours, labor_cost = engine.calculate_labor(materials)

    # Override labor rate if specified
    if args.labor_rate != 65.0:
        labor_cost = labor_hours * args.labor_rate

    # Generate quote
    generator = QuoteGenerator(
        project_name=args.project_name,
        measurements=measurements,
        materials=materials,
        labor_hours=labor_hours,
        labor_rate=args.labor_rate,
        contingency_percent=args.contingency,
    )
    quote = generator.generate_quote()

    # Print summary
    material_total = sum(m.total_price for m in quote.materials)
    labor_total = quote.labor_hours * quote.labor_rate
    contingency = quote.subtotal * (quote.contingency_percent / 100)

    print("\n" + "=" * 60)
    print(f"  GUARANTEED INSULATION INC. — ESTIMATE SUMMARY")
    print("=" * 60)
    print(f"  Project:     {quote.project_name}")
    print(f"  Quote No.:   {quote.quote_number}")
    print(f"  Date:        {quote.date}")
    print()
    print(f"  Materials .............. ${material_total:>12,.2f}")
    print(f"  Labor ({quote.labor_hours:.1f} hrs @ ${quote.labor_rate:,.2f})")
    print(f"                           ${labor_total:>12,.2f}")
    print(f"  Subtotal ............... ${quote.subtotal:>12,.2f}")
    print(f"  Contingency ({quote.contingency_percent:.0f}%) ...... ${contingency:>12,.2f}")
    print(f"  {'':─<30}──────────────")
    print(f"  TOTAL .................. ${quote.total:>12,.2f}")
    print("=" * 60)

    # Export formal bid package if requested
    if args.output:
        bid_text = generate_bid_package_text(quote, scope_summary)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(bid_text, encoding="utf-8")
        print(f"\nFormal bid package written to: {output_path}")


if __name__ == "__main__":
    main()
