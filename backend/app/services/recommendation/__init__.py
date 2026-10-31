"""
WorkforceIQ Explainable Recommendation Package.
Generates Reallocate, Train, Hire, and Reschedule recommendations following strict decision hierarchy.
"""

from app.services.recommendation.engine import RecommendationEngine
from app.services.recommendation.hiring_evaluator import HiringEvaluator
from app.services.recommendation.reallocation_evaluator import ReallocationEvaluator
from app.services.recommendation.rescheduling_evaluator import ReschedulingEvaluator
from app.services.recommendation.training_evaluator import TrainingEvaluator
from app.services.recommendation.types import (
    FeasibilityEvaluation,
    RecommendationAction,
    RecommendationItem,
    RecommendationPlan,
)

__all__ = [
    "RecommendationAction",
    "FeasibilityEvaluation",
    "RecommendationItem",
    "RecommendationPlan",
    "ReallocationEvaluator",
    "TrainingEvaluator",
    "HiringEvaluator",
    "ReschedulingEvaluator",
    "RecommendationEngine",
]

