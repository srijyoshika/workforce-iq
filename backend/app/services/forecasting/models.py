"""
WorkforceIQ Demand Forecasting Model Implementations.
Includes:
1. Seasonal Naive Baseline (benchmark)
2. Moving Average
3. Double Exponential Smoothing (Holt's Linear Trend)
4. Random Forest Regression (multi-feature lag regression)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Sequence
import numpy as np


class BaseDemandForecastModel(ABC):
    """Abstract interface for workforce demand time-series forecasting models."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.history: List[float] = []

    @abstractmethod
    def fit(self, series: Sequence[float]) -> "BaseDemandForecastModel":
        """Fit model on historical training demand series."""
        pass

    @abstractmethod
    def predict(self, horizon: int) -> List[float]:
        """Generate point forecasts for the next `horizon` periods."""
        pass


class SeasonalNaiveModel(BaseDemandForecastModel):
    """
    Seasonal Naive Baseline Model.
    Forecasts future demand by repeating the demand observed at the same seasonal cycle.
    Default seasonality period = 4 (e.g. 4-week monthly cycle).
    Serves as the canonical baseline for all benchmark comparisons.
    """

    def __init__(self, seasonality: int = 4, version: str = "1.0.0"):
        super().__init__(name="Seasonal Naive Baseline", version=version)
        self.seasonality = max(1, seasonality)

    def fit(self, series: Sequence[float]) -> "SeasonalNaiveModel":
        self.history = [float(v) for v in series]
        return self

    def predict(self, horizon: int) -> List[float]:
        if not self.history:
            return [0.0] * horizon

        n = len(self.history)
        predictions: List[float] = []

        for h in range(1, horizon + 1):
            if n >= self.seasonality:
                # Value from identical seasonal offset in the most recent cycle
                idx = n - self.seasonality + ((h - 1) % self.seasonality)
                val = self.history[idx]
            else:
                # Fallback to naive last known value if history is shorter than seasonality
                val = self.history[-1]
            predictions.append(max(0.0, float(val)))

        return predictions


class MovingAverageModel(BaseDemandForecastModel):
    """
    Moving Average Forecast Model.
    Forecasts demand as the mean of the trailing `window_size` periods.
    """

    def __init__(self, window_size: int = 4, version: str = "1.0.0"):
        super().__init__(name=f"Moving Average (k={window_size})", version=version)
        self.window_size = max(1, window_size)

    def fit(self, series: Sequence[float]) -> "MovingAverageModel":
        self.history = [float(v) for v in series]
        return self

    def predict(self, horizon: int) -> List[float]:
        if not self.history:
            return [0.0] * horizon

        k = min(len(self.history), self.window_size)
        recent_window = self.history[-k:]
        mean_val = float(np.mean(recent_window))
        # Moving average produces constant forward projection
        return [max(0.0, round(mean_val, 2))] * horizon


class ExponentialSmoothingModel(BaseDemandForecastModel):
    """
    Holt's Linear Exponential Smoothing Model.
    Captures both current demand level and linear trend velocity.
    Formula:
        level: l_t = alpha * y_t + (1 - alpha) * (l_{t-1} + b_{t-1})
        trend: b_t = beta * (l_t - l_{t-1}) + (1 - beta) * b_{t-1}
        forecast: y_hat_{t+h} = l_t + h * b_t
    """

    def __init__(self, alpha: float = 0.3, beta: float = 0.1, version: str = "1.0.0"):
        super().__init__(name="Double Exponential Smoothing (Holt)", version=version)
        self.alpha = min(1.0, max(0.01, alpha))
        self.beta = min(1.0, max(0.01, beta))
        self.level = 0.0
        self.trend = 0.0

    def fit(self, series: Sequence[float]) -> "ExponentialSmoothingModel":
        self.history = [float(v) for v in series]
        n = len(self.history)
        if n == 0:
            self.level = 0.0
            self.trend = 0.0
            return self

        if n == 1:
            self.level = self.history[0]
            self.trend = 0.0
            return self

        # Initialize level and trend from first two observations
        self.level = self.history[0]
        self.trend = self.history[1] - self.history[0]

        for t in range(1, n):
            y_t = self.history[t]
            prev_level = self.level
            prev_trend = self.trend

            # Update equations
            self.level = self.alpha * y_t + (1.0 - self.alpha) * (prev_level + prev_trend)
            self.trend = self.beta * (self.level - prev_level) + (1.0 - self.beta) * prev_trend

        return self

    def predict(self, horizon: int) -> List[float]:
        if not self.history:
            return [0.0] * horizon

        predictions: List[float] = []
        for h in range(1, horizon + 1):
            pred = self.level + (h * self.trend)
            # Workforce demand cannot be negative
            predictions.append(max(0.0, round(float(pred), 2)))

        return predictions


class RandomForestForecastModel(BaseDemandForecastModel):
    """
    Random Forest Autoregressive Demand Forecasting Model.
    Transforms time-series demand into supervised tabular features:
    - Lag 1, Lag 2, Lag 3, Lag 4
    - Rolling 3-period mean
    - Cyclical seasonal index (period % 4)
    - Trend step index
    Uses scikit-learn RandomForestRegressor with recursive multi-step forecasting.
    """

    def __init__(
        self,
        n_estimators: int = 50,
        max_depth: int = 5,
        random_state: int = 20261022,
        version: str = "1.0.0",
    ):
        super().__init__(name="Random Forest Regressor", version=version)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = None

    def _build_features(self, series: List[float], idx: int) -> List[float]:
        """
        Extract lag and rolling features for position `idx` using strictly past data (idx-1, idx-2, ...).
        Guarantees zero data leakage from future periods.
        """
        lag1 = series[idx - 1] if idx >= 1 else series[0]
        lag2 = series[idx - 2] if idx >= 2 else lag1
        lag3 = series[idx - 3] if idx >= 3 else lag2
        lag4 = series[idx - 4] if idx >= 4 else lag3

        # Trailing 3-period rolling average
        trailing_3 = [series[idx - k] for k in range(1, min(4, idx + 1))]
        rolling_mean = float(np.mean(trailing_3)) if trailing_3 else lag1

        seasonal_cycle = float(idx % 4)
        trend_index = float(idx)

        return [lag1, lag2, lag3, lag4, rolling_mean, seasonal_cycle, trend_index]

    def fit(self, series: Sequence[float]) -> "RandomForestForecastModel":
        self.history = [float(v) for v in series]
        n = len(self.history)

        if n < 6:
            # Insufficient samples for random forest tabular lag creation; will fallback to naive on predict
            self.model = None
            return self

        from sklearn.ensemble import RandomForestRegressor

        X = []
        y = []
        # Build training rows from lag window
        for i in range(4, n):
            features = self._build_features(self.history, i)
            X.append(features)
            y.append(self.history[i])

        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_state,
        )
        self.model.fit(X, y)
        return self

    def predict(self, horizon: int) -> List[float]:
        if not self.history:
            return [0.0] * horizon

        if self.model is None:
            # Fallback to mean of recent history if history is too short for RF training
            mean_val = float(np.mean(self.history[-4:]))
            return [max(0.0, round(mean_val, 2))] * horizon

        # Recursive multi-step forecasting
        simulated_history = list(self.history)
        predictions: List[float] = []

        for h in range(horizon):
            curr_idx = len(simulated_history)
            features = self._build_features(simulated_history, curr_idx)
            pred_val = float(self.model.predict([features])[0])
            pred_clean = max(0.0, round(pred_val, 2))
            predictions.append(pred_clean)
            simulated_history.append(pred_clean)

        return predictions

