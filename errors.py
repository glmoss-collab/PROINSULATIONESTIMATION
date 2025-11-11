"""
Custom Exception Classes
=========================

Comprehensive error handling with helpful error messages and recovery suggestions.
"""

from typing import Optional
from pathlib import Path


# ============================================================================
# BASE EXCEPTIONS
# ============================================================================

class EstimationError(Exception):
    """Base exception for all estimation-related errors."""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        context: Optional[dict] = None
    ):
        self.message = message
        self.suggestion = suggestion
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self):
        parts = [self.message]
        if self.suggestion:
            parts.append(f"\n💡 Suggestion: {self.suggestion}")
        if self.context:
            parts.append(f"\n📋 Context: {self.context}")
        return "".join(parts)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "error": self.message,
            "suggestion": self.suggestion,
            "context": self.context,
            "error_type": self.__class__.__name__
        }


# ============================================================================
# PDF PROCESSING ERRORS
# ============================================================================

class PDFError(EstimationError):
    """Base class for PDF-related errors."""

    def __init__(
        self,
        message: str,
        pdf_path: str,
        page_num: Optional[int] = None,
        suggestion: Optional[str] = None
    ):
        self.pdf_path = pdf_path
        self.page_num = page_num

        context = {"pdf_path": pdf_path}
        if page_num:
            context["page_number"] = page_num

        super().__init__(message, suggestion, context)


class PDFNotFoundError(PDFError):
    """PDF file not found."""

    def __init__(self, pdf_path: str):
        super().__init__(
            message=f"PDF file not found: {pdf_path}",
            pdf_path=pdf_path,
            suggestion="Verify the file path is correct and the file exists"
        )


class PDFInvalidError(PDFError):
    """PDF file is invalid or corrupted."""

    def __init__(self, pdf_path: str, reason: str = ""):
        super().__init__(
            message=f"Invalid PDF file: {pdf_path}" + (f" ({reason})" if reason else ""),
            pdf_path=pdf_path,
            suggestion="The file may be corrupted, password-protected, or not a valid PDF"
        )


class PDFEmptyError(PDFError):
    """PDF has no pages."""

    def __init__(self, pdf_path: str):
        super().__init__(
            message=f"PDF has no pages: {pdf_path}",
            pdf_path=pdf_path,
            suggestion="The PDF file may be corrupted"
        )


class PDFPageOutOfRangeError(PDFError):
    """Requested page number out of range."""

    def __init__(self, pdf_path: str, page_num: int, total_pages: int):
        super().__init__(
            message=f"Page {page_num} out of range (PDF has {total_pages} pages)",
            pdf_path=pdf_path,
            page_num=page_num,
            suggestion=f"Use page numbers 1-{total_pages}"
        )


# ============================================================================
# EXTRACTION ERRORS
# ============================================================================

class ExtractionError(EstimationError):
    """Base class for extraction errors."""
    pass


class SpecificationExtractionError(ExtractionError):
    """Failed to extract specifications."""

    def __init__(self, pdf_path: str, reason: str = ""):
        super().__init__(
            message=f"Failed to extract specifications from {Path(pdf_path).name}" +
                    (f": {reason}" if reason else ""),
            suggestion="Ensure the PDF contains insulation specifications in a readable format",
            context={"pdf_path": pdf_path}
        )


class MeasurementExtractionError(ExtractionError):
    """Failed to extract measurements."""

    def __init__(self, pdf_path: str, reason: str = ""):
        super().__init__(
            message=f"Failed to extract measurements from {Path(pdf_path).name}" +
                    (f": {reason}" if reason else ""),
            suggestion="Ensure the PDF contains mechanical drawings with dimensions",
            context={"pdf_path": pdf_path}
        )


class ProjectInfoExtractionError(ExtractionError):
    """Failed to extract project information."""

    def __init__(self, pdf_path: str, reason: str = ""):
        super().__init__(
            message=f"Failed to extract project info from {Path(pdf_path).name}" +
                    (f": {reason}" if reason else ""),
            suggestion="Ensure the PDF has a title block or cover sheet",
            context={"pdf_path": pdf_path}
        )


# ============================================================================
# VALIDATION ERRORS
# ============================================================================

class ValidationError(EstimationError):
    """Base class for validation errors."""
    pass


class SpecificationValidationError(ValidationError):
    """Specification validation failed."""

    def __init__(self, spec_id: str, issues: list):
        super().__init__(
            message=f"Specification {spec_id} failed validation",
            suggestion="Review specification requirements and correct issues",
            context={"spec_id": spec_id, "issues": issues}
        )


class CrossReferenceError(ValidationError):
    """Cross-reference validation failed."""

    def __init__(self, conflicts: list):
        super().__init__(
            message=f"Found {len(conflicts)} cross-reference conflicts",
            suggestion="Review conflicts and resolve discrepancies between specs and measurements",
            context={"conflicts": conflicts}
        )


