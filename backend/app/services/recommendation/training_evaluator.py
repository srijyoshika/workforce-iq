"""
Internal Upskilling and Training Evaluator.

Assesses feasibility of training internal employees with adjacent skills or partial proficiency.
Evaluates training duration, cost, and deadline feasibility.
"""

from typing import Dict, Optional, Sequence
from app.services.recommendation.types import RecommendationAction, RecommendationItem
from app.services.skill_matching_service import CandidateMatch


class TrainingEvaluator:
    """Evaluates candidates for accelerated upskilling / certification training."""

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
        Evaluate candidate pool for training.
        Selects candidate with existing partial competence (proficiency gap <= 2 levels)
        and available learning capacity.
        """
        trainable_candidate: Optional[CandidateMatch] = None
        gap_levels = 1

        for cand in candidates:
            # Already fully qualified employees are handled by reallocation
            if cand.is_fully_qualified and not cand.is_stale:
                continue

            # Check capacity availability
            already_committed = committed_capacities.get(cand.employee_id, 0.0)
            net_free_hours = max(0.0, cand.remaining_capacity_hours - already_committed)

            if net_free_hours < 10.0:
                continue

            # Candidate is trainable if they have assessed proficiency within 2 levels of requirement
            level_deficit = max(1, cand.required_proficiency - cand.assessed_proficiency)
            if level_deficit <= 2 or cand.is_stale:
                trainable_candidate = cand
                gap_levels = level_deficit
                break

        if not trainable_candidate:
            return None

        # Estimated training duration: 14 days per level deficit (or 7 days for stale skill refresher)
        if trainable_candidate.is_stale and gap_levels == 0:
            training_days = 7
            training_cost = 1500.0
        else:
            training_days = 14 * gap_levels
            training_cost = 2500.0 + (1000.0 * (gap_levels - 1))

        is_deadline_feasible = training_days <= days_to_deadline
        usable_hours = min(trainable_candidate.available_hours, required_hours)

        # Confidence is penalised if training duration exceeds deadline
        confidence = round(0.80 if is_deadline_feasible else 0.55, 3)

        committed_capacities[trainable_candidate.employee_id] = (
            committed_capacities.get(trainable_candidate.employee_id, 0.0) + usable_hours
        )

        reason_str = "re-certification" if trainable_candidate.is_stale else f"upskilling by {gap_levels} level(s)"
        explanation = (
            f"Recommend targeted training and {reason_str} for {trainable_candidate.employee_name} ({trainable_candidate.business_id}). "
            f"Candidate has adjacent proficiency in {trainable_candidate.skill_name}. "
            f"Curriculum requires {training_days} days to reach certified Level {trainable_candidate.required_proficiency}."
        )

        assumptions = [
            f"Candidate completes structured coursework and achieves certification within {training_days} days.",
            f"Manager allocates dedicated learning hours without operational delivery conflicts.",
            f"Training program cost of ${training_cost:.2f} is absorbed by corporate learning budget.",
        ]

        return RecommendationItem(
            action=RecommendationAction.TRAIN,
            gap_id=gap_id,
            project_id=project_id,
            required_skill=required_skill,
            required_hours=usable_hours,
            affected_employees=[trainable_candidate.employee_id],
            expected_cost=training_cost,
            estimated_time_to_resolve_days=training_days,
            expected_shortage_reduction_hours=usable_hours,
            deadline_feasibility=is_deadline_feasible,
            confidence_score=confidence,
            explanation=explanation,
            assumptions=assumptions,
            rule_version="1.0.0",
        )

