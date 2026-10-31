"""
Historical Demand Time-Series Forecasting Service.

Implements rigorous time-based train/test splitting, candidate model evaluation
against a Seasonal Naive baseline, and future multi-period demand projections.
Guarantees zero future-information leakage during training.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np

from app.services.forecasting.metrics import calculate_forecast_metrics
from app.services.forecasting.models import (
    BaseDemandForecastModel,
    ExponentialSmoothingModel,
    MovingAverageModel,
    RandomForestForecastModel,
    SeasonalNaiveModel,
)
from app.services.forecasting.types import (
    ForecastMetrics,
    ForecastResult,
    ModelComparisonItem,
)


class HistoricalDemandForecastService:
    """
    Coordinates time-series demand forecasting across historical intervals.
    Enforces time-based splitting, baseline benchmarking, and automated model selection.
    """

    @classmethod
    def time_based_split(
        cls,
        series: Sequence[float],
        test_ratio: float = 0.2,
        min_train_size: int = 4,
    ) -> Tuple[List[float], List[float]]:
        """
        Split time-series strictly chronologically.
        The first portion is used for training; the subsequent contiguous portion is used for testing.
        Never shuffles data or uses future observations for training.
        """
        n = len(series)
        if n < min_train_size + 1:
            # Series too short for meaningful split; use last observation as test
            train = list(series[:-1]) if n > 1 else list(series)
            test = [series[-1]] if n > 1 else list(series)
            return train, test

        test_size = max(1, int(n * test_ratio))
        train_size = n - test_size

        train = [float(v) for v in series[:train_size]]
        test = [float(v) for v in series[train_size:]]
        return train, test

    @classmethod
    def generate_synthetic_history(
        cls,
        periods: int = 52,
        base_demand: float = 120.0,
        trend_slope: float = 0.5,
        seasonal_amplitude: float = 25.0,
        seasonality: int = 4,
        noise_std: float = 5.0,
        seed: int = 20261022,
    ) -> List[float]:
        """
        Generate deterministic synthetic historical demand with realistic trend and seasonality.
        Used for benchmarks, unit tests, and simulation scenarios.
        """
        rng = np.random.default_rng(seed)
        history: List[float] = []

        for t in range(periods):
            trend = trend_slope * t
            # Sinusoidal seasonal wave
            seasonal = seasonal_amplitude * np.sin((2.0 * np.pi * t) / seasonality)
            noise = rng.normal(0.0, noise_std)
            val = max(10.0, round(base_demand + trend + seasonal + noise, 2))
            history.append(float(val))

        return history

    @classmethod
    def forecast_demand(
        cls,
        series: Sequence[float],
        prediction_horizon: int = 8,
        series_identifier: str = "Workforce:OverallDemand",
        start_period_label: str = "2026W45",
        seasonality: int = 4,
        test_ratio: float = 0.2,
        include_random_forest: bool = True,
    ) -> ForecastResult:
        """
        Execute full forecasting workflow:
        1. Time-based train/test splitting.
        2. Fit and evaluate Seasonal Naive Baseline.
        3. Fit and evaluate candidate models (Moving Average, Exponential Smoothing, Random Forest).
        4. Calculate MAE, RMSE, WAPE, and Bias on the held-out test split.
        5. Select the best performing model.
        6. Refit the winning model on the full historical series.
        7. Generate forward predictions for `prediction_horizon` periods.
        """
        if len(series) == 0:
            raise ValueError("Input series cannot be empty")

        clean_series = [float(v) for v in series]
        train, test = cls.time_based_split(clean_series, test_ratio=test_ratio)
        test_horizon = len(test)

        # 1. Baseline Model: Seasonal Naive
        baseline_model = SeasonalNaiveModel(seasonality=seasonality)
        baseline_model.fit(train)
        baseline_test_preds = baseline_model.predict(test_horizon)
        baseline_metrics = calculate_forecast_metrics(test, baseline_test_preds)

        comparisons: List[ModelComparisonItem] = [
            ModelComparisonItem(
                model_name=baseline_model.name,
                model_version=baseline_model.version,
                metrics=baseline_metrics,
                is_baseline=True,
                improvement_over_baseline_wape=0.0,
            )
        ]

        # 2. Candidate Models
        candidates: List[BaseDemandForecastModel] = [
            MovingAverageModel(window_size=max(2, seasonality)),
            ExponentialSmoothingModel(alpha=0.35, beta=0.15),
        ]

        if include_random_forest and len(train) >= 6:
            candidates.append(RandomForestForecastModel(n_estimators=50, random_state=20261022))

        candidate_evaluations: List[Tuple[BaseDemandForecastModel, ForecastMetrics]] = [
            (baseline_model, baseline_metrics)
        ]

        for cand in candidates:
            cand.fit(train)
            preds = cand.predict(test_horizon)
            metrics = calculate_forecast_metrics(test, preds)

            # Improvement: baseline_wape - candidate_wape (positive = better)
            imp = baseline_metrics.wape - metrics.wape
            comparisons.append(
                ModelComparisonItem(
                    model_name=cand.name,
                    model_version=cand.version,
                    metrics=metrics,
                    is_baseline=False,
                    improvement_over_baseline_wape=imp,
                )
            )
            candidate_evaluations.append((cand, metrics))

        # 3. Model Selection: Pick model with lowest WAPE (tie-break by lowest MAE)
        best_candidate, best_metrics = min(
            candidate_evaluations,
            key=lambda x: (x[1].wape, x[1].mae),
        )

        # 4. Refit winning model architecture on FULL history
        if isinstance(best_candidate, SeasonalNaiveModel):
            full_model = SeasonalNaiveModel(seasonality=seasonality)
        elif isinstance(best_candidate, MovingAverageModel):
            full_model = MovingAverageModel(window_size=best_candidate.window_size)
        elif isinstance(best_candidate, ExponentialSmoothingModel):
            full_model = ExponentialSmoothingModel(alpha=best_candidate.alpha, beta=best_candidate.beta)
        elif isinstance(best_candidate, RandomForestForecastModel):
            full_model = RandomForestForecastModel(
                n_estimators=best_candidate.n_estimators,
                random_state=best_candidate.random_state,
            )
        else:
            full_model = SeasonalNaiveModel(seasonality=seasonality)

        full_model.fit(clean_series)
        future_forecast = full_model.predict(prediction_horizon)

        # Build prediction period labels (e.g. 2026W45, 2026W46...)
        prediction_periods: List[str] = []
        try:
            year = int(start_period_label[:4])
            week = int(start_period_label[5:])
        except (ValueError, IndexError):
            year = 2026
            week = 45

        for i in range(prediction_horizon):
            w = week + i
            # Basic 52-week rollover formatting
            y = year + (w - 1) // 52
            actual_w = ((w - 1) % 52) + 1
            prediction_periods.append(f"{y}W{actual_w:02d}")

        return ForecastResult(
            series_identifier=series_identifier,
            granularity="weekly",
            prediction_periods=prediction_periods,
            forecast_values=future_forecast,
            selected_model_name=best_candidate.name,
            selected_model_version=best_candidate.version,
            evaluation_metrics=best_metrics,
            comparison_benchmarks=comparisons,
            historical_train_periods_count=len(train),
            historical_test_periods_count=len(test),
            rule_version="1.0.0",
        )

