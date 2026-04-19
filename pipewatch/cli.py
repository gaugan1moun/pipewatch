"""CLI entry points for pipewatch."""

import click

from pipewatch.config import load_thresholds, default_config_template
from pipewatch.alert_config import load_dispatcher, default_alert_config_template
from pipewatch.collector import MetricCollector
from pipewatch.formatters import format_table, format_json, format_summary
from pipewatch.history import record_metrics, DEFAULT_HISTORY_PATH
from pipewatch.report import build_report, format_report


@click.group()
def cli():
    """Pipewatch — monitor and alert on data pipeline health."""


@cli.command()
@click.option("--config", default="pipewatch.yaml", show_default=True)
@click.option("--alerts", default="pipewatch_alerts.yaml", show_default=True)
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json", "summary"]))
@click.option("--save-history", is_flag=True, default=False, help="Persist metrics to history file.")
def check(config, alerts, fmt, save_history):
    """Collect metrics and evaluate thresholds."""
    thresholds = load_thresholds(config)
    collector = MetricCollector(thresholds)
    metrics = collector.collect()

    if fmt == "table":
        click.echo(format_table(metrics))
    elif fmt == "json":
        click.echo(format_json(metrics))
    else:
        click.echo(format_summary(metrics))

    if save_history:
        record_metrics(metrics)
        click.echo(f"History saved to {DEFAULT_HISTORY_PATH}")

    dispatcher = load_dispatcher(alerts)
    dispatcher.dispatch(metrics)


@cli.command()
@click.option("--config", default="pipewatch.yaml", show_default=True)
@click.option("--window", default=5, show_default=True, help="Number of past runs for trend.")
def report(config, window):
    """Show metric history and trends."""
    thresholds = load_thresholds(config)
    collector = MetricCollector(thresholds)
    metrics = collector.collect()
    reports = build_report(metrics, trend_window=window)
    click.echo(format_report(reports))


@cli.command()
def init():
    """Write default config files."""
    with open("pipewatch.yaml", "w") as f:
        f.write(default_config_template())
    with open("pipewatch_alerts.yaml", "w") as f:
        f.write(default_alert_config_template())
    click.echo("Created pipewatch.yaml and pipewatch_alerts.yaml")
