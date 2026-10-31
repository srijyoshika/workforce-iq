"""
WorkforceIQ Demand Forecasting Package.
Provides project-based forward demand aggregation and historical time-series forecasting.
"""

from app.services.forecasting.historical_forecast import HistoricalDemandForecastService
from app.services.forecasting.metrics import calculate_forecast_metrics
from app.services.forecasting.models import (
    BaseDemandForecastModel,
    ExponentialSmoothingModel,
    MovingAverageModel,
    RandomForestForecastModel,
    SeasonalNaiveModel,
)
from app.services.forecasting.project_demand import ProjectDemandAggregator
from app.services.forecasting.types import (
    ForecastMetrics,
    ForecastResult,
    ModelComparisonItem,
    ProjectDemandAggregate,
)

__all__ = [
    "BaseDemandForecastModel",
    "SeasonalNaiveModel",
    "MovingAverageModel",
    "ExponentialSmoothingModel",
    "RandomForestForecastModel",
    "calculate_forecast_metrics",
    "ForecastMetrics",
    "ModelComparisonItem",
    "ForecastResult",
    "ProjectDemandAggregate",
    "ProjectDemandAggregator",
    "HistoricalDemandForecastService",
]

