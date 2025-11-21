"""
Demo: Agent Skills for HVAC Insulation Estimation
==================================================

This script demonstrates how to use the advanced agent skills
for professional HVAC insulation estimation workflows.

Run with:
    python demo_skills.py --demo [1-5]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

# Import skills
from agent_skills import (
    IntelligentDocumentProcessor,
    SpecificationIntelligenceEngine,
    SmartQuoteOptimizer,
    ProjectIntelligenceAnalyzer,
    create_skill_registry,
    get_available_skills
)


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_results(results: Dict[str, Any], indent: int = 0):
    """Print results in formatted way."""
    prefix = "  " * indent
    for key, value in results.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_results(value, indent + 1)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            print(f"{prefix}{key}:")
            for item in value:
                print_results(item, indent + 1)
                print()
        else:
            print(f"{prefix}{key}: {value}")


# ==========================================================================
# DEMO 1: List All Available Skills
# ==========================================================================

def demo_1_list_skills():
    """Demo: List all available skills."""
    print_section("DEMO 1: Available Agent Skills")

    skills = get_available_skills()

    print(f"Total Skills Available: {len(skills)}\n")

    for skill in skills:
        print(f"📋 {skill['name']}")
        print(f"   Category: {skill['category']}")
        print(f"   Description: {skill['description']}")
        print(f"   Complexity: {skill['complexity']}")
        print(f"   Requires API: {skill['requires_api']}")
        print()


# ==========================================================================
# DEMO 2: Intelligent Document Processing
# ==========================================================================

def demo_2_document_processing():
    """Demo: Intelligent document processing skill."""
    print_section("DEMO 2: Intelligent Document Processing")

    # This demo shows how the skill would work
    # In production, you'd provide actual PDF path

    print("This skill demonstrates:")
    print("  • Auto-detection of document type (spec vs drawing)")
    print("  • Smart page selection (saves 85% API cost)")
    print("  • Intelligent extraction based on document type")
    print("  • Automatic validation and confidence scoring")
    print()

    print("Example usage:")
    print("""
    from agent_skills import IntelligentDocumentProcessor

    processor = IntelligentDocumentProcessor()

    # Process a document (auto-detects type)
    results = processor.execute(
        pdf_path="project_spec.pdf"
    )

    # Results include:
    # - document_type: "spec", "drawing", or "both"
    # - project_info: Extracted project metadata
    # - specifications: List of insulation specs
    # - measurements: List of measurements
    # - confidence: Overall confidence score
    # - validation: Validation report
    """)

    # Simulate results
    print("\nSimulated Results:")
    simulated_results = {
        "document_type": "spec",
        "pages_analyzed": [1, 2, 3, 15, 16, 17],
        "project_info": {
            "project_name": "Commercial Office HVAC Retrofit",
            "project_number": "2024-CO-0456",
            "location": "Phoenix, AZ"
        },
        "specifications": [
            {
                "system_type": "supply_duct",
                "thickness": 2.0,
                "material": "fiberglass",
                "confidence": 0.95
            },
            {
                "system_type": "chilled_water_pipe",
                "thickness": 1.0,
                "material": "elastomeric",
                "confidence": 0.92
            }
        ],
        "confidence": 0.94,
        "validation": {
            "is_valid": True,
            "warnings": [],
            "suggestions": ["Upload drawing PDF for complete estimate"]
        }
    }

    print_results(simulated_results)


# ==========================================================================
# DEMO 3: Specification Intelligence Engine
# ==========================================================================

def demo_3_specification_intelligence():
    """Demo: Specification intelligence and recommendations."""
    print_section("DEMO 3: Specification Intelligence Engine")

    print("This skill provides:")
    print("  • Validation against industry standards")
    print("  • Intelligent recommendations")
    print("  • Cost-saving alternatives")
    print("  • Compliance checking")
    print("  • Gap analysis")
    print()

    # Simulate specifications
    sample_specs = [
        {
            "system_type": "supply_duct",
            "size_range": "12-24 inch",
            "thickness": 2.0,
            "material": "fiberglass",
            "facing": "FSK",
            "location": "indoor"
        },
        {
            "system_type": "chilled_water_pipe",
            "size_range": "1-2 inch",
            "thickness": 1.0,
            "material": "fiberglass",
            "facing": "ASJ",
            "location": "outdoor",
            "special_requirements": []
        }
    ]

    print("Analyzing sample specifications...")
    print()

    engine = SpecificationIntelligenceEngine()
    results = engine.execute(
        specifications=sample_specs,
        project_type="commercial",
        climate_zone="hot_dry"
    )

    print("Analysis Results:")
    print_results(results)


# ==========================================================================
# DEMO 4: Smart Quote Optimizer
# ==========================================================================

def demo_4_quote_optimization():
    """Demo: Smart quote optimization."""
    print_section("DEMO 4: Smart Quote Optimizer")

    print("This skill optimizes quotes by:")
    print("  • Identifying cost reduction opportunities")
    print("  • Suggesting material substitutions")
    print("  • Analyzing volume discount potential")
    print("  • Recommending labor efficiency improvements")
    print("  • Providing multiple optimization scenarios")
    print()

    # Sample quote data
    sample_quote = {
        "total": 125000,
        "subtotal": 115000,
        "materials": [
            {
                "description": "Fiberglass duct insulation 2\" thick",
                "unit": "LF",
                "quantity": 1200,
                "unit_price": 12.50,
                "total_price": 15000
            },
            {
                "description": "FSK facing",
                "unit": "SF",
                "quantity": 2400,
                "unit_price": 2.25,
                "total_price": 5400
            }
        ],
        "labor_hours": 320,
        "labor_rate": 75,
        "contingency_percent": 12
    }

    print("Optimizing sample quote...")
    print(f"Original Total: ${sample_quote['total']:,.2f}")
    print()

    optimizer = SmartQuoteOptimizer()
    results = optimizer.execute(
        quote_data=sample_quote,
        optimization_goal="balanced"
    )

    print("Optimization Results:")
    print(f"Original Total: ${results['original_total']:,.2f}")
    print()

    for scenario in results.get("optimized_scenarios", []):
        print(f"Scenario: {scenario['name']}")
        print(f"  Strategy: {scenario['strategy']}")
        print(f"  Estimated Savings: ${scenario['estimated_savings']:,.2f}")
        print(f"  Optimized Total: ${scenario['estimated_total']:,.2f}")
        print(f"  Savings Percentage: {scenario['savings_percentage']:.1f}%")
        print(f"  Quality Impact: {scenario['quality_impact']}")
        print()
        print("  Changes:")
        for change in scenario.get("changes", []):
            print(f"    • {change['description']}: ${change['savings']:,.2f}")
        print()

    print("Savings Opportunities:")
    for opp in results.get("savings_opportunities", []):
        print(f"  • {opp['category']}: {opp['opportunity']}")
        if "potential_savings" in opp:
            print(f"    Potential: ${opp['potential_savings']:,.2f}")
        print()


# ==========================================================================
# DEMO 5: Project Intelligence Analyzer
# ==========================================================================

def demo_5_project_intelligence():
    """Demo: Project intelligence and strategic analysis."""
    print_section("DEMO 5: Project Intelligence Analyzer")

    print("This skill provides strategic insights:")
    print("  • Complexity analysis")
    print("  • Timeline estimation")
    print("  • Risk assessment")
    print("  • Strategic recommendations")
    print("  • Project benchmarking")
    print()

    # Sample project data
    sample_project = {
        "project_info": {
            "project_name": "Downtown Hospital HVAC Renovation",
            "project_type": "healthcare",
            "location": "Phoenix, AZ"
        },
        "specifications": [
            {"system_type": "supply_duct", "thickness": 2.0},
            {"system_type": "return_duct", "thickness": 1.5},
            {"system_type": "chilled_water_pipe", "thickness": 1.0},
            {"system_type": "hot_water_pipe", "thickness": 1.5}
        ],
        "measurements": [{"item_id": f"M{i:03d}"} for i in range(75)],
        "quote": {
            "total": 185000,
            "labor_hours": 450,
            "contingency_percent": 8
        }
    }

    print("Analyzing project intelligence...")
    print()

    analyzer = ProjectIntelligenceAnalyzer()
    results = analyzer.execute(project_data=sample_project)

    print("Project Intelligence Report:")
    print_results(results)


# ==========================================================================
# DEMO 6: Complete Workflow
# ==========================================================================

def demo_6_complete_workflow():
    """Demo: Complete estimation workflow using skills."""
    print_section("DEMO 6: Complete Estimation Workflow")

    print("This demonstrates a complete workflow using multiple skills:")
    print()

    print("Step 1: Document Processing")
    print("  ↓")
    print("Step 2: Specification Intelligence")
    print("  ↓")
    print("Step 3: Quote Generation (existing tools)")
    print("  ↓")
    print("Step 4: Quote Optimization")
    print("  ↓")
    print("Step 5: Project Intelligence Analysis")
    print()

    print("Example code for complete workflow:")
    print("""
