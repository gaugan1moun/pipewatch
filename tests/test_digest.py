"""Tests for pipewatch.digest module."""

import json
from datetime import datetime, timedelta

import pytest

from pipewatch.digest import build_digest, DigestReport, MetricDigest
from pipewatch.history import save_history, HistoryEntry
from pipewatch.metrics import MetricStatus


def _entry(name: str, status: MetricStatus, hours_ago: float = 1.0) -> HistoryEntry:
    ts = (datetime.utcnow() - timedelta(hours=hours_ago)).isoformat(timespec="seconds")
    return HistoryEntry(name=name, value=1.0, status=status, timestamp=ts, unit="count")


@pytest.fixture
def tmp_history(tmp_path):
    return str(tmp_path / "history.json")


def test_empty_history_returns_no_metrics(tmp_history):
    report = build_digest(tmp_history, window_hours=24)
    assert isinstance(report, DigestReport)
    assert report.metrics == []


def test_digest_counts_statuses(tmp_history):
    entries = [
        _entry("row_count", MetricStatus.OK),
        _entry("row_count", MetricStatus.WARNING),
        _entry("row_count", MetricStatus.CRITICAL),
    ]
    save_history(tmp_history, entries)
    report = build_digest(tmp_history, window_hours=24)
    assert len(report.metrics) == 1
    m = report.metrics[0]
    assert m.ok == 1
    assert m.warning == 1
    assert m.critical == 1
    assert m.total == 3


def test_digest_worst_is_critical(tmp_history):
    entries = [
        _entry("latency", MetricStatus.OK),
        _entry("latency", MetricStatus.CRITICAL),
    ]
    save_history(tmp_history, entries)
    report = build_digest(tmp_history, window_hours=24)
    assert report.metrics[0].worst == MetricStatus.CRITICAL


def test_digest_excludes_old_entries(tmp_history):
    entries = [
        _entry("row_count", MetricStatus.OK, hours_ago=0.5),
        _entry("row_count", MetricStatus.CRITICAL, hours_ago=48),
    ]
    save_history(tmp_history, entries)
    report = build_digest(tmp_history, window_hours=24)
    assert report.metrics[0].total == 1
    assert report.metrics[0].worst == MetricStatus.OK


def test_digest_to_dict_serializable(tmp_history):
    entries = [_entry("errors", MetricStatus.WARNING)]
    save_history(tmp_history, entries)
    report = build_digest(tmp_history, window_hours=24)
    d = report.to_dict()
    assert json.dumps(d)  # must be JSON-serializable
    assert d["window_hours"] == 24
    assert d["metrics"][0]["name"] == "errors"


def test_digest_multiple_metrics(tmp_history):
    entries = [
        _entry("a", MetricStatus.OK),
        _entry("b", MetricStatus.WARNING),
    ]
    save_history(tmp_history, entries)
    report = build_digest(tmp_history, window_hours=24)
    names = [m.name for m in report.metrics]
    assert "a" in names
    assert "b" in names
