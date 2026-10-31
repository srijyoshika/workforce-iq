"""
Forecasting Accuracy and Error Evaluation Metrics.
Calculates MAE, RMSE, WAPE, and Forecast Bias.
"""

from typing import Sequence
import numpy as np
from app.services.forecasting.types import ForecastMetrics


def calculate_forecast_metrics(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> ForecastMetrics:
    """
    Calculate quantitative forecast accuracy and bias metrics.
    Guards against zero-division for sparse workforce demand series.

    Formulas:
    - MAE  = mean(|y - y_hat|)
    - RMSE = sqrt(mean((y - y_hat)^2))
    - WAPE = sum(|y - y_hat|) / sum(y)
    - Bias = sum(y_hat - y) / sum(y)
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")

    n = len(y_true)
    if n == 0:
        return ForecastMetrics(mae=0.0, rmse=0.0, wape=0.0, bias=0.0, sample_size=0)

    y_arr = np.array(y_true, dtype=float)
    y_hat = np.array(y_pred, dtype=float)

    errors = y_hat - y_arr
    abs_errors = np.abs(errors)

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    total_actual = float(np.sum(y_arr))
    total_abs_error = float(np.sum(abs_errors))
    total_error = float(np.sum(errors))

    if total_actual > 0.0:
        wape = float(total_abs_error / total_actual)
        bias = float(total_error / total_actual)
    else:
        # Fallback when actual demand is 0 across the entire evaluation interval
        wape = 0.0 if total_abs_error == 0.0 else 1.0
        bias = 0.0 if total_error == 0.0 else float(np.sign(total_error))

    return ForecastMetrics(
        mae=round(mae, 4),
        rmse=round(rmse, 4),
        wape=round(wape, 4),
        bias=round(bias, 4),
        sample_size=n,
    )

