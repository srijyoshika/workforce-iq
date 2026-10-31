"""
Demand Forecasting API Endpoints.
Provides planned project demand aggregation and historical time-series forecasting.
"""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.employee import Employee
from app.schemas.forecasting import (
    ForecastExecutionRequest,
    ForecastMetricsSchema,
    ForecastResponse,
    ModelComparisonSchema,
    ProjectDemandAggregateResponse,
)
from app.services.forecasting import HistoricalDemandForecastService, ProjectDemandAggregator

router = APIRouter(prefix="/forecasting", tags=["Demand Forecasting"])


@router.post("/historical", response_model=ForecastResponse, summary="Execute Time-Series Demand Forecast")
async def forecast_historical_demand(
    payload: ForecastExecutionRequest,
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    """
    Execute multi-model time-series forecasting across historical observations.
    Compares candidate models against Seasonal Naive baseline and selects optimal model.
    """
    series = payload.historical_series
    if not series:
        # Generate realistic baseline synthetic history for portfolio benchmark
        series = HistoricalDemandForecastService.generate_synthetic_history(periods=52, seed=20261022)

    result = HistoricalDemandForecastService.forecast_demand(
        series=series,
        prediction_horizon=payload.prediction_horizon,
        series_identifier=payload.series_identifier,
        start_period_label=payload.start_period_label,
        seasonality=payload.seasonality,
    )

    metrics_schema = ForecastMetricsSchema(
        mae=result.evaluation_metrics.mae,
        rmse=result.evaluation_metrics.rmse,
        wape=result.evaluation_metrics.wape,
        bias=result.evaluation_metrics.bias,
        sample_size=result.evaluation_metrics.sample_size,
    )

    benchmarks = [
        ModelComparisonSchema(
            model_name=b.model_name,
            model_version=b.model_version,
            metrics=ForecastMetricsSchema(
                mae=b.metrics.mae,
                rmse=b.metrics.rmse,
                wape=b.metrics.wape,
                bias=b.metrics.bias,
                sample_size=b.metrics.sample_size,
            ),
            is_baseline=b.is_baseline,
            improvement_over_baseline_wape=b.improvement_over_baseline_wape,
        )
        for b in result.comparison_benchmarks
    ]

    return ForecastResponse(
        series_identifier=result.series_identifier,
        granularity=result.granularity,
        prediction_periods=result.prediction_periods,
        forecast_values=result.forecast_values,
        selected_model_name=result.selected_model_name,
        selected_model_version=result.selected_model_version,
        evaluation_metrics=metrics_schema,
        comparison_benchmarks=benchmarks,
        historical_train_periods_count=result.historical_train_periods_count,
        historical_test_periods_count=result.historical_test_periods_count,
        rule_version=result.rule_version,
    )


@router.get("/project-demand", response_model=List[ProjectDemandAggregateResponse], summary="Aggregate Forward Project Demands")
async def get_project_demand_aggregates(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    department: Optional[str] = Query(default=None, description="Filter by department"),
    min_priority: Optional[int] = Query(default=None, ge=1, le=4, description="Filter up to priority tier"),
):
    """
    Aggregate active project demand lines across role, skill, department, week, and priority level.
    """
    aggregates = await ProjectDemandAggregator.aggregate_project_demands_async(
        session=session,
        department=department,
        min_priority=min_priority,
    )
    return [
        ProjectDemandAggregateResponse(
            role_id=a.role_id,
            skill_id=a.skill_id,
            department=a.department,
            week_label=a.week_label,
            start_date=a.start_date,
            end_date=a.end_date,
            priority_level=a.priority_level,
            total_required_headcount=a.total_required_headcount,
            total_required_hours=a.total_required_hours,
            active_projects_count=a.active_projects_count,
            project_ids=a.project_ids,
        )
        for a in aggregates
    ]
