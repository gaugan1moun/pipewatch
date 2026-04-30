"""Tests for pipewatch.scorer."""
from __future__ import annotations

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.scorer import HealthScore, ScoredMetric, score_metrics


def _m(name: str, status: MetricStatus, value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=status)


# ---------------------------------------------------------------------------
# score_metrics
# ---------------------------------------------------------------------------

def test_all_ok_gives_100() -> None:
    metrics = [_m("a", MetricStatus.OK), _m("b", MetricStatus.OK)]
    hs = score_metrics(metrics)
    assert hs.total == pytest.approx(100.0)


def test_all_critical_gives_0() -> None:
    metrics = [_m("a", MetricStatus.CRITICAL), _m("b", MetricStatus.CRITICAL)]
    hs = score_metrics(metrics)
    assert hs.total == pytest.approx(0.0)


def test_mixed_unweighted() -> None:
    metrics = [_m("a", MetricStatus.OK), _m("b", MetricStatus.CRITICAL)]
    hs = score_metrics(metrics)
    # (1.0 + 0.0) / 2 * 100 = 50
    assert hs.total == pytest.approx(50.0)


def test_warning_gives_50_per_metric() -> None:
    metrics = [_m("a", MetricStatus.WARNING)]
    hs = score_metrics(metrics)
    assert hs.total == pytest.approx(50.0)


def test_empty_metrics_gives_100() -> None:
    hs = score_metrics([])
    assert hs.total == pytest.approx(100.0)


def test_counts_are_correct() -> None:
    metrics = [
        _m("a", MetricStatus.OK),
        _m("b", MetricStatus.WARNING),
        _m("c", MetricStatus.CRITICAL),
        _m("d", MetricStatus.OK),
    ]
    hs = score_metrics(metrics)
    assert hs.num_ok == 2
    assert hs.num_warning == 1
    assert hs.num_critical == 1


def test_weighted_score() -> None:
    # critical metric has weight 3, ok metric has weight 1
    # weighted sum = 0.0*3 + 1.0*1 = 1.0; total_weight = 4
    # score = 1/4 * 100 = 25
    metrics = [_m("heavy", MetricStatus.CRITICAL), _m("light", MetricStatus.OK)]
    hs = score_metrics(metrics, weights={"heavy": 3.0, "light": 1.0})
    assert hs.total == pytest.approx(25.0)


def test_to_dict_keys() -> None:
    metrics = [_m("x", MetricStatus.OK)]
    d = score_metrics(metrics).to_dict()
    assert "total" in d
    assert "num_ok" in d
    assert "metrics" in d


# ---------------------------------------------------------------------------
# HealthScore.grade
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected_grade", [
    (100.0, "A"),
    (90.0, "A"),
    (89.9, "B"),
    (75.0, "B"),
    (74.9, "C"),
    (50.0, "C"),
    (49.9, "D"),
    (25.0, "D"),
    (24.9, "F"),
    (0.0, "F"),
])
def test_grade(score: float, expected_grade: str) -> None:
    hs = HealthScore(total=score)
    assert hs.grade() == expected_grade
