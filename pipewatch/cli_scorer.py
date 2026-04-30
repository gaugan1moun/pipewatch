"""CLI commands for health scoring."""
from __future__ import annotations

import json
import sys

import click

from pipewatch.collector import MetricCollector
from pipewatch.config import load_thresholds
from pipewatch.metrics import evaluate
from pipewatch.scorer import score_metrics


@click.group()
def scorer() -> None:
    """Health score commands."""


@scorer.command("show")
@click.option("--config", "cfg_path", default="pipewatch.yml", show_default=True,
              help="Path to threshold config file.")
@click.option("--weights", "weights_json", default=None,
              help='JSON object of metric weights, e.g. \'{"latency": 2.0}\'')
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text",
              show_default=True)
@click.option("--fail-on-critical", is_flag=True, default=False,
              help="Exit with a non-zero status code when any metric is CRITICAL.")
def show(
    cfg_path: str,
    weights_json: str | None,
    fmt: str,
    fail_on_critical: bool,
) -> None:
    """Display a weighted health score for all registered metrics."""
    thresholds = load_thresholds(cfg_path)

    try:
        weights: dict[str, float] = json.loads(weights_json) if weights_json else {}
    except json.JSONDecodeError as exc:
        raise click.BadParameter(
            f"Invalid JSON for --weights: {exc}", param_hint="'--weights'"
        ) from exc

    collector = MetricCollector()
    # Collect raw values and evaluate against thresholds
    raw = collector.collect()
    metrics = [evaluate(m, thresholds.get(m.name)) for m in raw]

    hs = score_metrics(metrics, weights=weights)

    if fmt == "json":
        click.echo(json.dumps(hs.to_dict(), indent=2))
    else:
        click.echo(f"Health Score : {hs.total:.1f} / 100  (Grade: {hs.grade()})")
        click.echo(f"  OK       : {hs.num_ok}")
        click.echo(f"  WARNING  : {hs.num_warning}")
        click.echo(f"  CRITICAL : {hs.num_critical}")
        click.echo("")
        click.echo(f"  {'Metric':<30} {'Status':<10} {'Score':>6}")
        click.echo("  " + "-" * 50)
        for sm in hs.metrics:
            click.echo(
                f"  {sm.name:<30} {sm.status.value:<10} {sm.score * 100:>5.0f}%"
            )

    if fail_on_critical and hs.num_critical > 0:
        sys.exit(1)
