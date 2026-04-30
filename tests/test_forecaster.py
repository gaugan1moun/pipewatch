"""Tests for pipewatch.forecaster."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from pipewatch.history import HistoryEntry
from pipewatch.forecaster import (
    ForecastResult,
    forecast_metric,
    forecast_all,
    _linear_regression,
    _confidence,
)


def _entry(name: str, value: float, ts: str = "2024-01-01T00:00:00") -> HistoryEntry:
    return HistoryEntry(metric_name=name, value=value, status="ok", timestamp=ts)


def _series(name: str, values: List[float]) -> List[HistoryEntry]:
    return [_entry(name, v, f"2024-01-01T{i:02d}:00:00") for i, v in enumerate(values)]


# --- _linear_regression ---

def test_linear_regression_perfect_line():
    slope, intercept = _linear_regression([0, 1, 2, 3], [0, 2, 4, 6])
    assert abs(slope - 2.0) < 1e-9
    assert abs(intercept) < 1e-9


def test_linear_regression_flat():
    slope, intercept = _linear_regression([0, 1, 2], [5, 5, 5])
    assert abs(slope) < 1e-9
    assert abs(intercept - 5.0) < 1e-9


def test_linear_regression_single_point():
    slope, intercept = _linear_regression([0], [3.0])
    assert slope == 0.0
    assert intercept == 3.0


# --- _confidence ---

def test_confidence_low():
    assert _confidence(1) == "low"
    assert _confidence(7) == "low"


def test_confidence_medium():
    assert _confidence(8) == "medium"
    assert _confidence(19) == "medium"


def test_confidence_high():
    assert _confidence(20) == "high"
    assert _confidence(100) == "high"


# --- forecast_metric ---

def test_forecast_returns_none_for_single_entry():
    entries = [_entry("lag", 1.0)]
    assert forecast_metric(entries, "lag") is None


def test_forecast_returns_none_for_unknown_metric():
    entries = _series("lag", [1.0, 2.0, 3.0])
    assert forecast_metric(entries, "unknown") is None


def test_forecast_increasing_trend():
    entries = _series("lag", [1.0, 2.0, 3.0, 4.0, 5.0])
    result = forecast_metric(entries, "lag", horizon=1)
    assert isinstance(result, ForecastResult)
    assert result.metric_name == "lag"
    assert abs(result.predicted_value - 6.0) < 0.01
    assert result.slope > 0


def test_forecast_horizon_2():
    entries = _series("lag", [0.0, 1.0, 2.0, 3.0])
    r1 = forecast_metric(entries, "lag", horizon=1)
    r2 = forecast_metric(entries, "lag", horizon=2)
    assert r2.predicted_value > r1.predicted_value


def test_forecast_window_limits_data():
    entries = _series("lag", [100.0, 200.0, 1.0, 2.0, 3.0])
    result_windowed = forecast_metric(entries, "lag", horizon=1, window=3)
    result_full = forecast_metric(entries, "lag", horizon=1)
    # windowed result should be based on only 3 points
    assert result_windowed.based_on == 3
    assert result_full.based_on == 5


def test_forecast_to_dict_keys():
    entries = _series("lag", [1.0, 2.0, 3.0])
    result = forecast_metric(entries, "lag")
    d = result.to_dict()
    for key in ("metric_name", "horizon", "predicted_value", "slope", "intercept", "confidence", "based_on"):
        assert key in d


# --- forecast_all ---

def test_forecast_all_returns_all_metrics():
    entries = _series("lag", [1.0, 2.0, 3.0]) + _series("errors", [5.0, 4.0, 3.0])
    results = forecast_all(entries)
    names = {r.metric_name for r in results}
    assert names == {"lag", "errors"}


def test_forecast_all_skips_insufficient():
    entries = _series("lag", [1.0, 2.0, 3.0]) + [_entry("errors", 1.0)]
    results = forecast_all(entries)
    assert len(results) == 1
    assert results[0].metric_name == "lag"


def test_forecast_all_empty_entries():
    assert forecast_all([]) == []
