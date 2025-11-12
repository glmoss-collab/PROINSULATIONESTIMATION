#!/usr/bin/env python3
"""
Simplest Workflow Integration Example

This demonstrates the easiest way to integrate the workflow orchestrator
with the HVAC Insulation Estimation skill.
"""

import os
from claude_workflow_enhancement import WorkflowOrchestrator


def simple_workflow_example():
    """
    Easiest workflow example - track progress through estimation stages.

    This shows the minimal code needed to use the workflow orchestrator.
    """
    print("\n" + "="*70)
    print("EASIEST WORKFLOW INTEGRATION EXAMPLE")
    print("="*70)

    # 1. Create workflow orchestrator
    workflow = WorkflowOrchestrator()
    print("\n✓ Workflow orchestrator created\n")

    # 2. Show current stage
    current = workflow.get_current_stage()
    print(f"📍 Current Stage: {current.config.name.value}")
    print(f"   Description: {current.config.description}")
    print(f"   Tools: {', '.join(current.config.tools_available)}\n")

    # 3. Add data for discovery stage
    print("📝 Adding discovery data...")
    workflow.update_stage_data({
        "project_type": "commercial",
        "building_type": "office",
        "system_type": "HVAC",
        "square_footage": 50000,
        "has_specifications": True,
        "has_drawings": True
    })

    # 4. Get recommendations
    recommendations = workflow.get_recommendations()
    if recommendations:
        print(f"\n💡 Recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("\n✓ No recommendations - data looks good!")

    # 5. Complete current stage
    workflow.complete_stage(cost=0.05)
    print(f"\n✓ Completed {current.config.name.value} stage")

    # 6. Advance to next stage
    if workflow.advance_to_next_stage():
        current = workflow.get_current_stage()
        print(f"✓ Advanced to {current.config.name.value} stage\n")

    # 7. Show workflow status
    status = workflow.get_workflow_status()
    print("📊 Workflow Status:")
    print(f"   Progress: {status['progress_pct']:.0f}%")
    print(f"   Stage: {status['current_stage']}")
    print(f"   Completed: {status['stages_completed']}/{status['total_stages']}")
    print(f"   Cost: ${status['total_cost']:.2f}")
    print(f"   Quality: {status['overall_quality']:.1%}")

    return workflow


def complete_workflow_example():
    """
    Complete workflow example - run through all stages.

    This shows how to process a complete estimation workflow.
    """
    print("\n\n" + "="*70)
    print("COMPLETE WORKFLOW EXAMPLE")
    print("="*70)

    workflow = WorkflowOrchestrator()

    # Mock data for each stage (in real usage, this comes from agent tools)
    stage_data = {
        "discovery": {
            "project_type": "healthcare",
            "building_type": "hospital",
            "system_type": "HVAC",
            "square_footage": 150000,
            "has_specifications": True,
            "has_drawings": True
        },
        "document_analysis": {
            "specifications": [
                {"system_type": "supply_duct", "thickness": 2.0, "material": "fiberglass"},
                {"system_type": "return_duct", "thickness": 1.5, "material": "fiberglass"},
                {"system_type": "chilled_water_pipe", "thickness": 1.0, "material": "elastomeric"}
            ],
            "measurements": [
                {"item_id": "D-001", "system_type": "duct", "size": "24x18", "length": 250},
                {"item_id": "D-002", "system_type": "duct", "size": "18x12", "length": 180},
                {"item_id": "P-001", "system_type": "pipe", "size": "6\"", "length": 400}
            ],
            "extraction_confidence": 0.92
        },
        "data_enrichment": {
            "validated_specs": [
                {"system_type": "supply_duct", "thickness": 2.0, "material": "fiberglass", "validated": True},
                {"system_type": "return_duct", "thickness": 1.5, "material": "fiberglass", "validated": True},
                {"system_type": "chilled_water_pipe", "thickness": 1.0, "material": "elastomeric", "validated": True}
            ],
            "validated_measurements": [
                {"item_id": "D-001", "system_type": "duct", "size": "24x18", "length": 250, "validated": True},
                {"item_id": "D-002", "system_type": "duct", "size": "18x12", "length": 180, "validated": True},
                {"item_id": "P-001", "system_type": "pipe", "size": "6\"", "length": 400, "validated": True}
            ]
        },
        "calculation": {
            "material_quantities": {
                "fiberglass_2in": 850,  # sq ft
                "fiberglass_1.5in": 540,  # sq ft
                "elastomeric_1in": 628  # sq ft
            },
            "labor_hours": 45,
            "pricing": {
                "material_total": 4200,
                "labor_total": 2250,
                "total_price": 6450
            }
        },
        "quote_generation": {
            "quote": {
                "quote_number": "Q-2025-001",
                "project_name": "Memorial Hospital HVAC Insulation",
                "total_price": 6450,
                "date": "2025-11-12"
            }
        }
    }

    print("\n🚀 Processing workflow through all stages...\n")

    stage_costs = [0.05, 0.03, 0.02, 0.03, 0.02]  # Cost per stage
    stage_number = 0

    while not workflow.is_complete():
        current = workflow.get_current_stage()
        stage_name = current.config.name.value

        print(f"{'─'*70}")
        print(f"Stage {stage_number + 1}/5: {stage_name.upper()}")
        print(f"{'─'*70}")
        print(f"Description: {current.config.description}")

        # Update with stage data
        if stage_name in stage_data:
            workflow.update_stage_data(stage_data[stage_name])
            print(f"✓ Processed data for {stage_name}")

        # Get recommendations
        recs = workflow.get_recommendations()
        if recs:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(recs[:3], 1):  # Show max 3
                print(f"   {i}. {rec}")

        # Complete stage
        cost = stage_costs[stage_number] if stage_number < len(stage_costs) else 0.02
        workflow.complete_stage(cost=cost)
        print(f"\n✓ Completed {stage_name} (cost: ${cost:.2f})")

        # Show progress
        status = workflow.get_workflow_status()
        print(f"   Progress: {status['progress_pct']:.0f}% | Total cost: ${status['total_cost']:.2f}\n")

        # Advance
        if not workflow.is_complete():
            workflow.advance_to_next_stage()

        stage_number += 1

    # Final summary
    print("=" * 70)
    print("WORKFLOW COMPLETE! 🎉")
    print("=" * 70)

    status = workflow.get_workflow_status()
    print(f"\n📊 Final Statistics:")
    print(f"   ✓ All {status['total_stages']} stages completed")
    print(f"   ✓ Total cost: ${status['total_cost']:.2f}")
    print(f"   ✓ Quality score: {status['overall_quality']:.1%}")
    print(f"   ✓ Validation pass rate: {status['validation_pass_rate']:.1%}")

    # Show quote details
    quote_stage = workflow.get_stage_by_name(
        workflow.stages[-1].config.name
    )
    if quote_stage and "quote" in quote_stage.data:
        quote = quote_stage.data["quote"]
        print(f"\n📄 Generated Quote:")
        print(f"   Quote #: {quote.get('quote_number')}")
        print(f"   Project: {quote.get('project_name')}")
        print(f"   Total: ${quote.get('total_price'):,.2f}")

    return workflow


def with_skill_integration_example():
    """
    Example showing how to integrate workflow with HVAC skill.

    This demonstrates the pattern for using workflow + skill together.
    """
    print("\n\n" + "="*70)
    print("WORKFLOW + SKILL INTEGRATION PATTERN")
    print("="*70)

    # Note: This example shows the pattern without actually importing the skill
    # to avoid API key requirements for this demo

    print("""
The integration pattern is straightforward:

1. CREATE BOTH COMPONENTS:

   from hvac_insulation_skill import HVACInsulationSkill
   from claude_workflow_enhancement import WorkflowOrchestrator

   skill = HVACInsulationSkill(api_key="your-key")
   workflow = WorkflowOrchestrator()


2. USE WORKFLOW TO GUIDE SKILL:

   while not workflow.is_complete():
       current_stage = workflow.get_current_stage()

       # Get stage-specific recommendations
       recs = workflow.get_recommendations()

       # Run skill for current stage
       result = skill.run(f"Process {current_stage.config.name.value}")

       # Update workflow with results
       workflow.update_stage_data(skill.session_data)
       workflow.complete_stage(cost=0.03)
       workflow.advance_to_next_stage()


3. MONITOR PROGRESS:

   status = workflow.get_workflow_status()
   print(f"Progress: {status['progress_pct']:.0f}%")
   print(f"Cost: ${status['total_cost']:.2f}")
   print(f"Quality: {status['overall_quality']:.1%}")


4. GET FINAL RESULTS:

   # From workflow
   final_status = workflow.get_workflow_status()
   audit_trail = workflow.get_audit_trail()

   # From skill
   quote = skill.session_data.get('quote')
   pricing = skill.session_data.get('pricing')

    """)

    print("=" * 70)
    print("This pattern provides:")
    print("  ✓ Structured progression through stages")
    print("  ✓ Smart recommendations at each step")
    print("  ✓ Cost and quality tracking")
    print("  ✓ Validation gates between stages")
    print("  ✓ Complete audit trail")
    print("=" * 70)


if __name__ == "__main__":
    # Run examples
    print("\n" + "="*70)
    print("HVAC WORKFLOW - SIMPLE INTEGRATION EXAMPLES")
    print("="*70)

    # Example 1: Basic workflow usage
    workflow1 = simple_workflow_example()

    # Example 2: Complete workflow
    workflow2 = complete_workflow_example()

    # Example 3: Integration pattern
    with_skill_integration_example()

    print("\n\n✅ All examples completed successfully!")
    print("\nNext steps:")
    print("  1. Try test_easiest_workflow.py for comprehensive tests")
    print("  2. Review claude_workflow_enhancement.py for full API")
    print("  3. Integrate with hvac_insulation_skill.py for production use")
    print()
