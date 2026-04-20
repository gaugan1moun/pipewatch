"""CLI commands for inspecting and managing alert rate-limit state."""
import click

from pipewatch.ratelimiter import (
    DEFAULT_STATE_PATH,
    load_rate_limit_state,
    save_rate_limit_state,
)


@click.group("ratelimit")
def ratelimit() -> None:
    """Manage alert rate-limit state."""


@ratelimit.command("status")
@click.option("--state-file", default=str(DEFAULT_STATE_PATH), show_default=True)
def status(state_file: str) -> None:
    """Show current rate-limit counters."""
    import time

    state = load_rate_limit_state(__import__("pathlib").Path(state_file))
    if not state:
        click.echo("No rate-limit state recorded.")
        return
    now = time.time()
    click.echo(f"{'KEY':<40} {'WINDOW(s)':<12} {'MAX':<6} {'RECENT'}")
    click.echo("-" * 72)
    for k, entry in sorted(state.items()):
        entry._prune(now)
        click.echo(
            f"{k:<40} {entry.window_seconds:<12} {entry.max_alerts:<6} {len(entry.timestamps)}"
        )


@ratelimit.command("reset")
@click.argument("metric_name")
@click.argument("channel")
@click.option("--state-file", default=str(DEFAULT_STATE_PATH), show_default=True)
def reset(metric_name: str, channel: str, state_file: str) -> None:
    """Clear rate-limit history for a specific metric/channel pair."""
    path = __import__("pathlib").Path(state_file)
    state = load_rate_limit_state(path)
    key = f"{metric_name}::{channel}"
    if key in state:
        del state[key]
        save_rate_limit_state(state, path)
        click.echo(f"Reset rate-limit for {key}.")
    else:
        click.echo(f"No entry found for {key}.")


@ratelimit.command("purge")
@click.option("--state-file", default=str(DEFAULT_STATE_PATH), show_default=True)
def purge(state_file: str) -> None:
    """Remove all rate-limit state."""
    path = __import__("pathlib").Path(state_file)
    save_rate_limit_state({}, path)
    click.echo("Rate-limit state purged.")
