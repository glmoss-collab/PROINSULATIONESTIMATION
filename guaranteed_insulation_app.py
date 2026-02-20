"""
Guaranteed Insulation Inc. — Bid Package App

Upload commercial mechanical drawings/specs (PDF). The app will:
1. Extract specifications and measurements
2. Apply scope filter (external HVAC/mechanical insulation ONLY; excludes duct liner, waste plumbing, etc.)
3. Calculate pricing from the environment pricebook
4. Produce a formal Bid Package with Executive Summary and Financial Breakdown

Company: Guaranteed Insulation Inc.
Scope: External HVAC/mechanical insulation only.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from guaranteed_insulation_bid_package import (
    COMPANY_NAME,
    generate_bid_package_text,
)
from guaranteed_insulation_scope import (
    SCOPE_DESCRIPTION,
    filter_measurements_to_scope,
    filter_specs_to_scope,
    get_scope_exclusion_summary,
)
from hvac_insulation_estimator import (
    DrawingMeasurementExtractor,
    InsulationSpec,
    PricingEngine,
    QuoteGenerator,
    SpecificationExtractor,
)

# Optional AI extractor
try:
    from gemini_pdf_extractor import GeminiPDFExtractor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    GeminiPDFExtractor = None


st.set_page_config(
    page_title=f"{COMPANY_NAME} — Bid Package",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Branding CSS
st.markdown("""
<style>
    .company-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1a5276;
        text-align: center;
        margin-bottom: 0.25rem;
    }
    .company-tagline {
        font-size: 1rem;
        color: #566573;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .upload-box {
        border: 2px dashed #1a5276;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        background-color: #ebf5fb;
        margin: 1rem 0;
    }
    .success-box { background-color: #d4edda; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #28a745; }
    .info-box { background-color: #d1ecf1; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #17a2b8; }
</style>
""", unsafe_allow_html=True)


def init_session():
    if "gi_specs" not in st.session_state:
        st.session_state.gi_specs = []
    if "gi_measurements" not in st.session_state:
        st.session_state.gi_measurements = []
    if "gi_project_info" not in st.session_state:
        st.session_state.gi_project_info = {"project_name": "Commercial Mechanical Project", "location": ""}
    if "gi_quote" not in st.session_state:
        st.session_state.gi_quote = None
    if "gi_scope_exclusion_summary" not in st.session_state:
        st.session_state.gi_scope_exclusion_summary = None
    if "gi_ai_extractor" not in st.session_state:
        st.session_state.gi_ai_extractor = None


def render_header():
    st.markdown(f'<div class="company-header">{COMPANY_NAME}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="company-tagline">Upload mechanical drawings &amp; specs → Receive formal bid package with executive summary and financial breakdown. External HVAC/mechanical insulation only.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")


def render_upload_and_process():
    st.header("1. Upload PDFs")

    st.markdown("""
    **Upload your commercial mechanical specification PDF and/or drawing PDF.**  
    We will extract insulation requirements and takeoff, apply our **external HVAC/mechanical insulation only** scope, and prepare your bid package.
    """)

    col1, col2 = st.columns(2)
    with col1:
        spec_pdf = st.file_uploader("Specification PDF", type=["pdf"], key="gi_spec_pdf", help="Mechanical specs, Division 23, etc.")
    with col2:
        drawing_pdf = st.file_uploader("Drawing PDF (optional)", type=["pdf"], key="gi_drawing_pdf", help="Mechanical plans for takeoff")

    if not spec_pdf and not drawing_pdf:
        st.info("Upload at least a specification PDF to continue.")
        return

    # AI key for extraction
    if AI_AVAILABLE:
        default_key = ""
        try:
            default_key = st.secrets.get("GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        except Exception:
            default_key = os.getenv("GEMINI_API_KEY", "")
        api_key = st.text_input("Gemini API Key (for AI extraction)", value=default_key, type="password", key="gi_api_key")
        if api_key and st.session_state.gi_ai_extractor is None:
            try:
                st.session_state.gi_ai_extractor = GeminiPDFExtractor(api_key=api_key)
            except Exception as e:
                st.error(f"AI init error: {e}")

    use_ai = AI_AVAILABLE and st.session_state.gi_ai_extractor is not None

    if st.button("Process PDFs and prepare bid (scope filter applied)", type="primary", use_container_width=True):
        if not spec_pdf and not drawing_pdf:
            st.error("Please upload at least one PDF.")
            return

        with st.spinner("Extracting from PDFs and applying scope filter..."):
            specs_before, measurements_before = 0, 0
            if use_ai and (spec_pdf or drawing_pdf):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_spec:
                        if spec_pdf:
                            tmp_spec.write(spec_pdf.getvalue())
                            spec_path = tmp_spec.name
                        else:
                            spec_path = None
                    drawing_path = None
                    if drawing_pdf:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_draw:
                            tmp_draw.write(drawing_pdf.getvalue())
                            drawing_path = tmp_draw.name
                    result = st.session_state.gi_ai_extractor.process_complete_project(
                        spec_pdf_path=spec_path or drawing_path,
                        drawing_pdf_path=drawing_path,
                    )
                    if result.get("project_info"):
                        st.session_state.gi_project_info = result["project_info"]
                    raw_specs = []
                    if result.get("specifications"):
                        for s in result["specifications"]:
                            raw_specs.append(
                                InsulationSpec(
                                    system_type=s.get("system_type", "duct"),
                                    size_range=s.get("size_range", "all"),
                                    thickness=float(s.get("thickness", 1.5)),
                                    material=s.get("material", "fiberglass"),
                                    facing=s.get("facing"),
                                    location=s.get("location", "indoor"),
                                    special_requirements=s.get("special_requirements") or [],
                                )
                            )
                    specs_before = len(raw_specs)
                    st.session_state.gi_specs = filter_specs_to_scope(raw_specs)
                    if result.get("measurements"):
                        ext = DrawingMeasurementExtractor()
                        raw_meas = ext.manual_entry_measurements(result["measurements"])
                        measurements_before = len(raw_meas)
                        st.session_state.gi_measurements = filter_measurements_to_scope(raw_meas)
                    else:
                        st.session_state.gi_measurements = []
                        measurements_before = 0
                    st.session_state.gi_scope_exclusion_summary = get_scope_exclusion_summary(
                        specs_before, len(st.session_state.gi_specs),
                        measurements_before, len(st.session_state.gi_measurements),
                    )
                except Exception as e:
                    st.error(f"AI extraction failed: {e}")
                    st.session_state.gi_specs = []
                    st.session_state.gi_measurements = []
            else:
                # Fallback: basic spec extract from first PDF
                st.session_state.gi_specs = []
                st.session_state.gi_measurements = []
                pdf_path = None
                if spec_pdf:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(spec_pdf.getvalue())
                        pdf_path = tmp.name
                elif drawing_pdf:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(drawing_pdf.getvalue())
                        pdf_path = tmp.name
                if pdf_path:
                    extractor = SpecificationExtractor()
                    raw_specs = extractor.extract_from_pdf(pdf_path)
                    specs_before = len(raw_specs)
                    st.session_state.gi_specs = filter_specs_to_scope(raw_specs)
                    st.session_state.gi_scope_exclusion_summary = get_scope_exclusion_summary(
                        specs_before, len(st.session_state.gi_specs), 0, 0,
                    )
            st.success("Processing complete. Scope filter applied (external HVAC/mechanical only).")
        st.rerun()

    if st.session_state.gi_specs or st.session_state.gi_measurements:
        st.markdown("---")
        st.subheader("Filtered scope (included in bid)")
        st.write(f"Specifications: {len(st.session_state.gi_specs)} | Measurements: {len(st.session_state.gi_measurements)}")
        if st.session_state.gi_scope_exclusion_summary:
            st.info(st.session_state.gi_scope_exclusion_summary)


def render_manual_fallback():
    """If no specs/measurements after PDF, allow minimal manual add for demo."""
    if st.session_state.gi_specs or not st.session_state.gi_measurements:
        return
    with st.expander("Add one specification and one measurement manually (if no PDF extraction)"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Add sample duct spec"):
                st.session_state.gi_specs.append(
                    InsulationSpec(
                        system_type="duct",
                        size_range="all",
                        thickness=1.5,
                        material="fiberglass",
                        facing="FSK",
                        location="outdoor",
                        special_requirements=["aluminum_jacket"],
                    )
                )
                st.rerun()
        with c2:
            if st.button("Add sample measurement"):
                ext = DrawingMeasurementExtractor()
                st.session_state.gi_measurements = ext.manual_entry_measurements([
                    {"id": "D-1", "system_type": "duct", "size": '12"', "length": 100, "location": "Roof", "fittings": {}}
                ])
                st.rerun()


def render_calculate_and_bid():
    st.header("2. Calculate and generate bid package")

    if not st.session_state.gi_specs:
        st.warning("No specifications in scope. Upload and process PDFs first, or add a sample spec.")
        return
    if not st.session_state.gi_measurements:
        st.warning("No measurements in scope. Upload and process PDFs with drawings, or add a sample measurement.")
        return

    pricebook_path = Path(__file__).parent / "pricebook_sample.json"
    if not pricebook_path.exists():
        pricebook_path = None

    labor_rate = st.sidebar.number_input("Labor rate ($/hr)", value=65.0, min_value=0.0, step=5.0, key="gi_labor_rate")
    markup = st.sidebar.slider("Markup", 0, 50, 15, key="gi_markup") / 100.0 + 1.0
    contingency = st.sidebar.slider("Contingency %", 0, 20, 10, key="gi_contingency")

    if st.button("Generate formal bid package", type="primary", use_container_width=True):
        with st.spinner("Calculating materials and generating bid..."):
            engine = PricingEngine(price_book_path=str(pricebook_path) if pricebook_path else None, markup=markup)
            materials = engine.calculate_materials(st.session_state.gi_measurements, st.session_state.gi_specs)
            labor_hours, labor_cost = engine.calculate_labor(materials)
            # Override labor rate for display
            labor_cost = labor_hours * labor_rate
            gen = QuoteGenerator()
            # Build labor cost with user's rate
            labor_cost = labor_hours * labor_rate
            quote = gen.generate_quote(
                project_name=st.session_state.gi_project_info.get("project_name", "Commercial Mechanical Project"),
                measurements=st.session_state.gi_measurements,
                materials=materials,
                labor_hours=labor_hours,
                labor_cost=labor_cost,
                specs=st.session_state.gi_specs,
            )
            # Override contingency, total, and labor rate from sidebar
            quote.labor_rate = labor_rate
            quote.contingency_percent = float(contingency)
            contingency_dollars = quote.subtotal * (contingency / 100)
            quote.total = quote.subtotal + contingency_dollars
            st.session_state.gi_quote = quote
        st.success("Bid package ready.")
        st.rerun()

    if st.session_state.gi_quote:
        quote = st.session_state.gi_quote
        st.metric("Total bid", f"${quote.total:,.2f}")
        st.markdown("---")
        st.subheader("3. Download formal bid package")
        bid_text = generate_bid_package_text(quote, st.session_state.gi_scope_exclusion_summary)
        st.download_button(
            label="Download bid package (TXT)",
            data=bid_text,
            file_name=f"Guaranteed_Insulation_Bid_{quote.quote_number}.txt",
            mime="text/plain",
            use_container_width=True,
        )
        with st.expander("Preview bid package"):
            st.text(bid_text)


def main():
    init_session()
    render_header()
    render_upload_and_process()
    render_manual_fallback()
    render_calculate_and_bid()
    st.markdown("---")
    st.markdown(
        f'<div style="text-align: center; color: #666;">{COMPANY_NAME} — {SCOPE_DESCRIPTION}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
