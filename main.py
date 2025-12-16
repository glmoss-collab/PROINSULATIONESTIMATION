"""
FastAPI Application for HVAC Insulation Estimation
===================================================

Enterprise API layer that translates web requests (JSON) into the objects
the existing Python estimation engine understands.

This provides a clean separation between:
- API Layer (this file): Handles HTTP, validation, serialization
- Client Layer: AppSheet, React, or any HTTP client
- Core Engine: hvac_insulation_estimator.py business logic
"""

import os
import tempfile
import logging
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import existing core estimation logic
from hvac_insulation_estimator import (
    PricingEngine,
    QuoteGenerator,
    MeasurementItem,
    InsulationSpec,
    MaterialItem,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# API REQUEST/RESPONSE MODELS (Pydantic)
# =============================================================================

class SpecInput(BaseModel):
    """API input model for insulation specification."""

    system_type: str = Field(
        description="System type: 'duct', 'pipe', or 'equipment'"
    )
    size_range: str = Field(
        description="Size range this spec applies to (e.g., '4-12 inch')"
    )
    thickness: float = Field(
        gt=0,
        le=6,
        description="Insulation thickness in inches"
    )
    material: str = Field(
        description="Material type: 'fiberglass', 'elastomeric', etc."
    )
    facing: Optional[str] = Field(
        default=None,
        description="Facing type: 'FSK', 'ASJ', 'PVC', etc."
    )
    special_requirements: List[str] = Field(
        default_factory=list,
        description="Special requirements: 'aluminum_jacket', 'mastic_coating', etc."
    )
    location: str = Field(
        default="indoor",
        description="Installation location: 'indoor', 'outdoor', 'exposed'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "system_type": "duct",
                "size_range": "all",
                "thickness": 1.5,
                "material": "fiberglass",
                "facing": "FSK",
                "special_requirements": [],
                "location": "indoor"
            }
        }


class MeasurementInput(BaseModel):
    """API input model for measurement item."""

    item_id: str = Field(description="Unique item identifier")
    system_type: str = Field(description="System type: 'duct' or 'pipe'")
    size: str = Field(description="Size specification (e.g., '18x12', '2\"')")
    length: float = Field(gt=0, description="Linear feet")
    location: str = Field(description="Location or zone description")
    elevation_changes: int = Field(
        default=0,
        ge=0,
        description="Number of rises/drops"
    )
    fittings: Dict[str, int] = Field(
        default_factory=dict,
        description="Fitting counts: {'elbow': 3, 'tee': 1}"
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Additional notes"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "DUCT-001",
                "system_type": "duct",
                "size": "18x12",
                "length": 125.5,
                "location": "Main corridor",
                "elevation_changes": 0,
                "fittings": {"elbow": 3, "tee": 1},
                "notes": []
            }
        }


class CalculationRequest(BaseModel):
    """API request model for estimate calculation."""

    project_name: str = Field(description="Project name for the estimate")
    measurements: List[MeasurementInput] = Field(
        description="List of measurement items"
    )
    specs: List[SpecInput] = Field(
        description="List of insulation specifications"
    )
    markup_percent: float = Field(
        default=15.0,
        ge=0,
        le=100,
        description="Markup percentage (e.g., 15 for 15%)"
    )
    labor_rate: float = Field(
        default=65.0,
        gt=0,
        description="Labor rate per hour in dollars"
    )
    distributor_prices: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional custom price overrides"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "Office Building HVAC",
                "measurements": [
                    {
                        "item_id": "DUCT-001",
                        "system_type": "duct",
                        "size": "18x12",
                        "length": 125.5,
                        "location": "Main corridor",
                        "fittings": {"elbow": 3, "tee": 1}
                    }
                ],
                "specs": [
                    {
                        "system_type": "duct",
                        "size_range": "all",
                        "thickness": 1.5,
                        "material": "fiberglass",
                        "facing": "FSK",
                        "location": "indoor"
                    }
                ],
                "markup_percent": 15.0,
                "labor_rate": 65.0
            }
        }


class MaterialBreakdown(BaseModel):
    """Material item in response breakdown."""

    description: str
    quantity: float
    unit: str
    unit_price: float
    total: float
    category: str


