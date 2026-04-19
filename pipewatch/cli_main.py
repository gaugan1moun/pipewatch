"""Unified CLI entry point combining all pipewatch command groups."""
import click
from pipewatch.cli import cli
from pipewatch.cli_schedule import watch
from pipewatch.cli_silence import silence
from pipewatch.cli_tags import tags
from pipewatch.cli_retention import retention


@click.group()
def main():
    """pipewatch — monitor and alert on data pipeline health metrics."""


main.add_command(cli, name="pipeline")
main.add_command(watch)
main.add_command(silence)
main.add_command(tags)
main.add_command(retention)

if __name__ == "__main__":
    main()
