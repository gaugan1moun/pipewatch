"""CLI commands for the metric profiler."""

from __future__ import annotations

import json

import click

from pipewatch.history import load_history
from pipewatch.profiler import profile_all, profile_metric


@click.group()
def profiler() -> None:
    """Inspect value profiles (min/max/avg/percentiles) for metrics."""


@profiler.command("show")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--metric", default=None, help="Limit to a single metric name.")
@click.option("--window", default=None, type=int, help="Only use the N most-recent entries.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def show(
    history_file: str,
    metric: str | None,
    window: int | None,
    fmt: str,
) -> None:
    """Show value profiles for one or all metrics."""
    entries = load_history(history_file)

    if metric:
        profile = profile_metric(metric, entries, window=window)
        profiles = [profile] if profile else []
    else:
        profiles = profile_all(entries, window=window)

    if not profiles:
        click.echo("No profile data available.")
        return

    if fmt == "json":
        click.echo(json.dumps([p.to_dict() for p in profiles], indent=2))
        return

    header = f"{'Metric':<30} {'Count':>6} {'Min':>10} {'Max':>10} {'Avg':>10} {'P50':>10} {'P95':>10}"
    click.echo(header)
    click.echo("-" * len(header))
    for p in profiles:
        click.echo(
            f"{p.metric_name:<30} {p.count:>6} "
            f"{p.min_value:>10.4f} {p.max_value:>10.4f} "
            f"{p.avg_value:>10.4f} {p.p50:>10.4f} {p.p95:>10.4f}"
        )
