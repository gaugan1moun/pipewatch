"""CLI commands for the heatmap feature."""
import json

import click

from pipewatch.heatmap import build_heatmap, heatmap_summary
from pipewatch.history import load_history


@click.group()
def heatmap():
    """Visualise metric status frequency as a heatmap."""


@heatmap.command("show")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--granularity", default="day", type=click.Choice(["day", "hour"]), show_default=True)
@click.option("--metric", default=None, help="Filter to a single metric name.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def show(
    history_file: str,
    granularity: str,
    metric: str | None,
    fmt: str,
) -> None:
    """Show a status-frequency heatmap from history."""
    entries = load_history(history_file)
    if not entries:
        click.echo("No history found.")
        return

    cells = build_heatmap(entries, granularity=granularity, metric_name=metric)

    if fmt == "json":
        click.echo(json.dumps([c.to_dict() for c in cells], indent=2))
    else:
        click.echo(heatmap_summary(cells))
