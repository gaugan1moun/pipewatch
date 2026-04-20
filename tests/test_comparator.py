"""Tests for pipewatch.comparator."""
from __future__ import annotations

import pytest

from pipewatch.comparator import (
    MetricDiff,
    SnapshotComparison,
    compare_snapshots,
)
from pipewatch.metrics import MetricStatus
from pipewatch.snapshot import Snapshot


def _snap(timestamp: str, entries: list) -> Snapshot:
    return Snapshot(timestamp=timestamp, entries=entries)


def _entry(name: str, status: str, value: float = 1.0) -> dict:
    return {"name": name, "status": status, "value": value}


# ---------------------------------------------------------------------------
# MetricDiff.direction
# ---------------------------------------------------------------------------

def test_direction_degraded():
    d = MetricDiff("m", MetricStatus.OK, MetricStatus.CRITICAL, 1.0, 9.0)
    assert d.direction == "degraded"


def test_direction_improved():
    d = MetricDiff("m", MetricStatus.CRITICAL, MetricStatus.OK, 9.0, 1.0)
    assert d.direction == "improved"


def test_direction_unchanged():
    d = MetricDiff("m", MetricStatus.OK, MetricStatus.OK, 1.0, 1.0)
    assert d.direction == "unchanged"
    assert not d.changed


def test_direction_new():
    d = MetricDiff("m", None, MetricStatus.WARNING, None, 5.0)
    assert d.direction == "new"
    assert d.changed


def test_direction_removed():
    d = MetricDiff("m", MetricStatus.OK, None, 1.0, None)
    assert d.direction == "removed"
    assert d.changed


# ---------------------------------------------------------------------------
# compare_snapshots
# ---------------------------------------------------------------------------

def test_compare_same_snapshots():
    snap = _snap("2024-01-01T00:00:00", [
        _entry("rows", "ok", 100),
        _entry("lag", "warning", 5),
    ])
    result = compare_snapshots(snap, snap)
    assert len(result.diffs) == 2
    assert len(result.changed_metrics) == 0


def test_compare_detects_degradation():
    old = _snap("2024-01-01T00:00:00", [_entry("rows", "ok", 100)])
    new = _snap("2024-01-01T01:00:00", [_entry("rows", "critical", 0)])
    result = compare_snapshots(old, new)
    assert len(result.changed_metrics) == 1
    assert result.changed_metrics[0].direction == "degraded"


def test_compare_detects_new_metric():
    old = _snap("2024-01-01T00:00:00", [])
    new = _snap("2024-01-01T01:00:00", [_entry("rows", "ok", 50)])
    result = compare_snapshots(old, new)
    assert result.diffs[0].direction == "new"


def test_compare_detects_removed_metric():
    old = _snap("2024-01-01T00:00:00", [_entry("rows", "ok", 50)])
    new = _snap("2024-01-01T01:00:00", [])
    result = compare_snapshots(old, new)
    assert result.diffs[0].direction == "removed"


def test_to_dict_structure():
    old = _snap("T1", [_entry("m", "ok", 1)])
    new = _snap("T2", [_entry("m", "warning", 3)])
    result = compare_snapshots(old, new)
    d = result.to_dict()
    assert d["old_timestamp"] == "T1"
    assert d["new_timestamp"] == "T2"
    assert d["changed"] == 1
    assert d["diffs"][0]["direction"] == "degraded"
