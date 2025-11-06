"""
Pydantic Data Models
====================

Structured data models with validation for type safety and data quality.
Prevents malformed data and provides clear error messages.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# SPECIFICATION MODELS
# ============================================================================

class InsulationSpecExtracted(BaseModel):
    """
    Validated insulation specification extracted from documents.

    Uses Pydantic for automatic validation and type safety.
    """

    system_type: Literal[
        "supply_duct", "return_duct", "exhaust_duct",
        "chilled_water_pipe", "hot_water_pipe", "steam_pipe",
        "condenser_water_pipe", "refrigerant_pipe", "equipment"
    ] = Field(description="Specific system type")

    size_range: str = Field(
        description="Size range this spec applies to (e.g., '4-12 inch', '1-2 inch pipe')",
        min_length=1
    )

    thickness: float = Field(
        gt=0,
        le=6,
        description="Insulation thickness in inches"
    )

    material: Literal[
        "fiberglass", "elastomeric", "cellular_glass",
        "mineral_wool", "polyisocyanurate", "phenolic"
    ] = Field(description="Insulation material type")

    facing: Optional[Literal[
        "FSK", "ASJ", "PSK", "aluminum", "PVC", "vinyl", "unfaced"
    ]] = Field(default=None, description="Facing type if applicable")

    special_requirements: List[str] = Field(
        default_factory=list,
        description="Special requirements (mastic, jacketing, etc.)"
    )

    location: Literal[
        "indoor", "outdoor", "exposed_to_weather",
        "concealed", "mechanical_room"
    ] = Field(description="Installation location/environment")

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for extraction"
    )

    spec_text: str = Field(
        description="Original specification language from document",
        min_length=1
    )

    page_number: int = Field(
        gt=0,
        description="Source page number"
    )

    section_number: Optional[str] = Field(
        default=None,
        description="Specification section number (e.g., '23 07 13')"
    )

    @validator('thickness')
    def validate_thickness(cls, v):
        """Ensure thickness is reasonable."""
        if v < 0.5:
            logger.warning(f"Very thin insulation: {v}\" - verify")
        if v > 4:
            logger.warning(f"Very thick insulation: {v}\" - verify")
        return v

    @validator('special_requirements')
    def normalize_requirements(cls, v):
        """Normalize special requirements to standard terms."""
        normalized = []
        for req in v:
            req_lower = req.lower().strip()

            # Map variations to standard terms
            if "mastic" in req_lower or "seal" in req_lower:
                normalized.append("mastic_seal")
            elif "aluminum" in req_lower and "jacket" in req_lower:
                normalized.append("aluminum_jacket")
            elif "stainless" in req_lower and ("band" in req_lower or "strap" in req_lower):
                normalized.append("stainless_bands")
            elif "vapor" in req_lower and "barrier" in req_lower:
                normalized.append("vapor_barrier")
            elif "weather" in req_lower:
                normalized.append("weatherproofing")
            else:
                normalized.append(req)

        return list(set(normalized))  # Remove duplicates

    @root_validator
    def check_outdoor_requirements(cls, values):
        """Validate outdoor specs have appropriate protection."""
        location = values.get('location')
        special_reqs = values.get('special_requirements', [])

        if location == "outdoor" or location == "exposed_to_weather":
            if not any(req in special_reqs for req in ["aluminum_jacket", "weatherproofing"]):
                logger.warning(
                    f"Outdoor insulation on page {values.get('page_number')} "
                    f"may need weather protection"
                )

        return values

    class Config:
        validate_assignment = True
        extra = "forbid"  # Reject unknown fields


# ============================================================================
# MEASUREMENT MODELS
# ============================================================================

class MeasurementItemExtracted(BaseModel):
    """Validated measurement item from drawings."""

    item_id: str = Field(description="Unique item identifier")

    system_type: Literal["duct", "pipe"] = Field(
        description="System type (duct or pipe)"
    )

    size: str = Field(
        description="Size specification (e.g., '18x12' for duct, '2\"' for pipe)",
        min_length=1
    )

    length: float = Field(
        gt=0,
        description="Linear feet"
    )

    location: str = Field(
        description="Location or zone description",
        min_length=1
    )

    elevation_changes: int = Field(
        ge=0,
        default=0,
        description="Number of rises/drops"
    )

    fittings: Dict[str, int] = Field(
        default_factory=dict,
        description="Fitting counts (e.g., {'elbow': 3, 'tee': 1})"
    )

    notes: List[str] = Field(
        default_factory=list,
        description="Additional notes"
    )

    page_number: int = Field(
        gt=0,
        description="Source page/sheet number"
    )

    sheet_number: Optional[str] = Field(
        default=None,
        description="Drawing sheet number (e.g., 'M-2.1')"
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        default=0.9,
        description="Confidence score"
    )

    @validator('length')
    def validate_length(cls, v):
        """Check for unreasonable lengths."""
        if v > 1000:
            logger.warning(f"Very long measurement: {v} LF - verify")
        return v

    @validator('fittings')
    def normalize_fitting_names(cls, v):
        """Normalize fitting names."""
        normalized = {}
        for fitting_type, count in v.items():
            fitting_lower = fitting_type.lower().strip()

            if "elbow" in fitting_lower or "90" in fitting_lower:
                normalized["elbow"] = normalized.get("elbow", 0) + count
            elif "tee" in fitting_lower or "branch" in fitting_lower:
                normalized["tee"] = normalized.get("tee", 0) + count
            elif "valve" in fitting_lower:
                normalized["valve"] = normalized.get("valve", 0) + count
            elif "transition" in fitting_lower or "reducer" in fitting_lower:
                normalized["transition"] = normalized.get("transition", 0) + count
            else:
                normalized[fitting_type] = count

        return normalized


# ============================================================================
# PROJECT INFO MODEL
# ============================================================================

class ProjectInfoExtracted(BaseModel):
    """Validated project information."""

    project_name: Optional[str] = Field(
        default=None,
        description="Full project title"
    )

    project_number: Optional[str] = Field(
        default=None,
        description="Project or job number"
    )

    client: Optional[str] = Field(
        default=None,
        description="Client or owner organization"
    )

    location: Optional[str] = Field(
        default=None,
        description="City, state, address"
    )

    architect: Optional[str] = Field(
        default=None,
        description="Architect firm name"
    )

    engineer: Optional[str] = Field(
        default=None,
        description="MEP or mechanical engineer"
    )

    project_type: Optional[Literal[
        "commercial", "industrial", "healthcare",
        "educational", "residential", "mixed_use"
    ]] = Field(default=None)

    building_type: Optional[str] = Field(
        default=None,
        description="Building type (office, hospital, etc.)"
    )

    total_square_footage: Optional[float] = Field(
        default=None,
        gt=0,
        description="Building size"
    )

    system_description: Optional[str] = Field(
        default=None,
        description="HVAC/mechanical system description"
    )

    date: Optional[str] = Field(
        default=None,
        description="Document date"
    )

    revision: Optional[str] = Field(
        default=None,
        description="Revision number or date"
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        default=0.8,
        description="Confidence in extraction"
    )

    notes: Optional[str] = Field(
        default=None,
        description="Additional notes or observations"
    )


# ============================================================================
# VALIDATION REPORT MODELS
# ============================================================================

class ValidationIssue(BaseModel):
    """Individual validation issue."""

    severity: Literal["error", "warning", "info"]
    message: str
    spec_or_item_id: Optional[str] = None
    page_number: Optional[int] = None
    suggestion: Optional[str] = None


class ValidationReport(BaseModel):
    """Comprehensive validation report."""

    status: Literal["pass", "warning", "error"]
    total_items_validated: int
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    recommendations: List[ValidationIssue] = Field(default_factory=list)
    summary: str

    def add_error(self, message: str, **kwargs):
        """Add an error."""
        self.errors.append(
            ValidationIssue(severity="error", message=message, **kwargs)
        )

    def add_warning(self, message: str, **kwargs):
        """Add a warning."""
        self.warnings.append(
            ValidationIssue(severity="warning", message=message, **kwargs)
        )

    def add_recommendation(self, message: str, **kwargs):
        """Add a recommendation."""
        self.recommendations.append(
            ValidationIssue(severity="info", message=message, **kwargs)
        )


# ============================================================================
# API RESPONSE MODELS
# ============================================================================

class ToolResponse(BaseModel):
    """Standard tool response format."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if operation succeeded."""
        return self.success and self.error is None

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Create and validate a specification
    spec_data = {
        "system_type": "supply_duct",
        "size_range": "4-12 inch",
        "thickness": 2.0,
        "material": "fiberglass",
        "facing": "FSK",
        "special_requirements": ["mastic sealing", "aluminum jacket"],
        "location": "outdoor",
        "confidence": 0.95,
        "spec_text": "Supply ductwork 4-12 inch: 2 inch fiberglass with FSK facing",
        "page_number": 5,
        "section_number": "23 07 13"
    }

    try:
        spec = InsulationSpecExtracted(**spec_data)
        print("✅ Specification validated successfully:")
        print(spec.json(indent=2))
    except Exception as e:
        print(f"❌ Validation failed: {e}")

    # Example: Invalid data
    invalid_spec = {
        "system_type": "supply_duct",
        "size_range": "4-12 inch",
        "thickness": -1.0,  # Invalid!
        "material": "fiberglass",
        "location": "outdoor",
        "confidence": 0.95,
        "spec_text": "Invalid spec",
        "page_number": 5
    }

    try:
        spec_invalid = InsulationSpecExtracted(**invalid_spec)
    except Exception as e:
        print(f"\n❌ Expected validation error: {e}")
