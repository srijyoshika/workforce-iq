"""
External Talent Acquisition and Hiring Evaluator.

Assesses hiring requirements when internal capacity or training is insufficient.
Estimates market hiring lead time, agency fees, and start feasibility.
"""

from app.services.recommendation.types import RecommendationAction, RecommendationItem


class HiringEvaluator:
    """Evaluates external hiring requirements for unmitigated workforce deficits."""

    @classmethod
    def evaluate(
        cls,
        required_hours: float,
        days_to_deadline: int,
        gap_id: str,
        project_id: str,
        required_skill: str,
        standard_hours_per_head: float = 40.0,
    ) -> RecommendationItem:
        """
        Generate external hiring recommendation for open demand deficit.
        """
        headcount_needed = max(1, int(round(required_hours / standard_hours_per_head)))
        hiring_lead_time_days = 45  # Standard sourcing, interviewing, and offer notice period
        cost_per_hire = 12000.0     # Recruitment fee, background check, onboarding
        total_cost = headcount_needed * cost_per_hire

        is_deadline_feasible = hiring_lead_time_days <= days_to_deadline

        confidence = 0.85 if is_deadline_feasible else 0.45

        explanation = (
            f"Recommend external hiring of {headcount_needed} qualified professional(s) with {required_skill} skill profile. "
            f"Internal talent pool has no available capacity or adjacent skills suitable for timely training. "
            f"Estimated acquisition lifecycle is {hiring_lead_time_days} days."
        )

        assumptions = [
            f"Market talent availability for {required_skill} aligns with 45-day median recruitment cycle.",
            f"Hiring budget of ${total_cost:.2f} (${cost_per_hire:.2f}/head) approved by executive sponsor.",
            f"Selected candidate starts and becomes operational within target notice period.",
        ]

        if not is_deadline_feasible:
            assumptions.append(
                f"WARNING: Hiring cycle ({hiring_lead_time_days} days) exceeds deadline ({days_to_deadline} days). "
                f"Pair with project schedule adjustment to prevent day-one delivery delays."
            )

        return RecommendationItem(
            action=RecommendationAction.HIRE,
            gap_id=gap_id,
            project_id=project_id,
            required_skill=required_skill,
            required_hours=required_hours,
            affected_employees=[],
            expected_cost=total_cost,
            estimated_time_to_resolve_days=hiring_lead_time_days,
            expected_shortage_reduction_hours=required_hours,
            deadline_feasibility=is_deadline_feasible,
            confidence_score=confidence,
            explanation=explanation,
            assumptions=assumptions,
            rule_version="1.0.0",
        )

