"""Tests for pipewatch.export."""

from __future__ import annotations

import csv
import json
import os

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.snapshot import Snapshot
from pipewatch.export import export_snapshot, export_snapshot_csv, export_snapshot_json


def _snapshot() -> Snapshot:
    metrics = [
        Metric(name="row_count", value=100.0, status=MetricStatus.OK),
        Metric(name="error_rate", value=0.05, status=MetricStatus.WARNING),
    ]
    return Snapshot(timestamp="2024-01-01T00:00:00", metrics=metrics)


def test_export_json_creates_file(tmp_path):
    snap = _snapshot()
    out = tmp_path / "snap.json"
    export_snapshot_json(snap, str(out))
    assert out.exists()


def test_export_json_content(tmp_path):
    snap = _snapshot()
    out = tmp_path / "snap.json"
    export_snapshot_json(snap, str(out))
    data = json.loads(out.read_text())
    assert data["timestamp"] == "2024-01-01T00:00:00"
    names = [m["name"] for m in data["metrics"]]
    assert "row_count" in names
    assert "error_rate" in names


def test_export_csv_creates_file(tmp_path):
    snap = _snapshot()
    out = tmp_path / "snap.csv"
    export_snapshot_csv(snap, str(out))
    assert out.exists()


def test_export_csv_rows(tmp_path):
    snap = _snapshot()
    out = tmp_path / "snap.csv"
    export_snapshot_csv(snap, str(out))
    with open(out, newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2
    names = {r["name"] for r in rows}
    assert names == {"row_count", "error_rate"}


def test_export_csv_statuses(tmp_path):
    snap = _snapshot()
    out = tmp_path / "snap.csv"
    export_snapshot_csv(snap, str(out))
    with open(out, newline="") as fh:
        rows = {r["name"]: r for r in csv.DictReader(fh)}
    assert rows["row_count"]["status"] == MetricStatus.OK.value
    assert rows["error_rate"]["status"] == MetricStatus.WARNING.value


def test_export_dispatch_json(tmp_path):
    snap = _snapshot()
    out = tmp_path / "out.json"
    export_snapshot(snap, str(out), fmt="json")
    assert out.exists()


def test_export_dispatch_csv(tmp_path):
    snap = _snapshot()
    out = tmp_path / "out.csv"
    export_snapshot(snap, str(out), fmt="csv")
    assert out.exists()


def test_export_invalid_format(tmp_path):
    snap = _snapshot()
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_snapshot(snap, str(tmp_path / "out.xml"), fmt="xml")
