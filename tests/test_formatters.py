"""Tests for output formatters."""

from __future__ import annotations

import json

import pytest

from pipewatch.formatters import format_json, format_summary, format_table
from pipewatch.metrics import Metric, MetricStatus


def _metrics():
    return [
        Metric(name="pipeline.lag", value=5.0, status=MetricStatus.OK, message="ok"),
        Metric(name="pipeline.errors", value=12.0, status=MetricStatus.WARNING, message="high"),
        Metric(name="pipeline.drop", value=99.0, status=MetricStatus.CRITICAL, message="critical"),
    ]


def test_format_table_contains_names():
    out = format_table(_metrics(), color=False)
    assert "pipeline.lag" in out
    assert "pipeline.errors" in out
    assert "pipeline.drop" in out


def test_format_table_contains_statuses():
    out = format_table(_metrics(), color=False)
    assert "ok" in out
    assert "warning" in out
    assert "critical" in out


def test_format_table_header():
    out = format_table(_metrics(), color=False)
    assert "NAME" in out
    assert "STATUS" in out
    assert "VALUE" in out


def test_format_json_valid():
    out = format_json(_metrics())
    data = json.loads(out)
    assert len(data) == 3
    assert data[0]["name"] == "pipeline.lag"
    assert data[1]["status"] == "warning"


def test_format_json_all_fields():
    out = format_json(_metrics())
    data = json.loads(out)
    for entry in data:
        assert "name" in entry
        assert "value" in entry
        assert "status" in entry


def test_format_summary_ok():
    metrics = [Metric(name="x", value=1, status=MetricStatus.OK, message="")]
    out = format_summary(metrics)
    assert "OK" in out.upper()


def test_format_summary_critical_dominates():
    out = format_summary(_metrics())
    assert "CRITICAL" in out.upper()


def test_format_summary_counts():
    out = format_summary(_metrics())
    assert "ok=1" in out
    assert "warning=1" in out
    assert "critical=1" in out
