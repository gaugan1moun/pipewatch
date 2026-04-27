"""Metric value profiler: tracks min/max/avg over a sliding window of history entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import HistoryEntry


@dataclass
class MetricProfile:
    metric_name: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    p50: float
    p95: float

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "count": self.count,
            "min": self.min_value,
            "max": self.max_value,
            "avg": round(self.avg_value, 4),
            "p50": self.p50,
            "p95": self.p95,
        }


def _percentile(sorted_vals: List[float], pct: float) -> float:
    """Return the pct-th percentile from a sorted list."""
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * pct / 100.0
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def profile_metric(
    metric_name: str,
    entries: List[HistoryEntry],
    window: Optional[int] = None,
) -> Optional[MetricProfile]:
    """Build a MetricProfile for *metric_name* from *entries*.

    Args:
        metric_name: The metric to profile.
        entries: Full history list (will be filtered by name).
        window: If given, only consider the most-recent *window* entries.

    Returns:
        A MetricProfile, or None if no matching entries exist.
    """
    relevant = [e for e in entries if e.metric_name == metric_name]
    if not relevant:
        return None
    if window is not None:
        relevant = relevant[-window:]

    values = sorted(e.value for e in relevant)
    count = len(values)
    return MetricProfile(
        metric_name=metric_name,
        count=count,
        min_value=values[0],
        max_value=values[-1],
        avg_value=sum(values) / count,
        p50=_percentile(values, 50),
        p95=_percentile(values, 95),
    )


def profile_all(
    entries: List[HistoryEntry],
    window: Optional[int] = None,
) -> List[MetricProfile]:
    """Return a MetricProfile for every distinct metric name in *entries*."""
    names = sorted({e.metric_name for e in entries})
    profiles = [profile_metric(n, entries, window=window) for n in names]
    return [p for p in profiles if p is not None]
