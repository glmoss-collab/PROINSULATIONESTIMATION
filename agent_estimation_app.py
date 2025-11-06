"""
Agent-Powered Estimation App
==============================

Streamlit application with Claude Agents SDK for conversational estimation.
"""

import streamlit as st
import os
import tempfile
import json
from datetime import datetime
from pathlib import Path

# Import the agent
from claude_estimation_agent import InsulationEstimationAgent


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AI Estimation Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state."""
    if "agent" not in st.session_state:
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
            st.session_state.agent = InsulationEstimationAgent(api_key=api_key)
            st.session_state.agent_initialized = True
        except Exception as e:
            st.session_state.agent_initialized = False
            st.session_state.init_error = str(e)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "temp_files" not in st.session_state:
        st.session_state.temp_files = {}


init_session_state()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file to temp directory and return path."""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


def format_session_summary() -> str:
    """Format current session data as readable summary."""
    if not st.session_state.agent_initialized:
        return "Agent not initialized"

    data = st.session_state.agent.get_session_data()

    summary_lines = []

    # Project info
    if data["project_info"]:
        info = data["project_info"]
        summary_lines.append("### Project Information")
        summary_lines.append(f"- **Name**: {info.get('project_name', 'N/A')}")
        summary_lines.append(f"- **Location**: {info.get('location', 'N/A')}")
        summary_lines.append(f"- **Client**: {info.get('client', 'N/A')}")
        summary_lines.append(f"- **Type**: {info.get('project_type', 'N/A')}")
        summary_lines.append("")

    # Specifications
    spec_count = len(data["specifications"])
    if spec_count > 0:
        summary_lines.append(f"### Specifications ({spec_count} items)")
        for idx, spec in enumerate(data["specifications"][:5], 1):
            system = spec.get("system_type", "N/A")
            material = spec.get("material", "N/A")
            thickness = spec.get("thickness", 0)
            summary_lines.append(f"{idx}. {system.title()}: {thickness}\" {material}")

        if spec_count > 5:
            summary_lines.append(f"   *(and {spec_count - 5} more...)*")
        summary_lines.append("")

    # Measurements
    measurement_count = len(data["measurements"])
    if measurement_count > 0:
        summary_lines.append(f"### Measurements ({measurement_count} items)")

        # Calculate totals
        total_duct_lf = sum(
            m.get("length", 0) for m in data["measurements"]
            if m.get("system_type") == "duct"
        )
        total_pipe_lf = sum(
            m.get("length", 0) for m in data["measurements"]
            if m.get("system_type") == "pipe"
        )

        summary_lines.append(f"- **Total Ductwork**: {total_duct_lf:,.1f} LF")
        summary_lines.append(f"- **Total Piping**: {total_pipe_lf:,.1f} LF")
        summary_lines.append("")

    # Pricing
    if data["pricing"]:
        pricing = data["pricing"]
        summary_lines.append("### Pricing Summary")
        summary_lines.append(f"- **Materials**: ${pricing.get('material_subtotal', 0):,.2f}")
        summary_lines.append(f"- **Labor**: ${pricing.get('labor_cost', 0):,.2f} ({pricing.get('labor_hours', 0):.1f} hours)")
        summary_lines.append(f"- **Subtotal**: ${pricing.get('subtotal', 0):,.2f}")
        summary_lines.append(f"- **Contingency**: ${pricing.get('contingency', 0):,.2f}")
        summary_lines.append(f"- **TOTAL**: **${pricing.get('total', 0):,.2f}**")
        summary_lines.append("")

    # Quote
    if data["quote"]:
        summary_lines.append("### Quote")
        summary_lines.append(f"✅ Quote generated: {data['quote'].get('quote_number', 'N/A')}")

    if not summary_lines:
        return "*No data available yet. Upload documents or start a conversation!*"

    return "\n".join(summary_lines)


# ============================================================================
# MAIN UI
# ============================================================================