class CalculationTotals(BaseModel):
    """Calculation totals in response."""

    material_cost: float
    labor_hours: float
    labor_cost: float
    subtotal: float
    contingency_percent: float
    contingency_amount: float
    total_estimate: float


class CalculationResponse(BaseModel):
    """API response model for estimate calculation."""

    project: str
    totals: CalculationTotals
    breakdown: List[MaterialBreakdown]


class QuoteResponse(BaseModel):
    """API response model for quote generation."""

    project: str
    quote_number: str
    quote_text: str
    totals: CalculationTotals


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str


# =============================================================================
# CONVERSION UTILITIES
# =============================================================================

def spec_input_to_dataclass(spec: SpecInput) -> InsulationSpec:
    """Convert API SpecInput to internal InsulationSpec dataclass."""
    return InsulationSpec(
        system_type=spec.system_type,
        size_range=spec.size_range,
        thickness=spec.thickness,
        material=spec.material,
        facing=spec.facing,
        special_requirements=spec.special_requirements,
        location=spec.location,
    )


def measurement_input_to_dataclass(measurement: MeasurementInput) -> MeasurementItem:
    """Convert API MeasurementInput to internal MeasurementItem dataclass."""
    return MeasurementItem(
        item_id=measurement.item_id,
        system_type=measurement.system_type,
        size=measurement.size,
        length=measurement.length,
        location=measurement.location,
        elevation_changes=measurement.elevation_changes,
        fittings=measurement.fittings,
        notes=measurement.notes,
    )


def material_to_breakdown(material: MaterialItem) -> MaterialBreakdown:
    """Convert internal MaterialItem to API MaterialBreakdown."""
    return MaterialBreakdown(
        description=material.description,
        quantity=round(material.quantity, 2),
        unit=material.unit,
        unit_price=round(material.unit_price, 2),
        total=round(material.total_price, 2),
        category=material.category,
    )


