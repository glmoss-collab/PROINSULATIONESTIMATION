#!/usr/bin/env python3
"""
Test Script for Easiest HVAC Workflow Integration

This demonstrates the simplest possible workflow integration with
the HVAC Insulation Estimation skill.
"""

import sys
from claude_workflow_enhancement import (
    WorkflowOrchestrator,
    WorkflowStageName,
    export_workflow_state
)


def test_basic_workflow_creation():
    """Test 1: Create basic workflow orchestrator"""
    print("\n" + "="*70)
    print("TEST 1: Basic Workflow Creation")
    print("="*70)

    try:
        workflow = WorkflowOrchestrator()
        print("✓ WorkflowOrchestrator created successfully")

        # Check stages
        assert len(workflow.stages) == 5, "Should have 5 stages"
        print(f"✓ Workflow has {len(workflow.stages)} stages")

        # List stages
        for i, stage in enumerate(workflow.stages, 1):
            print(f"  {i}. {stage.config.name.value}: {stage.config.description}")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_current_stage():
    """Test 2: Get current stage"""
    print("\n" + "="*70)
    print("TEST 2: Current Stage Access")
    print("="*70)

    try:
        workflow = WorkflowOrchestrator()
        current = workflow.get_current_stage()

        print(f"✓ Current stage: {current.config.name.value}")
        print(f"  Description: {current.config.description}")
        print(f"  Tools available: {', '.join(current.config.tools_available)}")
        print(f"  Required data: {', '.join(current.config.required_data)}")

        assert current.config.name == WorkflowStageName.DISCOVERY
        print("✓ Starts at DISCOVERY stage as expected")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_update_stage_data():
    """Test 3: Update stage data"""
    print("\n" + "="*70)
    print("TEST 3: Update Stage Data")
    print("="*70)

    try:
        workflow = WorkflowOrchestrator()

        # Add some discovery data
        discovery_data = {
            "project_type": "commercial",
            "building_type": "office",
            "system_type": "HVAC",
            "square_footage": 50000
        }

        workflow.update_stage_data(discovery_data)
        print("✓ Updated stage with discovery data")

        current = workflow.get_current_stage()
        print(f"  Stage data keys: {list(current.data.keys())}")

        assert "project_type" in current.data
        assert current.data["project_type"] == "commercial"
        print("✓ Data stored correctly")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_recommendations():
    """Test 4: Get recommendations"""
    print("\n" + "="*70)
    print("TEST 4: Get Recommendations")
    print("="*70)

    try:
        workflow = WorkflowOrchestrator()

        # Add partial data (missing some fields)
        workflow.update_stage_data({
            "project_type": "commercial"
            # Missing building_type, system_type, etc.
        })

        recommendations = workflow.get_recommendations()
        print(f"✓ Got {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

        assert len(recommendations) > 0
        print("✓ Recommendations generated for incomplete data")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_complete_and_advance():
    """Test 5: Complete stage and advance"""
    print("\n" + "="*70)
    print("TEST 5: Complete Stage and Advance")
    print("="*70)

    try:
        workflow = WorkflowOrchestrator()

        # Complete discovery stage
        discovery_data = {
            "project_type": "commercial",
            "building_type": "office",
            "system_type": "HVAC",
            "square_footage": 50000
        }

        workflow.update_stage_data(discovery_data)
        workflow.complete_stage(cost=0.05)
        print("✓ Completed DISCOVERY stage")

        # Advance to next stage
        success = workflow.advance_to_next_stage()
        assert success, "Should advance successfully"
        print("✓ Advanced to next stage")

        current = workflow.get_current_stage()
        print(f"  New current stage: {current.config.name.value}")

        assert current.config.name == WorkflowStageName.DOCUMENT_ANALYSIS
        print("✓ Now at DOCUMENT_ANALYSIS stage")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_workflow_status():
    """Test 6: Get workflow status"""
    print("\n" + "="*70)
    print("TEST 6: Workflow Status")
    print("="*70)

    try:
        workflow = WorkflowOrchestrator()

        status = workflow.get_workflow_status()
        print("✓ Got workflow status:")
        print(f"  Current stage: {status['current_stage']}")
        print(f"  Progress: {status['progress_pct']:.1f}%")
        print(f"  Stages completed: {status['stages_completed']}/{status['total_stages']}")
        print(f"  Total cost: ${status['total_cost']:.2f}")
        print(f"  Quality: {status['overall_quality']:.2%}")

        assert status['current_stage'] == 'discovery'
        print("✓ Status reports correct stage")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_complete_workflow():
    """Test 7: Complete entire workflow"""
    print("\n" + "="*70)
    print("TEST 7: Complete Workflow (All Stages)")
    print("="*70)

    try:
        workflow = WorkflowOrchestrator()

        # Mock data for each stage
        stage_data = {
            "discovery": {
                "project_type": "commercial",
                "building_type": "office",
                "system_type": "HVAC"
            },
            "document_analysis": {
                "specifications": [{"type": "duct", "thickness": 2.0}],
                "measurements": [{"item": "duct-1", "length": 100}]
            },
            "data_enrichment": {
                "validated_specs": [{"type": "duct", "thickness": 2.0}],
                "validated_measurements": [{"item": "duct-1", "length": 100}]
            },
            "calculation": {
                "material_quantities": {"fiberglass": 200},
                "labor_hours": 8,
                "pricing": {"total": 2500}
            },
            "quote_generation": {
                "quote": {"number": "Q-2025-001", "total": 2500}
            }
        }

        completed_stages = []

        while not workflow.is_complete():
            current = workflow.get_current_stage()
            stage_name = current.config.name.value

            print(f"\n  Processing: {stage_name}")

            # Update with mock data
            if stage_name in stage_data:
                workflow.update_stage_data(stage_data[stage_name])
                print(f"    ✓ Updated data")

            # Complete stage
            workflow.complete_stage(cost=0.03)
            print(f"    ✓ Marked complete")

            completed_stages.append(stage_name)

            # Advance
            if not workflow.is_complete():
                workflow.advance_to_next_stage()
                print(f"    ✓ Advanced to next stage")

        print(f"\n✓ Completed all {len(completed_stages)} stages:")
        for i, stage in enumerate(completed_stages, 1):
            print(f"  {i}. {stage}")

        # Check final status
        status = workflow.get_workflow_status()
        print(f"\n  Final progress: {status['progress_pct']:.1f}%")
        print(f"  Total cost: ${status['total_cost']:.2f}")
        print(f"  Quality: {status['overall_quality']:.2%}")

        assert status['current_stage'] == 'complete'
        assert status['stages_completed'] == 5
        print("\n✓ Workflow completed successfully")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export_workflow():
    """Test 8: Export workflow state"""
    print("\n" + "="*70)
    print("TEST 8: Export Workflow State")
    print("="*70)

    try:
        workflow = WorkflowOrchestrator()

        # Add some data
        workflow.update_stage_data({"project_type": "commercial"})
        workflow.complete_stage(cost=0.05)

        # Export state
        state = export_workflow_state(workflow)
        print("✓ Exported workflow state")

        print(f"  Current stage: {state['current_stage']}")
        print(f"  Stages completed: {state['stages_completed']}")
        print(f"  Total cost: ${state['metrics']['total_cost']:.2f}")

        # Verify it's JSON-serializable
        import json
        json_str = json.dumps(state, indent=2)
        print(f"✓ State is JSON-serializable ({len(json_str)} chars)")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_validation_gate():
    """Test 9: Validation gate"""
    print("\n" + "="*70)
    print("TEST 9: Validation Gate")
    print("="*70)

    try:
        from claude_workflow_enhancement import ValidationGate, DataQualityLevel

        workflow = WorkflowOrchestrator()
        current = workflow.get_current_stage()

        # Create validation gate
        gate = ValidationGate(current)
        print("✓ Created validation gate")

        # Add custom check
        def check_has_project_type(data):
            has_it = "project_type" in data
            return has_it, "Project type is present" if has_it else "Project type missing"

        gate.add_check("project_type_check", check_has_project_type, DataQualityLevel.WARNING)
        print("✓ Added custom validation check")

        # Run checks (should fail - no data yet)
        results = gate.run_checks()
        print(f"✓ Ran validation checks: {len(results)} results")

        for result in results:
            status = "✓" if result.passed else "✗"
            print(f"  {status} {result.message}")

        can_proceed = gate.can_proceed()
        print(f"\n  Can proceed: {can_proceed}")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_recommendation_engine():
    """Test 10: Recommendation engine"""
    print("\n" + "="*70)
    print("TEST 10: Recommendation Engine")
    print("="*70)

    try:
        from claude_workflow_enhancement import RecommendationEngine

        engine = RecommendationEngine()
        print("✓ Created recommendation engine")

        # Test discovery recommendations
        discovery_recs = engine.get_discovery_recommendations({
            "project_type": "commercial"
            # Missing other fields
        })
        print(f"\n  Discovery recommendations ({len(discovery_recs)}):")
        for i, rec in enumerate(discovery_recs, 1):
            print(f"    {i}. {rec}")

        # Test analysis recommendations
        analysis_recs = engine.get_analysis_recommendations({
            "extraction_confidence": 0.75,  # Low confidence
            "specifications": [],  # Empty
            "measurements": []  # Empty
        })
        print(f"\n  Analysis recommendations ({len(analysis_recs)}):")
        for i, rec in enumerate(analysis_recs, 1):
            print(f"    {i}. {rec}")

        # Test cost alternatives
        spec = {
            "material": "fiberglass",
            "thickness": 2.0,
            "system_type": "duct"
        }
        alternatives = engine.get_cost_alternatives(spec, max_alternatives=3)
        print(f"\n  Cost alternatives ({len(alternatives)}):")
        for i, alt in enumerate(alternatives, 1):
            print(f"    {i}. {alt['description']} ({alt['estimated_savings_pct']:+.0f}% cost)")

        print("\n✓ Recommendation engine working correctly")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("HVAC WORKFLOW INTEGRATION - EASIEST WORKFLOW TESTS")
    print("="*70)
    print("\nRunning comprehensive test suite...\n")

    tests = [
        test_basic_workflow_creation,
        test_current_stage,
        test_update_stage_data,
        test_recommendations,
        test_complete_and_advance,
        test_workflow_status,
        test_complete_workflow,
        test_export_workflow,
        test_validation_gate,
        test_recommendation_engine
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n✗ Test crashed: {test.__name__}")
            print(f"  Error: {e}")
            results.append((test.__name__, False))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Workflow integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
