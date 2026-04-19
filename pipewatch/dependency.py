"""Pipeline dependency tracking — detect blocked/stale upstream metrics."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pipewatch.metrics import Metric, MetricStatus


@dataclass
class DependencyNode:
    name: str
    depends_on: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "depends_on": self.depends_on}

    @staticmethod
    def from_dict(d: dict) -> "DependencyNode":
        return DependencyNode(name=d["name"], depends_on=d.get("depends_on", []))


@dataclass
class DependencyCheckResult:
    metric_name: str
    blocked: bool
    blocking_metrics: List[str] = field(default_factory=list)
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "blocked": self.blocked,
            "blocking_metrics": self.blocking_metrics,
            "reason": self.reason,
        }


def build_graph(nodes: List[DependencyNode]) -> Dict[str, List[str]]:
    """Return adjacency map: metric -> list of its dependencies."""
    return {n.name: n.depends_on for n in nodes}


def check_dependencies(
    metric: Metric,
    graph: Dict[str, List[str]],
    metric_map: Dict[str, Metric],
) -> DependencyCheckResult:
    """Check whether any upstream dependency of *metric* is non-OK."""
    deps = graph.get(metric.name, [])
    blocking = [
        dep
        for dep in deps
        if dep in metric_map and metric_map[dep].status != MetricStatus.OK
    ]
    if blocking:
        reason = f"Upstream metrics not OK: {', '.join(blocking)}"
        return DependencyCheckResult(
            metric_name=metric.name,
            blocked=True,
            blocking_metrics=blocking,
            reason=reason,
        )
    return DependencyCheckResult(metric_name=metric.name, blocked=False)


def check_all(
    metrics: List[Metric],
    nodes: List[DependencyNode],
) -> List[DependencyCheckResult]:
    graph = build_graph(nodes)
    metric_map = {m.name: m for m in metrics}
    return [check_dependencies(m, graph, metric_map) for m in metrics]
