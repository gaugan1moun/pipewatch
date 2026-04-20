"""Tests for pipewatch.cli_rollup CLI commands."""

from __future__ import annotations

import json
import os

import pytest
from click.testing import CliRunner

from pipewatch.cli_rollup import rollup
from pipewatch.history import HistoryEntry, save_history
from pipewatch.metrics import MetricStatus


@pytest.fixture()
def tmp_history(tmp_path):
    path = str(tmp_path / "history.json")
    entries = [
        HistoryEntry(
            metric_name="lag",
            timestamp="2024-06-01T08:00:00",
            status=MetricStatus.OK.value,
            value=1.0,
        ),
        HistoryEntry(
            metric_name="lag",
            timestamp="2024-06-01T14:00:00",
            status=MetricStatus.WARNING.value,
            value=5.0,
        ),
        HistoryEntry(
            metric_name="errors",
            timestamp="2024-06-01T09:00:00",
            status=MetricStatus.CRITICAL.value,
            value=None,
        ),
    ]
    save_history(entries, path)
    return path


def test_show_text_output(tmp_history):
    runner = CliRunner()
    result = runner.invoke(rollup, ["show", "--path", tmp_history])
    assert result.exit_code == 0
    assert "lag" in result.output
    assert "errors" in result.output


def test_show_json_output(tmp_history):
    runner = CliRunner()
    result = runner.invoke(
        rollup, ["show", "--path", tmp_history, "--format", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "lag" in data
    assert isinstance(data["lag"], list)
    assert data["lag"][0]["count"] == 2


def test_show_filter_metric(tmp_history):
    runner = CliRunner()
    result = runner.invoke(
        rollup,
        ["show", "--path", tmp_history, "--metric", "lag", "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "lag" in data
    assert "errors" not in data


def test_show_hour_granularity(tmp_history):
    runner = CliRunner()
    result = runner.invoke(
        rollup,
        ["show", "--path", tmp_history, "--granularity", "hour", "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    # Two different hours for 'lag'
    assert len(data["lag"]) == 2


def test_show_missing_history_file(tmp_path):
    runner = CliRunner()
    missing = str(tmp_path / "no_such.json")
    result = runner.invoke(rollup, ["show", "--path", missing])
    # Should not crash — empty history returns graceful message
    assert result.exit_code == 0
    assert "No rollup" in result.output
