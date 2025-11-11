#!/usr/bin/env python3
"""
Demo script for Claude Estimation Agent
========================================

This script demonstrates the agent's capabilities with example workflows.
"""

import os
import sys
import argparse
from pathlib import Path

from claude_estimation_agent import create_agent, quick_estimate


def demo_conversational():
    """Demo: Conversational estimation without PDFs."""
    print("=" * 70)
    print("DEMO 1: Conversational Estimation (No PDFs)")
    print("=" * 70)
    print()

    agent = create_agent()

    print("Scenario: User wants estimate for rooftop HVAC system")
    print()

    # Simulate conversation
    queries = [
        "I need a quote for insulating a 50-ton rooftop HVAC system in Phoenix, AZ. About 30% of ductwork will be on the roof.",
        "What are the typical specifications you'd recommend?",
        "Can you estimate the total cost with typical measurements?"
    ]

    for query in queries:
        print(f"User: {query}")
        print()
        print("Agent: ", end="", flush=True)

        response = agent.run(query)
        print(response)
        print()
        print("-" * 70)
        print()

    # Show session summary
    print("Session Summary:")
    print(agent._get_session_summary())
    print()


def demo_pdf_analysis(spec_pdf: str, drawing_pdf: str = None):
    """Demo: Analyze PDFs and generate quote."""
    print("=" * 70)
    print("DEMO 2: PDF Analysis & Quote Generation")
    print("=" * 70)
    print()

    if not Path(spec_pdf).exists():
        print(f"❌ Error: Specification PDF not found: {spec_pdf}")
        print()
        print("To run this demo, provide a valid PDF path:")
        print(f"  python demo_agent.py --spec /path/to/spec.pdf")
        return

    agent = create_agent()

    print(f"Analyzing PDF: {spec_pdf}")
    print()

    # Workflow
    context = {"spec_pdf": spec_pdf}
    if drawing_pdf:
        context["drawing_pdf"] = drawing_pdf
        print(f"Drawing PDF: {drawing_pdf}")
        print()

    # Single comprehensive request
    query = """
    Please analyze all uploaded documents and:
    1. Extract project information
    2. Extract specifications
    3. Extract measurements (if drawings provided)
    4. Validate all data
    5. Calculate pricing with 15% markup
    6. Generate a complete quote

    Show me a summary when done.
    """

    print("Agent: ", end="", flush=True)
    response = agent.run(query, context=context, max_iterations=15)
    print(response)
    print()

    # Show final data
    print("=" * 70)
    print("Final Session Data:")
    print("=" * 70)
    print()

    data = agent.get_session_data()

    if data["project_info"]:
        print("Project:", data["project_info"].get("project_name", "N/A"))

    print(f"Specifications: {len(data['specifications'])} items")
    print(f"Measurements: {len(data['measurements'])} items")

    if data["pricing"]:
        print(f"Total Cost: ${data['pricing']['total']:,.2f}")

    if data["quote"]:
        print(f"Quote Number: {data['quote']['quote_number']}")

    print()


def demo_quick_estimate(spec_pdf: str, drawing_pdf: str = None):
    """Demo: Quick estimate in one function call."""
    print("=" * 70)
    print("DEMO 3: Quick Estimate (One Function Call)")
    print("=" * 70)
    print()

    if not Path(spec_pdf).exists():
        print(f"❌ Error: Specification PDF not found: {spec_pdf}")
        return

    print("Running quick_estimate()...")
    print()

    result = quick_estimate(
        spec_pdf=spec_pdf,
        drawing_pdf=drawing_pdf
    )

    print("Agent Response:")
    print(result["response"])
    print()

    if result["quote_ready"]:
        print("✅ Quote generated successfully!")

        quote = result["session_data"]["quote"]
        pricing = result["session_data"]["pricing"]

        print(f"   Quote Number: {quote.get('quote_number', 'N/A')}")
        print(f"   Total: ${pricing.get('total', 0):,.2f}")
    else:
        print("⚠️  Quote not yet complete - may need more information")

    print()


