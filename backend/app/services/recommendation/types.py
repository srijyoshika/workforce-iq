"""
WorkforceIQ Explainable Recommendation Types and Schemas.
Defines data structures for Reallocate, Train, Hire, and Reschedule recommendations.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RecommendationAction(str, Enum):
    """Categorization of workforce gap remediation actions."""
    REALLOCATE = "REALLOCATE"
    TRAIN = "TRAIN"
    HIRE = "HIRE"
    RESCHEDULE = "RESCHEDULE"


@dataclass(frozen=True)
class FeasibilityEvaluation:
    """Detailed feasibility evaluation of an action option."""
    is_feasible: bool
    reason: str
    estimated_days: int
    estimated_cost: float
    shortage_reduction_hours: float
    confidence_score: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecommendationItem:
    """
    Actionable and explainable workforce planning recommendation.
    Derived from hierarchical evaluation: Reallocate -> Train -> Hire -> Reschedule.
    """
    action: RecommendationAction
    gap_id: str
    project_id: str
    required_skill: str
    required_hours: float
    affected_employees: List[str]               # Employee IDs (empty for external hire)
    expected_cost: float                        # Estimated cost in USD
    estimated_time_to_resolve_days: int        # Resolution duration in days
    expected_shortage_reduction_hours: float    # Reduction in deficit hours
    deadline_feasibility: bool                  # Can this action resolve the gap before project start?
    confidence_score: float                     # 0.000 to 1.000 suitability score
    explanation: str                            # Transparent narrative explaining why chosen
    assumptions: List[str]                      # Documented business and operational assumptions
    rule_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "gap_id": self.gap_id,
            "project_id": self.project_id,
            "required_skill": self.required_skill,
            "required_hours": round(self.required_hours, 2),
            "affected_employees": self.affected_employees,
            "expected_cost": round(self.expected_cost, 2),
            "estimated_time_to_resolve_days": self.estimated_time_to_resolve_days,
            "expected_shortage_reduction_hours": round(self.expected_shortage_reduction_hours, 2),
            "deadline_feasibility": self.deadline_feasibility,
            "confidence_score": round(self.confidence_score, 3),
            "explanation": self.explanation,
            "assumptions": self.assumptions,
            "rule_version": self.rule_version,
        }


@dataclass(frozen=True)
class RecommendationPlan:
    """Portfolio-level compilation of actionable recommendations for identified gaps."""
    recommendations: List[RecommendationItem]
    total_expected_cost: float
    total_shortage_reduction_hours: float
    gaps_analyzed_count: int
    gaps_mitigated_count: int
    unmitigated_gap_ids: List[str]
    rule_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_expected_cost": round(self.total_expected_cost, 2),
            "total_shortage_reduction_hours": round(self.total_shortage_reduction_hours, 2),
            "gaps_analyzed_count": self.gaps_analyzed_count,
            "gaps_mitigated_count": self.gaps_mitigated_count,
            "unmitigated_gap_ids": self.unmitigated_gap_ids,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "rule_version": self.rule_version,
        }

