"""Tests for pipewatch.report."""

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import record_metrics
from pipewatch.report import build_report, format_report


@pytest.fixture
def tmp_history(tmp_path):
    return str(tmp_path / "history.json")


def _metric(name, value, status=MetricStatus.OK):
    return Metric(name=name, value=value, status=status)


def test_build_report_no_history(tmp_history):
    metrics = [_metric("row_count", 500.0)]
    reports = build_report(metrics, history_path=tmp_history)
    assert len(reports) == 1
    assert reports[0].name == "row_count"
    assert reports[0].trend is None
    assert reports[0].history_count == 0


def test_build_report_with_trend(tmp_history):
    for v in [100.0, 200.0, 300.0]:
        record_metrics([_metric("row_count", v)], path=tmp_history)
    metrics = [_metric("row_count", 400.0)]
    reports = build_report(metrics, history_path=tmp_history)
    assert reports[0].trend == "up"
    assert reports[0].history_count == 3


def test_build_report_status_passed(tmp_history):
    m = _metric("latency", 0.9, MetricStatus.WARNING)
    reports = build_report([m], history_path=tmp_history)
    assert reports[0].status == "warning"


def test_format_report_contains_headers(tmp_history):
    metrics = [_metric("row_count", 100.0)]
    reports = build_report(metrics, history_path=tmp_history)
    output = format_report(reports)
    assert "Metric" in output
    assert "Trend" in output
    assert "History" in output


def test_format_report_contains_metric_name(tmp_history):
    metrics = [_metric("error_rate", 0.02)]
    reports = build_report(metrics, history_path=tmp_history)
    output = format_report(reports)
    assert "error_rate" in output
