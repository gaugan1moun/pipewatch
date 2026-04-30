"""Tests for pipewatch.history and pipewatch.report."""

import json
import os
import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import (
    record_metrics, load_history, get_metric_history,
    trend, HistoryEntry, save_history,
)


@pytest.fixture
def tmp_history(tmp_path):
    return str(tmp_path / "history.json")


def _metric(name, value, status=MetricStatus.OK):
    return Metric(name=name, value=value, status=status)


def test_record_and_load(tmp_history):
    metrics = [_metric("row_count", 100.0), _metric("latency", 0.5)]
    record_metrics(metrics, path=tmp_history)
    entries = load_history(tmp_history)
    assert len(entries) == 2
    assert entries[0].name == "row_count"
    assert entries[1].name == "latency"


def test_record_appends(tmp_history):
    record_metrics([_metric("row_count", 100.0)], path=tmp_history)
    record_metrics([_metric("row_count", 110.0)], path=tmp_history)
    entries = load_history(tmp_history)
    assert len(entries) == 2


def test_get_metric_history_filters(tmp_history):
    record_metrics([_metric("a", 1.0), _metric("b", 2.0)], path=tmp_history)
    entries = get_metric_history("a", path=tmp_history)
    assert all(e.name == "a" for e in entries)
    assert len(entries) == 1


def test_trend_up(tmp_history):
    for v in [1.0, 2.0, 3.0]:
        record_metrics([_metric("x", v)], path=tmp_history)
    assert trend("x", path=tmp_history) == "up"


def test_trend_down(tmp_history):
    for v in [3.0, 2.0, 1.0]:
        record_metrics([_metric("x", v)], path=tmp_history)
    assert trend("x", path=tmp_history) == "down"


def test_trend_stable(tmp_history):
    for v in [5.0, 5.0, 5.0]:
        record_metrics([_metric("x", v)], path=tmp_history)
    assert trend("x", path=tmp_history) == "stable"


def test_trend_insufficient_data(tmp_history):
    record_metrics([_metric("x", 1.0)], path=tmp_history)
    assert trend("x", path=tmp_history) is None


def test_trend_unknown_metric(tmp_history):
    """trend() should return None when the metric has no recorded history."""
    record_metrics([_metric("a", 1.0)], path=tmp_history)
    assert trend("nonexistent", path=tmp_history) is None


def test_load_missing_file(tmp_history):
    assert load_history(tmp_history) == []
