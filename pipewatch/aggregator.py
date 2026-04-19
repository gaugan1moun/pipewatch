"""Aggregate metrics across groups or time windows."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pipewatch.metrics import Metric, MetricStatus


@dataclass
class AggregatedMetric:
    name: str
    count: int
    mean: float
    min_val: float
    max_val: float
    statuses: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "mean": round(self.mean, 4),
            "min": self.min_val,
            "max": self.max_val,
            "statuses": self.statuses,
        }

    @property
    def worst_status(self) -> str:
        for s in (MetricStatus.CRITICAL, MetricStatus.WARNING, MetricStatus.OK):
            if self.statuses.get(s.value, 0) > 0:
                return s.value
        return MetricStatus.OK.value


def aggregate_metrics(metrics: List[Metric]) -> Dict[str, AggregatedMetric]:
    """Group metrics by name and compute aggregate statistics."""
    groups: Dict[str, List[Metric]] = {}
    for m in metrics:
        groups.setdefault(m.name, []).append(m)

    result = {}
    for name, group in groups.items():
        values = [m.value for m in group]
        statuses: Dict[str, int] = {}
        for m in group:
            statuses[m.status.value] = statuses.get(m.status.value, 0) + 1
        result[name] = AggregatedMetric(
            name=name,
            count=len(values),
            mean=sum(values) / len(values),
            min_val=min(values),
            max_val=max(values),
            statuses=statuses,
        )
    return result


def aggregation_summary(aggregated: Dict[str, AggregatedMetric]) -> str:
    lines = [f"{'Metric':<30} {'Count':>6} {'Mean':>10} {'Min':>10} {'Max':>10} {'Worst':<10}"]
    lines.append("-" * 80)
    for agg in aggregated.values():
        lines.append(
            f"{agg.name:<30} {agg.count:>6} {agg.mean:>10.3f} "
            f"{agg.min_val:>10.3f} {agg.max_val:>10.3f} {agg.worst_status:<10}"
        )
    return "\n".join(lines)
