"""CLI commands for the watchdog / staleness checker."""

import json
import click

from pipewatch.snapshot import load_snapshot
from pipewatch.watchdog import check_staleness, watchdog_summary

DEFAULT_SNAPSHOT = ".pipewatch_snapshot.json"
DEFAULT_TTL = 300.0


@click.group()
def watchdog():
    """Monitor metrics for staleness."""


@watchdog.command("check")
@click.option("--snapshot", default=DEFAULT_SNAPSHOT, show_default=True,
              help="Path to the snapshot file.")
@click.option("--ttl", default=DEFAULT_TTL, show_default=True, type=float,
              help="Staleness threshold in seconds.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]),
              show_default=True, help="Output format.")
@click.option("--fail-on-stale", is_flag=True, default=False,
              help="Exit with code 1 if any metric is stale.")
def check_cmd(snapshot: str, ttl: float, fmt: str, fail_on_stale: bool):
    """Check snapshot metrics for staleness."""
    try:
        snap = load_snapshot(snapshot)
    except FileNotFoundError:
        click.echo(f"Snapshot file not found: {snapshot}", err=True)
        raise SystemExit(2)

    report = check_staleness(snap, ttl_seconds=ttl)

    if fmt == "json":
        click.echo(json.dumps(report.to_dict(), indent=2))
    else:
        click.echo(watchdog_summary(report))

    if fail_on_stale and report.stale_metrics:
        raise SystemExit(1)
