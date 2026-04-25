"""Tests for pipewatch.quota."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from pipewatch.quota import (
    QuotaRule,
    QuotaState,
    QuotaResult,
    check_quota,
    load_quota_state,
    save_quota_state,
)


@pytest.fixture
def tmp_quota_path(tmp_path: Path) -> str:
    return str(tmp_path / "quota_state.json")


def _rule(max_violations: int = 3, window: int = 3600) -> QuotaRule:
    return QuotaRule(metric_name="rows_processed", max_violations=max_violations, window_seconds=window)


def test_load_quota_state_missing_file(tmp_quota_path: str) -> None:
    state = load_quota_state(tmp_quota_path)
    assert state == {}


def test_save_and_load_roundtrip(tmp_quota_path: str) -> None:
    state: dict = {}
    entry = state.setdefault("m1", QuotaState(metric_name="m1"))
    entry.record("2024-01-01T00:00:00")
    save_quota_state(state, tmp_quota_path)
    loaded = load_quota_state(tmp_quota_path)
    assert "m1" in loaded
    assert loaded["m1"].count() == 1


def test_no_breach_below_max() -> None:
    rule = _rule(max_violations=3)
    state: dict = {}
    for _ in range(3):
        result = check_quota(rule, "warning", state)
    assert result.violations_in_window == 3
    assert result.breached is False


def test_breach_above_max() -> None:
    rule = _rule(max_violations=2)
    state: dict = {}
    for _ in range(3):
        result = check_quota(rule, "critical", state)
    assert result.breached is True
    assert result.violations_in_window == 3


def test_ok_status_not_counted() -> None:
    rule = _rule(max_violations=2)
    state: dict = {}
    for _ in range(5):
        result = check_quota(rule, "ok", state)
    assert result.violations_in_window == 0
    assert result.breached is False


def test_prune_removes_old_timestamps() -> None:
    entry = QuotaState(metric_name="m")
    old_ts = (datetime.utcnow() - timedelta(seconds=7200)).isoformat()
    entry.violation_timestamps.append(old_ts)
    entry.prune(window_seconds=3600)
    assert entry.count() == 0


def test_prune_keeps_recent_timestamps() -> None:
    entry = QuotaState(metric_name="m")
    entry.record()  # now
    entry.prune(window_seconds=3600)
    assert entry.count() == 1


def test_quota_result_to_dict() -> None:
    r = QuotaResult(
        metric_name="m", breached=True, violations_in_window=4, max_violations=3, window_seconds=60
    )
    d = r.to_dict()
    assert d["breached"] is True
    assert d["violations_in_window"] == 4


def test_custom_status_filter() -> None:
    rule = QuotaRule(
        metric_name="m", max_violations=1, window_seconds=3600, status_filter=["critical"]
    )
    state: dict = {}
    check_quota(rule, "warning", state)  # should NOT count
    result = check_quota(rule, "critical", state)  # should count
    assert result.violations_in_window == 1
