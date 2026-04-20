"""Tests for pipewatch.cli_ratelimiter CLI commands."""
import time

import pytest
from click.testing import CliRunner

from pipewatch.cli_ratelimiter import ratelimit
from pipewatch.ratelimiter import check_rate_limit, save_rate_limit_state


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def state_file(tmp_path):
    return str(tmp_path / "rl_test.json")


def test_status_empty(runner, state_file):
    result = runner.invoke(ratelimit, ["status", "--state-file", state_file])
    assert result.exit_code == 0
    assert "No rate-limit state" in result.output


def test_status_shows_entries(runner, state_file, tmp_path):
    path = tmp_path / "rl_test.json"
    state = {}
    check_rate_limit(state, "row_count", "log", 300, 3, time.time())
    save_rate_limit_state(state, path)
    result = runner.invoke(ratelimit, ["status", "--state-file", str(path)])
    assert result.exit_code == 0
    assert "row_count::log" in result.output


def test_reset_removes_entry(runner, tmp_path):
    path = tmp_path / "rl_test.json"
    state = {}
    check_rate_limit(state, "lag", "email", 60, 2, time.time())
    save_rate_limit_state(state, path)

    result = runner.invoke(
        ratelimit, ["reset", "lag", "email", "--state-file", str(path)]
    )
    assert result.exit_code == 0
    assert "Reset" in result.output

    from pipewatch.ratelimiter import load_rate_limit_state
    loaded = load_rate_limit_state(path)
    assert "lag::email" not in loaded


def test_reset_missing_entry(runner, state_file):
    result = runner.invoke(
        ratelimit, ["reset", "ghost", "log", "--state-file", state_file]
    )
    assert result.exit_code == 0
    assert "No entry found" in result.output


def test_purge_clears_all(runner, tmp_path):
    path = tmp_path / "rl_test.json"
    state = {}
    check_rate_limit(state, "a", "log", 60, 1, time.time())
    check_rate_limit(state, "b", "log", 60, 1, time.time())
    save_rate_limit_state(state, path)

    result = runner.invoke(ratelimit, ["purge", "--state-file", str(path)])
    assert result.exit_code == 0
    assert "purged" in result.output.lower()

    from pipewatch.ratelimiter import load_rate_limit_state
    assert load_rate_limit_state(path) == {}