class DataIntegrityError(ValidationError):
    """Data integrity check failed."""

    def __init__(self, message: str, data_type: str):
        super().__init__(
            message=message,
            suggestion=f"Verify {data_type} data is complete and accurate",
            context={"data_type": data_type}
        )


# ============================================================================
# API ERRORS
# ============================================================================

class APIError(EstimationError):
    """Base class for API-related errors."""
    pass


class APIKeyMissingError(APIError):
    """API key not configured."""

    def __init__(self, service: str = "Anthropic"):
        super().__init__(
            message=f"{service} API key not configured",
            suggestion=f"Set the API key in environment variable or secrets file"
        )


class APIRateLimitError(APIError):
    """API rate limit exceeded."""

    def __init__(self, retry_after: Optional[int] = None):
        message = "API rate limit exceeded"
        suggestion = "Wait a moment and try again"

        if retry_after:
            suggestion = f"Retry after {retry_after} seconds"

        super().__init__(message=message, suggestion=suggestion)


class APIQuotaExceededError(APIError):
    """API quota exceeded."""

    def __init__(self):
        super().__init__(
            message="API quota exceeded",
            suggestion="Check your API usage and billing settings"
        )


class APITimeoutError(APIError):
    """API request timed out."""

    def __init__(self, operation: str):
        super().__init__(
            message=f"API request timed out during {operation}",
            suggestion="Try again with fewer pages or smaller documents"
        )


# ============================================================================
# CALCULATION ERRORS
# ============================================================================

class CalculationError(EstimationError):
    """Base class for calculation errors."""
    pass


class PricingCalculationError(CalculationError):
    """Pricing calculation failed."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Pricing calculation failed: {reason}",
            suggestion="Verify pricebook data and measurement quantities"
        )


class QuantityCalculationError(CalculationError):
    """Quantity calculation failed."""

    def __init__(self, item_id: str, reason: str):
        super().__init__(
            message=f"Failed to calculate quantities for {item_id}: {reason}",
            suggestion="Check measurement data and specification details",
            context={"item_id": item_id}
        )


# ============================================================================
# CONFIGURATION ERRORS
# ============================================================================

class ConfigurationError(EstimationError):
    """Configuration error."""

    def __init__(self, setting: str, reason: str):
        super().__init__(
            message=f"Configuration error for '{setting}': {reason}",
            suggestion="Check configuration file or environment variables",
            context={"setting": setting}
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def handle_pdf_error(pdf_path: str, exception: Exception) -> PDFError:
    """
    Convert generic exceptions to specific PDF errors.

    Args:
        pdf_path: Path to PDF
        exception: Original exception

    Returns:
        Specific PDFError subclass
    """
    if not Path(pdf_path).exists():
        return PDFNotFoundError(pdf_path)

    error_msg = str(exception).lower()

    if "password" in error_msg or "encrypted" in error_msg:
        return PDFInvalidError(pdf_path, "Password-protected")

    if "corrupt" in error_msg or "damaged" in error_msg:
        return PDFInvalidError(pdf_path, "File corrupted")

    # Generic PDF error
    return PDFInvalidError(pdf_path, str(exception))


def safe_execute(
    func,
    *args,
    error_class=EstimationError,
    error_message: str = "Operation failed",
    **kwargs
):
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Function arguments
        error_class: Exception class to raise on failure
        error_message: Error message
        **kwargs: Function keyword arguments

    Returns:
        Function result or raises error_class
    """
    try:
        return func(*args, **kwargs)
    except EstimationError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Wrap other exceptions
        raise error_class(
            message=f"{error_message}: {str(e)}",
            suggestion="Check the input data and try again"
        ) from e


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Handling PDF errors
    try:
        pdf_path = "nonexistent.pdf"
        if not Path(pdf_path).exists():
            raise PDFNotFoundError(pdf_path)
    except PDFError as e:
        print(f"❌ Error: {e}")
        print(e.to_dict())

    print()

    # Example: Validation error
    try:
        raise SpecificationValidationError(
            "SPEC-001",
            ["Missing thickness", "Invalid material type"]
        )
    except ValidationError as e:
        print(f"❌ Validation Error: {e}")

    print()

    # Example: API error
    try:
        raise APIRateLimitError(retry_after=60)
    except APIError as e:
        print(f"❌ API Error: {e}")

    print()

    # Example: Safe execution
    def risky_operation():
        raise ValueError("Something went wrong!")

    try:
        safe_execute(
            risky_operation,
            error_class=CalculationError,
            error_message="Calculation failed"
        )
    except CalculationError as e:
        print(f"❌ Calculation Error: {e}")
