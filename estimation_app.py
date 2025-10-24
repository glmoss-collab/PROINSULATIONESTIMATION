"""Streamlit application for HVAC insulation estimation using Anthropics Claude."""
from __future__ import annotations

import base64
import os
from datetime import datetime, date
from typing import Any, Iterable, Optional

import streamlit as st

try:  # pragma: no cover - optional dependency for runtime environment
    from anthropic import APIError, Anthropic
except Exception:  # pragma: no cover - handle missing library gracefully
    APIError = Exception  # type: ignore[assignment]
    Anthropic = None  # type: ignore[assignment]


ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
SYSTEM_INSTRUCTIONS = (
    "You are an HVAC mechanical insulation estimating assistant. "
    "Provide detailed, professional, and well-structured responses tailored to "
    "estimating project specifications, drawing takeoffs, and proposal generation."
)

_client: Optional[Anthropic] = None


def encode_file_to_base64(uploaded_file: Any) -> str:
    """Encode an uploaded file (Streamlit UploadedFile) into a base64 string."""

    if uploaded_file is None:
        raise ValueError("No file provided for encoding")

    if hasattr(uploaded_file, "getvalue"):
        file_bytes = uploaded_file.getvalue()
    else:
        file_bytes = uploaded_file.read()

    if not file_bytes:
        raise ValueError("Uploaded file is empty")

    return base64.b64encode(file_bytes).decode("utf-8")


def _ensure_anthropic_client() -> Anthropic:
    """Return a cached Anthropics client, instantiating it when needed."""

    global _client

    if Anthropic is None:  # pragma: no cover - runtime guard
        raise RuntimeError(
            "anthropic package is not installed. Install it with `pip install anthropic`."
        )

    if _client is not None:
        return _client

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured in the environment")

    _client = Anthropic(api_key=api_key)
    return _client


def _extract_text_block(response: Any) -> str:
    """Extract the first text block from an Anthropics response."""

    if not response:
        return ""

    content: Iterable[Any] = getattr(response, "content", [])
    for block in content:
        if isinstance(block, dict):
            if block.get("type") == "text":
                return str(block.get("text", ""))
        else:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                return str(getattr(block, "text", ""))

    return ""


def analyze_specifications(spec_file: Any) -> str:
    """Send the specification PDF to Claude for analysis and summary."""

    client = _ensure_anthropic_client()
    spec_base64 = encode_file_to_base64(spec_file)

    user_prompt = """
    Analyze this mechanical insulation specification PDF. Extract the key requirements
    needed for estimating, including:
    - Relevant sections and system types (ductwork, piping, equipment)
    - Required insulation materials, thicknesses, facings, and special treatments
    - Application notes (indoor/outdoor, vapor barrier, jacketing, codes)
    - Any explicit exclusions, alternates, or contractor responsibilities

    Summarize your findings in a structured markdown format with sections for
    "System Requirements", "Materials", "Special Instructions", and "Notes".
    """

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4000,
            temperature=0.2,
            system=SYSTEM_INSTRUCTIONS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": spec_base64,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                }
            ],
        )
    except APIError as exc:
        raise RuntimeError(f"Specification analysis failed: {exc}") from exc

    return _extract_text_block(response)


# ============================================================================
# NEW HELPER FUNCTION TO ADD
# ============================================================================

