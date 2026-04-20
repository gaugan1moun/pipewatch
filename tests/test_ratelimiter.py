"""Tests for pipewatch.ratelimiter."""
import json
import time

import pytest

from pipewatch.ratelimiter import (
    RateLimitEntry,
    check_rate_limit,
    load_rate_limit_state,
    save_rate_limit_state,
)


# ---------------------------------------------------------------------------
# RateLimitEntry unit tests
# ---------------------------------------------------------------------------

def test_entry_allows_up_to_max():
    entry = RateLimitEntry("rows", "log", window_seconds=60, max_alerts=3)
    now = time.time()
    assert entry.is_allowed(now)
    entry.record(now)
    assert entry.is_allowed(now)
    entry.record(now)
    assert entry.is_allowed(now)
    entry.record(now)
    assert not entry.is_allowed(now)  # 3 already recorded


def test_entry_prunes_old_timestamps():
    entry = RateLimitEntry("rows", "log", window_seconds=10, max_alerts=2)
    old = time.time() - 20
    entry.timestamps = [old, old]  # both outside window
    assert entry.is_allowed()  # pruned → 0 in window


def test_entry_to_dict_roundtrip():
    entry = RateLimitEntry("rows", "email", 120, 5, [1.0, 2.0])
    restored = RateLimitEntry.from_dict(entry.to_dict())
    assert restored.metric_name == entry.metric_name
    assert restored.channel == entry.channel
    assert restored.timestamps == entry.timestamps


# ---------------------------------------------------------------------------
# check_rate_limit helper
# ---------------------------------------------------------------------------

def test_check_rate_limit_first_call_allowed():
    state = {}
    assert check_rate_limit(state, "lag", "log", window_seconds=60, max_alerts=2)


def test_check_rate_limit_blocks_after_max():
    state = {}
    now = time.time()
    assert check_rate_limit(state, "lag", "log", 60, 2, now)
    assert check_rate_limit(state, "lag", "log", 60, 2, now)
    assert not check_rate_limit(state, "lag", "log", 60, 2, now)


def test_check_rate_limit_different_channels_independent():
    state = {}
    now = time.time()
    check_rate_limit(state, "lag", "log", 60, 1, now)
    assert not check_rate_limit(state, "lag", "log", 60, 1, now)
    # email channel should still be allowed
    assert check_rate_limit(state, "lag", "email", 60, 1, now)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "rl.json"
    state = {}
    now = time.time()
    check_rate_limit(state, "errors", "log", 300, 5, now)
    save_rate_limit_state(state, path)
    loaded = load_rate_limit_state(path)
    assert "errors::log" in loaded
    assert len(loaded["errors::log"].timestamps) == 1


def test_load_missing_file_returns_empty(tmp_path):
    result = load_rate_limit_state(tmp_path / "nonexistent.json")
    assert result == {}
