"""CLI entry point for pipewatch."""

import json
import sys
from pathlib import Path

import click

from pipewatch.collector import MetricCollector
from pipewatch.config import default_config_template, load_thresholds
from pipewatch.metrics import MetricStatus


@click.group()
def cli():
    """pipewatch — monitor and alert on data pipeline health metrics."""


@cli.command("check")
@click.option("--config", default="pipewatch.json", show_default=True, help="Path to config file.")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]), show_default=True)
def check(config, output_format):
    """Run metric checks and report status."""
    thresholds = load_thresholds(Path(config))
    collector = MetricCollector()

    for name, threshold in thresholds.items():
        collector.register(name, lambda: 0.0, threshold)

    metrics = collector.collect()
    has_critical = any(m.status == MetricStatus.CRITICAL for m in metrics)

    if output_format == "json":
        click.echo(json.dumps([m.to_dict() for m in metrics], indent=2))
    else:
        for m in metrics:
            symbol = {"ok": "✓", "warning": "!", "critical": "✗", "unknown": "?"}.get(m.status.value, "?")
            click.echo(f"[{symbol}] {m.name}: {m.value} {m.unit} ({m.status.value})")

    sys.exit(2 if has_critical else 0)


@cli.command("init")
def init():
    """Generate a default pipewatch.json configuration file."""
    config_path = Path("pipewatch.json")
    if config_path.exists():
        click.echo("pipewatch.json already exists. Aborting.")
        sys.exit(1)
    config_path.write_text(json.dumps(default_config_template(), indent=2))
    click.echo("Created pipewatch.json with default thresholds.")


if __name__ == "__main__":
    cli()
