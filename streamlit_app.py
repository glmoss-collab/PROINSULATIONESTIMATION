"""HVAC Insulation Estimator - Streamlit SaaS Application

Professional estimation tool for mechanical insulation contractors.
Upload specifications, enter measurements, get instant quotes.
"""

import io
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from hvac_insulation_estimator import (
    DrawingMeasurementExtractor,
    InsulationSpec,
    MaterialItem,
    MeasurementItem,
    PricingEngine,
    QuoteGenerator,
    SpecificationExtractor,
)

# Import AI extractor
try:
    from gemini_pdf_extractor import GeminiPDFExtractor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    GeminiPDFExtractor = None

# Page configuration
st.set_page_config(
    page_title="HVAC Insulation Estimator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'specs' not in st.session_state:
        st.session_state.specs = []
    if 'measurements' not in st.session_state:
        st.session_state.measurements = []
    if 'materials' not in st.session_state:
        st.session_state.materials = []
    if 'quote' not in st.session_state:
        st.session_state.quote = None
    if 'pricing_engine' not in st.session_state:
        st.session_state.pricing_engine = None
    if 'distributor_prices' not in st.session_state:
        st.session_state.distributor_prices = None
    if 'project_info' not in st.session_state:
        st.session_state.project_info = {"project_name": "", "location": ""}
    if 'ai_extractor' not in st.session_state:
        st.session_state.ai_extractor = None
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = None


def render_header():
    """Render application header."""
    st.markdown('<div class="main-header">🏗️ HVAC Insulation Estimator</div>', unsafe_allow_html=True)

    # Show project info if available
    if st.session_state.project_info.get('project_name'):
        project_name = st.session_state.project_info['project_name']
        location = st.session_state.project_info.get('location', '')
        if location and location != "Not specified":
            st.markdown(f'<div class="sub-header">Project: {project_name} | {location}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="sub-header">Project: {project_name}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sub-header">Professional Mechanical Insulation Estimation Tool</div>', unsafe_allow_html=True)

    st.markdown("---")


def render_sidebar():
    """Render sidebar with configuration options."""
    with st.sidebar:
        st.header("⚙️ Configuration")

        # AI API Key Configuration
        st.subheader("🤖 AI Extraction")

        if AI_AVAILABLE:
            # Check for API key in secrets first (for Streamlit Cloud)
            default_key = ""
            try:
                default_key = st.secrets.get("GEMINI_API_KEY", "")
            except:
                default_key = os.getenv("GEMINI_API_KEY", "")

            api_key = st.text_input(
                "Google Gemini API Key",
                value=default_key,
                type="password",
                help="Get your free API key at: https://aistudio.google.com/app/apikey"
            )

            if api_key:
                st.session_state.gemini_api_key = api_key
                if st.session_state.ai_extractor is None:
                    try:
                        st.session_state.ai_extractor = GeminiPDFExtractor(api_key=api_key)
                        st.success("✓ AI Ready")
                    except Exception as e:
                        st.error(f"Error initializing AI: {str(e)}")
            else:
                st.warning("⚠️ Enter API key to enable AI extraction")
                st.markdown("[Get free API key](https://aistudio.google.com/app/apikey)")

        else:
            st.warning("⚠️ AI features require: `pip install google-generativeai pillow`")

        st.markdown("---")

        # Distributor pricing upload
        st.subheader("Distributor Pricing")
        distributor_name = st.text_input(
            "Distributor Name",
            value="Your Distributor",
            help="Enter the name of your distributor"
        )

        uploaded_pricebook = st.file_uploader(
            "Upload Pricebook",
            type=['json', 'csv', 'xlsx', 'xls'],
            help="Upload your distributor's pricebook (JSON, CSV, or Excel)"
        )

        markup = st.slider(
            "Markup %",
            min_value=0,
            max_value=100,
            value=15,
            step=5,
            help="Percentage markup on distributor prices"
        ) / 100 + 1.0

        # Labor rate configuration
        st.subheader("Labor Rates")
        labor_rate = st.number_input(
            "Hourly Labor Rate ($)",
            min_value=0.0,
            value=65.0,
            step=5.0,
            help="Labor rate per hour"
        )

        # Contingency
        contingency = st.slider(
            "Contingency %",
            min_value=0,
            max_value=20,
            value=10,
            step=1,
            help="Percentage contingency for quote"
        )

        # Load pricebook if uploaded
        if uploaded_pricebook:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_pricebook.name).suffix) as tmp:
                tmp.write(uploaded_pricebook.getvalue())
                tmp_path = tmp.name

            st.session_state.distributor_prices = tmp_path
            st.session_state.distributor_name = distributor_name
            st.session_state.markup = markup
            st.success(f"✓ Loaded {uploaded_pricebook.name}")

        return {
            'distributor_name': distributor_name,
            'markup': markup,
            'labor_rate': labor_rate,
            'contingency': contingency,
        }


