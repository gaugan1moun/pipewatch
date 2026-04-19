"""CLI commands for tag-based metric inspection."""
import click
from pipewatch.config import load_thresholds
from pipewatch.collector import MetricCollector
from pipewatch.tags import TagFilter, filter_metrics, group_by_tag
from pipewatch.formatters import format_table


@click.group()
def tags():
    """Tag-based metric filtering and grouping."""


@tags.command("filter")
@click.option("--require", "-r", multiple=True, help="Tags that must be present.")
@click.option("--exclude", "-e", multiple=True, help="Tags that must not be present.")
@click.option("--config", default="pipewatch.yaml", show_default=True)
def filter_cmd(require, exclude, config):
    """Show metrics matching the given tag constraints."""
    thresholds = load_thresholds(config)
    collector = MetricCollector(thresholds)
    metrics = collector.collect()
    tf = TagFilter(required=list(require), excluded=list(exclude))
    matched = filter_metrics(metrics, tf)
    if not matched:
        click.echo("No metrics matched the tag filter.")
        return
    click.echo(format_table(matched))


@tags.command("group")
@click.option("--config", default="pipewatch.yaml", show_default=True)
def group_cmd(config):
    """Show metrics grouped by tag."""
    thresholds = load_thresholds(config)
    collector = MetricCollector(thresholds)
    metrics = collector.collect()
    groups = group_by_tag(metrics)
    if not groups:
        click.echo("No tags found.")
        return
    for tag, ms in sorted(groups.items()):
        click.echo(f"\n[{tag}]")
        click.echo(format_table(ms))
