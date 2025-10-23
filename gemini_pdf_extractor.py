"""AI-Powered PDF Extraction using Google Gemini API

Extracts insulation specifications, measurements, and project information
from PDF documents using Google's Gemini vision and text models.
"""

import base64
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import pdfplumber
    from PIL import Image
except ImportError:
    pdfplumber = None
    Image = None


class GeminiPDFExtractor:
    """AI-powered PDF extraction using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini PDF extractor.

        Args:
            api_key: Google API key for Gemini. If None, will try environment variable.
        """
        if genai is None:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)

        # Use Gemini 2.0 Flash for vision tasks
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.text_model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def extract_project_info(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract project information from PDF title block or cover page.

        Returns:
            Dictionary with project_name, location, contractor, date, etc.
        """
        try:
            # Convert first page to image
            images = self._pdf_to_images(pdf_path, max_pages=2)

            if not images:
                return {"project_name": "Unknown Project", "location": "Not specified"}

            # Prepare prompt for project info extraction
            prompt = """Analyze this document and extract the following project information:
- Project Name
- Project Location/Address
- General Contractor (if mentioned)
- Project Number (if any)
- Date (if any)

Look for title blocks, cover pages, or project headers.
Return the information in JSON format like this:
{
    "project_name": "Project name here",
    "location": "City, State or address",
    "contractor": "Company name",
    "project_number": "Number if found",
    "date": "Date if found"
}

If information is not found, use "Not specified" for that field.
Only return the JSON, no other text."""

            # Send to Gemini
            response = self.vision_model.generate_content([prompt, images[0]])
            text = response.text.strip()

            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
            if json_match:
                project_info = json.loads(json_match.group())
                return project_info
            else:
                return {"project_name": "Unknown Project", "location": "Not specified"}

        except Exception as e:
            print(f"Error extracting project info: {e}")
            return {"project_name": "Unknown Project", "location": "Not specified"}

    def extract_specifications(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract insulation specifications from PDF using AI.

        Returns:
            List of specification dictionaries
        """
        try:
            # Convert PDF pages to images
            images = self._pdf_to_images(pdf_path, max_pages=50)

            if not images:
                return []

            # Prepare prompt for specification extraction
            prompt = """You are an expert mechanical insulation estimator. Analyze this PDF document and extract ALL insulation specifications.

Look for:
1. Ductwork insulation requirements (material, thickness, facing)
2. Piping insulation requirements (material, thickness, jacketing)
3. Equipment insulation specifications
4. Special requirements (outdoor, indoor, exposed to weather)
5. Size ranges that apply to each specification

Common materials: fiberglass, elastomeric, cellular glass, mineral wool
Common facings: FSK, ASJ, PVC jacket, aluminum jacket
Common thicknesses: 0.5", 1", 1.5", 2", 2.5", 3"

For each specification found, return JSON in this format:
[
    {
        "system_type": "duct" or "pipe" or "equipment",
        "size_range": "size range like '1-2 inch' or '4-12 inch' or 'all'",
        "thickness": thickness in decimal (e.g., 1.5 for 1.5"),
        "material": "fiberglass" or "elastomeric" or "cellular_glass" or "mineral_wool",
        "facing": "FSK" or "ASJ" or "PVC Jacket" or "Aluminum Jacket" or null,
        "location": "indoor" or "outdoor" or "exposed",
        "special_requirements": ["aluminum_jacket", "mastic_coating", "stainless_bands"] or []
    }
]

Extract ALL specifications you find. Be thorough.
Only return valid JSON array, no other text."""

            all_specs = []

            # Process in batches of images (Gemini can handle multiple images)
            batch_size = 10
            for i in range(0, len(images), batch_size):
                batch = images[i:i+batch_size]

                try:
                    # Send batch to Gemini
                    content = [prompt] + batch
                    response = self.vision_model.generate_content(content)
                    text = response.text.strip()

                    # Extract JSON array from response
                    json_match = re.search(r'\[.*\]', text, re.DOTALL)
                    if json_match:
                        specs = json.loads(json_match.group())
                        all_specs.extend(specs)

                except Exception as e:
                    print(f"Error processing batch {i//batch_size + 1}: {e}")
                    continue

            return all_specs

        except Exception as e:
            print(f"Error extracting specifications: {e}")
            return []

    def extract_measurements_from_drawings(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract measurements from mechanical drawings using AI vision.

        Returns:
            List of measurement dictionaries
        """
        try:
            # Convert drawing pages to images
            images = self._pdf_to_images(pdf_path, max_pages=30)

            if not images:
                return []

            # Prepare prompt for measurement extraction
            prompt = """You are an expert mechanical insulation estimator analyzing mechanical drawings.

Extract ALL ductwork and piping measurements from these drawings.

For each item, identify:
1. System type (duct or pipe)
2. Size (diameter for pipes like "2\"", dimensions for ducts like "18x12")
3. Length in linear feet (estimate from scale if shown)
4. Location/area description
5. Count fittings: elbows, tees, crosses
6. Any elevation changes

Return measurements in JSON format:
[
    {
        "item_id": "DUCT-001" or "PIPE-001" (number sequentially),
        "system_type": "duct" or "pipe",
        "size": "18x12" or "2\"" or similar,
        "length": estimated length in feet as a number,
        "location": "describe area/room",
        "elbows": count of elbows,
        "tees": count of tees,
        "elevation_changes": count of vertical runs
    }
]

Be thorough and extract ALL visible ductwork and piping.
Only return valid JSON array, no other text."""

            all_measurements = []

            # Process in batches
            batch_size = 5  # Smaller batches for complex drawings
            for i in range(0, len(images), batch_size):
                batch = images[i:i+batch_size]

                try:
                    # Send batch to Gemini
                    content = [prompt] + batch
                    response = self.vision_model.generate_content(content)
                    text = response.text.strip()

                    # Extract JSON array from response
                    json_match = re.search(r'\[.*\]', text, re.DOTALL)
                    if json_match:
                        measurements = json.loads(json_match.group())
                        all_measurements.extend(measurements)

                except Exception as e:
                    print(f"Error processing drawing batch {i//batch_size + 1}: {e}")
                    continue

            return all_measurements

        except Exception as e:
            print(f"Error extracting measurements: {e}")
            return []

    def _pdf_to_images(self, pdf_path: str, max_pages: Optional[int] = None) -> List[Image.Image]:
        """
        Convert PDF pages to PIL Images for Gemini vision.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to convert

        Returns:
            List of PIL Image objects
        """
        if pdfplumber is None or Image is None:
            raise ImportError("pdfplumber and PIL required for PDF processing")

        images = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_to_process = min(len(pdf.pages), max_pages) if max_pages else len(pdf.pages)

                for i in range(pages_to_process):
                    try:
                        # Convert page to image
                        page = pdf.pages[i]
                        pil_image = page.to_image(resolution=150).original

                        images.append(pil_image)

                    except Exception as e:
                        print(f"Error converting page {i+1}: {e}")
                        continue

        except Exception as e:
            print(f"Error opening PDF: {e}")

        return images

    def process_complete_project(self, spec_pdf_path: str, drawing_pdf_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process complete project: extract project info, specs, and measurements.

        Args:
            spec_pdf_path: Path to specification PDF
            drawing_pdf_path: Optional path to drawing PDF (if separate)

        Returns:
            Dictionary with project_info, specifications, measurements
        """
        print("🤖 AI Extraction: Starting project analysis...")

        # Extract project info
        print("  📋 Extracting project information...")
        project_info = self.extract_project_info(spec_pdf_path)
        print(f"     ✓ Project: {project_info.get('project_name', 'Unknown')}")

        # Extract specifications
        print("  📝 Extracting insulation specifications...")
        specifications = self.extract_specifications(spec_pdf_path)
        print(f"     ✓ Found {len(specifications)} specifications")

        # Extract measurements from drawings
        measurements = []
        if drawing_pdf_path:
            print("  📐 Extracting measurements from drawings...")
            measurements = self.extract_measurements_from_drawings(drawing_pdf_path)
            print(f"     ✓ Found {len(measurements)} measurements")

        print("✓ AI Extraction complete!")

        return {
            "project_info": project_info,
            "specifications": specifications,
            "measurements": measurements,
        }


def test_extractor():
    """Test the Gemini PDF extractor."""
    import os

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        return

    extractor = GeminiPDFExtractor(api_key=api_key)

    # Test with sample PDF
    print("Testing AI PDF Extraction...")
    # results = extractor.process_complete_project("sample_specs.pdf")
    # print(json.dumps(results, indent=2))


if __name__ == "__main__":
    test_extractor()
