"""CLI commands for metric history rollup summaries."""

from __future__ import annotations

import json

import click

from pipewatch.history import load_history
from pipewatch.rollup import rollup_history, rollup_summary


@click.group("rollup")
def rollup():
    """Rollup metric history into time-bucketed summaries."""


@rollup.command("show")
@click.option(
    "--path",
    default="pipewatch_history.json",
    show_default=True,
    help="Path to history file.",
)
@click.option(
    "--granularity",
    type=click.Choice(["day", "hour"]),
    default="day",
    show_default=True,
    help="Time bucket granularity.",
)
@click.option(
    "--metric",
    default=None,
    help="Filter to a single metric name.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
)
def show(path: str, granularity: str, metric: str | None, fmt: str) -> None:
    """Show rollup summary for recorded metrics."""
    entries = load_history(path)
    if metric:
        entries = [e for e in entries if e.metric_name == metric]

    rollups = rollup_history(entries, granularity=granularity)

    if fmt == "json":
        output = {
            name: [b.to_dict() for b in buckets]
            for name, buckets in rollups.items()
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(rollup_summary(rollups))
