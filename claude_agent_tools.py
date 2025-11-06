"""
Claude Agent Tools for Insulation Estimation
==============================================

This module provides tool implementations for the Claude Agents SDK
to enable intelligent, autonomous insulation estimation workflows.

Each tool is designed to work with the existing estimation engine
while adding AI-powered validation, cross-referencing, and recommendations.
"""

import os
import json
import base64
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import tempfile

# Import existing estimation modules
from hvac_insulation_estimator import (
    SpecificationExtractor,
    DrawingMeasurementExtractor,
    PricingEngine,
    QuoteGenerator,
    InsulationSpec,
    MeasurementItem,
    MaterialItem,
    ProjectQuote
)

# PDF processing
import pdfplumber
from pdf2image import convert_from_path
from PIL import Image
import io

# AI integration
from anthropic import Anthropic


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def pdf_to_base64_images(pdf_path: str, pages: Optional[List[int]] = None) -> List[Tuple[int, str]]:
    """
    Convert PDF pages to base64-encoded images for Claude vision analysis.

    Args:
        pdf_path: Path to PDF file
        pages: Optional list of specific page numbers (1-indexed)

    Returns:
        List of tuples: (page_number, base64_image_data)
    """
    try:
        # Convert PDF to images
        if pages:
            images = convert_from_path(pdf_path, first_page=min(pages), last_page=max(pages))
        else:
            images = convert_from_path(pdf_path)

        result = []
        for idx, image in enumerate(images):
            page_num = pages[idx] if pages else idx + 1

            # Convert to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            result.append((page_num, img_str))

        return result

    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF to images: {e}")


def extract_text_from_pdf(pdf_path: str, pages: Optional[List[int]] = None) -> Dict[int, str]:
    """
    Extract text from PDF pages.

    Args:
        pdf_path: Path to PDF file
        pages: Optional list of specific page numbers (1-indexed)

    Returns:
        Dictionary mapping page number to extracted text
    """
    text_by_page = {}

    with pdfplumber.open(pdf_path) as pdf:
        pages_to_process = pages if pages else range(1, len(pdf.pages) + 1)

        for page_num in pages_to_process:
            page = pdf.pages[page_num - 1]  # pdfplumber uses 0-indexed
            text = page.extract_text() or ""
            text_by_page[page_num] = text

    return text_by_page


