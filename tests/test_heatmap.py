"""Tests for pipewatch.heatmap."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pipewatch.heatmap import HeatmapCell, build_heatmap, heatmap_summary
from pipewatch.history import HistoryEntry
from pipewatch.metrics import MetricStatus
from pipewatch.cli_heatmap import heatmap


def _entry(name: str, ts: str, status: str) -> HistoryEntry:
    return HistoryEntry(metric_name=name, timestamp=ts, value=1.0, status=status)


# ---------------------------------------------------------------------------
# HeatmapCell
# ---------------------------------------------------------------------------

def test_dominant_ok():
    cell = HeatmapCell(bucket="2024-01-01", metric_name="m", ok=5, warning=1, critical=0)
    assert cell.dominant == "ok"


def test_dominant_critical():
    cell = HeatmapCell(bucket="2024-01-01", metric_name="m", ok=1, warning=2, critical=9)
    assert cell.dominant == "critical"


def test_to_dict_keys():
    cell = HeatmapCell(bucket="2024-01-01", metric_name="latency", ok=3, warning=0, critical=0)
    d = cell.to_dict()
    assert set(d.keys()) == {"bucket", "metric", "ok", "warning", "critical", "dominant"}


# ---------------------------------------------------------------------------
# build_heatmap
# ---------------------------------------------------------------------------

ENTRIES = [
    _entry("rows", "2024-06-01T10:00:00", "ok"),
    _entry("rows", "2024-06-01T11:00:00", "warning"),
    _entry("rows", "2024-06-02T09:00:00", "critical"),
    _entry("lag",  "2024-06-01T10:30:00", "ok"),
    _entry("lag",  "2024-06-01T14:00:00", "ok"),
]


def test_build_heatmap_day_granularity():
    cells = build_heatmap(ENTRIES, granularity="day")
    buckets = {c.bucket for c in cells}
    assert "2024-06-01" in buckets
    assert "2024-06-02" in buckets


def test_build_heatmap_counts_statuses():
    cells = build_heatmap(ENTRIES, granularity="day")
    rows_day1 = next(c for c in cells if c.metric_name == "rows" and c.bucket == "2024-06-01")
    assert rows_day1.ok == 1
    assert rows_day1.warning == 1


def test_build_heatmap_filter_metric():
    cells = build_heatmap(ENTRIES, granularity="day", metric_name="lag")
    assert all(c.metric_name == "lag" for c in cells)


def test_build_heatmap_hour_granularity():
    cells = build_heatmap(ENTRIES, granularity="hour")
    buckets = {c.bucket for c in cells}
    assert "2024-06-01T10" in buckets
    assert "2024-06-01T11" in buckets


def test_build_heatmap_empty():
    assert build_heatmap([]) == []


# ---------------------------------------------------------------------------
# heatmap_summary
# ---------------------------------------------------------------------------

def test_heatmap_summary_no_data():
    assert "No heatmap data" in heatmap_summary([])


def test_heatmap_summary_contains_metric():
    cells = build_heatmap(ENTRIES, granularity="day")
    summary = heatmap_summary(cells)
    assert "rows" in summary
    assert "lag" in summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_show_text(tmp_path):
    hist_file = tmp_path / "hist.json"
    data = [
        {"metric_name": "rows", "timestamp": "2024-06-01T10:00:00", "value": 1.0, "status": "ok"},
        {"metric_name": "rows", "timestamp": "2024-06-02T10:00:00", "value": 2.0, "status": "critical"},
    ]
    hist_file.write_text(json.dumps(data))
    runner = CliRunner()
    result = runner.invoke(heatmap, ["show", "--history-file", str(hist_file)])
    assert result.exit_code == 0
    assert "rows" in result.output


def test_cli_show_json(tmp_path):
    hist_file = tmp_path / "hist.json"
    data = [
        {"metric_name": "lag", "timestamp": "2024-06-01T08:00:00", "value": 5.0, "status": "warning"},
    ]
    hist_file.write_text(json.dumps(data))
    runner = CliRunner()
    result = runner.invoke(heatmap, ["show", "--history-file", str(hist_file), "--format", "json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert isinstance(parsed, list)
    assert parsed[0]["metric"] == "lag"


def test_cli_show_no_history(tmp_path):
    missing = tmp_path / "nope.json"
    runner = CliRunner()
    result = runner.invoke(heatmap, ["show", "--history-file", str(missing)])
    assert result.exit_code == 0
    assert "No history" in result.output
