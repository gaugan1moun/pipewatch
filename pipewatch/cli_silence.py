"""CLI commands for managing alert silences."""
import click
from datetime import datetime

from pipewatch.silencer import add_silence, load_silences, purge_expired, is_silenced

DEFAULT_SILENCE_PATH = ".pipewatch_silences.json"


@click.group()
def silence():
    """Manage alert silencing rules."""
    pass


@silence.command()
@click.argument("metric_name")
@click.option("--reason", default="manual", help="Reason for silencing.")
@click.option("--duration", default=60, help="Duration in minutes.", show_default=True)
@click.option("--path", default=DEFAULT_SILENCE_PATH, hidden=True)
def add(metric_name, reason, duration, path):
    """Silence alerts for METRIC_NAME for a given duration."""
    rule = add_silence(path, metric_name, reason, duration)
    click.echo(f"Silenced '{metric_name}' until {rule.expires_at.isoformat()} UTC. Reason: {reason}")


@silence.command(name="list")
@click.option("--path", default=DEFAULT_SILENCE_PATH, hidden=True)
def list_silences(path):
    """List active silence rules."""
    rules = load_silences(path)
    active = [r for r in rules if r.is_active()]
    if not active:
        click.echo("No active silences.")
        return
    for r in active:
        click.echo(f"  {r.metric_name:30s} expires={r.expires_at.isoformat()} reason={r.reason}")


@silence.command()
@click.option("--path", default=DEFAULT_SILENCE_PATH, hidden=True)
def purge(path):
    """Remove expired silence rules."""
    removed = purge_expired(path)
    click.echo(f"Purged {removed} expired silence(s).")


@silence.command()
@click.argument("metric_name")
@click.option("--path", default=DEFAULT_SILENCE_PATH, hidden=True)
def check(metric_name, path):
    """Check if a metric is currently silenced."""
    if is_silenced(path, metric_name):
        click.echo(f"'{metric_name}' is currently silenced.")
    else:
        click.echo(f"'{metric_name}' is NOT silenced.")
