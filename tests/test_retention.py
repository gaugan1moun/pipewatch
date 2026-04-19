"""Tests for pipewatch.retention."""
import json
import os
import pytest
from datetime import datetime, timedelta, timezone
from pipewatch.history import HistoryEntry, save_history
from pipewatch.retention import RetentionPolicy, prune_history, retention_summary


def _entry(name: str, days_ago: float, value: float = 1.0) -> HistoryEntry:
    ts = (datetime.now(tz=timezone.utc) - timedelta(days=days_ago)).isoformat()
    return HistoryEntry(metric_name=name, timestamp=ts, value=value, status="ok")


@pytest.fixture
def tmp_hist(tmp_path):
    return str(tmp_path / "history.json")


def test_prune_removes_expired(tmp_hist):
    entries = [_entry("m", 40), _entry("m", 10)]
    save_history(tmp_hist, entries)
    removed = prune_history(tmp_hist, RetentionPolicy(max_age_days=30))
    assert removed == 1


def test_prune_keeps_recent(tmp_hist):
    entries = [_entry("m", 5), _entry("m", 10)]
    save_history(tmp_hist, entries)
    removed = prune_history(tmp_hist, RetentionPolicy(max_age_days=30))
    assert removed == 0


def test_prune_respects_max_entries(tmp_hist):
    entries = [_entry("m", i * 0.1) for i in range(10)]
    save_history(tmp_hist, entries)
    removed = prune_history(tmp_hist, RetentionPolicy(max_age_days=365, max_entries_per_metric=5))
    assert removed == 5


def test_prune_multiple_metrics(tmp_hist):
    entries = [_entry("a", 50), _entry("b", 5), _entry("a", 5)]
    save_history(tmp_hist, entries)
    removed = prune_history(tmp_hist, RetentionPolicy(max_age_days=30))
    assert removed == 1


def test_retention_summary_counts(tmp_hist):
    entries = [_entry("m", 40), _entry("m", 5)]
    save_history(tmp_hist, entries)
    summary = retention_summary(tmp_hist, RetentionPolicy(max_age_days=30))
    assert summary["total_entries"] == 2
    assert summary["expired_entries"] == 1


def test_prune_empty_history(tmp_hist):
    save_history(tmp_hist, [])
    removed = prune_history(tmp_hist)
    assert removed == 0


def test_retention_summary_defaults(tmp_hist):
    save_history(tmp_hist, [])
    summary = retention_summary(tmp_hist)
    assert summary["max_age_days"] == 30
    assert summary["max_entries_per_metric"] == 500