from agent_skills import create_skill_registry

# Create registry
registry = create_skill_registry()

# Step 1: Process documents
doc_results = registry.execute_skill(
    'intelligent_document_processor',
    pdf_path='project_spec.pdf'
)

# Step 2: Analyze specifications
spec_analysis = registry.execute_skill(
    'specification_intelligence_engine',
    specifications=doc_results['specifications'],
    project_type='commercial'
)

# Step 3: Generate quote (using existing tools)
# ... quote generation code ...

# Step 4: Optimize quote
optimization = registry.execute_skill(
    'smart_quote_optimizer',
    quote_data=quote,
    optimization_goal='balanced'
)

# Step 5: Project intelligence
intelligence = registry.execute_skill(
    'project_intelligence_analyzer',
    project_data={
        'project_info': doc_results['project_info'],
        'specifications': doc_results['specifications'],
        'quote': quote
    }
)

# Present results to user
print(f"Project: {doc_results['project_info']['project_name']}")
print(f"Original Quote: ${quote['total']:,.2f}")
print(f"Optimized Quote: ${optimization['optimized_scenarios'][0]['estimated_total']:,.2f}")
print(f"Estimated Savings: ${optimization['optimized_scenarios'][0]['estimated_savings']:,.2f}")
print(f"Complexity: {intelligence['complexity_analysis']['complexity_level']}")
print(f"Timeline: {intelligence['timeline_estimate']['estimated_duration_weeks']} weeks")
    """)


# ==========================================================================
# DEMO 7: Skill Composition
# ==========================================================================

def demo_7_skill_composition():
    """Demo: Composing skills for advanced workflows."""
    print_section("DEMO 7: Advanced Skill Composition")

    print("Skills can be composed to create advanced workflows:")
    print()

    print("Example: Smart Pre-Qualification Workflow")
    print("""
