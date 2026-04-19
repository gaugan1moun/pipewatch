"""Tests for pipewatch.snapshot module."""
import json
import os
import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.snapshot import (
    Snapshot,
    capture_snapshot,
    save_snapshot,
    load_snapshots,
    diff_snapshots,
)


def _metric(name: str, status: MetricStatus, value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=status, threshold=None)


@pytest.fixture
def tmp_snapshot_path(tmp_path):
    return str(tmp_path / "snapshots.json")


def test_capture_snapshot_records_statuses():
    metrics = [
        _metric("lag", MetricStatus.OK),
        _metric("error_rate", MetricStatus.WARNING),
    ]
    snap = capture_snapshot(metrics)
    assert snap.metrics["lag"] == "ok"
    assert snap.metrics["error_rate"] == "warning"


def test_capture_snapshot_has_timestamp():
    snap = capture_snapshot([_metric("x", MetricStatus.OK)])
    assert isinstance(snap.timestamp, str)
    assert len(snap.timestamp) > 0


def test_save_and_load_snapshot(tmp_snapshot_path):
    snap = capture_snapshot([_metric("lag", MetricStatus.OK)])
    save_snapshot(snap, tmp_snapshot_path)
    loaded = load_snapshots(tmp_snapshot_path)
    assert len(loaded) == 1
    assert loaded[0].metrics["lag"] == "ok"


def test_save_appends_snapshots(tmp_snapshot_path):
    s1 = capture_snapshot([_metric("lag", MetricStatus.OK)])
    s2 = capture_snapshot([_metric("lag", MetricStatus.CRITICAL)])
    save_snapshot(s1, tmp_snapshot_path)
    save_snapshot(s2, tmp_snapshot_path)
    loaded = load_snapshots(tmp_snapshot_path)
    assert len(loaded) == 2


def test_load_snapshots_missing_file(tmp_snapshot_path):
    result = load_snapshots(tmp_snapshot_path)
    assert result == []


def test_diff_snapshots_detects_change():
    prev = Snapshot(timestamp="t1", metrics={"lag": "ok", "errors": "ok"})
    curr = Snapshot(timestamp="t2", metrics={"lag": "warning", "errors": "ok"})
    changes = diff_snapshots(prev, curr)
    assert "lag" in changes
    assert changes["lag"] == {"previous": "ok", "current": "warning"}
    assert "errors" not in changes


def test_diff_snapshots_new_metric():
    prev = Snapshot(timestamp="t1", metrics={"lag": "ok"})
    curr = Snapshot(timestamp="t2", metrics={"lag": "ok", "errors": "critical"})
    changes = diff_snapshots(prev, curr)
    assert "errors" in changes
    assert changes["errors"]["previous"] is None


def test_diff_snapshots_no_changes():
    prev = Snapshot(timestamp="t1", metrics={"lag": "ok"})
    curr = Snapshot(timestamp="t2", metrics={"lag": "ok"})
    assert diff_snapshots(prev, curr) == {}
