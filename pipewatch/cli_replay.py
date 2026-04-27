"""CLI commands for replaying historical snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import click

from pipewatch.replay import load_replay_snapshots, replay_summary


@click.group()
def replay() -> None:
    """Replay and inspect historical pipeline snapshots."""


@replay.command("show")
@click.argument("snapshot_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--frame", default=None, type=int, help="Show a specific frame by index.")
@click.option("--output", default="text", type=click.Choice(["text", "json"]), show_default=True)
def show_cmd(
    snapshot_files: tuple,
    frame: int | None,
    output: str,
) -> None:
    """Display frames from one or more snapshot files."""
    paths: List[Path] = [Path(p) for p in snapshot_files]
    session = load_replay_snapshots(paths)

    if len(session) == 0:
        click.echo("No snapshots loaded.")
        return

    if frame is not None:
        f = session.get_frame(frame)
        if f is None:
            click.echo(f"Frame {frame} not found. Session has {len(session)} frame(s).")
            raise SystemExit(1)
        frames = [f]
    else:
        frames = list(session)

    if output == "json":
        click.echo(json.dumps([f.to_dict() for f in frames], indent=2))
    else:
        for line in replay_summary(session):
            idx = int(line.split("]")[0].lstrip("["))
            if frame is None or idx == frame:
                click.echo(line)
