"""CLI tests for the circuit breaker commands."""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from pipewatch.cli_circuit_breaker import circuit
from pipewatch.circuit_breaker import (
    save_circuit_state,
    CircuitState,
)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def state_file(tmp_path: Path) -> str:
    return str(tmp_path / "cb.json")


def test_status_empty(runner: CliRunner, state_file: str) -> None:
    result = runner.invoke(circuit, ["status", "--state-file", state_file])
    assert result.exit_code == 0
    assert "No circuit breaker entries found" in result.output


def test_status_shows_entries(runner: CliRunner, state_file: str) -> None:
    state = {
        "pipe_a": CircuitState(
            metric_name="pipe_a",
            failure_count=3,
            tripped=True,
            tripped_at="2024-06-01T00:00:00+00:00",
        )
    }
    save_circuit_state(state, state_file)
    result = runner.invoke(circuit, ["status", "--state-file", state_file])
    assert result.exit_code == 0
    assert "TRIPPED" in result.output
    assert "pipe_a" in result.output


def test_reset_command(runner: CliRunner, state_file: str) -> None:
    state = {
        "pipe_b": CircuitState(metric_name="pipe_b", failure_count=5, tripped=True)
    }
    save_circuit_state(state, state_file)
    result = runner.invoke(circuit, ["reset", "pipe_b", "--state-file", state_file])
    assert result.exit_code == 0
    assert "reset" in result.output.lower()


def test_purge_command(runner: CliRunner, state_file: str) -> None:
    state = {
        "x": CircuitState(metric_name="x", failure_count=1)
    }
    save_circuit_state(state, state_file)
    result = runner.invoke(circuit, ["purge", "--state-file", state_file])
    assert result.exit_code == 0
    assert "purged" in result.output.lower()
    # file should now have empty state
    from pipewatch.circuit_breaker import load_circuit_state
    assert load_circuit_state(state_file) == {}
