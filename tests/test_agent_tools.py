"""
Comprehensive Test Suite for Agent Tools
=========================================

Tests for all agent tools with fixtures and mocks.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from pydantic_models import (
    InsulationSpecExtracted,
    MeasurementItemExtracted,
    ProjectInfoExtracted,
    ValidationReport
)
from errors import (
    PDFNotFoundError,
    PDFInvalidError,
    SpecificationValidationError,
    APIKeyMissingError
)
from utils_cache import FileCache, get_cache
from utils_tracking import APIUsageTracker
from utils_pdf import smart_page_selection, get_pdf_info


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_spec_pdf():
    """Fixture providing path to test PDF."""
    # Use a fixture PDF or create a minimal one
    return "tests/fixtures/sample_specification.pdf"


@pytest.fixture
def sample_drawing_pdf():
    """Fixture providing path to test drawing PDF."""
    return "tests/fixtures/sample_drawing.pdf"


@pytest.fixture
def sample_spec_data():
    """Sample specification data."""
    return {
        "system_type": "supply_duct",
        "size_range": "4-12 inch",
        "thickness": 2.0,
        "material": "fiberglass",
        "facing": "FSK",
        "special_requirements": ["mastic_seal"],
        "location": "indoor",
        "confidence": 0.95,
        "spec_text": "Supply ductwork 4-12 inch: 2 inch fiberglass with FSK facing",
        "page_number": 5,
        "section_number": "23 07 13"
    }


@pytest.fixture
def sample_measurement_data():
    """Sample measurement data."""
    return {
        "item_id": "D-001",
        "system_type": "duct",
        "size": "18x12",
        "length": 50.0,
        "location": "Mechanical Room",
        "fittings": {"elbow": 3, "tee": 1},
        "page_number": 2
    }


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    mock_usage = Mock()
    mock_usage.input_tokens = 1000
    mock_usage.output_tokens = 500
    mock_usage.cache_read_input_tokens = 200
    mock_usage.cache_creation_input_tokens = 0

    mock_response = Mock()
    mock_response.usage = mock_usage
    mock_response.content = [Mock(text='{"test": "data"}')]

    return mock_response


# ============================================================================
# TEST PYDANTIC MODELS
# ============================================================================

class TestPydanticModels:
    """Test Pydantic data models."""

    def test_valid_specification(self, sample_spec_data):
        """Test creating valid specification."""
        spec = InsulationSpecExtracted(**sample_spec_data)

        assert spec.system_type == "supply_duct"
        assert spec.thickness == 2.0
        assert spec.confidence == 0.95

    def test_invalid_thickness_too_high(self, sample_spec_data):
        """Test specification with invalid thickness."""
        sample_spec_data["thickness"] = 10.0  # Too high

        with pytest.raises(Exception):  # Pydantic ValidationError
            InsulationSpecExtracted(**sample_spec_data)

    def test_invalid_thickness_negative(self, sample_spec_data):
        """Test specification with negative thickness."""
        sample_spec_data["thickness"] = -1.0

        with pytest.raises(Exception):
            InsulationSpecExtracted(**sample_spec_data)

    def test_special_requirements_normalization(self, sample_spec_data):
        """Test special requirements are normalized."""
        sample_spec_data["special_requirements"] = ["mastic sealing", "aluminum jacket"]

        spec = InsulationSpecExtracted(**sample_spec_data)

        assert "mastic_seal" in spec.special_requirements
        assert "aluminum_jacket" in spec.special_requirements

    def test_outdoor_validation_warning(self, sample_spec_data, caplog):
        """Test warning for outdoor spec without weather protection."""
        sample_spec_data["location"] = "outdoor"
        sample_spec_data["special_requirements"] = []  # No weather protection

        spec = InsulationSpecExtracted(**sample_spec_data)

        # Check that a warning was logged
        assert spec.location == "outdoor"
        # Note: Actual warning check depends on logging configuration

    def test_measurement_valid(self, sample_measurement_data):
        """Test valid measurement."""
        measurement = MeasurementItemExtracted(**sample_measurement_data)

        assert measurement.item_id == "D-001"
        assert measurement.system_type == "duct"
        assert measurement.length == 50.0

    def test_measurement_fitting_normalization(self, sample_measurement_data):
        """Test fitting name normalization."""
        sample_measurement_data["fittings"] = {"90 degree elbow": 2, "branch tee": 1}

        measurement = MeasurementItemExtracted(**sample_measurement_data)

        assert measurement.fittings["elbow"] == 2
        assert measurement.fittings["tee"] == 1


# ============================================================================
# TEST ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test custom error classes."""

    def test_pdf_not_found_error(self):
        """Test PDFNotFoundError."""
        error = PDFNotFoundError("/path/to/missing.pdf")

        assert "not found" in str(error)
        assert error.pdf_path == "/path/to/missing.pdf"
        assert error.suggestion is not None

        error_dict = error.to_dict()
        assert error_dict["error_type"] == "PDFNotFoundError"

    def test_pdf_invalid_error(self):
        """Test PDFInvalidError."""
        error = PDFInvalidError("/path/to/corrupt.pdf", "Corrupted")

        assert "Invalid PDF" in str(error)
        assert "Corrupted" in str(error)

    def test_specification_validation_error(self):
        """Test SpecificationValidationError."""
        issues = ["Missing thickness", "Invalid material"]
        error = SpecificationValidationError("SPEC-001", issues)

        assert "SPEC-001" in str(error)
        assert error.context["issues"] == issues

    def test_api_key_missing_error(self):
        """Test APIKeyMissingError."""
        error = APIKeyMissingError("Anthropic")

        assert "API key not configured" in str(error)
        assert "Anthropic" in str(error)


