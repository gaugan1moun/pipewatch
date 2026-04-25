"""CLI commands for inspecting and managing circuit breaker state."""

import click
from pipewatch.circuit_breaker import (
    load_circuit_state,
    save_circuit_state,
    reset_circuit,
    DEFAULT_STATE_PATH,
)


@click.group(name="circuit")
def circuit() -> None:
    """Manage circuit breaker state for pipeline metrics."""


@circuit.command(name="status")
@click.option("--state-file", default=DEFAULT_STATE_PATH, show_default=True)
def status(state_file: str) -> None:
    """Show current circuit breaker states."""
    state = load_circuit_state(state_file)
    if not state:
        click.echo("No circuit breaker entries found.")
        return
    for name, entry in sorted(state.items()):
        flag = "[TRIPPED]" if entry.tripped else "[OK]"
        click.echo(
            f"  {flag} {name}  failures={entry.failure_count}"
            + (f"  tripped_at={entry.tripped_at}" if entry.tripped_at else "")
        )


@circuit.command(name="reset")
@click.argument("metric_name")
@click.option("--state-file", default=DEFAULT_STATE_PATH, show_default=True)
def reset(metric_name: str, state_file: str) -> None:
    """Reset the circuit breaker for a specific metric."""
    state = load_circuit_state(state_file)
    reset_circuit(metric_name, state)
    save_circuit_state(state, state_file)
    click.echo(f"Circuit breaker reset for '{metric_name}'.")


@circuit.command(name="purge")
@click.option("--state-file", default=DEFAULT_STATE_PATH, show_default=True)
def purge(state_file: str) -> None:
    """Remove all circuit breaker entries."""
    save_circuit_state({}, state_file)
    click.echo("All circuit breaker entries purged.")
