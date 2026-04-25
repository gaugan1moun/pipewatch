"""CLI tests for pipewatch.cli_quota."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from pipewatch.cli_quota import quota


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def state_file(tmp_path: Path) -> str:
    return str(tmp_path / "quota.json")


def test_check_ok_output(runner: CliRunner, state_file: str) -> None:
    result = runner.invoke(
        quota,
        ["check", "my_metric", "warning", "--max-violations", "5", "--state-file", state_file],
    )
    assert result.exit_code == 0
    assert "my_metric" in result.output
    assert "1/5" in result.output


def test_check_breached_output(runner: CliRunner, state_file: str) -> None:
    for _ in range(4):
        runner.invoke(
            quota,
            ["check", "m", "critical", "--max-violations", "3", "--state-file", state_file],
        )
    result = runner.invoke(
        quota,
        ["check", "m", "critical", "--max-violations", "3", "--state-file", state_file],
    )
    assert "BREACHED" in result.output


def test_status_empty(runner: CliRunner, state_file: str) -> None:
    result = runner.invoke(quota, ["status", "--state-file", state_file])
    assert result.exit_code == 0
    assert "No quota state" in result.output


def test_status_shows_entry(runner: CliRunner, state_file: str) -> None:
    runner.invoke(quota, ["check", "pipe_a", "warning", "--state-file", state_file])
    result = runner.invoke(quota, ["status", "--state-file", state_file])
    assert "pipe_a" in result.output


def test_status_json_flag(runner: CliRunner, state_file: str) -> None:
    runner.invoke(quota, ["check", "pipe_b", "critical", "--state-file", state_file])
    result = runner.invoke(quota, ["status", "--state-file", state_file, "--json"])
    assert result.exit_code == 0
    assert "pipe_b" in result.output
    assert "violation_timestamps" in result.output


def test_reset_existing(runner: CliRunner, state_file: str) -> None:
    runner.invoke(quota, ["check", "pipe_c", "critical", "--state-file", state_file])
    result = runner.invoke(quota, ["reset", "pipe_c", "--state-file", state_file])
    assert result.exit_code == 0
    assert "reset" in result.output.lower()


def test_reset_missing(runner: CliRunner, state_file: str) -> None:
    result = runner.invoke(quota, ["reset", "ghost_metric", "--state-file", state_file])
    assert result.exit_code == 0
    assert "No quota state found" in result.output
