"""Tests for pipewatch.deduplicator."""

import pytest
from pathlib import Path

from pipewatch.deduplicator import (
    DeduplicatorEntry,
    load_dedup_state,
    save_dedup_state,
    is_duplicate,
    record_alert,
    reset_metric,
)


@pytest.fixture
def tmp_dedup_path(tmp_path: Path) -> Path:
    return tmp_path / "dedup_state.json"


def test_load_dedup_state_missing_file(tmp_dedup_path: Path):
    state = load_dedup_state(tmp_dedup_path)
    assert state == {}


def test_save_and_load_roundtrip(tmp_dedup_path: Path):
    state = {}
    record_alert("row_count", "WARNING", state)
    save_dedup_state(state, tmp_dedup_path)
    loaded = load_dedup_state(tmp_dedup_path)
    assert "row_count" in loaded
    assert loaded["row_count"].last_status == "WARNING"
    assert loaded["row_count"].alert_count == 1


def test_is_duplicate_no_entry():
    state = {}
    assert is_duplicate("latency", "CRITICAL", state) is False


def test_is_duplicate_same_status():
    state = {}
    record_alert("latency", "CRITICAL", state)
    assert is_duplicate("latency", "CRITICAL", state) is True


def test_is_duplicate_different_status():
    state = {}
    record_alert("latency", "WARNING", state)
    assert is_duplicate("latency", "CRITICAL", state) is False


def test_record_alert_increments_count():
    state = {}
    record_alert("row_count", "WARNING", state)
    record_alert("row_count", "WARNING", state)
    assert state["row_count"].alert_count == 2


def test_record_alert_resets_count_on_status_change():
    state = {}
    record_alert("row_count", "WARNING", state)
    record_alert("row_count", "CRITICAL", state)
    assert state["row_count"].alert_count == 1
    assert state["row_count"].last_status == "CRITICAL"


def test_reset_metric_removes_entry():
    state = {}
    record_alert("freshness", "WARNING", state)
    assert "freshness" in state
    reset_metric("freshness", state)
    assert "freshness" not in state


def test_reset_metric_missing_key_is_safe():
    state = {}
    reset_metric("nonexistent", state)  # should not raise


def test_entry_to_dict_and_from_dict():
    entry = DeduplicatorEntry(metric_name="foo", last_status="CRITICAL", alert_count=3)
    d = entry.to_dict()
    restored = DeduplicatorEntry.from_dict(d)
    assert restored.metric_name == "foo"
    assert restored.last_status == "CRITICAL"
    assert restored.alert_count == 3
