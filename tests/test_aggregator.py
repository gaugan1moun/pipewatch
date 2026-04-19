import pytest
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.aggregator import aggregate_metrics, aggregation_summary, AggregatedMetric


def _m(name: str, value: float, status: MetricStatus) -> Metric:
    return Metric(name=name, value=value, status=status, tags={})


def test_aggregate_single_metric():
    metrics = [_m("latency", 100.0, MetricStatus.OK)]
    result = aggregate_metrics(metrics)
    assert "latency" in result
    agg = result["latency"]
    assert agg.count == 1
    assert agg.mean == 100.0
    assert agg.min_val == 100.0
    assert agg.max_val == 100.0


def test_aggregate_multiple_same_name():
    metrics = [
        _m("latency", 50.0, MetricStatus.OK),
        _m("latency", 150.0, MetricStatus.WARNING),
        _m("latency", 200.0, MetricStatus.CRITICAL),
    ]
    result = aggregate_metrics(metrics)
    agg = result["latency"]
    assert agg.count == 3
    assert agg.mean == pytest.approx(133.333, rel=1e-3)
    assert agg.min_val == 50.0
    assert agg.max_val == 200.0


def test_aggregate_status_counts():
    metrics = [
        _m("latency", 50.0, MetricStatus.OK),
        _m("latency", 150.0, MetricStatus.OK),
        _m("latency", 200.0, MetricStatus.CRITICAL),
    ]
    result = aggregate_metrics(metrics)
    agg = result["latency"]
    assert agg.statuses.get("ok", 0) == 2
    assert agg.statuses.get("critical", 0) == 1


def test_worst_status_critical():
    metrics = [
        _m("latency", 50.0, MetricStatus.OK),
        _m("latency", 200.0, MetricStatus.CRITICAL),
    ]
    result = aggregate_metrics(metrics)
    assert result["latency"].worst_status == "critical"


def test_worst_status_warning():
    metrics = [
        _m("latency", 50.0, MetricStatus.OK),
        _m("latency", 120.0, MetricStatus.WARNING),
    ]
    result = aggregate_metrics(metrics)
    assert result["latency"].worst_status == "warning"


def test_worst_status_ok():
    metrics = [_m("latency", 50.0, MetricStatus.OK)]
    result = aggregate_metrics(metrics)
    assert result["latency"].worst_status == "ok"


def test_aggregate_multiple_metrics():
    metrics = [
        _m("latency", 100.0, MetricStatus.OK),
        _m("error_rate", 0.5, MetricStatus.WARNING),
    ]
    result = aggregate_metrics(metrics)
    assert "latency" in result
    assert "error_rate" in result


def test_to_dict_keys():
    metrics = [_m("latency", 100.0, MetricStatus.OK)]
    result = aggregate_metrics(metrics)
    d = result["latency"].to_dict()
    assert set(d.keys()) == {"name", "count", "mean", "min", "max", "statuses"}


def test_aggregation_summary_contains_name():
    metrics = [_m("latency", 100.0, MetricStatus.OK)]
    result = aggregate_metrics(metrics)
    summary = aggregation_summary(result)
    assert "latency" in summary
