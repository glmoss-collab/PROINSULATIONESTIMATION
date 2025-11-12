"""
Claude Workflow Enhancement Module
===================================

Extends the InsulationEstimationAgent with intelligent workflow orchestration,
multi-stage validation gates, recommendation engine, and cost optimization.

This module provides:
- WorkflowOrchestrator: Manages progression through estimation stages
- ValidationGate: Progressive validation at each stage
- RecommendationEngine: Contextual recommendations based on project data
- Quality metrics and audit trail tracking
"""

import json
import logging
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class WorkflowStageName(str, Enum):
    """Enumeration of workflow stages."""
    DISCOVERY = "discovery"
    DOCUMENT_ANALYSIS = "document_analysis"
    DATA_ENRICHMENT = "data_enrichment"
    CALCULATION = "calculation"
    QUOTE_GENERATION = "quote_generation"


class DataQualityLevel(str, Enum):
    """Data quality assessment levels."""
    CRITICAL = "critical"  # Stop progress
    WARNING = "warning"    # Proceed with caution
    INFO = "info"          # FYI
    OK = "ok"              # All clear


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    level: DataQualityLevel
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class WorkflowStageConfig:
    """Configuration for a workflow stage."""
    name: WorkflowStageName
    description: str
    tools_available: List[str] = field(default_factory=list)
    required_data: List[str] = field(default_factory=list)
    validation_checks: Dict[str, Callable] = field(default_factory=dict)
    order: int = 0


