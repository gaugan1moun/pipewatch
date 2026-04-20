"""CLI commands for comparing two snapshots."""
from __future__ import annotations

import json

import click

from pipewatch.comparator import compare_snapshots
from pipewatch.snapshot import load_snapshot


@click.group("compare")
def compare() -> None:
    """Compare two pipeline snapshots."""


@compare.command("diff")
@click.argument("old_path", type=click.Path(exists=True))
@click.argument("new_path", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--changed-only", is_flag=True, default=False, help="Only show changed metrics.")
def diff_cmd(old_path: str, new_path: str, fmt: str, changed_only: bool) -> None:
    """Diff OLD_PATH snapshot against NEW_PATH snapshot."""
    old_snap = load_snapshot(old_path)
    new_snap = load_snapshot(new_path)
    comparison = compare_snapshots(old_snap, new_snap)

    diffs = comparison.changed_metrics if changed_only else comparison.diffs

    if fmt == "json":
        data = comparison.to_dict()
        if changed_only:
            data["diffs"] = [d.to_dict() for d in diffs]
        click.echo(json.dumps(data, indent=2))
        return

    click.echo(f"Comparing snapshots:")
    click.echo(f"  OLD: {comparison.old_timestamp}")
    click.echo(f"  NEW: {comparison.new_timestamp}")
    click.echo(f"  Total metrics: {len(comparison.diffs)}  Changed: {len(comparison.changed_metrics)}")
    click.echo("")

    if not diffs:
        click.echo("No changes detected." if changed_only else "No metrics found.")
        return

    header = f"{'METRIC':<30} {'OLD':>10} {'NEW':>10} {'DIRECTION':>12}"
    click.echo(header)
    click.echo("-" * len(header))
    for d in diffs:
        old_s = d.old_status.value if d.old_status else "(none)"
        new_s = d.new_status.value if d.new_status else "(none)"
        click.echo(f"{d.name:<30} {old_s:>10} {new_s:>10} {d.direction:>12}")
