"""CLI commands for pipeline dependency inspection."""
import json
import click
from pipewatch.dependency import DependencyNode, check_all
from pipewatch.metrics import Metric, MetricStatus


@click.group("dependency")
def dependency():
    """Inspect pipeline metric dependencies."""


@dependency.command("check")
@click.option("--graph", "graph_file", required=True, type=click.Path(exists=True),
              help="JSON file defining dependency nodes.")
@click.option("--metrics", "metrics_file", required=True, type=click.Path(exists=True),
              help="JSON file with current metric snapshots.")
def check_cmd(graph_file: str, metrics_file: str):
    """Check which metrics are blocked by unhealthy upstreams."""
    with open(graph_file) as f:
        raw_nodes = json.load(f)
    nodes = [DependencyNode.from_dict(n) for n in raw_nodes]

    with open(metrics_file) as f:
        raw_metrics = json.load(f)
    metrics = [
        Metric(
            name=m["name"],
            value=m["value"],
            status=MetricStatus(m["status"]),
            tags=m.get("tags", {}),
        )
        for m in raw_metrics
    ]

    results = check_all(metrics, nodes)
    blocked = [r for r in results if r.blocked]

    if not blocked:
        click.echo(click.style("All metrics clear — no blocked dependencies.", fg="green"))
        return

    click.echo(click.style(f"{len(blocked)} metric(s) blocked:", fg="red"))
    for r in blocked:
        click.echo(f"  {r.metric_name}: {r.reason}")
