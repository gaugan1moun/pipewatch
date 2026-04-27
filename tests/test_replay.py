"""Tests for pipewatch.replay."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from pipewatch.cli_replay import replay
from pipewatch.metrics import MetricStatus
from pipewatch.replay import ReplayFrame, ReplaySession, load_replay_snapshots, replay_summary
from pipewatch.snapshot import Snapshot, SnapshotEntry


def _write_snapshot(path: Path, timestamp: str, entries: list) -> None:
    data = {"timestamp": timestamp, "entries": entries}
    path.write_text(json.dumps(data))


@pytest.fixture()
def two_snapshots(tmp_path: Path):
    p1 = tmp_path / "snap1.json"
    p2 = tmp_path / "snap2.json"
    _write_snapshot(
        p1,
        "2024-01-01T10:00:00",
        [{"metric_name": "rows", "value": 100.0, "status": "ok", "tags": {}}],
    )
    _write_snapshot(
        p2,
        "2024-01-01T11:00:00",
        [{"metric_name": "rows", "value": 5.0, "status": "critical", "tags": {}}],
    )
    return [p1, p2]


def test_load_replay_snapshots_count(two_snapshots):
    session = load_replay_snapshots(two_snapshots)
    assert len(session) == 2


def test_load_replay_snapshots_sorted(two_snapshots):
    session = load_replay_snapshots(two_snapshots)
    timestamps = [f.snapshot.timestamp for f in session]
    assert timestamps == sorted(timestamps)


def test_load_replay_missing_file(tmp_path: Path):
    session = load_replay_snapshots([tmp_path / "nonexistent.json"])
    assert len(session) == 0


def test_get_frame_found(two_snapshots):
    session = load_replay_snapshots(two_snapshots)
    frame = session.get_frame(0)
    assert frame is not None
    assert frame.index == 0


def test_get_frame_not_found(two_snapshots):
    session = load_replay_snapshots(two_snapshots)
    assert session.get_frame(99) is None


def test_replay_summary_lines(two_snapshots):
    session = load_replay_snapshots(two_snapshots)
    lines = replay_summary(session)
    assert len(lines) == 2
    assert "rows=ok" in lines[0] or "rows=critical" in lines[0]


def test_replay_frame_to_dict(two_snapshots):
    session = load_replay_snapshots(two_snapshots)
    d = session.get_frame(0).to_dict()
    assert "index" in d
    assert "snapshot" in d


def test_cli_show_text(two_snapshots):
    runner = CliRunner()
    result = runner.invoke(replay, ["show", str(two_snapshots[0]), str(two_snapshots[1])])
    assert result.exit_code == 0
    assert "[0]" in result.output


def test_cli_show_json(two_snapshots):
    runner = CliRunner()
    result = runner.invoke(replay, ["show", "--output", "json", str(two_snapshots[0]), str(two_snapshots[1])])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert isinstance(parsed, list)
    assert len(parsed) == 2


def test_cli_show_specific_frame(two_snapshots):
    runner = CliRunner()
    result = runner.invoke(replay, ["show", "--frame", "1", str(two_snapshots[0]), str(two_snapshots[1])])
    assert result.exit_code == 0
    assert "[1]" in result.output
    assert "[0]" not in result.output


def test_cli_show_invalid_frame(two_snapshots):
    runner = CliRunner()
    result = runner.invoke(replay, ["show", "--frame", "99", str(two_snapshots[0])])
    assert result.exit_code != 0 or "not found" in result.output