def render_spec_input():
    """Render specification input section."""
    st.header("1️⃣ Insulation Specifications")

    tab1, tab2 = st.tabs(["📄 Manual Entry", "📎 Upload PDF"])

    with tab1:
        st.subheader("Add Specification")

        col1, col2, col3 = st.columns(3)

        with col1:
            system_type = st.selectbox(
                "System Type",
                options=["duct", "pipe", "equipment"],
                key="spec_system_type"
            )
            material = st.selectbox(
                "Material",
                options=["fiberglass", "elastomeric", "cellular_glass", "mineral_wool"],
                key="spec_material"
            )

        with col2:
            thickness = st.number_input(
                "Thickness (inches)",
                min_value=0.5,
                max_value=4.0,
                value=1.5,
                step=0.5,
                key="spec_thickness"
            )
            facing = st.selectbox(
                "Facing",
                options=["None", "FSK", "ASJ", "All Service Jacket"],
                key="spec_facing"
            )

        with col3:
            location = st.selectbox(
                "Location",
                options=["indoor", "outdoor", "exposed"],
                key="spec_location"
            )
            size_range = st.text_input(
                "Size Range",
                value="all",
                key="spec_size_range",
                help="e.g., '1-2 inch', '4-12 inch', 'all'"
            )

        # Special requirements
        st.subheader("Special Requirements")
        col1, col2, col3 = st.columns(3)

        with col1:
            aluminum_jacket = st.checkbox("Aluminum Jacketing", key="spec_aluminum")
        with col2:
            mastic = st.checkbox("Mastic Coating", key="spec_mastic")
        with col3:
            bands = st.checkbox("Stainless Bands", key="spec_bands")

        if st.button("➕ Add Specification", type="primary"):
            special_req = []
            if aluminum_jacket:
                special_req.append("aluminum_jacket")
            if mastic:
                special_req.append("mastic_coating")
            if bands:
                special_req.append("stainless_bands")

            spec = InsulationSpec(
                system_type=system_type,
                size_range=size_range,
                thickness=thickness,
                material=material,
                facing=facing if facing != "None" else None,
                special_requirements=special_req,
                location=location,
            )
            st.session_state.specs.append(spec)
            st.success(f"✓ Added {material.title()} specification for {system_type}")
            st.rerun()

    with tab2:
        if st.session_state.ai_extractor:
            st.success("🤖 AI-Powered Extraction Ready")
            st.info("Upload your project specification PDF. AI will automatically extract ALL insulation specifications.")
        else:
            st.warning("⚠️ Enter your Gemini API key in the sidebar to enable AI extraction")

        uploaded_spec_pdf = st.file_uploader(
            "Upload Specification PDF",
            type=['pdf'],
            key="spec_pdf",
            help="Upload project specifications (mechanical, insulation specs, etc.)"
        )

        # Also allow drawing PDF upload here for complete project extraction
        uploaded_drawing_pdf = st.file_uploader(
            "Upload Drawing PDF (Optional)",
            type=['pdf'],
            key="drawing_pdf_specs",
            help="Upload mechanical drawings to extract measurements automatically"
        )

        col1, col2 = st.columns(2)

        with col1:
            if uploaded_spec_pdf and st.button("🤖 AI Extract Specs & Measurements", type="primary", use_container_width=True):
                if not st.session_state.ai_extractor:
                    st.error("❌ Please enter your Gemini API key in the sidebar first")
                else:
                    try:
                        # Save PDFs to temp files
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_spec:
                            tmp_spec.write(uploaded_spec_pdf.getvalue())
                            spec_path = tmp_spec.name

                        drawing_path = None
                        if uploaded_drawing_pdf:
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_draw:
                                tmp_draw.write(uploaded_drawing_pdf.getvalue())
                                drawing_path = tmp_draw.name

                        # Run AI extraction
                        with st.spinner("🤖 AI is analyzing your PDFs... This may take 30-60 seconds..."):
                            result = st.session_state.ai_extractor.process_complete_project(
                                spec_pdf_path=spec_path,
                                drawing_pdf_path=drawing_path
                            )

                        # Extract project info
                        if result.get('project_info'):
                            st.session_state.project_info = result['project_info']
                            st.success(f"✓ Project: {result['project_info'].get('project_name', 'Unknown')}")

                        # Extract specifications
                        if result.get('specifications'):
                            for spec_dict in result['specifications']:
                                spec = InsulationSpec(
                                    system_type=spec_dict.get('system_type', 'duct'),
                                    size_range=spec_dict.get('size_range', 'all'),
                                    thickness=float(spec_dict.get('thickness', 1.5)),
                                    material=spec_dict.get('material', 'fiberglass'),
                                    facing=spec_dict.get('facing'),
                                    location=spec_dict.get('location', 'indoor'),
                                    special_requirements=spec_dict.get('special_requirements', [])
                                )
                                st.session_state.specs.append(spec)
                            st.success(f"✓ Extracted {len(result['specifications'])} specifications")

                        # Extract measurements (if drawing PDF provided)
                        if result.get('measurements'):
                            extractor = DrawingMeasurementExtractor()
                            measurements = extractor.manual_entry_measurements(result['measurements'])
                            st.session_state.measurements.extend(measurements)
                            st.success(f"✓ Extracted {len(result['measurements'])} measurements from drawings")

                        if not result.get('specifications') and not result.get('measurements'):
                            st.warning("⚠️ No specifications or measurements found. Please check your PDF or try manual entry.")

                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error during AI extraction: {str(e)}")
                        st.info("💡 Tip: Make sure your PDF contains clear specification tables or text")

        with col2:
            if uploaded_spec_pdf and st.button("📄 Basic Text Extract", use_container_width=True):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        tmp.write(uploaded_spec_pdf.getvalue())
                        tmp_path = tmp.name

                    extractor = SpecificationExtractor()
                    extracted_specs = extractor.extract_from_pdf(tmp_path)
                    st.session_state.specs.extend(extracted_specs)
                    st.success(f"✓ Extracted {len(extracted_specs)} specifications")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Display current specs
    if st.session_state.specs:
        st.subheader("Current Specifications")
        specs_data = []
        for i, spec in enumerate(st.session_state.specs):
            specs_data.append({
                "#": i + 1,
                "System": spec.system_type.title(),
                "Material": spec.material.title(),
                "Thickness": f"{spec.thickness}\"",
                "Facing": spec.facing or "None",
                "Location": spec.location.title(),
                "Special": ", ".join(spec.special_requirements) if spec.special_requirements else "None",
            })

        df = pd.DataFrame(specs_data)
        st.dataframe(df, use_container_width=True)

        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Clear All Specs", type="secondary"):
                st.session_state.specs = []
                st.rerun()


