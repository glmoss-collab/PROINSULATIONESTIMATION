# Test Coverage Analysis

## Current State

### Test Files

| File | Tests | Framework | Status |
|------|-------|-----------|--------|
| `tests/test_agent_tools.py` | 27 functions in 8 classes | pytest | **Broken** - cannot collect due to Pydantic v2 incompatibility |
| `test_easiest_workflow.py` | 10 functions | Custom runner | Standalone (not in `tests/`) |

### Blocking Issue: Tests Cannot Run

The test suite fails at collection time:

```
pydantic.errors.PydanticUserError: If you use `@root_validator` with pre=False
(the default) you MUST specify `skip_on_failure=True`.
```

`pydantic_models.py:117` uses the deprecated `@root_validator` decorator without
`skip_on_failure=True`, which is an error in Pydantic v2.x. The file also uses
deprecated `@validator` (should be `@field_validator`). Until this is fixed, **zero
tests can run**.

### What Exists (When Fixed)

Tests that actually assert something:

- **Pydantic models (7 tests):** `InsulationSpecExtracted` and `MeasurementItemExtracted` validation
- **Error classes (4 tests):** `PDFNotFoundError`, `PDFInvalidError`, `SpecificationValidationError`, `APIKeyMissingError`
- **FileCache (5 tests):** set/get, miss, expiration, clear, stats
- **APIUsageTracker (6 tests):** init, record, cost calc, cache savings, summary, reset
- **Performance (1 test):** Conceptual cache benchmark (doesn't actually test the cache system)

Tests that are stubs (`pass` body, no assertions):

- `TestValidation::test_validate_outdoor_specs` — empty
- `TestValidation::test_cross_reference_matching` — empty
- `TestIntegration::test_full_extraction_workflow` — empty (also requires missing fixture PDF)

Tests that are always skipped:

- `TestPDFUtilities::test_smart_page_selection` — `tests/fixtures/` directory does not exist
- `TestPDFUtilities::test_get_pdf_info` — same

### Infrastructure Gaps

- **No `conftest.py`** — no shared fixtures across test modules
- **No `pytest.ini` / `pyproject.toml` `[tool.pytest]`** — no test configuration
- **No `.coveragerc`** — no coverage configuration
- **No test fixtures directory** — `tests/fixtures/` referenced but missing
- **No CI configuration** — no automated test runs

---

## Coverage Gaps by Module

### 1. `hvac_insulation_estimator.py` (1,081 lines) — **0% tested**

This is the core domain engine and has **zero test coverage**. It contains pure
business logic that is highly testable without any API mocking.

**Untested classes and methods:**

| Class | Method | Priority | Notes |
|-------|--------|----------|-------|
| `SpecificationExtractor` | `extract_from_text(text)` | **Critical** | Pure text parsing, no I/O |
| `SpecificationExtractor` | `_is_insulation_section(text)` | **Critical** | Keyword matching |
| `SpecificationExtractor` | `_parse_insulation_specs(text)` | **Critical** | Regex-based spec extraction |
| `SpecificationExtractor` | `_extract_facing(text, position)` | High | Facing type detection |
| `SpecificationExtractor` | `_extract_special_requirements(text, specs)` | High | Requirements parsing |
| `PricingEngine` | `_load_prices(path)` | High | Price book loading (JSON parsing) |
| `PricingEngine` | `calculate_materials(measurements, specs)` | **Critical** | Core material calculation |
| `PricingEngine` | `_find_applicable_spec(measurement, specs)` | High | Spec-to-measurement matching |
| `PricingEngine` | `_calculate_insulation(measurement, spec)` | **Critical** | Quantity/cost calculation |
| `PricingEngine` | `_calculate_jacketing(measurement, spec)` | High | Jacketing cost calculation |
| `PricingEngine` | `_calculate_mastic(measurement, spec)` | Medium | Mastic cost calculation |
| `PricingEngine` | `_calculate_accessories(measurement, spec)` | Medium | Accessories calculation |
| `PricingEngine` | `_parse_size_to_diameter(size)` | High | Size string parsing |
| `PricingEngine` | `calculate_labor(materials)` | **Critical** | Labor hours/cost estimation |
| `QuoteGenerator` | `generate_quote(...)` | High | Quote assembly |
| `QuoteGenerator` | `calculate_alternative_options(...)` | Medium | Alternative cost scenarios |
| `QuoteGenerator` | `export_quote_to_file(...)` | Medium | File output |
| `DrawingMeasurementExtractor` | `manual_entry_measurements(data)` | High | Manual data import |
| `DrawingMeasurementExtractor` | `_parse_scale(groups)` | Medium | Scale factor parsing |

### 2. `claude_agent_tools.py` (1,107 lines) — **0% tested**

All 7 agent tools are untested. The utility functions are testable with mocks.

| Function | Priority | Notes |
|----------|----------|-------|
| `extract_text_from_pdf(path, pages)` | High | Text extraction (needs PDF fixture or mock) |
| `get_tool_schemas()` | High | Schema validation — ensure schemas are well-formed |
| `validate_specifications(specs)` | **Critical** | Core validation logic |
| `cross_reference_data(specs, measurements, info)` | **Critical** | Cross-referencing logic |
| `calculate_pricing(specs, measurements, ...)` | High | Pricing orchestration |
| `generate_quote(info, specs, measurements, pricing)` | Medium | Quote generation orchestration |

### 3. `claude_estimation_agent.py` (616 lines) — **0% tested**

The agent orchestrator has no tests.

| Method | Priority | Notes |
|--------|----------|-------|
| `InsulationEstimationAgent.__init__` | Medium | Constructor validation |
| `add_file(path, type)` | High | File registration logic |
| `_extract_text_content(blocks)` | High | Content block parsing |
| `_execute_tools(blocks)` | **Critical** | Tool dispatch logic |
| `_update_session_data(name, result)` | High | State management |
| `get_session_data()` | Medium | Data retrieval |
| `reset_session()` | Medium | State cleanup |
| `export_session(path)` | Medium | Serialization |
| `create_agent(api_key)` | Medium | Factory function |

### 4. `errors.py` (410 lines) — **~20% tested**

Only 4 of 18+ error classes are tested. Helper functions are untested.

**Untested:**

| Item | Priority |
|------|----------|
| `PDFEmptyError` | Medium |
| `PDFPageOutOfRangeError` | Medium |
| `ExtractionError` and subclasses (3) | Medium |
| `CrossReferenceError` | Medium |
| `DataIntegrityError` | Medium |
| `APIRateLimitError` (with/without retry_after) | Medium |
| `APIQuotaExceededError` | Low |
| `APITimeoutError` | Low |
| `PricingCalculationError` | Medium |
| `QuantityCalculationError` | Medium |
| `ConfigurationError` | Low |
| `handle_pdf_error(path, exception)` | High |
| `safe_execute(func, ...)` | **Critical** |

### 5. `pydantic_models.py` (417 lines) — **~30% tested**

Tested: `InsulationSpecExtracted` (partial), `MeasurementItemExtracted` (partial).

**Untested:**

| Model/Feature | Priority |
|---------------|----------|
| `ProjectInfoExtracted` — all fields and defaults | High |
| `ValidationReport` — `add_error`, `add_warning`, `add_recommendation` | High |
| `ValidationIssue` — construction and serialization | Medium |
| `ToolResponse` — `is_success`, `has_warnings` properties | High |
| Edge cases: boundary values for `confidence` (0.0, 1.0), max `thickness` (6.0) | Medium |

### 6. `utils_cache.py` (339 lines) — **~50% tested**

`FileCache` basic operations are tested. Decorator functions are not.

**Untested:**

| Item | Priority |
|------|----------|
| `cached()` decorator — function wrapping, key generation | **Critical** |
| `pdf_cache_key(path, operation)` — key generation from file hash | High |
| `cache_pdf_analysis()` decorator | High |
| `get_cache()` singleton behavior | Medium |
| Category-based cache clearing | Medium |

### 7. `utils_tracking.py` (300 lines) — **~60% tested**

Good coverage on `APIUsageTracker`. Missing:

| Item | Priority |
|------|----------|
| `get_detailed_breakdown()` | Medium |
| `export_report(output_path)` — file writing | Medium |
| `print_summary()` | Low |
| `get_tracker()` / `reset_tracker()` singleton functions | Medium |

### 8. `utils_pdf.py` (369 lines) — **0% functional tests**

Both PDF utility tests are always skipped due to missing fixtures.

| Function | Priority | Notes |
|----------|----------|-------|
| `smart_page_selection(path, max_pages, keywords)` | High | Can test with a generated PDF |
| `get_pdf_info(path)` | High | Can test with a generated PDF |
| `pdf_to_base64_images_optimized(...)` | Medium | Image conversion |
| `extract_text_from_pdf_optimized(...)` | Medium | Text extraction |
| `preprocess_pdf(...)` | Low | PDF preprocessing |

### 9. `utils_async.py` (326 lines) — **0% tested**

| Item | Priority | Notes |
|------|----------|-------|
| `AsyncBatchProcessor.__init__` | Medium | Constructor validation |
| `AsyncBatchProcessor.process_batch(...)` | High | Needs async test with mocked API |
| `extract_specifications_batch(...)` | Medium | Sync wrapper |

### 10. `gemini_pdf_extractor.py` (339 lines) — **0% tested**

Legacy module but still imported by `streamlit_app.py`.

### 11. Streamlit apps — **0% tested**

`agent_estimation_app.py`, `streamlit_app.py`, `estimation_app.py` have no tests.
Streamlit apps are harder to unit test, but utility functions within them
(`save_uploaded_file`, `init_session_state`, `encode_file_to_base64`) are testable.

---

## Recommended Improvements (Priority Order)

### P0 — Fix the test infrastructure

1. **Fix `pydantic_models.py` Pydantic v2 compatibility** — replace `@root_validator`
   with `@model_validator(mode='after')` and `@validator` with `@field_validator`.
   Without this, no tests run at all.

2. **Add `conftest.py`** with shared fixtures (sample data dicts, tmp directories,
   mock Anthropic responses).

3. **Add `pyproject.toml` `[tool.pytest.ini_options]`** with `testpaths`, `markers`,
   and coverage settings.

4. **Create `tests/fixtures/`** with minimal test PDFs (can be generated
   programmatically with `reportlab` or `fpdf`).

### P1 — Test the core estimation engine

5. **`test_specification_extractor.py`** — Tests for `SpecificationExtractor`:
   - `_is_insulation_section()` with positive/negative text samples
   - `_parse_insulation_specs()` with realistic spec text
   - `_extract_facing()` with various facing types
   - `_extract_special_requirements()` with different requirement patterns
   - `extract_from_text()` end-to-end with sample spec documents

6. **`test_pricing_engine.py`** — Tests for `PricingEngine`:
   - `_parse_size_to_diameter()` with various size formats ("4\"", "18x12", "2 inch")
   - `_find_applicable_spec()` with matching/non-matching specs
   - `_calculate_insulation()` verifying quantity and cost math
   - `_calculate_jacketing()` verifying area calculations
   - `calculate_materials()` end-to-end with measurements + specs
   - `calculate_labor()` verifying hour calculations and overhead
   - `_load_prices()` with default prices, simple JSON, and supplier-aware JSON

7. **`test_quote_generator.py`** — Tests for `QuoteGenerator`:
   - `generate_quote()` with known inputs, verify totals
   - `calculate_alternative_options()` with pipe/duct measurements

### P2 — Test validation and error handling

8. **Complete the stub tests** — Fill in `test_validate_outdoor_specs` and
   `test_cross_reference_matching` with actual assertions.

9. **`test_errors.py`** (expand) — Test remaining error classes, `handle_pdf_error()`
   routing logic, and `safe_execute()` with both passing and failing functions.

10. **Test all Pydantic models** — Add tests for `ProjectInfoExtracted`,
    `ValidationReport` methods, `ToolResponse` properties, and boundary values.

### P3 — Test utilities and decorators

11. **Test cache decorators** — `@cached()` and `@cache_pdf_analysis()` wrapping
    behavior, key generation, and TTL handling.

12. **Test `utils_pdf.py`** — Generate simple PDFs in fixtures (using `fpdf2` or
    `reportlab`) so `smart_page_selection` and `get_pdf_info` can run.

13. **Test async processing** — Use `pytest-asyncio` to test `AsyncBatchProcessor`
    with mocked `AsyncAnthropic` client.

### P4 — Test agent layer

14. **`test_agent_tools_schemas.py`** — Validate that `get_tool_schemas()` returns
    well-formed tool definitions (correct types, required fields present, descriptions
    non-empty).

15. **`test_estimation_agent.py`** — Test `InsulationEstimationAgent` with mocked
    Anthropic client:
    - Session state management (`add_file`, `reset_session`, `get_session_data`)
    - Tool dispatch in `_execute_tools()`
    - Content extraction from response blocks

---

## Summary

| Module | Lines | Current Coverage | Target Coverage |
|--------|-------|-----------------|-----------------|
| `hvac_insulation_estimator.py` | 1,081 | 0% | 80%+ |
| `claude_agent_tools.py` | 1,107 | 0% | 60%+ |
| `claude_estimation_agent.py` | 616 | 0% | 50%+ |
| `pydantic_models.py` | 417 | ~30% | 90%+ |
| `errors.py` | 410 | ~20% | 80%+ |
| `utils_cache.py` | 339 | ~50% | 80%+ |
| `utils_async.py` | 326 | 0% | 50%+ |
| `utils_tracking.py` | 300 | ~60% | 80%+ |
| `utils_pdf.py` | 369 | 0% | 60%+ |

The most impactful improvement is fixing the Pydantic v2 compatibility so existing
tests can run, followed by adding tests for `hvac_insulation_estimator.py` — the
core business logic that handles all pricing and material calculations.