def demo_tool_usage():
    """Demo: Direct tool usage (low-level)."""
    print("=" * 70)
    print("DEMO 4: Direct Tool Usage")
    print("=" * 70)
    print()

    from claude_agent_tools import (
        validate_specifications,
        cross_reference_data,
        calculate_pricing
    )

    # Example specifications
    specs = [
        {
            "system_type": "duct",
            "material": "fiberglass",
            "thickness": 2.0,
            "facing": "FSK",
            "location": "indoor",
            "special_requirements": []
        },
        {
            "system_type": "pipe",
            "material": "elastomeric",
            "thickness": 1.0,
            "location": "outdoor",
            "special_requirements": []  # Missing jacketing!
        }
    ]

    # Example measurements
    measurements = [
        {
            "item_id": "D-001",
            "system_type": "duct",
            "size": "18x12",
            "length": 120.0,
            "location": "Mechanical Room",
            "fittings": {"elbow": 4, "tee": 2}
        },
        {
            "item_id": "P-001",
            "system_type": "pipe",
            "size": "2\"",
            "length": 85.0,
            "location": "Roof",
            "fittings": {"elbow": 6, "tee": 1}
        }
    ]

    print("1. Validating specifications...")
    validation = validate_specifications(specs)
    print(f"   Status: {validation['status']}")
    if validation['warnings']:
        print(f"   Warnings:")
        for warning in validation['warnings']:
            print(f"     - {warning}")
    print()

    print("2. Cross-referencing data...")
    cross_ref = cross_reference_data(specs, measurements)
    print(f"   Status: {cross_ref['status']}")
    print(f"   Matched: {cross_ref['matched_items']} items")
    if cross_ref['missing_specifications']:
        print(f"   Missing specs: {len(cross_ref['missing_specifications'])}")
    print()

    print("3. Calculating pricing...")
    pricing = calculate_pricing(specs, measurements, markup_percent=15.0)
    if pricing["success"]:
        print(f"   Materials: ${pricing['material_subtotal']:,.2f}")
        print(f"   Labor: ${pricing['labor_cost']:,.2f} ({pricing['labor_hours']:.1f} hrs)")
        print(f"   Total: ${pricing['total']:,.2f}")
    else:
        print(f"   Error: {pricing['error']}")
    print()


def demo_session_management():
    """Demo: Session management features."""
    print("=" * 70)
    print("DEMO 5: Session Management")
    print("=" * 70)
    print()

    agent = create_agent()

    # Simulate some work
    print("1. Doing some estimation work...")
    agent.run("I need to estimate ductwork insulation for a small commercial building")
    print()

    # Get session data
    print("2. Getting session data...")
    data = agent.get_session_data()
    print(f"   Messages: {len(agent.conversation_history)}")
    print(f"   Specifications: {len(data['specifications'])}")
    print(f"   Measurements: {len(data['measurements'])}")
    print()

    # Export session
    print("3. Exporting session...")
    export_path = "demo_session_export.json"
    agent.export_session(export_path)
    print(f"   ✅ Exported to: {export_path}")
    print()

    # Reset session
    print("4. Resetting session...")
    agent.reset_session()
    data_after = agent.get_session_data()
    print(f"   Messages after reset: {len(agent.conversation_history)}")
    print(f"   Specifications after reset: {len(data_after['specifications'])}")
    print()


def main():
    """Main demo runner."""
    parser = argparse.ArgumentParser(
        description="Demo script for Claude Estimation Agent"
    )
    parser.add_argument(
        "--demo",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Demo number to run (1-5, default: all)"
    )
    parser.add_argument(
        "--spec",
        help="Path to specification PDF (for demos 2 & 3)"
    )
    parser.add_argument(
        "--drawing",
        help="Path to drawing PDF (optional, for demos 2 & 3)"
    )

    args = parser.parse_args()

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("=" * 70)
        print("ERROR: ANTHROPIC_API_KEY not set")
        print("=" * 70)
        print()
        print("Please set your Anthropic API key:")
        print()
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print()
        print("Or add to .env file:")
        print()
        print("  ANTHROPIC_API_KEY=your-key-here")
        print()
        sys.exit(1)

    print()
    print("*" * 70)
    print("CLAUDE ESTIMATION AGENT - DEMO SUITE")
    print("*" * 70)
    print()

    # Run selected demo or all demos
    if args.demo == 1 or args.demo is None:
        demo_conversational()
        if args.demo is None:
            input("Press Enter to continue to next demo...")
            print()

    if args.demo == 2 or (args.demo is None and args.spec):
        if args.spec:
            demo_pdf_analysis(args.spec, args.drawing)
            if args.demo is None:
                input("Press Enter to continue to next demo...")
                print()
        elif args.demo == 2:
            print("Demo 2 requires --spec argument")
            print()

    if args.demo == 3 or (args.demo is None and args.spec):
        if args.spec:
            demo_quick_estimate(args.spec, args.drawing)
            if args.demo is None:
                input("Press Enter to continue to next demo...")
                print()
        elif args.demo == 3:
            print("Demo 3 requires --spec argument")
            print()

    if args.demo == 4 or args.demo is None:
        demo_tool_usage()
        if args.demo is None:
            input("Press Enter to continue to next demo...")
            print()

    if args.demo == 5 or args.demo is None:
        demo_session_management()
        print()

    print("=" * 70)
    print("DEMOS COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print()
    print("  1. Try the Streamlit app:")
    print("       streamlit run agent_estimation_app.py")
    print()
    print("  2. Try the CLI:")
    print("       python claude_estimation_agent.py")
    print()
    print("  3. Read the setup guide:")
    print("       cat AGENT_SETUP_GUIDE.md")
    print()


if __name__ == "__main__":
    main()