def render_measurement_input():
    """Render measurement input section."""
    st.header("2️⃣ Measurements")

    tab1, tab2 = st.tabs(["📝 Manual Entry", "📋 Bulk Import"])

    with tab1:
        st.subheader("Add Measurement")

        col1, col2, col3 = st.columns(3)

        with col1:
            item_id = st.text_input(
                "Item ID",
                value=f"ITEM-{len(st.session_state.measurements) + 1:03d}",
                key="meas_id"
            )
            system_type = st.selectbox(
                "System Type",
                options=["duct", "pipe"],
                key="meas_system_type"
            )

        with col2:
            size = st.text_input(
                "Size",
                value='12"',
                key="meas_size",
                help='e.g., 12", 18x12, 2"'
            )
            length = st.number_input(
                "Length (LF)",
                min_value=0.0,
                value=50.0,
                step=1.0,
                key="meas_length"
            )

        with col3:
            location = st.text_input(
                "Location",
                value="Main corridor",
                key="meas_location"
            )
            elevation_changes = st.number_input(
                "Elevation Changes",
                min_value=0,
                value=0,
                step=1,
                key="meas_elevation"
            )

        # Fittings
        st.subheader("Fittings")
        col1, col2, col3 = st.columns(3)

        with col1:
            elbows = st.number_input("Elbows", min_value=0, value=0, step=1, key="meas_elbows")
        with col2:
            tees = st.number_input("Tees", min_value=0, value=0, step=1, key="meas_tees")
        with col3:
            other = st.number_input("Other", min_value=0, value=0, step=1, key="meas_other")

        if st.button("➕ Add Measurement", type="primary"):
            fittings = {}
            if elbows > 0:
                fittings['elbow'] = elbows
            if tees > 0:
                fittings['tee'] = tees
            if other > 0:
                fittings['other'] = other

            measurement = MeasurementItem(
                item_id=item_id,
                system_type=system_type,
                size=size,
                length=length,
                location=location,
                elevation_changes=elevation_changes,
                fittings=fittings,
            )
            st.session_state.measurements.append(measurement)
            st.success(f"✓ Added measurement {item_id}")
            st.rerun()

    with tab2:
        st.info("Upload a CSV file with columns: item_id, system_type, size, length, location, elbows, tees")

        uploaded_csv = st.file_uploader(
            "Upload Measurements CSV",
            type=['csv'],
            key="meas_csv"
        )

        if uploaded_csv:
            try:
                df = pd.read_csv(uploaded_csv)
                st.dataframe(df)

                if st.button("Import Measurements"):
                    extractor = DrawingMeasurementExtractor()
                    measurements_list = []

                    for _, row in df.iterrows():
                        meas_dict = {
                            'id': str(row.get('item_id', '')),
                            'system_type': str(row.get('system_type', 'duct')),
                            'size': str(row.get('size', '12"')),
                            'length': float(row.get('length', 0)),
                            'location': str(row.get('location', '')),
                            'fittings': {}
                        }

                        if 'elbows' in row and row['elbows'] > 0:
                            meas_dict['fittings']['elbow'] = int(row['elbows'])
                        if 'tees' in row and row['tees'] > 0:
                            meas_dict['fittings']['tee'] = int(row['tees'])

                        measurements_list.append(meas_dict)

                    imported = extractor.manual_entry_measurements(measurements_list)
                    st.session_state.measurements.extend(imported)
                    st.success(f"✓ Imported {len(imported)} measurements")
                    st.rerun()
            except Exception as e:
                st.error(f"Error importing CSV: {str(e)}")

    # Display current measurements
    if st.session_state.measurements:
        st.subheader("Current Measurements")
        meas_data = []
        for i, meas in enumerate(st.session_state.measurements):
            fittings_str = ", ".join([f"{count} {name}" for name, count in meas.fittings.items()]) if meas.fittings else "None"
            meas_data.append({
                "#": i + 1,
                "ID": meas.item_id,
                "Type": meas.system_type.title(),
                "Size": meas.size,
                "Length": f"{meas.length:.1f} LF",
                "Location": meas.location,
                "Fittings": fittings_str,
            })

        df = pd.DataFrame(meas_data)
        st.dataframe(df, use_container_width=True)

        total_lf = sum(m.length for m in st.session_state.measurements)
        st.metric("Total Linear Feet", f"{total_lf:.1f} LF")

        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Clear All Measurements", type="secondary"):
                st.session_state.measurements = []
                st.rerun()


