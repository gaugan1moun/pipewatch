"""Health scorer: computes a numeric health score (0-100) for a set of metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.metrics import Metric, MetricStatus

# Weight per status (lower is worse)
_STATUS_WEIGHT: dict[MetricStatus, float] = {
    MetricStatus.OK: 1.0,
    MetricStatus.WARNING: 0.5,
    MetricStatus.CRITICAL: 0.0,
}


@dataclass
class ScoredMetric:
    name: str
    status: MetricStatus
    weight: float  # contribution weight (default 1.0)
    score: float   # 0.0 – 1.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "weight": self.weight,
            "score": round(self.score, 4),
        }


@dataclass
class HealthScore:
    total: float          # 0 – 100
    metrics: List[ScoredMetric] = field(default_factory=list)
    num_ok: int = 0
    num_warning: int = 0
    num_critical: int = 0

    def to_dict(self) -> dict:
        return {
            "total": round(self.total, 2),
            "num_ok": self.num_ok,
            "num_warning": self.num_warning,
            "num_critical": self.num_critical,
            "metrics": [m.to_dict() for m in self.metrics],
        }

    def grade(self) -> str:
        if self.total >= 90:
            return "A"
        if self.total >= 75:
            return "B"
        if self.total >= 50:
            return "C"
        if self.total >= 25:
            return "D"
        return "F"


def score_metrics(
    metrics: List[Metric],
    weights: Optional[dict[str, float]] = None,
) -> HealthScore:
    """Compute a weighted health score from a list of evaluated Metric objects."""
    weights = weights or {}
    scored: List[ScoredMetric] = []
    total_weight = 0.0
    weighted_sum = 0.0
    counts = {MetricStatus.OK: 0, MetricStatus.WARNING: 0, MetricStatus.CRITICAL: 0}

    for m in metrics:
        w = weights.get(m.name, 1.0)
        s = _STATUS_WEIGHT.get(m.status, 0.0)
        scored.append(ScoredMetric(name=m.name, status=m.status, weight=w, score=s))
        weighted_sum += s * w
        total_weight += w
        counts[m.status] = counts.get(m.status, 0) + 1

    total = (weighted_sum / total_weight * 100) if total_weight > 0 else 100.0

    return HealthScore(
        total=total,
        metrics=scored,
        num_ok=counts[MetricStatus.OK],
        num_warning=counts[MetricStatus.WARNING],
        num_critical=counts[MetricStatus.CRITICAL],
    )
