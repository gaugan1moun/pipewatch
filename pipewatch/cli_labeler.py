"""CLI commands for metric label filtering and grouping."""

import json
import click

from pipewatch.labeler import LabelSet, label_metrics, group_by_label, label_summary
from pipewatch.metrics import Metric, MetricStatus


def _demo_metrics():
    """Build a small set of demo labeled metrics for CLI testing."""
    from pipewatch.metrics import ThresholdConfig
    demos = [
        ("pipeline.rows", 120.0, "pipeline", "ingestion", "team-a"),
        ("pipeline.latency", 5.2, "pipeline", "transform", "team-b"),
        ("db.connections", 80.0, "database", "connections", "team-a"),
        ("db.query_time", 2.1, "database", "query", "team-b"),
    ]
    metrics = []
    for name, val, layer, stage, team in demos:
        cfg = ThresholdConfig(warning=50.0, critical=100.0)
        m = Metric(name=name, value=val, config=cfg)
        m.labels = LabelSet({"layer": layer, "stage": stage, "team": team})
        metrics.append(m)
    return metrics


@click.group()
def labeler():
    """Commands for label-based metric filtering and grouping."""


@labeler.command("filter")
@click.option("--label", "-l", multiple=True, help="key=value label selector (repeatable).")
@click.option("--output", "-o", default="text", type=click.Choice(["text", "json"]), show_default=True)
def filter_cmd(label, output):
    """Filter demo metrics by label selectors."""
    selector = {}
    for item in label:
        if "=" not in item:
            raise click.BadParameter(f"Expected key=value, got: {item}")
        k, v = item.split("=", 1)
        selector[k.strip()] = v.strip()

    metrics = _demo_metrics()
    matched = label_metrics(metrics, selector) if selector else metrics

    if output == "json":
        out = [{"name": m.name, "value": m.value, "labels": m.labels.to_dict()} for m in matched]
        click.echo(json.dumps(out, indent=2))
    else:
        if not matched:
            click.echo("No metrics matched the selector.")
        for m in matched:
            click.echo(f"{m.name}  value={m.value}  labels={m.labels.to_dict()}")


@labeler.command("group")
@click.argument("key")
def group_cmd(key):
    """Group demo metrics by a label KEY and show counts."""
    metrics = _demo_metrics()
    lines = label_summary(metrics, key)
    for line in lines:
        click.echo(line)
