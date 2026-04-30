"""Main CLI entry-point aggregating all sub-command groups."""
from __future__ import annotations

import click

from pipewatch.cli import cli
from pipewatch.cli_schedule import watch
from pipewatch.cli_tags import tags
from pipewatch.cli_retention import retention
from pipewatch.cli_silence import silence
from pipewatch.cli_notifier import notifier
from pipewatch.cli_escalation import escalation
from pipewatch.cli_dependency import dependency
from pipewatch.cli_rollup import rollup
from pipewatch.cli_comparator import compare
from pipewatch.cli_labeler import labeler
from pipewatch.cli_ratelimiter import ratelimit
from pipewatch.cli_watchdog import watchdog
from pipewatch.cli_circuit_breaker import circuit
from pipewatch.cli_quota import quota
from pipewatch.cli_replay import replay
from pipewatch.cli_profiler import profiler
from pipewatch.cli_heatmap import heatmap
from pipewatch.cli_correlator import correlate
from pipewatch.cli_scorer import scorer


@click.group()
def main() -> None:
    """pipewatch — monitor and alert on data pipeline health metrics."""


main.add_command(cli)
main.add_command(watch)
main.add_command(tags)
main.add_command(retention)
main.add_command(silence)
main.add_command(notifier)
main.add_command(escalation)
main.add_command(dependency)
main.add_command(rollup)
main.add_command(compare)
main.add_command(labeler)
main.add_command(ratelimit)
main.add_command(watchdog)
main.add_command(circuit)
main.add_command(quota)
main.add_command(replay)
main.add_command(profiler)
main.add_command(heatmap)
main.add_command(correlate)
main.add_command(scorer)
