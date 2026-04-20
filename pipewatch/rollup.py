"""Rollup: aggregate metric history into time-bucketed summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipewatch.history import HistoryEntry
from pipewatch.metrics import MetricStatus


@dataclass
class RollupBucket:
    """A single time-bucket summary for one metric."""

    metric_name: str
    bucket_label: str          # e.g. "2024-06-01" or "2024-06-01T14"
    count: int = 0
    ok_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    avg_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "bucket_label": self.bucket_label,
            "count": self.count,
            "ok_count": self.ok_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
            "avg_value": self.avg_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
        }


def _bucket_label(ts: str, granularity: str) -> str:
    """Return a bucket label for a timestamp string."""
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return ts[:10]
    if granularity == "hour":
        return dt.strftime("%Y-%m-%dT%H")
    return dt.strftime("%Y-%m-%d")


def rollup_history(
    entries: List[HistoryEntry],
    granularity: str = "day",
) -> Dict[str, List[RollupBucket]]:
    """Group history entries into rollup buckets per metric.

    Args:
        entries: List of HistoryEntry objects.
        granularity: 'day' or 'hour'.

    Returns:
        Dict mapping metric_name -> list of RollupBucket (sorted by label).
    """
    # bucket_map: metric_name -> bucket_label -> RollupBucket
    bucket_map: Dict[str, Dict[str, RollupBucket]] = {}

    for entry in entries:
        name = entry.metric_name
        label = _bucket_label(entry.timestamp, granularity)
        bucket_map.setdefault(name, {})
        if label not in bucket_map[name]:
            bucket_map[name][label] = RollupBucket(metric_name=name, bucket_label=label)

        b = bucket_map[name][label]
        b.count += 1
        status = entry.status
        if status == MetricStatus.OK.value:
            b.ok_count += 1
        elif status == MetricStatus.WARNING.value:
            b.warning_count += 1
        elif status == MetricStatus.CRITICAL.value:
            b.critical_count += 1

        if entry.value is not None:
            vals = [] if b.avg_value is None else []
            # Incremental mean/min/max
            prev_count = b.count - 1
            if b.avg_value is None:
                b.avg_value = entry.value
                b.min_value = entry.value
                b.max_value = entry.value
            else:
                b.avg_value = (b.avg_value * prev_count + entry.value) / b.count
                b.min_value = min(b.min_value, entry.value)
                b.max_value = max(b.max_value, entry.value)

    result: Dict[str, List[RollupBucket]] = {}
    for name, buckets in bucket_map.items():
        result[name] = sorted(buckets.values(), key=lambda bk: bk.bucket_label)
    return result


def rollup_summary(rollups: Dict[str, List[RollupBucket]]) -> str:
    """Return a human-readable summary of rollup data."""
    if not rollups:
        return "No rollup data available."
    lines = []
    for name, buckets in sorted(rollups.items()):
        lines.append(f"Metric: {name}")
        for b in buckets:
            lines.append(
                f"  [{b.bucket_label}] count={b.count} "
                f"ok={b.ok_count} warn={b.warning_count} crit={b.critical_count}"
                + (f" avg={b.avg_value:.3f}" if b.avg_value is not None else "")
            )
    return "\n".join(lines)