def render_calculation_section(config: Dict[str, Any]):
    """Render calculation and results section."""
    st.header("3️⃣ Calculate Estimate")

    if not st.session_state.specs:
        st.warning("⚠️ Please add at least one specification before calculating.")
        return

    if not st.session_state.measurements:
        st.warning("⚠️ Please add at least one measurement before calculating.")
        return

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Ready to Calculate")
        st.write(f"✓ {len(st.session_state.specs)} specifications")
        st.write(f"✓ {len(st.session_state.measurements)} measurements")
        st.write(f"✓ {config['markup']:.0%} markup")

        if st.button("🔢 Calculate Estimate", type="primary", use_container_width=True):
            with st.spinner("Calculating materials and pricing..."):
                # Initialize pricing engine
                pricing_engine = PricingEngine(
                    price_book_path=st.session_state.get('distributor_prices'),
                    markup=config['markup'],
                    distributor_name=config['distributor_name'],
                )

                # Calculate materials
                materials = pricing_engine.calculate_materials(
                    st.session_state.measurements,
                    st.session_state.specs
                )

                # Calculate labor
                labor_hours, labor_cost = pricing_engine.calculate_labor(materials)

                # Generate quote
                quote_generator = QuoteGenerator()
                quote = quote_generator.generate_quote(
                    project_name="Streamlit Project",
                    measurements=st.session_state.measurements,
                    materials=materials,
                    labor_hours=labor_hours,
                    labor_cost=labor_cost,
                    specs=st.session_state.specs,
                )

                # Store in session state
                st.session_state.pricing_engine = pricing_engine
                st.session_state.materials = materials
                st.session_state.quote = quote

                st.success("✓ Calculation complete!")
                st.rerun()

    with col2:
        if st.session_state.quote:
            render_results(config)


