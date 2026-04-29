"""Tests for pipewatch.correlator."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import pytest
from click.testing import CliRunner

from pipewatch.correlator import (
    CorrelationResult,
    _pearson,
    correlate_metrics,
    correlation_summary,
)
from pipewatch.history import HistoryEntry
from pipewatch.cli_correlator import correlate


def _entry(name: str, status: str, offset_minutes: int = 0) -> HistoryEntry:
    ts = (datetime(2024, 1, 1) + timedelta(minutes=offset_minutes)).isoformat()
    return HistoryEntry(metric_name=name, status=status, value=0.0, timestamp=ts)


def _paired_entries(n: int, status_a: List[str], status_b: List[str]) -> List[HistoryEntry]:
    entries = []
    for i in range(n):
        entries.append(_entry("alpha", status_a[i], i))
        entries.append(_entry("beta", status_b[i], i))
    return entries


# --- unit: _pearson ---

def test_pearson_perfect_positive():
    r = _pearson([0, 1, 2], [0, 1, 2])
    assert r == pytest.approx(1.0)


def test_pearson_perfect_negative():
    r = _pearson([0, 1, 2], [2, 1, 0])
    assert r == pytest.approx(-1.0)


def test_pearson_no_variance_returns_none():
    assert _pearson([1, 1, 1], [0, 1, 2]) is None


def test_pearson_too_short_returns_none():
    assert _pearson([1], [1]) is None


# --- correlate_metrics ---

def test_no_correlation_below_threshold():
    # alternating statuses → low correlation
    statuses_a = ["ok", "critical", "ok", "critical", "ok", "critical"]
    statuses_b = ["critical", "ok", "critical", "ok", "critical", "ok"]
    entries = _paired_entries(6, statuses_a, statuses_b)
    results = correlate_metrics(entries, min_samples=5, threshold=0.6)
    assert results == []


def test_strong_positive_correlation_detected():
    statuses = ["ok", "ok", "warning", "warning", "critical", "critical"]
    entries = _paired_entries(6, statuses, statuses)
    results = correlate_metrics(entries, min_samples=5, threshold=0.6)
    assert len(results) == 1
    assert results[0].metric_a == "alpha"
    assert results[0].metric_b == "beta"
    assert results[0].coefficient == pytest.approx(1.0)


def test_insufficient_samples_skipped():
    statuses = ["ok", "critical", "ok"]
    entries = _paired_entries(3, statuses, statuses)
    results = correlate_metrics(entries, min_samples=5, threshold=0.6)
    assert results == []


def test_results_sorted_by_abs_coefficient():
    # alpha-beta: perfect correlation; alpha-gamma: weaker
    entries = []
    for i, (sa, sb, sc) in enumerate([
        ("ok", "ok", "warning"),
        ("ok", "ok", "ok"),
        ("warning", "warning", "warning"),
        ("critical", "critical", "ok"),
        ("critical", "critical", "critical"),
    ]):
        entries.append(_entry("alpha", sa, i))
        entries.append(_entry("beta", sb, i))
        entries.append(_entry("gamma", sc, i))
    results = correlate_metrics(entries, min_samples=5, threshold=0.0)
    coefficients = [abs(r.coefficient) for r in results]
    assert coefficients == sorted(coefficients, reverse=True)


# --- correlation_summary ---

def test_summary_empty():
    assert "No significant" in correlation_summary([])


def test_summary_contains_metric_names():
    r = CorrelationResult("alpha", "beta", 0.95, 10)
    out = correlation_summary([r])
    assert "alpha" in out
    assert "beta" in out


# --- CLI ---

def test_cli_show_no_history(tmp_path):
    runner = CliRunner()
    result = runner.invoke(correlate, ["show", "--history-file", str(tmp_path / "nope.json")])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_cli_show_json_output(tmp_path):
    import json as _json
    from pipewatch.history import save_history

    statuses = ["ok", "ok", "warning", "warning", "critical", "critical"]
    entries = _paired_entries(6, statuses, statuses)
    hist_path = tmp_path / "h.json"
    save_history(str(hist_path), entries)

    runner = CliRunner()
    result = runner.invoke(
        correlate,
        ["show", "--history-file", str(hist_path), "--format", "json", "--min-samples", "5"],
    )
    assert result.exit_code == 0
    data = _json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["metric_a"] == "alpha"
