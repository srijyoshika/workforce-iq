"""
Demand Forecasting Request and Response Pydantic Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ForecastExecutionRequest(BaseModel):
    series_identifier: str = Field(default="Portfolio:OverallDemand", description="Identifier of the series")
    historical_series: Optional[List[float]] = Field(default=None, description="Optional custom historical values")
    prediction_horizon: int = Field(default=8, ge=1, le=52, description="Number of future weeks to predict")
    seasonality: int = Field(default=4, ge=1, description="Seasonal cycle period")
    start_period_label: str = Field(default="2026W45", description="Starting future week label")


class ForecastMetricsSchema(BaseModel):
    mae: float
    rmse: float
    wape: float
    bias: float
    sample_size: int


class ModelComparisonSchema(BaseModel):
    model_name: str
    model_version: str
    metrics: ForecastMetricsSchema
    is_baseline: bool
    improvement_over_baseline_wape: float


class ForecastResponse(BaseModel):
    series_identifier: str
    granularity: str
    prediction_periods: List[str]
    forecast_values: List[float]
    selected_model_name: str
    selected_model_version: str
    evaluation_metrics: ForecastMetricsSchema
    comparison_benchmarks: List[ModelComparisonSchema]
    historical_train_periods_count: int
    historical_test_periods_count: int
    rule_version: str


class ProjectDemandAggregateResponse(BaseModel):
    role_id: str
    skill_id: str
    department: str
    week_label: str
    start_date: str
    end_date: str
    priority_level: int
    total_required_headcount: int
    total_required_hours: float
    active_projects_count: int
    project_ids: List[str]