@dataclass
class WorkflowStage:
    """State of a workflow stage."""
    config: WorkflowStageConfig
    is_complete: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    validation_results: List[ValidationResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    cost: float = 0.0
    duration_seconds: float = 0.0
    timestamp_started: Optional[datetime] = None
    timestamp_completed: Optional[datetime] = None

    @property
    def all_validations_passed(self) -> bool:
        """Check if all validations passed."""
        return all(v.passed for v in self.validation_results)

    @property
    def has_critical_issues(self) -> bool:
        """Check if there are critical validation issues."""
        return any(
            v.level == DataQualityLevel.CRITICAL
            for v in self.validation_results
        )

    @property
    def quality_score(self) -> float:
        """Calculate overall quality score (0.0-1.0)."""
        if not self.validation_results:
            return 0.0
        passed = sum(1 for v in self.validation_results if v.passed)
        return passed / len(self.validation_results)


@dataclass
class AuditLogEntry:
    """Entry in the audit trail."""
    timestamp: datetime
    stage: WorkflowStageName
    action: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    cost: float
    duration_seconds: float
    user_feedback: Optional[str] = None
    error: Optional[str] = None


@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution."""
    total_cost: float = 0.0
    total_duration_seconds: float = 0.0
    stages_completed: int = 0
    total_validations: int = 0
    validations_passed: int = 0
    critical_issues: int = 0
    warnings: int = 0

    @property
    def validation_pass_rate(self) -> float:
        """Percentage of validations that passed."""
        if self.total_validations == 0:
            return 0.0
        return self.validations_passed / self.total_validations

    @property
    def overall_quality(self) -> float:
        """Overall quality score (0.0-1.0)."""
        return 1.0 - (self.critical_issues * 0.1) - (self.warnings * 0.02)


# ============================================================================
# VALIDATION GATE
# ============================================================================

class ValidationGate:
    """
    Validation checkpoint between workflow stages.

    Performs comprehensive validation to ensure data integrity before
    proceeding to the next stage.
    """

    def __init__(self, stage: WorkflowStage):
        self.stage = stage
        self.results: List[ValidationResult] = []

    def add_check(
        self,
        name: str,
        check_func: Callable[[Dict], tuple[bool, Optional[str]]],
        level: DataQualityLevel = DataQualityLevel.WARNING
    ) -> None:
        """Add a validation check."""
        # Store for later use
        if not hasattr(self, "_custom_checks"):
            self._custom_checks = {}
        self._custom_checks[name] = (check_func, level)

    def run_checks(self) -> List[ValidationResult]:
        """Run all validation checks for the stage."""
        results = []

        # Run built-in checks from stage config
        for check_name, check_func in self.stage.config.validation_checks.items():
            try:
                passed, message = check_func(self.stage.data)
                results.append(ValidationResult(
                    passed=passed,
                    level=DataQualityLevel.OK if passed else DataQualityLevel.WARNING,
                    message=message or f"Check '{check_name}' {'passed' if passed else 'failed'}",
                    field=check_name
                ))
            except Exception as e:
                results.append(ValidationResult(
                    passed=False,
                    level=DataQualityLevel.WARNING,
                    message=f"Error in check '{check_name}': {str(e)}",
                    field=check_name
                ))

        # Run custom checks if any
        if hasattr(self, "_custom_checks"):
            for check_name, (check_func, level) in self._custom_checks.items():
                try:
                    passed, message = check_func(self.stage.data)
                    results.append(ValidationResult(
                        passed=passed,
                        level=level if not passed else DataQualityLevel.OK,
                        message=message or f"Check '{check_name}' {'passed' if passed else 'failed'}",
                        field=check_name
                    ))
                except Exception as e:
                    results.append(ValidationResult(
                        passed=False,
                        level=DataQualityLevel.WARNING,
                        message=f"Error in check '{check_name}': {str(e)}",
                        field=check_name
                    ))

        self.results = results
        self.stage.validation_results = results
        return results

    def can_proceed(self) -> bool:
        """Check if we can proceed to next stage."""
        # Can proceed if no critical issues
        critical_issues = [r for r in self.results if r.level == DataQualityLevel.CRITICAL]
        return len(critical_issues) == 0

    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        critical = [r for r in self.results if r.level == DataQualityLevel.CRITICAL]
        warnings = [r for r in self.results if r.level == DataQualityLevel.WARNING]

        return {
            "can_proceed": self.can_proceed(),
            "passed": passed,
            "total": total,
            "pass_rate": passed / total if total > 0 else 0.0,
            "critical_issues": [asdict(r) for r in critical],
            "warnings": [asdict(r) for r in warnings]
        }


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

class RecommendationEngine:
    """
    Generates contextual recommendations based on project data and stage.

    Provides intelligent suggestions for materials, specifications, processes,
    and cost optimizations throughout the estimation workflow.
    """

    def __init__(self):
        self.recommendations_history: List[Dict] = []

    def get_discovery_recommendations(self, project_scope: Dict) -> List[str]:
        """Get recommendations for discovery stage."""
        recommendations = []

        # Check for missing project info
        required_fields = ["project_type", "building_type", "square_footage"]
        missing = [f for f in required_fields if f not in project_scope or not project_scope[f]]
        if missing:
            recommendations.append(
                f"Request the following information: {', '.join(missing)}"
            )

        # Check for system type specification
        if "system_type" not in project_scope or not project_scope.get("system_type"):
            recommendations.append(
                "Clarify which mechanical systems need insulation (HVAC, plumbing, refrigeration)"
            )

        # Recommend document gathering
        if "has_specifications" not in project_scope or not project_scope.get("has_specifications"):
            recommendations.append(
                "Request engineering specifications PDF (typically in Division 23 or 15)"
            )

        if "has_drawings" not in project_scope or not project_scope.get("has_drawings"):
            recommendations.append(
                "Request mechanical drawings with system measurements and scale"
            )

        return recommendations

    def get_analysis_recommendations(self, extracted_data: Dict) -> List[str]:
        """Get recommendations for document analysis stage."""
        recommendations = []

        # Check extraction quality
        if extracted_data.get("extraction_confidence", 0) < 0.85:
            recommendations.append(
                "Extraction confidence is below target. Review extracted data carefully for accuracy."
            )

        # Check for missing specifications
        specs = extracted_data.get("specifications", [])
        if not specs:
            recommendations.append(
                "No specifications were detected in the documents. Verify specs are complete."
            )

        # Check for measurement data
        measurements = extracted_data.get("measurements", [])
        if not measurements:
            recommendations.append(
                "No measurements were extracted from drawings. Verify drawing quality and scale."
            )

        # Check for ambiguous data
        ambiguities = extracted_data.get("ambiguities", [])
        if ambiguities:
            recommendations.append(
                f"Found {len(ambiguities)} ambiguous items that should be clarified"
            )

        return recommendations

    def get_enrichment_recommendations(self, validated_data: Dict) -> List[str]:
        """Get recommendations for data enrichment stage."""
        recommendations = []

        # Check specification coverage
        specs = validated_data.get("specifications", [])
        if len(specs) < 3:
            recommendations.append(
                "Specifications appear incomplete. Consider requesting additional spec details."
            )

        # Check for energy efficiency opportunities
        if validated_data.get("project_type") == "healthcare":
            recommendations.append(
                "Healthcare facilities benefit from higher R-values. Consider increasing insulation thickness."
            )

        # Check for redundant specifications
        if len(specs) > 1:
            duplicate_types = [s.get("system_type") for s in specs]
            if len(duplicate_types) != len(set(duplicate_types)):
                recommendations.append(
                    "Multiple specifications for same system type detected. Consolidate if appropriate."
                )

        # Material recommendations
        for spec in specs:
            if spec.get("location") == "outdoor" and spec.get("material") == "fiberglass":
                recommendations.append(
                    f"Outdoor duct requires weather protection. Ensure {spec.get('facing', 'FSK')} facing is specified."
                )

        return recommendations

    def get_optimization_recommendations(self, quote_data: Dict) -> List[str]:
        """Get recommendations for cost optimization stage."""
        recommendations = []

        total_price = quote_data.get("total_price", 0)
        material_cost = quote_data.get("material_total", 0)
        labor_cost = quote_data.get("labor_total", 0)

        # Check material vs labor ratio
        if total_price > 0:
            material_ratio = material_cost / total_price
            labor_ratio = labor_cost / total_price

            if material_ratio > 0.7:
                recommendations.append(
                    "Material costs are high (>70% of total). Consider material alternatives or bulk purchasing discounts."
                )

            if labor_ratio > 0.7:
                recommendations.append(
                    "Labor costs are high (>70% of total). Consider prefab options or crew optimization."
                )

        # Check for alternative opportunities
        alternatives = quote_data.get("alternatives", [])
        if alternatives:
            most_expensive = quote_data.get("total_price", 0)
            least_expensive = min(a.get("total_price", 0) for a in alternatives)
            savings = most_expensive - least_expensive

            if savings > 0:
                savings_pct = (savings / most_expensive) * 100
                recommendations.append(
                    f"Alternative option available: Save ${savings:,.2f} ({savings_pct:.1f}%) with {alternatives[0].get('description', 'alternative materials')}"
                )

        # Contingency check
        contingency = quote_data.get("contingency_pct", 0)
        if contingency < 10:
            recommendations.append(
                "Consider increasing contingency to 10-15% for unforeseen conditions"
            )

        # Markup check
        markup = quote_data.get("markup_pct", 0)
        if markup > 50:
            recommendations.append(
                "High markup detected. Consider whether market rates support this pricing."
            )

        return recommendations

    def get_cost_alternatives(
        self,
        current_spec: Dict,
        max_alternatives: int = 3
    ) -> List[Dict]:
        """
        Generate cost-effective alternatives to current specification.

        Args:
            current_spec: Current specification details
            max_alternatives: Maximum alternatives to generate

        Returns:
            List of alternative specifications with cost comparison
        """
        alternatives = []

        material = current_spec.get("material", "fiberglass")
        thickness = current_spec.get("thickness", 2.0)
        system_type = current_spec.get("system_type", "duct")

        # Generate alternatives based on material
        if material == "fiberglass":
            # Alternative 1: Reduce thickness
            if thickness > 1.0:
                alternatives.append({
                    "description": f"Reduce thickness to {thickness - 0.5}\"",
                    "material": material,
                    "thickness": thickness - 0.5,
                    "estimated_savings_pct": 15,
                    "performance_impact": "Slight reduction in R-value"
                })

            # Alternative 2: Use elastomeric
            alternatives.append({
                "description": "Switch to elastomeric foam (better outdoor performance)",
                "material": "elastomeric",
                "thickness": thickness - 0.5,
                "estimated_savings_pct": -5,  # Negative = more expensive
                "performance_impact": "Better durability and moisture resistance"
            })

        elif material == "elastomeric":
            # Alternative 1: Use fiberglass for indoor applications
            if system_type in ["duct", "pipe"]:
                alternatives.append({
                    "description": f"Use fiberglass instead of elastomeric for indoor installation",
                    "material": "fiberglass",
                    "thickness": thickness + 0.5,
                    "estimated_savings_pct": 20,
                    "performance_impact": "Adequate for indoor, lower cost"
                })

        # Add generic cost-reduction option
        alternatives.append({
            "description": "Consolidate material types (fewer SKUs)",
            "material": material,
            "thickness": thickness,
            "estimated_savings_pct": 8,
            "performance_impact": "Lower material costs from consolidation"
        })

        return alternatives[:max_alternatives]

    def get_markup_recommendations(self, cost_data: Dict) -> Dict[str, Any]:
        """
        Get recommended markup percentages based on project characteristics.

        Args:
            cost_data: Cost data including material and labor costs

        Returns:
            Dictionary with recommended markups for different factors
        """
        base_markup = 30  # 30% base

        # Adjust for project complexity
        if cost_data.get("project_complexity") == "high":
            base_markup += 5
        elif cost_data.get("project_complexity") == "low":
            base_markup -= 5

        # Adjust for project type
        project_type = cost_data.get("project_type", "commercial")
        type_adjustments = {
            "healthcare": 10,      # Higher risk/standards
            "industrial": 5,       # Moderate complexity
            "commercial": 0,       # Standard
            "residential": -5,     # Lower complexity
        }
        base_markup += type_adjustments.get(project_type, 0)

        return {
            "base_markup": float(max(20, base_markup)),
            "material_markup": float(max(20, base_markup - 5)),
            "labor_markup": float(max(25, base_markup)),
            "recommended_range": [float(base_markup - 5), float(base_markup + 10)]
        }


# ============================================================================
# WORKFLOW ORCHESTRATOR
# ============================================================================

class WorkflowOrchestrator:
    """
    Orchestrates multi-stage estimation workflow with validation gates.

    Manages progression through discovery, analysis, enrichment, calculation,
    and quote generation stages with built-in validation, recommendations,
    and quality assurance.
    """

    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.stages: List[WorkflowStage] = []
        self.current_stage_index: int = 0
        self.stage_history: List[Dict] = []
        self.audit_trail: List[AuditLogEntry] = []
        self.metrics = WorkflowMetrics()
        self.recommendations = RecommendationEngine()
        self.custom_validations: List[Callable] = []

        # Initialize default stages
        self._initialize_stages()

        logger.info("WorkflowOrchestrator initialized")

    def _initialize_stages(self) -> None:
        """Initialize default workflow stages."""
        stage_configs = [
            WorkflowStageConfig(
                name=WorkflowStageName.DISCOVERY,
                description="Understanding project scope and requirements",
                tools_available=["clarify_scope", "validate_requirements"],
                required_data=["project_type", "building_type", "system_type"],
                order=0
            ),
            WorkflowStageConfig(
                name=WorkflowStageName.DOCUMENT_ANALYSIS,
                description="Extracting and analyzing project documents",
                tools_available=[
                    "extract_project_info",
                    "extract_specifications",
                    "extract_measurements"
                ],
                required_data=["specifications", "measurements"],
                order=1
            ),
            WorkflowStageConfig(
                name=WorkflowStageName.DATA_ENRICHMENT,
                description="Validating and enriching extracted data",
                tools_available=[
                    "validate_specifications",
                    "cross_reference_data",
                    "normalize_data"
                ],
                required_data=["validated_specs", "validated_measurements"],
                order=2
            ),
            WorkflowStageConfig(
                name=WorkflowStageName.CALCULATION,
                description="Calculating quantities, labor, and pricing",
                tools_available=[
                    "calculate_quantities",
                    "calculate_labor",
                    "calculate_pricing",
                    "generate_alternatives"
                ],
                required_data=["material_quantities", "labor_hours", "pricing"],
                order=3
            ),
            WorkflowStageConfig(
                name=WorkflowStageName.QUOTE_GENERATION,
                description="Generating professional quote documents",
                tools_available=[
                    "generate_quote",
                    "generate_material_list",
                    "generate_summary",
                    "export_documents"
                ],
                required_data=["quote"],
                order=4
            ),
        ]

        for config in stage_configs:
            stage = WorkflowStage(config=config)
            self.stages.append(stage)

    def get_current_stage(self) -> WorkflowStage:
        """Get the current workflow stage."""
        if 0 <= self.current_stage_index < len(self.stages):
            return self.stages[self.current_stage_index]
        raise IndexError(f"Invalid stage index: {self.current_stage_index}")

    def get_stage_by_name(self, name: WorkflowStageName) -> Optional[WorkflowStage]:
        """Get a stage by name."""
        for stage in self.stages:
            if stage.config.name == name:
                return stage
        return None

    def advance_to_next_stage(self) -> bool:
        """
        Advance to next stage if current stage is complete and valid.

        Returns:
            True if successfully advanced, False otherwise
        """
        current = self.get_current_stage()

        # Validate current stage
        gate = ValidationGate(current)
        gate.run_checks()

        if not gate.can_proceed() and current.has_critical_issues:
            logger.warning(f"Cannot advance from {current.config.name}: critical validation issues")
            return False

        if not current.is_complete:
            logger.warning(f"Cannot advance from {current.config.name}: stage not complete")
            return False

        # Record in history
        self.stage_history.append({
            "stage": current.config.name.value,
            "timestamp": datetime.now().isoformat(),
            "completed": True,
            "quality_score": current.quality_score,
            "cost": current.cost
        })

        # Move to next stage
        self.current_stage_index += 1
        self.metrics.stages_completed += 1

        if self.current_stage_index < len(self.stages):
            next_stage = self.get_current_stage()
            next_stage.timestamp_started = datetime.now()
            logger.info(f"Advanced to stage: {next_stage.config.name.value}")
            return True
        else:
            logger.info("Workflow complete!")
            return False

    def validate_stage(self) -> Dict[str, Any]:
        """
        Validate current stage against criteria.

        Returns:
            Dictionary with validation results
        """
        current = self.get_current_stage()
        gate = ValidationGate(current)

        # Run built-in checks
        gate.run_checks()

        # Run custom validations
        for custom_check in self.custom_validations:
            try:
                passed, message = custom_check(current.data)
                gate.results.append(ValidationResult(
                    passed=passed,
                    level=DataQualityLevel.CRITICAL if not passed else DataQualityLevel.OK,
                    message=message or "Custom validation check"
                ))
            except Exception as e:
                logger.error(f"Error in custom validation: {e}")

        # Update stage with validation results
        current.validation_results = gate.results

        # Update metrics
        self.metrics.total_validations += len(gate.results)
        self.metrics.validations_passed += sum(1 for r in gate.results if r.passed)

        return gate.get_summary()

    def get_recommendations(self) -> List[str]:
        """Get recommendations for current stage."""
        current = self.get_current_stage()

        if current.config.name == WorkflowStageName.DISCOVERY:
            return self.recommendations.get_discovery_recommendations(current.data)
        elif current.config.name == WorkflowStageName.DOCUMENT_ANALYSIS:
            return self.recommendations.get_analysis_recommendations(current.data)
        elif current.config.name == WorkflowStageName.DATA_ENRICHMENT:
            return self.recommendations.get_enrichment_recommendations(current.data)
        elif current.config.name == WorkflowStageName.CALCULATION:
            return self.recommendations.get_optimization_recommendations(current.data)
        else:
            return []

    def update_stage_data(self, data: Dict[str, Any]) -> None:
        """Update current stage data."""
        current = self.get_current_stage()
        current.data.update(data)
        logger.debug(f"Updated {current.config.name.value} data: {list(data.keys())}")

    def complete_stage(self, data: Optional[Dict] = None, cost: float = 0.0) -> None:
        """Mark current stage as complete."""
        current = self.get_current_stage()

        if data:
            current.data.update(data)

        current.is_complete = True
        current.cost = cost
        current.timestamp_completed = datetime.now()

        if current.timestamp_started:
            duration = (current.timestamp_completed - current.timestamp_started).total_seconds()
            current.duration_seconds = duration

        self.metrics.total_cost += cost
        logger.info(f"Completed stage: {current.config.name.value} (cost: ${cost:.2f})")

    def add_custom_validation(self, validation_func: Callable) -> None:
        """Add custom validation function."""
        self.custom_validations.append(validation_func)
        logger.debug("Added custom validation function")

    def add_audit_entry(
        self,
        action: str,
        input_data: Dict,
        output_data: Dict,
        cost: float = 0.0,
        duration: float = 0.0,
        error: Optional[str] = None
    ) -> None:
        """Add entry to audit trail."""
        current = self.get_current_stage()
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            stage=current.config.name,
            action=action,
            input_data=input_data,
            output_data=output_data,
            cost=cost,
            duration_seconds=duration,
            error=error
        )
        self.audit_trail.append(entry)

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.current_stage_index >= len(self.stages)

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get overall workflow status."""
        return {
            "current_stage": self.get_current_stage().config.name.value if not self.is_complete() else "complete",
            "stage_number": self.current_stage_index + 1,
            "total_stages": len(self.stages),
            "progress_pct": ((self.current_stage_index) / len(self.stages)) * 100,
            "stages_completed": self.metrics.stages_completed,
            "total_cost": self.metrics.total_cost,
            "total_duration_seconds": self.metrics.total_duration_seconds,
            "validation_pass_rate": self.metrics.validation_pass_rate,
            "overall_quality": self.metrics.overall_quality
        }

    def get_audit_trail(self) -> List[Dict]:
        """Get audit trail as list of dictionaries."""
        return [
            {
                "timestamp": entry.timestamp.isoformat(),
                "stage": entry.stage.value,
                "action": entry.action,
                "cost": entry.cost,
                "duration_seconds": entry.duration_seconds,
                "error": entry.error
            }
            for entry in self.audit_trail
        ]

    def reset(self) -> None:
        """Reset workflow to initial state."""
        self.current_stage_index = 0
        self.stages = []
        self.stage_history = []
        self.audit_trail = []
        self.metrics = WorkflowMetrics()
        self._initialize_stages()
        logger.info("Workflow reset to initial state")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_workflow_orchestrator() -> WorkflowOrchestrator:
    """Factory function to create a new orchestrator."""
    return WorkflowOrchestrator()


def export_workflow_state(orchestrator: WorkflowOrchestrator) -> Dict[str, Any]:
    """Export workflow state as JSON-serializable dictionary."""
    return {
        "current_stage": orchestrator.get_current_stage().config.name.value,
        "stage_number": orchestrator.current_stage_index + 1,
        "total_stages": len(orchestrator.stages),
        "stages_completed": orchestrator.metrics.stages_completed,
        "metrics": {
            "total_cost": orchestrator.metrics.total_cost,
            "total_duration_seconds": orchestrator.metrics.total_duration_seconds,
            "validation_pass_rate": orchestrator.metrics.validation_pass_rate,
            "overall_quality": orchestrator.metrics.overall_quality
        },
        "stage_history": orchestrator.stage_history,
        "audit_trail": orchestrator.get_audit_trail(),
        "is_complete": orchestrator.is_complete()
    }
