"""Main entry point that registers all CLI command groups."""

from __future__ import annotations

import click

from pipewatch.cli import cli
from pipewatch.cli_schedule import watch
from pipewatch.cli_silence import silence
from pipewatch.cli_tags import tags
from pipewatch.cli_retention import retention
from pipewatch.cli_notifier import notifier
from pipewatch.cli_escalation import escalation
from pipewatch.cli_dependency import dependency
from pipewatch.cli_rollup import rollup


cli.add_command(watch)
cli.add_command(silence)
cli.add_command(tags)
cli.add_command(retention)
cli.add_command(notifier)
cli.add_command(escalation)
cli.add_command(dependency)
cli.add_command(rollup)


def main() -> None:  # pragma: no cover
    cli()