def pre_qualify_project(pdf_path, budget_limit):
    \"\"\"Pre-qualify a project quickly.\"\"\"

    registry = create_skill_registry()

    # Quick document scan
    doc_scan = registry.execute_skill(
        'intelligent_document_processor',
        pdf_path=pdf_path,
        priority_pages=[1, 2, 3]  # Just cover pages
    )

    # Assess complexity
    intelligence = registry.execute_skill(
        'project_intelligence_analyzer',
        project_data=doc_scan
    )

    # Quick cost estimate based on complexity
    complexity = intelligence['complexity_analysis']['complexity_level']

    if complexity == 'high' and budget_limit < 100000:
        return {
            'qualified': False,
            'reason': 'Project complexity exceeds budget capacity'
        }

    return {
        'qualified': True,
        'complexity': complexity,
        'estimated_timeline': intelligence['timeline_estimate']
    }
    """)

    print("\nExample: Continuous Optimization Loop")
    print("""
def optimize_iteratively(quote_data, target_savings_pct):
    \"\"\"Iteratively optimize quote to reach target savings.\"\"\"

    registry = create_skill_registry()
    current_total = quote_data['total']
    target_total = current_total * (1 - target_savings_pct / 100)

    iterations = 0
    max_iterations = 5

    while current_total > target_total and iterations < max_iterations:
        # Optimize
        result = registry.execute_skill(
            'smart_quote_optimizer',
            quote_data=quote_data,
            optimization_goal='maximum_savings'
        )

        # Get best scenario
        best_scenario = result['optimized_scenarios'][0]

        # Check if we can safely apply
        if result['risk_analysis']['overall_risk'] == 'high':
            break  # Stop if risks are too high

        # Apply optimizations
        quote_data = apply_optimizations(quote_data, best_scenario)
        current_total = quote_data['total']
        iterations += 1

    return quote_data, iterations
    """)


# ==========================================================================
# MAIN
# ==========================================================================

def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description="Agent Skills Demo")
    parser.add_argument(
        "--demo",
        type=int,
        choices=[1, 2, 3, 4, 5, 6, 7],
        help="Demo number to run (1-7)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all demos"
    )

    args = parser.parse_args()

    demos = {
        1: ("List Available Skills", demo_1_list_skills),
        2: ("Intelligent Document Processing", demo_2_document_processing),
        3: ("Specification Intelligence", demo_3_specification_intelligence),
        4: ("Smart Quote Optimization", demo_4_quote_optimization),
        5: ("Project Intelligence Analysis", demo_5_project_intelligence),
        6: ("Complete Workflow", demo_6_complete_workflow),
        7: ("Advanced Skill Composition", demo_7_skill_composition)
    }

    if args.all:
        for num, (title, func) in demos.items():
            func()
            print("\n")
    elif args.demo:
        title, func = demos[args.demo]
        func()
    else:
        print("Available Demos:")
        print()
        for num, (title, _) in demos.items():
            print(f"  {num}. {title}")
        print()
        print("Run with: python demo_skills.py --demo [1-7]")
        print("Or run all: python demo_skills.py --all")


if __name__ == "__main__":
    main()
