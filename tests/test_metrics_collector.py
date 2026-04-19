"""Tests for metric definitions and the MetricCollector."""

import pytest

from pipewatch.collector import MetricCollector
from pipewatch.metrics import Metric, MetricStatus, ThresholdConfig


def test_threshold_ok():
    t = ThresholdConfig(warning=10, critical=20, compare="gt")
    assert t.evaluate(5) == MetricStatus.OK


def test_threshold_warning():
    t = ThresholdConfig(warning=10, critical=20, compare="gt")
    assert t.evaluate(15) == MetricStatus.WARNING


def test_threshold_critical():
    t = ThresholdConfig(warning=10, critical=20, compare="gt")
    assert t.evaluate(25) == MetricStatus.CRITICAL


def test_threshold_lt():
    t = ThresholdConfig(warning=5, critical=2, compare="lt")
    assert t.evaluate(1) == MetricStatus.CRITICAL
    assert t.evaluate(4) == MetricStatus.WARNING
    assert t.evaluate(10) == MetricStatus.OK


def test_collector_registers_and_collects():
    collector = MetricCollector()
    collector.register("row_count", lambda: 42.0)
    metrics = collector.collect()
    assert len(metrics) == 1
    assert metrics[0].name == "row_count"
    assert metrics[0].value == 42.0
    assert metrics[0].status == MetricStatus.OK


def test_collector_applies_threshold():
    collector = MetricCollector()
    threshold = ThresholdConfig(warning=50, critical=100, compare="gt")
    collector.register("lag", lambda: 75.0, threshold)
    metrics = collector.collect()
    assert metrics[0].status == MetricStatus.WARNING


def test_collector_handles_source_error():
    def bad_source():
        raise RuntimeError("connection failed")

    collector = MetricCollector()
    collector.register("broken", bad_source)
    metrics = collector.collect()
    assert metrics[0].status == MetricStatus.UNKNOWN
    assert "error" in metrics[0].labels


def test_collect_one_unknown_raises():
    collector = MetricCollector()
    with pytest.raises(KeyError):
        collector.collect_one("nonexistent")
