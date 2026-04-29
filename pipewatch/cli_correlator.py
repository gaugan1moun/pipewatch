"""CLI sub-command: pipewatch correlate"""
from __future__ import annotations

import json

import click

from pipewatch.correlator import correlate_metrics, correlation_summary
from pipewatch.history import load_history


@click.group()
def correlate() -> None:
    """Analyse correlations between metric status histories."""


@correlate.command("show")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--min-samples", default=5, show_default=True, help="Minimum overlapping samples required.")
@click.option("--threshold", default=0.6, show_default=True, help="Minimum |r| to report.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def show(
    history_file: str,
    min_samples: int,
    threshold: float,
    fmt: str,
) -> None:
    """Show correlated metric pairs from history."""
    entries = load_history(history_file)
    if not entries:
        click.echo("No history data found.")
        return

    results = correlate_metrics(entries, min_samples=min_samples, threshold=threshold)

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        click.echo(correlation_summary(results))
