"""Tests for pipewatch.rollup."""

from __future__ import annotations

from pipewatch.history import HistoryEntry
from pipewatch.metrics import MetricStatus
from pipewatch.rollup import (
    RollupBucket,
    _bucket_label,
    rollup_history,
    rollup_summary,
)


def _entry(
    name: str,
    ts: str,
    status: str = MetricStatus.OK.value,
    value: float | None = None,
) -> HistoryEntry:
    return HistoryEntry(metric_name=name, timestamp=ts, status=status, value=value)


# ---------------------------------------------------------------------------
# _bucket_label
# ---------------------------------------------------------------------------

def test_bucket_label_day():
    assert _bucket_label("2024-06-15T10:30:00", "day") == "2024-06-15"


def test_bucket_label_hour():
    assert _bucket_label("2024-06-15T10:30:00", "hour") == "2024-06-15T10"


def test_bucket_label_invalid_ts():
    # Falls back to first 10 chars
    assert _bucket_label("2024-06-15", "day") == "2024-06-15"


# ---------------------------------------------------------------------------
# rollup_history
# ---------------------------------------------------------------------------

def test_empty_entries_returns_empty():
    assert rollup_history([]) == {}


def test_single_entry_creates_bucket():
    entries = [_entry("lag", "2024-06-01T08:00:00", MetricStatus.OK.value, 1.0)]
    rollups = rollup_history(entries, granularity="day")
    assert "lag" in rollups
    assert len(rollups["lag"]) == 1
    b = rollups["lag"][0]
    assert b.count == 1
    assert b.ok_count == 1
    assert b.avg_value == 1.0


def test_multiple_entries_same_bucket():
    entries = [
        _entry("lag", "2024-06-01T08:00:00", MetricStatus.OK.value, 2.0),
        _entry("lag", "2024-06-01T12:00:00", MetricStatus.WARNING.value, 4.0),
        _entry("lag", "2024-06-01T18:00:00", MetricStatus.CRITICAL.value, 6.0),
    ]
    rollups = rollup_history(entries, granularity="day")
    b = rollups["lag"][0]
    assert b.count == 3
    assert b.ok_count == 1
    assert b.warning_count == 1
    assert b.critical_count == 1
    assert abs(b.avg_value - 4.0) < 1e-9
    assert b.min_value == 2.0
    assert b.max_value == 6.0


def test_multiple_buckets_sorted():
    entries = [
        _entry("lag", "2024-06-03T00:00:00"),
        _entry("lag", "2024-06-01T00:00:00"),
        _entry("lag", "2024-06-02T00:00:00"),
    ]
    rollups = rollup_history(entries, granularity="day")
    labels = [b.bucket_label for b in rollups["lag"]]
    assert labels == sorted(labels)


def test_multiple_metrics_separated():
    entries = [
        _entry("lag", "2024-06-01T00:00:00"),
        _entry("errors", "2024-06-01T00:00:00"),
    ]
    rollups = rollup_history(entries)
    assert "lag" in rollups
    assert "errors" in rollups


def test_none_value_no_avg():
    entries = [_entry("lag", "2024-06-01T00:00:00", MetricStatus.OK.value, None)]
    rollups = rollup_history(entries)
    b = rollups["lag"][0]
    assert b.avg_value is None
    assert b.min_value is None
    assert b.max_value is None


def test_hour_granularity_splits_same_day():
    entries = [
        _entry("lag", "2024-06-01T08:00:00"),
        _entry("lag", "2024-06-01T09:00:00"),
    ]
    rollups = rollup_history(entries, granularity="hour")
    assert len(rollups["lag"]) == 2


# ---------------------------------------------------------------------------
# rollup_summary
# ---------------------------------------------------------------------------

def test_rollup_summary_empty():
    assert "No rollup" in rollup_summary({})


def test_rollup_summary_contains_metric_name():
    entries = [_entry("lag", "2024-06-01T00:00:00", MetricStatus.OK.value, 3.0)]
    rollups = rollup_history(entries)
    summary = rollup_summary(rollups)
    assert "lag" in summary
    assert "count=1" in summary


def test_to_dict_keys():
    b = RollupBucket(metric_name="x", bucket_label="2024-06-01", count=2)
    d = b.to_dict()
    for key in ("metric_name", "bucket_label", "count", "ok_count",
                "warning_count", "critical_count", "avg_value"):
        assert key in d
