"""Simple linear trend forecasting for metric values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import HistoryEntry


@dataclass
class ForecastResult:
    metric_name: str
    horizon: int  # steps ahead
    predicted_value: float
    slope: float
    intercept: float
    confidence: str  # 'low' | 'medium' | 'high'
    based_on: int  # number of data points used

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "horizon": self.horizon,
            "predicted_value": round(self.predicted_value, 4),
            "slope": round(self.slope, 4),
            "intercept": round(self.intercept, 4),
            "confidence": self.confidence,
            "based_on": self.based_on,
        }


def _linear_regression(xs: List[float], ys: List[float]):
    """Return (slope, intercept) for a simple least-squares fit."""
    n = len(xs)
    if n < 2:
        return 0.0, ys[0] if ys else 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    slope = num / den if den != 0 else 0.0
    intercept = mean_y - slope * mean_x
    return slope, intercept


def _confidence(n: int) -> str:
    if n >= 20:
        return "high"
    if n >= 8:
        return "medium"
    return "low"


def forecast_metric(
    entries: List[HistoryEntry],
    metric_name: str,
    horizon: int = 1,
    window: Optional[int] = None,
) -> Optional[ForecastResult]:
    """Forecast *metric_name* ``horizon`` steps ahead using linear regression.

    Returns ``None`` when fewer than 2 matching entries are found.
    """
    relevant = [e for e in entries if e.metric_name == metric_name]
    if window is not None:
        relevant = relevant[-window:]
    if len(relevant) < 2:
        return None

    xs = list(range(len(relevant)))
    ys = [e.value for e in relevant]
    slope, intercept = _linear_regression(xs, ys)
    next_x = len(relevant) - 1 + horizon
    predicted = slope * next_x + intercept

    return ForecastResult(
        metric_name=metric_name,
        horizon=horizon,
        predicted_value=predicted,
        slope=slope,
        intercept=intercept,
        confidence=_confidence(len(relevant)),
        based_on=len(relevant),
    )


def forecast_all(
    entries: List[HistoryEntry],
    horizon: int = 1,
    window: Optional[int] = None,
) -> List[ForecastResult]:
    """Forecast all distinct metrics found in *entries*."""
    names = list(dict.fromkeys(e.metric_name for e in entries))
    results = []
    for name in names:
        result = forecast_metric(entries, name, horizon=horizon, window=window)
        if result is not None:
            results.append(result)
    return results
