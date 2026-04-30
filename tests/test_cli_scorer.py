"""CLI tests for the scorer commands."""
from __future__ import annotations

import json
from unittest.mock import patch

from click.testing import CliRunner

from pipewatch.cli_scorer import scorer
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.scorer import HealthScore, ScoredMetric


def _make_health_score(
    total: float = 80.0,
    ok: int = 2,
    warn: int = 1,
    crit: int = 0,
) -> HealthScore:
    scored = [
        ScoredMetric("metric_a", MetricStatus.OK, 1.0, 1.0),
        ScoredMetric("metric_b", MetricStatus.OK, 1.0, 1.0),
        ScoredMetric("metric_c", MetricStatus.WARNING, 1.0, 0.5),
    ]
    return HealthScore(
        total=total,
        metrics=scored[:ok + warn + crit],
        num_ok=ok,
        num_warning=warn,
        num_critical=crit,
    )


def test_show_text_output() -> None:
    runner = CliRunner()
    hs = _make_health_score()
    with (
        patch("pipewatch.cli_scorer.load_thresholds", return_value={}),
        patch("pipewatch.cli_scorer.MetricCollector") as mc,
        patch("pipewatch.cli_scorer.evaluate", side_effect=lambda m, _: m),
        patch("pipewatch.cli_scorer.score_metrics", return_value=hs),
    ):
        mc.return_value.collect.return_value = []
        result = runner.invoke(scorer, ["show"])
    assert result.exit_code == 0
    assert "Health Score" in result.output
    assert "Grade" in result.output
    assert "OK" in result.output


def test_show_json_output() -> None:
    runner = CliRunner()
    hs = _make_health_score(total=75.0)
    with (
        patch("pipewatch.cli_scorer.load_thresholds", return_value={}),
        patch("pipewatch.cli_scorer.MetricCollector") as mc,
        patch("pipewatch.cli_scorer.evaluate", side_effect=lambda m, _: m),
        patch("pipewatch.cli_scorer.score_metrics", return_value=hs),
    ):
        mc.return_value.collect.return_value = []
        result = runner.invoke(scorer, ["show", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total" in data
    assert data["total"] == pytest.approx(75.0)


def test_show_with_weights() -> None:
    runner = CliRunner()
    hs = _make_health_score(total=60.0)
    weights_arg = json.dumps({"metric_a": 2.0})
    with (
        patch("pipewatch.cli_scorer.load_thresholds", return_value={}),
        patch("pipewatch.cli_scorer.MetricCollector") as mc,
        patch("pipewatch.cli_scorer.evaluate", side_effect=lambda m, _: m),
        patch("pipewatch.cli_scorer.score_metrics", return_value=hs) as mock_score,
    ):
        mc.return_value.collect.return_value = []
        result = runner.invoke(scorer, ["show", "--weights", weights_arg])
    assert result.exit_code == 0
    called_weights = mock_score.call_args[1]["weights"]
    assert called_weights == {"metric_a": 2.0}


import pytest  # noqa: E402 (needed for parametrize above)
