"""CLI commands for escalation state management."""
import click
from pathlib import Path
from pipewatch.escalation import load_escalation_state, save_escalation_state, DEFAULT_PATH


@click.group()
def escalation():
    """Manage escalation state for repeated failures."""
    pass


@escalation.command("status")
@click.option("--path", default=str(DEFAULT_PATH), show_default=True)
def status(path: str):
    """Show current escalation state for all metrics."""
    entries = load_escalation_state(Path(path))
    if not entries:
        click.echo("No escalation state recorded.")
        return
    click.echo(f"{'Metric':<30} {'Failures':>8} {'Last Escalated'}")
    click.echo("-" * 60)
    for e in entries:
        last = e.last_escalated or "never"
        click.echo(f"{e.metric_name:<30} {e.consecutive_failures:>8} {last}")


@escalation.command("reset")
@click.argument("metric_name")
@click.option("--path", default=str(DEFAULT_PATH), show_default=True)
def reset(metric_name: str, path: str):
    """Reset escalation counter for a specific metric."""
    p = Path(path)
    entries = load_escalation_state(p)
    updated = [e for e in entries if e.metric_name != metric_name]
    if len(updated) == len(entries):
        click.echo(f"No escalation entry found for '{metric_name}'.")
        return
    save_escalation_state(updated, p)
    click.echo(f"Reset escalation state for '{metric_name}'.")


@escalation.command("purge")
@click.option("--path", default=str(DEFAULT_PATH), show_default=True)
def purge(path: str):
    """Clear all escalation state."""
    p = Path(path)
    save_escalation_state([], p)
    click.echo("Escalation state cleared.")