# =============================================================================
# APPLICATION LIFECYCLE
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("HVAC Estimation API starting up...")

    # Load default pricebook if available
    pricebook_path = os.environ.get("PRICEBOOK_PATH")
    if pricebook_path and Path(pricebook_path).exists():
        logger.info(f"Using pricebook: {pricebook_path}")
    else:
        logger.info("Using default internal pricing")

    yield

    logger.info("HVAC Estimation API shutting down...")


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="HVAC Insulation Estimation API",
    description=(
        "Enterprise API for HVAC insulation material estimation, "
        "pricing calculations, and quote generation. "
        "Designed for integration with AppSheet, React, or any HTTP client."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Simple check to verify the API is operational.
    Used by Cloud Run and load balancers.
    """
    return HealthResponse(
        status="operational",
        service="hvac-insulation-estimator",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
def health_check_explicit() -> HealthResponse:
    """Explicit health check endpoint for monitoring."""
    return HealthResponse(
        status="operational",
        service="hvac-insulation-estimator",
        version="1.0.0"
    )


@app.post("/calculate", response_model=CalculationResponse)
def calculate_estimate(request: CalculationRequest) -> CalculationResponse:
    """
    Calculate material quantities and pricing.

    Takes measurements and specifications, returns detailed material
    breakdown with pricing and labor estimates.

    This is the primary endpoint for estimation calculations.
    """
    try:
        # 1. Convert API models to internal dataclasses
        internal_measurements = [
            measurement_input_to_dataclass(m) for m in request.measurements
        ]
        internal_specs = [
            spec_input_to_dataclass(s) for s in request.specs
        ]

        # 2. Initialize pricing engine with markup
        markup_multiplier = 1.0 + (request.markup_percent / 100.0)

        # Check for custom pricebook path
        pricebook_path = os.environ.get("PRICEBOOK_PATH")

        engine = PricingEngine(
            price_book_path=pricebook_path,
            markup=markup_multiplier
        )

        # Apply custom distributor prices if provided
        if request.distributor_prices:
            for key, price in request.distributor_prices.items():
                engine.prices[key] = price

        # 3. Calculate materials using existing logic
        materials = engine.calculate_materials(internal_measurements, internal_specs)

        # 4. Calculate labor
        labor_hours, labor_cost = engine.calculate_labor(materials)

        # Adjust labor cost if custom labor rate provided
        if request.labor_rate != 65.0:
            labor_cost = labor_hours * request.labor_rate

        # 5. Calculate totals
        material_total = sum(m.total_price for m in materials)
        subtotal = material_total + labor_cost

        # Add contingency (10%)
        contingency_percent = 10.0
        contingency_amount = subtotal * (contingency_percent / 100)
        total_estimate = subtotal + contingency_amount

        # 6. Build response
        return CalculationResponse(
            project=request.project_name,
            totals=CalculationTotals(
                material_cost=round(material_total, 2),
                labor_hours=round(labor_hours, 2),
                labor_cost=round(labor_cost, 2),
                subtotal=round(subtotal, 2),
                contingency_percent=contingency_percent,
                contingency_amount=round(contingency_amount, 2),
                total_estimate=round(total_estimate, 2),
            ),
            breakdown=[material_to_breakdown(m) for m in materials],
        )

    except ValueError as e:
        logger.warning(f"Validation error in calculation: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.exception(f"Calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/generate_quote", response_model=QuoteResponse)
def create_quote_document(request: CalculationRequest) -> QuoteResponse:
    """
    Generate a complete quote document.

    Runs the full calculation and generates a formatted quote
    with all details, notes, and terms.

    Returns the quote as structured data plus the full text.
    """
    try:
        # 1. Convert API models to internal dataclasses
        internal_measurements = [
            measurement_input_to_dataclass(m) for m in request.measurements
        ]
        internal_specs = [
            spec_input_to_dataclass(s) for s in request.specs
        ]

        # 2. Initialize pricing engine
        markup_multiplier = 1.0 + (request.markup_percent / 100.0)
        pricebook_path = os.environ.get("PRICEBOOK_PATH")

        engine = PricingEngine(
            price_book_path=pricebook_path,
            markup=markup_multiplier
        )

        if request.distributor_prices:
            for key, price in request.distributor_prices.items():
                engine.prices[key] = price

        # 3. Calculate materials and labor
        materials = engine.calculate_materials(internal_measurements, internal_specs)
        labor_hours, labor_cost = engine.calculate_labor(materials)

        if request.labor_rate != 65.0:
            labor_cost = labor_hours * request.labor_rate

        # 4. Generate quote using existing QuoteGenerator
        generator = QuoteGenerator()
        quote = generator.generate_quote(
            project_name=request.project_name,
            measurements=internal_measurements,
            materials=materials,
            labor_hours=labor_hours,
            labor_cost=labor_cost,
            specs=internal_specs,
        )

        # 5. Export quote to temporary file and read content
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False
        ) as temp_file:
            temp_path = temp_file.name

        try:
            generator.export_quote_to_file(quote, temp_path)
            with open(temp_path, 'r', encoding='utf-8') as f:
                quote_text = f.read()
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

        # 6. Calculate totals for response
        material_total = sum(m.total_price for m in materials)
        subtotal = material_total + labor_cost
        contingency_percent = quote.contingency_percent
        contingency_amount = subtotal * (contingency_percent / 100)

        return QuoteResponse(
            project=request.project_name,
            quote_number=quote.quote_number,
            quote_text=quote_text,
            totals=CalculationTotals(
                material_cost=round(material_total, 2),
                labor_hours=round(labor_hours, 2),
                labor_cost=round(labor_cost, 2),
                subtotal=round(subtotal, 2),
                contingency_percent=contingency_percent,
                contingency_amount=round(contingency_amount, 2),
                total_estimate=round(quote.total, 2),
            ),
        )

    except ValueError as e:
        logger.warning(f"Validation error in quote generation: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.exception(f"Quote generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Quote generation error: {str(e)}")


@app.get("/pricing/default")
def get_default_pricing() -> Dict[str, Any]:
    """
    Get default pricing information.

    Returns the default material prices and labor rates
    used when no custom pricebook is provided.
    """
    engine = PricingEngine()
    return {
        "prices": engine.prices,
        "labor_rates": engine.labor_rates,
        "note": "Prices are base rates before markup"
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Disable in production
        log_level="info"
    )
