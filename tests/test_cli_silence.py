"""Tests for CLI silence commands."""
import os
from click.testing import CliRunner
from pipewatch.cli_silence import silence


def _path(tmp_path):
    return str(tmp_path / "silences.json")


def test_add_silence_cli(tmp_path):
    runner = CliRunner()
    result = runner.invoke(silence, ["add", "row_count", "--duration", "30", "--path", _path(tmp_path)])
    assert result.exit_code == 0
    assert "row_count" in result.output
    assert "Silenced" in result.output


def test_list_silences_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(silence, ["list", "--path", _path(tmp_path)])
    assert result.exit_code == 0
    assert "No active silences" in result.output


def test_list_silences_shows_entry(tmp_path):
    runner = CliRunner()
    path = _path(tmp_path)
    runner.invoke(silence, ["add", "latency", "--reason", "deploy", "--path", path])
    result = runner.invoke(silence, ["list", "--path", path])
    assert "latency" in result.output
    assert "deploy" in result.output


def test_purge_cli(tmp_path):
    runner = CliRunner()
    result = runner.invoke(silence, ["purge", "--path", _path(tmp_path)])
    assert result.exit_code == 0
    assert "Purged" in result.output


def test_check_not_silenced(tmp_path):
    runner = CliRunner()
    result = runner.invoke(silence, ["check", "row_count", "--path", _path(tmp_path)])
    assert "NOT silenced" in result.output


def test_check_silenced(tmp_path):
    runner = CliRunner()
    path = _path(tmp_path)
    runner.invoke(silence, ["add", "row_count", "--path", path])
    result = runner.invoke(silence, ["check", "row_count", "--path", path])
    assert "currently silenced" in result.output


def test_add_multiple_silences_list_shows_all(tmp_path):
    """Adding multiple silences should show all entries in list output."""
    runner = CliRunner()
    path = _path(tmp_path)
    runner.invoke(silence, ["add", "row_count", "--reason", "maintenance", "--path", path])
    runner.invoke(silence, ["add", "latency", "--reason", "deploy", "--path", path])
    result = runner.invoke(silence, ["list", "--path", path])
    assert result.exit_code == 0
    assert "row_count" in result.output
    assert "latency" in result.output
