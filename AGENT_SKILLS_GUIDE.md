# Agent Skills Guide - Professional HVAC Insulation Estimation

## Table of Contents

1. [Overview](#overview)
2. [What Are Agent Skills?](#what-are-agent-skills)
3. [Available Skills](#available-skills)
4. [Quick Start](#quick-start)
5. [Skill Descriptions](#skill-descriptions)
6. [Usage Examples](#usage-examples)
7. [Advanced Workflows](#advanced-workflows)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)

---

## Overview

The Agent Skills Framework provides **high-level, composable capabilities** for professional HVAC insulation estimation. Unlike basic tools that perform single operations, skills combine multiple tools, domain expertise, and intelligent decision-making to accomplish complex workflows.

### Key Benefits

- **🧠 Intelligent**: Skills make smart decisions based on context
- **🔄 Composable**: Combine skills to create advanced workflows
- **📊 Optimized**: Built-in cost and performance optimization
- **✅ Validated**: Automatic validation and quality assurance
- **📈 Strategic**: Provides business intelligence and recommendations

### Skills vs Tools

| Aspect | Tools | Skills |
|--------|-------|--------|
| **Level** | Low-level operations | High-level capabilities |
| **Scope** | Single task | Multi-step workflows |
| **Intelligence** | Basic execution | Context-aware decisions |
| **Example** | Extract text from PDF | Intelligently process document with auto-detection and optimization |

---

## What Are Agent Skills?

Agent Skills are **intelligent, composable capabilities** that combine:

1. **Multiple Tools**: Orchestrate several tools in sequence
2. **Domain Expertise**: Built-in HVAC/insulation industry knowledge
3. **Decision Making**: Intelligent choices based on context
4. **Validation**: Automatic quality assurance
5. **Optimization**: Cost and performance improvements
6. **Recommendations**: Strategic insights and alternatives

### Skill Categories

The framework organizes skills into 8 categories:

```python
class SkillCategory(Enum):
    DOCUMENT_ANALYSIS = "document_analysis"              # PDF processing
    SPECIFICATION_INTELLIGENCE = "specification_intelligence"  # Spec analysis
    MEASUREMENT_EXTRACTION = "measurement_extraction"    # Drawing analysis
    COST_OPTIMIZATION = "cost_optimization"              # Cost reduction
    QUALITY_ASSURANCE = "quality_assurance"              # Validation
    RECOMMENDATION_ENGINE = "recommendation_engine"      # Suggestions
    QUOTE_GENERATION = "quote_generation"                # Quote creation
    PROJECT_INTELLIGENCE = "project_intelligence"        # Strategic analysis
```

---

## Available Skills

### 1. Intelligent Document Processor

**Category:** Document Analysis
**Complexity:** Complex
**API Required:** Yes
**Cacheable:** Yes

**What it does:**
- Auto-detects document type (spec, drawing, both)
- Intelligently selects pages to analyze (saves 85% API cost)
- Extracts relevant information based on document type
- Validates extraction quality
- Provides confidence scores

**Use when:**
- Processing construction documents
- Analyzing PDFs with unknown content
- Need to minimize API costs
- Want automatic validation

**Key Features:**
- 🎯 Auto document type detection
- 💰 85% cost savings through smart page selection
- ✅ Automatic validation
- 📊 Confidence scoring

---

### 2. Specification Intelligence Engine

**Category:** Specification Intelligence
**Complexity:** Complex
**API Required:** No
**Cacheable:** Yes

**What it does:**
- Validates specs against industry standards
- Identifies missing or conflicting requirements
- Recommends optimal specifications
- Suggests cost-saving alternatives
- Checks code compliance
- Identifies specification gaps

**Use when:**
- Reviewing extracted specifications
- Need recommendations for project type
- Want to identify cost savings
- Checking code compliance

**Key Features:**
- 📋 Industry standards validation
- 💡 Intelligent recommendations
- 💰 Cost-saving alternatives
- ✓ Compliance checking
- 🔍 Gap analysis

---

### 3. Smart Quote Optimizer

**Category:** Cost Optimization
**Complexity:** Complex
**API Required:** No
**Cacheable:** No

**What it does:**
- Analyzes quotes for cost reduction opportunities
- Suggests material substitutions
- Identifies volume discount opportunities
- Recommends labor efficiency improvements
- Provides multiple optimization scenarios
- Performs risk analysis

**Use when:**
- Want to reduce project costs
- Need to provide alternatives to clients
- Analyzing quote competitiveness
- Looking for efficiency improvements

**Key Features:**
- 💰 Multiple optimization scenarios
- 📊 Detailed savings breakdown
- ⚖️ Risk analysis
- 🎯 Material substitution recommendations
- 📈 Volume discount identification

**Optimization Goals:**
- **Maximum Savings**: Aggressive cost reduction (15-35% savings)
- **Balanced**: Moderate savings with maintained quality (10-20% savings)
- **Premium**: Minimal changes, maximum quality

---

### 4. Project Intelligence Analyzer

**Category:** Project Intelligence
**Complexity:** Complex
**API Required:** No
**Cacheable:** Yes

**What it does:**
- Analyzes project complexity
- Estimates timeline and resource needs
- Assesses risks
- Provides strategic recommendations
- Benchmarks against similar projects
- Identifies potential challenges

**Use when:**
- Pre-qualifying projects
- Planning resource allocation
- Assessing project viability
- Need strategic insights

**Key Features:**
- 🎯 Complexity scoring
- ⏱️ Timeline estimation
- ⚠️ Risk assessment
- 💡 Strategic recommendations
- 📊 Project benchmarking

---

## Quick Start

### Installation

```bash
# Skills are included in the main installation
pip install -r requirements.txt

# Verify skills are available
python -c "from agent_skills import get_available_skills; print(get_available_skills())"
```

### Basic Usage

```python
from agent_skills import create_skill_registry

# Create skill registry
registry = create_skill_registry()

# List available skills
skills = registry.list_skills()
for skill in skills:
    print(f"{skill['name']}: {skill['description']}")

# Execute a skill
results = registry.execute_skill(
    'intelligent_document_processor',
    pdf_path='specification.pdf'
)

print(f"Confidence: {results['confidence']:.2%}")
print(f"Specifications found: {len(results['specifications'])}")
```

### Running Demos

```bash
# List all demos
python demo_skills.py

# Run specific demo
python demo_skills.py --demo 1  # List skills
python demo_skills.py --demo 2  # Document processing
python demo_skills.py --demo 3  # Specification intelligence
python demo_skills.py --demo 4  # Quote optimization
python demo_skills.py --demo 5  # Project intelligence

# Run all demos
python demo_skills.py --all
```

---

## Skill Descriptions

### Intelligent Document Processor

#### Input Parameters

```python
{
    "pdf_path": str,                    # Required: Path to PDF
    "document_type_hint": Optional[str], # Optional: "spec", "drawing", "both"
    "priority_pages": Optional[List[int]] # Optional: Pages to prioritize
}
```

#### Output Structure

```python
{
    "document_type": str,              # Detected type
    "pages_analyzed": List[int],       # Pages that were analyzed
    "project_info": Dict,              # Extracted project metadata
    "specifications": List[Dict],      # Extracted specs
    "measurements": List[Dict],        # Extracted measurements
    "warnings": List[str],             # Any warnings
    "confidence": float,               # Overall confidence (0-1)
    "validation": Dict                 # Validation results
}
```

#### Usage Example

```python
from agent_skills import IntelligentDocumentProcessor

processor = IntelligentDocumentProcessor()

# Process with auto-detection
results = processor.execute(
    pdf_path="project_spec.pdf"
)

# Process with hints for faster execution
results = processor.execute(
    pdf_path="mechanical_drawings.pdf",
    document_type_hint="drawing",
    priority_pages=[1, 2, 5, 6]  # Specific sheets
)

# Check results
if results['confidence'] > 0.8:
    print(f"High confidence extraction!")
    print(f"Found {len(results['specifications'])} specifications")
else:
    print(f"Low confidence - review warnings:")
    for warning in results['warnings']:
        print(f"  - {warning}")
```

---

### Specification Intelligence Engine

#### Input Parameters

```python
{
    "specifications": List[Dict],        # Required: List of specs
    "project_type": Optional[str],       # Optional: Project type
    "climate_zone": Optional[str],       # Optional: Climate zone
    "budget_target": Optional[float]     # Optional: Budget limit
}
```

#### Output Structure

```python
{
    "summary": Dict,                    # Summary statistics
    "validation": Dict,                 # Validation results
    "recommendations": List[Dict],      # Intelligent recommendations
    "alternatives": List[Dict],         # Cost-saving alternatives
    "compliance": Dict,                 # Code compliance check
    "gaps": List[Dict]                  # Identified gaps
}
```

#### Usage Example

```python
from agent_skills import SpecificationIntelligenceEngine

engine = SpecificationIntelligenceEngine()

# Analyze specifications
results = engine.execute(
    specifications=extracted_specs,
    project_type="healthcare",
    climate_zone="hot_humid",
    budget_target=100000
)

# Review validation
if not results['validation']['is_valid']:
    print("Validation errors found:")
    for error in results['validation']['errors']:
        print(f"  ❌ {error}")

# Review recommendations
print("\nRecommendations:")
for rec in results['recommendations']:
    print(f"  💡 [{rec['priority']}] {rec['description']}")
    print(f"     Rationale: {rec['rationale']}")

# Review alternatives
print("\nCost-Saving Alternatives:")
for alt in results['alternatives']:
    print(f"  💰 {alt['cost_impact']}")
    print(f"     {alt['notes']}")
```

---

### Smart Quote Optimizer

#### Input Parameters

```python
{
    "quote_data": Dict,                 # Required: Quote to optimize
    "optimization_goal": str,           # "maximum_savings", "balanced", "premium"
    "constraints": Optional[Dict]        # Optional: Constraints
}
```

#### Output Structure

```python
{
    "original_total": float,            # Original quote total
    "optimized_scenarios": List[Dict],  # Optimization scenarios
    "savings_opportunities": List[Dict], # Specific opportunities
    "risk_analysis": Dict,              # Risk assessment
    "recommendations": List[Dict]       # Recommendations
}
```

#### Usage Example

```python
from agent_skills import SmartQuoteOptimizer

optimizer = SmartQuoteOptimizer()

# Optimize for maximum savings
results = optimizer.execute(
    quote_data=current_quote,
    optimization_goal="maximum_savings"
)

print(f"Original Total: ${results['original_total']:,.2f}")

# Review scenarios
for scenario in results['optimized_scenarios']:
    print(f"\n{scenario['name']}:")
    print(f"  Strategy: {scenario['strategy']}")
    print(f"  Savings: ${scenario['estimated_savings']:,.2f} ({scenario['savings_percentage']:.1f}%)")
    print(f"  New Total: ${scenario['estimated_total']:,.2f}")
    print(f"  Quality Impact: {scenario['quality_impact']}")

# Check risks
risk_level = results['risk_analysis']['overall_risk_level']
if risk_level == 'high':
    print("\n⚠️  High risk scenario - review carefully")
    for risk in results['risk_analysis']['identified_risks']:
        print(f"  - {risk['risk']} (Impact: {risk['impact']})")
```

---

### Project Intelligence Analyzer

#### Input Parameters

```python
{
    "project_data": Dict,               # Required: Complete project data
    "historical_projects": Optional[List[Dict]]  # Optional: Historical data
}
```

#### Output Structure

```python
{
    "complexity_analysis": Dict,        # Complexity assessment
    "timeline_estimate": Dict,          # Timeline estimation
    "risk_assessment": Dict,            # Risk analysis
    "recommendations": List[Dict],      # Strategic recommendations
    "benchmarking": Dict                # Comparison to historical
}
```

#### Usage Example

```python
from agent_skills import ProjectIntelligenceAnalyzer

analyzer = ProjectIntelligenceAnalyzer()

# Analyze project
project_data = {
    "project_info": project_info,
    "specifications": specifications,
    "measurements": measurements,
    "quote": quote
}

results = analyzer.execute(project_data=project_data)

# Review complexity
complexity = results['complexity_analysis']
print(f"Complexity Level: {complexity['complexity_level']}")
print(f"Score: {complexity['complexity_score']}/12")
print(f"Description: {complexity['description']}")

# Review timeline
timeline = results['timeline_estimate']
print(f"\nEstimated Duration: {timeline['estimated_duration_weeks']} weeks")
print(f"Recommended Crew Size: {timeline['crew_size_recommended']}")

# Review risks
risk_assessment = results['risk_assessment']
print(f"\nOverall Risk: {risk_assessment['overall_risk_level']}")
for risk in risk_assessment['identified_risks']:
    print(f"  ⚠️  {risk['risk']}")
    print(f"      Mitigation: {risk['mitigation']}")
```

---

## Usage Examples

### Example 1: Complete Document-to-Quote Workflow

```python
from agent_skills import create_skill_registry

def complete_estimation_workflow(pdf_path):
    """Complete workflow from document to optimized quote."""

    registry = create_skill_registry()

    # Step 1: Process document intelligently
    print("Step 1: Processing document...")
    doc_results = registry.execute_skill(
        'intelligent_document_processor',
        pdf_path=pdf_path
    )

    if doc_results['confidence'] < 0.7:
        print("⚠️  Low confidence - manual review recommended")

    # Step 2: Analyze specifications
    print("Step 2: Analyzing specifications...")
    spec_analysis = registry.execute_skill(
        'specification_intelligence_engine',
        specifications=doc_results['specifications'],
        project_type=doc_results['project_info'].get('project_type')
    )

    # Apply recommendations
    if spec_analysis['recommendations']:
        print(f"Found {len(spec_analysis['recommendations'])} recommendations")

    # Step 3: Generate quote (using existing tools)
    print("Step 3: Generating quote...")
    # ... use existing quote generation tools ...
    quote = generate_quote(doc_results)  # Your existing function

    # Step 4: Optimize quote
    print("Step 4: Optimizing quote...")
    optimization = registry.execute_skill(
        'smart_quote_optimizer',
        quote_data=quote,
        optimization_goal='balanced'
    )

    # Step 5: Project intelligence
    print("Step 5: Analyzing project intelligence...")
    intelligence = registry.execute_skill(
        'project_intelligence_analyzer',
        project_data={
            'project_info': doc_results['project_info'],
            'specifications': doc_results['specifications'],
            'measurements': doc_results['measurements'],
            'quote': quote
        }
    )

    # Return comprehensive results
    return {
        'document_analysis': doc_results,
        'specification_analysis': spec_analysis,
        'original_quote': quote,
        'optimization': optimization,
        'intelligence': intelligence
    }

# Use it
results = complete_estimation_workflow('project_spec.pdf')

# Present results
print("\n" + "="*80)
print("ESTIMATION COMPLETE")
print("="*80)
print(f"\nProject: {results['document_analysis']['project_info']['project_name']}")
print(f"Complexity: {results['intelligence']['complexity_analysis']['complexity_level']}")
print(f"\nOriginal Quote: ${results['original_quote']['total']:,.2f}")

best_scenario = results['optimization']['optimized_scenarios'][0]
print(f"Optimized Quote: ${best_scenario['estimated_total']:,.2f}")
print(f"Potential Savings: ${best_scenario['estimated_savings']:,.2f} ({best_scenario['savings_percentage']:.1f}%)")

print(f"\nEstimated Timeline: {results['intelligence']['timeline_estimate']['estimated_duration_weeks']} weeks")
print(f"Risk Level: {results['intelligence']['risk_assessment']['overall_risk_level']}")
```

### Example 2: Quick Project Pre-Qualification

```python
def pre_qualify_project(pdf_path, min_budget, max_budget):
    """Quickly determine if project is within scope."""

    registry = create_skill_registry()

    # Quick scan (just cover pages)
    doc_scan = registry.execute_skill(
        'intelligent_document_processor',
        pdf_path=pdf_path,
        priority_pages=[1, 2, 3]
    )

    # Assess complexity
    quick_data = {
        'project_info': doc_scan['project_info'],
        'specifications': doc_scan['specifications'],
        'measurements': [],  # Don't need full measurements yet
        'quote': {'total': 0, 'labor_hours': 0}
    }

    intelligence = registry.execute_skill(
        'project_intelligence_analyzer',
        project_data=quick_data
    )

    complexity = intelligence['complexity_analysis']['complexity_level']

    # Rough estimate based on complexity
    rough_estimates = {
        'low': (min_budget * 0.5, min_budget * 1.5),
        'medium': (min_budget * 1.0, max_budget * 0.7),
        'high': (max_budget * 0.7, max_budget * 2.0)
    }

    est_min, est_max = rough_estimates.get(complexity, (0, float('inf')))

    qualified = min_budget <= est_max and max_budget >= est_min

    return {
        'qualified': qualified,
        'reason': f"Complexity: {complexity}, Est range: ${est_min:,.0f}-${est_max:,.0f}",
        'complexity': complexity,
        'project_name': doc_scan['project_info'].get('project_name', 'Unknown'),
        'confidence': doc_scan['confidence']
    }

# Use it
result = pre_qualify_project('rfp_documents.pdf', 50000, 150000)

if result['qualified']:
    print(f"✅ Project qualified: {result['project_name']}")
    print(f"   Complexity: {result['complexity']}")
    print(f"   Reason: {result['reason']}")
else:
    print(f"❌ Project not qualified: {result['project_name']}")
    print(f"   Reason: {result['reason']}")
```

### Example 3: Continuous Optimization

```python
def optimize_to_target(quote_data, target_savings_percentage, max_risk='medium'):
    """Iteratively optimize quote to reach target savings."""

    registry = create_skill_registry()
    original_total = quote_data['total']
    target_total = original_total * (1 - target_savings_percentage / 100)

    print(f"Original: ${original_total:,.2f}")
    print(f"Target: ${target_total:,.2f} ({target_savings_percentage}% savings)")

    current_quote = quote_data.copy()
    iterations = 0
    max_iterations = 3

    while current_quote['total'] > target_total and iterations < max_iterations:
        iterations += 1
        print(f"\nIteration {iterations}:")

        # Optimize
        result = registry.execute_skill(
            'smart_quote_optimizer',
            quote_data=current_quote,
            optimization_goal='maximum_savings'
        )

        # Check risk level
        risk_level = result['risk_analysis']['overall_risk_level']
        print(f"  Risk level: {risk_level}")

        if risk_level == 'high' and max_risk != 'high':
            print("  ⚠️  Risk too high - stopping optimization")
            break

        # Apply best scenario
        best_scenario = result['optimized_scenarios'][0]
        current_quote['total'] = best_scenario['estimated_total']

        print(f"  New total: ${current_quote['total']:,.2f}")
        print(f"  Savings so far: ${original_total - current_quote['total']:,.2f}")

        # Check if we reached target
        if current_quote['total'] <= target_total:
            print(f"\n✅ Target reached!")
            break

    final_savings = original_total - current_quote['total']
    final_pct = (final_savings / original_total * 100) if original_total > 0 else 0

    return {
        'original_total': original_total,
        'final_total': current_quote['total'],
        'savings': final_savings,
        'savings_percentage': final_pct,
        'iterations': iterations,
        'target_reached': current_quote['total'] <= target_total
    }

# Use it
result = optimize_to_target(quote, target_savings_percentage=20, max_risk='medium')

print(f"\n{'='*60}")
print(f"Final Results:")
print(f"  Original: ${result['original_total']:,.2f}")
print(f"  Final: ${result['final_total']:,.2f}")
print(f"  Savings: ${result['savings']:,.2f} ({result['savings_percentage']:.1f}%)")
print(f"  Iterations: {result['iterations']}")
print(f"  Target Reached: {'Yes' if result['target_reached'] else 'No'}")
```

---

## Advanced Workflows

### Multi-Document Analysis

```python
def analyze_complete_project(spec_pdf, drawing_pdf, pricebook_path):
    """Analyze complete project with multiple documents."""

    registry = create_skill_registry()

    # Process specification document
    spec_results = registry.execute_skill(
        'intelligent_document_processor',
        pdf_path=spec_pdf,
        document_type_hint='spec'
    )

    # Process drawing document
    drawing_results = registry.execute_skill(
        'intelligent_document_processor',
        pdf_path=drawing_pdf,
        document_type_hint='drawing'
    )

    # Merge results
    merged_specs = spec_results['specifications'] + drawing_results.get('specifications', [])
    merged_measurements = spec_results.get('measurements', []) + drawing_results['measurements']

    # Analyze combined specifications
    spec_analysis = registry.execute_skill(
        'specification_intelligence_engine',
        specifications=merged_specs
    )

    # Check for conflicts
    if spec_analysis['validation']['warnings']:
        print("⚠️  Conflicts between spec and drawing:")
        for warning in spec_analysis['validation']['warnings']:
            print(f"  - {warning}")

    return {
        'specifications': merged_specs,
        'measurements': merged_measurements,
        'analysis': spec_analysis
    }
```

### Automated Bid Generation

```python
def generate_competitive_bid(project_docs, competitor_prices):
    """Generate competitive bid automatically."""

    registry = create_skill_registry()

    # Process documents
    results = complete_estimation_workflow(project_docs)

    # Get original quote
    original_quote = results['original_quote']

    # Check competitor prices
    avg_competitor = sum(competitor_prices) / len(competitor_prices)
    target_price = avg_competitor * 0.95  # Beat average by 5%

    # Optimize to target
    if original_quote['total'] > target_price:
        target_savings_pct = ((original_quote['total'] - target_price) / original_quote['total'] * 100)

        optimization = optimize_to_target(
            original_quote,
            target_savings_percentage=target_savings_pct,
            max_risk='medium'
        )

        if optimization['target_reached']:
            print(f"✅ Competitive bid achieved: ${optimization['final_total']:,.2f}")
            return optimization['final_total']
        else:
            print(f"⚠️  Could not reach target price without high risk")
            print(f"   Best price: ${optimization['final_total']:,.2f}")
            return optimization['final_total']
    else:
        print(f"✅ Already competitive: ${original_quote['total']:,.2f}")
        return original_quote['total']
```

---

## Best Practices

### 1. Use the Right Skill for the Job

```python
# ✅ Good: Use specialized skills
results = registry.execute_skill('intelligent_document_processor', pdf_path='spec.pdf')

# ❌ Bad: Use low-level tools when skill exists
# Manually calling extract_project_info, extract_specifications, etc.
```

### 2. Cache Expensive Operations

```python
# ✅ Good: Skills are cacheable by default
results = processor.execute(pdf_path='large_document.pdf')  # Cached
results = processor.execute(pdf_path='large_document.pdf')  # Uses cache

# Note: Skills automatically handle caching based on input parameters
```

### 3. Handle Low Confidence Results

```python
results = processor.execute(pdf_path='document.pdf')

if results['confidence'] < 0.7:
    # Low confidence - need manual review
    print("⚠️  Low confidence extraction")
    print("Please review and correct:")

    for spec in results['specifications']:
        if spec.get('confidence', 1.0) < 0.7:
            print(f"  - {spec['system_type']}: {spec['spec_text']}")
```

### 4. Apply Recommendations Selectively

```python
# Get recommendations
spec_analysis = engine.execute(specifications=specs)

# Filter by priority
high_priority = [r for r in spec_analysis['recommendations'] if r['priority'] == 'high']

# Apply high priority automatically
for rec in high_priority:
    apply_recommendation(rec)

# Ask user for medium priority
medium_priority = [r for r in spec_analysis['recommendations'] if r['priority'] == 'medium']
for rec in medium_priority:
    if ask_user(f"Apply: {rec['description']}?"):
        apply_recommendation(rec)
```

### 5. Validate Optimization Results

```python
optimization = optimizer.execute(quote_data=quote)

# Always check risk analysis
if optimization['risk_analysis']['overall_risk_level'] == 'high':
    print("⚠️  High risk optimization - review carefully")

    # Show specific risks
    for risk in optimization['risk_analysis']['identified_risks']:
        print(f"  Risk: {risk['risk']}")
        print(f"  Impact: {risk['impact']}")
        print(f"  Mitigation: Get client approval first")
```

### 6. Combine Skills for Power

```python
def intelligent_workflow(pdf_path):
    """Combine multiple skills intelligently."""

    registry = create_skill_registry()

    # Start with document processing
    doc_results = registry.execute_skill(
        'intelligent_document_processor',
        pdf_path=pdf_path
    )

    # Check if we need more data
    if not doc_results['specifications']:
        print("⚠️  No specs found - may need additional documents")

    if not doc_results['measurements']:
        print("⚠️  No measurements found - may need drawing PDF")

    # If we have enough data, continue
    if doc_results['specifications'] and doc_results['measurements']:
        # Analyze specifications
        spec_analysis = registry.execute_skill(
            'specification_intelligence_engine',
            specifications=doc_results['specifications']
        )

        # Generate quote
        quote = generate_quote(doc_results)

        # Optimize quote
        optimization = registry.execute_skill(
            'smart_quote_optimizer',
            quote_data=quote
        )

        # Analyze project
        intelligence = registry.execute_skill(
            'project_intelligence_analyzer',
            project_data={
                'project_info': doc_results['project_info'],
                'specifications': doc_results['specifications'],
                'quote': quote
            }
        )

        return {
            'complete': True,
            'doc_results': doc_results,
            'spec_analysis': spec_analysis,
            'quote': quote,
            'optimization': optimization,
            'intelligence': intelligence
        }
    else:
        return {
            'complete': False,
            'doc_results': doc_results,
            'needs': {
                'specifications': not doc_results['specifications'],
                'measurements': not doc_results['measurements']
            }
        }
```

---

## API Reference

### SkillRegistry

```python
class SkillRegistry:
    """Central registry for all agent skills."""

    def get_skill(self, skill_name: str)
        """Get skill instance by name."""

    def list_skills(self) -> List[Dict[str, Any]]
        """List all available skills with metadata."""

    def execute_skill(self, skill_name: str, **kwargs) -> Dict[str, Any]
        """Execute a skill by name with parameters."""
```

### Convenience Functions

```python
def create_skill_registry() -> SkillRegistry
    """Create and return skill registry."""

def get_available_skills() -> List[Dict[str, Any]]
    """Get list of all available skills."""
```

---

## Troubleshooting

### Common Issues

**Issue: Skill not found**
```python
# Error: ValueError: Skill not found: my_skill

# Solution: Check available skills
skills = registry.list_skills()
print([s['name'] for s in skills])
```

**Issue: Low confidence results**
```python
# Problem: results['confidence'] < 0.5

# Solutions:
# 1. Provide document type hint
results = processor.execute(pdf_path=path, document_type_hint='spec')

# 2. Specify priority pages
results = processor.execute(pdf_path=path, priority_pages=[1, 2, 5, 6])

# 3. Try different document
# - Some PDFs are scan quality issues
# - Some are image-based (need OCR)
```

**Issue: Optimization too aggressive**
```python
# Problem: optimization['risk_analysis']['overall_risk_level'] == 'high'

# Solution: Use balanced goal instead
optimization = optimizer.execute(
    quote_data=quote,
    optimization_goal='balanced'  # Instead of 'maximum_savings'
)
```

---

## Next Steps

### Learn More

- **[CLAUDE_AGENTS_ARCHITECTURE.md](CLAUDE_AGENTS_ARCHITECTURE.md)** - System architecture
- **[AGENT_SETUP_GUIDE.md](AGENT_SETUP_GUIDE.md)** - Setup and configuration
- **[PRODUCTION_ENHANCEMENTS.md](PRODUCTION_ENHANCEMENTS.md)** - Advanced optimizations

### Try It Out

```bash
# Run demos to see skills in action
python demo_skills.py --all

# Try complete workflow
python demo_skills.py --demo 6
```

### Extend Skills

See the skills source code in `agent_skills.py` for examples of how to:
- Create custom skills
- Combine existing tools
- Add domain expertise
- Implement validation logic

---

**Version:** 2.0
**Last Updated:** 2025-11-21
**Maintained By:** Professional Insulation Estimation System Team
