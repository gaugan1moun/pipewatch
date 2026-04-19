"""Tests for pipewatch.escalation."""
import pytest
from pathlib import Path
from pipewatch.escalation import (
    EscalationEntry,
    load_escalation_state,
    save_escalation_state,
    evaluate_escalation,
)


@pytest.fixture
def tmp_path_esc(tmp_path):
    return tmp_path / "escalation_state.json"


def test_load_missing_file(tmp_path_esc):
    assert load_escalation_state(tmp_path_esc) == []


def test_save_and_load_roundtrip(tmp_path_esc):
    entries = [EscalationEntry(metric_name="row_count", consecutive_failures=2, last_escalated=None)]
    save_escalation_state(entries, tmp_path_esc)
    loaded = load_escalation_state(tmp_path_esc)
    assert len(loaded) == 1
    assert loaded[0].metric_name == "row_count"
    assert loaded[0].consecutive_failures == 2


def test_no_escalation_below_threshold():
    entries = []
    for _ in range(2):
        entries, should = evaluate_escalation("m", True, entries, threshold=3)
    assert not should
    assert entries[0].consecutive_failures == 2


def test_escalation_at_threshold():
    entries = []
    should = False
    for _ in range(3):
        entries, should = evaluate_escalation("m", True, entries, threshold=3)
    assert should
    assert entries[0].last_escalated is not None


def test_reset_on_recovery():
    entries = [EscalationEntry(metric_name="m", consecutive_failures=5)]
    entries, should = evaluate_escalation("m", False, entries, threshold=3)
    assert not should
    assert entries[0].consecutive_failures == 0


def test_new_entry_created_for_unknown_metric():
    entries = []
    entries, _ = evaluate_escalation("new_metric", True, entries, threshold=3)
    assert any(e.metric_name == "new_metric" for e in entries)


def test_multiple_metrics_independent():
    entries = []
    for _ in range(3):
        entries, _ = evaluate_escalation("a", True, entries, threshold=3)
    entries, should_b = evaluate_escalation("b", True, entries, threshold=3)
    assert not should_b
    a_entry = next(e for e in entries if e.metric_name == "a")
    assert a_entry.consecutive_failures == 3
