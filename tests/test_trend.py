"""Tests for pipewatch.trend module."""
import pytest
from pipewatch.trend import compute_trend, trend_summary, TrendDirection
from pipewatch.history import HistoryEntry
from pipewatch.metrics import MetricStatus


def _entry(value: float, name: str = "test_metric") -> HistoryEntry:
    return HistoryEntry(
        metric_name=name,
        value=value,
        status=MetricStatus.OK,
        timestamp="2024-01-01T00:00:00",
    )


def test_insufficient_data_empty():
    assert compute_trend([]) == TrendDirection.INSUFFICIENT_DATA


def test_insufficient_data_single():
    assert compute_trend([_entry(1.0)]) == TrendDirection.INSUFFICIENT_DATA


def test_stable_trend():
    entries = [_entry(5.0)] * 5
    assert compute_trend(entries) == TrendDirection.STABLE


def test_degrading_trend():
    entries = [_entry(float(i)) for i in range(1, 6)]  # 1,2,3,4,5 rising
    assert compute_trend(entries) == TrendDirection.DEGRADING


def test_improving_trend():
    entries = [_entry(float(i)) for i in range(5, 0, -1)]  # 5,4,3,2,1 falling
    assert compute_trend(entries) == TrendDirection.IMPROVING


def test_window_limits_entries():
    # First entries are degrading, last 3 are stable — window=3 should give stable
    entries = [_entry(float(i)) for i in range(1, 6)]  # 1..5 degrading
    entries += [_entry(10.0), _entry(10.0), _entry(10.0)]  # stable tail
    result = compute_trend(entries, window=3)
    assert result == TrendDirection.STABLE


def test_trend_summary_insufficient():
    summary = trend_summary("my_metric", [])
    assert "insufficient" in summary
    assert "my_metric" in summary


def test_trend_summary_degrading():
    entries = [_entry(float(i)) for i in range(1, 6)]
    summary = trend_summary("errors", entries)
    assert "degrading" in summary
    assert "errors" in summary
    assert "->" in summary


def test_trend_summary_improving():
    entries = [_entry(float(i)) for i in range(10, 5, -1)]
    summary = trend_summary("latency", entries)
    assert "improving" in summary
