#!/usr/bin/env python3
"""
HVAC Insulation Skill - Usage Examples

This script demonstrates various ways to use the HVAC Insulation Estimation skill
with the Claude Agent SDK.
"""

import os
from hvac_insulation_skill import (
    HVACInsulationSkill,
    quick_estimate,
    extract_specs_only,
    extract_measurements_only
)


def example_1_basic_usage():
    """Example 1: Basic skill usage with agent conversation."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Skill Usage")
    print("=" * 70)

    # Initialize the skill
    skill = HVACInsulationSkill(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Run a simple query
    result = skill.run(
        "What tools do you have available for HVAC insulation estimation?"
    )

    print(f"\nAgent Response:\n{result['response']}")
    print(f"\nTool Calls: {result['tool_calls']}")
    print(f"Iterations: {result['iterations']}")


def example_2_extract_project_info():
    """Example 2: Extract project information from a document."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Extract Project Information")
    print("=" * 70)

    skill = HVACInsulationSkill(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Specify a PDF path (replace with actual path)
    pdf_path = "/path/to/your/project_specs.pdf"

    result = skill.run(
        f"Please extract project information from the document at {pdf_path}"
    )

    print(f"\nAgent Response:\n{result['response']}")
    print(f"\nExtracted Project Info:")
    print(result['session_data'].get('project_info'))


def example_3_direct_tool_call():
    """Example 3: Call tools directly without the agent loop."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Direct Tool Call")
    print("=" * 70)

    skill = HVACInsulationSkill(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Call a tool directly
    pdf_path = "/path/to/your/specifications.pdf"

    result = skill.call_tool_directly(
        "extract_specifications",
        pdf_path=pdf_path,
        pages=[15, 16, 17, 18, 19]  # Optional: specify pages to analyze
    )

    if result['success']:
        print("\nExtraction successful!")
        specs = result['data'].get('specifications', [])
        print(f"Found {len(specs)} specifications:")
        for i, spec in enumerate(specs, 1):
            print(f"\n  Spec {i}:")
            print(f"    System Type: {spec.get('system_type')}")
            print(f"    Thickness: {spec.get('thickness')} inches")
            print(f"    Material: {spec.get('material')}")
            print(f"    Confidence: {spec.get('confidence', 0):.2%}")
    else:
        print(f"\nExtraction failed: {result.get('error')}")


def example_4_complete_workflow():
    """Example 4: Complete estimation workflow."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Complete Estimation Workflow")
    print("=" * 70)

    skill = HVACInsulationSkill(api_key=os.getenv("ANTHROPIC_API_KEY"))

    pdf_path = "/path/to/your/complete_project.pdf"

    # Request a complete estimation
    result = skill.run(
        f"Please perform a complete HVAC insulation estimation for {pdf_path}. "
        f"I need you to:\n"
        f"1. Extract project information\n"
        f"2. Extract insulation specifications\n"
        f"3. Extract measurements from mechanical drawings\n"
        f"4. Validate the specifications\n"
        f"5. Cross-reference specs with measurements\n"
        f"6. Calculate material quantities and pricing\n"
        f"7. Generate a professional quote"
    )

    print(f"\nAgent Response:\n{result['response']}")
    print(f"\nTotal tool calls: {len(result['tool_calls'])}")
    print(f"Iterations: {result['iterations']}")

    # Access session data
    session = result['session_data']
    print(f"\nSession Data Summary:")
    print(f"  - Project Info: {'Yes' if session.get('project_info') else 'No'}")
    print(f"  - Specifications: {len(session.get('specifications', []))}")
    print(f"  - Measurements: {len(session.get('measurements', []))}")
    print(f"  - Pricing: {'Yes' if session.get('pricing') else 'No'}")
    print(f"  - Quote: {'Yes' if session.get('quote') else 'No'}")


