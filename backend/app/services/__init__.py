"""WorkforceIQ Business and System Services Package."""

from app.services.capacity_service import CapacityResult, CapacityService
from app.services.demand_aggregation_service import (
    DemandAggregateItem,
    DemandAggregationService,
)
from app.services.forecasting import (
    HistoricalDemandForecastService,
    ProjectDemandAggregator,
)
from app.services.gap_analysis_service import GapAnalysisResult, GapAnalysisService
from app.services.health_service import HealthService
from app.services.optimization import (
    GreedyBaselineSolver,
    OrToolsWorkforceSolver,
    WorkforceOptimizerService,
)
from app.services.recommendation import (
    RecommendationAction,
    RecommendationEngine,
    RecommendationItem,
    RecommendationPlan,
)
from app.services.risk_service import RiskDetectionItem, RiskService
from app.services.scenario_service import ScenarioEngineService
from app.services.skill_matching_service import CandidateMatch, SkillMatchingService
from app.services.thresholds import DEFAULT_THRESHOLDS, PlanningThresholds
from app.services.utilization_service import (
    DepartmentUtilizationSummary,
    UtilizationCategory,
    UtilizationResult,
    UtilizationService,
)

__all__ = [
    "HealthService",
    "PlanningThresholds",
    "DEFAULT_THRESHOLDS",
    "CapacityService",
    "CapacityResult",
    "UtilizationService",
    "UtilizationResult",
    "UtilizationCategory",
    "DepartmentUtilizationSummary",
    "SkillMatchingService",
    "CandidateMatch",
    "DemandAggregationService",
    "DemandAggregateItem",
    "GapAnalysisService",
    "GapAnalysisResult",
    "RiskService",
    "RiskDetectionItem",
    "HistoricalDemandForecastService",
    "ProjectDemandAggregator",
    "RecommendationEngine",
    "RecommendationAction",
    "RecommendationItem",
    "RecommendationPlan",
    "WorkforceOptimizerService",
    "OrToolsWorkforceSolver",
    "GreedyBaselineSolver",
]
