"""Tests for pipewatch.anomaly module."""
import pytest
from pipewatch.anomaly import detect_anomaly, AnomalyResult
from pipewatch.history import HistoryEntry


def _entries(name: str, values: list) -> list:
    return [HistoryEntry(metric_name=name, value=v, status="ok", timestamp="2024-01-01T00:00:00") for v in values]


def test_returns_none_when_insufficient_history():
    entries = _entries("latency", [1.0, 2.0, 3.0])
    result = detect_anomaly("latency", 5.0, entries, min_samples=5)
    assert result is None


def test_returns_none_for_wrong_metric():
    entries = _entries("throughput", [1.0, 2.0, 3.0, 4.0, 5.0])
    result = detect_anomaly("latency", 5.0, entries, min_samples=5)
    assert result is None


def test_no_anomaly_for_normal_value():
    values = [10.0, 10.1, 9.9, 10.2, 9.8, 10.0]
    entries = _entries("cpu", values)
    result = detect_anomaly("cpu", 10.05, entries, z_threshold=2.5)
    assert result is not None
    assert result.is_anomaly is False
    assert "within normal range" in result.message


def test_anomaly_detected_for_spike():
    values = [10.0, 10.1, 9.9, 10.2, 9.8, 10.0]
    entries = _entries("cpu", values)
    result = detect_anomaly("cpu", 99.0, entries, z_threshold=2.5)
    assert result is not None
    assert result.is_anomaly is True
    assert "Anomaly detected" in result.message


def test_zero_std_no_anomaly():
    values = [5.0, 5.0, 5.0, 5.0, 5.0]
    entries = _entries("flat", values)
    result = detect_anomaly("flat", 5.0, entries)
    assert result is not None
    assert result.is_anomaly is False
    assert result.z_score == 0.0


def test_to_dict_keys():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    entries = _entries("mem", values)
    result = detect_anomaly("mem", 3.0, entries)
    assert result is not None
    d = result.to_dict()
    for key in ("metric_name", "is_anomaly", "current_value", "mean", "std", "z_score", "message"):
        assert key in d


def test_result_metric_name():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    entries = _entries("disk", values)
    result = detect_anomaly("disk", 3.0, entries)
    assert result.metric_name == "disk"
