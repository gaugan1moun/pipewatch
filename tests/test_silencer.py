"""Tests for pipewatch.silencer."""
import json
import os
from datetime import datetime, timedelta

import pytest

from pipewatch.silencer import (
    SilenceRule,
    add_silence,
    is_silenced,
    load_silences,
    purge_expired,
    save_silences,
)


@pytest.fixture
def tmp_silence_path(tmp_path):
    return str(tmp_path / "silences.json")


def test_load_silences_missing_file(tmp_silence_path):
    assert load_silences(tmp_silence_path) == []


def test_save_and_load_roundtrip(tmp_silence_path):
    future = datetime.utcnow() + timedelta(hours=1)
    rule = SilenceRule(metric_name="row_count", reason="planned maintenance", expires_at=future)
    save_silences(tmp_silence_path, [rule])
    loaded = load_silences(tmp_silence_path)
    assert len(loaded) == 1
    assert loaded[0].metric_name == "row_count"
    assert loaded[0].reason == "planned maintenance"


def test_silence_rule_active(tmp_silence_path):
    future = datetime.utcnow() + timedelta(hours=1)
    rule = SilenceRule("m", "r", future)
    assert rule.is_active() is True


def test_silence_rule_expired():
    past = datetime.utcnow() - timedelta(minutes=1)
    rule = SilenceRule("m", "r", past)
    assert rule.is_active() is False


def test_add_silence_creates_rule(tmp_silence_path):
    rule = add_silence(tmp_silence_path, "latency", "deploy", 60)
    assert rule.metric_name == "latency"
    loaded = load_silences(tmp_silence_path)
    assert len(loaded) == 1


def test_is_silenced_true(tmp_silence_path):
    add_silence(tmp_silence_path, "latency", "deploy", 60)
    assert is_silenced(tmp_silence_path, "latency") is True


def test_is_silenced_false(tmp_silence_path):
    assert is_silenced(tmp_silence_path, "latency") is False


def test_is_silenced_expired(tmp_silence_path):
    past = datetime.utcnow() - timedelta(minutes=5)
    rule = SilenceRule("latency", "old", past)
    save_silences(tmp_silence_path, [rule])
    assert is_silenced(tmp_silence_path, "latency") is False


def test_purge_expired_removes_old(tmp_silence_path):
    past = datetime.utcnow() - timedelta(minutes=1)
    future = datetime.utcnow() + timedelta(hours=1)
    rules = [
        SilenceRule("a", "r", past),
        SilenceRule("b", "r", future),
    ]
    save_silences(tmp_silence_path, rules)
    removed = purge_expired(tmp_silence_path)
    assert removed == 1
    assert len(load_silences(tmp_silence_path)) == 1
