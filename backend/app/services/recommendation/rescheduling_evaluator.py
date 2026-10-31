"""
Project Rescheduling and Timeline Shift Evaluator.

Assesses feasibility of delaying or shifting project start dates when:
1. Hiring or training lead time exceeds project start deadline.
2. Talent shortages make on-time staffing impossible.
3. Project priority allows schedule flexibility (Priority > 1).
"""

from typing import Optional
from app.services.recommendation.types import RecommendationAction, RecommendationItem


class ReschedulingEvaluator:
    """Evaluates project schedule adjustments to accommodate workforce constraints."""

    @classmethod
    def evaluate(
        cls,
        required_hours: float,
        days_to_deadline: int,
        project_priority: int,
        recommended_action: Optional[RecommendationAction],
        gap_id: str,
        project_id: str,
        required_skill: str,
    ) -> Optional[RecommendationItem]:
        """
        Evaluate project timeline shift feasibility.
        If priority is critical (Priority 1), rescheduling is strongly discouraged.
        If priority > 1 and deadline is breached by hiring/training, rescheduling is recommended.
        """
        # Critical tier projects (Priority 1) cannot be rescheduled easily
        if project_priority <= 1:
            return None

        # Determine recommended shift delay based on whether hiring (45d) or training (14-28d) is needed
        if recommended_action == RecommendationAction.HIRE:
            needed_days = 45
        elif recommended_action == RecommendationAction.TRAIN:
            needed_days = 28
        else:
            needed_days = 14

        shift_days = max(14, needed_days - days_to_deadline)

        # Minimal schedule adjustment cost
        schedule_adjustment_cost = 1000.0

        explanation = (
            f"Recommend shifting Project {project_id} start timeline by {shift_days} days. "
            f"Project priority level ({project_priority}) allows scheduling flexibility. "
            f"Extending start date allows sufficient window for workforce onboarding / upskilling."
        )

        assumptions = [
            f"Client / executive stakeholders accept a {shift_days}-day delivery start milestone delay.",
            f"Non-critical priority rating ({project_priority}) allows flexible schedule sequencing.",
            f"Talent acquisition or upskilling actions proceed concurrently during the shift window.",
        ]

        return RecommendationItem(
            action=RecommendationAction.RESCHEDULE,
            gap_id=gap_id,
            project_id=project_id,
            required_skill=required_skill,
            required_hours=required_hours,
            affected_employees=[],
            expected_cost=schedule_adjustment_cost,
            estimated_time_to_resolve_days=shift_days,
            expected_shortage_reduction_hours=required_hours,
            deadline_feasibility=True,
            confidence_score=0.90,
            explanation=explanation,
            assumptions=assumptions,
            rule_version="1.0.0",
        )