def analyze_drawings_and_get_takeoff(drawing_file: Any) -> str:
    """Analyze a drawing PDF with Claude to extract ductwork and piping takeoffs."""

    client = _ensure_anthropic_client()
    drawing_base64 = encode_file_to_base64(drawing_file)

    user_prompt = """
    Analyze this HVAC construction drawing PDF. Your goal is to perform a detailed takeoff
    for **Ductwork and Piping** only.

    1.  **Extract Ductwork Data:** Find all labeled duct sizes (e.g., '24x20', '18x12') and
        measure the **linear feet (LF)** for each size. Also, count the **fittings**
        (elbows/tees) for each size.
    2.  **Extract Piping Data:** Find all labeled pipe sizes (e.g., '2" CHW', '3" HW') and
        measure the **linear feet (LF)** for each size. Also, count the **fittings**
        (elbows/valves).
    3.  **Identify Scale:** Note the drawing scale (e.g., 1/4" = 1'-0").

    Format your final output **ONLY** in a structured text block like this:

    ***TAKEOFF_DATA_START***
    SCALE: [Drawing Scale, e.g., 1/8" = 1'-0"]

    DUCTWORK:
    [Size]: [LF] LF, [Fittings] fittings
    24x20: 180 LF, 6 elbows
    18x14: 225 LF, 4 tees
    ...

    PIPING:
    [Size]: [LF] LF, [Fittings] fittings
    2" CHW: 240 LF, 8 elbows, 4 valves
    1" HW: 180 LF, 6 elbows
    ...
    ***TAKEOFF_DATA_END***

    If you cannot find a specific quantity, use 'N/A' but state the size. Be as accurate as
    possible.
    """

    try:
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=8000,
            temperature=0.1,  # Lower temperature for better accuracy in measurement
            system=SYSTEM_INSTRUCTIONS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": drawing_base64,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                }
            ],
        )
    except APIError as exc:
        raise RuntimeError(f"Drawing analysis failed: {exc}") from exc

    return _extract_text_block(message)


