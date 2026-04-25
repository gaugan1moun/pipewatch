"""Tests for pipewatch.watchdog staleness detection."""

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pipewatch.snapshot import Snapshot
from pipewatch.watchdog import check_staleness, watchdog_summary, WatchdogReport
from pipewatch.cli_watchdog import watchdog


FIXED_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _snap(age_seconds: float) -> Snapshot:
    ts = (FIXED_NOW - timedelta(seconds=age_seconds)).isoformat()
    return Snapshot(
        timestamp=ts,
        metrics=[
            {"name": "row_count", "value": 100, "status": "ok"},
            {"name": "latency_ms", "value": 42, "status": "warning"},
        ],
    )


@patch("pipewatch.watchdog._now", return_value=FIXED_NOW)
def test_no_stale_metrics_within_ttl(mock_now):
    snap = _snap(age_seconds=60)
    report = check_staleness(snap, ttl_seconds=300)
    assert len(report.results) == 2
    assert all(not r.is_stale for r in report.results)
    assert len(report.stale_metrics) == 0


@patch("pipewatch.watchdog._now", return_value=FIXED_NOW)
def test_stale_metrics_beyond_ttl(mock_now):
    snap = _snap(age_seconds=400)
    report = check_staleness(snap, ttl_seconds=300)
    assert all(r.is_stale for r in report.results)
    assert len(report.stale_metrics) == 2


@patch("pipewatch.watchdog._now", return_value=FIXED_NOW)
def test_age_seconds_calculated_correctly(mock_now):
    snap = _snap(age_seconds=120)
    report = check_staleness(snap, ttl_seconds=300)
    for r in report.results:
        assert r.age_seconds == pytest.approx(120.0, abs=0.1)


@patch("pipewatch.watchdog._now", return_value=FIXED_NOW)
def test_invalid_timestamp_marks_stale(mock_now):
    snap = Snapshot(
        timestamp="not-a-timestamp",
        metrics=[{"name": "x", "value": 1, "status": "ok"}],
    )
    report = check_staleness(snap, ttl_seconds=300)
    assert report.results[0].is_stale is True
    assert report.results[0].age_seconds is None


@patch("pipewatch.watchdog._now", return_value=FIXED_NOW)
def test_to_dict_structure(mock_now):
    snap = _snap(age_seconds=50)
    report = check_staleness(snap, ttl_seconds=300)
    d = report.to_dict()
    assert "checked_at" in d
    assert "ttl_seconds" in d
    assert "results" in d
    assert d["stale_count"] == 0


@patch("pipewatch.watchdog._now", return_value=FIXED_NOW)
def test_watchdog_summary_contains_metric_names(mock_now):
    snap = _snap(age_seconds=50)
    report = check_staleness(snap, ttl_seconds=300)
    summary = watchdog_summary(report)
    assert "row_count" in summary
    assert "latency_ms" in summary
    assert "OK" in summary


@patch("pipewatch.watchdog._now", return_value=FIXED_NOW)
def test_watchdog_summary_shows_stale(mock_now):
    snap = _snap(age_seconds=500)
    report = check_staleness(snap, ttl_seconds=300)
    summary = watchdog_summary(report)
    assert "STALE" in summary


def test_cli_check_missing_snapshot(tmp_path):
    runner = CliRunner()
    result = runner.invoke(watchdog, ["check", "--snapshot", str(tmp_path / "missing.json")])
    assert result.exit_code == 2


@patch("pipewatch.watchdog._now", return_value=FIXED_NOW)
def test_cli_check_json_output(mock_now, tmp_path):
    import json as _json
    from pipewatch.snapshot import save_snapshot

    snap = _snap(age_seconds=60)
    snap_path = str(tmp_path / "snap.json")
    save_snapshot(snap, snap_path)

    runner = CliRunner()
    result = runner.invoke(watchdog, ["check", "--snapshot", snap_path, "--format", "json"])
    assert result.exit_code == 0
    data = _json.loads(result.output)
    assert "results" in data
    assert data["stale_count"] == 0