def get_claude_client() -> Anthropic:
    """Get configured Anthropic client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return Anthropic(api_key=api_key)


# ============================================================================
# TOOL 1: EXTRACT PROJECT INFO
# ============================================================================

def extract_project_info(pdf_path: str) -> Dict[str, Any]:
    """
    Extract high-level project information from cover sheets and title blocks.

    This tool analyzes the first few pages of a PDF to identify:
    - Project name and number
    - Client/owner information
    - Location and address
    - Architect/Engineer of record
    - Project type and scope
    - Date and revision information

    Args:
        pdf_path: Path to PDF specification or drawing document

    Returns:
        Dictionary with project information and confidence scores
    """
    try:
        # Convert first 3 pages to images
        images = pdf_to_base64_images(pdf_path, pages=[1, 2, 3])

        # Also extract text for supplementary analysis
        text_by_page = extract_text_from_pdf(pdf_path, pages=[1, 2, 3])

        # Use Claude vision to analyze
        client = get_claude_client()

        # Build prompt with both image and text
        content_blocks = []

        for page_num, img_data in images:
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_data
                }
            })

            if page_num in text_by_page and text_by_page[page_num]:
                content_blocks.append({
                    "type": "text",
                    "text": f"Text extracted from page {page_num}:\n{text_by_page[page_num][:2000]}"
                })

        content_blocks.append({
            "type": "text",
            "text": """
            Analyze these document pages (typically cover sheets or title blocks) and extract project information.

            Extract the following if present:
            - project_name: Full project title
            - project_number: Project or job number
            - client: Client or owner organization
            - location: City, state, address
            - architect: Architect firm name
            - engineer: MEP or mechanical engineer name
            - project_type: (commercial, industrial, healthcare, educational, residential, etc.)
            - building_type: (office, hospital, school, warehouse, etc.)
            - total_square_footage: Building size if mentioned
            - system_description: Brief HVAC/mechanical system description
            - date: Document date
            - revision: Revision number or date

            Return as JSON with null for any fields not found.
            Also include a "confidence" field (0.0-1.0) indicating how confident you are in the extraction.
            Include a "notes" field with any relevant observations.

            Example response:
            {
                "project_name": "Downtown Medical Center HVAC Upgrade",
                "project_number": "2024-HC-0123",
                "client": "City Hospital Authority",
                "location": "Phoenix, AZ",
                "architect": "Smith & Associates",
                "engineer": "Johnson MEP Engineers",
                "project_type": "healthcare",
                "building_type": "hospital",
                "total_square_footage": 125000,
                "system_description": "Replacement of existing rooftop units and ductwork",
                "date": "2024-09-15",
                "revision": "R2",
                "confidence": 0.95,
                "notes": "Information extracted from title block on page 1"
            }
            """
        })

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": content_blocks
            }]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "{" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
        else:
            json_str = response_text

        project_info = json.loads(json_str)

        return {
            "success": True,
            "project_info": project_info,
            "source_file": pdf_path,
            "pages_analyzed": [1, 2, 3]
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "project_info": None
        }


# ============================================================================
# TOOL 2: EXTRACT SPECIFICATIONS
# ============================================================================

def extract_specifications(pdf_path: str, pages: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Extract insulation specifications from specification documents.

    Uses both Claude vision analysis and the existing SpecificationExtractor
    for robust specification detection. Identifies:
    - System types (duct, pipe, equipment)
    - Size ranges
    - Material types and thicknesses
    - Facing requirements
    - Special requirements (mastic, jacketing, etc.)
    - Location conditions (indoor, outdoor, exposed)

    Args:
        pdf_path: Path to PDF specification document
        pages: Optional list of specific page numbers to analyze

    Returns:
        Dictionary with specifications list, confidence scores, and warnings
    """
    try:
        # Use existing extractor as baseline
        extractor = SpecificationExtractor()

        # Extract text for pattern matching
        text_by_page = extract_text_from_pdf(pdf_path, pages)
        full_text = "\n".join(text_by_page.values())

        # Use existing regex-based extraction
        baseline_specs = extractor.extract_from_text(full_text)

        # Convert a few pages to images for Claude vision analysis
        pages_to_analyze = pages[:5] if pages and len(pages) > 5 else pages
        if not pages_to_analyze:
            # Analyze first 10 pages if not specified
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                pages_to_analyze = list(range(1, min(11, total_pages + 1)))

        images = pdf_to_base64_images(pdf_path, pages=pages_to_analyze)

        # Use Claude for enhanced analysis
        client = get_claude_client()

        all_specs = []

        for page_num, img_data in images:
            content_blocks = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_data
                    }
                },
                {
                    "type": "text",
                    "text": f"""
                    Analyze this specification page for HVAC insulation requirements.

                    Look for specifications describing:

                    1. **System Type**: Duct, Pipe, or Equipment insulation
                    2. **Size Range**: Which sizes this spec applies to (e.g., "4-12 inch duct", "1-2 inch pipe", "all sizes")
                    3. **Material**: Fiberglass, elastomeric, cellular glass, mineral wool, etc.
                    4. **Thickness**: Insulation thickness in inches
                    5. **Facing**: FSK, ASJ, Aluminum, PVC, unfaced, etc.
                    6. **Special Requirements**:
                       - Mastic coating
                       - Aluminum jacketing
                       - Stainless steel bands
                       - Vapor barriers
                       - Weatherproofing
                    7. **Location**: Indoor, outdoor, exposed to weather, mechanical room, etc.

                    Example specifications to look for:
                    - "Duct insulation shall be 2 inch fiberglass with FSK facing"
                    - "Chilled water piping 2 inch and under: 1 inch elastomeric"
                    - "Outdoor ductwork: Aluminum jacket over 1.5 inch fiberglass"

                    Page text (if available): {text_by_page.get(page_num, 'N/A')[:1500]}

                    Return JSON array of specification objects:
                    [
                      {{
                        "system_type": "duct|pipe|equipment",
                        "size_range": "description of size range",
                        "thickness": 1.5,
                        "material": "fiberglass|elastomeric|cellular_glass|mineral_wool",
                        "facing": "FSK|ASJ|Aluminum|PVC|unfaced|null",
                        "special_requirements": ["mastic", "aluminum_jacket", "stainless_bands"],
                        "location": "indoor|outdoor|exposed",
                        "confidence": 0.0-1.0,
                        "spec_text": "original spec language",
                        "page_number": {page_num}
                      }}
                    ]

                    Return empty array [] if no specifications found on this page.
                    """
                }
            ]

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3096,
                messages=[{
                    "role": "user",
                    "content": content_blocks
                }]
            )

            # Parse response
            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "[" in response_text:
                json_start = response_text.find("[")
                json_end = response_text.rfind("]") + 1
                json_str = response_text[json_start:json_end]
            else:
                json_str = "[]"

            page_specs = json.loads(json_str)
            all_specs.extend(page_specs)

        # Merge with baseline specs and deduplicate
        # Combine Claude and regex results, preferring Claude for conflicts
        final_specs = all_specs  # Claude specs take priority

        # Validate specifications
        warnings = []
        for spec in final_specs:
            # Check for outdoor without weather protection
            if spec.get("location") == "outdoor":
                if "aluminum_jacket" not in spec.get("special_requirements", []):
                    warnings.append(
                        f"Outdoor {spec['system_type']} spec on page {spec.get('page_number')} "
                        f"may need aluminum jacketing or weather protection"
                    )

            # Check for reasonable thickness ranges
            thickness = spec.get("thickness", 0)
            if thickness < 0.5 or thickness > 4:
                warnings.append(
                    f"Unusual thickness {thickness}\" on page {spec.get('page_number')} - verify"
                )

        return {
            "success": True,
            "specifications": final_specs,
            "count": len(final_specs),
            "warnings": warnings,
            "pages_analyzed": pages_to_analyze,
            "source_file": pdf_path
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "specifications": [],
            "warnings": [f"Extraction failed: {e}"]
        }