def example_5_validate_specifications():
    """Example 5: Validate specifications against industry standards."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Validate Specifications")
    print("=" * 70)

    skill = HVACInsulationSkill(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Example specifications to validate
    specifications = [
        {
            "system_type": "supply_duct",
            "size_range": "12\" and larger",
            "thickness": 2.0,
            "material": "fiberglass",
            "facing": "FSK",
            "location": "outdoor"
        },
        {
            "system_type": "chilled_water_pipe",
            "size_range": "4\" and larger",
            "thickness": 1.0,
            "material": "elastomeric",
            "facing": None,
            "location": "indoor"
        }
    ]

    result = skill.call_tool_directly(
        "validate_specifications",
        specifications=specifications
    )

    if result['success']:
        validation = result['data']
        print(f"\nValidation Status: {validation['status']}")
        print(f"\nErrors: {len(validation.get('errors', []))}")
        for error in validation.get('errors', []):
            print(f"  - {error}")
        print(f"\nWarnings: {len(validation.get('warnings', []))}")
        for warning in validation.get('warnings', []):
            print(f"  - {warning}")
        print(f"\nRecommendations: {len(validation.get('recommendations', []))}")
        for rec in validation.get('recommendations', []):
            print(f"  - {rec}")


def example_6_session_management():
    """Example 6: Managing session data."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Session Management")
    print("=" * 70)

    skill = HVACInsulationSkill(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Perform some operations
    skill.run("List your available tools")

    # Get current session data
    session_data = skill.get_session_data()
    print(f"\nCurrent session data: {session_data}")

    # Export session to file
    skill.export_session("/tmp/hvac_session.json")
    print("\nSession exported to /tmp/hvac_session.json")

    # Reset session
    skill.reset_session()
    print("Session reset")

    # Import session from file
    skill.import_session("/tmp/hvac_session.json")
    print("Session imported from file")


def example_7_convenience_functions():
    """Example 7: Using convenience functions."""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Convenience Functions")
    print("=" * 70)

    # Quick estimate (all-in-one)
    print("\n1. Quick Estimate:")
    result = quick_estimate(
        pdf_path="/path/to/project.pdf",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    print(f"   Status: {result['success']}")

    # Extract specs only
    print("\n2. Extract Specifications Only:")
    specs = extract_specs_only(
        pdf_path="/path/to/specs.pdf",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    print(f"   Found {len(specs.get('data', {}).get('specifications', []))} specs")

    # Extract measurements only
    print("\n3. Extract Measurements Only:")
    measurements = extract_measurements_only(
        pdf_path="/path/to/drawings.pdf",
        scale="1/4\" = 1'",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    print(f"   Found {len(measurements.get('data', {}).get('measurements', []))} items")


def example_8_multi_turn_conversation():
    """Example 8: Multi-turn conversation for complex analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Multi-turn Conversation")
    print("=" * 70)

    skill = HVACInsulationSkill(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Turn 1: Extract specifications
    result1 = skill.run(
        "Extract specifications from /path/to/specs.pdf, focusing on Section 23 07 00"
    )
    print(f"\nTurn 1: {result1['response'][:100]}...")

    # Turn 2: Ask about the extracted specs (maintains context)
    result2 = skill.run(
        "What are the most common insulation thicknesses in the specifications you just extracted?"
    )
    print(f"\nTurn 2: {result2['response'][:100]}...")

    # Turn 3: Validate them
    result3 = skill.run(
        "Validate those specifications against ASHRAE standards"
    )
    print(f"\nTurn 3: {result3['response'][:100]}...")


def example_9_get_available_tools():
    """Example 9: Query available tools."""
    print("\n" + "=" * 70)
    print("EXAMPLE 9: Available Tools")
    print("=" * 70)

    skill = HVACInsulationSkill(api_key=os.getenv("ANTHROPIC_API_KEY"))

    tools = skill.get_available_tools()

    print(f"\nThe skill provides {len(tools)} tools:\n")
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']}")
        print(f"   {tool['description']}\n")


def example_10_error_handling():
    """Example 10: Error handling."""
    print("\n" + "=" * 70)
    print("EXAMPLE 10: Error Handling")
    print("=" * 70)

    skill = HVACInsulationSkill(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Try to call a non-existent tool
    result = skill.call_tool_directly(
        "nonexistent_tool",
        param="value"
    )

    if not result['success']:
        print(f"\nExpected error: {result['error']}")

    # Try with invalid PDF path
    result = skill.call_tool_directly(
        "extract_project_info",
        pdf_path="/nonexistent/file.pdf"
    )

    if not result['success']:
        print(f"\nExpected error: {result['error']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("HVAC INSULATION SKILL - USAGE EXAMPLES")
    print("=" * 70)
    print("\nThese examples demonstrate how to use the HVAC Insulation Estimation")
    print("skill with the Claude Agent SDK.")
    print("\nNote: Update PDF paths in the examples before running.")
    print("=" * 70)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\nERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Please set it before running examples:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        return

    # Run examples (comment out ones you don't want to run)
    try:
        example_1_basic_usage()
        # example_2_extract_project_info()  # Requires PDF path
        # example_3_direct_tool_call()  # Requires PDF path
        # example_4_complete_workflow()  # Requires PDF path
        # example_5_validate_specifications()
        # example_6_session_management()
        # example_7_convenience_functions()  # Requires PDF paths
        # example_8_multi_turn_conversation()  # Requires PDF path
        example_9_get_available_tools()
        example_10_error_handling()

    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
