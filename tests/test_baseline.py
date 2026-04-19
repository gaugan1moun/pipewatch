"""Tests for pipewatch.baseline module."""

import pytest
from dataclasses import dataclass
from pipewatch.baseline import (
    BaselineEntry,
    load_baseline,
    save_baseline,
    record_baseline,
    compare_to_baseline,
)


@dataclass
class _FakeMetric:
    name: str
    value: float


@pytest.fixture
def tmp_baseline(tmp_path):
    return str(tmp_path / "baseline.json")


def test_load_baseline_missing_file(tmp_baseline):
    result = load_baseline(tmp_baseline)
    assert result == {}


def test_save_and_load_roundtrip(tmp_baseline):
    entries = {
        "row_count": BaselineEntry(metric_name="row_count", value=1000.0, recorded_at="2024-01-01T00:00:00+00:00")
    }
    save_baseline(entries, tmp_baseline)
    loaded = load_baseline(tmp_baseline)
    assert "row_count" in loaded
    assert loaded["row_count"].value == 1000.0
    assert loaded["row_count"].recorded_at == "2024-01-01T00:00:00+00:00"


def test_record_baseline_creates_entries(tmp_baseline):
    metrics = [_FakeMetric("latency", 0.5), _FakeMetric("error_rate", 0.01)]
    entries = record_baseline(metrics, path=tmp_baseline, recorded_at="2024-06-01T12:00:00+00:00")
    assert "latency" in entries
    assert entries["latency"].value == 0.5
    assert entries["error_rate"].value == 0.01


def test_record_baseline_persists(tmp_baseline):
    metrics = [_FakeMetric("throughput", 250.0)]
    record_baseline(metrics, path=tmp_baseline)
    loaded = load_baseline(tmp_baseline)
    assert "throughput" in loaded
    assert loaded["throughput"].value == 250.0


def test_compare_no_baseline(tmp_baseline):
    metrics = [_FakeMetric("row_count", 900.0)]
    result = compare_to_baseline(metrics, path=tmp_baseline)
    assert result == {}


def test_compare_delta_positive(tmp_baseline):
    metrics = [_FakeMetric("row_count", 1000.0)]
    record_baseline(metrics, path=tmp_baseline)
    current = [_FakeMetric("row_count", 1200.0)]
    result = compare_to_baseline(current, path=tmp_baseline)
    assert result["row_count"]["delta"] == pytest.approx(200.0)
    assert result["row_count"]["pct_change"] == pytest.approx(20.0)


def test_compare_delta_negative(tmp_baseline):
    metrics = [_FakeMetric("row_count", 1000.0)]
    record_baseline(metrics, path=tmp_baseline)
    current = [_FakeMetric("row_count", 800.0)]
    result = compare_to_baseline(current, path=tmp_baseline)
    assert result["row_count"]["delta"] == pytest.approx(-200.0)
    assert result["row_count"]["pct_change"] == pytest.approx(-20.0)


def test_compare_zero_baseline(tmp_baseline):
    metrics = [_FakeMetric("errors", 0.0)]
    record_baseline(metrics, path=tmp_baseline)
    current = [_FakeMetric("errors", 5.0)]
    result = compare_to_baseline(current, path=tmp_baseline)
    assert result["errors"]["pct_change"] is None
    assert result["errors"]["delta"] == pytest.approx(5.0)
