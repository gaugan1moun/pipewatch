"""Tests for pipewatch.sampler."""

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.sampler import MetricSampler, SampleSummary, _percentile


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _metric(value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name="test", value=value, status=status, unit="ms")


def _counter(values):
    """Return a callable that yields successive values from *values*."""
    it = iter(values)
    def fn():
        return _metric(next(it))
    return fn


# ---------------------------------------------------------------------------
# _percentile
# ---------------------------------------------------------------------------

def test_percentile_empty():
    assert _percentile([], 50) == 0.0


def test_percentile_single():
    assert _percentile([7.0], 50) == 7.0
    assert _percentile([7.0], 95) == 7.0


def test_percentile_known_values():
    data = sorted([1.0, 2.0, 3.0, 4.0, 5.0])
    assert _percentile(data, 0) == 1.0
    assert _percentile(data, 100) == 5.0
    assert _percentile(data, 50) == 3.0


# ---------------------------------------------------------------------------
# MetricSampler construction
# ---------------------------------------------------------------------------

def test_invalid_n_raises():
    with pytest.raises(ValueError):
        MetricSampler(n=0)


def test_unknown_name_raises():
    sampler = MetricSampler(n=3)
    with pytest.raises(KeyError):
        sampler.sample("missing")


# ---------------------------------------------------------------------------
# sampling
# ---------------------------------------------------------------------------

def test_sample_returns_summary():
    sampler = MetricSampler(n=4)
    sampler.register("latency", _counter([10.0, 20.0, 30.0, 40.0]))
    summary = sampler.sample("latency")
    assert isinstance(summary, SampleSummary)
    assert summary.name == "latency"
    assert len(summary.samples) == 4


def test_sample_statistics():
    sampler = MetricSampler(n=5)
    sampler.register("q", _counter([1.0, 2.0, 3.0, 4.0, 5.0]))
    s = sampler.sample("q")
    assert s.mean == pytest.approx(3.0)
    assert s.minimum == 1.0
    assert s.maximum == 5.0
    assert s.p50 == pytest.approx(3.0)


def test_sample_worst_status_propagated():
    def fn():
        fn.call += 1
        status = MetricStatus.CRITICAL if fn.call == 2 else MetricStatus.OK
        return _metric(1.0, status)
    fn.call = 0
    sampler = MetricSampler(n=3)
    sampler.register("s", fn)
    s = sampler.sample("s")
    assert s.status == MetricStatus.CRITICAL


def test_sample_all_returns_all_names():
    sampler = MetricSampler(n=2)
    sampler.register("a", lambda: _metric(1.0))
    sampler.register("b", lambda: _metric(2.0))
    results = sampler.sample_all()
    assert set(results.keys()) == {"a", "b"}


def test_to_dict_keys():
    sampler = MetricSampler(n=2)
    sampler.register("x", lambda: _metric(5.0))
    d = sampler.sample("x").to_dict()
    for key in ("name", "samples", "mean", "min", "max", "p50", "p95", "status"):
        assert key in d