def main():
    """Main application UI."""

    # Title and header
    st.title("🤖 AI-Powered Insulation Estimation Agent")
    st.caption("Powered by Claude 3.5 Sonnet with Agents SDK")

    # Check initialization
    if not st.session_state.agent_initialized:
        st.error(f"❌ Failed to initialize agent: {st.session_state.get('init_error', 'Unknown error')}")
        st.info("Please set ANTHROPIC_API_KEY environment variable or add it to Streamlit secrets.")
        return

    # ========================================================================
    # SIDEBAR - File Upload & Session Management
    # ========================================================================

    with st.sidebar:
        st.header("📁 Upload Documents")

        # Specification PDF
        spec_pdf = st.file_uploader(
            "Specification PDF",
            type=["pdf"],
            help="Upload specification document containing insulation requirements",
            key="spec_upload"
        )

        if spec_pdf:
            if "spec_pdf_path" not in st.session_state.temp_files:
                path = save_uploaded_file(spec_pdf)
                st.session_state.temp_files["spec_pdf_path"] = path
                st.session_state.agent.add_file(path, "spec")
                st.success(f"✅ {spec_pdf.name}")
            else:
                st.success(f"✅ {spec_pdf.name} (loaded)")

        # Drawing PDF
        drawing_pdf = st.file_uploader(
            "Drawing PDF",
            type=["pdf"],
            help="Upload mechanical drawings for takeoff measurements",
            key="drawing_upload"
        )

        if drawing_pdf:
            if "drawing_pdf_path" not in st.session_state.temp_files:
                path = save_uploaded_file(drawing_pdf)
                st.session_state.temp_files["drawing_pdf_path"] = path
                st.session_state.agent.add_file(path, "drawing")
                st.success(f"✅ {drawing_pdf.name}")
            else:
                st.success(f"✅ {drawing_pdf.name} (loaded)")

        # Pricebook
        pricebook_file = st.file_uploader(
            "Price Book (Optional)",
            type=["json", "csv", "xlsx"],
            help="Upload custom distributor price book",
            key="pricebook_upload"
        )

        if pricebook_file:
            if "pricebook_path" not in st.session_state.temp_files:
                path = save_uploaded_file(pricebook_file)
                st.session_state.temp_files["pricebook_path"] = path
                st.session_state.agent.add_file(path, "pricebook")
                st.success(f"✅ {pricebook_file.name}")
            else:
                st.success(f"✅ {pricebook_file.name} (loaded)")

        st.divider()

        # Quick Actions
        st.header("⚡ Quick Actions")

        if st.button("🔍 Analyze All Documents", use_container_width=True):
            if st.session_state.temp_files:
                prompt = "Please analyze all uploaded documents and extract project info, specifications, and measurements."
                st.session_state.trigger_prompt = prompt
                st.rerun()
            else:
                st.warning("Please upload documents first")

        if st.button("💰 Calculate Pricing", use_container_width=True):
            prompt = "Calculate pricing for all specifications and measurements."
            st.session_state.trigger_prompt = prompt
            st.rerun()

        if st.button("📄 Generate Quote", use_container_width=True):
            prompt = "Generate a complete professional quote with all available data."
            st.session_state.trigger_prompt = prompt
            st.rerun()

        st.divider()

        # Session Management
        st.header("⚙️ Session")

        if st.button("🔄 Reset Session", use_container_width=True):
            st.session_state.agent.reset_session()
            st.session_state.messages = []
            st.session_state.temp_files = {}
            st.success("Session reset!")
            st.rerun()

        if st.button("💾 Export Session Data", use_container_width=True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"session_export_{timestamp}.json"

            st.session_state.agent.export_session(export_path)

            with open(export_path, "r") as f:
                session_json = f.read()

            st.download_button(
                label="Download JSON",
                data=session_json,
                file_name=export_path,
                mime="application/json"
            )

    # ========================================================================
    # MAIN AREA - Chat Interface & Session Summary
    # ========================================================================

    # Create two columns
    chat_col, summary_col = st.columns([2, 1])

    # Left column - Chat
    with chat_col:
        st.subheader("💬 Conversation")

        # Display chat history
        chat_container = st.container(height=500)

        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask me anything about your estimate...", key="chat_input"):
            st.session_state.trigger_prompt = prompt

        # Handle triggered prompts (from buttons or chat input)
        if hasattr(st.session_state, "trigger_prompt"):
            prompt = st.session_state.trigger_prompt
            del st.session_state.trigger_prompt

            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Build context
            context = {}
            if "spec_pdf_path" in st.session_state.temp_files:
                context["spec_pdf"] = st.session_state.temp_files["spec_pdf_path"]
            if "drawing_pdf_path" in st.session_state.temp_files:
                context["drawing_pdf"] = st.session_state.temp_files["drawing_pdf_path"]
            if "pricebook_path" in st.session_state.temp_files:
                context["pricebook"] = st.session_state.temp_files["pricebook_path"]

            # Show thinking indicator
            with st.spinner("🤔 Agent is thinking..."):
                try:
                    response = st.session_state.agent.run(prompt, context=context)

                    # Add assistant message
                    st.session_state.messages.append({"role": "assistant", "content": response})

                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

            st.rerun()

    # Right column - Session Summary
    with summary_col:
        st.subheader("📊 Session Summary")

        summary_container = st.container(height=500)

        with summary_container:
            summary_markdown = format_session_summary()
            st.markdown(summary_markdown)

        # Download buttons for generated files
        data = st.session_state.agent.get_session_data()

        if data["quote"]:
            st.divider()
            st.markdown("### 📥 Downloads")

            quote_text = data["quote"].get("quote_text", "")
            if quote_text:
                st.download_button(
                    label="📄 Download Quote (TXT)",
                    data=quote_text,
                    file_name=f"quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            material_list = data["quote"].get("material_list", "")
            if material_list:
                st.download_button(
                    label="📋 Download Material List",
                    data=material_list,
                    file_name=f"materials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    # ========================================================================
    # FOOTER
    # ========================================================================

    st.divider()

    footer_cols = st.columns([1, 1, 1])

    with footer_cols[0]:
        st.caption(f"Model: {st.session_state.agent.model}")

    with footer_cols[1]:
        st.caption(f"Messages: {len(st.session_state.messages)}")

    with footer_cols[2]:
        session_data = st.session_state.agent.get_session_data()
        items_count = (
            len(session_data["specifications"]) +
            len(session_data["measurements"])
        )
        st.caption(f"Data Items: {items_count}")


# ============================================================================
# EXAMPLE PROMPTS (Expander at bottom)
# ============================================================================

def show_examples():
    """Show example prompts in an expander."""
    with st.expander("💡 Example Prompts"):
        st.markdown("""
        ### Getting Started
        - "Analyze the uploaded specification PDF and tell me what you find"
        - "Extract all measurements from the drawing PDF"
        - "What specifications are needed for this project?"

        ### Analysis & Validation
        - "Check if the specifications match the measurements"
        - "Are there any missing requirements or conflicts?"
        - "Validate the specifications against industry standards"

        ### Calculations
        - "Calculate material quantities for all items"
        - "What's the estimated labor hours for this project?"
        - "Calculate pricing with 15% markup"

        ### Alternatives & Optimization
        - "Can you suggest cost-saving alternatives?"
        - "What would it cost if we used elastomeric instead of fiberglass?"
        - "Show me different options with pricing comparisons"

        ### Quote Generation
        - "Generate a complete professional quote"
        - "Create a material list for my distributor"
        - "Generate an executive summary of the estimate"

        ### Complex Workflows
        - "I have a 75-ton rooftop unit in Phoenix with outdoor ductwork. Give me a typical estimate."
        - "This is a hospital project with strict energy codes. What specs do you recommend?"
        - "Compare the cost of R-6 vs R-8 ductwork for this project"
        """)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
    show_examples()
