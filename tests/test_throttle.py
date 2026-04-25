"""Tests for pipewatch.throttle."""
import time
import pytest
from pipewatch.throttle import (
    ThrottleEntry,
    check_throttle,
    load_throttle_state,
    save_throttle_state,
)


# ---------------------------------------------------------------------------
# ThrottleEntry unit tests
# ---------------------------------------------------------------------------

def test_entry_not_throttled_after_cooldown():
    now = time.time()
    entry = ThrottleEntry("cpu", last_fired=now - 120, cooldown_seconds=60)
    assert entry.is_throttled(now) is False


def test_entry_throttled_within_cooldown():
    now = time.time()
    entry = ThrottleEntry("cpu", last_fired=now - 10, cooldown_seconds=60)
    assert entry.is_throttled(now) is True


def test_entry_to_dict_roundtrip():
    now = time.time()
    entry = ThrottleEntry("latency", last_fired=now, cooldown_seconds=300)
    restored = ThrottleEntry.from_dict(entry.to_dict())
    assert restored.metric_name == entry.metric_name
    assert restored.last_fired == pytest.approx(entry.last_fired)
    assert restored.cooldown_seconds == entry.cooldown_seconds


# ---------------------------------------------------------------------------
# check_throttle logic
# ---------------------------------------------------------------------------

def test_check_throttle_first_call_allowed():
    state = {}
    suppressed = check_throttle("cpu", cooldown_seconds=60, state=state, now=1000.0)
    assert suppressed is False
    assert "cpu" in state


def test_check_throttle_second_call_suppressed():
    state = {}
    now = 1000.0
    check_throttle("cpu", cooldown_seconds=60, state=state, now=now)
    suppressed = check_throttle("cpu", cooldown_seconds=60, state=state, now=now + 30)
    assert suppressed is True


def test_check_throttle_allowed_after_cooldown_expires():
    state = {}
    now = 1000.0
    check_throttle("cpu", cooldown_seconds=60, state=state, now=now)
    suppressed = check_throttle("cpu", cooldown_seconds=60, state=state, now=now + 61)
    assert suppressed is False


def test_check_throttle_independent_metrics():
    state = {}
    now = 1000.0
    check_throttle("cpu", cooldown_seconds=60, state=state, now=now)
    suppressed_cpu = check_throttle("cpu", cooldown_seconds=60, state=state, now=now + 5)
    suppressed_mem = check_throttle("mem", cooldown_seconds=60, state=state, now=now + 5)
    assert suppressed_cpu is True
    assert suppressed_mem is False


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "throttle.json")
    now = time.time()
    state = {
        "errors": ThrottleEntry("errors", last_fired=now, cooldown_seconds=120)
    }
    save_throttle_state(state, path=path)
    loaded = load_throttle_state(path=path)
    assert "errors" in loaded
    assert loaded["errors"].cooldown_seconds == 120
    assert loaded["errors"].last_fired == pytest.approx(now)


def test_load_throttle_state_missing_file(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    state = load_throttle_state(path=path)
    assert state == {}
