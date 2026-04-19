"""CLI commands for managing notifier cooldown state."""
import click
from pathlib import Path
from pipewatch.notifier import load_state, save_state, purge_expired

DEFAULT_STATE_PATH = Path(".pipewatch") / "notifier_state.json"


@click.group("notifier")
def notifier():
    """Manage alert notification cooldown state."""


@notifier.command("status")
@click.option("--state-file", default=str(DEFAULT_STATE_PATH), show_default=True)
def status(state_file: str):
    """Show current cooldown state for all metrics."""
    path = Path(state_file)
    state = load_state(path)
    if not state.last_notified:
        click.echo("No notifier state recorded.")
        return
    click.echo(f"{'Metric':<30} {'Last Notified (epoch)':<22}")
    click.echo("-" * 54)
    for metric, ts in sorted(state.last_notified.items()):
        click.echo(f"{metric:<30} {ts:<22.2f}")


@notifier.command("purge")
@click.option("--cooldown", default=300, show_default=True, help="Cooldown in seconds.")
@click.option("--state-file", default=str(DEFAULT_STATE_PATH), show_default=True)
def purge(cooldown: int, state_file: str):
    """Purge expired cooldown entries from state."""
    path = Path(state_file)
    state = load_state(path)
    removed = purge_expired(state, cooldown=cooldown)
    save_state(state, path)
    click.echo(f"Purged {removed} expired entr{'y' if removed == 1 else 'ies'}.")


@notifier.command("reset")
@click.argument("metric")
@click.option("--state-file", default=str(DEFAULT_STATE_PATH), show_default=True)
def reset(metric: str, state_file: str):
    """Reset cooldown for a specific metric."""
    path = Path(state_file)
    state = load_state(path)
    if metric in state.last_notified:
        del state.last_notified[metric]
        save_state(state, path)
        click.echo(f"Reset cooldown for '{metric}'.")
    else:
        click.echo(f"No cooldown entry found for '{metric}'.")
