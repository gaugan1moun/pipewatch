"""Metric correlation: detect pairs of metrics that tend to degrade together."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pipewatch.history import HistoryEntry
from pipewatch.metrics import MetricStatus

# Map status to a numeric score for correlation math
_STATUS_SCORE: Dict[str, float] = {
    MetricStatus.OK.value: 0.0,
    MetricStatus.WARNING.value: 1.0,
    MetricStatus.CRITICAL.value: 2.0,
}


@dataclass
class CorrelationResult:
    metric_a: str
    metric_b: str
    coefficient: float          # Pearson r in [-1, 1]
    sample_count: int

    def to_dict(self) -> dict:
        return {
            "metric_a": self.metric_a,
            "metric_b": self.metric_b,
            "coefficient": round(self.coefficient, 4),
            "sample_count": self.sample_count,
        }


def _scores_for_metric(entries: List[HistoryEntry], name: str) -> List[float]:
    """Return ordered status scores for *name* from history entries."""
    return [
        _STATUS_SCORE.get(e.status, 0.0)
        for e in entries
        if e.metric_name == name
    ]


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    """Compute Pearson correlation coefficient for two equal-length sequences."""
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    den_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def correlate_metrics(
    entries: List[HistoryEntry],
    min_samples: int = 5,
    threshold: float = 0.6,
) -> List[CorrelationResult]:
    """Return metric pairs whose status scores are correlated above *threshold*."""
    names = sorted({e.metric_name for e in entries})
    results: List[CorrelationResult] = []

    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            scores_a = _scores_for_metric(entries, a)
            scores_b = _scores_for_metric(entries, b)
            # Align by position (assumes same collection cadence)
            length = min(len(scores_a), len(scores_b))
            if length < min_samples:
                continue
            r = _pearson(scores_a[:length], scores_b[:length])
            if r is not None and abs(r) >= threshold:
                results.append(CorrelationResult(a, b, r, length))

    results.sort(key=lambda c: abs(c.coefficient), reverse=True)
    return results


def correlation_summary(results: List[CorrelationResult]) -> str:
    if not results:
        return "No significant correlations found."
    lines = [f"{'Metric A':<30} {'Metric B':<30} {'r':>8} {'n':>6}"]
    lines.append("-" * 78)
    for r in results:
        lines.append(f"{r.metric_a:<30} {r.metric_b:<30} {r.coefficient:>8.4f} {r.sample_count:>6}")
    return "\n".join(lines)
