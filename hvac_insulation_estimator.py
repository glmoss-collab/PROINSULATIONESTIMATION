"""HVAC Insulation Takeoff Estimator & Spec Finder
Lead Estimator Tool for Commercial Mechanical Insulation

This framework provides:
1. PDF specification extraction
2. Drawing measurement extraction with scale
3. Insulation spec application
4. Quantity calculations
5. Pricing engine
6. Quote generation
7. Material list generation
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pdfplumber


@dataclass
class InsulationSpec:
    """Insulation specification extracted from project specs."""

    system_type: str  # "duct", "pipe", "equipment"
    size_range: str  # e.g., "4-12 inch", "1/2-2 inch"
    thickness: float  # inches
    material: str  # "fiberglass", "elastomeric", etc.
    facing: Optional[str] = None  # "FSK", "ASJ", etc.
    special_requirements: List[str] = field(default_factory=list)
    location: str = "indoor"  # "indoor", "outdoor", "exposed"


@dataclass
class MeasurementItem:
    """Single measurement from drawings."""

    item_id: str
    system_type: str  # "duct", "pipe"
    size: str  # diameter or dimensions
    length: float  # linear feet
    location: str
    elevation_changes: int = 0  # number of rises/drops
    fittings: Dict[str, int] = field(default_factory=dict)  # type: count
    notes: List[str] = field(default_factory=list)


@dataclass
class MaterialItem:
    """Material item with pricing."""

    description: str
    unit: str  # "LF", "SF", "EA"
    quantity: float
    unit_price: float
    total_price: float
    category: str  # "insulation", "jacket", "mastic", "accessories"


@dataclass
class ProjectQuote:
    """Complete project quote."""

    project_name: str
    quote_number: str
    date: str
    measurements: List[MeasurementItem]
    materials: List[MaterialItem]
    labor_hours: float
    labor_rate: float
    subtotal: float
    contingency_percent: float
    total: float
    notes: List[str]
    material_list: List[Dict]


class SpecificationExtractor:
    """Extract insulation specs from project specification PDFs."""

    def __init__(self) -> None:
        self.specs: List[InsulationSpec] = []

    def extract_from_pdf(self, pdf_path: str) -> List[InsulationSpec]:
        """Extract insulation specifications from PDF."""

        specs: List[InsulationSpec] = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""

                # Find insulation specification sections
                if self._is_insulation_section(text):
                    page_specs = self._parse_insulation_specs(text)
                    specs.extend(page_specs)

        self.specs = specs
        return specs

    def _is_insulation_section(self, text: str) -> bool:
        """Determine if page contains insulation specs."""

        keywords = [
            "insulation",
            "thermal insulation",
            "mechanical insulation",
            "duct insulation",
            "pipe insulation",
            "HVAC insulation",
            "division 23",
            "section 23 07",
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def _parse_insulation_specs(self, text: str) -> List[InsulationSpec]:
        """Parse insulation specifications from text."""

        specs: List[InsulationSpec] = []

        # Pattern matching for common spec formats
        # Example: "Duct insulation: 1.5" fiberglass with FSK facing"
        duct_pattern = r"duct.*?insulation.*?(\d+\.?\d*)\s*[\"']?\s*(fiberglass|mineral wool|elastomeric)"
        pipe_pattern = r"pipe.*?insulation.*?(\d+\.?\d*)\s*[\"']?\s*(fiberglass|elastomeric|cellular glass)"

        # Find duct insulation specs
        for match in re.finditer(duct_pattern, text, re.IGNORECASE | re.DOTALL):
            spec = InsulationSpec(
                system_type="duct",
                size_range="all",
                thickness=float(match.group(1)),
                material=match.group(2).lower(),
                facing=self._extract_facing(text, match.start()),
            )
            specs.append(spec)

        # Find pipe insulation specs
        for match in re.finditer(pipe_pattern, text, re.IGNORECASE | re.DOTALL):
            spec = InsulationSpec(
                system_type="pipe",
                size_range="all",
                thickness=float(match.group(1)),
                material=match.group(2).lower(),
            )
            specs.append(spec)

        # Extract special requirements
        self._extract_special_requirements(text, specs)

        return specs

    def _extract_facing(self, text: str, position: int) -> Optional[str]:
        """Extract facing type from nearby text."""

        # Look at 200 characters around the position
        context = text[max(0, position - 100) : position + 100].lower()

        facings = {
            "fsk": "FSK",
            "asj": "ASJ",
            "all service jacket": "ASJ",
            "foil scrim kraft": "FSK",
            "white jacket": "White Vinyl",
            "pvj": "PVJ",
        }

        for key, value in facings.items():
            if key in context:
                return value
        return None

    def _extract_special_requirements(self, text: str, specs: List[InsulationSpec]) -> None:
        """Extract special requirements like mastic, weatherproofing."""

        text_lower = text.lower()

        for spec in specs:
            if "mastic" in text_lower or "vapor seal" in text_lower:
                spec.special_requirements.append("mastic_coating")

            if any(keyword in text_lower for keyword in ("outdoor", "exterior", "exposed")):
                spec.location = "outdoor"
                spec.special_requirements.append("weatherproofing")

            if "aluminum" in text_lower and "jacket" in text_lower:
                spec.special_requirements.append("aluminum_jacket")

            if "stainless steel" in text_lower and ("band" in text_lower or "strap" in text_lower):
                spec.special_requirements.append("stainless_bands")


class DrawingMeasurementExtractor:
    """Extract measurements from PDF construction drawings."""

    def __init__(self, scale: Optional[float] = None) -> None:
        self.scale = scale  # scale in format: 1/4" = 1'-0" becomes 48
        self.measurements: List[MeasurementItem] = []

    def extract_scale_from_pdf(self, pdf_path: str) -> Optional[float]:
        """Automatically detect scale from drawing."""

        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text() or ""

            # Common scale patterns
            # 1/4" = 1'-0" means 48:1 (48 inches per 1/4 inch on drawing)
            scale_patterns = [
                r'(\d+/\d+)"\s*=\s*(\d+)' r"'-(\d+)\"",
                r'scale:\s*(\d+/\d+)"\s*=\s*(\d+)' r"'-(\d+)\"",
                r'1:\s*(\d+)',
            ]

            for pattern in scale_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return self._parse_scale(match.groups())

        return None

    def _parse_scale(self, groups: Tuple[str, ...]) -> float:
        """Parse scale groups into scale factor."""

        # This is simplified - you'd need more complex logic for different formats
        if len(groups) == 3:
            # Format: 1/4" = 1'-0"
            fraction = eval(groups[0])  # e.g., 1/4
            feet = int(groups[1])
            inches = int(groups[2])
            total_inches = feet * 12 + inches
            return total_inches / fraction
        if len(groups) == 1:
            # Format: 1:100
            return float(groups[0])
        return 48  # default 1/4" scale

    def measure_from_drawing(self, pdf_path: str, page_number: int = 0) -> List[MeasurementItem]:
        """Extract measurements from drawing using computer vision."""

        measurements: List[MeasurementItem] = []

        # Convert PDF page to image
        from pdf2image import convert_from_path

        images = convert_from_path(pdf_path, first_page=page_number + 1, last_page=page_number + 1)

        if images:
            img = np.array(images[0])

            # Detect lines (ductwork and piping)
            measurements.extend(self._detect_lines_and_measure(img))

        return measurements

    def _detect_lines_and_measure(self, image: np.ndarray) -> List[MeasurementItem]:
        """Use computer vision to detect and measure lines."""

        measurements: List[MeasurementItem] = []

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=50, maxLineGap=10)

        if lines is not None:
            for i, line in enumerate(lines):
                x1, y1, x2, y2 = line[0]

                # Calculate length in pixels
                length_pixels = float(np.hypot(x2 - x1, y2 - y1))

                # Convert to real dimensions using scale
                if self.scale:
                    length_inches = length_pixels * self.scale
                    length_feet = length_inches / 12
                else:
                    length_feet = length_pixels  # placeholder

                # Create measurement item
                measurement = MeasurementItem(
                    item_id=f"LINE_{i:04d}",
                    system_type="unknown",  # Would need OCR/classification
                    size="TBD",
                    length=length_feet,
                    location="TBD",
                )
                measurements.append(measurement)

        return measurements

    def manual_entry_measurements(self, measurement_data: List[Dict]) -> List[MeasurementItem]:
        """Process manually entered measurements from user."""

        measurements: List[MeasurementItem] = []

        for data in measurement_data:
            measurement = MeasurementItem(
                item_id=data.get("id", "MANUAL_" + str(len(measurements))),
                system_type=data["system_type"],
                size=data["size"],
                length=float(data["length"]),
                location=data.get("location", "Indoor"),
                elevation_changes=int(data.get("elevation_changes", 0)),
                fittings=data.get("fittings", {}),
                notes=data.get("notes", []),
            )
            measurements.append(measurement)

        return measurements


class PricingEngine:
    """Calculate material quantities and pricing."""

    def __init__(self, price_book_path: Optional[str] = None) -> None:
        self.prices = self._load_prices(price_book_path)
        self.labor_rates = {
            "duct_insulation": 0.45,  # hours per linear foot
            "pipe_insulation": 0.35,
            "jacketing": 0.25,
            "mastic": 0.15,
        }

    def _load_prices(self, price_book_path: Optional[str]) -> Dict[str, float]:
        """Load current market prices."""

        if price_book_path:
            with open(price_book_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # Default prices (would load from file/database in production)
        return {
            "fiberglass_1.5": 4.50,  # per linear foot for duct
            "fiberglass_2.0": 5.75,
            "elastomeric_0.5": 3.25,  # per linear foot for pipe
            "elastomeric_1.0": 4.50,
            "fsk_facing": 1.25,  # per square foot
            "aluminum_jacket": 8.50,  # per square foot
            "mastic": 0.75,  # per square foot
            "stainless_bands": 2.50,  # per band
            "adhesive": 12.50,  # per gallon
            "vapor_seal": 15.00,  # per gallon
        }

    def calculate_materials(self, measurements: List[MeasurementItem], specs: List[InsulationSpec]) -> List[MaterialItem]:
        """Calculate material quantities from measurements and specs."""

        materials: List[MaterialItem] = []

        for measurement in measurements:
            # Find applicable spec
            spec = self._find_applicable_spec(measurement, specs)

            if spec:
                # Calculate insulation material
                insulation = self._calculate_insulation(measurement, spec)
                materials.append(insulation)

                # Calculate facing/jacket
                if spec.facing or "aluminum_jacket" in spec.special_requirements:
                    jacket = self._calculate_jacketing(measurement, spec)
                    materials.append(jacket)

                # Calculate mastic
                if "mastic_coating" in spec.special_requirements:
                    mastic = self._calculate_mastic(measurement, spec)
                    materials.append(mastic)

                # Calculate fittings/accessories
                accessories = self._calculate_accessories(measurement, spec)
                materials.extend(accessories)

        return materials

    def _find_applicable_spec(self, measurement: MeasurementItem, specs: List[InsulationSpec]) -> Optional[InsulationSpec]:
        """Find the specification that applies to this measurement."""

        for spec in specs:
            if spec.system_type == measurement.system_type:
                # Could add size range checking here
                return spec
        return None

    def _calculate_insulation(self, measurement: MeasurementItem, spec: InsulationSpec) -> MaterialItem:
        """Calculate insulation material quantity and cost."""

        # Linear feet of insulation
        quantity = measurement.length

        # Add for fittings (rule of thumb: 1.5x for elbows, 2x for tees)
        fitting_multiplier = 1.0
        if measurement.fittings:
            fitting_multiplier += measurement.fittings.get("elbow", 0) * 0.5
            fitting_multiplier += measurement.fittings.get("tee", 0) * 1.0

        adjusted_quantity = quantity * fitting_multiplier

        # Get price key
        price_key = f"{spec.material}_{spec.thickness}"
        unit_price = self.prices.get(price_key, 5.0)  # default

        return MaterialItem(
            description=f"{spec.material.title()} Insulation {spec.thickness}\" - {measurement.size}",
            unit="LF",
            quantity=adjusted_quantity,
            unit_price=unit_price,
            total_price=adjusted_quantity * unit_price,
            category="insulation",
        )

    def _calculate_jacketing(self, measurement: MeasurementItem, spec: InsulationSpec) -> MaterialItem:
        """Calculate jacketing/facing material."""

        # Convert linear feet to square feet based on size
        # Simplified: assume average circumference
        size_diameter = self._parse_size_to_diameter(measurement.size)
        circumference = np.pi * (size_diameter + 2 * spec.thickness) / 12  # in feet
        square_feet = measurement.length * circumference

        if "aluminum_jacket" in spec.special_requirements:
            description = f"Aluminum Jacketing - {measurement.size}"
            unit_price = self.prices["aluminum_jacket"]
        else:
            facing_description = spec.facing or "Facing"
            description = f"{facing_description} Facing - {measurement.size}"
            unit_price = self.prices.get("fsk_facing", 1.25)

        return MaterialItem(
            description=description,
            unit="SF",
            quantity=square_feet,
            unit_price=unit_price,
            total_price=square_feet * unit_price,
            category="jacket",
        )

    def _calculate_mastic(self, measurement: MeasurementItem, spec: InsulationSpec) -> MaterialItem:
        """Calculate mastic coating."""

        size_diameter = self._parse_size_to_diameter(measurement.size)
        circumference = np.pi * (size_diameter + 2 * spec.thickness) / 12
        square_feet = measurement.length * circumference

        return MaterialItem(
            description="Mastic Vapor Seal Coating",
            unit="SF",
            quantity=square_feet,
            unit_price=self.prices["mastic"],
            total_price=square_feet * self.prices["mastic"],
            category="mastic",
        )

    def _calculate_accessories(self, measurement: MeasurementItem, spec: InsulationSpec) -> List[MaterialItem]:
        """Calculate bands, adhesive, etc."""

        accessories: List[MaterialItem] = []

        # Stainless steel bands (outdoor applications)
        if "stainless_bands" in spec.special_requirements:
            # Assume bands every 12 inches
            band_count = int(measurement.length) + 1
            accessories.append(
                MaterialItem(
                    description="Stainless Steel Bands",
                    unit="EA",
                    quantity=band_count,
                    unit_price=self.prices["stainless_bands"],
                    total_price=band_count * self.prices["stainless_bands"],
                    category="accessories",
                )
            )

        # Adhesive (estimate based on surface area)
        # Add adhesive calculation here

        return accessories

    def _parse_size_to_diameter(self, size: str) -> float:
        """Parse size string to diameter in inches."""

        # Handle various formats: "4\"", "4 inch", "4x6", etc.
        numbers = re.findall(r"\d+(?:\.\d+)?", size)
        if numbers:
            return float(numbers[0])
        return 12.0  # default

    def calculate_labor(self, materials: List[MaterialItem]) -> Tuple[float, float]:
        """Calculate labor hours and cost."""

        total_hours = 0.0

        for material in materials:
            if material.category == "insulation":
                if "duct" in material.description.lower():
                    hours = material.quantity * self.labor_rates["duct_insulation"]
                else:
                    hours = material.quantity * self.labor_rates["pipe_insulation"]
                total_hours += hours
            elif material.category == "jacket":
                total_hours += material.quantity * self.labor_rates["jacketing"]
            elif material.category == "mastic":
                total_hours += material.quantity * self.labor_rates["mastic"]

        # Add setup, cleanup, and supervision (20% overhead)
        total_hours *= 1.20

        labor_rate = 65.0
        return total_hours, total_hours * labor_rate


class QuoteGenerator:
    """Generate formal quotes and material lists."""

    def generate_quote(
        self,
        project_name: str,
        measurements: List[MeasurementItem],
        materials: List[MaterialItem],
        labor_hours: float,
        labor_cost: float,
        specs: List[InsulationSpec],
    ) -> ProjectQuote:
        """Generate complete project quote."""

        # Calculate totals
        material_total = sum(m.total_price for m in materials)
        subtotal = material_total + labor_cost

        # Add contingency (10% for unforeseen issues)
        contingency_percent = 10.0
        contingency = subtotal * (contingency_percent / 100)
        total = subtotal + contingency

        # Generate quote notes
        notes = self._generate_quote_notes(specs, measurements)

        # Generate material list for distributor
        material_list = self._generate_material_list(materials)

        quote = ProjectQuote(
            project_name=project_name,
            quote_number=f"Q{datetime.now().strftime('%Y%m%d-%H%M')}",
            date=datetime.now().strftime("%Y-%m-%d"),
            measurements=measurements,
            materials=materials,
            labor_hours=labor_hours,
            labor_rate=65.0,
            subtotal=subtotal,
            contingency_percent=contingency_percent,
            total=total,
            notes=notes,
            material_list=material_list,
        )

        return quote

    def _generate_quote_notes(self, specs: List[InsulationSpec], measurements: List[MeasurementItem]) -> List[str]:
        """Generate important notes for quote."""

        notes: List[str] = []

        # Check for special requirements
        outdoor = any("outdoor" in s.location for s in specs)
        if outdoor:
            notes.append("Weather protection jacketing included for outdoor applications")

        mastic_required = any("mastic_coating" in s.special_requirements for s in specs)
        if mastic_required:
            notes.append("Vapor seal mastic coating per specifications")

        # Check for elevation changes
        vertical_work = sum(m.elevation_changes for m in measurements)
        if vertical_work > 10:
            notes.append(f"Significant vertical work: {vertical_work} elevation changes")

        # Standard notes
        notes.extend(
            [
                "Pricing valid for 30 days",
                "Subject to final site verification",
                "Assumes clear access to work areas",
                "All work per project specifications and applicable codes",
            ]
        )

        return notes

    def _generate_material_list(self, materials: List[MaterialItem]) -> List[Dict]:
        """Generate consolidated material list for distributor."""

        # Consolidate by description
        consolidated: Dict[str, Dict[str, object]] = {}

        for material in materials:
            key = f"{material.description}|{material.unit}"
            if key in consolidated:
                consolidated[key]["quantity"] = float(consolidated[key]["quantity"]) + material.quantity
                consolidated[key]["total_price"] = float(consolidated[key]["total_price"]) + material.total_price
            else:
                consolidated[key] = {
                    "description": material.description,
                    "unit": material.unit,
                    "quantity": material.quantity,
                    "category": material.category,
                    "total_price": material.total_price,
                }

        # Sort by category
        material_list = sorted(consolidated.values(), key=lambda x: (x["category"], x["description"]))

        return material_list

    def export_quote_to_file(self, quote: ProjectQuote, output_path: str | Path) -> None:
        """Export quote to formatted text file."""

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("HVAC INSULATION QUOTE\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Project: {quote.project_name}\n")
            f.write(f"Quote Number: {quote.quote_number}\n")
            f.write(f"Date: {quote.date}\n\n")

            f.write("-" * 80 + "\n")
            f.write("MATERIALS\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Description':<50} {'Qty':>10} {'Unit':<6} {'Price':>12}\n")
            f.write("-" * 80 + "\n")

            for material in quote.materials:
                f.write(
                    f"{material.description:<50} {material.quantity:>10.2f} {material.unit:<6} "
                    f"${material.total_price:>11.2f}\n"
                )

            f.write("\n")
            f.write(f"{'Material Subtotal':>68} ${sum(m.total_price for m in quote.materials):>11.2f}\n")
            f.write(
                f"{'Labor (' + str(int(quote.labor_hours)) + ' hours @ $' + str(quote.labor_rate) + '/hr)':>68} "
                f"${quote.labor_hours * quote.labor_rate:>11.2f}\n"
            )
            f.write(f"{'Subtotal':>68} ${quote.subtotal:>11.2f}\n")
            f.write(
                f"{'Contingency (' + str(quote.contingency_percent) + '%)':>68} "
                f"${quote.subtotal * quote.contingency_percent / 100:>11.2f}\n"
            )
            f.write("=" * 80 + "\n")
            f.write(f"{'TOTAL':>68} ${quote.total:>11.2f}\n")
            f.write("=" * 80 + "\n\n")

            f.write("NOTES:\n")
            for i, note in enumerate(quote.notes, 1):
                f.write(f"{i}. {note}\n")

    def export_material_list(self, quote: ProjectQuote, output_path: str | Path) -> None:
        """Export material list for distributor."""

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            f.write("MATERIAL ORDER LIST\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Project: {quote.project_name}\n")
            f.write(f"Quote: {quote.quote_number}\n")
            f.write(f"Date: {quote.date}\n\n")

            current_category: Optional[str] = None
            for item in quote.material_list:
                if item["category"] != current_category:
                    current_category = str(item["category"])
                    f.write(f"\n{current_category.upper()}\n")
                    f.write("-" * 80 + "\n")

                f.write(f"{item['description']:<50} {item['quantity']:>10.2f} {item['unit']}\n")


def main() -> None:
    """Example usage of the HVAC Insulation Estimator."""

    print("HVAC Insulation Takeoff Estimator - Framework Demo")
    print("=" * 80)

    # Step 1: Extract specifications from PDF
    print("\n1. Extracting specifications from project specs PDF...")
    spec_extractor = SpecificationExtractor()
    # specs = spec_extractor.extract_from_pdf("project_specs.pdf")

    # Example manual specs for demo
    specs = [
        InsulationSpec(
            system_type="duct",
            size_range="all",
            thickness=1.5,
            material="fiberglass",
            facing="FSK",
            location="indoor",
        ),
        InsulationSpec(
            system_type="pipe",
            size_range="1-2 inch",
            thickness=1.0,
            material="elastomeric",
            location="outdoor",
            special_requirements=["aluminum_jacket", "stainless_bands"],
        ),
    ]

    print(f"   Found {len(specs)} insulation specifications")

    # Step 2: Extract measurements from drawings
    print("\n2. Processing measurements from drawings...")
    drawing_extractor = DrawingMeasurementExtractor(scale=48)

    # Example manual measurements for demo
    manual_measurements = [
        {
            "id": "DUCT-001",
            "system_type": "duct",
            "size": "18x12",
            "length": 125.5,
            "location": "Main corridor",
            "fittings": {"elbow": 3, "tee": 1},
        },
        {
            "id": "PIPE-001",
            "system_type": "pipe",
            "size": '2"',
            "length": 85.0,
            "location": "Exterior wall",
            "elevation_changes": 2,
            "fittings": {"elbow": 4},
        },
    ]

    measurements = drawing_extractor.manual_entry_measurements(manual_measurements)
    print(f"   Processed {len(measurements)} measurement items")

    # Step 3: Calculate materials and pricing
    print("\n3. Calculating materials and pricing...")
    pricing_engine = PricingEngine()
    materials = pricing_engine.calculate_materials(measurements, specs)
    labor_hours, labor_cost = pricing_engine.calculate_labor(materials)

    print(f"   Material items: {len(materials)}")
    print(f"   Labor hours: {labor_hours:.1f}")

    # Step 4: Generate quote
    print("\n4. Generating formal quote...")
    quote_generator = QuoteGenerator()
    quote = quote_generator.generate_quote(
        project_name="Example Commercial Building",
        measurements=measurements,
        materials=materials,
        labor_hours=labor_hours,
        labor_cost=labor_cost,
        specs=specs,
    )

    print(f"   Quote Number: {quote.quote_number}")
    print(f"   Total: ${quote.total:,.2f}")

    # Step 5: Export documents
    print("\n5. Exporting quote and material list...")
    output_dir = Path.cwd()
    quote_generator.export_quote_to_file(quote, output_dir / "quote.txt")
    quote_generator.export_material_list(quote, output_dir / "material_list.txt")

    print("\n" + "=" * 80)
    print("Processing complete!")
    print("Files created:")
    print("  - quote.txt (formal quote)")
    print("  - material_list.txt (distributor order list)")


if __name__ == "__main__":
    main()