# ============================================================================
# TOOL 3: EXTRACT MEASUREMENTS
# ============================================================================

def extract_measurements(pdf_path: str, scale: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract measurements from architectural/mechanical drawings.

    Analyzes drawing sheets to identify:
    - Duct sizes and lengths
    - Pipe sizes and lengths
    - Fitting counts (elbows, tees, valves)
    - Drawing scale
    - Location/zone information
    - Equipment items

    Args:
        pdf_path: Path to PDF drawing document
        scale: Optional drawing scale (e.g., "1/4\" = 1'-0\"")

    Returns:
        Dictionary with measurements list and metadata
    """
    try:
        # Convert drawing pages to images
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

        # Limit to first 15 pages for performance
        pages_to_analyze = list(range(1, min(16, total_pages + 1)))
        images = pdf_to_base64_images(pdf_path, pages=pages_to_analyze)

        client = get_claude_client()

        all_measurements = []
        detected_scale = scale

        for page_num, img_data in images:
            content_blocks = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_data
                    }
                },
                {
                    "type": "text",
                    "text": f"""
                    Analyze this mechanical drawing sheet to extract HVAC insulation takeoff measurements.

                    Extract:

                    1. **Drawing Scale**: Look for scale notation (e.g., "1/4\" = 1'-0\"", "SCALE: 1/8\" = 1'-0\"")

                    2. **Ductwork Measurements**:
                       - Size: Width x Height (e.g., "18x12", "24x18")
                       - Length: Linear feet
                       - Location: Room name, zone, or area
                       - Fittings: Count of elbows, tees, transitions

                    3. **Piping Measurements**:
                       - Size: Diameter (e.g., "2\"", "4\" CHW", "1.5\" HW")
                       - Length: Linear feet
                       - System: CHW (chilled water), HW (hot water), CW (condenser water), etc.
                       - Location: Room or area
                       - Fittings: Elbows, tees, valves

                    4. **Equipment**:
                       - Type: AHU, FCU, boiler, chiller, etc.
                       - Size/capacity if shown
                       - Quantity

                    Look for:
                    - Dimension lines and callouts
                    - Equipment schedules
                    - Legend items
                    - Line types indicating duct vs pipe

                    Current scale: {detected_scale or "Auto-detect from drawing"}

                    Return JSON:
                    {{
                      "scale": "detected or provided scale",
                      "measurements": [
                        {{
                          "item_id": "D-001",
                          "system_type": "duct|pipe",
                          "size": "18x12" or "2\"",
                          "length": 45.5,
                          "location": "Room 101",
                          "fittings": {{"elbow": 2, "tee": 1}},
                          "notes": ["Supply duct", "Exposed to weather"],
                          "confidence": 0.0-1.0
                        }}
                      ],
                      "equipment": [
                        {{
                          "type": "AHU",
                          "model": "AHU-1",
                          "capacity": "10 ton",
                          "quantity": 1
                        }}
                      ],
                      "page_info": {{
                        "sheet_number": "M-2.1",
                        "sheet_title": "Second Floor Mechanical Plan"
                      }}
                    }}

                    If the page is not a mechanical drawing (e.g., cover sheet, specs, details),
                    return empty measurements array.
                    """
                }
            ]

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": content_blocks
                }]
            )

            # Parse response
            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
            else:
                continue

            page_data = json.loads(json_str)

            # Update scale if detected
            if not detected_scale and page_data.get("scale"):
                detected_scale = page_data["scale"]

            # Add page number to measurements
            for measurement in page_data.get("measurements", []):
                measurement["page_number"] = page_num
                measurement["sheet_number"] = page_data.get("page_info", {}).get("sheet_number", f"Page {page_num}")

            all_measurements.extend(page_data.get("measurements", []))

        # Generate summary statistics
        total_duct_lf = sum(m["length"] for m in all_measurements if m["system_type"] == "duct")
        total_pipe_lf = sum(m["length"] for m in all_measurements if m["system_type"] == "pipe")

        return {
            "success": True,
            "measurements": all_measurements,
            "count": len(all_measurements),
            "scale": detected_scale,
            "summary": {
                "total_duct_lf": round(total_duct_lf, 1),
                "total_pipe_lf": round(total_pipe_lf, 1),
                "total_items": len(all_measurements)
            },
            "pages_analyzed": pages_to_analyze,
            "source_file": pdf_path
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "measurements": [],
            "summary": {}
        }


# ============================================================================
# TOOL 4: VALIDATE SPECIFICATIONS
# ============================================================================

def validate_specifications(specifications: List[Dict]) -> Dict[str, Any]:
    """
    Validate specifications against industry standards and best practices.

    Checks for:
    - Material/thickness compatibility
    - Climate-appropriate specifications
    - Indoor vs outdoor requirements
    - Missing critical details
    - Conflicting requirements

    Args:
        specifications: List of specification dictionaries

    Returns:
        Validation report with status, warnings, and recommendations
    """
    warnings = []
    errors = []
    recommendations = []

    for idx, spec in enumerate(specifications):
        spec_id = f"Spec #{idx + 1}"

        # Check for required fields
        required_fields = ["system_type", "material", "thickness"]
        missing_fields = [f for f in required_fields if not spec.get(f)]
        if missing_fields:
            errors.append(f"{spec_id}: Missing required fields: {', '.join(missing_fields)}")

        # Validate thickness ranges
        thickness = spec.get("thickness", 0)
        system_type = spec.get("system_type", "")

        if system_type == "duct" and thickness < 1.0:
            warnings.append(f"{spec_id}: Duct insulation < 1\" may not meet energy codes")

        if system_type == "pipe" and thickness < 0.5:
            warnings.append(f"{spec_id}: Pipe insulation < 0.5\" may be inadequate")

        # Check outdoor specifications
        location = spec.get("location", "")
        special_reqs = spec.get("special_requirements", [])

        if location == "outdoor":
            if "aluminum_jacket" not in special_reqs and "pvc_jacket" not in special_reqs:
                warnings.append(f"{spec_id}: Outdoor insulation should have weather protection jacketing")

            if "stainless_bands" not in special_reqs:
                recommendations.append(f"{spec_id}: Consider stainless steel bands for outdoor installations")

        # Check material compatibility
        material = spec.get("material", "")

        if material == "elastomeric" and spec.get("facing"):
            warnings.append(f"{spec_id}: Elastomeric typically doesn't use separate facing")

        if material == "fiberglass" and not spec.get("facing") and location == "exposed":
            warnings.append(f"{spec_id}: Exposed fiberglass insulation should have facing or jacketing")

        # Check for vapor barriers on cold systems
        if "chilled" in str(spec).lower() or "cold" in str(spec).lower():
            if "vapor_seal" not in special_reqs and material != "elastomeric":
                recommendations.append(f"{spec_id}: Chilled water systems should have vapor barrier")

    # Overall assessment
    if errors:
        status = "error"
    elif warnings:
        status = "warning"
    else:
        status = "pass"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "recommendations": recommendations,
        "specifications_validated": len(specifications),
        "summary": f"Validated {len(specifications)} specifications: {len(errors)} errors, {len(warnings)} warnings"
    }


# ============================================================================
# TOOL 5: CROSS-REFERENCE DATA
# ============================================================================

def cross_reference_data(
    specifications: List[Dict],
    measurements: List[Dict],
    project_info: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Cross-reference specifications, measurements, and project info for consistency.

    Validates:
    - Every measurement has a matching specification
    - Specifications cover all system types found
    - Size ranges are appropriate
    - Special requirements are consistently applied

    Args:
        specifications: List of InsulationSpec dictionaries
        measurements: List of MeasurementItem dictionaries
        project_info: Optional project information dictionary

    Returns:
        Cross-reference report with conflicts and missing items
    """
    conflicts = []
    missing_specs = []
    missing_measurements = []
    matched_items = []

    # Check each measurement has a matching spec
    for measurement in measurements:
        system_type = measurement.get("system_type")
        size = measurement.get("size", "")
        location = measurement.get("location", "")

        # Find matching specifications
        matching_specs = [
            s for s in specifications
            if s.get("system_type") == system_type
        ]

        if not matching_specs:
            missing_specs.append({
                "measurement_id": measurement.get("item_id"),
                "system_type": system_type,
                "reason": f"No specification found for {system_type} insulation"
            })
        else:
            matched_items.append({
                "measurement_id": measurement.get("item_id"),
                "specification": matching_specs[0],
                "match_quality": "exact" if len(matching_specs) == 1 else "multiple"
            })

    # Check each specification has measurements
    for spec in specifications:
        system_type = spec.get("system_type")

        matching_measurements = [
            m for m in measurements
            if m.get("system_type") == system_type
        ]

        if not matching_measurements:
            missing_measurements.append({
                "system_type": system_type,
                "spec_material": spec.get("material"),
                "spec_thickness": spec.get("thickness"),
                "reason": f"Specification exists but no {system_type} measurements found"
            })

    # Determine overall status
    if conflicts or missing_specs:
        status = "issues_found"
    elif missing_measurements:
        status = "warning"
    else:
        status = "validated"

    return {
        "status": status,
        "matched_items": len(matched_items),
        "conflicts": conflicts,
        "missing_specifications": missing_specs,
        "missing_measurements": missing_measurements,
        "summary": {
            "total_measurements": len(measurements),
            "total_specifications": len(specifications),
            "matched": len(matched_items),
            "unmatched_measurements": len(missing_specs),
            "unused_specifications": len(missing_measurements)
        }
    }


# ============================================================================
# TOOL 6: CALCULATE PRICING
# ============================================================================

def calculate_pricing(
    specifications: List[Dict],
    measurements: List[Dict],
    pricebook: Optional[Dict] = None,
    markup_percent: float = 15.0,
    labor_rate: float = 65.0
) -> Dict[str, Any]:
    """
    Calculate complete pricing for insulation project.

    Uses the existing PricingEngine with provided pricebook and parameters.

    Args:
        specifications: List of specification dictionaries
        measurements: List of measurement dictionaries
        pricebook: Optional custom pricebook dict
        markup_percent: Markup percentage (default 15%)
        labor_rate: Labor rate per hour (default $65/hr)

    Returns:
        Complete pricing breakdown with materials, labor, and totals
    """
    try:
        # Initialize pricing engine
        engine = PricingEngine(
            pricebook=pricebook,
            markup_percent=markup_percent,
            labor_rate=labor_rate
        )

        # Calculate materials and labor
        material_items = []
        total_labor_hours = 0.0

        for measurement in measurements:
            # Find matching specification
            system_type = measurement.get("system_type")
            matching_spec = next(
                (s for s in specifications if s.get("system_type") == system_type),
                None
            )

            if not matching_spec:
                continue

            # Calculate for this item
            result = engine.calculate_item(
                measurement=measurement,
                specification=matching_spec
            )

            material_items.extend(result["materials"])
            total_labor_hours += result["labor_hours"]

        # Calculate totals
        material_subtotal = sum(item["total_price"] for item in material_items)
        labor_cost = total_labor_hours * labor_rate
        subtotal = material_subtotal + labor_cost

        # Apply contingency (default 10%)
        contingency_percent = 10.0
        contingency = subtotal * (contingency_percent / 100)
        total = subtotal + contingency

        return {
            "success": True,
            "materials": material_items,
            "material_subtotal": round(material_subtotal, 2),
            "labor_hours": round(total_labor_hours, 2),
            "labor_rate": labor_rate,
            "labor_cost": round(labor_cost, 2),
            "subtotal": round(subtotal, 2),
            "contingency_percent": contingency_percent,
            "contingency": round(contingency, 2),
            "total": round(total, 2),
            "summary": f"${round(total, 2):,.2f} ({len(material_items)} line items, {round(total_labor_hours, 1)} labor hours)"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total": 0
        }


# ============================================================================
# TOOL 7: GENERATE QUOTE
# ============================================================================

def generate_quote(
    project_info: Dict,
    specifications: List[Dict],
    measurements: List[Dict],
    pricing: Dict
) -> Dict[str, Any]:
    """
    Generate a comprehensive professional quote document.

    Creates a complete quote with:
    - Executive summary
    - Project information
    - Scope of work
    - Detailed material list
    - Pricing breakdown
    - Terms and conditions

    Args:
        project_info: Project information dictionary
        specifications: List of specifications
        measurements: List of measurements
        pricing: Pricing calculation results

    Returns:
        Quote document with formatted text and export-ready data
    """
    try:
        generator = QuoteGenerator()

        # Build ProjectQuote object
        quote_obj = generator.create_quote(
            project_info=project_info,
            specifications=specifications,
            measurements=measurements,
            pricing=pricing
        )

        # Generate formatted quote text
        quote_text = generator.format_quote(quote_obj)

        # Generate material list for distributor
        material_list = generator.generate_material_list(pricing["materials"])

        return {
            "success": True,
            "quote_text": quote_text,
            "material_list": material_list,
            "quote_number": quote_obj.quote_number,
            "total": pricing["total"],
            "project_name": project_info.get("project_name", "Untitled Project")
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# TOOL REGISTRY
# ============================================================================

AGENT_TOOLS = {
    "extract_project_info": extract_project_info,
    "extract_specifications": extract_specifications,
    "extract_measurements": extract_measurements,
    "validate_specifications": validate_specifications,
    "cross_reference_data": cross_reference_data,
    "calculate_pricing": calculate_pricing,
    "generate_quote": generate_quote,
}


def get_tool_schemas() -> List[Dict]:
    """
    Get OpenAPI-style tool schemas for Claude API.

    Returns:
        List of tool definition dictionaries
    """
    return [
        {
            "name": "extract_project_info",
            "description": "Extracts project information from PDF cover sheets and title blocks including project name, client, location, and system description",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF document"
                    }
                },
                "required": ["pdf_path"]
            }
        },
        {
            "name": "extract_specifications",
            "description": "Extracts insulation specifications from specification documents including system types, materials, thicknesses, facing, and special requirements",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF specification document"
                    },
                    "pages": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Optional list of specific page numbers to analyze (1-indexed)"
                    }
                },
                "required": ["pdf_path"]
            }
        },
        {
            "name": "extract_measurements",
            "description": "Extracts measurements from mechanical drawings including duct/pipe sizes, lengths, fittings, and locations",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF drawing document"
                    },
                    "scale": {
                        "type": "string",
                        "description": "Optional drawing scale (e.g., '1/4 = 1-0')"
                    }
                },
                "required": ["pdf_path"]
            }
        },
        {
            "name": "validate_specifications",
            "description": "Validates specifications against industry standards and identifies missing requirements or conflicts",
            "input_schema": {
                "type": "object",
                "properties": {
                    "specifications": {
                        "type": "array",
                        "description": "Array of specification objects to validate"
                    }
                },
                "required": ["specifications"]
            }
        },
        {
            "name": "cross_reference_data",
            "description": "Cross-references specifications and measurements to ensure consistency and identify gaps",
            "input_schema": {
                "type": "object",
                "properties": {
                    "specifications": {
                        "type": "array",
                        "description": "Array of specification objects"
                    },
                    "measurements": {
                        "type": "array",
                        "description": "Array of measurement objects"
                    },
                    "project_info": {
                        "type": "object",
                        "description": "Optional project information object"
                    }
                },
                "required": ["specifications", "measurements"]
            }
        },
        {
            "name": "calculate_pricing",
            "description": "Calculates complete pricing including materials, labor, markup, and contingency",
            "input_schema": {
                "type": "object",
                "properties": {
                    "specifications": {
                        "type": "array",
                        "description": "Array of specification objects"
                    },
                    "measurements": {
                        "type": "array",
                        "description": "Array of measurement objects"
                    },
                    "pricebook": {
                        "type": "object",
                        "description": "Optional custom pricebook dictionary"
                    },
                    "markup_percent": {
                        "type": "number",
                        "description": "Markup percentage (default 15.0)"
                    },
                    "labor_rate": {
                        "type": "number",
                        "description": "Labor rate per hour (default 65.0)"
                    }
                },
                "required": ["specifications", "measurements"]
            }
        },
        {
            "name": "generate_quote",
            "description": "Generates a comprehensive professional quote document with all project details",
            "input_schema": {
                "type": "object",
                "properties": {
                    "project_info": {
                        "type": "object",
                        "description": "Project information object"
                    },
                    "specifications": {
                        "type": "array",
                        "description": "Array of specification objects"
                    },
                    "measurements": {
                        "type": "array",
                        "description": "Array of measurement objects"
                    },
                    "pricing": {
                        "type": "object",
                        "description": "Pricing calculation results object"
                    }
                },
                "required": ["project_info", "specifications", "measurements", "pricing"]
            }
        }
    ]
