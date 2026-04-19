"""CLI commands for scheduled pipeline monitoring."""

import click
import logging

from pipewatch.collector import MetricCollector
from pipewatch.config import load_thresholds
from pipewatch.alert_config import load_dispatcher
from pipewatch.history import record_metric
from pipewatch.schedule import ScheduleConfig, ScheduledRunner

logger = logging.getLogger(__name__)


@click.command("watch")
@click.option("--config", "config_path", default="pipewatch.yml", show_default=True)
@click.option("--alerts", "alert_path", default="alerts.yml", show_default=True)
@click.option("--interval", default=60, show_default=True, help="Seconds between checks.")
@click.option("--runs", default=None, type=int, help="Max number of runs (default: unlimited).")
@click.option("--history", "history_path", default="pipewatch_history.json", show_default=True)
def watch(config_path, alert_path, interval, runs, history_path):
    """Continuously monitor pipeline metrics on a schedule."""
    thresholds = load_thresholds(config_path)
    dispatcher = load_dispatcher(alert_path)
    collector = MetricCollector(thresholds)

    def _run_check():
        metrics = collector.collect()
        for metric in metrics:
            record_metric(metric, path=history_path)
        dispatcher.dispatch(metrics)
        statuses = ", ".join(f"{m.name}={m.status.value}" for m in metrics)
        click.echo(f"[check] {statuses}")

    schedule_cfg = ScheduleConfig(interval_seconds=interval, max_runs=runs)
    runner = ScheduledRunner(check_fn=_run_check, config=schedule_cfg)
    try:
        runner.run()
    except KeyboardInterrupt:
        click.echo("\nWatch stopped.")
