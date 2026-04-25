"""CLI commands for quota management."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import click

from pipewatch.quota import (
    DEFAULT_QUOTA_PATH,
    QuotaRule,
    QuotaState,
    check_quota,
    load_quota_state,
    save_quota_state,
)


@click.group()
def quota() -> None:
    """Manage metric violation quotas."""


@quota.command("check")
@click.argument("metric_name")
@click.argument("status")
@click.option("--max-violations", default=5, show_default=True, help="Max violations allowed.")
@click.option("--window", default=3600, show_default=True, help="Rolling window in seconds.")
@click.option("--state-file", default=DEFAULT_QUOTA_PATH, show_default=True)
def check_cmd(
    metric_name: str,
    status: str,
    max_violations: int,
    window: int,
    state_file: str,
) -> None:
    """Record a violation event and check if quota is breached."""
    rule = QuotaRule(metric_name=metric_name, max_violations=max_violations, window_seconds=window)
    state = load_quota_state(state_file)
    result = check_quota(rule, status, state)
    save_quota_state(state, state_file)
    if result.breached:
        click.echo(
            f"[QUOTA BREACHED] {metric_name}: {result.violations_in_window}/{result.max_violations} "
            f"violations in last {window}s"
        )
    else:
        click.echo(
            f"[OK] {metric_name}: {result.violations_in_window}/{result.max_violations} "
            f"violations in last {window}s"
        )


@quota.command("status")
@click.option("--state-file", default=DEFAULT_QUOTA_PATH, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def status_cmd(state_file: str, as_json: bool) -> None:
    """Show current quota violation state."""
    state = load_quota_state(state_file)
    if not state:
        click.echo("No quota state recorded.")
        return
    if as_json:
        click.echo(json.dumps({k: v.to_dict() for k, v in state.items()}, indent=2))
    else:
        for name, entry in state.items():
            click.echo(f"  {name}: {entry.count()} violation(s) recorded")


@quota.command("reset")
@click.argument("metric_name")
@click.option("--state-file", default=DEFAULT_QUOTA_PATH, show_default=True)
def reset_cmd(metric_name: str, state_file: str) -> None:
    """Clear quota state for a specific metric."""
    state = load_quota_state(state_file)
    if metric_name in state:
        del state[metric_name]
        save_quota_state(state, state_file)
        click.echo(f"Quota state reset for '{metric_name}'.")
    else:
        click.echo(f"No quota state found for '{metric_name}'.")