def render_results(config: Dict[str, Any]):
    """Render calculation results."""
    quote = st.session_state.quote
    pricing_engine = st.session_state.pricing_engine

    st.subheader("Estimate Results")

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Materials",
            f"${sum(m.total_price for m in st.session_state.materials):,.2f}"
        )

    with col2:
        st.metric(
            "Labor",
            f"${quote.labor_hours * config['labor_rate']:,.2f}",
            f"{quote.labor_hours:.1f} hrs"
        )

    with col3:
        st.metric(
            "Subtotal",
            f"${quote.subtotal:,.2f}"
        )

    with col4:
        st.metric(
            "TOTAL",
            f"${quote.total:,.2f}",
            f"+{config['contingency']}% contingency"
        )

    # Distributor pricing info
    if pricing_engine:
        st.markdown("---")
        dist_info = pricing_engine.get_distributor_info()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Distributor:** {dist_info['distributor_name']}")
        with col2:
            st.write(f"**Pricebook Items:** {dist_info['total_items']}")
        with col3:
            st.write(f"**Markup:** {dist_info['markup_percentage']}")

        if dist_info['missing_prices']:
            st.warning(f"⚠️ {len(dist_info['missing_prices'])} items not found in distributor pricebook (using fallback prices)")

    # Materials breakdown
    st.markdown("---")
    st.subheader("Materials Breakdown")

    materials_data = []
    for material in st.session_state.materials:
        materials_data.append({
            "Description": material.description,
            "Quantity": f"{material.quantity:.2f}",
            "Unit": material.unit,
            "Unit Price": f"${material.unit_price:.2f}",
            "Total": f"${material.total_price:.2f}",
            "Category": material.category.title(),
        })

    df = pd.DataFrame(materials_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Category breakdown chart
    st.markdown("---")
    st.subheader("Cost by Category")

    category_totals = {}
    for material in st.session_state.materials:
        if material.category not in category_totals:
            category_totals[material.category] = 0.0
        category_totals[material.category] += material.total_price

    chart_data = pd.DataFrame({
        'Category': [cat.title() for cat in category_totals.keys()],
        'Amount': list(category_totals.values())
    })
    st.bar_chart(chart_data.set_index('Category'))


def render_export_section():
    """Render export and download section."""
    if not st.session_state.quote:
        return

    st.header("4️⃣ Export Quote")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Export quote as text
        quote_generator = QuoteGenerator()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            quote_generator.export_quote_to_file(st.session_state.quote, tmp.name)
            with open(tmp.name, 'r') as f:
                quote_text = f.read()

        st.download_button(
            label="📄 Download Quote (TXT)",
            data=quote_text,
            file_name=f"quote_{st.session_state.quote.quote_number}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col2:
        # Export material list
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            quote_generator.export_material_list(st.session_state.quote, tmp.name)
            with open(tmp.name, 'r') as f:
                material_list_text = f.read()

        st.download_button(
            label="📋 Download Material List (TXT)",
            data=material_list_text,
            file_name=f"materials_{st.session_state.quote.quote_number}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col3:
        # Export as CSV
        materials_data = []
        for material in st.session_state.materials:
            materials_data.append({
                "Description": material.description,
                "Quantity": material.quantity,
                "Unit": material.unit,
                "Unit Price": material.unit_price,
                "Total Price": material.total_price,
                "Category": material.category,
            })

        df = pd.DataFrame(materials_data)
        csv = df.to_csv(index=False)

        st.download_button(
            label="📊 Download Materials (CSV)",
            data=csv,
            file_name=f"materials_{st.session_state.quote.quote_number}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Display pricing report
    if st.session_state.pricing_engine:
        with st.expander("📊 View Detailed Pricing Report"):
            summary = st.session_state.pricing_engine.get_pricing_summary(st.session_state.materials)

            st.json(summary)


def main():
    """Main application entry point."""
    initialize_session_state()
    render_header()

    # Get configuration from sidebar
    config = render_sidebar()

    # Main content area
    render_spec_input()
    st.markdown("---")
    render_measurement_input()
    st.markdown("---")
    render_calculation_section(config)
    st.markdown("---")
    render_export_section()

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666; padding: 2rem;">'
        '🏗️ HVAC Insulation Estimator | Professional Estimation Tool<br>'
        'Built with Streamlit | Powered by Python'
        '</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
