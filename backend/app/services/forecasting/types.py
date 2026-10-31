"""
WorkforceIQ Forecasting Data Types and Metrics Schemas.
Defines structured data classes for time-series demand forecasting and project rollups.
"""

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ForecastMetrics:
    """Quantitative performance evaluation metrics for demand forecasting models."""
    mae: float            # Mean Absolute Error
    rmse: float           # Root Mean Squared Error
    wape: float           # Weighted Absolute Percentage Error: sum(|y - y_hat|) / sum(y)
    bias: float           # Forecast Bias: sum(y_hat - y) / sum(y)
    sample_size: int      # Number of evaluated test periods

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelComparisonItem:
    """Benchmark evaluation comparison for a candidate model against baseline."""
    model_name: str
    model_version: str
    metrics: ForecastMetrics
    is_baseline: bool
    improvement_over_baseline_wape: float  # Positive indicates better than baseline

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "metrics": self.metrics.to_dict(),
            "is_baseline": self.is_baseline,
            "improvement_over_baseline_wape": round(self.improvement_over_baseline_wape, 4),
        }


@dataclass(frozen=True)
class ForecastResult:
    """Complete multi-period demand forecast output with evaluation traceability."""
    series_identifier: str                 # e.g. "Role:ROL-000001" or "Skill:SKL-000005"
    granularity: str                       # e.g. "weekly"
    prediction_periods: List[str]          # Future time period labels e.g. ["2026W45", "2026W46", ...]
    forecast_values: List[float]           # Predicted demand headcount or hours
    selected_model_name: str
    selected_model_version: str
    evaluation_metrics: ForecastMetrics
    comparison_benchmarks: List[ModelComparisonItem]
    historical_train_periods_count: int
    historical_test_periods_count: int
    rule_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "series_identifier": self.series_identifier,
            "granularity": self.granularity,
            "prediction_periods": self.prediction_periods,
            "forecast_values": [round(v, 2) for v in self.forecast_values],
            "selected_model_name": self.selected_model_name,
            "selected_model_version": self.selected_model_version,
            "evaluation_metrics": self.evaluation_metrics.to_dict(),
            "comparison_benchmarks": [b.to_dict() for b in self.comparison_benchmarks],
            "historical_train_periods_count": self.historical_train_periods_count,
            "historical_test_periods_count": self.historical_test_periods_count,
            "rule_version": self.rule_version,
        }


@dataclass(frozen=True)
class ProjectDemandAggregate:
    """Time-phased planned project demand line grouped across organizational dimensions."""
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "skill_id": self.skill_id,
            "department": self.department,
            "week_label": self.week_label,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "priority_level": self.priority_level,
            "total_required_headcount": self.total_required_headcount,
            "total_required_hours": round(self.total_required_hours, 2),
            "active_projects_count": self.active_projects_count,
            "project_ids": self.project_ids,
        }

