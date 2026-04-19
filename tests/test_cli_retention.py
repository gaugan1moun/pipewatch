"""Tests for pipewatch.cli_retention."""
import pytest
from click.testing import CliRunner
from datetime import datetime, timedelta, timezone
from pipewatch.history import HistoryEntry, save_history
from pipewatch.cli_retention import retention


def _entry(name, days_ago, value=1.0):
    ts = (datetime.now(tz=timezone.utc) - timedelta(days=days_ago)).isoformat()
    return HistoryEntry(metric_name=name, timestamp=ts, value=value, status="ok")


@pytest.fixture
def runner():
    return CliRunner()


def test_prune_command_output(runner, tmp_path):
    path = str(tmp_path / "h.json")
    save_history(path, [_entry("m", 40), _entry("m", 5)])
    result = runner.invoke(retention, ["prune", "--path", path, "--max-age-days", "30"])
    assert result.exit_code == 0
    assert "Pruned 1 entries" in result.output


def test_status_command_output(runner, tmp_path):
    path = str(tmp_path / "h.json")
    save_history(path, [_entry("m", 5), _entry("m", 10)])
    result = runner.invoke(retention, ["status", "--path", path])
    assert result.exit_code == 0
    assert "Total entries" in result.output
    assert "2" in result.output


def test_prune_empty(runner, tmp_path):
    path = str(tmp_path / "h.json")
    save_history(path, [])
    result = runner.invoke(retention, ["prune", "--path", path])
    assert result.exit_code == 0
    assert "0" in result.output
