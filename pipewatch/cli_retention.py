"""CLI commands for history retention management."""
import click
from pipewatch.retention import RetentionPolicy, prune_history, retention_summary

DEFAULT_HISTORY = "pipewatch_history.json"


@click.group()
def retention():
    """Manage history retention policies."""


@retention.command()
@click.option("--path", default=DEFAULT_HISTORY, show_default=True, help="History file path.")
@click.option("--max-age-days", default=30, show_default=True, help="Max age in days.")
@click.option("--max-entries", default=500, show_default=True, help="Max entries per metric.")
def prune(path, max_age_days, max_entries):
    """Prune old history entries according to retention policy."""
    policy = RetentionPolicy(max_age_days=max_age_days, max_entries_per_metric=max_entries)
    removed = prune_history(path, policy)
    click.echo(f"Pruned {removed} entries from {path}.")


@retention.command()
@click.option("--path", default=DEFAULT_HISTORY, show_default=True, help="History file path.")
@click.option("--max-age-days", default=30, show_default=True)
@click.option("--max-entries", default=500, show_default=True)
def status(path, max_age_days, max_entries):
    """Show retention status for the history file."""
    policy = RetentionPolicy(max_age_days=max_age_days, max_entries_per_metric=max_entries)
    summary = retention_summary(path, policy)
    click.echo(f"Total entries     : {summary['total_entries']}")
    click.echo(f"Expired entries   : {summary['expired_entries']}")
    click.echo(f"Max age (days)    : {summary['max_age_days']}")
    click.echo(f"Max per metric    : {summary['max_entries_per_metric']}")
