"""Main CLI entry point — registers all sub-command groups."""

import click

from pipewatch.cli import cli as core_cli
from pipewatch.cli_schedule import watch
from pipewatch.cli_silence import silence
from pipewatch.cli_tags import tags
from pipewatch.cli_retention import retention
from pipewatch.cli_notifier import notifier
from pipewatch.cli_escalation import escalation
from pipewatch.cli_dependency import dependency
from pipewatch.cli_ratelimiter import ratelimit
from pipewatch.cli_rollup import rollup
from pipewatch.cli_comparator import compare
from pipewatch.cli_labeler import labeler
from pipewatch.cli_watchdog import watchdog
from pipewatch.cli_circuit_breaker import circuit


@click.group()
def main() -> None:
    """pipewatch — monitor and alert on data pipeline health."""


main.add_command(core_cli, name="core")
main.add_command(watch)
main.add_command(silence)
main.add_command(tags)
main.add_command(retention)
main.add_command(notifier)
main.add_command(escalation)
main.add_command(dependency)
main.add_command(ratelimit)
main.add_command(rollup)
main.add_command(compare)
main.add_command(labeler)
main.add_command(watchdog)
main.add_command(circuit)

if __name__ == "__main__":
    main()