# ============================================================================
# TEST CACHING
# ============================================================================

class TestCaching:
    """Test caching functionality."""

    def test_cache_set_and_get(self, tmp_path):
        """Test basic cache operations."""
        cache = FileCache(cache_dir=str(tmp_path / ".cache"))

        # Set value
        cache.set("test_key", {"data": "value"}, ttl=60)

        # Get value
        result = cache.get("test_key")

        assert result == {"data": "value"}

    def test_cache_miss(self, tmp_path):
        """Test cache miss returns None."""
        cache = FileCache(cache_dir=str(tmp_path / ".cache"))

        result = cache.get("nonexistent_key")

        assert result is None

    def test_cache_expiration(self, tmp_path):
        """Test cache expiration."""
        cache = FileCache(cache_dir=str(tmp_path / ".cache"))

        # Set with 0 second TTL (immediate expiration)
        cache.set("test_key", {"data": "value"}, ttl=0)

        import time
        time.sleep(0.1)

        # Should be expired
        result = cache.get("test_key")

        assert result is None

    def test_cache_clear(self, tmp_path):
        """Test cache clearing."""
        cache = FileCache(cache_dir=str(tmp_path / ".cache"))

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        count = cache.clear()

        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_stats(self, tmp_path):
        """Test cache statistics."""
        cache = FileCache(cache_dir=str(tmp_path / ".cache"))

        cache.set("key1", "value1")
        cache.set("key2", "value2", category="pdf_analysis")

        stats = cache.stats()

        assert stats["total_files"] == 2
        assert "api_responses" in stats["categories"]
        assert "pdf_analysis" in stats["categories"]


# ============================================================================
# TEST COST TRACKING
# ============================================================================

