"""Tests for pipewatch.profiler."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from pipewatch.history import HistoryEntry
from pipewatch.profiler import MetricProfile, profile_all, profile_metric
from pipewatch.cli_profiler import profiler


def _entry(name: str, value: float, ts: str = "2024-01-01T00:00:00") -> HistoryEntry:
    return HistoryEntry(metric_name=name, value=value, status="ok", timestamp=ts)


# ---------------------------------------------------------------------------
# profile_metric
# ---------------------------------------------------------------------------

def test_returns_none_for_unknown_metric():
    entries = [_entry("cpu", 10.0)]
    assert profile_metric("memory", entries) is None


def test_single_entry_profile():
    entries = [_entry("cpu", 42.0)]
    p = profile_metric("cpu", entries)
    assert p is not None
    assert p.count == 1
    assert p.min_value == 42.0
    assert p.max_value == 42.0
    assert p.avg_value == 42.0
    assert p.p50 == 42.0
    assert p.p95 == 42.0


def test_multiple_entries_stats():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    entries = [_entry("cpu", v) for v in values]
    p = profile_metric("cpu", entries)
    assert p.count == 5
    assert p.min_value == 1.0
    assert p.max_value == 5.0
    assert abs(p.avg_value - 3.0) < 1e-6


def test_window_limits_entries():
    entries = [_entry("cpu", float(i)) for i in range(10)]
    p = profile_metric("cpu", entries, window=3)
    # last 3 values: 7, 8, 9
    assert p.count == 3
    assert p.min_value == 7.0
    assert p.max_value == 9.0


def test_to_dict_keys():
    entries = [_entry("cpu", 5.0)]
    p = profile_metric("cpu", entries)
    d = p.to_dict()
    for key in ("metric_name", "count", "min", "max", "avg", "p50", "p95"):
        assert key in d


# ---------------------------------------------------------------------------
# profile_all
# ---------------------------------------------------------------------------

def test_profile_all_returns_all_metrics():
    entries = [
        _entry("cpu", 10.0),
        _entry("memory", 20.0),
        _entry("cpu", 30.0),
    ]
    profiles = profile_all(entries)
    names = {p.metric_name for p in profiles}
    assert names == {"cpu", "memory"}


def test_profile_all_empty():
    assert profile_all([]) == []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_show_text(tmp_path):
    from pipewatch.history import save_history
    hist_file = str(tmp_path / "hist.json")
    entries = [_entry("latency", float(i)) for i in range(5)]
    save_history(hist_file, entries)

    runner = CliRunner()
    result = runner.invoke(profiler, ["show", "--history-file", hist_file])
    assert result.exit_code == 0
    assert "latency" in result.output


def test_cli_show_json(tmp_path):
    import json as _json
    from pipewatch.history import save_history
    hist_file = str(tmp_path / "hist.json")
    entries = [_entry("latency", float(i)) for i in range(5)]
    save_history(hist_file, entries)

    runner = CliRunner()
    result = runner.invoke(profiler, ["show", "--history-file", hist_file, "--format", "json"])
    assert result.exit_code == 0
    data = _json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["metric_name"] == "latency"


def test_cli_show_no_data(tmp_path):
    from pipewatch.history import save_history
    hist_file = str(tmp_path / "hist.json")
    save_history(hist_file, [])

    runner = CliRunner()
    result = runner.invoke(profiler, ["show", "--history-file", hist_file])
    assert result.exit_code == 0
    assert "No profile data" in result.output
