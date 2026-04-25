"""Tests for pipewatch.circuit_breaker."""

import json
import pytest
from pathlib import Path

from pipewatch.circuit_breaker import (
    CircuitState,
    load_circuit_state,
    save_circuit_state,
    record_failure,
    reset_circuit,
    is_tripped,
)


@pytest.fixture()
def tmp_cb_path(tmp_path: Path) -> str:
    return str(tmp_path / "cb.json")


def test_load_circuit_state_missing_file(tmp_cb_path: str) -> None:
    state = load_circuit_state(tmp_cb_path)
    assert state == {}


def test_save_and_load_roundtrip(tmp_cb_path: str) -> None:
    state: dict = {}
    record_failure("my_metric", state, threshold=3, now="2024-01-01T00:00:00+00:00")
    save_circuit_state(state, tmp_cb_path)
    loaded = load_circuit_state(tmp_cb_path)
    assert "my_metric" in loaded
    assert loaded["my_metric"].failure_count == 1
    assert loaded["my_metric"].tripped is False


def test_no_trip_below_threshold() -> None:
    state: dict = {}
    for _ in range(2):
        record_failure("m", state, threshold=3)
    assert not is_tripped("m", state)
    assert state["m"].failure_count == 2


def test_trips_at_threshold() -> None:
    state: dict = {}
    for _ in range(3):
        record_failure("m", state, threshold=3, now="2024-06-01T12:00:00+00:00")
    assert is_tripped("m", state)
    assert state["m"].tripped_at == "2024-06-01T12:00:00+00:00"


def test_no_extra_increments_after_trip() -> None:
    state: dict = {}
    for _ in range(5):
        record_failure("m", state, threshold=3)
    assert state["m"].failure_count == 3


def test_reset_clears_state() -> None:
    state: dict = {}
    for _ in range(3):
        record_failure("m", state, threshold=3)
    assert is_tripped("m", state)
    reset_circuit("m", state)
    assert not is_tripped("m", state)
    assert state["m"].failure_count == 0


def test_is_tripped_unknown_metric() -> None:
    assert not is_tripped("unknown", {})


def test_circuit_state_to_dict_from_dict() -> None:
    cs = CircuitState(
        metric_name="x", failure_count=2, tripped=True, tripped_at="2024-01-01T00:00:00"
    )
    restored = CircuitState.from_dict(cs.to_dict())
    assert restored.metric_name == "x"
    assert restored.failure_count == 2
    assert restored.tripped is True
    assert restored.tripped_at == "2024-01-01T00:00:00"