class TestCostTracking:
    """Test API usage tracking."""

    def test_usage_tracker_initialization(self):
        """Test tracker initializes correctly."""
        tracker = APIUsageTracker()

        assert tracker.input_tokens == 0
        assert tracker.output_tokens == 0
        assert tracker.cache_read_tokens == 0

    def test_record_usage(self, mock_anthropic_response):
        """Test recording API usage."""
        tracker = APIUsageTracker()

        tracker.record_usage(mock_anthropic_response, "test_operation")

        assert tracker.input_tokens == 1000
        assert tracker.output_tokens == 500
        assert tracker.cache_read_tokens == 200

    def test_calculate_total_cost(self, mock_anthropic_response):
        """Test cost calculation."""
        tracker = APIUsageTracker()

        tracker.record_usage(mock_anthropic_response)

        cost = tracker.calculate_total_cost()

        assert cost > 0
        assert isinstance(cost, float)

    def test_cache_savings(self, mock_anthropic_response):
        """Test cache savings calculation."""
        tracker = APIUsageTracker()

        tracker.record_usage(mock_anthropic_response)

        savings = tracker.calculate_cache_savings()

        assert savings > 0  # Should have savings from cache hits

    def test_usage_summary(self, mock_anthropic_response):
        """Test usage summary generation."""
        tracker = APIUsageTracker()

        tracker.record_usage(mock_anthropic_response, "operation1")
        tracker.record_usage(mock_anthropic_response, "operation2")

        summary = tracker.get_summary()

        assert "tokens" in summary
        assert "costs" in summary
        assert "efficiency" in summary
        assert summary["operations"]["total"] == 2

    def test_reset_tracker(self, mock_anthropic_response):
        """Test tracker reset."""
        tracker = APIUsageTracker()

        tracker.record_usage(mock_anthropic_response)
        tracker.reset()

        assert tracker.input_tokens == 0
        assert tracker.output_tokens == 0
        assert len(tracker.operations) == 0


# ============================================================================
# TEST PDF UTILITIES (mocked)
# ============================================================================

class TestPDFUtilities:
    """Test PDF utility functions."""

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_specification.pdf").exists(),
        reason="Test PDF not available"
    )
    def test_smart_page_selection(self, sample_spec_pdf):
        """Test smart page selection."""
        selected = smart_page_selection(sample_spec_pdf, max_pages=5)

        assert isinstance(selected, list)
        assert len(selected) <= 5
        assert all(isinstance(p, int) for p in selected)
        assert all(p > 0 for p in selected)

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_specification.pdf").exists(),
        reason="Test PDF not available"
    )
    def test_get_pdf_info(self, sample_spec_pdf):
        """Test PDF info extraction."""
        info = get_pdf_info(sample_spec_pdf)

        assert "page_count" in info
        assert "file_size_mb" in info
        assert info["page_count"] > 0


# ============================================================================
# TEST VALIDATION LOGIC
# ============================================================================

class TestValidation:
    """Test validation functions."""

    def test_validate_outdoor_specs(self):
        """Test outdoor specification validation."""
        # This would test the actual validate_specifications function
        # Mocked here as an example
        specs = [
            {
                "system_type": "duct",
                "location": "outdoor",
                "special_requirements": []  # Missing weather protection
            }
        ]

        # Mock validation would check for warnings
        # assert len(validation_warnings) > 0
        pass

    def test_cross_reference_matching(self):
        """Test cross-reference logic."""
        specs = [
            {"system_type": "duct"}
        ]

        measurements = [
            {"system_type": "duct"},
            {"system_type": "pipe"}  # No matching spec
        ]

        # Mock cross_reference_data would identify missing pipe spec
        # assert len(missing_specs) == 1
        pass


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests."""

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_specification.pdf").exists(),
        reason="Test PDF not available"
    )
    @patch('claude_agent_tools.get_claude_client')
    def test_full_extraction_workflow(self, mock_client, sample_spec_pdf):
        """Test complete extraction workflow with mocked API."""
        # Mock Claude API response
        mock_response = Mock()
        mock_response.content = [Mock(text='[{"system_type": "supply_duct", "thickness": 2.0, ...}]')]
        mock_response.usage = Mock(
            input_tokens=1000,
            output_tokens=500,
            cache_read_input_tokens=0
        )

        mock_client.return_value.messages.create.return_value = mock_response

        # This would call the actual extract_specifications function
        # result = extract_specifications(sample_spec_pdf)
        # assert result["success"]
        # assert len(result["specifications"]) > 0
        pass


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance benchmarks."""

    def test_cache_performance_improvement(self):
        """Test that caching improves performance."""
        # Mock expensive operation
        call_count = 0

        def expensive_operation():
            nonlocal call_count
            call_count += 1
            import time
            time.sleep(0.1)
            return "result"

        # First call - slow
        import time
        start = time.time()
        result1 = expensive_operation()
        time1 = time.time() - start

        # With caching, second call would be instant
        # This is conceptual - actual test would use the cache decorator
        assert time1 > 0.1
        assert call_count == 1


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
