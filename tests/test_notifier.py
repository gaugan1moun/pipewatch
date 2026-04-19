"""Tests for pipewatch.notifier."""
import json
import time
import pytest
from pathlib import Path
from pipewatch.notifier import (
    NotifierState,
    load_state,
    save_state,
    should_notify,
    mark_notified,
    purge_expired,
)


@pytest.fixture
def tmp_state_path(tmp_path):
    return tmp_path / "notifier_state.json"


def test_load_state_missing_file(tmp_state_path):
    state = load_state(tmp_state_path)
    assert state.last_notified == {}


def test_save_and_load_roundtrip(tmp_state_path):
    state = NotifierState()
    mark_notified("my_metric", state, ts=1000.0)
    save_state(state, tmp_state_path)
    loaded = load_state(tmp_state_path)
    assert loaded.last_notified["my_metric"] == pytest.approx(1000.0)


def test_should_notify_first_time():
    state = NotifierState()
    assert should_notify("metric_a", state, cooldown=300) is True


def test_should_notify_within_cooldown():
    state = NotifierState()
    mark_notified("metric_a", state, ts=time.time())
    assert should_notify("metric_a", state, cooldown=300) is False


def test_should_notify_after_cooldown():
    state = NotifierState()
    mark_notified("metric_a", state, ts=time.time() - 400)
    assert should_notify("metric_a", state, cooldown=300) is True


def test_mark_notified_updates_timestamp():
    state = NotifierState()
    before = time.time()
    mark_notified("metric_b", state)
    after = time.time()
    assert before <= state.last_notified["metric_b"] <= after


def test_purge_expired_removes_old():
    state = NotifierState()
    mark_notified("old", state, ts=time.time() - 400)
    mark_notified("fresh", state, ts=time.time())
    removed = purge_expired(state, cooldown=300)
    assert removed == 1
    assert "old" not in state.last_notified
    assert "fresh" in state.last_notified


def test_load_state_corrupt_file(tmp_state_path):
    tmp_state_path.write_text("not json")
    state = load_state(tmp_state_path)
    assert state.last_notified == {}
