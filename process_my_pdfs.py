"""
Quick Start: Process YOUR PDF Specifications
Run this to extract insulation specs from your project PDFs
"""

import sys
from pathlib import Path
from typing import Iterable, List, Optional

import pdfplumber


INSULATION_KEYWORDS: List[str] = [
    "insulation",
    "thermal insulation",
    "mechanical insulation",
    "duct insulation",
    "pipe insulation",
    "fiberglass",
    "elastomeric",
    "FSK",
    "ASJ",
    "mastic",
    "vapor barrier",
    "jacketing",
]

THICKNESS_PATTERNS: Iterable[str] = (
    r"(\d+\.?\d*)\s*[\"']?\s*thick",
    r"thickness.*?(\d+\.?\d*)\s*[\"']",
    r"(\d+\.?\d*)\s*inch.*?insulation",
)

MATERIALS: Iterable[str] = (
    "fiberglass",
    "mineral wool",
    "elastomeric",
    "cellular glass",
    "polyisocyanurate",
)

FACINGS: Iterable[str] = (
    "FSK",
    "ASJ",
    "All Service Jacket",
    "Foil Scrim Kraft",
    "white jacket",
    "PVJ",
)


def extract_spec_text(pdf_path: Path) -> Optional[str]:
    """Extract all text from a PDF specification."""
    print(f"\n{'=' * 80}")
    print(f"Processing: {pdf_path}")
    print(f"{'=' * 80}\n")

    all_text: List[str] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}\n")

            for page_number, page in enumerate(pdf.pages, 1):
                text = page.extract_text()

                if text:
                    print(f"Page {page_number}: {len(text)} characters extracted")
                    all_text.append(text)
                else:
                    print(f"Page {page_number}: No text found (might be an image)")

        full_text = "\n\n".join(all_text)

        output_path = pdf_path.with_name(f"{pdf_path.stem}_extracted.txt")
        output_path.write_text(full_text, encoding="utf-8")

        print(f"\n✓ Extracted text saved to: {output_path}")

        _search_for_insulation_keywords(full_text.splitlines())
        return full_text

    except Exception as exc:  # noqa: BLE001 - provide user friendly error output
        print(f"❌ Error processing PDF: {exc}")
        return None


def _search_for_insulation_keywords(lines: List[str]) -> None:
    """Print context around discovered insulation keywords."""
    print(f"\n{'=' * 80}")
    print("SEARCHING FOR INSULATION SPECIFICATIONS...")
    print(f"{'=' * 80}\n")

    found_sections: List[str] = []

    for index, line in enumerate(lines):
        lowered = line.lower()
        for keyword in INSULATION_KEYWORDS:
            if keyword.lower() in lowered:
                start = max(0, index - 1)
                end = min(len(lines), index + 2)
                context = "\n".join(lines[start:end])
                found_sections.append(context)
                break

    if found_sections:
        print(f"Found {len(found_sections)} mentions of insulation!\n")
        print("Here are the first few:")
        for idx, section in enumerate(found_sections[:5], 1):
            print(f"\n--- Match {idx} ---")
            print(section)
            print("-" * 40)
    else:
        print("⚠ No insulation keywords found. This might not be an HVAC spec.")
        print("Try searching the extracted text file manually.\n")


def search_for_specs(text: str) -> None:
    """Look for specific insulation specifications."""
    import re

    print(f"\n{'=' * 80}")
    print("DETAILED SPEC SEARCH")
    print(f"{'=' * 80}\n")

    print("Looking for insulation thickness...")
    for pattern in THICKNESS_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            print(f"  → Found: {match.group(0)}")

    print("\nLooking for material types...")
    lowered_text = text.lower()
    for material in MATERIALS:
        if material in lowered_text:
            print(f"  → Found: {material}")

    print("\nLooking for facing types...")
    for facing in FACINGS:
        if facing.lower() in lowered_text:
            print(f"  → Found: {facing}")


def _print_intro() -> None:
    print("\n" + "=" * 80)
    print("HVAC INSULATION SPEC EXTRACTOR")
    print("=" * 80)


def main() -> None:
    """Main function to process PDFs."""
    _print_intro()

    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1]).expanduser()
    else:
        print("\nHow to use this script:")
        print("-" * 80)
        print("1. Drag and drop your PDF file onto this terminal window, OR")
        print("2. Type the full path to your PDF file")
        print("\nExample:")
        print('  python process_my_pdfs.py "C:/Projects/MyProject/specs.pdf"')
        print("  python process_my_pdfs.py /Users/you/Desktop/specs.pdf")
        print("\n" + "=" * 80 + "\n")

        user_input = input("Enter the path to your PDF file: ")
        pdf_path = Path(user_input.strip().strip('"').strip("'")).expanduser()

    if pdf_path.suffix.lower() != ".pdf":
        print(f"\n❌ Error: Expected a .pdf file, received: {pdf_path.suffix or 'no extension'}")
        return

    if not pdf_path.exists():
        print(f"\n❌ Error: File not found: {pdf_path}")
        print("\nMake sure:")
        print("  1. The file path is correct")
        print("  2. The file ends with .pdf")
        print("  3. You have permission to read the file")
        return

    text = extract_spec_text(pdf_path)

    if text:
        search_for_specs(text)

        print(f"\n{'=' * 80}")
        print("NEXT STEPS")
        print(f"{'=' * 80}")
        print("\n1. Review the extracted text file")
        print("2. Copy relevant specs to use in the main estimator")
        print("3. After Google Cloud training, this will be automatic!")
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