def generate_quote(
    project_info: str, spec_summary: str, takeoff_text: str, customer_name: str
) -> str:
    """Generate a formatted quote using Claude based on gathered project data."""

    client = _ensure_anthropic_client()

    user_prompt = f"""
    You are preparing a professional mechanical insulation proposal for HVAC systems.

    Use the provided information to craft a polished quote addressed to {customer_name}. Include:
    - Executive summary referencing project name, location, and bid date if available
    - Key scope of work derived from the takeoff
    - Materials and insulation systems reflecting the specification analysis
    - Assumptions, exclusions, and qualifications
    - Pricing summary (present as placeholders if actual pricing is not provided)

    Maintain a clear structure with headings, bullet lists, and professional tone. If any
    information is missing, note it gracefully without inventing data.

    PROJECT INFO:
    {project_info}

    SPECIFICATION SUMMARY:
    {spec_summary}

    TAKEOFF DETAILS:
    {takeoff_text}
    """

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4000,
            temperature=0.3,
            system=SYSTEM_INSTRUCTIONS,
            messages=[{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
        )
    except APIError as exc:
        raise RuntimeError(f"Quote generation failed: {exc}") from exc

    return _extract_text_block(response)


# ============================================================================
# UPDATED MAIN FUNCTION (Replaces the old one in estimation_app.py)
# ============================================================================

def main() -> None:
    """Run the Streamlit UI for the HVAC estimation workflow."""

    st.set_page_config(page_title="Guaranteed Insulation - AI Estimator", page_icon="🏗️")

    # Header
    st.title("🏗️ Guaranteed Insulation - AI Estimator")
    st.markdown("**Professional HVAC Mechanical Insulation Quote Generator**")
    st.markdown("---")

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Key check
        if not os.environ.get("ANTHROPIC_API_KEY"):
            st.error("⚠️ ANTHROPIC_API_KEY not set!")
            st.info("Set it in your environment variables or Streamlit secrets")
            api_key = st.text_input("Enter API Key (temporary):", type="password")
            if api_key:
                os.environ["ANTHROPIC_API_KEY"] = api_key
                st.success("API Key set!")
                global _client
                _client = None  # reset so the new key is used on next call
        else:
            st.success("✅ API Key configured")

        st.markdown("---")
        st.header("📚 About")
        st.info(
            """
        This AI-powered estimator:
        - Analyzes PDF specifications
        - **Automates Takeoff from Drawings**
        - Calculates materials & labor
        - Generates professional quotes

        **Powered by Claude 3.5 Sonnet**
        """
        )

    # Main workflow tabs
    # Renamed tab 3 to better reflect the new automated process
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📄 1. Upload Specs",
            "📐 2. Analyze Drawings",
            "📝 3. Review Takeoff",
            "💰 4. Generate Quote",
        ]
    )

    # Tab 1: Upload Specifications
    with tab1:
        st.header("Upload Project Specifications")

        col1, _ = st.columns(2)

        with col1:
            spec_file = st.file_uploader(
                "Upload Specification PDF",
                type=["pdf"],
                help="Upload the project specification document (typically Division 23)",
            )

        if spec_file and st.button("🔍 Analyze Specifications", type="primary"):
            with st.spinner("Analyzing specifications... This may take 30-60 seconds..."):
                try:
                    analysis = analyze_specifications(spec_file)
                    st.session_state["spec_analysis"] = analysis
                    st.session_state["spec_file_name"] = spec_file.name
                    st.success("✅ Specification analysis complete!")
                    st.balloons()
                except Exception as exc:  # pragma: no cover - interactive feedback
                    st.error(f"Error analyzing specifications: {exc}")

        if "spec_analysis" in st.session_state:
            st.success(f"✅ Analysis saved: {st.session_state['spec_file_name']}")
            st.markdown("---")
            st.markdown("Go to **Tab 2** to upload and analyze drawings.")

    # Tab 2: Analyze Drawings (NEW STEP)
    with tab2:
        st.header("Upload and Analyze Construction Drawings")

        drawing_file = st.file_uploader(
            "Upload Mechanical Drawing PDF (Single File)",
            type=["pdf"],
            help="Upload the core drawing file containing ductwork/piping plans (e.g., M-2.0)",
        )

        if drawing_file and st.button("🚀 Run Automated Takeoff", type="primary"):
            with st.spinner("Analyzing drawings and measuring quantities... This may take 60-120 seconds..."):
                try:
                    takeoff_text = analyze_drawings_and_get_takeoff(drawing_file)

                    # We save the raw text output for the user to review/edit
                    st.session_state["automated_takeoff_text"] = takeoff_text
                    st.session_state["drawing_file_name"] = drawing_file.name

                    st.success("✅ Drawing takeoff complete! Review the results in Tab 3.")
                    st.balloons()
                except Exception as exc:  # pragma: no cover - interactive feedback
                    st.error(f"Error analyzing drawings: {exc}")

        if "automated_takeoff_text" in st.session_state:
            st.success(f"✅ Takeoff analysis saved for: {st.session_state['drawing_file_name']}")

    # Tab 3: Review Takeoff Data (Replaced manual entry)
    with tab3:
        st.header("Review & Refine Automated Takeoff Data")

        if "automated_takeoff_text" not in st.session_state:
            st.warning("⚠️ Please complete drawing analysis first (Tab 2)")
        else:
            st.markdown(
                "The AI extracted the following measurements from the drawing. Please review and make any necessary corrections."
            )

            # Allow the user to edit the structured text output
            reviewed_takeoff_text = st.text_area(
                "Automated Takeoff Data (Edit if necessary):",
                value=st.session_state.get("automated_takeoff_text", ""),
                height=350,
            )

            # --- Project Info moved here to tie the takeoff to a project ---
            st.markdown("---")
            with st.expander("📋 Project Information", expanded=True):
                col_left, col_right = st.columns(2)
                with col_left:
                    project_name = st.text_input(
                        "Project Name", value=st.session_state.get("project_name", "")
                    )
                    project_location = st.text_input(
                        "Project Location",
                        value=st.session_state.get("project_location", ""),
                    )
                with col_right:
                    customer_name = st.text_input(
                        "Customer Name", value=st.session_state.get("customer_name", "")
                    )
                    default_bid_date: date = st.session_state.get(
                        "bid_date", datetime.now().date()
                    )
                    bid_date = st.date_input("Bid Date", value=default_bid_date)

                    st.session_state["bid_date"] = bid_date

                # Save project info to session state
                st.session_state["project_name"] = project_name
                st.session_state["project_location"] = project_location
                st.session_state["customer_name"] = customer_name

            # Special Requirements (For any items the AI might miss or for equipment)
            special_items = st.text_area(
                "Special Items / Equipment (Manual Entry):",
                placeholder=(
                    "Cooling tower: Exposed piping, approximately 85 LF\n"
                    "Boiler: 500 MBH\n"
                    "Outdoor jacketing: 120 SF (Manual Add-on)"
                ),
                height=100,
                value=st.session_state.get("special_items", ""),
            )
            st.session_state["special_items"] = special_items
            # --- End Project Info ---

            if st.button("💾 Save Final Takeoff Data", type="primary"):
                bid_date_str = bid_date.strftime("%B %d, %Y") if isinstance(bid_date, date) else str(bid_date)

                # The data stored for the quote generator is now the full text block
                takeoff_data = {
                    "project_name": project_name,
                    "project_location": project_location,
                    "customer_name": customer_name,
                    "bid_date": bid_date_str,
                    "takeoff_text": reviewed_takeoff_text,
                    "special_items": special_items,
                }
                st.session_state["takeoff_data"] = takeoff_data
                st.success("✅ Final Takeoff data saved and ready for quote generation!")

    # Tab 4: Generate Quote
    with tab4:
        st.header("Generate Professional Quote")

        if "takeoff_data" not in st.session_state or "spec_analysis" not in st.session_state:
            st.warning("⚠️ Please complete all previous steps first")
        else:
            st.success("✅ All data ready - ready to generate quote!")

            # Show summary
            with st.expander("📋 Project Summary", expanded=True):
                st.markdown(
                    f"**Project:** {st.session_state['takeoff_data']['project_name']}"
                )
                st.markdown(
                    f"**Customer:** {st.session_state['takeoff_data']['customer_name']}"
                )
                st.markdown(
                    f"**Location:** {st.session_state['takeoff_data']['project_location']}"
                )
                st.markdown(
                    f"**Automated Takeoff:** {st.session_state.get('drawing_file_name', 'N/A')}"
                )

            # Generate button
            if st.button("🎯 Generate Complete Quote", type="primary"):
                with st.spinner("Generating professional quote... This may take 60-90 seconds..."):
                    try:
                        # Compile project info
                        project_info = f"""
                        Project Name: {st.session_state['takeoff_data']['project_name']}
                        Location: {st.session_state['takeoff_data']['project_location']}
                        Bid Date: {st.session_state['takeoff_data']['bid_date']}
                        """

                        # Compile takeoff data (now a single text block with all measurements)
                        takeoff_text = f"""
                        AUTOMATED TAKEOFF MEASUREMENTS:
                        {st.session_state['takeoff_data']['takeoff_text']}

                        SPECIAL ITEMS/EQUIPMENT:
                        {st.session_state['takeoff_data']['special_items']}
                        """

                        # Generate quote
                        quote = generate_quote(
                            project_info,
                            st.session_state["spec_analysis"],
                            takeoff_text,
                            st.session_state["takeoff_data"]["customer_name"],
                        )

                        st.session_state["generated_quote"] = quote
                        st.success("✅ Quote generated successfully!")
                        st.balloons()

                    except Exception as exc:  # pragma: no cover - interactive feedback
                        st.error(f"Error generating quote: {exc}")

            # Display generated quote (rest of the display logic is the same)
            if "generated_quote" in st.session_state:
                st.markdown("---")
                st.markdown("### 📄 Generated Quote")

                # Show quote in text area for editing
                final_quote = st.text_area(
                    "Review and edit quote if needed:",
                    value=st.session_state["generated_quote"],
                    height=600,
                )

                # Download button
                st.download_button(
                    label="📥 Download Quote (TXT)",
                    data=final_quote,
                    file_name=(
                        f"Quote_{st.session_state['takeoff_data']['project_name'].replace(' ', '_')}"
                        f"_{datetime.now().strftime('%Y%m%d')}.txt"
                    ),
                    mime="text/plain",
                )

                # Copy to clipboard button (simulated)
                if st.button("📋 Copy to Clipboard"):
                    st.info("Quote ready to copy! Select all text above and use Ctrl+C (Cmd+C on Mac)")


if __name__ == "__main__":
    main()
