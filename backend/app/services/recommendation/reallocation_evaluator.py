"""
Internal Employee Reallocation Evaluator.

Assesses feasibility of shifting qualified, available internal employees to open project demands.
Strictly guards against:
1. Stale skills (skills older than 730 days without re-verification).
2. Insufficient available capacity.
3. Capacity double-counting across concurrent projects.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Tuple
from app.services.recommendation.types import FeasibilityEvaluation, RecommendationAction, RecommendationItem
from app.services.skill_matching_service import CandidateMatch


class ReallocationEvaluator:
    """Evaluates candidate suitability for internal cross-project reallocation."""

    @classmethod
    def evaluate(
        cls,
        candidates: Sequence[CandidateMatch],
        committed_capacities: Dict[str, float],
        required_hours: float,
        days_to_deadline: int,
        gap_id: str,
        project_id: str,
        required_skill: str,
    ) -> Optional[RecommendationItem]:
        """
        Evaluate candidate pool for reallocation.
        Selects candidate with verified, current qualification and sufficient uncommitted capacity.
        Updates `committed_capacities` to prevent double-counting across subsequent recommendations.
        """
        best_candidate: Optional[CandidateMatch] = None
        usable_hours = 0.0

        for cand in candidates:
            # 1. Stale Skill Guard: Must be current and certified
            if cand.is_stale or not cand.is_fully_qualified or cand.effective_certified_proficiency < cand.required_proficiency:
                continue

            # 2. Capacity Guard: Net remaining hours minus hours already committed in this planning run
            already_committed = committed_capacities.get(cand.employee_id, 0.0)
            net_free_hours = max(0.0, cand.remaining_capacity_hours - already_committed)

            # Minimum viable allocation is at least 10 hours/week
            if net_free_hours >= 10.0:
                best_candidate = cand
                usable_hours = min(net_free_hours, required_hours)
                break

        if not best_candidate:
            return None

        # Reallocation lead time (3 to 5 business days for project handoff)
        resolution_days = 4
        is_deadline_feasible = resolution_days <= days_to_deadline

        # Reallocation administrative and onboarding cost estimate
        expected_cost = 500.0

        confidence = round(min(0.95, (best_candidate.match_score / 100.0) * (0.95 if is_deadline_feasible else 0.70)), 3)

        # Commit capacity in the accumulator map to prevent double-counting
        committed_capacities[best_candidate.employee_id] = (
            committed_capacities.get(best_candidate.employee_id, 0.0) + usable_hours
        )

        explanation = (
            f"Recommend internal reallocation of {best_candidate.employee_name} ({best_candidate.business_id}). "
            f"Candidate holds verified Level {best_candidate.effective_certified_proficiency} in {best_candidate.skill_name} "
            f"and has {usable_hours:.1f}h/week uncommitted capacity. Transition requires {resolution_days} days."
        )

        assumptions = [
            f"Candidate maintains active employment status without sudden leave requests.",
            f"Releasing project management approves partial/full capacity transition within {resolution_days} days.",
            f"No double-counting: {usable_hours:.1f}h dedicated exclusively to this project requirement.",
        ]

        return RecommendationItem(
            action=RecommendationAction.REALLOCATE,
            gap_id=gap_id,
            project_id=project_id,
            required_skill=required_skill,
            required_hours=usable_hours,
            affected_employees=[best_candidate.employee_id],
            expected_cost=expected_cost,
            estimated_time_to_resolve_days=resolution_days,
            expected_shortage_reduction_hours=usable_hours,
            deadline_feasibility=is_deadline_feasible,
            confidence_score=confidence,
            explanation=explanation,
            assumptions=assumptions,
            rule_version="1.0.0",
        )

