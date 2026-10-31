"""
WorkforceIQ Optimization Data Types and Metrics Schemas.
Defines data structures for OR-Tools mathematical programming and baseline comparisons.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class OptimizationStatus(str, Enum):
    """Solver termination status."""
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    MODEL_INVALID = "MODEL_INVALID"


@dataclass(frozen=True)
class AllocationDecision:
    """Individual assignment decision from the optimization solver."""
    demand_id: str
    project_id: str
    employee_id: Optional[str]
    employee_name: Optional[str]
    action_type: str                   # "INTERNAL_ALLOCATION", "TRAINING_AND_ALLOCATE", "EXTERNAL_HIRE", "UNFILLED"
    allocated_hours: float
    skill_mismatch_penalty: float
    decision_cost: float
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InfeasibilityDiagnosis:
    """Explainable diagnostic report when complete feasible allocation cannot be achieved."""
    is_fully_feasible: bool
    unfilled_demand_count: int
    unfilled_hours: float
    infeasibility_reasons: List[str]
    violated_constraints: List[str]
    mitigation_suggestions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BenchmarkComparison:
    """Quantitative comparison between OR-Tools optimizer and Greedy baseline allocator."""
    solver_name: str
    status: str
    demand_fulfillment_percentage: float
    total_cost: float
    skill_mismatch_score: float
    constraint_violations_count: int
    solve_duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solver_name": self.solver_name,
            "status": self.status,
            "demand_fulfillment_percentage": round(self.demand_fulfillment_percentage, 2),
            "total_cost": round(self.total_cost, 2),
            "skill_mismatch_score": round(self.skill_mismatch_score, 2),
            "constraint_violations_count": self.constraint_violations_count,
            "solve_duration_ms": round(self.solve_duration_ms, 2),
        }


@dataclass(frozen=True)
class OptimizationResult:
    """Master optimization solution containing decisions, metrics, and benchmarks."""
    status: OptimizationStatus
    solver_name: str
    demand_fulfillment_percentage: float
    total_allocated_hours: float
    total_unfilled_hours: float
    total_cost: float
    skill_mismatch_score: float
    constraint_violations_count: int
    allocations: List[AllocationDecision]
    infeasibility_diagnosis: InfeasibilityDiagnosis
    baseline_benchmark: Optional[BenchmarkComparison] = None
    solve_duration_ms: float = 0.0
    rule_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "solver_name": self.solver_name,
            "demand_fulfillment_percentage": round(self.demand_fulfillment_percentage, 2),
            "total_allocated_hours": round(self.total_allocated_hours, 2),
            "total_unfilled_hours": round(self.total_unfilled_hours, 2),
            "total_cost": round(self.total_cost, 2),
            "skill_mismatch_score": round(self.skill_mismatch_score, 2),
            "constraint_violations_count": self.constraint_violations_count,
            "solve_duration_ms": round(self.solve_duration_ms, 2),
            "allocations": [a.to_dict() for a in self.allocations],
            "infeasibility_diagnosis": self.infeasibility_diagnosis.to_dict(),
            "baseline_benchmark": self.baseline_benchmark.to_dict() if self.baseline_benchmark else None,
            "rule_version": self.rule_version,
        }

